from __future__ import annotations

import asyncio
import json

import pytest

from cliente import cliente_laylay as cliente
from mente_laylay.integracao import pc_b_integracao


class _WebSocketFake:
    def __init__(self) -> None:
        self.enviadas: list[dict] = []

    async def send(self, mensagem: str) -> None:
        self.enviadas.append(json.loads(mensagem))


class _EndpointVolumeFake:
    def __init__(self, *, volume: float = 0.5, mudo: bool = True) -> None:
        self.volume = volume
        self.mudo = mudo

    def SetMasterVolumeLevelScalar(self, valor, _contexto) -> None:
        self.volume = float(valor)

    def GetMasterVolumeLevelScalar(self) -> float:
        return self.volume

    def SetMute(self, valor, _contexto) -> None:
        self.mudo = bool(valor)

    def GetMute(self) -> bool:
        return self.mudo


class _JanelaFake:
    def __init__(self, titulo: str) -> None:
        self.title = titulo
        self.isMinimized = False
        self.isMaximized = False
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.closed = False

    def restore(self) -> None:
        self.isMinimized = False
        self.isMaximized = False

    def maximize(self) -> None:
        self.isMaximized = True

    def moveTo(self, x: int, y: int) -> None:
        self.left = x
        self.top = y

    def resizeTo(self, largura: int, altura: int) -> None:
        self.width = largura
        self.height = altura

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize(
    ("payload", "esperado"),
    [
        ({"nivel": 0}, 0),
        ({"level": 35}, 35),
        ({"volume": 72}, 72),
    ],
)
def test_volume_absoluto_aceita_aliases_e_preserva_zero(
    monkeypatch, payload, esperado,
) -> None:
    endpoint = _EndpointVolumeFake()
    monkeypatch.setattr(cliente, "_endpoint_volume", lambda: endpoint)

    observado = cliente._ajustar_volume_absoluto(payload)

    assert observado == esperado
    assert round(endpoint.volume * 100) == esperado


def test_volume_unmute_confirma_estado_observado(monkeypatch) -> None:
    endpoint = _EndpointVolumeFake(mudo=True)
    monkeypatch.setattr(cliente, "_endpoint_volume", lambda: endpoint)

    assert cliente._desmutar_volume() is True
    assert endpoint.mudo is False


def test_controle_midia_rejeita_comando_inexistente_e_skip_ad(monkeypatch) -> None:
    teclas: list[int] = []
    monkeypatch.setattr(cliente, "_pressionar_tecla_midia", teclas.append)

    assert cliente._executar_controle_midia("next")["ok"] is True
    assert teclas == [cliente.VK_MEDIA_NEXT_TRACK]
    assert cliente._executar_controle_midia("skip_ad")["ok"] is False
    assert cliente._executar_controle_midia("teletransporte")["ok"] is False
    assert teclas == [cliente.VK_MEDIA_NEXT_TRACK]


def test_maximizar_janela_rele_estado_final(monkeypatch) -> None:
    janela = _JanelaFake("Opera - YouTube")
    monkeypatch.setattr(cliente.gw, "getAllWindows", lambda: [janela])
    monkeypatch.setattr(cliente.time, "sleep", lambda _segundos: None)

    resultado = cliente._maximizar_janela_remota("Opera")

    assert resultado["ok"] is True
    assert resultado["window"] == "Opera - YouTube"
    assert janela.isMaximized is True


def test_fechar_app_exige_janela_anterior_e_rele_ausencia(monkeypatch) -> None:
    janela = _JanelaFake("Bloco de Notas")
    monkeypatch.setattr(
        cliente.gw,
        "getAllWindows",
        lambda: [] if janela.closed else [janela],
    )
    monkeypatch.setattr(cliente.time, "sleep", lambda _segundos: None)

    confirmado = cliente.ExecutorRemotoPC()._fechar_app({"app": "Bloco de Notas"})
    ausente = cliente.ExecutorRemotoPC()._fechar_app({"app": "Calculadora"})

    assert confirmado["ok"] is True
    assert confirmado["confirmed"] is True
    assert ausente["ok"] is False
    assert ausente.get("executed") is not True


