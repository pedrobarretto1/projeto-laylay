#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FALSIFICAÇÃO V2.5.1 — QUOTE BALANCE EM FILENAME / TESTE 4.33.

NÃO ALTERA PRODUÇÃO. EFEITO FÍSICO ZERO.

Hipótese:
O B REV3 protege `nao.<ext>` em slot literal de filename, mas aceita uma aspa
imediatamente antes do átomo sem provar que ela fecha depois dele.

Invariante:
- quotes balanceadas/orientadas podem reforçar evidência literal;
- quote aberta, órfã, cruzada ou invertida nunca pode transformar negação
  ambígua em filename autorizado;
- quote balanceada no filename nunca protege negação operacional posterior.

EXIT 0 = nenhum RED; 1 = harness/lock inválido; 2 = B REV3 falsificado.
"""
from __future__ import annotations
import hashlib, importlib.util, re, subprocess, sys
from pathlib import Path
from typing import Any

HEAD="5cd3582562291a947464c3bcdca3bc7b83e036d8"
B_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"
B_SHA="29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
BLOBS={
"mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
"mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
"mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
"mente_laylay/arquivos/roteador_arquivos.py":"36fc40861db60c0aabe324669272c28d1d89d2f5",
"mente_laylay/arquivos/nome_natural.py":"9f6f7d10fa7ac0baae2c11204b984a1d451a5c5e",
}

def git(repo,*args,check=True):
    q=subprocess.run(["git",*args],cwd=str(repo),text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and q.returncode: raise RuntimeError(q.stderr.strip() or q.stdout.strip())
    return q.stdout.strip()

def repo_root():
    seen=set()
    for start in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (start,*start.parents):
            if x in seen: continue
            seen.add(x)
            if (x/".git").exists() and (x/"laylay.py").exists(): return x
    raise RuntimeError("execute dentro do repositório Laylay")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m

def title(s): print("\n# "+s+"\n"+"="*96)
def marker_span(texto):
    m=re.search(r"\b(?:nao|não)\b",str(texto or ""),re.I)
    return (m.start(),m.end()) if m else (-1,-1)
def auth(base,t): return bool(base.autoriza_execucao_efetiva(t))
def veto(base,t): return bool(base.turno_tem_veto_execucao(t))


def main():
    print("FALSIFICAÇÃO V2.5.1 — QUOTE BALANCE EM FILENAME / TESTE 4.33")
    print("="*96)
    print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=repo_root()
    except Exception as e: print(f"\n🟠 EXIT 1 — {e}"); return 1

    title("GUARDS / LOCKS / ARTEFATOS EXATOS")
    bad=[]; h=git(repo,"rev-parse","HEAD")
    print(f"HEAD ........................................ {'PASS' if h==HEAD else 'FAIL'} {h}")
    if h!=HEAD: bad.append("HEAD mudou")
    for f,e in BLOBS.items():
        got=git(repo,"rev-parse",f"HEAD:{f}"); ok=got==e
        print(f"{f:<72} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f"blob mudou: {f}")
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip()
    print(f"produção causal limpa .................................. {'PASS' if clean else 'FAIL'}")
    if not clean: print(dirty); bad.append("produção causal suja")
    for name,expected in ((B_FILE,B_SHA),(BASE_FILE,BASE_SHA)):
        q=repo/name; got=sha(q) if q.is_file() else ""; ok=got==expected
        print(f"{name:<72} {'PASS' if ok else 'FAIL'} {got or 'ausente'}")
        if not ok: bad.append(f"artefato ausente/divergente: {name}")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1

    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        B=imod("v251b_quote433",repo/B_FILE); base=imod("v25_quote433",repo/BASE_FILE)
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
        from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1

    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    regex=B.regex_atomo_producao(exts)
    def build(texto):
        return B.construir_turno_b(texto,base=base,extensoes=exts,resolver_revisao_real=resolver_revisao_intra_turno,classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito)[0]

    title("FASE 0 — PRECONDIÇÃO: HELPER B REAL ACEITA QUOTE NÃO BALANCEADA")
    probes=[
        'cria arquivo chamado "nao.txt',
        "cria arquivo chamado 'nao.txt",
        'cria arquivo chamado “nao.txt',
        'cria arquivo chamado nao.txt"',
        'cria arquivo chamado nao.txt”',
        'cria arquivo chamado ”nao.txt“',
        'cria arquivo chamado “nao.txt"',
    ]
    marker_results=[]
    for texto in probes:
        st,en=marker_span(texto); r=B.marcador_atom_b(texto,st,en,regex=regex) if st>=0 else (False,"")
        marker_results.append((texto,r)); print(f"{texto!r:<54} marker={r}")
    helper_expoe=any(bool(r[0]) for _,r in marker_results)
    print(f"helper aceita ao menos uma quote não balanceada ....... {'RED observado' if helper_expoe else 'não observado'}")
    if not helper_expoe:
        print("\n🟠 EXIT 1 — precondição causal não reproduzida"); return 1

    title("FASE 1 — CONTROLES POSITIVOS: QUOTES PROVADAS")
    positivos=[
        ('cria arquivo nao.txt',"sem quote"),
        ('cria arquivo chamado "nao.txt"',"ASCII dupla"),
        ("cria arquivo chamado 'nao.txt'","ASCII simples"),
        ('cria arquivo chamado “nao.txt”',"smart dupla"),
        ('cria arquivo chamado "não.md"',"acentuado"),
        ('cria arquivo chamado "nao.markdown"',"markdown"),
    ]
    pos_ok=[]
    for texto,rotulo in positivos:
        t=build(texto); ok=(not veto(base,t) and auth(base,t)); pos_ok.append(ok)
        print(f"{rotulo:<24} veto={veto(base,t)!s:<5} auth={auth(base,t)!s:<5} {'PASS' if ok else 'FAIL'} | {texto}")
    if not all(pos_ok): print("\n🟠 EXIT 1 — controle positivo divergiu"); return 1


    title("FASE 2 — KILLERS: QUOTE NÃO BALANCEADA DEVE FAIL-CLOSED")
    killers=[
        ('cria arquivo chamado "nao.txt',"abertura dupla sem fechamento"),
        ("cria arquivo chamado 'nao.txt","abertura simples sem fechamento"),
        ('cria arquivo chamado “nao.txt',"abertura smart sem fechamento"),
        ('cria arquivo chamado nao.txt"',"fechamento duplo órfão"),
        ('cria arquivo chamado nao.txt”',"fechamento smart órfão"),
        ('cria arquivo chamado ”nao.txt“',"smart invertida"),
        ('cria arquivo chamado “nao.txt"',"quotes cruzadas smart/ASCII"),
        ('cria arquivo chamado "nao.txt e fecha o opera',"quote aberta atravessa ato real"),
    ]
    reds=[]; observations=[]
    for texto,rotulo in killers:
        t=build(texto)
        ok=bool(veto(base,t) and not auth(base,t) and not str(t.get("texto_operacional") or ""))
        observations.append((texto,rotulo,t,ok))
        print(f"{rotulo:<40} veto={veto(base,t)!s:<5} auth={auth(base,t)!s:<5} op={str(t.get('texto_operacional') or '')!r} {'PASS' if ok else 'RED'}")
        if not ok and not reds: reds.append(f"quote-balance: {rotulo} ganhou autoridade")

    title("FASE 3 — QUOTE BALANCEADA NÃO ESCONDE NEGAÇÃO POSTERIOR")
    boundaries=[
        'cria arquivo chamado "nao.txt" contendo nao aumenta o volume',
        'cria arquivo chamado "nao.txt" e nao fecha o opera',
        'cria arquivo chamado “nao.md” e nao abre a calculadora',
        "cria arquivo chamado 'nao.txt' contendo nao diminui o volume",
    ]
    boundary_ok=[]
    for texto in boundaries:
        t=build(texto); ok=bool(veto(base,t) and not auth(base,t) and not str(t.get("texto_operacional") or "")); boundary_ok.append(ok)
        print(f"{'PASS' if ok else 'RED '} {texto!r} -> veto={veto(base,t)} auth={auth(base,t)} op={str(t.get('texto_operacional') or '')!r}")
        if not ok and not reds: reds.append("quote balanceada protegeu negação operacional posterior")

    title("FASE 4 — AMPLIFICAÇÃO DOWNSTREAM DO FIRST RED / SEM EXECUÇÃO")
    vulneraveis=[x for x in observations if (not x[3]) and auth(base,x[2])]
    amplified=[]
    for texto,rotulo,t,_ in vulneraveis[:4]:
        resultado,rota,campos=B.resolver_b(t,texto,base=base,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts)
        hit=isinstance(resultado,dict); amplified.append(hit)
        print(f"{rotulo:<40} rota={rota!r} campos={campos} resultado={resultado}")
    print(f"vulneráveis autorizados que alcançam roteador .......... {sum(1 for x in amplified if x)}/{len(amplified)}")

    title("RESUMO")
    checks={
        "controles balanceados":all(pos_ok),
        "quotes não balanceadas fail-closed":all(x[3] for x in observations),
        "negação posterior continua soberana":all(boundary_ok),
    }
    for k,v in checks.items(): print(f"{k:<50} {'PASS' if v else 'FAIL'}")
    if reds:
        print("\n🔴 EXIT 2 — QUOTE BALANCE FALSIFICOU O B REV3")
        print("FIRST RED:",reds[0])
        print("Conclusão: filename só pode proteger `nao.<ext>` quando a estrutura de quote estiver provadamente balanceada/orientada.")
        return 2
    if not all(checks.values()):
        print("\n🔴 EXIT 2 — INVARIANTE FINAL DE QUOTE BALANCE FALHOU"); return 2
    print("\n🟢 EXIT 0 — TESTE 4.33 GREEN")
    print("B REV3 já satisfaz o quote-balance declarado.")
    return 0

if __name__=="__main__": raise SystemExit(main())
