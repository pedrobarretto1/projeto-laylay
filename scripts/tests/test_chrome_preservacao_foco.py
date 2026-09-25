"""Restrição de foco deve sobreviver ao transporte, fora e dentro de jogos."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from mente_laylay.integracao.chrome_comandos import ChromeComandosRuntime
from mente_laylay.integracao.chrome_navegacao import abrir_url_reutilizando_aba
from mente_laylay.integracao.ambiente_navegacao import AmbienteNavegacaoRuntime
from mente_laylay.integracao.navegador_runtime import criar_navegador_operacoes_runtime
from mente_laylay.integracao.registro_navegador import registrar_navegador_operacoes
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


def _executor(*, conectado=True, jogo=False, confirma=True, busca=""):
    enviados = []
    resultado = {}

    def enviar(msg, **kwargs):
        enviados.append(dict(msg))
        resultado.update(
            action=msg["action"], ok=confirma,
            status="playing_confirmed" if confirma else "navigation_timeout",
            tab={"id": 19}, evidence={"playing": confirma, "audible": confirma},
        )
        return confirma

    ctx = {
        "ALLOWED_ACTIONS": {"open_url", "open_tab", "youtube_play", "youtube_search"},
        "connected_extensions": {"extensao"} if conectado else set(),
        "ws_loop": object() if conectado else None,
        "broadcast_command": lambda *_: None,
        "executar_chrome_confirmado": enviar,
        "enviar_chrome_confirmado": enviar,
        "ultimo_resultado_chrome": lambda: resultado,
        "modo_jogo_ativo": lambda: jogo,
        "is_valid_url": lambda url: url.startswith("https://"),
        "formatar_url_ou_busca": lambda url, **kwargs: url,
        "atualizar_contexto": lambda **kwargs: None,
        "_buscar_primeiro_video_youtube": lambda query: busca,
    }
    return ChromeComandosRuntime(contexto_getter=lambda: ctx), enviados


@pytest.mark.parametrize("acao", ["youtube_play", "youtube_search", "open_url", "open_tab", "entrar_no_site"])
@pytest.mark.parametrize("jogo", [False, True])
def test_restricao_explicita_de_foco_chega_a_extensao_em_qualquer_modo(acao, jogo):
    executor, enviados = _executor(jogo=jogo)
    assert executor.enviar(acao, {
        "url": "https://example.com/video", "query": "musica",
        "permitir_foco": False, "target_tab_id": 19,
    })
    assert enviados[0].get("background") is True
    if acao == "youtube_play":
        assert enviados[0]["target_tab_id"] == 19


def test_busca_convertida_em_url_preserva_restricao_de_foco():
    executor, enviados = _executor(busca="https://youtube.com/watch?v=abcdefghijk")
    assert executor.enviar("youtube_search", {"query": "musica", "permitir_foco": False})
    assert enviados[0]["action"] == "open_url"
    assert enviados[0].get("background") is True


@pytest.mark.parametrize("jogo", [False, True])
def test_foco_explicitamente_permitido_continua_disponivel(jogo):
    executor, enviados = _executor(jogo=jogo)
    assert executor.enviar("youtube_play", {"url": "https://youtube.com/watch?v=abcdefghijk", "permitir_foco": True})
    assert not enviados[0].get("background")


def test_navegacao_legada_sem_restricao_preserva_comportamento():
    executor, enviados = _executor()
    assert executor.enviar("open_url", {"url": "https://example.com"})
    assert not enviados[0].get("background")


def test_background_explicito_nao_e_desfeito_por_permissao_de_foco():
    executor, enviados = _executor()
    assert executor.enviar("open_url", {
        "url": "https://example.com", "background": True, "permitir_foco": True,
    })
    assert enviados[0]["background"] is True


@pytest.mark.parametrize("acao", ["open_url", "youtube_play"])
def test_abertura_nativa_legada_sem_restricao_continua_disponivel(monkeypatch, acao):
    aberturas = []
    monkeypatch.setattr("mente_laylay.integracao.chrome_comandos.webbrowser.open", lambda url: aberturas.append(url) or True)
    executor, _ = _executor(conectado=False)
    assert executor.enviar(acao, {"url": "https://example.com"})
    assert aberturas == ["https://example.com"]


@pytest.mark.parametrize("acao", ["open_url", "youtube_play"])
@pytest.mark.parametrize("restricao", [{"permitir_foco": False}, {"background": True}])
def test_sem_extensao_nao_contorna_restricao_com_abertura_nativa(monkeypatch, acao, restricao):
    aberturas = []
    monkeypatch.setattr("mente_laylay.integracao.chrome_comandos.webbrowser.open", lambda url: aberturas.append(url) or True)
    executor, enviados = _executor(conectado=False)
    assert executor.enviar(acao, {"url": "https://example.com", **restricao}) is False
    assert aberturas == []
    assert enviados == []


@pytest.mark.parametrize("confirma", [False, True])
def test_playlist_registro_e_executor_reais_preservam_aba_foco_e_receipt(tmp_path, confirma):
    executor, enviados = _executor(confirma=confirma)
    operacoes = registrar_navegador_operacoes(criar_navegador_operacoes_runtime(
        comandos=executor, ambiente=object(),
    ))
    # Usa o callback efetivamente injetado em produção, sem iniciar serviços,
    # microfone ou dispositivos ao importar o composition root completo.
    fonte = Path(__file__).resolve().parents[2] / "laylay.py"
    arvore = ast.parse(fonte.read_text(encoding="utf-8"))
    composicao = next(
        no.value for no in arvore.body if isinstance(no, ast.Assign)
        and any(isinstance(alvo, ast.Name) and alvo.id == "_playlist_runtime" for alvo in no.targets)
    )
    callback = next(kw.value for kw in composicao.keywords if kw.arg == "youtube_play")
    tocar = eval(compile(ast.Expression(callback), str(fonte), "eval"), {
        "_registro_navegador_operacoes_runtime": operacoes,
    })
    estado = {"name": "estudo", "tab_id": 19}
    playlist = PlaylistRuntime(
        state_file=str(tmp_path / "playlists.json"), legacy_file=str(tmp_path / "legacy.json"),
        cache={}, ultima_playlist_getter=lambda: "estudo", playlist_state=estado,
        youtube_play=tocar,
        log=lambda _: None,
    )
    assert playlist._abrir_youtube_item("https://youtube.com/watch?v=abcdefghijk") is confirma
    assert enviados[0]["target_tab_id"] == 19
    assert enviados[0].get("background") is True
    assert estado["last_play_confirmed"] is confirma


@pytest.mark.parametrize("url", ["https://example.com/estudo", "https://youtube.com/watch?v=abcdefghijk"])
def test_reuso_sem_extensao_respeita_restricao_sem_depender_do_callback(url):
    aberturas = []
    comandos = []
    ok = abrir_url_reutilizando_aba(
        url, conectado=lambda: False,
        solicitar_lista_abas=lambda: pytest.fail("Não consultar extensão desconectada"),
        enviar_comando=lambda *args: comandos.append(args),
        abrir_fallback=lambda alvo: aberturas.append(alvo) or True,
        preservar_foco=True,
    )
    assert aberturas == [], "Fallback não pode violar preservação de foco"
    assert comandos == []
    assert ok is False


@pytest.mark.parametrize("resultado", [True, False])
def test_reuso_sem_restricao_preserva_receipt_do_fallback(resultado):
    aberturas = []
    ok = abrir_url_reutilizando_aba(
        "https://example.com", conectado=lambda: False,
        solicitar_lista_abas=lambda: [], enviar_comando=lambda *_: True,
        abrir_fallback=lambda alvo: aberturas.append(alvo) or resultado,
    )
    assert aberturas == ["https://example.com"]
    assert ok is resultado


@pytest.mark.parametrize("jogo,permitir_foco,abre", [(True, False, False), (True, True, True), (False, False, True)])
def test_composicao_ambiente_sem_extensao_preserva_politica_existente(jogo, permitir_foco, abre):
    aberturas = []
    ambiente = AmbienteNavegacaoRuntime(servicos_iniciais={
        "_modo_jogo_runtime": SimpleNamespace(ativo=jogo),
        "_abrir_url_reutilizando_aba_chrome_mente": abrir_url_reutilizando_aba,
        "webbrowser": SimpleNamespace(open=lambda url, **kwargs: aberturas.append(url) or True),
    })
    executor, enviados = _executor(conectado=False, jogo=jogo)
    ambiente.conectar_navegador(
        solicitacoes=SimpleNamespace(conectado=lambda: False, solicitar_lista_abas=lambda: []),
        comandos=executor,
    )
    assert ambiente.abrir_url("https://example.com", permitir_foco=permitir_foco) is abre
    assert aberturas == (["https://example.com"] if abre else [])
    assert enviados == []
