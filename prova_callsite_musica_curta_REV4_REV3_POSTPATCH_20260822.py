from __future__ import annotations

import ast
from contextlib import redirect_stdout
import hashlib
import inspect
import io
import json
from pathlib import Path
import subprocess
import sys
import textwrap
import time
from typing import Any


REPO = Path(__file__).resolve().parent
RESULTADO = REPO / "CALLSITE_MUSICA_CURTA_REV4_POSTPATCH_RESULTADO_REV1_20260822.json"

HEAD_ESPERADO = "bdeaee9fbb8f26976fc2c00c612fd45402a6bf3f"
MODALIDADE_SHA_ESPERADO = (
    "ac71f49ee9cfb67e6f2aa09a9b3f7b5196300d34fab3add3a91d142d6f382124"
)
GRAMATICA_SHA_ESPERADO = (
    "0f07d8954dafd3ba2d0b12202057eba35ca71e620a5f9051057766e077ed2994"
)
CALLSITE_BLOB_ESPERADO = "ad60a3e6d4f471128452e33f058718465d8f80a0"
GATE_SOURCE_SHA_ESPERADO = (
    "78789862c5c9cb2812cf040a422345ed990ee0091b1bd29811a1ed0ff4c9689f"
)


class ProvaInvalida(RuntimeError):
    pass


class BypassConfirmado(RuntimeError):
    pass


def _sha256(arquivo: Path) -> str:
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    concluido = subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return concluido.stdout.strip()


def _corpus_gate_real() -> list[str]:
    formas: set[str] = set()
    for verbo in ("tenta", "manda", "coloca", "toca"):
        for outro in ("outra", "outro"):
            for alvo in ("", " musica", " faixa"):
                formas.add(f"{verbo} {outro}{alvo}")
    for verbo in ("continua", "continue"):
        for alvo in ("", " a", " essa", " ela", " musica", " tocando"):
            formas.add(f"{verbo}{alvo}")
    formas.update(("pausa", "pause"))
    for artigo in ("", "a "):
        for direcao in ("proxima", "proximo", "pula", "pule"):
            formas.add(f"{artigo}{direcao}")
        formas.add(f"{artigo}anterior")
    for preposicao in ("para", "pra"):
        for artigo in ("", "a "):
            formas.add(f"volta {preposicao} {artigo}anterior")
    return sorted(formas)


def _candidato(intent: str) -> dict[str, Any]:
    if intent == "MUSIC_SEARCH":
        return {
            "intent": intent,
            "params": {"query": "canario post-patch", "origem": "prova_postpatch"},
        }
    return {
        "intent": intent,
        "params": {"acao": "next", "platform": "music"},
    }


def _atravessar_callsite(
    texto: str,
    turno: dict[str, Any],
    *,
    intent: str,
) -> dict[str, Any]:
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime

    class Estado:
        mental = {
            "turno_atual": dict(turno),
            "ultima_acao_intent": "MUSIC_SEARCH",
            "ultima_acao_params": {"query": "musica anterior"},
            "ultima_acao_alvo": "faixa anterior",
            "ultima_habilidade": "musica",
            "ts": time.time(),
        }

    candidato = _candidato(intent)
    resolvedor: list[tuple[str, dict[str, Any]]] = []
    executor: list[tuple[dict[str, Any], str]] = []
    registros: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def resolver(recebido: str) -> dict[str, Any]:
        resolvedor.append((recebido, candidato))
        return candidato

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": Estado(),
            "processar_comandos_em_cadeia": lambda *_args: False,
            "_resolver_comando_midia_contextual_forcado": resolver,
            "executar_intencao": (
                lambda detectado, original: executor.append((detectado, original)) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
        },
        loop_getter=lambda: None,
    )
    saida = io.StringIO()
    with redirect_stdout(saida):
        retorno = runtime.processar_prioritarios(texto)
    return {
        "retorno": retorno,
        "resolvedor_chamadas": len(resolvedor),
        "executor_chamadas": len(executor),
        "registros": len(registros),
        "log": saida.getvalue().strip().splitlines(),
    }


