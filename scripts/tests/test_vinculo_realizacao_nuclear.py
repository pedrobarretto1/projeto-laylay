"""A escolha do núcleo não prova que o texto entregue realizou esse núcleo."""
import json
from dataclasses import replace

import pytest

from scripts.analises.sonda_prioridade_turnos_mistos import projetar_nucleo_explicativo
from scripts.analises.sonda_prioridade_turnos_mistos import coletar
from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


def _base(acao="retoma a música", sujeito="eu"):
    texto = f"Abre a calculadora; quando {sujeito} confirmar, {acao}"
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "realizacao-1"
    c = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert c is not None
    contrato = projetar_nucleo_explicativo(turno, texto)
    contrato.update(complemento_nuclear=c,
        proposta_nuclear={"realizacoes": [{"indice": c.indices[0], "opcao": "condicao_1"}]})
    fonte = json.dumps(c.atos_explicativos[0].texto, ensure_ascii=False)
    fala = (f"O trecho {fonte} expressa uma condição não verificada neste pedido. "
            "Esta explicação não deixou a ação agendada. Quando quiser executá-la, faça um novo pedido direto.")
    return c, contrato, fala


@pytest.mark.parametrize("acao", ["retoma a música", "liga a luz", "abre o navegador", "abre o arquivo notas.txt"])
@pytest.mark.parametrize("sujeito", ["eu", "você", "a gente"])
def test_realizacao_controlada_vincula_texto_a_fonte_sem_mudar_pessoa(acao, sujeito):
    c, contrato, fala = _base(acao, sujeito)
    r = validar_aderencia_contrato_fala(c.texto, fala, contrato_fala=contrato, turno_id=c.turno_id)
    assert r["aceita"]  # RED alcança a guarda de cobertura, não import/API ausente
    assert r["categoria"] == "aderencia"
    assert r["nucleo_atendido"] and r["avaliado"] and not r["requer_reparo"]
    assert r["autoriza_execucao"] is False
    assert r["prova_semantica_livre"] is False


@pytest.mark.parametrize("adicao", [
    " Quando você confirmar, eu paro a música.",
    " Quando você confirmar, a música retomará.",
    " Não tenho capacidade de abrir aplicativos.",
])
def test_nucleo_correto_acompanhado_de_texto_nao_coberto_nao_e_aprovado(adicao):
    c, contrato, fala = _base()
    r = validar_aderencia_contrato_fala(c.texto, fala + adicao, contrato_fala=contrato, turno_id=c.turno_id)
    assert not r["aceita"]
    assert r["categoria"] == "contradicao_vinculo"
    assert r["problemas"] == ["texto_diverge_da_realizacao"]
    assert r["requer_reparo"]  # violação verificável de proposta, não de cobertura


def test_texto_livre_correto_continua_sem_prova_de_aderencia():
    c, contrato, _ = _base()
    contrato.pop("proposta_nuclear")
    r = validar_aderencia_contrato_fala(c.texto, "A condição não deixou agendamento; faça novo pedido.",
                                      contrato_fala=contrato, turno_id=c.turno_id)
    assert r["categoria"] == "cobertura_ausente"
    assert not r["aceita"] and not r["avaliado"] and not r["requer_reparo"]


@pytest.mark.parametrize("campo", ["turno", "fonte", "indice", "opcao", "comando"])
def test_vinculo_invalido_nao_empresta_verdade_de_outro_ato(campo):
    c, contrato, fala = _base()
    turno_id = c.turno_id
    texto = c.texto
    if campo == "turno": turno_id = "outro-turno"
    elif campo == "fonte": texto = "quando eu confirmar, liga a luz"
    elif campo == "indice": contrato["proposta_nuclear"]["realizacoes"][0]["indice"] = 99
    elif campo == "opcao": contrato["proposta_nuclear"]["realizacoes"][0]["opcao"] = "execucao_agendada"
    else: contrato["proposta_nuclear"]["comandos"] = [{"intent": "IOT_CONTROL"}]
    r = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato, turno_id=turno_id)
    assert not r["aceita"] and not r["autoriza_execucao"]


