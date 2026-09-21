"""P1-D RED — toda fonte de presença usa o Diretor e o mesmo recibo de fila."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mente_laylay.integracao.ponte_clipboard_aplicacao import (
    PonteClipboardAplicacaoRuntime,
)
from mente_laylay.percepcao.observador_area_transferencia import (
    ObservadorAreaTransferenciaRuntime,
)
from mente_laylay.percepcao.visao_jogo.coordenador import (
    CoordenadorVisaoJogoRuntime,
)


def _decisao_cognitiva(*, agendada: bool = True) -> dict[str, Any]:
    return {
        "status": "proposta_cognitiva",
        "emissao_fisica": False,
        "proposta_comunicativa": {
            "status": "agendada" if agendada else "bloqueada_porteiro",
            "agendada": agendada,
            "emissao_fisica": False,
            "autoriza_execucao": False,
        },
    }


def _observar_clipboard(
    considerar_presenca: Any,
    *,
    oferta_entregue: Any = None,
) -> tuple[ObservadorAreaTransferenciaRuntime, list[dict[str, Any]], list[float]]:
    agora = [0.0]
    snapshots = [{
        "status": "ok",
        "tipo": "texto_curto",
        "relevante": False,
        "assinatura": "baseline",
        "sequencia_evento": 1,
        "tamanho": 8,
    }]
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=lambda: dict(snapshots[0]),
        considerar_presenca=considerar_presenca,
        oferta_entregue=oferta_entregue,
        contexto_getter=lambda: {"titulo_janela": "Visual Studio Code"},
        estabilidade_s=1.0,
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )
    runtime.preparar_baseline()
    snapshots[0] = {
        "status": "ok",
        "tipo": "erro",
        "relevante": True,
        "assinatura": "erro-sanitizado-42",
        "sequencia_evento": 2,
        "tamanho": 80,
        "confianca": 0.92,
    }
    return runtime, snapshots, agora


def test_red_p1d_root_clipboard_entra_no_diretor_sem_ponte_de_emissao() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    keywords: dict[str, str] = {}
    nomes_atribuidos: set[str] = set()
    for no in arvore.body:
        if isinstance(no, ast.Assign):
            nomes_atribuidos.update(
                alvo.id for alvo in no.targets if isinstance(alvo, ast.Name)
            )
        if not isinstance(no, ast.Assign) or not isinstance(no.value, ast.Call):
            continue
        if any(
            isinstance(alvo, ast.Name)
            and alvo.id == "_observador_area_transferencia_runtime"
            for alvo in no.targets
        ):
            keywords = {
                item.arg: ast.unparse(item.value)
                for item in no.value.keywords
                if item.arg
            }

    assert keywords["considerar_presenca"] == "_diretor_presenca_runtime.considerar"
    assert "_encaminhar_oferta_area_transferencia" not in nomes_atribuidos

    codigo_ponte = inspect.getsource(PonteClipboardAplicacaoRuntime)
    assert "def encaminhar_oferta" not in codigo_ponte
    assert "self._agendar_fala" not in codigo_ponte


def test_red_p1d_observador_aceita_recibo_cognitivo_agendado_sem_republicar() -> None:
    eventos: list[dict[str, Any]] = []
    runtime, _snapshots, agora = _observar_clipboard(
        lambda evento: eventos.append(dict(evento)) or _decisao_cognitiva(),
    )

    assert runtime.observar_uma_vez()["status"] == "estabilizando"
    agora[0] = 1.1
    resultado = runtime.observar_uma_vez()

    assert resultado["status"] == "publicada"
    assert eventos and eventos[0]["origem"] == "observador_area_transferencia"
    assert runtime.diagnostico()["reagendadas"] == 0


def test_red_p1d_pendencia_clipboard_usa_fala_materializada_pela_cognicao() -> None:
    eventos: list[dict[str, Any]] = []
    ofertas: list[dict[str, Any]] = []
    runtime, _snapshots, agora = _observar_clipboard(
        lambda evento: eventos.append(evento) or _decisao_cognitiva(),
        oferta_entregue=lambda oferta: ofertas.append(dict(oferta)),
    )

    assert runtime.observar_uma_vez()["status"] == "estabilizando"
    agora[0] = 1.1
    assert runtime.observar_uma_vez()["status"] == "publicada"

    evento = eventos[0]
    fala_sensor = str(evento.get("fala") or "")
    fala_gerada = "Esse erro parece específico. Quer que eu investigue com você?"
    evento["ao_materializar_fala"](fala_gerada)
    evento["ao_iniciar"]()

    assert ofertas[0]["fala"] == fala_gerada
    assert ofertas[0]["fala"] != fala_sensor


class _DiretorCognitivoFake:
    def __init__(self) -> None:
        self.eventos: list[dict[str, Any]] = []

    def considerar(self, evento: dict[str, Any]) -> dict[str, Any]:
        self.eventos.append(dict(evento))
        return _decisao_cognitiva()


def test_red_p1d_visao_jogo_entende_o_mesmo_recibo_cognitivo() -> None:
    diretor = _DiretorCognitivoFake()
    falas_diretas: list[tuple[Any, ...]] = []
    runtime = CoordenadorVisaoJogoRuntime(
        memoria_jogos=SimpleNamespace(),
        observador_inventario_getter=lambda: None,
        diretor_presenca_getter=lambda: diretor,
        recomendar_playlist=lambda _clima: "",
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        decisao_permite_emissao=lambda _decisao: True,
        agendar_fala=lambda *args, **kwargs: falas_diretas.append((*args, kwargs)) or True,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        estado_mental_getter=lambda: {},
        estado_mental_substituir=lambda _estado: None,
        criar_pendencia=lambda **_dados: {},
        registrar_pendencia=lambda _estado, **_dados: {},
        pendencia_ativa=lambda _estado: None,
        limpar_pendencia=lambda _estado: {},
        salvar_memoria=lambda: None,
        clock=lambda: 1000.0,
    )

    aceita = runtime.processar_sugestao_proativa(
        {
            "relevante": True,
            "fala": "Template do sensor que não deve ser emitido.",
            "confianca": 0.92,
            "categoria": "dica",
            "item": "Bota da Tempestade",
            "slot": "botas",
            "motivo": "mais resistência",
            "momento_seguro": True,
        },
        {"chave": "poe2"},
        {"classe": "monge"},
    )

    assert aceita is True
    assert diretor.eventos
    assert falas_diretas == []