def _validar_estrutura() -> dict[str, Any]:
    from mente_laylay.autonomia.comandos_imediatos import (
        ComandosImediatosRuntime,
        texto_pede_continuacao_musical_curta,
    )

    fonte_metodo = textwrap.dedent(
        inspect.getsource(ComandosImediatosRuntime.processar_prioritarios)
    )
    ast.parse(fonte_metodo)
    p0 = fonte_metodo.find("bloqueia_execucao_operacional_prioritaria(")
    gate = fonte_metodo.find("if texto_pede_continuacao_musical_curta(texto):")
    helper = fonte_metodo.find("_candidato_prioritario_autorizado(", gate)
    executor = fonte_metodo.find("executar(continuacao_musical, texto)", helper)
    if min(p0, gate, helper, executor) < 0:
        raise ProvaInvalida("estrutura esperada não foi localizada na fonte real")
    if not p0 < gate < helper < executor:
        raise ProvaInvalida("ordem P0 -> gate -> helper -> executor não foi preservada")

    gate_sha = hashlib.sha256(
        inspect.getsource(texto_pede_continuacao_musical_curta).encode("utf-8")
    ).hexdigest()
    if gate_sha != GATE_SOURCE_SHA_ESPERADO:
        raise ProvaInvalida(f"gate source SHA inesperado: {gate_sha}")
    return {
        "p0_antes_gate": True,
        "gate_antes_helper": True,
        "helper_antes_executor": True,
        "helper_local_na_fatia": True,
        "gate_source_sha": gate_sha,
    }


def _validar_locks() -> dict[str, str]:
    modalidade = REPO / "mente_laylay" / "cognicao" / "modalidade_turno.py"
    gramatica = REPO / "mente_laylay" / "cognicao" / "gramatica_musical.py"
    callsite = REPO / "mente_laylay" / "autonomia" / "comandos_imediatos.py"
    locks = {
        "head": _git("rev-parse", "HEAD"),
        "modalidade_sha256": _sha256(modalidade),
        "gramatica_sha256": _sha256(gramatica),
        "callsite_blob": _git("hash-object", str(callsite)),
    }
    esperados = {
        "head": HEAD_ESPERADO,
        "modalidade_sha256": MODALIDADE_SHA_ESPERADO,
        "gramatica_sha256": GRAMATICA_SHA_ESPERADO,
        "callsite_blob": CALLSITE_BLOB_ESPERADO,
    }
    divergencias = {
        chave: {"esperado": esperados[chave], "obtido": valor}
        for chave, valor in locks.items()
        if valor != esperados[chave]
    }
    if divergencias:
        raise ProvaInvalida(
            "locks divergentes: " + json.dumps(divergencias, ensure_ascii=False)
        )
    return locks