def test_organizar_desktop_respeita_esquerda_e_direita(monkeypatch) -> None:
    opera = _JanelaFake("Música - Opera")
    vscode = _JanelaFake("laylay.py - Visual Studio Code")
    monkeypatch.setattr(cliente.gw, "getAllWindows", lambda: [opera, vscode])
    monkeypatch.setattr(cliente, "_dimensoes_tela", lambda: (1920, 1080))
    monkeypatch.setattr(cliente.time, "sleep", lambda _segundos: None)

    resultado = cliente._organizar_janelas_remotas("Opera", "Visual Studio Code")

    assert resultado["ok"] is True
    assert (opera.left, opera.top, opera.width) == (0, 0, 960)
    assert (vscode.left, vscode.top, vscode.width) == (960, 0, 960)


def test_cliente_implementa_acoes_que_o_cerebro_envia() -> None:
    obrigatorias = {
        "open_app", "close_app", "maximize_window", "organizar_desktop",
        "set_volume", "volume_up", "volume_down", "volume_unmute",
        "youtube_control", "open_url", "close_specific_tab", "notificar",
        "criar_pasta", "deletar_item", "capturar_tela", "lock_pc",
    }
    assert obrigatorias <= cliente.ExecutorRemotoPC().acoes_suportadas


def test_executor_remoto_envia_um_unico_estado_final() -> None:
    executor = cliente.ExecutorRemotoPC()
    websocket = _WebSocketFake()
    executor._handlers["teste"] = lambda _dados: cliente._resultado_remoto(
        True, confirmed=True, detalhe="observado",
    )

    asyncio.run(executor.executar(websocket, {"action": "teste"}))

    assert websocket.enviadas == [{
        "type": "pc_b_status",
        "status": "success",
        "action": "teste",
        "executed": True,
        "confirmed": True,
        "error": "",
        "detalhe": "observado",
    }]


def test_executor_remoto_converte_excecao_em_falha_final() -> None:
    executor = cliente.ExecutorRemotoPC()
    websocket = _WebSocketFake()

    def falhar(_dados):
        raise RuntimeError("quebrou no teste")

    executor._handlers["teste"] = falhar
    asyncio.run(executor.executar(websocket, {"action": "teste"}))

    assert len(websocket.enviadas) == 1
    assert websocket.enviadas[0]["status"] == "error"
    assert websocket.enviadas[0]["confirmed"] is None
    assert "RuntimeError" in websocket.enviadas[0]["error"]


def test_executor_remoto_rejeita_acao_desconhecida_sem_timeout() -> None:
    executor = cliente.ExecutorRemotoPC()
    websocket = _WebSocketFake()

    asyncio.run(executor.executar(websocket, {"action": "teletransporte"}))

    assert len(websocket.enviadas) == 1
    assert websocket.enviadas[0]["status"] == "error"
    assert websocket.enviadas[0]["errorCode"] == "acao_nao_suportada"


def test_executor_remoto_rejeita_payload_malformado_sem_excecao() -> None:
    executor = cliente.ExecutorRemotoPC()
    websocket = _WebSocketFake()

    asyncio.run(executor.executar(websocket, ["não", "é", "objeto"]))

    assert len(websocket.enviadas) == 1
    assert websocket.enviadas[0]["status"] == "error"
    assert websocket.enviadas[0]["errorCode"] == "payload_invalido"


def test_executor_remoto_envia_payload_auxiliar_antes_do_status_final() -> None:
    executor = cliente.ExecutorRemotoPC()
    websocket = _WebSocketFake()
    executor._handlers["teste"] = lambda _dados: cliente._resultado_remoto(
        True,
        confirmed=True,
        _messages=[{"type": "pc_b_screenshot", "imagem_b64": "abc"}],
    )

    asyncio.run(executor.executar(websocket, {"action": "teste"}))

    assert [item["type"] for item in websocket.enviadas] == [
        "pc_b_screenshot", "pc_b_status",
    ]
    assert websocket.enviadas[-1]["confirmed"] is True


def test_executor_remoto_catalogo_cobre_protocolo_atual() -> None:
    executor = cliente.ExecutorRemotoPC()
    assert {
        "open_app", "close_app", "maximize_window", "organizar_desktop",
        "set_volume", "volume_up", "volume_down", "volume_unmute",
        "youtube_control", "media_control", "open_url", "close_specific_tab",
        "close_current_tab", "notificar", "criar_pasta", "criar_arquivo",
        "deletar_item", "capturar_tela", "lock_pc",
    } <= executor.acoes_suportadas


