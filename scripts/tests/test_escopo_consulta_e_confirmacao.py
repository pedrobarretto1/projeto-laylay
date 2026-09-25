"""Contexto referencia uma consulta; não amplia fatos de outro receipt."""
import json
import time

import pytest

from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
from mente_laylay.autonomia.executor_informacoes import DependenciasExecutorInformacoes, executar_intencao_informacoes
from mente_laylay.memoria_mental.continuidade_geral import registrar_evento_continuidade
from mente_laylay.memoria_mental.memoria_confiavel import normalizar_texto
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_llm


def _estado():
    return registrar_evento_continuidade({}, evento="acao", intent="WEATHER",
        params={"local": "Boituva", "day_offset": 1}, status="previsao_consultada")


def _detectar(texto, estado):
    return detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado,
        "detectar_intencao_iot": lambda *_: None,
    })


@pytest.mark.parametrize("texto", ["mas é garantia que vai chover?", "mas é certeza que vai chover?", "é garantido que chove?"])
def test_pergunta_sobre_certeza_preserva_escopo_da_consulta(texto):
    estado = _estado()
    assert estado["continuidade_geral"]["dominios"]["clima"]["params"] == {"local": "Boituva", "day_offset": 1}
    comando = _detectar(texto, estado)
    assert comando["intent"] == "WEATHER"
    assert comando["params"]["day_offset"] == 1
    assert comando["params"]["local"] == "Boituva"
    chamadas, falas, resultados = [], [], []

    def obter(local, *, day_offset):
        chamadas.append((local, day_offset))
        return {"ok": True, "localidade": local, "day_offset": day_offset,
                "chance_chuva_pct": 27, "temperatura_c": 27, "sensacao_c": 28, "umidade": 51}

    executar_intencao_informacoes("WEATHER", comando["params"], texto,
        {"obter_clima_localidade": obter, "falar_com_lipsync": lambda f, *_: falas.append(f)},
        DependenciasExecutorInformacoes(lambda *a, **k: resultados.append((a, k)), lambda *_: None, lambda *_: None))
    assert chamadas == [("Boituva", 1)]
    assert "não é garantia" in falas[0].lower()
    assert "amanhã" in falas[0].lower() and "27%" in falas[0]
    assert not any(t in falas[0].lower() for t in ("hoje", "sensação", "umidade", "graus"))
    assert resultados[-1][1]["confirmado"] is True


@pytest.mark.parametrize("alteracao", ["expirado", "outro_assunto", "nova_consulta", "hoje_explicito", "outro_local"])
def test_contexto_climatico_nao_substitui_pedido_atual(alteracao):
    estado = _estado()
    texto = "mas é garantia que vai chover?"
    if alteracao == "expirado":
        estado["continuidade_geral"]["dominios"]["clima"]["expira_em"] = time.time() - 1
    elif alteracao == "outro_assunto":
        estado = registrar_evento_continuidade(estado, evento="acao", intent="PLAYLIST_ADD", alvo="rock")
    elif alteracao == "nova_consulta":
        texto = "vai chover hoje?"
    elif alteracao == "hoje_explicito":
        texto = "mas é garantia que vai chover hoje?"
    else:
        texto = "é garantia que vai chover em Campinas?"
    comando = _detectar(texto, estado)
    assert comando["params"].get("day_offset", 0) == 0
    if alteracao == "outro_local":
        assert comando["params"]["local"] == "campinas"


@pytest.mark.parametrize("intent,status,alvo,segura", [
    ("PLAYLIST_ADD", "playlist_musica_adicionada", "yago", "Salvei Viver ta Osso em yago."),
    ("IOT_CONTROL", "desligado", "lâmpada", "Desliguei a lâmpada."),
    ("CREATE_FOLDER", "pasta_criada", "estudos", "Criei a pasta estudos."),
])
def test_autoria_isola_historico_e_repara_fatos_numericos_alheios(intent, status, alvo, segura):
    historico = "O tempo aqui em Boituva está limpo, 27 graus, sensação de 28."
    resultado = normalizar_resultado_acao({"intent": intent, "status": status, "alvo": alvo,
                                         "executou": True, "confirmado": True})
    chamadas = []

    def modelo(msgs, **opcoes):
        chamadas.append((msgs, opcoes))
        return (segura + " O tempo aqui em Boituva tá limpo, 27 graus, sente quase 28 — é um dia de sol.") if len(chamadas) == 1 else segura

    resposta = personalizar_confirmacao_llm(resultado, segura, classe="sucesso", emocao="calma", nivel=1,
        enviar_mensagem=modelo, contexto={"ultima_resposta": historico, "falas_recentes": [historico]})
    assert len(chamadas) == 2
    assert resposta.usada_llm and resposta.fala == segura
    for msgs, opcoes in chamadas:
        assert "Boituva" not in json.dumps(msgs, ensure_ascii=False)
        assert opcoes["_contexto_fechado"] is True