@pytest.mark.parametrize("opcao", ["condicao_1", "condicao_2", "condicao_3"])
def test_variantes_sao_conferidas_pelo_texto_real_e_nao_por_um_selo(opcao):
    from mente_laylay.cognicao.contrato_fala import construir_realizacoes_nucleo_explicativo
    c, contrato, _ = _base()
    opcoes = construir_realizacoes_nucleo_explicativo(c)
    fala = next(o["fala"] for o in opcoes[0]["opcoes"] if o["id"] == opcao)
    contrato["proposta_nuclear"]["realizacoes"][0]["opcao"] = opcao
    r = validar_aderencia_contrato_fala(c.texto, fala, contrato_fala=contrato, turno_id=c.turno_id)
    assert r["aceita"]
    # Inventário enviado ao modelo não é uma fonte de verdade para validação.
    opcoes[0]["opcoes"][0]["fala"] = "Quando você confirmar, eu paro a música."
    r = validar_aderencia_contrato_fala(c.texto, opcoes[0]["opcoes"][0]["fala"],
                                      contrato_fala=contrato, turno_id=c.turno_id)
    assert not r["aceita"]


def test_indices_duplicados_e_pessoa_adulterada_nao_geram_realizacoes():
    from mente_laylay.cognicao.contrato_fala import construir_realizacoes_nucleo_explicativo
    c, _, _ = _base()
    duplicado = replace(c, indices=c.indices * 2, atos_explicativos=c.atos_explicativos * 2)
    assert construir_realizacoes_nucleo_explicativo(duplicado) == ()
    pessoa_trocada = replace(c, atos_explicativos=(replace(c.atos_explicativos[0], pessoa_condicao="destinatario"),))
    assert construir_realizacoes_nucleo_explicativo(pessoa_trocada) == ()


def test_consulta_de_significado_ainda_nao_herda_cobertura_condicional():
    from mente_laylay.cognicao.contrato_fala import construir_realizacoes_nucleo_explicativo
    texto = "Abre a calculadora; pode apagar o arquivo notas.txt significa o quê?"
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "consulta-sem-cobertura"
    c = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert c is not None and construir_realizacoes_nucleo_explicativo(c) == ()
    contrato = projetar_nucleo_explicativo(turno, texto)
    contrato.update(complemento_nuclear=c,
        proposta_nuclear={"realizacoes": [{"indice": c.indices[0], "opcao": "condicao_1"}]})
    r = validar_aderencia_contrato_fala(c.texto, "Uma consulta não é uma condição.",
                                      contrato_fala=contrato, turno_id=c.turno_id)
    assert r["categoria"] == "cobertura_ausente" and not r["aceita"]


def test_fonte_longa_com_aspas_unicode_nao_e_truncada_ou_normalizada_no_vinculo():
    from mente_laylay.cognicao.contrato_fala import construir_realizacoes_nucleo_explicativo
    c, contrato, _ = _base('abre o arquivo "' + "á" * 320 + '.txt"')
    opcoes = construir_realizacoes_nucleo_explicativo(c)
    fala = opcoes[0]["opcoes"][0]["fala"]
    assert json.dumps(c.atos_explicativos[0].texto, ensure_ascii=False) in fala
    r = validar_aderencia_contrato_fala(c.texto, fala, contrato_fala=contrato, turno_id=c.turno_id)
    assert r["aceita"]
    r = validar_aderencia_contrato_fala(c.texto, fala.replace("á", "a"),
                                      contrato_fala=contrato, turno_id=c.turno_id)
    assert r["categoria"] == "contradicao_vinculo"


@pytest.mark.parametrize("negativo", [False, True])
def test_vinculo_instalado_publica_uma_resposta_sem_reentrada_e_recusa_adicao(negativo):
    r = coletar(realizacao_controlada=True, contraprova_compromisso=negativo)
    assert all(r["instalacao"].values()) and r["fontes_estaveis"]
    assert len(r["resultados"]) == 3
    for caso in r["resultados"]:
        assert len(caso["recebidos"]) == len(caso["modelos"]) == len(caso["textos_publicados"]) == 1
        assert not caso["reentrada_porta_operacional"]
        avaliacao = caso["modelos"][0]["avaliacao_nuclear"]
        assert avaliacao["aceita"] is not negativo
        assert not avaliacao["autoriza_execucao"] and not avaliacao["prova_semantica_livre"]
        assert caso["primeira_fronteira_red"] == ""
        if negativo:
            assert avaliacao["categoria"] == "contradicao_vinculo"
            assert caso["compromisso_injetado"] not in caso["textos_publicados"][0]
            assert caso["plano"]["fase"] == "tratado_prioritario_parcial"
        else:
            assert avaliacao["categoria"] == "aderencia"
            assert caso["plano"]["fase"] == "tratado_prioritario_misto"
    assert not r["efeitos_externos_executados"] and not r["modelo_real_consultado"]


