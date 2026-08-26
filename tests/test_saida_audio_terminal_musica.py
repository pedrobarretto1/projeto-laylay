from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.integracao.acoes_painel_runtime import executar_acao_painel_tipado
from mente_laylay.integracao.desktop_bridge import sanitizar_dashboard_estado
from mente_laylay.integracao.desktop_bridge import validar_mensagem_cliente
from mente_laylay.percepcao.saidas_audio_windows import GerenciadorSaidasAudioWindows


class _AudioUtilitiesFake:
    atual = "{0.0.0.00000000}.{AAA}"
    trocas: list[str] = []
    consultas: list[tuple[int | None, int | None]] = []
    dispositivos = [
        SimpleNamespace(
            id="{0.0.0.00000000}.{AAA}",
            FriendlyName="Alto-falantes Realtek", state=SimpleNamespace(value=1),
        ),
        SimpleNamespace(
            id="{0.0.0.00000000}.{BBB}",
            FriendlyName="Fones Bluetooth", state=SimpleNamespace(value=1),
        ),
        SimpleNamespace(
            id="{0.0.1.00000000}.{MIC}",
            FriendlyName="Microfone", state=SimpleNamespace(value=1),
        ),
    ]

    @classmethod
    def GetSpeakers(cls):
        item = next(item for item in cls.dispositivos if item.id == cls.atual)
        return item

    @classmethod
    def GetAllDevices(cls, *, data_flow=None, device_state=None):
        cls.consultas.append((data_flow, device_state))
        return list(cls.dispositivos)

    @classmethod
    def SetDefaultDevice(cls, endpoint_id, roles=None):
        del roles
        cls.trocas.append(endpoint_id)
        cls.atual = endpoint_id


def _gerenciador() -> GerenciadorSaidasAudioWindows:
    _AudioUtilitiesFake.atual = "{0.0.0.00000000}.{AAA}"
    _AudioUtilitiesFake.trocas = []
    _AudioUtilitiesFake.consultas = []
    return GerenciadorSaidasAudioWindows(
        audio_utilities=_AudioUtilitiesFake,
        cache_s=0,
        log=lambda _texto: None,
    )


def test_runtime_restringe_inventario_na_origem_a_saidas_ativas() -> None:
    runtime = _gerenciador()

    runtime.snapshot()

    assert _AudioUtilitiesFake.consultas == [(0, 1)]


def test_runtime_lista_apenas_saidas_e_confirma_troca_sem_expor_endpoint() -> None:
    runtime = _gerenciador()
    inicial = runtime.snapshot()

    assert inicial["name"] == "Alto-falantes Realtek"
    assert [item["name"] for item in inicial["devices"]] == [
        "Alto-falantes Realtek", "Fones Bluetooth",
    ]
    assert all("0.0.0" not in item["ref"] for item in inicial["devices"])
    destino = next(item for item in inicial["devices"] if item["name"] == "Fones Bluetooth")

    resultado = runtime.selecionar(destino["ref"])

    assert resultado["executou"] is True
    assert resultado["confirmado"] is True
    assert runtime.snapshot()["name"] == "Fones Bluetooth"


def test_ponte_publica_tokens_opacos_e_descarta_ids_e_campos_extras() -> None:
    token = "0123456789abcdef"
    retrato = sanitizar_dashboard_estado({
        "generated_at": 1_000,
        "music": {
            "audio_output": {
                "name": "Fones", "source": "padrão do sistema",
                "available": True, "selected_ref": token,
                "switch_available": True, "observed_at": 1_000,
                "device_id": "endpoint-secreto",
                "devices": [{
                    "ref": token, "name": "Fones", "selected": True,
                    "device_id": "endpoint-secreto",
                }],
            },
        },
    })

    audio = retrato["music"]["audio_output"]
    assert audio["selected_ref"] == token
    assert audio["devices"] == [{"ref": token, "name": "Fones", "selected": True}]
    assert "endpoint-secreto" not in str(audio)


def test_acao_manual_troca_saida_sem_chamar_interpretacao() -> None:
    chamadas: list[str] = []
    llm: list[dict] = []

    resultado = executar_acao_painel_tipado(
        "audio_output_select",
        {"device_ref": "0123456789abcdef"},
        executar_intencao=lambda *_args: llm.append({}) or False,
        selecionar_saida_audio=lambda token: (
            chamadas.append(token)
            or {"executou": True, "confirmado": True, "resumo": "Saída alterada"}
        ),
    )

    assert resultado["confirmado"] is True
    assert chamadas == ["0123456789abcdef"]
    assert llm == []


def test_ponte_aceita_somente_token_opaco_na_troca_de_saida() -> None:
    mensagem = validar_mensagem_cliente({
        "type": "input_submit", "id": "audio-1",
        "text": "trocar saída", "kind": "panel_action",
        "action": "audio_output_select",
        "payload": {"device_ref": "0123456789abcdef"},
    }, token="segredo", autenticado=True)

    assert mensagem["payload"] == {"device_ref": "0123456789abcdef"}
    with pytest.raises(ValueError):
        validar_mensagem_cliente({
            "type": "input_submit", "text": "trocar saída",
            "kind": "panel_action", "action": "audio_output_select",
            "payload": {"device_ref": "endpoint-do-windows"},
        }, token="segredo", autenticado=True)


def test_bloco_musica_lista_dispositivos_e_emite_token_ao_selecionar(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard({
        "music": {
            "audio_output": {
                "name": "Realtek", "source": "padrão do sistema",
                "available": True, "selected_ref": "1111111111111111",
                "switch_available": True, "observed_at": 1_000,
                "devices": [
                    {"ref": "1111111111111111", "name": "Realtek", "selected": True},
                    {"ref": "2222222222222222", "name": "Fones", "selected": False},
                ],
            },
        }, "system": {}, "routines": {},
    })
    pedidos: list[tuple[str, str, dict]] = []
    pagina.acao_fila_solicitada.connect(
        lambda acao, texto, payload: pedidos.append((acao, texto, payload)),
    )

    pagina._solicitar_saida_audio(1)

    assert pagina.audio_lista.count() == 2
    assert pagina.audio_gerenciar.isEnabled()
    assert pedidos == [(
        "audio_output_select", "trocar a saída de áudio para Fones",
        {"device_ref": "2222222222222222"},
    )]
    pagina.close()
    app.processEvents()
