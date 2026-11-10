"""Reparo autoral é read-only e não troca a pessoa da condição."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime


def complemento(sujeito="eu", acao="retoma a música"):
    texto = f"Abre a calculadora; quando {sujeito} confirmar, {acao}."
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "reparo-1"
    c = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert c is not None
    return c


def consulta_sem_cobertura_nuclear():
    # O reparo livre continua aplicável às consultas. Condições cobertas
    # agora exigem escolhas; não manter uma fixture de protocolo extinto.
    texto = "Abre a calculadora; pode abrir o bloco de notas significa o quê?"
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "reparo-consulta"
    c = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    assert c is not None
    return c


@pytest.mark.parametrize("acao", ["retoma a música", "liga a luz", "abre o arquivo notas.txt"])
def test_condicao_do_usuario_nao_vira_condicao_da_autora(acao):
    c = complemento(acao=acao)
    r = validar_alegacoes_da_fala("A ação depende da minha confirmação.",
        plano={"comandos": [], "atos_explicativos": c.atos_explicativos}, origem="canal_voz")
    assert "pessoa_condicao_divergente" in r["problemas"]


@pytest.mark.parametrize("sujeito,fala", [
    ("eu", "A condição depende da sua confirmação; não criou agendamento."),
    ("eu", "Não depende da minha confirmação."),
    ("eu", 'Você escreveu "quando eu confirmar". Isso não cria agendamento.'),
    ("você", "A condição depende da minha confirmação; não criou agendamento."),
    ("nós", "Essa condição não criou agendamento."),
])
def test_explicacao_negacao_e_citacao_preservam_perspectiva(sujeito, fala):
    c = complemento(sujeito)
    r = validar_alegacoes_da_fala(fala,
        plano={"comandos": [], "atos_explicativos": c.atos_explicativos}, origem="canal_voz")
    assert "pessoa_condicao_divergente" not in r["problemas"]


def test_reparo_revalida_resposta_sem_converter_falha_em_sucesso():
    c = consulta_sem_cobertura_nuclear()
    chamadas = []
    boa = "A expressão citada é um pedido educado para abrir o aplicativo. Explicar não o abriu."
    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        fala = "A música está pausada." if len(chamadas) == 1 else boa
        return json.dumps({"trechos": [], "conversa": fala})
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert len(chamadas) == 2
    assert r.usada_llm and r.fala == boa
    assert chamadas[1][1]["_com_tools"] is False
    assert chamadas[1][1]["_contexto_fechado"] is True
    assert chamadas[1][1]["_tipo_chamada"] == "reparo_factual"
    assert chamadas[1][0][:2] == chamadas[0][0]  # contrato original, não novo resultado
    assert "resultado_operacional_sem_evidencia" in chamadas[1][0][2]["content"]
    assert "A música está pausada" not in chamadas[1][0][2]["content"]


def test_reparo_tambem_invalido_nao_e_aceito_e_nao_repete_indefinidamente():
    c = consulta_sem_cobertura_nuclear()
    chamadas = []
    def modelo(*_a, **_k):
        chamadas.append(True)
        return json.dumps({"trechos": [], "conversa": "A música está pausada."})
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert len(chamadas) == 2
    assert not r.usada_llm
    assert "A música está pausada" not in r.fala
    assert "Sem confirmação operacional." in r.fala


@pytest.mark.parametrize("trecho_reparo", ["Abri e foquei a calculadora.", "Abri a calculadora e deixei em foco."])
def test_reparo_nao_pode_modificar_receipt_da_outra_etapa(trecho_reparo):
    c = consulta_sem_cobertura_nuclear()
    receipt = ResultadoAcao(id_solicitacao="calculadora-1", intent="APP_OPEN",
        alvo="calculadora", status="aberto", executou=True, confirmado=True,
        origem="executor", params={"nome_app": "calculadora"})
    chamadas = []
    def modelo(mensagens, **_):
        chamadas.append(mensagens)
        conversa = "A música está pausada." if len(chamadas) == 1 else "A expressão é um pedido educado."
        trecho = "Abri a calculadora." if len(chamadas) == 1 else trecho_reparo
        return json.dumps({"trechos": [trecho], "conversa": conversa})
    r = personalizar_confirmacao_composta_llm([receipt], "A calculadora está aberta.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert len(chamadas) == 2
    assert not r.usada_llm
    assert "foquei" not in r.fala
    assert chamadas[0][:2] == chamadas[1][:2]


def test_abertura_sem_prova_de_foco_rejeita_alegacao_na_primeira_resposta():
    receipt = ResultadoAcao(id_solicitacao="controle-foco", intent="APP_OPEN",
        alvo="calculadora", status="aberto", executou=True, confirmado=True, origem="executor")
    r = personalizar_confirmacao_composta_llm([receipt], "A calculadora está aberta.",
        texto_conversacional="Explique o significado.",
        enviar_mensagem=lambda *_a, **_k: json.dumps({
            "trechos": ["Abri e foquei a calculadora."], "conversa": "Essa expressão é um pedido."}))
    assert not r.usada_llm


@pytest.mark.parametrize("frase,esperado", [
    ("Explicar não o abriu.", []),
    ("A descrição não fechou o arquivo.", []),
    ("Citar isso não enviou a mensagem.", []),
    ("O aplicativo não o abriu.", ["falha_operacional_sem_evidencia"]),
    ("Explicar não o abriu. O aplicativo abriu.", ["resultado_operacional_sem_evidencia"]),
    ("Explicar abriu o aplicativo.", ["resultado_operacional_sem_evidencia"]),
    ("O aplicativo não abriu.", ["falha_operacional_sem_evidencia"]),
])
def test_guardiao_distingue_limite_da_explicacao_de_resultado_narrado(frase, esperado):
    c = consulta_sem_cobertura_nuclear()
    r = validar_alegacoes_da_fala(frase, plano={"comandos": [], "texto_usuario": c.texto,
        "atos_explicativos": c.atos_explicativos}, origem="canal_voz")
    assert r["problemas"] == esperado


@pytest.mark.parametrize("status,trecho,aceita", [
    ("app_aberto", "Abri a calculadora e foquei a janela.", False),
    ("app_aberto", "Abri a calculadora e deixei a janela em primeiro plano.", False),
    ("app_aberto", "Abri a calculadora.", True),
    ("app_iniciado_focado", "Abri e foquei a calculadora.", True),
])
def test_foco_exige_prova_do_resultado_e_nao_parametro_do_pedido(status, trecho, aceita):
    receipt = ResultadoAcao(id_solicitacao="calc", intent="APP_OPEN", alvo="calculadora",
        status=status, executou=True, confirmado=True, origem="executor",
        params={"foco_confirmado": True})
    r = personalizar_confirmacao_composta_llm([receipt], "Abri a calculadora.",
        texto_conversacional="Explique o significado.",
        enviar_mensagem=lambda *_a, **_k: json.dumps({"trechos": [trecho], "conversa": "É um pedido."}))
    assert r.usada_llm is aceita, r.motivo_fallback


def test_explicacao_nao_empresta_foco_do_receipt_de_outra_parte():
    receipt = ResultadoAcao(id_solicitacao="calc", intent="APP_OPEN", alvo="calculadora",
        status="app_iniciado_focado", executou=True, confirmado=True, origem="executor")
    r = personalizar_confirmacao_composta_llm([receipt], "Iniciei a calculadora em foco.",
        texto_conversacional="Explique o significado.",
        enviar_mensagem=lambda *_a, **_k: json.dumps({
            "trechos": ["Iniciei a calculadora em foco."], "conversa": "Eu foquei o editor."}))
    assert not r.usada_llm and r.motivo_fallback == "conversa_composta_invalida:foco_sem_receipt"


def test_explicar_o_que_e_foco_nao_e_alegar_que_ele_ocorreu():
    fala = "Pôr a janela em foco significa trazê-la para a frente."
    r = personalizar_confirmacao_composta_llm([], "",
        texto_conversacional="Explique o significado.",
        enviar_mensagem=lambda *_a, **_k: json.dumps({"trechos": [], "conversa": fala}))
    assert r.usada_llm and r.fala == fala


def test_composicao_instalada_publica_so_efeito_simulado_e_explicacao_revisada(tmp_path):
    codigo = textwrap.dedent(r'''
        import json, sys
        from pathlib import Path
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from scripts.tests.test_reparo_explicativo_misto import consulta_sem_cobertura_nuclear
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao

        root = preparar_instalacao_isolada(Path(sys.argv[1]))
        root._voz_runtime.falar = lambda *_a, **_k: False
        orq = root._orquestrador_fala_runtime
        textos = []
        orq.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        c = consulta_sem_cobertura_nuclear()
        turno = classificar_modalidade_turno(c.texto_usuario)
        turno["id"] = c.turno_id
        casos = []
        for nome, status, trecho in [
            ("reparo", "app_aberto", "Abri a calculadora."),
            ("abertura", "app_aberto", "Abri e foquei a calculadora."),
            ("foco", "app_iniciado_focado", "Abri e foquei a calculadora."),
            ("ja_aberto", "app_ja_aberto_observado", "Calculadora já está aberto; não repeti a abertura."),
            ("nova_abertura_inventada", "app_ja_aberto_observado",
                "Calculadora já está aberto; não repeti a abertura. Abri a calculadora."),
        ]:
            chamadas = []
            def modelo(_mensagens, **opcoes):
                chamadas.append([opcoes["_tipo_chamada"], opcoes["_com_tools"]])
                fala = ("A música está pausada." if nome == "reparo" and len(chamadas) == 1 else
                        "É um pedido para abrir o aplicativo. Explicar não o abriu.")
                return json.dumps({"trechos": [trecho], "conversa": fala}, ensure_ascii=False)
            recibo = ResultadoAcao(id_solicitacao=nome, intent="APP_OPEN", alvo="calculadora",
                status=status, executou=status != "app_ja_aberto_observado", confirmado=True, origem="executor")
            root._estado_compartilhado_runtime.atualizar_campos("mental", turno_atual=turno,
                plano_turno_atual={"id": c.turno_id, "texto_usuario": c.texto_usuario,
                    "requer_execucao": True, "comandos": [recibo.como_dict()]})
            inicio = len(textos)
            with orq.agrupar_resultados_operacionais(texto_usuario=c.texto_usuario, enviar_mensagem=modelo) as lote:
                lote.complemento = c
                assert orq.acumular_resultado_operacional(recibo, "Abri a calculadora.")
                assert lote.resultados == [recibo]
            casos.append({"nome": nome, "chamadas": chamadas, "textos": textos[inicio:],
                "publicada": lote.resposta_publicada})
        sys.__stdout__.write("MISTO " + json.dumps(casos, ensure_ascii=False) + "\n")
    ''')
    p = subprocess.run([sys.executable, "-c", codigo, str(tmp_path)], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_IOT_MODO="simulado"),
        capture_output=True, encoding="utf-8", timeout=60)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    casos = json.loads(next(l[6:] for l in p.stdout.splitlines() if l.startswith("MISTO ")))
    reparo, abertura, foco, ja_aberto, nova_abertura = casos
    assert all(c["publicada"] and len(c["textos"]) == 1 for c in casos)
    assert reparo["chamadas"] == [["autoria_operacional", False], ["reparo_factual", False]]
    assert "Explicar não o abriu." in reparo["textos"][0] and "música está pausada" not in reparo["textos"][0]
    assert abertura["chamadas"] == foco["chamadas"] == [["autoria_operacional", False]]
    assert "Abri calculadora." in abertura["textos"][0] and "foquei" not in abertura["textos"][0]
    assert "Abri e foquei a calculadora." in foco["textos"][0]
    assert ja_aberto["chamadas"] == [["autoria_operacional", False]]
    assert "já está aberto; não repeti a abertura." in ja_aberto["textos"][0]
    assert "Explicar não o abriu." in ja_aberto["textos"][0]
    assert "Abri" not in ja_aberto["textos"][0] and "foco" not in ja_aberto["textos"][0]
    assert "já está aberto; não repeti a abertura." in nova_abertura["textos"][0]
    assert "Abri a calculadora." not in nova_abertura["textos"][0]


@pytest.mark.parametrize("mudanca", ["turno", "objeto"])
def test_lote_revalida_vigencia_depois_do_reparo(mudanca):
    c = consulta_sem_cobertura_nuclear()
    turno = classificar_modalidade_turno(c.texto_usuario, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = c.turno_id
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno})
    chamadas, publicados = [], []
    orq = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado, "print": lambda *_: None})
    orq.falar = lambda fala, *_: publicados.append(fala) or True
    def modelo(*_a, **_k):
        chamadas.append(True)
        if len(chamadas) == 1:
            return json.dumps({"trechos": [], "conversa": "A música está pausada."})
        if mudanca == "turno":
            estado.mental["turno_atual"]["id"] = "novo-turno"
        else:
            estado.mental["turno_atual"]["segmentos"][1]["contrato_explicativo"]["objeto_textual"] = "outro objeto"
        return json.dumps({"trechos": [], "conversa": "A expressão é um pedido educado para abrir o aplicativo."})
    with orq.agrupar_resultados_operacionais(texto_usuario=c.texto_usuario, enviar_mensagem=modelo) as lote:
        lote.complemento = c
    assert len(chamadas) == 2
    assert publicados == []
    assert not lote.resposta_publicada


def test_autoria_valida_nao_aciona_reparo():
    c = complemento()
    chamadas = []
    def modelo(*_a, **_k):
        chamadas.append(True)
        return json.dumps({"trechos": [], "realizacoes": [{"indice": c.indices[0], "opcao": "condicao_1"}]})
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert len(chamadas) == 1
    assert r.usada_llm


def test_prosa_fora_do_assunto_nao_e_reparada_no_canal_condicional_coberto():
    c = complemento()
    chamadas = []
    def modelo(*_a, **_k):
        chamadas.append(True)
        fala = "Vou aguardar seu sinal." if len(chamadas) == 1 else "Essa expressão é um pedido educado."
        return json.dumps({"trechos": [], "conversa": fala})
    r = personalizar_confirmacao_composta_llm([], "Sem confirmação operacional.",
        texto_conversacional=c.texto, complemento_conversacional=c, enviar_mensagem=modelo)
    assert len(chamadas) == 1
    assert not r.usada_llm
    assert r.motivo_fallback == "estrutura_nuclear_invalida"
