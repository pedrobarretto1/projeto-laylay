"""P3-B RED — rotina aprendida e musica usam o contrato unico de presenca."""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Any

from mente_laylay.memoria_mental.aprendizado_runtime import AprendizadoRuntime


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


def _runtime(
    tmp_path: Path,
    *,
    estado: dict[str, Any],
    contexto: dict[str, Any],
) -> AprendizadoRuntime:
    return AprendizadoRuntime(
        pasta_memoria=str(tmp_path),
        arquivo_rotina=str(tmp_path / "rotina.json"),
        arquivo_musica_historico=str(tmp_path / "musica.json"),
        arquivo_musica_feedback=str(tmp_path / "feedback.json"),
        contexto_getter=lambda: contexto,
        estado_getter=lambda: estado,
        estado_setter=lambda **campos: estado.update(campos),
        log=lambda *_args: None,
    )


def test_red_p3b_rotina_aprendida_publica_evento_e_espera_entrega_para_pendencia(
    tmp_path: Path,
) -> None:
    hora = datetime.now().strftime("%H:00")
    dados = {
        hora: {
            "janelas": ["visual studio code - projeto laylay"] * 10,
            "assuntos": ["Programacao"] * 10,
        },
        **{
            f"2026-08-{dia:02d} 00:00": {"janelas": [], "assuntos": []}
            for dia in range(1, 7)
        },
    }
    estado: dict[str, Any] = {
        "rotina_dados_diarios": dados,
        "rotina_feedback_pesos": {},
        "rotina_ultima_sugestao": 0.0,
    }
    continuidades = {"rotina_sugestao_pendente": None}
    eventos: list[dict[str, Any]] = []
    vozes_diretas: list[tuple[Any, ...]] = []
    contexto = {
        "continuidades_get": lambda chave: continuidades.get(chave),
        "continuidades_set": lambda chave, valor: continuidades.__setitem__(chave, valor),
        "contexto_aponta_descanso": lambda: False,
        "considerar_presenca": _aceitar_evento(eventos),
        # Armadilha arquitetural: o produtor nao pode mais possuir esta saida.
        "agendar_fala_proativa": lambda *args, **_kwargs: vozes_diretas.append(args),
    }
    runtime = _runtime(tmp_path, estado=estado, contexto=contexto)

    runtime.analisar_e_sugerir_rotina(
        dias_para_aprender=7,
        limite_rejeicao=3,
    )

    assert vozes_diretas == []
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["natureza"] == "evento"
    assert evento["origem"] == "aprendizado_rotina"
    assert evento["dominio"] == "rotina"
    assert evento["autoridade_usuario"] is False
    assert evento["permissao_execucao"] is False
    assert evento["executavel"] is False
    assert evento["acao_proposta"]["intent"] == "OPEN_APP"
    assert "visual studio code" in evento["acao_proposta"]["params"]["app"]
    assert "fala" not in evento
    assert continuidades["rotina_sugestao_pendente"] is None
    assert estado["rotina_ultima_sugestao"] == 0.0

    evento["ao_concluir"](True, "entregue")

    assert continuidades["rotina_sugestao_pendente"]["app"].startswith(
        "visual studio code"
    )
    assert estado["rotina_ultima_sugestao"] > 0.0


def test_red_p3b_reproducao_musical_vira_evento_sem_autoplay_ou_permissao(
    tmp_path: Path,
) -> None:
    estado: dict[str, Any] = {"musica_dados_diarios": {}}
    eventos: list[dict[str, Any]] = []
    runtime = _runtime(
        tmp_path,
        estado=estado,
        contexto={"considerar_presenca": _aceitar_evento(eventos)},
    )

    runtime.musica_registrar_historico("Nirvana - Come As You Are - YouTube")

    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["natureza"] == "evento"
    assert evento["origem"] == "aprendizado_musical"
    assert evento["dominio"] == "musica"
    assert evento["categoria"] == "musica"
    assert evento["autoridade_usuario"] is False
    assert evento["permissao_execucao"] is False
    assert evento["executar_automaticamente"] is False
    assert evento["executavel"] is False
    assert not evento.get("acao_proposta")
    assert "Nirvana - Come As You Are" in evento["evidencias"]
    assert "fala" not in evento


def test_red_p3b_root_conecta_aprendizado_ao_diretor_sem_porta_de_voz() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    chamada: ast.Call | None = None
    for no in arvore.body:
        if not isinstance(no, ast.Assign) or not isinstance(no.value, ast.Call):
            continue
        if any(
            isinstance(alvo, ast.Name) and alvo.id == "_aprendizado_runtime"
            for alvo in no.targets
        ):
            chamada = no.value
            break

    assert chamada is not None
    contexto_getter = next(
        item.value
        for item in chamada.keywords
        if item.arg == "contexto_getter"
    )
    assert isinstance(contexto_getter, ast.Lambda)
    assert isinstance(contexto_getter.body, ast.Dict)
    portas = {
        chave.value: valor
        for chave, valor in zip(contexto_getter.body.keys, contexto_getter.body.values)
        if isinstance(chave, ast.Constant) and isinstance(chave.value, str)
    }

    assert "considerar_presenca" in portas
    assert "_diretor_presenca_runtime.considerar" in ast.unparse(
        portas["considerar_presenca"]
    )
    assert "agendar_fala_proativa" not in portas
