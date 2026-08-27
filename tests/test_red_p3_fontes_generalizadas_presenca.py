"""P3-A RED — apps, Chrome e IoT entram pela mesma cognição de presença."""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Any

from mente_laylay.percepcao.monitor_janelas import MonitorJanelasRuntime
from mente_laylay.percepcao.ritmo_circadiano import RitmoCircadianoRuntime


def _aceitar_evento(eventos: list[dict[str, Any]]):
    def considerar(evento: dict[str, Any]) -> dict[str, Any]:
        eventos.append(dict(evento))
        return {
            "status": "proposta_cognitiva",
            "emissao_fisica": False,
            "proposta_comunicativa": {
                "status": "agendada",
                "agendada": True,
                "emissao_fisica": False,
                "autoriza_execucao": False,
            },
        }

    return considerar


def _monitor(
    *,
    considerar_presenca: Any,
    continuidade: dict[str, Any],
    detectar_gatilho: Any = lambda *_args: ("", None),
    fala_gatilho: Any = lambda _gatilho: "",
) -> MonitorJanelasRuntime:
    return MonitorJanelasRuntime(
        capturar_janela=lambda: {},
        atualizar_contexto=lambda _retrato: None,
        continuidade_get=lambda chave, padrao=None: continuidade.get(chave, padrao),
        continuidade_update=lambda **campos: continuidade.update(campos),
        esta_falando=lambda: False,
        conversa_ativa=lambda: False,
        ultimo_proativo_get=lambda: 0.0,
        ultimo_proativo_set=lambda _valor: None,
        sugestoes_bloqueadas_get=lambda: {},
        janela_em_tela_cheia=lambda _janela: False,
        detectar_gatilho=detectar_gatilho,
        fala_gatilho=fala_gatilho,
        considerar_presenca=considerar_presenca,
        clock=lambda: 2_000.0,
        log=lambda _texto: None,
    )


def test_red_p3_app_publica_evento_semantico_e_so_cria_pendencia_apos_entrega() -> None:
    eventos: list[dict[str, Any]] = []
    continuidade = {"comando_sugerido_estado": "NONE"}
    runtime = _monitor(
        considerar_presenca=_aceitar_evento(eventos),
        continuidade=continuidade,
    )

    assert runtime.sugerir_assunto("Programação", agora=2_000.0) is True
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["origem"] == "monitor_janelas"
    assert evento["dominio"] == "janelas"
    assert evento["natureza"] == "evento"
    assert evento["autoridade_usuario"] is False
    assert evento["permissao_execucao"] is False
    assert evento["acao_proposta"]["intent"] == "SYS_MODE_CODE"
    assert "fala" not in evento
    assert continuidade["comando_sugerido_estado"] == "NONE"

    evento["ao_concluir"](True, "entregue")
    assert continuidade["comando_sugerido"] == "SYS_MODE_CODE"
    assert continuidade["comando_sugerido_estado"] == "PENDING_CONFIRM"


def test_red_p3_chrome_publica_o_mesmo_contrato_sem_fala_direta() -> None:
    eventos: list[dict[str, Any]] = []
    continuidade = {"comando_sugerido_estado": "NONE"}
    runtime = _monitor(
        considerar_presenca=_aceitar_evento(eventos),
        continuidade=continuidade,
        detectar_gatilho=lambda *_args: (
            "RELOAD_PAGE", {"aba_id": 7, "motivo": "erro_visivel"},
        ),
        fala_gatilho=lambda _gatilho: "A página parece ter travado.",
    )
    runtime.ultimo_gatilho = "RELOAD_PAGE"
    runtime.gatilho_inicio_ts = 1_980.0
    runtime.capturar_janela = lambda: {
        "win": object(),
        "hwnd": 9,
        "title": "Erro - Chrome",
        "exe": "chrome.exe",
        "assunto": "Navegação",
    }
    runtime.ultimo_hwnd = 9

    resultado = runtime.executar_ciclo()

    assert resultado["status"] == "sugestao_emitida"
    evento = eventos[0]
    assert evento["dominio"] == "navegador"
    assert evento["natureza"] == "evento"
    assert evento["autoridade_usuario"] is False
    assert evento["permissao_execucao"] is False
    assert evento["acao_proposta"]["intent"] == "RELOAD_PAGE"
    assert "fala" not in evento
    assert continuidade["comando_sugerido_estado"] == "NONE"

    evento["ao_concluir"](True, "entregue")
    assert continuidade["comando_sugerido"] == "RELOAD_PAGE"
    assert continuidade["comando_sugerido_estado"] == "PENDING_CONFIRM"


def test_red_p3_ritmo_publica_evento_iot_sem_promover_relogio_a_permissao() -> None:
    eventos: list[dict[str, Any]] = []
    estado: dict[str, Any] = {}
    continuidade = {"comando_sugerido_estado": "NONE"}
    runtime = RitmoCircadianoRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.update(novo),
        continuidades_get=lambda chave, padrao=None: continuidade.get(chave, padrao),
        continuidades_update=lambda **campos: continuidade.update(campos),
        considerar_presenca=_aceitar_evento(eventos),
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        agora_cb=lambda: datetime(2026, 7, 16, 19, 10),
        log=lambda _texto: None,
    )

    resultado = runtime.executar_ciclo()

    assert resultado["status"] == "sugestao_agendada"
    evento = eventos[0]
    assert evento["origem"] == "ritmo_circadiano"
    assert evento["dominio"] == "iot"
    assert evento["natureza"] == "evento"
    assert evento["autoridade_usuario"] is False
    assert evento["permissao_execucao"] is False
    assert evento["acao_proposta"]["intent"] == "TIME_LIGHT_ON"
    assert "fala" not in evento
    assert continuidade["comando_sugerido_estado"] == "NONE"

    evento["ao_concluir"](True, "entregue")
    assert continuidade["comando_sugerido"] == "TIME_LIGHT_ON"
    assert continuidade["comando_sugerido_estado"] == "PENDING_CONFIRM"
    assert estado["sugestoes_emitidas"]["luz_anoitecer"] == "2026-07-16"


def test_red_p3_root_nao_liga_fontes_generalizadas_direto_a_voz() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    chamadas: dict[str, dict[str, str]] = {}
    alvos = {"_monitor_janelas_runtime", "_ritmo_circadiano_runtime"}
    for no in arvore.body:
        if not isinstance(no, ast.Assign) or not isinstance(no.value, ast.Call):
            continue
        nomes = {
            alvo.id for alvo in no.targets if isinstance(alvo, ast.Name)
        }
        alvo = next(iter(nomes & alvos), "")
        if alvo:
            chamadas[alvo] = {
                item.arg: ast.unparse(item.value)
                for item in no.value.keywords
                if item.arg
            }

    assert set(chamadas) == alvos
    for keywords in chamadas.values():
        assert "considerar_presenca" in keywords
        assert "agendar_fala" not in keywords
        assert "falar" not in keywords
        assert "registrar_oportunidade" not in keywords