@pytest.mark.parametrize("probabilidade", [0, 100, None])
def test_previsao_nao_vira_garantia_nos_extremos_ou_sem_probabilidade(probabilidade):
    falas = []
    executar_intencao_informacoes("WEATHER", {"day_offset": 1}, "é certeza que vai chover?", {
        "obter_clima_localidade": lambda *a, **k: {"ok": True, "chance_chuva_pct": probabilidade},
        "falar_com_lipsync": lambda f, *_: falas.append(f),
    }, DependenciasExecutorInformacoes(lambda *a, **k: None, lambda *_: None, lambda *_: None))
    assert "Não é garantia" in falas[0]
    assert "amanhã" in falas[0]
    if probabilidade is None:
        assert "não informou" in falas[0] and "%" not in falas[0]
    else:
        assert f"{probabilidade}%" in falas[0]


def test_fonte_indisponivel_nao_confirma_nem_inventa_probabilidade():
    falas, resultados = [], []
    executar_intencao_informacoes("WEATHER", {"day_offset": 1}, "é certeza que vai chover?", {
        "obter_clima_localidade": lambda *a, **k: {"ok": False},
        "falar_com_lipsync": lambda f, *_: falas.append(f),
    }, DependenciasExecutorInformacoes(lambda *a, **k: resultados.append(k), lambda *_: None, lambda *_: None))
    assert falas and "%" not in falas[0]
    assert resultados[-1]["confirmado"] is False


@pytest.mark.parametrize("anexo", ["", " Quer mais alguma coisa?"])
def test_fato_numerico_sem_evidencia_nao_passa_apos_limpeza(anexo):
    resultado = normalizar_resultado_acao({"intent": "PLAYLIST_ADD", "alvo": "yago",
        "status": "playlist_musica_adicionada", "executou": True, "confirmado": True})
    chamadas = []

    def modelo(*a, **k):
        chamadas.append(True)
        return "Salvei a música em yago. Lá fora está 27 graus." + anexo

    resposta = personalizar_confirmacao_llm(resultado, "Salvei a música em yago.", classe="sucesso",
        emocao="calma", nivel=1, enviar_mensagem=modelo)
    assert len(chamadas) == 2
    assert not resposta.usada_llm and resposta.fala == "Salvei a música em yago."


def test_numero_do_receipt_e_humor_curto_sao_preservados():
    resultado = normalizar_resultado_acao({"intent": "VOLUME", "alvo": "volume",
        "status": "volume_ajustado", "params": {"volume": 27}, "executou": True, "confirmado": True})
    resposta = personalizar_confirmacao_llm(resultado, "Ajustei o volume para 27%.", classe="sucesso",
        emocao="calma", nivel=1, enviar_mensagem=lambda *a, **k: "Ajustei o volume para 27%. Sem sustos agora.")
    assert resposta.usada_llm and "27%" in resposta.fala and "Sem sustos" in resposta.fala


def test_composicao_root_publica_escopo_e_prepara_autoria_sem_historico(monkeypatch):
    """Importa o composition root real; só transporte externo é controlado.

    Não inicia main, serviços, voz, dispositivos ou escrita de playlist. O
    receipt sintético serve para testar publicação/continuidade, não efeito.
    """
    import importlib
    import requests

    root = importlib.import_module("laylay")
    monkeypatch.setattr(root._estado_compartilhado_runtime, "mental", {})
    root._registrar_resultado_execucao_base({
        "intent": "WEATHER", "params": {"local": "Boituva", "day_offset": 1},
        "status": "previsao_consultada", "executou": True, "confirmado": True,
    }, texto="vai chover amanhã em Boituva?")
    comando = root.detectar_intencao_deterministica("mas é garantia que vai chover?")
    assert comando["params"]["day_offset"] == 1
    assert comando["params"]["local"] == "Boituva"

    payloads = []

    def post(_headers, data, **_kwargs):
        payloads.append(data)
        resposta = requests.Response()
        resposta.status_code = 200
        resposta._content = json.dumps({"choices": [{"message": {"content": "Salvei a música em yago."}}]}).encode()
        return resposta

    monkeypatch.setattr(root._cliente_llm_runtime.servico.cliente, "post_chat", post)
    preparador = root._cliente_llm_runtime.servico.preparador

    def proibido():
        raise AssertionError("autoria isolada consultou contexto global")

    for nome in ("resumo_do_dia_getter", "contexto_logs_getter", "contexto_sistema_getter", "data_atual_getter"):
        monkeypatch.setattr(preparador, nome, proibido)
    resultado = normalizar_resultado_acao({"intent": "PLAYLIST_ADD", "alvo": "yago",
        "status": "playlist_musica_adicionada", "executou": True, "confirmado": True})
    resposta = personalizar_confirmacao_llm(resultado, "Salvei a música em yago.", classe="sucesso",
        emocao="calma", nivel=1, enviar_mensagem=root._registro_modelo_llm_runtime.enviar,
        contexto={"ultima_resposta": "Agora em Boituva está 27 graus."})
    assert resposta.usada_llm and resposta.fala == "Salvei a música em yago."
    assert len(payloads) == 1
    assert "Boituva" not in json.dumps(payloads, ensure_ascii=False)
