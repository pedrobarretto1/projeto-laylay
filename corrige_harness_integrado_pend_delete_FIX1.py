#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correção cirúrgica do harness integrado V2.5.1.

NÃO altera produção. Atua somente em:
  falsificacao_candidato_final_turno229_LAB_V2_5_1_INTEGRADO.py

Mudança permitida:
  A.pendencia_delete() -> A.pend_delete()

Exige exatamente 3 ocorrências antigas. Depois:
- py_compile do integrado;
- AST parse;
- varredura de TODAS as referências A.* e B.* contra os exports estáticos
  dos artefatos exatos A/B existentes na raiz.

EXIT 0 = patch aplicado + preflight estático PASS.
EXIT 1 = premissa/arquivo divergente; nada é alterado ou patch é revertido.
"""
from __future__ import annotations

import ast
import hashlib
import py_compile
import sys
from pathlib import Path

TARGET="falsificacao_candidato_final_turno229_LAB_V2_5_1_INTEGRADO.py"
A_FILE="falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py"
B_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"
A_SHA="cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f"
B_SHA="29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab"
OLD=b"A.pendencia_delete()"
NEW=b"A.pend_delete()"
EXPECTED_COUNT=3


def sha256(p: Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def exports_estaticos(path: Path)->set[str]:
    tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    out=set()
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name): out.add(t.id)
        elif isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name):
            out.add(n.target.id)
        elif isinstance(n,(ast.Import,ast.ImportFrom)):
            for a in n.names:
                out.add(a.asname or a.name.split(".")[-1])
    return out


def refs_alias(tree: ast.AST, alias: str)->set[str]:
    refs=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id==alias:
            refs.add(n.attr)
    return refs


def main()->int:
    root=Path.cwd().resolve()
    target=root/TARGET; af=root/A_FILE; bf=root/B_FILE
    print("FIX1 — HARNESS INTEGRADO / pendencia_delete -> pend_delete")
    print("="*78)
    for p in (target,af,bf):
        if not p.is_file():
            print(f"🟠 EXIT 1 — ausente: {p.name}")
            return 1
    if sha256(af)!=A_SHA:
        print("🟠 EXIT 1 — artefato A divergiu",sha256(af)); return 1
    if sha256(bf)!=B_SHA:
        print("🟠 EXIT 1 — artefato B divergiu",sha256(bf)); return 1

    original=target.read_bytes()
    count=original.count(OLD)
    already=original.count(NEW)
    print(f"ocorrências antigas ........ {count}")
    print(f"ocorrências corretas antes . {already}")
    if count!=EXPECTED_COUNT:
        print(f"🟠 EXIT 1 — esperava exatamente {EXPECTED_COUNT} chamadas erradas; arquivo divergiu")
        return 1

    patched=original.replace(OLD,NEW)
    # Garantias byte-level: nenhuma outra transformação.
    if patched.count(OLD)!=0 or patched.count(NEW)<EXPECTED_COUNT:
        print("🟠 EXIT 1 — pós-condição byte-level falhou")
        return 1

    target.write_bytes(patched)
    try:
        py_compile.compile(str(target),doraise=True)
        src=target.read_text(encoding="utf-8")
        tree=ast.parse(src,filename=str(target))
        a_exports=exports_estaticos(af)
        b_exports=exports_estaticos(bf)
        a_refs=refs_alias(tree,"A")
        b_refs=refs_alias(tree,"B")
        missing_a=sorted(a_refs-a_exports)
        missing_b=sorted(b_refs-b_exports)
        print("py_compile ............... PASS")
        print("AST ...................... PASS")
        print("A.* refs .................",sorted(a_refs))
        print("A.* faltantes ............",missing_a or "NONE")
        print("B.* refs .................",sorted(b_refs))
        print("B.* faltantes ............",missing_b or "NONE")
        if missing_a or missing_b:
            raise RuntimeError(f"referências inválidas: A={missing_a} B={missing_b}")
    except Exception as e:
        target.write_bytes(original)
        print(f"🟠 EXIT 1 — preflight falhou; patch REVERTIDO: {type(e).__name__}: {e}")
        return 1

    print("\nPATCH BYTE-LEVEL")
    print(f"antes sha256 ............. {hashlib.sha256(original).hexdigest()}")
    print(f"depois sha256 ............ {hashlib.sha256(patched).hexdigest()}")
    print(f"substituições ............ {EXPECTED_COUNT}")
    print("produção alterada ........ NÃO")
    print("\n🟢 EXIT 0 — FIX1 APLICADO E PREFLIGHT ESTÁTICO PASS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
