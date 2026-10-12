"""Receipts e conversa têm escopos distintos numa só autoria, sem execução."""
import json

import pytest

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
from mente_laylay.personalidade.planejador_resposta import fala_factual_resultados_compostos


def _responder(conversa, *, violacao="", sem_receipt=False):
    itens = [] if sem_receipt else [ResultadoAcao(
        intent="APP_OPEN", alvo="calculadora", status="aberto", executou=True,
        confirmado=True, origem="executor", id_solicitacao="app-1",
        params={"nome_app": "calculadora"})]
    avisos = ["Ainda não tenho confirmação do resultado da parte operacional."] if sem_receipt else []
    segura = " ".join([fala_factual_resultados_compostos(itens), *avisos])
    chamadas = []
    def modelo(mensagens, **opcoes):
        chamadas.append((json.loads(mensagens[1]["content"]), opcoes))
        trechos = [] if sem_receipt else ["Abri a calculadora"]
        dados = {"trechos": trechos, "conversa": conversa}
        if violacao == "comando":
            dados["comandos"] = [{"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}]
        elif violacao == "residuo":
            dados["fala"] = "A luz foi ligada"
        elif violacao == "omissao":
            dados["conversa"] = ""
        return json.dumps(dados, ensure_ascii=False)
    resposta = personalizar_confirmacao_composta_llm(itens, segura,
        enviar_mensagem=modelo, texto_conversacional="Pode abrir a calculadora significa o quê?",
        avisos_obrigatorios=avisos)
    return resposta, chamadas


@pytest.mark.parametrize("sem_receipt", [False, True])
def test_autoria_mista_preserva_resultado_e_responde_sem_receipt_ficticio(sem_receipt):
    conversa = "Essa expressão é um pedido para abrir o aplicativo."
    resposta, chamadas = _responder(conversa, sem_receipt=sem_receipt)
    assert len(chamadas) == 1
    assert resposta.usada_llm
    assert conversa in resposta.fala
    assert len(chamadas[0][0]["resultados"]) == (0 if sem_receipt else 1)
    assert chamadas[0][1]["_com_tools"] is False
    if sem_receipt:
        assert resposta.fala.count("Ainda não tenho confirmação do resultado da parte operacional.") == 1


def test_autoria_mista_tem_orcamento_normal_sem_elevar_limite_global():
    from mente_laylay.integracao.orcamento_llm_turno import OrcamentoLLMTurnoRuntime
    _, chamadas = _responder("Essa expressão é um pedido para abrir o aplicativo.")
    opcoes = chamadas[0][1]
    decisao = OrcamentoLLMTurnoRuntime().autorizar_chamada(
        tipo_chamada=opcoes["_tipo_chamada"], classe_timeout=opcoes["_classe_timeout"],
        timeout_solicitado=opcoes["timeout"])
    assert decisao.permitida
    assert decisao.timeout_s == 15.0


@pytest.mark.parametrize("status,executou,confirmado", [
    ("aberto", True, True), ("falha_execucao", False, False),
    ("enviado", True, None), ("ja_estava_aberto", False, True),
])
def test_formato_misto_preserva_certeza_do_receipt(status, executou, confirmado):
    item = ResultadoAcao(intent="APP_OPEN", alvo="calculadora", status=status,
        executou=executou, confirmado=confirmado, origem="executor", id_solicitacao="app-certeza")
    fato = fala_factual_resultados_compostos([item])
    dados = {"trechos": [fato], "conversa": "Essa expressão é um pedido educado."}
    r = personalizar_confirmacao_composta_llm([item], fato,
        enviar_mensagem=lambda *_a, **_k: json.dumps(dados), texto_conversacional="O que significa essa expressão?")
    assert r.usada_llm, r.motivo_fallback
    assert fato in r.fala


@pytest.mark.parametrize("violacao", ["sucesso_falso", "troca", "omissao", "numero_emprestado"])
def test_lista_mista_nao_transfere_fatos_entre_receipts_e_conversa(violacao):
    itens = [
        ResultadoAcao(intent="APP_OPEN", alvo="calculadora", status="aberto", executou=True,
                      confirmado=True, origem="executor", id_solicitacao="app-a"),
        ResultadoAcao(intent="APP_OPEN", alvo="editor", status="falha_execucao", executou=False,
                      confirmado=False, origem="executor", id_solicitacao="app-b"),
    ]
    trechos = ["Abri a calculadora.", "Não consegui abrir o editor."]
    dados = {"trechos": trechos, "conversa": "O exemplo conceitual contém 27 números."}
    if violacao == "sucesso_falso": trechos[1] = "Abri o editor."
    elif violacao == "troca": trechos.reverse()
    elif violacao == "omissao": trechos.pop()
    elif violacao == "numero_emprestado": trechos[0] = "Abri a calculadora 27 vezes."
    r = personalizar_confirmacao_composta_llm(itens, fala_factual_resultados_compostos(itens),
        enviar_mensagem=lambda *_a, **_k: json.dumps(dados), texto_conversacional="Explique um exemplo numérico.")
    assert not r.usada_llm
    assert r.motivo_fallback


@pytest.mark.parametrize("conversa,violacao", [
    ("A música está pausada.", ""),
    ("Já agendei a pausa para quando você confirmar.", ""),
    ("Vou te avisar mais tarde.", ""),
    ("Essa expressão é um pedido para abrir o aplicativo.", "comando"),
    ("Essa expressão é um pedido para abrir o aplicativo.", "residuo"),
    ("Essa expressão é um pedido para abrir o aplicativo.", "omissao"),
])
def test_conversa_nao_empresta_receipt_nem_concede_nova_execucao(conversa, violacao):
    resposta, chamadas = _responder(conversa, violacao=violacao)
    assert len(chamadas) == 1
    assert not resposta.usada_llm
    assert resposta.motivo_fallback
    assert "parte conversacional" in resposta.fala
    assert conversa not in resposta.fala


@pytest.mark.parametrize("fala,proibida", [
    ("A música está pausada.", True),
    ("O aplicativo continua parado.", True),
    ("Vou te avisar mais tarde.", True),
    ("Vou avisar depois da apresentação.", True),
    ("Não tenho confirmação de que a música está pausada.", False),
    ("O termo pausada indica interrupção temporária.", False),
    ("Vou te explicar agora.", False),
])
def test_guardiao_canonico_separa_estado_e_promessa_de_explicacao(fala, proibida):
    from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
    r = validar_alegacoes_da_fala(fala,
        plano={"comandos": [], "exigir_receipt_para_estado": True}, origem="canal_voz")
    assert bool(r["problemas"]) is proibida


def _turno():
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
    from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
    texto = "Abre a calculadora; pode abrir o bloco de notas significa o quê?"
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                         texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "misto-1"
    return turno, texto


@pytest.mark.parametrize("adulteracao", ["nenhuma", "texto", "id", "revisao", "indice", "autoridade"])
def test_cobertura_restante_exige_frame_canonico_vinculado(adulteracao):
    from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
    turno, texto = _turno()
    if adulteracao == "texto": turno["texto"] = "outra entrada"
    elif adulteracao == "id": turno["id"] = None
    elif adulteracao == "revisao": turno["revisao_intra_turno"] = "formato inválido"
    elif adulteracao == "indice": turno["segmentos"][1]["indice"] = 0
    elif adulteracao == "autoridade": turno["autoriza_execucao"] = False
    c = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert (c is not None) is (adulteracao == "nenhuma")
    if c is not None:
        assert c.indices == (1,)
        assert c.texto == turno["texto_conversacional"]


@pytest.mark.parametrize("mudanca", ["nenhuma", "turno", "conteudo", "natureza"])
def test_lote_misto_revalida_cobertura_apos_autoria(mudanca):
    from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime
    turno, texto = _turno()
    estado = EstadoCompartilhadoRuntime()
    estado.mental["turno_atual"] = turno
    falas = []
    orq = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado, "print": lambda *_: None})
    orq.falar = lambda fala, *_: falas.append(fala) or True
    def modelo(mensagens, **_):
        entrada = json.loads(mensagens[1]["content"])
        aviso = entrada["avisos_obrigatorios"]
        conversa = "É um pedido para abrir o aplicativo."
        if mudanca == "turno": estado.mental["turno_atual"] = {**turno, "id": "outro"}
        elif mudanca == "conteudo": turno["texto_conversacional"] = "outro assunto"
        elif mudanca == "natureza": turno["segmentos"][1]["natureza_acao"] = "condicao_nao_verificada"
        return json.dumps({"trechos": [], "conversa": conversa})
    with orq.agrupar_resultados_operacionais(texto_usuario=texto, enviar_mensagem=modelo) as lote:
        lote.complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert len(falas) == (1 if mudanca == "nenhuma" else 0)
    assert lote.resposta_publicada is (mudanca == "nenhuma")
