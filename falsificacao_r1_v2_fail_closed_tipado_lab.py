#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R1-V2 — LAB DE FALSIFICAÇÃO DO FAIL-CLOSED MONOTÔNICO

NÃO altera produção. Usa parser/seletor/consumidores reais e injeta somente
esta SAÍDA conceitual do candidato:

    TIPADA(LER) + no-match -> veto_execucao_operacional sticky no turno

EXIT 0 = candidato sobreviveu ao LAB (ainda não aprova patch)
EXIT 1 = lock/import/controle inválido
EXIT 2 = candidato falsificado
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

HEAD = "dc72f429088949211b86bf0160de518bfd1bbccc"
BLOBS = {
    "mente_laylay/cognicao/modalidade_turno.py": "685e6728fa793ba52f390a9b68f467ac9d5fdb8a",
    "mente_laylay/cognicao/orquestrador_turno_runtime.py": "6105e8307e863f1a52a247e252cbbab130e7a3bd",
    "mente_laylay/cognicao/arbitro_turno.py": "52334027b1ee8cbfca23f5d2b63bdd280c168785",
    "mente_laylay/cognicao/decisao_turno.py": "a8d851db539b0c52822d3ecbde93f4e6928d2870",
    "mente_laylay/memoria_mental/compatibilidade_contexto.py": "95f93c29df0c91bf3f55a8b10236a06f8d0be3db",
    "mente_laylay/autonomia/comandos_imediatos.py": "9a216e2780a4b490c0b6acc1c8232e1f5489a0df",
    "mente_laylay/autonomia/porteiro_acoes.py": "b47c53f8e464f4e0ae4e4cb7549f46bdf9ce3494",
}

TIPADO = "Leia de novo."
GENERICO = "tenta de novo"


