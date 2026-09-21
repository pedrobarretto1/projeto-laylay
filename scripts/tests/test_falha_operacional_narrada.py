"""Falha alegada exige fonte; ausência de receipt não prova insucesso."""

import json
import time

import pytest

from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao,
)
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt


RELATO = "Ontem pedi para abrir o Opera; estou só relatando."
HISTORICA = "Ah, o Opera. Só que não abriu. Foi só um erro de conexão, ou foi só o que você queria ver?"


def plano(texto=RELATO, comandos=()):
    return {"texto_usuario": texto, "comandos": list(comandos),
            "requer_execucao": False, "autoriza_execucao": False}


@pytest.mark.parametrize("fala", [
    HISTORICA, "Não consegui abrir o Opera.", "O Opera não abriu.",
    "O arquivo não foi salvo.", "O e-mail não foi enviado.",
    "A lâmpada não ligou.", "A abertura falhou por erro de conexão.",
    "Não sei o resultado, mas o Opera não abriu.",
    "Por que o Opera não abriu?",
    "O Opera não abriu, né?",
])
def test_resultado_negativo_sem_fonte_exige_reparo_e_nao_fallback(fala):
    resultado = verificar_fala_turno(fala, plano=plano(), origem="ia_final")
    assert resultado["aceita"] is False
    assert resultado["acao"] == "reparar"
    assert "falha_operacional_sem_evidencia" in resultado["problemas"]


@pytest.mark.parametrize("fala", [
    "Entendi, você está relatando o pedido de ontem.",
    "E o Opera chegou a abrir?", "O Opera não abriu?",
    "Não sei se o Opera não abriu.",
    "Se o Opera não abriu, podemos investigar.",
    "Não executei essa ação.", "Não consegui confirmar se a janela está aberta.",
    "Essa ação não foi executada nem confirmada.",
    "Não consegui dormir ontem.",
])
def test_pergunta_hipotese_e_nao_execucao_nao_sao_falha_observada(fala):
    resultado = avaliar_qualidade_comunicacao(RELATO, fala, plano=plano())
    assert "falha_operacional_sem_evidencia" not in resultado["problemas"]


@pytest.mark.parametrize("texto,fala", [
    ("O Opera não abriu.", "Pelo que você contou, o Opera não abriu."),
    ('Explique a frase "o arquivo não foi salvo".',
     'A frase "o arquivo não foi salvo" descreve um resultado negativo.'),
])
def test_relato_atribuido_e_citacao_literal_preservados(texto, fala):
    resultado = avaliar_qualidade_comunicacao(texto, fala, plano=plano(texto))
    assert "falha_operacional_sem_evidencia" not in resultado["problemas"]


@pytest.mark.parametrize("texto,fala", [
    ("O Opera não abriu?", "O Opera não abriu."),
    ("Se o Opera não abriu, investigamos.", "O Opera não abriu."),
    ('Explique "o Opera não abriu".', "O Opera não abriu."),
    ("O Firefox não abriu.", "O Opera não abriu."),
    ("O Opera não abriu.", "O Opera não abriu por erro de conexão."),
])
def test_fonte_nao_libera_outro_alvo_causa_ou_modalidade(texto, fala):
    resultado = avaliar_qualidade_comunicacao(texto, fala, plano=plano(texto))
    assert "falha_operacional_sem_evidencia" in resultado["problemas"]


def receipt(**mudancas):
    return {"intent": "APP_OPEN", "alvo": "Opera", "origem": "executor",
            "status": "falha_abertura", "executou": False, "confirmado": False,
            "detalhe": "O Opera não abriu.", **mudancas}


def test_receipt_de_falha_preserva_somente_o_resultado_documentado():
    estado = plano("Abre o Opera", [receipt()])
    for fala, bloqueada in [("O Opera não abriu.", False),
                            ("O Firefox não abriu.", True),
                            ("O Opera não abriu por erro de conexão.", True)]:
        resultado = avaliar_qualidade_comunicacao(estado["texto_usuario"], fala, plano=estado)
        assert ("falha_operacional_sem_evidencia" in resultado["problemas"]) is bloqueada


@pytest.mark.parametrize("comando", [
    receipt(origem="llm"), receipt(status="aguardando_confirmacao"),
    receipt(status="aberto", executou=True, confirmado=True),
    {"intent": "APP_OPEN", "confirmado": False},
])
def test_receipt_pendente_sucesso_ou_proposta_nao_prova_falha(comando):
    estado = plano("Abre o Opera", [comando])
    resultado = avaliar_qualidade_comunicacao(estado["texto_usuario"], "O Opera não abriu.", plano=estado)
    assert "falha_operacional_sem_evidencia" in resultado["problemas"]


def test_reparo_recebe_contrato_sem_inventar_falha_ou_executar():
    avaliacao = avaliar_qualidade_comunicacao(RELATO, HISTORICA, plano=plano())
    mensagens = montar_mensagens_reparo_comunicacao(RELATO, HISTORICA, avaliacao)
    contrato = json.loads(mensagens[1]["content"])["contrato_de_reparo"]
    assert contrato["resultado_operacional_desconhecido"] is True
    assert contrato["autoriza_execucao"] is False