def _analisar_matriz() -> tuple[list[dict[str, Any]], dict[str, int]]:
    from mente_laylay.autonomia.comandos_imediatos import (
        _candidato_prioritario_autorizado,
        texto_pede_continuacao_musical_curta,
    )
    from mente_laylay.cognicao.modalidade_turno import (
        bloqueia_execucao_operacional_prioritaria,
        classificar_modalidade_turno,
    )

    linhas: list[dict[str, Any]] = []
    for texto in _corpus_gate_real():
        turno = classificar_modalidade_turno(texto)
        gate = texto_pede_continuacao_musical_curta(texto)
        barreira = bloqueia_execucao_operacional_prioritaria(
            texto,
            classificacao=turno,
        )
        allow_global = bool(gate and not barreira)
        allow_local = bool(
            allow_global
            and _candidato_prioritario_autorizado(
                _candidato("MEDIA_CONTROL"),
                turno,
            )
        )
        grupo = "G2_AUTORIZADO"
        if allow_global and not allow_local:
            grupo = "G1_BLOQUEIO_LOCAL"
        elif not allow_global:
            grupo = "G3_BLOQUEIO_P0"
        linhas.append({
            "texto": texto,
            "modalidade": turno.get("modalidade"),
            "natureza_acao": turno.get("natureza_acao"),
            "auth": bool(turno.get("autoriza_execucao")),
            "veto": bool(turno.get("veto_execucao_operacional")),
            "gate": gate,
            "barreira_bloqueia": barreira,
            "allow_global": allow_global,
            "allow_local": allow_local,
            "grupo": grupo,
            "turno": turno,
        })

    contagens = {
        "formas": len(linhas),
        "allow_global": sum(1 for linha in linhas if linha["allow_global"]),
        "allow_local": sum(1 for linha in linhas if linha["allow_local"]),
        "g1_bloqueio_local": sum(
            1 for linha in linhas if linha["grupo"] == "G1_BLOQUEIO_LOCAL"
        ),
        "g2_autorizado": sum(
            1 for linha in linhas if linha["grupo"] == "G2_AUTORIZADO"
        ),
        "g3_bloqueio_p0": sum(
            1 for linha in linhas if linha["grupo"] == "G3_BLOQUEIO_P0"
        ),
    }
    esperado = {
        "formas": 52,
        "allow_global": 40,
        "allow_local": 25,
        "g1_bloqueio_local": 15,
        "g2_autorizado": 25,
        "g3_bloqueio_p0": 12,
    }
    if contagens != esperado:
        raise ProvaInvalida(
            "matriz inesperada: "
            + json.dumps({"esperado": esperado, "obtido": contagens})
        )
    return linhas, contagens


def _provar_callsite(linhas: list[dict[str, Any]]) -> dict[str, Any]:
    resumo = {
        "execucoes_g1_proibidas": 0,
        "execucoes_g2_esperadas": 0,
        "resolvedores_g3_proibidos": 0,
        "casos_executados": 0,
    }
    detalhes: list[dict[str, Any]] = []
    for linha in linhas:
        for intent in ("MEDIA_CONTROL", "MUSIC_SEARCH"):
            travessia = _atravessar_callsite(
                str(linha["texto"]),
                dict(linha["turno"]),
                intent=intent,
            )
            resumo["casos_executados"] += 1
            grupo = str(linha["grupo"])
            if grupo == "G1_BLOQUEIO_LOCAL":
                resumo["execucoes_g1_proibidas"] += travessia["executor_chamadas"]
                ok = (
                    travessia["retorno"] is False
                    and travessia["resolvedor_chamadas"] == 1
                    and travessia["executor_chamadas"] == 0
                )
            elif grupo == "G2_AUTORIZADO":
                resumo["execucoes_g2_esperadas"] += travessia["executor_chamadas"]
                ok = (
                    travessia["retorno"] is True
                    and travessia["resolvedor_chamadas"] == 1
                    and travessia["executor_chamadas"] == 1
                )
            else:
                resumo["resolvedores_g3_proibidos"] += travessia["resolvedor_chamadas"]
                ok = (
                    travessia["retorno"] is False
                    and travessia["resolvedor_chamadas"] == 0
                    and travessia["executor_chamadas"] == 0
                )
            detalhes.append({
                "texto": linha["texto"],
                "grupo": grupo,
                "intent_canario": intent,
                "ok": ok,
                **travessia,
            })
            if not ok:
                raise BypassConfirmado(
                    "travessia divergente: "
                    + json.dumps(detalhes[-1], ensure_ascii=False)
                )

    if resumo != {
        "execucoes_g1_proibidas": 0,
        "execucoes_g2_esperadas": 50,
        "resolvedores_g3_proibidos": 0,
        "casos_executados": 104,
    }:
        raise BypassConfirmado(
            "contagem operacional inesperada: "
            + json.dumps(resumo, ensure_ascii=False)
        )
    return {"resumo": resumo, "detalhes": detalhes}


