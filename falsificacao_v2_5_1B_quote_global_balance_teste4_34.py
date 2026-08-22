#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FALSIFICAÇÃO V2.5.1-B — GLOBAL QUOTE BALANCE / TESTE 4.34.

NÃO ALTERA PRODUÇÃO. EFEITO FÍSICO ZERO.

Contexto
========
A REV4.1 corrigiu o FIRST RED 4.33 provando um par de quote apertado ao redor
 de `nao.<ext>`. A segunda revisão integral encontrou uma lacuna diferente:
 o helper valida o par LOCAL, mas não prova que a fala inteira ficou sem quote
 órfã/crossing antes ou depois desse par.

Exemplos suspeitos:

    cria arquivo chamado "nao.txt""
    cria arquivo chamado 'nao.txt''
    cria arquivo chamado “nao.txt””
    cria "arquivo chamado "nao.txt"
    cria “arquivo chamado “nao.txt”
    cria arquivo chamado "nao.txt" e fecha o opera"

Invariante soberana
===================
Quote só pode fortalecer literalidade quando a estrutura relevante está
provadamente balanceada/orientada. Quote órfã em qualquer lado da região que
sustenta o filename nunca pode suprimir fail-closed.

FIRST boundary esperado caso vulnerável:

    REV4.1.marcador_atom_rev4()

O roteador é apenas amplificador downstream; não recebe crédito de autoridade.

EXIT
====
0 = REV4.1 sobreviveu à família global-quote.
1 = lock/wiring/artefato/precondição/harness inválido.
2 = REV4.1 falsificada; FIRST RED manda.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HEAD="5cd3582562291a947464c3bcdca3bc7b83e036d8"
REV4_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV4_1_MERGE_FAILCLOSED.py"
REV4_SHA="19632b091934ff1392e83f7b2f4e62bd50b778ef38bfdb7be6426e2f5ab5e4fe"
REV3_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"
REV3_SHA="29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"

BLOBS={
    "mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
    "mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
    "mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
    "mente_laylay/arquivos/roteador_arquivos.py":"36fc40861db60c0aabe324669272c28d1d89d2f5",
    "mente_laylay/arquivos/nome_natural.py":"9f6f7d10fa7ac0baae2c11204b984a1d451a5c5e",
    "mente_laylay/autonomia/coordenador_intencao.py":"de8a893cd60ab44ad9bc3437d01db15ba54fb367",
}