def test_posprocessador_real_repara_rascunho_antes_de_entregar():
    chamadas = []
    def modelo(mensagens, **opcoes):
        chamadas.append(opcoes)
        return json.dumps({"fala": "Entendi, você está relatando o pedido de ontem.", "comandos": []})
    resultado = preparar_resposta_para_execucao(
        RELATO, json.dumps({"fala": HISTORICA, "comandos": []}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano()}, log=lambda texto: None,
    )
    assert len(chamadas) == 1
    assert chamadas[0]["_tipo_chamada"] == "reparo_comunicacao"
    assert resultado["fala"] == "Entendi, você está relatando o pedido de ontem."
    assert resultado["comandos"] == []


@pytest.mark.parametrize("fala", [
    "O Opera foi aberto, então tá tudo bem — você só quer dizer que o app tá funcionando.",
    "O Firefox abriu.", "O arquivo foi salvo.", "O e-mail foi enviado.",
    "A lâmpada ligou.", "A abertura funcionou.",
    "Eu já tinha aberto a janela para você.",
    "Eu havia enviado o arquivo.",
    "Só que eu já tinha aberto antes, né?",
    "O arquivo foi salvo, certo?",
])
def test_sucesso_narrado_tambem_exige_fonte(fala):
    resultado = verificar_fala_turno(fala, plano=plano(), origem="ia_final")
    assert resultado["aceita"] is False
    assert "resultado_operacional_sem_evidencia" in resultado["problemas"]


def test_composicao_publica_rejeicao_no_estado_real_sem_efeito():
    estado = EstadoCompartilhadoRuntime(mental={"plano_turno_atual": plano()})
    runtime = ComposicaoTurnoRuntime(servicos={
        "_estado_compartilhado_runtime": estado,
        "_verificar_fala_turno_mente": verificar_fala_turno,
        "_contexto_horario_atual": lambda: "tarde", "time": time,
        "print": lambda *args: None,
    })
    resultado = runtime.verificar_fala(HISTORICA, origem="ia_final")
    assert resultado["aceita"] is False
    assert estado.mental["plano_turno_atual"]["ultima_verificacao"] == resultado
    assert estado.mental["plano_turno_atual"]["comandos"] == []
    assert estado.mental["metricas_verificador"]["problema:falha_operacional_sem_evidencia"] == 1


@pytest.mark.parametrize("resposta", [
    {"fala": HISTORICA, "comandos": []},
    {"fala": "Entendi seu relato.", "comandos": [{"acao": "open_app", "alvo": "Opera"}]},
])
def test_reparo_invalido_nao_libera_rascunho_nem_comando(resposta):
    resultado = preparar_resposta_para_execucao(
        RELATO, json.dumps({"fala": HISTORICA, "comandos": []}),
        enviar_mensagem_cb=lambda *args, **kwargs: json.dumps(resposta),
        limpar_texto_fala_cb=lambda texto: texto, fallback_fala="Contingência",
        memoria_sqlite=None, contexto_comunicacao={"plano_turno": plano()}, log=lambda texto: None,
    )
    assert resultado["fala"]
    assert resultado["fala"] != HISTORICA
    assert resultado["comandos"] == []
    assert avaliar_qualidade_comunicacao(RELATO, resultado["fala"], plano=plano())["aceita"]


def test_receipt_confirmado_sustenta_sucesso_mas_nao_falha():
    estado = plano("Abre o Opera", [receipt(
        status="aberto", executou=True, confirmado=True, detalhe="O Opera foi aberto.",
    )])
    resultado = avaliar_qualidade_comunicacao(estado["texto_usuario"], "O Opera foi aberto.", plano=estado)
    assert resultado["aceita"]
    resultado = avaliar_qualidade_comunicacao(estado["texto_usuario"], "O Opera não abriu.", plano=estado)
    assert not resultado["aceita"]


@pytest.mark.parametrize("compacto", [False, True])
def test_geracao_inicial_distingue_pedido_de_resultado(compacto):
    contrato = construir_contrato_semantico_fala(RELATO, plano=plano())
    prompt = formatar_contrato_fala_para_prompt(contrato, compacto=compacto)
    assert "pedido não prova tentativa nem resultado" in prompt
    assert "falas antigas da assistente não são comprovantes" in prompt


@pytest.mark.parametrize("fala", [
    "Então você só quer dizer que o Opera tá aberto, né?",
    "O navegador está aberto.", "O processo está rodando.",
    "Não sei se o processo está rodando, mas a janela está aberta.",
])
def test_relato_nao_sustenta_estado_observavel_narrado(fala):
    resultado = verificar_fala_turno(fala, plano=plano(), origem="ia_final")
    assert not resultado["aceita"]
    assert "resultado_operacional_sem_evidencia" in resultado["problemas"]


@pytest.mark.parametrize("fala", [
    "Não sei se o navegador está aberto.", "O navegador está aberto?",
    "Me diga se o navegador está aberto.",
    "Se o navegador está aberto, podemos conversar sobre ele.",
])
def test_incerteza_e_pedido_sobre_estado_nao_sao_alegacoes(fala):
    resultado = avaliar_qualidade_comunicacao(RELATO, fala, plano=plano())
    assert "resultado_operacional_sem_evidencia" not in resultado["problemas"]