def _salvar(resultado: dict[str, Any]) -> None:
    RESULTADO.write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    resultado: dict[str, Any] = {
        "prova": "CALL-SITE MÚSICA CURTA REV4 REV3 PÓS-PATCH",
        "runner_sha256": _sha256(Path(__file__)),
        "executor_fisico": "ZERO",
        "caos_executado": False,
    }
    try:
        resultado["locks"] = _validar_locks()
        resultado["estrutura"] = _validar_estrutura()
        linhas, contagens = _analisar_matriz()
        resultado["matriz"] = contagens
        resultado["linhas"] = linhas
        resultado["callsite"] = _provar_callsite(linhas)
    except ProvaInvalida as erro:
        resultado.update(status="INVALID", erro=str(erro))
        _salvar(resultado)
        print(f"PROVA INVÁLIDA — {erro}")
        print("NÃO rodar caos.")
        return 1
    except BypassConfirmado as erro:
        resultado.update(status="RED", erro=str(erro))
        _salvar(resultado)
        print(f"CALL-SITE RED — {erro}")
        print("NÃO rodar caos.")
        return 2
    except Exception as erro:
        resultado.update(
            status="INVALID",
            erro=f"{type(erro).__name__}: {erro}",
        )
        _salvar(resultado)
        print(f"PROVA INVÁLIDA — {type(erro).__name__}: {erro}")
        print("NÃO rodar caos.")
        return 1

    resultado["status"] = "PASS"
    _salvar(resultado)
    locks = resultado["locks"]
    matriz = resultado["matriz"]
    operacional = resultado["callsite"]["resumo"]
    print("PROVA CALL-SITE PÓS-PATCH — MÚSICA CURTA — REV4 / REV3")
    print(f"HEAD                     : {locks['head']}")
    print(f"modalidade SHA           : {locks['modalidade_sha256']}")
    print(f"gramática SHA            : {locks['gramatica_sha256']}")
    print(f"call-site blob           : {locks['callsite_blob']}")
    print(f"runner SHA               : {resultado['runner_sha256']}")
    print("executor                 : CANÁRIO / ZERO FÍSICO")
    print("caos                     : NÃO EXECUTADO")
    print()
    print("--- ESTRUTURA REAL PÓS-PATCH ---")
    print("barreira P0 antes do gate ........ PASS")
    print("gate antes do helper local ....... PASS")
    print("helper local antes do executor ... PASS")
    print("helper local na fatia ............ SIM")
    print(f"gate source SHA .................. {resultado['estrutura']['gate_source_sha']}")
    print()
    print("--- MATRIZ DAS 52 FORMAS ---")
    print(f"formas analisadas ................. {matriz['formas']}")
    print(f"allow global ...................... {matriz['allow_global']}")
    print(f"allow local ....................... {matriz['allow_local']}")
    print(f"G1 bloqueadas pelo helper local ... {matriz['g1_bloqueio_local']}")
    print(f"G2 autorizadas .................... {matriz['g2_autorizado']}")
    print(f"G3 bloqueadas pela P0 ............. {matriz['g3_bloqueio_p0']}")
    print()
    print("--- TRAVESSIA OPERACIONAL REAL ---")
    print(f"casos call-site executados ........ {operacional['casos_executados']}")
    print(f"execuções proibidas em G1 ......... {operacional['execucoes_g1_proibidas']}")
    print(f"execuções esperadas em G2 ......... {operacional['execucoes_g2_esperadas']}")
    print(f"resolvedores alcançados em G3 ..... {operacional['resolvedores_g3_proibidos']}")
    print()
    print("CALL-SITE PÓS-PATCH — PASS.")
    print("As 15 divergências externas agora morrem no porteiro local.")
    print("Nenhum executor físico e nenhum roteiro de caos foram chamados.")
    print(f"resultado: {RESULTADO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