def test_lista_explicita_e_objeto_envolvente_preservam_a_mesma_selecao():
    c, contrato, fala = _base()
    contrato["proposta_nuclear"] = contrato["proposta_nuclear"]["realizacoes"]
    r = validar_aderencia_contrato_fala(c.texto, fala, contrato_fala=contrato, turno_id=c.turno_id)
    assert r["aceita"] and r["categoria"] == "aderencia"
    assert r["indices_cobertos"] == list(c.indices)


@pytest.mark.parametrize("acao", ["retoma a música", "liga a luz", "abre o navegador", "abre o arquivo notas.txt"])
@pytest.mark.parametrize("opcao", ["condicao_1", "condicao_2", "condicao_3"])
def test_autora_cotidiana_realiza_condicao_por_escolha_sem_ponte_diagnostica(acao, opcao):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    from mente_laylay.cognicao.contrato_fala import realizar_nucleo_explicativo
    c, _, _ = _base(acao)
    proposta = {"realizacoes": [{"indice": c.indices[0], "opcao": opcao}]}
    chamadas = []
    def modelo(mensagens, **opcoes):
        chamadas.append((json.loads(mensagens[1]["content"]), opcoes))
        return json.dumps({"trechos": [], **proposta})
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo,
        avisos_obrigatorios=["Sem confirmação operacional."])
    assert len(chamadas) == 1
    assert r.usada_llm, r.motivo_fallback  # primeiro RED: autora exige conversa livre
    assert r.fala == "Sem confirmação operacional. " + realizar_nucleo_explicativo(c, proposta)[0]
    assert chamadas[0][0]["realizacoes_permitidas"]
    assert chamadas[0][1]["_com_tools"] is False


@pytest.mark.parametrize("status,executou,confirmado", [
    ("aberto", True, True), ("falha_execucao", False, False),
    ("enviado", True, None), ("app_ja_aberto_observado", False, True),
])
def test_realizacao_cotidiana_preserva_certeza_independente_do_receipt(status, executou, confirmado):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    from mente_laylay.personalidade.planejador_resposta import fala_factual_resultados_compostos, classificar_resultado
    c, _, _ = _base()
    item = ResultadoAcao(id_solicitacao="nuclear-app", intent="APP_OPEN", alvo="calculadora",
        status=status, executou=executou, confirmado=confirmado, origem="executor")
    fato = fala_factual_resultados_compostos([item])
    assert classificar_resultado(item) == {"aberto": "sucesso", "falha_execucao": "falha",
        "enviado": "incerto", "app_ja_aberto_observado": "sem_acao"}[status]
    dados = {"trechos": [fato], "realizacoes": [{"indice": c.indices[0], "opcao": "condicao_2"}]}
    r = personalizar_confirmacao_composta_llm([item], fato,
        texto_conversacional=c.texto, complemento_conversacional=c,
        enviar_mensagem=lambda *_a, **_k: json.dumps(dados))
    assert r.usada_llm, r.motivo_fallback
    assert r.fala.startswith(fato + " ")


