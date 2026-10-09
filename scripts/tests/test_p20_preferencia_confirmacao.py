"""P20: tom leve veta ornamentação antes da autoria, sem mudar o receipt."""

from __future__ import annotations

from copy import deepcopy
import inspect
import json
import time

import pytest

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.cognicao.preferencia_humor import extrair_preferencia_humor
from mente_laylay.emocoes.avaliador_eventos import (
    AvaliadorEventosEmocionaisRuntime,
    contextualizar_fala_evento,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import (
    personalizar_confirmacao_llm,
    personalizar_informacao_llm,
)
from mente_laylay.personalidade.fala_operacional import estilizar_fala_operacional
from mente_laylay.personalidade.falas_variadas import fala_por_estado_acao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


@pytest.fixture(autouse=True)
def habilitar_autoria(monkeypatch):
    # O controle não pode ficar verde porque a porta de autoria está desligada.
    monkeypatch.setenv("LAYLAY_CONFIRMACOES_LLM", "1")


def _contexto(pedido: str = "pega leve hoje nos comandos", *, jogo: bool = False,
              idade: float = 1.0) -> dict:
    preferencia = extrair_preferencia_humor(
        pedido, turno_id="p20-confirmacao", agora=time.time() - idade)
    return {
        "preferencias_humor_contextuais": {
            preferencia["contexto"]: preferencia} if preferencia else {},
        "preferencia_humor_contextual": preferencia,
        "modo_jogo_ativo": jogo,
    }


def _resultado(intent: str = "APP_OPEN", status: str = "app_focado",
               alvo: str = "Calculadora", *, confirmado: bool = True,
               executou: bool = True, params: dict | None = None,
               ocorrencia: str = "") -> ResultadoAcao:
    return ResultadoAcao(
        intent=intent, status=status, alvo=alvo, params=dict(params or {}),
        executou=executou, confirmado=confirmado, origem="executor",
        id_solicitacao="p20:" + intent + ":" + status + ":" + ocorrencia,
        texto_usuario="execute o pedido em " + alvo,
    )


def _com_contexto(funcao, *args, contexto: dict, **kwargs):
    assert "contexto" in inspect.signature(funcao).parameters, (
        f"{funcao.__name__} precisa consumir a preferência antes de ornamentar")
    return funcao(*args, contexto=contexto, **kwargs)


def _modelo_proibido(chamadas: list):
    def modelo(*args, **kwargs):
        chamadas.append((args, kwargs))
        raise AssertionError("o veto de tom leve deve preceder a chamada de autoria")
    return modelo


@pytest.mark.parametrize("pedido", ["pega leve hoje", "pega leve hoje nos comandos"])
@pytest.mark.parametrize("status,alvo,factual", [
    ("app_focado", "Calculadora", "Trouxe Calculadora para o foco."),
    ("ja_aberto_focado", "Opera", "Opera já está aberto e em foco; não repeti a abertura."),
    ("volume_ajustado", "volume", "Não tenho confirmação de que a ação em volume chegou a ser executada."),
    ("falha_execucao", "anotações.txt", "Não consegui salvar anotações.txt."),
])
def test_gerador_de_estado_com_tom_leve_preserva_fala_factual(
    pedido: str, status: str, alvo: str, factual: str,
) -> None:
    fala = fala_por_estado_acao(
        status, fallback=factual, alvo=alvo, contexto=_contexto(pedido))
    assert fala == factual


@pytest.mark.parametrize("intent,status,alvo,factual", [
    ("APP_OPEN", "app_focado", "Calculadora", "Trouxe Calculadora para o foco."),
    ("IOT_CONTROL", "ligado", "ventilador", "Liguei ventilador."),
    ("SET_VOLUME", "volume_ajustado", "volume", "Ajustei o volume para 27%."),
    ("CREATE_FILE", "arquivo_criado", "anotações.txt", "Criei anotações.txt."),
])
def test_estilizador_com_tom_leve_preserva_alvo_status_e_numero(
    intent: str, status: str, alvo: str, factual: str,
) -> None:
    resultado = _resultado(intent, status, alvo)
    antes = deepcopy(resultado.como_dict())
    fala = _com_contexto(
        estilizar_fala_operacional, resultado, factual, classe="sucesso",
        contexto=_contexto(), emocao="debochada")
    assert fala == factual
    assert resultado.como_dict() == antes


@pytest.mark.parametrize("intent,status,alvo,factual", [
    ("APP_OPEN", "app_focado", "Calculadora", "Trouxe Calculadora para o foco."),
    ("IOT_CONTROL", "ligado", "ventilador", "Liguei ventilador."),
])
def test_planejador_com_tom_leve_nao_reintroduz_ornamentacao(
    intent: str, status: str, alvo: str, factual: str,
) -> None:
    resultado = _resultado(intent, status, alvo)
    plano = _com_contexto(
        planejar_resposta_acao, resultado, factual, contexto=_contexto(),
        emocao_preferida="debochada", nivel_preferido=2)
    assert plano.classe == "sucesso"
    assert plano.fala == factual


@pytest.mark.parametrize("pedido", ["pega leve hoje", "pega leve hoje nos comandos"])
@pytest.mark.parametrize("intent,status,alvo,factual,classe", [
    ("APP_OPEN", "app_focado", "Calculadora", "Trouxe Calculadora para o foco.", "sucesso"),
    ("IOT_CONTROL", "ligado", "ventilador", "Liguei ventilador.", "sucesso"),
    ("CREATE_FILE", "falha_execucao", "anotações.txt", "Não consegui salvar anotações.txt.", "falha"),
])
def test_tom_leve_veta_autoria_antes_do_modelo_e_preserva_resultado(
    pedido: str, intent: str, status: str, alvo: str, factual: str, classe: str,
) -> None:
    resultado = _resultado(
        intent, status, alvo, confirmado=classe == "sucesso", executou=classe == "sucesso")
    antes = deepcopy(resultado.como_dict())
    chamadas = []
    confirmacao = personalizar_confirmacao_llm(
        resultado, factual, classe=classe, emocao="calma", nivel=1,
        enviar_mensagem=_modelo_proibido(chamadas), contexto=_contexto(pedido))
    assert chamadas == [], "capturar a exceção do modelo não prova veto anterior à autoria"
    assert confirmacao.fala == factual
    assert confirmacao.usada_llm is False
    assert resultado.como_dict() == antes


@pytest.mark.parametrize("factual", [
    "Ventilador está ligado, com velocidade 2.",
    "Encontrei 3 arquivos: anotações.txt, aula.md e provas.pdf.",
    'Arquivo encontrado: "pode me zoar mais.txt", com 27 linhas.',
])
def test_tom_leve_veta_autoria_informativa_antes_do_modelo_preservando_fatos(factual: str) -> None:
    chamadas = []
    confirmacao = personalizar_informacao_llm(
        factual, fatos_obrigatorios=[factual], enviar_mensagem=_modelo_proibido(chamadas),
        contexto=_contexto())
    assert chamadas == []
    assert confirmacao.fala == factual
    assert confirmacao.usada_llm is False


def _evento_repetido(intent: str, alvo: str, *, falha: bool = False):
    avaliador = AvaliadorEventosEmocionaisRuntime(log=lambda *_: None)
    status = "falha_execucao" if falha else (
        "ja_aberto_focado" if intent == "APP_OPEN" else "ja_estava_ligado")
    evento = {}
    for indice in range(4):
        resultado = _resultado(
            intent, status, alvo, executou=False, confirmado=not falha, ocorrencia=str(indice))
        evento = avaliador.avaliar(resultado)
    assert evento["permite_expressao"] is True
    return resultado, evento


@pytest.mark.parametrize("intent,alvo", [("APP_OPEN", "Calculadora"), ("IOT_CONTROL", "ventilador")])
@pytest.mark.parametrize("falha", [False, True])
def test_tom_leve_no_jogo_suspende_tirada_causal_preservando_verdade(
    intent: str, alvo: str, falha: bool,
) -> None:
    resultado, evento = _evento_repetido(intent, alvo, falha=falha)
    factual = f"Não consegui executar o pedido em {alvo}." if falha else (
        f"{alvo} já estava como pedido; não repeti a ação.")
    antes = deepcopy(evento)
    fala = _com_contexto(
        contextualizar_fala_evento, factual, evento, alvo=alvo,
        contexto=_contexto("pega leve hoje", jogo=True))
    assert fala == factual
    assert evento == antes
    assert resultado.confirmado is (not falha)


@pytest.mark.parametrize("pedido,idade", [
    ("", 1.0),
    ("pode me zoar mais hoje nos comandos", 1.0),
    ("pega leve hoje nos comandos", 86401.0),
    ("pega leve hoje na conversa", 1.0),
    ('escreva "pega leve hoje" no arquivo', 1.0),
])
def test_ausencia_abertura_expiracao_outro_escopo_e_citacao_preservam_autoria_legitima(
    pedido: str, idade: float,
) -> None:
    resultado = _resultado()
    chamadas = []
    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        return json.dumps({"fala": "Trouxe Calculadora para o foco.",
                           "status": resultado.status, "alvo": resultado.alvo,
                           "emocao": "calma", "nivel": 1})
    confirmacao = personalizar_confirmacao_llm(
        resultado, "Trouxe Calculadora para o foco.", classe="sucesso", emocao="calma", nivel=1,
        enviar_mensagem=modelo, contexto=_contexto(pedido, idade=idade))
    assert len(chamadas) == 1
    assert confirmacao.usada_llm is True
    assert confirmacao.fala == "Trouxe Calculadora para o foco."


def test_mais_humor_nao_promove_falha_a_sucesso_ou_outro_alvo() -> None:
    resultado = _resultado("CREATE_FILE", "falha_execucao", "anotações.txt", executou=False, confirmado=False)
    factual = "Não consegui salvar anotações.txt."
    chamadas = []
    def modelo(*args, **kwargs):
        chamadas.append((args, kwargs))
        return json.dumps({"fala": "Criei notas.txt.", "status": "arquivo_criado",
                           "alvo": "notas.txt", "emocao": "debochada", "nivel": 3})
    confirmacao = personalizar_confirmacao_llm(
        resultado, factual, classe="falha", emocao="calma", nivel=1,
        enviar_mensagem=modelo, contexto=_contexto("pode me zoar mais hoje nos comandos"))
    assert chamadas
    assert confirmacao.usada_llm is False
    assert confirmacao.fala == factual
    assert resultado.confirmado is False and resultado.executou is False


def test_mais_humor_nao_revive_causa_expirada_no_jogo() -> None:
    _, evento = _evento_repetido("APP_OPEN", "Calculadora")
    expirado = {**evento, "validade": {**evento["validade"], "expira_ts": time.time() - 1.0}}
    factual = "Calculadora já estava em foco; não repeti a ação."
    fala = _com_contexto(
        contextualizar_fala_evento, factual, expirado, alvo="Calculadora",
        contexto=_contexto("pode me zoar mais hoje", jogo=True))
    assert fala == factual


def test_mais_humor_nao_certifica_causa_de_outra_ocorrencia() -> None:
    _, evento = _evento_repetido("APP_OPEN", "Calculadora")
    resultado = _resultado()
    chamadas = []
    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        return json.dumps({"fala": "Trouxe Calculadora para o foco.",
                           "status": resultado.status, "alvo": resultado.alvo,
                           "emocao": "calma", "nivel": 1})
    contexto = _contexto("pode me zoar mais hoje nos comandos")
    contexto["avaliacao_evento"] = evento
    personalizar_confirmacao_llm(
        resultado, "Trouxe Calculadora para o foco.", classe="sucesso", emocao="calma", nivel=1,
        enviar_mensagem=modelo, contexto=contexto)
    assert len(chamadas) == 1
    contrato = json.loads(chamadas[0][0][1]["content"])
    assert contrato["reacao_causal"]["permite_expressao"] is False


def test_adaptador_transporta_preferencia_selecionada_e_mapa_sem_mutar_owner() -> None:
    contexto = _contexto()
    antes = deepcopy(contexto)
    adaptador = AdaptadorResultadoOperacional(
        resultado={"intent": "APP_OPEN"}, params={"nome_app": "Calculadora"},
        texto_original="abra a calculadora", destino="pc_a", ctx=contexto)
    fala = adaptador.contexto_fala()
    assert fala.get("preferencias_humor_contextuais") == contexto["preferencias_humor_contextuais"]
    assert fala.get("preferencia_humor_contextual") == contexto["preferencia_humor_contextual"]
    assert contexto == antes


def test_tom_leve_na_alternancia_de_reproducao_nao_inventa_pausa() -> None:
    from mente_laylay.autonomia.controle_midia import executar_media_control
    from scripts.tests.test_controle_midia_confirmacao import _ctx_base

    falas, receipts = [], []
    enviado = []
    contexto = _contexto()
    ctx = _ctx_base(
        enviar_chrome=lambda _acao, dados: enviado.append(dados["command"]) or True,
        falas=falas,
    )
    assert executar_media_control(
        {"acao": "pause_play", "platform": "music"}, "alterna a reprodução", "pc_a", ctx,
        marcar_resultado=lambda status, executou=None, confirmado=None, **_k:
            receipts.append((status, executou, confirmado)),
        falar_por_status=lambda *_a, **_k: None, ctx_fala=lambda: contexto,
    ) is True
    assert enviado == ["pause_play"]
    assert receipts == [("midia_pause_play", True, True)]
    assert len(falas) == 1
    assert "alternada" in falas[0]
    assert "pausei" not in falas[0].casefold()
    assert "retomei" not in falas[0].casefold()


@pytest.mark.parametrize("acao", ("next", "prev"))
@pytest.mark.parametrize("ok", (True, False))
def test_playlist_interna_consumir_tom_leve_antes_da_variacao(monkeypatch, acao, ok) -> None:
    from types import SimpleNamespace
    from mente_laylay.autonomia import controle_midia
    from scripts.tests.test_controle_midia_confirmacao import _ctx_base

    falas, receipts, pedidos = [], [], []
    def pedir(tipo):
        pedidos.append(tipo)
        return ok
    porta = SimpleNamespace(
        estado=lambda: {"playlist_ativa": "lista"},
        avancar_proxima=lambda: pedir("next"), voltar_anterior=lambda: pedir("prev"),
    )
    # Somente a escolha aleatória é controlada; o consumidor e a política são reais.
    monkeypatch.setattr(controle_midia, "_escolher_fala_variada", lambda opcoes: opcoes[0])
    assert controle_midia.executar_media_control(
        {"acao": acao, "platform": "music"}, "mude a faixa", "pc_a",
        {**_ctx_base(enviar_chrome=None, falas=falas), "_registro_musica_operacoes_runtime": porta},
        marcar_resultado=lambda status, executou=None, **_k: receipts.append((status, executou)),
        falar_por_status=lambda *_a, **_k: None, ctx_fala=lambda: _contexto(),
    ) is ok
    assert pedidos == [acao]
    assert receipts == [(f"midia_{acao}_playlist" if ok else "falha_execucao", ok)]
    esperado = (
        "Pedi a próxima faixa da playlist." if acao == "next" else "Pedi a faixa anterior da playlist."
    ) if ok else (
        "Não consegui avançar a playlist." if acao == "next" else "Não consegui voltar na playlist."
    )
    assert falas == [esperado]


@pytest.mark.parametrize("intent,status,alvo,factual", [
    ("IOT_CONTROL", "brilho_ajustado", "lâmpada", "Ajustei o brilho de lâmpada para 27%."),
    ("SET_VOLUME", "volume_ajustado", "volume", "Ajustei o volume para 27%."),
])
@pytest.mark.parametrize("confirmado", [True, False, None])
def test_gerador_consume_receipt_em_vez_de_reinferir_confirmacao_por_status(
    intent: str, status: str, alvo: str, factual: str, confirmado: bool | None,
) -> None:
    receipt = _resultado(intent, status, alvo, confirmado=confirmado)
    antes = deepcopy(receipt.como_dict())
    fala = fala_por_estado_acao(
        status, fallback="Pronto. " + factual, alvo=alvo, contexto=_contexto(),
        resultado=receipt)
    assert receipt.como_dict() == antes
    if confirmado is True:
        assert fala == "Pronto. " + factual
    else:
        assert "Pronto" not in fala
        assert "27%" not in fala
        assert alvo in fala


def test_status_otimista_sem_receipt_nao_e_promovido_a_confirmacao() -> None:
    fala = fala_por_estado_acao(
        "brilho_ajustado", fallback="Pronto. Ajustei o brilho para 27%.",
        alvo="lâmpada", contexto=_contexto())
    assert "Pronto" not in fala
    assert "27%" not in fala
    assert "lâmpada" in fala
