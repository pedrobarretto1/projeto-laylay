import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
    montar_mensagens_reparo_comunicacao,
)


RELATO = "Ontem pedi para abrir o Opera; estou só relatando."


def preparar(texto, **dados):
    plano = {"texto_usuario": texto, "comandos": [], "requer_execucao": False, **dados}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, plano=plano)
    return plano


@pytest.mark.parametrize("texto", [
    RELATO,
    "Ontem pedi para ler o relatório; estou apenas relatando.",
    "Mais cedo pedi para ligar a luz. Eu estou só contando o ocorrido.",
    "Pedi uma música ontem; tô só contando.",
])
def test_relato_explicito_recebe_reconhecimento_sem_exigir_continuacao(texto):
    contrato = preparar(texto)["contrato_fala"]
    assert contrato["roteiro_concreto"]["estrategia"] == "reconhecimento_relato_explicito"
    assert contrato["permite_pergunta"] is False
    assert contrato["autoriza_execucao"] is False


@pytest.mark.parametrize("texto, dados", [
    ("Ontem pedi para abrir o Opera. Você sabe por que falhou?", {}),
    (RELATO + " Pode explicar o que aconteceu?", {}),
    ("Você acha isso normal? Estou só relatando.", {}),
    ('Ela disse: "estou só relatando".', {}),
    ("Não estou só relatando.", {}),
    ("Ontem abri o navegador.", {}),
    (RELATO, {"requer_execucao": True}),
    (RELATO, {"atos": [{"tipo": "pergunta"}]}),
])
def test_reconhecimento_nao_sufoca_outro_ato_nem_se_aplica_a_citacao(texto, dados):
    contrato = preparar(texto, **dados)["contrato_fala"]
    assert contrato["roteiro_concreto"]["estrategia"] != "reconhecimento_relato_explicito"


def test_pergunta_historica_e_rejeitada_pelo_contrato_sem_inventar_efeito():
    avaliacao = avaliar_qualidade_comunicacao(
        RELATO, "Ah, Opera. Tá aberto?", plano=preparar(RELATO),
    )
    assert not avaliacao["aceita"]
    assert "relato_explicito_abriu_pergunta" in avaliacao["problemas"]
    assert avaliacao["requer_reparo"]


@pytest.mark.parametrize("fala", [
    "Entendi, você está contando o pedido que fez ontem.",
    "Ah, entendi. Era o pedido de ontem, não um pedido para agora.",
])
def test_reconhecimento_livre_sem_frase_obrigatoria_e_aceito(fala):
    assert avaliar_qualidade_comunicacao(RELATO, fala, plano=preparar(RELATO))["aceita"]


def test_pipeline_repara_pergunta_sem_fallback_nem_comandos():
    chamadas = []

    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        return json.dumps({"fala": "Entendi, você está contando o pedido de ontem.", "comandos": []})

    resultado = preparar_resposta_para_execucao(
        RELATO, json.dumps({"fala": "Ah, Opera. Tá aberto?", "comandos": []}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": preparar(RELATO)}, log=lambda texto: None,
    )
    assert len(chamadas) == 1
    assert chamadas[0][1]["_tipo_chamada"] == "reparo_comunicacao"
    assert resultado["fala"] == "Entendi, você está contando o pedido de ontem."
    assert resultado["comandos"] == []


def test_reparo_de_resultado_inventado_preserva_limite_do_relato():
    avaliacao = avaliar_qualidade_comunicacao(
        RELATO, "O Opera não abriu.", plano=preparar(RELATO),
    )
    mensagens = montar_mensagens_reparo_comunicacao(RELATO, "O Opera não abriu.", avaliacao)
    assert "sem perguntar" in mensagens[0]["content"]
    assert avaliacao["contrato_reparo"]["autoriza_execucao"] is False


@pytest.mark.parametrize("comando", [
    {"acao": "open_app", "alvo": "Opera"},
    {"intent": "FILE_READ", "target": "relatório"},
    {"tipo": "desconhecido"},
])
def test_proposta_sem_autoridade_nao_pula_reparo_da_fala(comando):
    chamadas = []
    fala_correta = "Entendi, você está contando o pedido de ontem."

    def modelo(mensagens, **opcoes):
        chamadas.append(opcoes)
        return json.dumps({"fala": fala_correta, "comandos": []})

    resultado = preparar_resposta_para_execucao(
        RELATO, json.dumps({"fala": "Entendi, o Opera foi aberto.", "comandos": [comando]}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": preparar(RELATO, autoriza_execucao=False)},
        log=lambda texto: None,
    )
    assert [item["_tipo_chamada"] for item in chamadas] == ["reparo_comunicacao"]
    assert resultado["fala"] == fala_correta
    assert resultado["comandos"] == []


@pytest.mark.parametrize("dados", [
    {"autoriza_execucao": True},
    {},
    {"autoriza_execucao": False, "texto_usuario": "Outro turno"},
])
def test_preparacao_nao_inventa_veto_para_pedido_atual(dados):
    texto = "Abre o Opera."
    comando = {"acao": "open_app", "alvo": "Opera"}
    resultado = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": "Vou tentar abrir.", "comandos": [comando]}),
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": {"texto_usuario": texto, **dados}},
        log=lambda texto: None,
    )
    assert resultado["comandos"] == [comando]