@pytest.mark.parametrize("violacao", ["indice", "opcao", "promessa", "comando", "texto_livre", "sucesso_falso"])
def test_protocolo_cotidiano_rejeita_conteudo_nao_coberto_sem_receipt_emprestado(violacao):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    c, _, _ = _base()
    item = ResultadoAcao(id_solicitacao="falha-app", intent="APP_OPEN", alvo="calculadora",
        status="falha_execucao", executou=False, confirmado=False, origem="executor")
    dados = {"trechos": ["Não consegui abrir a calculadora."],
             "realizacoes": [{"indice": c.indices[0], "opcao": "condicao_1"}]}
    if violacao == "indice": dados["realizacoes"][0]["indice"] = 99
    elif violacao == "opcao": dados["realizacoes"][0]["opcao"] = "agendar"
    elif violacao == "promessa": dados["conversa"] = "Quando você confirmar, a música retomará."
    elif violacao == "comando": dados["comandos"] = [{"intent": "MEDIA_CONTROL"}]
    elif violacao == "texto_livre":
        dados = {"trechos": dados["trechos"], "conversa": "A condição não criou agendamento. Quando você confirmar, a música retomará."}
    else: dados["trechos"] = ["Abri a calculadora."]
    chamadas = []
    def modelo(*_a, **_k):
        chamadas.append(True)
        return json.dumps(dados)
    r = personalizar_confirmacao_composta_llm([item], "Não consegui abrir a calculadora.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert not r.usada_llm
    assert len(chamadas) == 1
    assert "Quando você confirmar" not in r.fala and "Abri a calculadora" not in r.fala
    assert "Não consegui abrir a calculadora." in r.fala


@pytest.mark.parametrize("mudanca", ["nenhuma", "turno", "pessoa"])
def test_lote_cotidiano_revalida_escolha_e_nao_apaga_pendencias_alheias(mudanca):
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    c, _, _ = _base()
    turno = classificar_modalidade_turno(c.texto_usuario, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = c.turno_id
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno},
        continuidades={"comando_sugerido_estado": {"tipo": "salvar", "dominio": "notas", "alvo": "nota-a"}})
    pendencias_antes = estado.snapshot()["continuidades"]
    orq = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado, "print": lambda *_: None})
    chamadas, publicados = [], []
    orq.falar = lambda fala, *_: publicados.append(fala) or True
    itens = [ResultadoAcao(id_solicitacao="nuclear-ok", intent="APP_OPEN", alvo="calculadora",
                status="aberto", executou=True, confirmado=True, origem="executor"),
             ResultadoAcao(id_solicitacao="nuclear-falha", intent="APP_OPEN", alvo="editor",
                status="falha_execucao", executou=False, confirmado=False, origem="executor")]
    def modelo(mensagens, **_):
        entrada = json.loads(mensagens[1]["content"])
        chamadas.append(entrada)
        if mudanca == "turno": estado.mental["turno_atual"]["id"] = "outro-turno"
        elif mudanca == "pessoa":
            estado.mental["turno_atual"]["segmentos"][1]["contrato_explicativo"]["pessoa_condicao"] = "destinatario"
        return json.dumps({"trechos": ["Abri a calculadora.", "Não consegui abrir o editor."],
            "realizacoes": [{"indice": c.indices[0], "opcao": "condicao_2"}]})
    with orq.agrupar_resultados_operacionais(texto_usuario=c.texto_usuario, enviar_mensagem=modelo) as lote:
        lote.complemento = c
        lote.avisos.append("Aviso independente imutável.")
        for item in itens:
            assert orq.acumular_resultado_operacional(item, "")
    assert len(chamadas) == 1
    assert [r["confirmado"] for r in chamadas[0]["resultados"]] == [True, False]
    assert lote.resultados == itens
    assert estado.snapshot()["continuidades"] == pendencias_antes
    assert len(publicados) == (1 if mudanca == "nenhuma" else 0)
    if publicados:
        assert publicados[0].startswith("Abri a calculadora. Não consegui abrir o editor.")
        assert publicados[0].count("Aviso independente imutável.") == 1
        assert "novo pedido direto" in publicados[0]
    assert lote.resposta_publicada is (mudanca == "nenhuma")


@pytest.mark.parametrize("promessa", [
    "Quando você confirmar, eu paro a música — mas só depois que você disser isso.",
    "Quando você confirmar, a música retomará.",
    "Será necessário que você confirme explicitamente para que eu ative a ação.",
])
def test_promessas_que_escapam_da_guarda_livre_nao_entram_no_canal_coberto(promessa):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    c, _, _ = _base()
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c,
        enviar_mensagem=lambda *_a, **_k: json.dumps({"trechos": [], "conversa": promessa}))
    assert not r.usada_llm and r.motivo_fallback == "estrutura_nuclear_invalida"
    assert promessa not in r.fala


@pytest.mark.parametrize("adulteracao", ["nenhuma", "texto_fora_json", "inventario"])
def test_autora_preserva_fonte_citada_e_nao_confia_em_inventario_mutavel(adulteracao):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    c, _, _ = _base('abre o arquivo "á 15.txt"')
    fonte = json.dumps(c.atos_explicativos[0].texto, ensure_ascii=False)
    def modelo(mensagens, **_):
        inventario = json.loads(mensagens[1]["content"])
        if adulteracao == "inventario":
            inventario["realizacoes_permitidas"][0]["opcoes"][0]["fala"] = "Vou executar depois."
        resposta = json.dumps({"trechos": [], "realizacoes": [{"indice": c.indices[0], "opcao": "condicao_1"}]})
        return resposta + (" Vou executar depois." if adulteracao == "texto_fora_json" else "")
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert r.usada_llm is (adulteracao != "texto_fora_json")
    assert "Vou executar depois" not in r.fala
    if r.usada_llm: assert fonte in r.fala