def test_acoes_privilegiadas_nao_sao_anunciadas_sem_opt_in() -> None:
    restrito = cliente.ExecutorRemotoPC(env_getter=lambda _nome, padrao="": padrao)
    liberado = cliente.ExecutorRemotoPC(
        env_getter=lambda nome, padrao="": {
            "LAYLAY_PC_B_ALLOW_INPUT_AUTOMATION": "1",
            "LAYLAY_PC_B_ALLOW_SHELL": "true",
        }.get(nome, padrao),
    )

    assert {
        "shell_command", "type_text", "press_key", "copy_to_clipboard",
    }.isdisjoint(restrito.acoes_suportadas)
    assert {
        "shell_command", "type_text", "press_key", "copy_to_clipboard",
    } <= liberado.acoes_suportadas


def test_mutacao_remota_fica_dentro_da_raiz_autorizada(tmp_path) -> None:
    executor = cliente.ExecutorRemotoPC(
        env_getter=lambda nome, padrao="": (
            str(tmp_path) if nome == "LAYLAY_PC_B_ALLOWED_ROOTS" else padrao
        ),
    )

    criado = executor._criar_arquivo({"alvo": "seguro/teste.txt"})

    assert criado["ok"] is True
    assert (tmp_path / "seguro" / "teste.txt").is_file()
    with pytest.raises(PermissionError):
        executor._deletar_item({"alvo": str(tmp_path.parent / "fora.txt")})


def test_request_id_repetido_nao_executa_duas_vezes() -> None:
    executor = cliente.ExecutorRemotoPC()
    websocket = _WebSocketFake()
    execucoes = []
    executor._handlers["teste"] = lambda _dados: (
        execucoes.append(True)
        or cliente._resultado_remoto(True, confirmed=True)
    )
    payload = {
        "action": "teste",
        "requestId": "mesmo-pedido",
        "expectsFinalStatus": True,
    }

    asyncio.run(executor.executar(websocket, payload))
    asyncio.run(executor.executar(websocket, payload))

    assert execucoes == [True]
    assert websocket.enviadas[-1]["errorCode"] == "request_repetido"


def test_captura_bloqueia_contexto_sensivel_mesmo_sem_flag(monkeypatch) -> None:
    janela = type("Janela", (), {"title": "Login do banco"})()
    monkeypatch.setattr(cliente.gw, "getActiveWindow", lambda: janela)
    monkeypatch.setattr(
        cliente.pyautogui,
        "screenshot",
        lambda: pytest.fail("não deveria capturar uma tela sensível"),
    )

    resultado = cliente.ExecutorRemotoPC()._capturar_tela({})

    assert resultado["ok"] is False
    assert resultado["sensitiveContext"] is True


def test_abertura_de_app_rejeita_metacaracteres_de_shell(monkeypatch) -> None:
    aberturas = []
    monkeypatch.setattr(cliente, "open_app", lambda *args, **kwargs: aberturas.append(args))

    resultado = cliente.ExecutorRemotoPC()._abrir_app({
        "app": "Opera & calc.exe", "quantidade": 3,
    })

    assert resultado["ok"] is False
    assert aberturas == []


def test_cerebro_nao_promove_falha_remota_a_resultado_confirmado(
    monkeypatch,
) -> None:
    capturados = []
    falas = []

    def planejar(resultado, *_args, **_kwargs):
        capturados.append(resultado)
        return type("Plano", (), {
            "fala": "falhou", "emocao": "calma", "nivel": 1,
        })()

    monkeypatch.setattr(pc_b_integracao, "planejar_resposta_acao", planejar)

    tratado = pc_b_integracao.processar_mensagem_pc_b(
        {
            "type": "pc_b_status",
            "status": "error",
            "action": "maximize_window",
            "app": "Opera",
            "error": "janela ausente",
        },
        {"falar_com_lipsync": lambda *args: falas.append(args)},
    )

    assert tratado is True
    assert capturados[0].executou is False
    assert capturados[0].confirmado is False
    assert falas == [("falhou", "calma", 1)]
