from __future__ import annotations

import pytest
from pathlib import Path

from mente_laylay.integracao.navegador_runtime import (
    criar_navegador_leitura_runtime,
    criar_navegador_operacoes_runtime,
)
from mente_laylay.integracao.composicao_contextos_ia import (
    _sanitizar_aba_para_prompt,
)
from mente_laylay.integracao.registro_navegador import (
    registrar_navegador_leitura,
    registrar_navegador_operacoes,
)
from mente_laylay.autonomia.rota_musical import RotaMusical


class _Solicitacoes:
    def conectado(self): return True
    def solicitar_aba_ativa(self, timeout_s=4.0):
        return {
            "url": "https://usuario:senha@example.com/privado?token=segredo",
            "title": "Página privada",
            "tabId": 31,
        }
    def solicitar_lista_abas(self, timeout_s=5.0): return []


class _Ambiente:
    def __init__(self): self.chamadas = []
    def listar_abas(self, timeout_s=5.0):
        return [{"titulo": "A", "url": "https://example.com/privado"}]
    def abrir_url(self, url, **kwargs):
        self.chamadas.append(("abrir", url, kwargs)); return True
    def fechar_abas_vazias(self): self.chamadas.append(("vazias",)); return True


class _Comandos:
    def __init__(self): self.chamadas = []
    def enviar(self, acao, payload):
        self.chamadas.append((acao, payload)); return True
    def enviar_detalhado(self, acao, payload):
        self.chamadas.append((acao, payload))
        return {
            "ok": False,
            "confirmado": False,
            "status": "autoplay_blocked",
            "tab": {"id": 7},
        }


class _ComandosSequenciais:
    def __init__(self, retornos):
        self.retornos = iter(retornos)
        self.chamadas = []

    def enviar_detalhado(self, acao, payload):
        self.chamadas.append((acao, dict(payload)))
        return dict(next(self.retornos))


def _registros():
    solicitacoes = _Solicitacoes()
    ambiente = _Ambiente()
    comandos = _Comandos()
    leitura = registrar_navegador_leitura(criar_navegador_leitura_runtime(
        solicitacoes=solicitacoes, ambiente=ambiente,
    ))
    operacoes = registrar_navegador_operacoes(criar_navegador_operacoes_runtime(
        comandos=comandos, ambiente=ambiente, fechar_aba_nativa=lambda _alvo: True,
    ))
    return leitura, operacoes, ambiente, comandos


def test_registros_validam_os_dois_contratos_na_composicao() -> None:
    with pytest.raises(RuntimeError, match="leitura"):
        registrar_navegador_leitura(object())
    with pytest.raises(RuntimeError, match="operacoes"):
        registrar_navegador_operacoes(object())


def test_leitura_preserva_dados_para_executor_mas_diagnostico_nao_vaza() -> None:
    leitura, *_ = _registros()
    aba = leitura.aba_ativa()
    diagnostico = leitura.diagnostico()

    assert aba["tabId"] == 31
    assert "token=segredo" in aba["url"]
    assert "url" not in diagnostico
    assert "title" not in diagnostico
    assert "tabId" not in diagnostico


def test_operacoes_sao_nomeadas_e_nao_expoem_javascript_arbitrario() -> None:
    _, operacoes, ambiente, comandos = _registros()

    assert not hasattr(operacoes, "enviar")
    assert not hasattr(operacoes, "execute_js")
    assert operacoes.pesquisar_youtube("C418 Sweden") is True
    assert operacoes.fechar_aba("youtube.com") is True
    assert operacoes.abrir_url("https://example.com") is True

    assert comandos.chamadas[0][0] == "youtube_search"
    assert comandos.chamadas[1] == (
        "close_specific_tab", {"target": "youtube.com"},
    )
    assert ambiente.chamadas[-1][0] == "abrir"


def test_diagnostico_de_operacoes_nao_publica_payloads() -> None:
    _, operacoes, *_ = _registros()
    operacoes.tocar_youtube("https://youtube.com/watch?v=segredo", tab_id=7)
    diagnostico = operacoes.diagnostico()
    serializado = repr(diagnostico)

    assert "segredo" not in serializado
    assert "tab_id" not in serializado.casefold()
    assert diagnostico["comandos_disponiveis"] is True


