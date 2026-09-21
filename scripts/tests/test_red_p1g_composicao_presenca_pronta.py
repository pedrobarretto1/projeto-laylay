"""P1-G RED — presença incompleta não pode atravessar o bootstrap oficial."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import time

import pytest

from mente_laylay.autonomia.composicao_servicos import (
    criar_composicao_servicos_padrao,
)
from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.servicos_background import (
    GerenciadorServicosBackground,
)


def _dependencias_minimas():
    return {
        "contexto_getter": lambda: {},
        "registrar_oportunidade": lambda _dados: {"decisao": "sugerir"},
        "log": lambda _texto: None,
    }


def test_red_p1g_dependencias_canonicas_sao_obrigatorias_na_assinatura() -> None:
    parametros = inspect.signature(DiretorPresencaRuntime).parameters

    assert parametros["processar_evento_cognitivo"].default is inspect.Parameter.empty
    assert (
        parametros["processar_proposta_comunicativa"].default
        is inspect.Parameter.empty
    )


@pytest.mark.parametrize(
    "campo",
    ("processar_evento_cognitivo", "processar_proposta_comunicativa"),
)
def test_red_p1g_none_explicito_falha_antes_de_publicar_runtime(campo: str) -> None:
    dependencias = {
        **_dependencias_minimas(),
        "processar_evento_cognitivo": lambda evento: dict(evento),
        "processar_proposta_comunicativa": lambda _turno, **_contexto: {},
    }
    dependencias[campo] = None

    with pytest.raises(ValueError, match=campo):
        DiretorPresencaRuntime(**dependencias)


def test_p1g_catalogo_oficial_so_e_publicado_depois_das_dependencias_tardias() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    atribuicoes: dict[str, int] = {}
    for no in arvore.body:
        if not isinstance(no, ast.Assign):
            continue
        for alvo in no.targets:
            if isinstance(alvo, ast.Name):
                atribuicoes.setdefault(alvo.id, no.lineno)

    assert atribuicoes["_resposta_evento_runtime"] < atribuicoes[
        "_composicao_servicos_runtime"
    ]
    assert atribuicoes["_composicao_turno_runtime"] < atribuicoes[
        "_composicao_servicos_runtime"
    ]
    assert atribuicoes["_diretor_presenca_runtime"] < atribuicoes[
        "_composicao_servicos_runtime"
    ]


def test_red_p1g_diretor_real_reflete_encerramento_do_supervisor_oficial() -> None:
    class _Runtime:
        def iniciar(self):
            return True

        def executar(self, **_contexto):
            return None

        def encerrar(self, **_contexto):
            return None

        def parar(self):
            return None

    supervisor = GerenciadorServicosBackground(log=lambda _texto: None)
    diretor = DiretorPresencaRuntime(
        contexto_getter=lambda: {},
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=lambda evento: dict(evento),
        processar_proposta_comunicativa=lambda _turno, **_contexto: {},
        stop_event=supervisor.evento_parada,
        intervalo_ciclo_s=2.0,
        log=lambda _texto: None,
    )
    nomes_funcoes = (
        "carregar_memoria", "_preparar_autonomia_segura_padrao",
        "_preparar_sugestoes_proativas_jogo", "init_memoria_contexto_diaria",
        "_carregar_playlists_para_memoria", "_iniciar_worker_de_falas",
        "_escutar_texto_do_chat_terminal", "run_ws_server_in_thread",
        "gmail_daemon", "_agenda_daemon", "monitor_rotina_daemon",
        "_porteiro_daemon", "_monitor_saude_daemon",
        "registrar_hotkeys_modo_chat", "registrar_hotkey_barra_comando",
        "salvar_memoria",
    )
    namespace = {nome: (lambda *args, **kwargs: True) for nome in nomes_funcoes}
    namespace["_renovar_sessao_conversa"] = lambda *_args: None
    for nome in (
        "_gamebar_bridge_runtime", "_avatar_runtime", "_ouvido_whisper_runtime",
        "_observador_inventario_jogo_runtime", "_observador_presenca_jogo_runtime",
        "_observador_area_transferencia_runtime", "_monitor_janelas_runtime",
        "_ritmo_circadiano_runtime", "_motor_temporal_runtime",
        "_motor_aprendizado_runtime", "_rede_associativa_runtime", "_voz_runtime",
        "_barra_comando_runtime",
    ):
        namespace[nome] = _Runtime()
    namespace["_diretor_presenca_runtime"] = diretor
    composicao = criar_composicao_servicos_padrao(
        namespace,
        gerenciador=supervisor,
        log=lambda _texto: None,
    )

    target = composicao.catalogo_threads()["Laylay-Diretor-Presença"]
    assert supervisor.iniciar("Laylay-Diretor-Presença", target) is True
    limite = time.monotonic() + 0.5
    while not diretor._running and time.monotonic() < limite:
        time.sleep(0.005)
    assert diretor._running is True

    supervisor.encerrar(timeout_s=0.5)
    limite = time.monotonic() + 0.5
    while supervisor.ativos() and time.monotonic() < limite:
        time.sleep(0.005)

    assert supervisor.ativos() == ()
    assert diretor._running is False
