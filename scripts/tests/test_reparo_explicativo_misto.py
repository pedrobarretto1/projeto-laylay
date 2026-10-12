"""Reparo autoral é read-only e não troca a pessoa da condição."""
import json

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
    assert "estado_atual_sem_evidencia" in chamadas[1][0][2]["content"]
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


def test_alegacao_de_foco_sem_receipt_permanece_red_tambem_sem_reparo():
    receipt = ResultadoAcao(id_solicitacao="controle-foco", intent="APP_OPEN",
        alvo="calculadora", status="aberto", executou=True, confirmado=True, origem="executor")
    r = personalizar_confirmacao_composta_llm([receipt], "A calculadora está aberta.",
        texto_conversacional="Explique o significado.",
        enviar_mensagem=lambda *_a, **_k: json.dumps({
            "trechos": ["Abri e foquei a calculadora."], "conversa": "Essa expressão é um pedido."}))
    assert not r.usada_llm


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