def test_operacoes_preservam_resultado_detalhado_do_player() -> None:
    _, operacoes, _, comandos = _registros()

    resultado = operacoes.tocar_youtube_detalhado(
        "https://youtube.com/watch?v=segredo", tab_id=7,
    )

    assert resultado["ok"] is False
    assert resultado["confirmado"] is False
    assert resultado["status"] == "autoplay_blocked"
    assert resultado["tab"] == {"id": 7}
    assert comandos.chamadas[0] == (
        "youtube_play",
        {
            "url": "https://youtube.com/watch?v=segredo",
            "permitir_foco": False,
            "target_tab_id": 7,
        },
    )
    assert comandos.chamadas[1] == (
        "youtube_control", {"command": "play", "target_tab_id": 7},
    )


def test_operacoes_repetem_play_na_mesma_aba_e_confirmam_audio_real() -> None:
    comandos = _ComandosSequenciais([
        {
            "ok": False,
            "confirmado": False,
            "status": "autoplay_blocked",
            "tab": {"id": 23},
            "evidence": {"playing": False, "audible": False},
        },
        {
            "ok": True,
            "confirmado": True,
            "status": "success",
            "tab": {"id": 23},
            "evidence": {"playing": True, "audible": True, "muted": False},
        },
    ])
    operacoes = criar_navegador_operacoes_runtime(
        comandos=comandos, ambiente=_Ambiente(),
    )

    resultado = operacoes.tocar_youtube_detalhado(
        "https://youtube.com/watch?v=segredo",
    )

    assert resultado["ok"] is True
    assert resultado["confirmado"] is True
    assert resultado["status"] == "playing_confirmed"
    assert resultado["evidence"]["audible"] is True
    assert comandos.chamadas[-1] == (
        "youtube_control", {"command": "play", "target_tab_id": 23},
    )


def test_operacoes_nao_confirmam_so_por_video_estar_rodando_mudo() -> None:
    comandos = _ComandosSequenciais([
        {
            "ok": False, "confirmado": False,
            "status": "autoplay_blocked", "tab": {"id": 24},
        },
        {
            "ok": True, "confirmado": True, "status": "success",
            "tab": {"id": 24},
            "evidence": {"playing": True, "audible": False, "muted": True},
        },
    ])
    operacoes = criar_navegador_operacoes_runtime(
        comandos=comandos, ambiente=_Ambiente(),
    )

    resultado = operacoes.tocar_youtube_detalhado(
        "https://youtube.com/watch?v=segredo",
    )

    assert resultado["ok"] is False
    assert resultado["confirmado"] is False
    assert resultado["status"] == "autoplay_blocked"
    assert resultado["retry_evidence"]["muted"] is True


def test_registro_tipado_e_rota_preservam_video_aberto_sem_audio_confirmado() -> None:
    _, operacoes, *_ = _registros()
    rota = RotaMusical({"_registro_navegador_operacoes_runtime": operacoes})

    resultado = rota.abrir_detalhado(
        "https://youtube.com/watch?v=segredo",
    )

    assert resultado["ok"] is True
    assert resultado["confirmado"] is None
    assert resultado["status"] == "video_aberto_sem_confirmacao"


def test_contexto_da_llm_recebe_apenas_origem_sem_credenciais_ou_query() -> None:
    titulo, url = _sanitizar_aba_para_prompt(
        "Conta\n privada",
        "https://usuario:senha@example.com/conta?token=segredo#painel",
    )

    assert titulo == "Conta privada"
    assert url == "https://example.com"


def test_composicao_principal_nao_republica_callbacks_genericos_do_navegador() -> None:
    fonte = (Path(__file__).resolve().parents[1] / "laylay.py").read_text(
        encoding="utf-8"
    )

    assert "enviar_comando_chrome = _chrome_comandos_runtime.enviar" not in fonte
    assert "validar_e_enviar_comando = _chrome_comandos_runtime.enviar" not in fonte
    assert "listar_abas_chrome = _ambiente_navegacao_runtime.listar_abas" not in fonte
    assert "abrir_url_com_reciclagem = _ambiente_navegacao_runtime.abrir_url" not in fonte