def git(repo,*args,check=True):
    q=subprocess.run(
        ["git",*args], cwd=str(repo), text=True, encoding="utf-8",
        errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and q.returncode:
        raise RuntimeError(q.stderr.strip() or q.stdout.strip())
    return q.stdout.strip()


def repo_root():
    seen=set()
    for start in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (start,*start.parents):
            if x in seen: continue
            seen.add(x)
            if (x/".git").exists() and (x/"laylay.py").exists(): return x
    raise RuntimeError("execute este teste dentro do repositório Laylay")


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def title(s): print("\n# "+s+"\n"+"="*98)


def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m


def marker_span(texto):
    m=re.search(r"\b(?:nao|não)\b",str(texto or ""),re.IGNORECASE)
    return (m.start(),m.end()) if m else (-1,-1)


def auth(base,t): return bool(base.autoriza_execucao_efetiva(t))
def veto(base,t): return bool(base.turno_tem_veto_execucao(t))


def main():
    print("FALSIFICAÇÃO V2.5.1-B — GLOBAL QUOTE BALANCE / TESTE 4.34")
    print("="*98)
    print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")

    try: repo=repo_root()
    except Exception as e:
        print(f"\n🟠 EXIT 1 — {e}"); return 1

    title("GUARDS / LOCKS / ARTEFATOS EXATOS")
    bad=[]
    h=git(repo,"rev-parse","HEAD")
    print(f"HEAD ........................................ {'PASS' if h==HEAD else 'FAIL'} {h}")
    if h!=HEAD: bad.append("HEAD mudou")
    for f,e in BLOBS.items():
        got=git(repo,"rev-parse",f"HEAD:{f}"); ok=got==e
        print(f"{f:<72} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f"blob mudou: {f}")
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False)
    clean=not dirty.strip()
    print(f"produção causal limpa .................................. {'PASS' if clean else 'FAIL'}")
    if not clean:
        print(dirty); bad.append("produção causal suja")

    for name,expected in ((REV4_FILE,REV4_SHA),(REV3_FILE,REV3_SHA),(BASE_FILE,BASE_SHA)):
        q=repo/name; got=sha(q) if q.is_file() else ""; ok=got==expected
        print(f"{name:<72} {'PASS' if ok else 'FAIL'} {got or 'ausente'}")
        if not ok: bad.append(f"artefato ausente/divergente: {name}")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA")
        for x in bad: print("❌",x)
        return 1

    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        R4=imod("v251b_rev41_434",repo/REV4_FILE)
        R3=imod("v251b_rev3_434",repo/REV3_FILE)
        base=imod("v25_base_434",repo/BASE_FILE)
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
        from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1

    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    regex=R3.regex_atomo_producao(exts)

    def build(texto):
        return R4.construir_turno_rev4(
            texto,base=base,rev3=R3,extensoes=exts,
            resolver_revisao_real=resolver_revisao_intra_turno,
            classificar_real=classificar_modalidade_turno,
            p0_real=_protecao_p0_ato_fala,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )[0]

    title("FASE 0 — CONTROLES REV4.1 QUE DEVEM CONTINUAR VÁLIDOS")
    controls=[
        'cria arquivo nao.txt',
        'cria arquivo chamado "nao.txt"',
        "cria arquivo chamado 'nao.txt'",
        'cria arquivo chamado “nao.txt”',
        'cria arquivo chamado “não.md”',
    ]
    c_ok=[]
    for texto in controls:
        st,en=marker_span(texto); marker=R4.marcador_atom_rev4(texto,st,en,regex=regex)
        t=build(texto)
        ok=bool(marker[0] and auth(base,t) and not veto(base,t))
        c_ok.append(ok)
        print(f"{'PASS' if ok else 'FAIL'} {texto!r} -> marker={marker} veto={veto(base,t)} auth={auth(base,t)}")
    if not all(c_ok):
        print("\n🟠 EXIT 1 — controle positivo REV4.1 divergiu"); return 1

    title("FASE 1 — GLOBAL QUOTE BALANCE: HELPER NÃO PODE TOMAR CRÉDITO")
    killers=[
        ('cria arquivo chamado "nao.txt""',"duplo fechamento ASCII"),
        ("cria arquivo chamado 'nao.txt''","duplo fechamento simples"),
        ('cria arquivo chamado “nao.txt””',"duplo fechamento smart"),
        ('cria "arquivo chamado "nao.txt"',"quote órfã antes do slot ASCII"),
        ('cria “arquivo chamado “nao.txt”',"quote órfã antes do slot smart"),
        ('cria arquivo chamado "nao.txt" "',"quote órfã depois do par ASCII"),
        ('cria arquivo chamado “nao.txt” ”',"quote órfã depois do par smart"),
        ('cria arquivo chamado "nao.txt" e fecha o opera"',"quote atravessa ato posterior ASCII"),
        ('cria arquivo chamado “nao.txt” e fecha o opera”',"quote atravessa ato posterior smart"),
    ]
    reds=[]; observations=[]
    for texto,rotulo in killers:
        st,en=marker_span(texto)
        marker=R4.marcador_atom_rev4(texto,st,en,regex=regex) if st>=0 else (False,"")
        ok=not bool(marker[0])
        observations.append((texto,rotulo,marker,ok))
        print(f"{rotulo:<42} marker={marker} {'PASS' if ok else 'RED'}")
        if not ok and not reds:
            reds.append(f"marcador_atom_rev4 aceitou {rotulo}")

    title("FASE 2 — AUTORIDADE: MALFORMED GLOBAL DEVE FAIL-CLOSED")
    authority=[]
    for texto,rotulo,marker,helper_ok in observations:
        t=build(texto)
        ok=bool(veto(base,t) and not auth(base,t) and not str(t.get("texto_operacional") or ""))
        authority.append(ok)
        print(f"{'PASS' if ok else 'RED '} {rotulo:<42} veto={veto(base,t)} auth={auth(base,t)} op={str(t.get('texto_operacional') or '')!r}")
        if not ok and not reds:
            reds.append(f"autoridade global-quote: {rotulo}")

    title("FASE 3 — AMPLIFICAÇÃO DOWNSTREAM / SEM EXECUÇÃO")
    amplified=[]
    for texto,rotulo,marker,helper_ok in observations:
        t=build(texto)
        if not auth(base,t) or veto(base,t):
            continue
        r,rota,fields=R4.resolver_rev4(
            t,texto,base=base,rev3=R3,
            detectar=detectar_intencao_arquivos,
            normalizar_texto=normalizar_texto,extensoes=exts,
        )
        hit=isinstance(r,dict)
        amplified.append(hit)
        print(f"{rotulo:<42} rota={rota!r} fields={fields} resultado={r}")
    print(f"turnos indevidamente autorizados que alcançam roteador . {sum(1 for x in amplified if x)}/{len(amplified)}")

    title("RESUMO")
    checks={
        "controles REV4.1 preservados":all(c_ok),
        "global quote helper fail-closed":all(x[3] for x in observations),
        "global quote autoridade fail-closed":all(authority),
    }
    for k,v in checks.items(): print(f"{k:<54} {'PASS' if v else 'FAIL'}")

    if reds:
        print("\n🔴 EXIT 2 — GLOBAL QUOTE BALANCE FALSIFICOU O B REV4.1")
        print("FIRST RED:",reds[0])
        print("Conclusão: par local apertado não basta; a região de quote que sustenta o filename precisa estar globalmente coerente, sem órfã/crossing residual.")
        return 2
    if not all(checks.values()):
        print("\n🔴 EXIT 2 — INVARIANTE FINAL GLOBAL-QUOTE FALHOU"); return 2

    print("\n🟢 EXIT 0 — TESTE 4.34 GREEN")
    print("REV4.1 já satisfaz o balanço global declarado.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