def git(repo: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(
        ["git", *args], cwd=str(repo), text=True, encoding="utf-8",
        errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def repo_root() -> Path:
    for start in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (start, *start.parents):
            if (p / ".git").exists() and (p / "laylay.py").is_file():
                return p
    raise RuntimeError("execute dentro do repositório da Laylay")


def source(repo: Path, rel: str) -> str:
    return git(repo, "show", f"HEAD:{rel}")


def main() -> int:
    print("R1-V2 — FALSIFICAÇÃO FAIL-CLOSED TIPADO")
    print("=" * 76)
    try:
        repo = repo_root()
    except Exception as exc:
        print(f"🟠 EXIT 1 — {exc}")
        return 1

    premissas: list[str] = []
    falhas: list[str] = []

    print("\n## GUARDS / LOCKS")
    print("-" * 76)
    head = git(repo, "rev-parse", "HEAD")
    print(f"HEAD {'PASS' if head == HEAD else 'FAIL'} {head}")
    if head != HEAD:
        premissas.append(f"HEAD mudou: esperado={HEAD} atual={head}")

    for rel, esperado in BLOBS.items():
        atual = git(repo, "rev-parse", f"HEAD:{rel}", check=False)
        ok = bool(atual) and atual == esperado
        print(f"{rel:<68} {'PASS' if ok else 'FAIL'} {atual or 'ausente'}")
        if not ok:
            premissas.append(f"blob mudou: {rel}")

    dirty = git(repo, "status", "--porcelain", "--", *BLOBS.keys(), check=False)
    print(f"worktree causal {'PASS' if not dirty.strip() else 'FAIL'}")
    if dirty.strip():
        print(dirty)
        premissas.append("worktree causal suja")

    print("\n## WIRING CAUSAL")
    print("-" * 76)
    try:
        src_compat = source(repo, "mente_laylay/memoria_mental/compatibilidade_contexto.py")
        src_orq = source(repo, "mente_laylay/cognicao/orquestrador_turno_runtime.py")
        src_imed = source(repo, "mente_laylay/autonomia/comandos_imediatos.py")
        src_modal = source(repo, "mente_laylay/cognicao/modalidade_turno.py")
        src_arb = source(repo, "mente_laylay/cognicao/arbitro_turno.py")
        src_coord = source(repo, "mente_laylay/autonomia/coordenador_intencao.py")
    except Exception as exc:
        print(f"🟠 EXIT 1 — fonte indisponível: {exc}")
        return 1

    checks = {
        "TIPADA(LER) canônica": (
            'return {"tipo": "tipada", "acao_semantica": "LER", "verbo": verbo}' in src_compat
        ),
        "tipada separada de genérica": (
            "# ROOT R1: repetição tipada nunca cai no fluxo genérico." in src_compat
        ),
        "orquestrador resolve repetição": (
            "resolver_repeticao_operacional_segura(ns, texto)" in src_orq
        ),
        "orquestrador aplica repetição": (
            "aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)" in src_orq
        ),
        "orquestrador conhece veto": "aplicar_veto_canonico" in src_orq,
        "porteiro consulta veto": "if turno_tem_veto_execucao(turno):" in src_imed,
        "veto sticky existe": (
            'return bool(dict(turno or {}).get("veto_execucao_operacional"))' in src_modal
        ),
        "árbitro consulta veto": "elif turno_tem_veto_execucao(leitura):" in src_arb,
        "coordenador consulta veto": "if turno_tem_veto_execucao(turno_congelado):" in src_coord,
    }
    for nome, ok in checks.items():
        print(f"{nome:<42} {'PASS' if ok else 'FAIL'}")
        if not ok:
            premissas.append(f"wiring mudou: {nome}")

    if premissas:
        print("\n🟠 EXIT 1 — LOCK/WIRING/PREMISSA INVÁLIDA")
        for x in premissas:
            print(f"❌ {x}")
        return 1

    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    try:
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto, texto_tem_comando_explicito
        from mente_laylay.cognicao.normalizacao_linguagem import corrigir_erros_portugues_operacionais
        from mente_laylay.memoria_mental.compatibilidade_contexto import classificar_repeticao_curta, resolver_repeticao_ultima_acao
        from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial, registrar_resultado_execucao
        from mente_laylay.cognicao.modalidade_turno import aplicar_veto_canonico, autoriza_execucao_efetiva, classificar_modalidade_turno, turno_tem_veto_execucao
        from mente_laylay.cognicao.orquestrador_turno_runtime import aplicar_repeticao_operacional_ao_turno
        from mente_laylay.autonomia.comandos_imediatos import _candidato_prioritario_autorizado, _candidato_arquivo_prioritario_autorizado
        from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
        from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
        from mente_laylay.cognicao.decisao_turno import filtrar_comandos_pelo_turno
    except Exception as exc:
        print(f"\n🟠 EXIT 1 — IMPORT REAL FALHOU: {type(exc).__name__}: {exc}")
        return 1

    def norm(texto: str) -> str:
        base = str(normalizar_texto(texto) or "").strip()
        try:
            corrigido, _ = corrigir_erros_portugues_operacionais(base)
            return str(corrigido or base).strip()
        except Exception:
            return base

    def turno_base(texto: str) -> dict[str, Any]:
        return classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )

    def registrar(estado: dict[str, Any], intent: str, params: dict[str, Any], status: str, executou: bool, confirmado: bool, texto: str) -> dict[str, Any]:
        return registrar_resultado_execucao(
            estado,
            {
                "intent": intent, "params": dict(params),
                "alvo": params.get("alvo") or params.get("caminho") or "",
                "status": status, "executou": executou,
                "confirmado": confirmado, "origem": "lab_r1_v2",
            },
            texto, executou, origem="lab_r1_v2", status=status,
        )

    def estado_iot() -> dict[str, Any]:
        return registrar(
            estado_mental_inicial(), "IOT_CONTROL",
            {"acao": "ligar", "alvo": "lampada_quarto"},
            "ligado", True, True, "Liga a lâmpada.",
        )

    def estado_leitura_iot() -> dict[str, Any]:
        e = registrar(
            estado_mental_inicial(), "FILE_READ",
            {"caminho": r"C:\tmp\r1_v2_alfa.txt", "alvo": "r1_v2_alfa.txt"},
            "conteudo_lido", True, True, "Leia r1_v2_alfa.txt.",
        )
        return registrar(
            e, "IOT_CONTROL", {"acao": "ligar", "alvo": "lampada_quarto"},
            "ligado", True, True, "Liga a lâmpada.",
        )

    def estado_delete_falho() -> dict[str, Any]:
        return registrar(
            estado_mental_inicial(), "DELETE_ITEM",
            {"alvo": r"C:\tmp\r1_v2_inexistente.txt"},
            "nao_encontrado", False, False, "Apaga r1_v2_inexistente.txt.",
        )

    def intervir(texto: str, estado: dict[str, Any]):
        turno = turno_base(texto)
        cls = classificar_repeticao_curta(texto, norm)
        rep = resolver_repeticao_ultima_acao(texto, estado, norm)
        if cls.get("tipo") == "tipada" and rep is None:
            turno = aplicar_veto_canonico(
                turno,
                texto=texto,
                modalidade="comando",
                natureza="repeticao_tipificada_sem_alvo_compativel",
                motivo="INTERVENCAO_R1_V2: tipada reconhecida sem alvo compatível",
                requer_esclarecimento=False,
                origem_veto="lab_r1_v2_intervencao",
            )
        elif isinstance(rep, dict):
            turno = aplicar_repeticao_operacional_ao_turno(turno, rep)
        return turno, cls, rep

    print("\n## FASE 1 — CONTROLES DO SELETOR REAL")
    print("-" * 76)
    ea, ed, ee, ef = estado_leitura_iot(), estado_iot(), estado_iot(), estado_delete_falho()
    a = resolver_repeticao_ultima_acao(TIPADO, ea, norm)
    d = resolver_repeticao_ultima_acao("de novo", ed, norm)
    e = resolver_repeticao_ultima_acao(TIPADO, ee, norm)
    f1 = resolver_repeticao_ultima_acao(TIPADO, ef, norm)
    f2 = resolver_repeticao_ultima_acao(GENERICO, ef, norm)
    print("A ", a)
    print("D ", d)
    print("E ", e)
    print("F1", f1)
    print("F2", f2)
    if str((a or {}).get("intent") or "") != "FILE_READ": premissas.append("A não recuperou FILE_READ")
    if str((d or {}).get("intent") or "") != "IOT_CONTROL": premissas.append("D genérico não recuperou IOT_CONTROL")
    if e is not None: premissas.append("E tipado sem leitura não retornou None")
    if f1 is not None: premissas.append("F1 tipado caiu no DELETE_ITEM")
    if str((f2 or {}).get("intent") or "") != "DELETE_ITEM": premissas.append("F2 genérico não recuperou DELETE_ITEM")
    if premissas:
        print("\n🟠 EXIT 1 — CONTROLE DO SELETOR INVÁLIDO")
        for x in premissas: print(f"❌ {x}")
        return 1

    print("\n## FASE 2 — INTERVENÇÃO CANDIDATA")
    print("-" * 76)
    ta, _, _ = intervir(TIPADO, ea)
    td, _, _ = intervir("de novo", ed)
    te, ce, re = intervir(TIPADO, ee)
    tf1, _, _ = intervir(TIPADO, ef)
    tf2, _, _ = intervir(GENERICO, ef)
    for nome, t in (("A", ta), ("D", td), ("E", te), ("F1", tf1), ("F2", tf2)):
        print(f"{nome:<3} auth_raw={bool(t.get('autoriza_execucao'))} auth_efetiva={autoriza_execucao_efetiva(t)} veto={turno_tem_veto_execucao(t)} rep={t.get('repeticao_operacional')!r}")
    if turno_tem_veto_execucao(ta) or not autoriza_execucao_efetiva(ta): falhas.append("A legítimo foi bloqueado")
    if turno_tem_veto_execucao(td) or not autoriza_execucao_efetiva(td): falhas.append("D genérico foi bloqueado")
    if not turno_tem_veto_execucao(te) or autoriza_execucao_efetiva(te): falhas.append("E não ficou fail-closed")
    if not turno_tem_veto_execucao(tf1): falhas.append("F1 não recebeu veto")
    if turno_tem_veto_execucao(tf2) or not autoriza_execucao_efetiva(tf2): falhas.append("F2 genérico foi bloqueado")

    print("\n## FASE 3 — PORTEIROS PRIORITÁRIOS")
    print("-" * 76)
    for intent, params in (
        ("IOT_CONTROL", {"acao": "ligar", "alvo": "lampada_quarto"}),
        ("IOT_STATUS", {"alvo": "lampada_quarto"}),
        ("LIST_TABS", {}),
    ):
        permitido = _candidato_prioritario_autorizado({"intent": intent, "params": params}, te)
        print(f"{intent:<16} permitido={permitido}")
        if permitido: falhas.append(f"porteiro deixou {intent} furar o veto")
    arq = _candidato_arquivo_prioritario_autorizado(
        {"intent": "FILE_SEARCH", "params": {"query": "x"}}, TIPADO, te, ee
    )
    print(f"{'FILE_SEARCH':<16} permitido={arq}")
    if arq: falhas.append("porta de arquivos deixou FILE_SEARCH furar veto")

    print("\n## FASE 4 — ÁRBITRO / COORDENADOR / FILTRO LLM")
    print("-" * 76)
    cand = CandidatoDecisao(
        tipo="comando_contextual",
        valor={"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}},
        origem="lab_escape_semantico", confianca=0.99,
        evidencia=("escape RT1-E",),
    )
    arb = arbitrar_turno(TIPADO, [cand], turno=te, retrato={})
    print("árbitro decisão:", arb.get("decisao"))
    if isinstance(arb.get("decisao"), dict): falhas.append("árbitro aceitou IoT sob veto")

    try:
        dec, origem = resolver_intencao(TIPADO, "lab_r1_v2", {"turno_atual": dict(te)})
        print("coordenador:", dec, origem)
        if isinstance(dec, dict): falhas.append("coordenador materializou comando sob veto")
        if origem != "veto_operacional_turno": falhas.append(f"coordenador não reportou veto: {origem!r}")
    except Exception as exc:
        premissas.append(f"coordenador não pôde ser medido: {type(exc).__name__}: {exc}")

    try:
        filtrado = filtrar_comandos_pelo_turno(
            [{"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}],
            turno=te,
            plano={"requer_execucao": True, "decisao_turno": {"permite_acao": False, "proprietario": "conversa"}},
            retrato={},
        )
        comandos = list(filtrado.get("comandos") or [])
        print("filtro LLM:", comandos)
        if comandos: falhas.append("filtro LLM deixou comando sob veto")
    except Exception as exc:
        premissas.append(f"filtro LLM não pôde ser medido: {type(exc).__name__}: {exc}")

    print("\n## FASE 5 — KILLER DE MONOTONICIDADE")
    print("-" * 76)
    reauth = aplicar_repeticao_operacional_ao_turno(
        dict(te), {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}
    )
    sticky = turno_tem_veto_execucao(reauth)
    auth = autoriza_execucao_efetiva(reauth)
    gate = _candidato_prioritario_autorizado(
        {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}, reauth
    )
    print(f"sticky={sticky} auth_efetiva={auth} porteiro_permitiu={gate}")
    if not sticky: falhas.append("reauth stale apagou veto sticky")
    if auth: falhas.append("reauth stale recuperou autoridade efetiva")
    if gate: falhas.append("porteiro permitiu IoT após reauth stale")

    if premissas:
        print("\n🟠 EXIT 1 — HARNESS/PREMISSA INVÁLIDA")
        for x in premissas: print(f"❌ {x}")
        return 1
    if falhas:
        print("\n🔴 EXIT 2 — ARQUITETURA R1-V2 FALSIFICADA")
        for x in falhas: print(f"❌ {x}")
        print("Não criar patch; a primeira falha é a nova fronteira de investigação.")
        return 2

    print("\n🟢 EXIT 0 — CANDIDATO R1-V2 SOBREVIVEU AO LAB")
    print("TIPADA(LER)+no-match ficou fail-closed nos consumidores medidos.")
    print("A/D/F2 continuaram válidos. Isto ainda NÃO substitui runtime-real RT1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
