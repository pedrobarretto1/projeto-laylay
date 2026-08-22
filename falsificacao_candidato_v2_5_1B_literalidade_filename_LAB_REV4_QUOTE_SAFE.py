#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANDIDATO LAB V2.5.1-B REV4 — FILENAME QUOTE-SAFE.

NÃO ALTERA PRODUÇÃO. EFEITO FÍSICO ZERO.

Root provado pelo teste 4.33
============================
O B REV3 aceitava uma quote opcional antes de `nao.<ext>` sem provar o par de
fechamento. Isso permitia autoridade em:

    cria arquivo chamado "nao.txt
    cria arquivo chamado nao.txt"
    cria arquivo chamado ”nao.txt“
    cria arquivo chamado “nao.txt"

O FIRST RED ocorre em `marcador_atom_b()`, antes do roteador. O roteador só
amplifica a autoridade indevida.

Contrato REV4
=============
- sem quote: permitido no slot de filename já provado;
- ASCII dupla: "nao.txt" somente se o par for apertado e balanceado;
- ASCII simples: 'nao.txt' idem;
- smart dupla: “nao.txt” somente nesta orientação;
- quote órfã, invertida, cruzada ou que atravesse texto depois do átomo:
  fail-closed;
- quote balanceada não esconde negação posterior;
- smart quote balanceada é desembrulhada SOMENTE no campo filename RAW já
  autorizado, nunca no texto inteiro e nunca para criar intent/autoridade.

O B REV3 exato continua sendo baseline para todos os outros contratos.

EXIT 0 = REV4 GREEN no LAB; ainda exige segunda revisão integral.
EXIT 1 = lock/wiring/premissa/harness inválido.
EXIT 2 = REV4 falsificado; FIRST RED manda.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HEAD="5cd3582562291a947464c3bcdca3bc7b83e036d8"
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

QUOTE_OPEN_TO_CLOSE={'"':'"', "'":"'", '“':'”'}
QUOTE_CHARS=frozenset({'"',"'",'“','”'})


def git(repo,*args,check=True):
    q=subprocess.run(["git",*args],cwd=str(repo),text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
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
    raise RuntimeError("execute este LAB dentro do repositório Laylay")


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def title(s): print("\n# "+s+"\n"+"="*98)

def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m

def _intent(r): return str((r or {}).get("intent") or "").upper().strip() if isinstance(r,dict) else ""
def _params(r): return dict((r or {}).get("params") or {}) if isinstance(r,dict) and isinstance((r or {}).get("params"),dict) else {}


def _char_nao_espaco_antes(texto,pos):
    i=int(pos)-1
    while i>=0 and texto[i].isspace(): i-=1
    return (texto[i],i) if i>=0 else ("",-1)


def _char_nao_espaco_depois(texto,pos):
    i=int(pos)
    while i<len(texto) and texto[i].isspace(): i+=1
    return (texto[i],i) if i<len(texto) else ("",len(texto))


def marcador_atom_rev4(raw,start,end,*,regex):
    """Protege `nao.<ext>` apenas em slot file + quote local provadamente válida."""
    texto=str(raw or "")
    trecho=texto[start:end].casefold().replace("ã","a")
    if trecho not in {"nao","não"}: return False,""
    atom=regex.match(texto,start)
    if not atom: return False,""

    prefixo=texto[:start]
    slot=re.search(
        r"\b(?:arquivo|documento)(?:\s+de\s+(?:texto|txt))?\b"
        r"(?:\s+(?:chamado|chamada|de\s+nome|com\s+nome))?"
        r"\s*(?P<quote>[\"'“”]?)\s*$",
        prefixo,
        flags=re.IGNORECASE,
    )
    if not slot: return False,""

    opener=str(slot.group("quote") or "")
    after,_idx=_char_nao_espaco_depois(texto,atom.end())

    if opener:
        expected=QUOTE_OPEN_TO_CLOSE.get(opener)
        # `”` nunca é opener; cruzada/invertida/orfã também falham aqui.
        if not expected or after!=expected:
            return False,""
    else:
        # Sem opener, uma quote imediatamente após o átomo é closing órfão.
        if after in QUOTE_CHARS:
            return False,""

    return True,str((atom.groupdict().get("atom") if hasattr(atom,"groupdict") else "") or atom.group(0) or "")


def desembrulhar_filename_raw(valor):
    """Remove SOMENTE um par externo provado; malformed quote retorna vazio."""
    v=str(valor or "").strip()
    if not v: return ""
    first=v[0] if v else ""; last=v[-1] if v else ""
    if first in QUOTE_CHARS or last in QUOTE_CHARS:
        expected=QUOTE_OPEN_TO_CLOSE.get(first)
        if not expected or last!=expected or len(v)<3:
            return ""
        return v[1:-1].strip()
    return v


def construir_turno_rev4(texto,*,base,rev3,extensoes,resolver_revisao_real,classificar_real,p0_real,normalizar_texto,texto_tem_comando_explicito):
    old_re=base.FILE_ATOM_RE; old_marker=base._marcador_em_atomo_arquivo
    regex=rev3.regex_atomo_producao(extensoes)
    base.FILE_ATOM_RE=regex
    base._marcador_em_atomo_arquivo=lambda raw,start,end: marcador_atom_rev4(raw,start,end,regex=regex)
    try:
        turno,rev,efetivo=base.construir_turno_candidato(
            texto,resolver_revisao_real=resolver_revisao_real,
            classificar_real=classificar_real,p0_real=p0_real,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
        return dict(turno or {}),rev,str(efetivo or "")
    finally:
        base.FILE_ATOM_RE=old_re
        base._marcador_em_atomo_arquivo=old_marker


def reconciliar_rev4(resultado_op,resultado_raw,*,texto_op,texto_raw,normalizar,extensoes,rev3):
    """REV3 + desembrulho tipado de quote somente nos campos filename RAW."""
    if not isinstance(resultado_raw,dict):
        return rev3.reconciliar_literalidade_filename(
            resultado_op,resultado_raw,texto_op=texto_op,texto_raw=texto_raw,
            normalizar=normalizar,extensoes=extensoes,
        )
    iop=_intent(resultado_op); iraw=_intent(resultado_raw)
    if not iop or iop!=iraw:
        return copy.deepcopy(resultado_op),[]
    raw2=copy.deepcopy(resultado_raw)
    p2=_params(raw2)
    for campo in rev3.CAMPOS_LITERALIDADE.get(iop,()):
        if campo not in p2: continue
        canon=desembrulhar_filename_raw(p2.get(campo))
        if not canon:
            # malformed quote no campo RAW não pode ser fonte de literalidade.
            continue
        p2[campo]=canon
    raw2["params"]=p2
    return rev3.reconciliar_literalidade_filename(
        resultado_op,raw2,texto_op=texto_op,texto_raw=texto_raw,
        normalizar=normalizar,extensoes=extensoes,
    )


def resolver_rev4(turno,texto_raw,*,base,rev3,detectar,normalizar_texto,extensoes):
    if base.turno_tem_veto_execucao(turno) or not base.autoriza_execucao_efetiva(turno):
        return None,"sem_autoridade",[]
    op=str(turno.get("texto_operacional") or "").strip()
    rop=rev3.detectar_arquivo_real(op,detectar=detectar,normalizar_texto=normalizar_texto)
    if not isinstance(rop,dict): return None,"op_sem_intent_arquivo",[]
    rraw=rev3.detectar_arquivo_real(texto_raw,detectar=detectar,normalizar_texto=normalizar_texto)
    if not isinstance(rraw,dict): return copy.deepcopy(rop),"arquivo_op",[]
    out,fields=reconciliar_rev4(
        rop,rraw,texto_op=op,texto_raw=texto_raw,
        normalizar=normalizar_texto,extensoes=extensoes,rev3=rev3,
    )
    return out,("arquivo_literalidade_quote_safe" if fields else "arquivo_op"),fields


def executar_fluxo_rev4(turno,texto_raw,*,base,rev3,detectar,normalizar_texto,extensoes,executar_fluxo):
    calls=[]
    if base.turno_tem_veto_execucao(turno) or not base.autoriza_execucao_efetiva(turno):
        return False,calls
    op=str(turno.get("texto_operacional") or "").strip()
    def resolver(segmento,origem,ctx):
        rop=rev3.detectar_arquivo_real(segmento,detectar=detectar,normalizar_texto=normalizar_texto)
        if not isinstance(rop,dict): return None,""
        rraw=rev3.detectar_arquivo_real(texto_raw,detectar=detectar,normalizar_texto=normalizar_texto)
        if not isinstance(rraw,dict): return rop,"arquivo-op"
        out,fields=reconciliar_rev4(
            rop,rraw,texto_op=segmento,texto_raw=texto_raw,
            normalizar=normalizar_texto,extensoes=extensoes,rev3=rev3,
        )
        return out,("arquivo-quote-safe" if fields else "arquivo-op")
    ctx={
        "executar_intencao":lambda r,t: calls.append({"intent":_intent(r),"params":_params(r),"texto":t}) or True,
        "registrar_resultado_execucao":lambda *a,**k:None,
        "registrar_autoaprimoramento":lambda *a,**k:None,
    }
    ok=bool(executar_fluxo(op,"lab-v2.5.1-b-rev4",ctx,texto_original=texto_raw,resolver_cb=resolver))
    return ok,calls


def main():
    print("CANDIDATO LAB V2.5.1-B REV4 — FILENAME QUOTE-SAFE")
    print("="*98)
    print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=repo_root()
    except Exception as e: print("\n🟠 EXIT 1 —",e); return 1

    title("GUARDS / LOCKS / BASELINES EXATOS")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print(f"HEAD ........................................ {'PASS' if h==HEAD else 'FAIL'} {h}")
    if h!=HEAD: bad.append("HEAD mudou")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e; print(f"{f:<72} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f"blob mudou: {f}")
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print("produção causal limpa .................................", "PASS" if clean else "FAIL")
    if not clean: print(dirty); bad.append("produção suja")
    rp=repo/REV3_FILE; bp=repo/BASE_FILE
    rh=sha(rp) if rp.is_file() else ""; bh=sha(bp) if bp.is_file() else ""
    print("B REV3 exato ..........................................", "PASS" if rh==REV3_SHA else "FAIL",rh or "ausente")
    print("V2.5 base exato .......................................", "PASS" if bh==BASE_SHA else "FAIL",bh or "ausente")
    if rh!=REV3_SHA: bad.append("REV3 ausente/divergente")
    if bh!=BASE_SHA: bad.append("V2.5 ausente/divergente")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))

    try:
        rev3=imod("v251b_rev3_quote_baseline",rp); base=imod("v25_quote_baseline",bp)
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
        from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
        from mente_laylay.autonomia.coordenador_intencao import executar_fluxo_intencao
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1

    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    regex=rev3.regex_atomo_producao(exts)
    def build_rev4(t):
        return construir_turno_rev4(
            t,base=base,rev3=rev3,extensoes=exts,
            resolver_revisao_real=resolver_revisao_intra_turno,
            classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,
            normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito,
        )[0]
    def build_rev3(t):
        return rev3.construir_turno_b(
            t,base=base,extensoes=exts,
            resolver_revisao_real=resolver_revisao_intra_turno,
            classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,
            normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito,
        )[0]

    reds=[]
    malformed=[
        ('cria arquivo chamado "nao.txt',"abertura dupla sem fechamento"),
        ("cria arquivo chamado 'nao.txt","abertura simples sem fechamento"),
        ('cria arquivo chamado “nao.txt',"abertura smart sem fechamento"),
        ('cria arquivo chamado nao.txt"',"fechamento duplo órfão"),
        ('cria arquivo chamado nao.txt”',"fechamento smart órfão"),
        ('cria arquivo chamado ”nao.txt“',"smart invertida"),
        ('cria arquivo chamado “nao.txt"',"quotes cruzadas smart/ASCII"),
        ('cria arquivo chamado "nao.txt fecha o opera',"quote atravessa ato sem fechar"),
        ('cria arquivo chamado "nao.txt fecha o opera"',"quote balanceada mas não apertada ao átomo"),
    ]

    title("FASE 0 — REPRODUÇÃO DO FIRST RED 4.33 NO REV3")
    rev3_vuln=[]
    for texto,rotulo in malformed[:8]:
        m=re.search(r"(?:nao|não)",texto,re.IGNORECASE)
        marker=rev3.marcador_atom_b(texto,m.start(),m.end(),regex=regex) if m else (False,"")
        t=build_rev3(texto); vuln=bool(marker[0] and base.autoriza_execucao_efetiva(t) and not base.turno_tem_veto_execucao(t))
        rev3_vuln.append(vuln)
        print(f"{rotulo:<46} marker={marker} auth={base.autoriza_execucao_efetiva(t)} {'RED' if vuln else '—'}")
    precond=any(rev3_vuln)
    print("REV3 reproduz ao menos um quote RED ....................", "PASS" if precond else "FAIL")
    if not precond:
        print("\n🟠 EXIT 1 — premissa do 4.33 não foi reproduzida"); return 1

    title("FASE 1 — HELPER REV4: QUOTE APERTADA / BALANCEADA / ORIENTADA")
    positives=[
        ("cria arquivo nao.txt","sem quote"),
        ('cria arquivo chamado "nao.txt"',"ASCII dupla"),
        ("cria arquivo chamado 'nao.txt'","ASCII simples"),
        ('cria arquivo chamado “nao.txt”',"smart dupla"),
        ('cria arquivo chamado " nao.txt "',"ASCII dupla com espaço interno"),
    ]
    helper_ok=True
    for texto,rotulo in positives:
        m=re.search(r"(?:nao|não)",texto,re.IGNORECASE); got=marcador_atom_rev4(texto,m.start(),m.end(),regex=regex)
        ok=bool(got[0]); helper_ok=helper_ok and ok; print(f"{rotulo:<46} {got} {'PASS' if ok else 'FAIL'}")
    for texto,rotulo in malformed:
        m=re.search(r"(?:nao|não)",texto,re.IGNORECASE); got=marcador_atom_rev4(texto,m.start(),m.end(),regex=regex)
        ok=not got[0]; helper_ok=helper_ok and ok; print(f"{rotulo:<46} {got} {'PASS' if ok else 'FAIL'}")
    if not helper_ok: reds.append("quote helper: estrutura malformada ainda protegida ou positiva morreu")

    title("FASE 2 — AUTORIDADE REV4 / FAIL-CLOSED")
    auth_pos=[
        "cria arquivo nao.txt",
        'cria arquivo chamado "nao.txt"',
        "cria arquivo chamado 'nao.txt'",
        'cria arquivo chamado “nao.txt”',
        'cria arquivo chamado "não.md"',
        'cria arquivo chamado “nao.markdown”',
    ]
    auth_ok=True
    for texto in auth_pos:
        t=build_rev4(texto); ok=bool(not base.turno_tem_veto_execucao(t) and base.autoriza_execucao_efetiva(t)); auth_ok=auth_ok and ok
        print(f"{'PASS' if ok else 'FAIL'} positivo {texto!r} -> veto={base.turno_tem_veto_execucao(t)} auth={base.autoriza_execucao_efetiva(t)}")
    for texto,rotulo in malformed:
        t=build_rev4(texto); ok=bool(base.turno_tem_veto_execucao(t) and not base.autoriza_execucao_efetiva(t)); auth_ok=auth_ok and ok
        print(f"{'PASS' if ok else 'FAIL'} killer {rotulo:<38} veto={base.turno_tem_veto_execucao(t)} auth={base.autoriza_execucao_efetiva(t)}")
    posterior=[
        'cria arquivo chamado "nao.txt" contendo nao aumenta o volume',
        'cria arquivo chamado “nao.txt” e nao fecha o opera',
        "cria arquivo chamado 'nao.txt' contendo nao diminui o volume",
    ]
    for texto in posterior:
        t=build_rev4(texto); ok=bool(base.turno_tem_veto_execucao(t) and not base.autoriza_execucao_efetiva(t)); auth_ok=auth_ok and ok
        print(f"{'PASS' if ok else 'FAIL'} negação posterior {texto!r}")
    if not auth_ok: reds.append("autoridade: quote malformed ganhou autoridade ou posterior perdeu soberania")

    title("FASE 3 — SMART QUOTE E2E: RAW NÃO LEVA ASPAS AO FILENAME")
    payload_cases=[
        ("cria arquivo nao.txt","nao.txt"),
        ('cria arquivo chamado "nao.txt"',"nao.txt"),
        ("cria arquivo chamado 'nao.txt'","nao.txt"),
        ('cria arquivo chamado “nao.txt”',"nao.txt"),
        ('cria arquivo chamado “não.md”',"não.md"),
        ('cria arquivo chamado “nao.markdown”',"nao.markdown"),
    ]
    payload_ok=True
    for texto,alvo in payload_cases:
        t=build_rev4(texto)
        r,rota,fields=resolver_rev4(t,texto,base=base,rev3=rev3,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts)
        got=str(_params(r).get("alvo") or "")
        ok=bool(_intent(r)=="CREATE_FILE" and got==alvo and '“' not in got and '”' not in got and '"' not in got and "'" not in got)
        payload_ok=payload_ok and ok
        print(f"{'PASS' if ok else 'FAIL'} {texto!r} -> rota={rota!r} fields={fields} alvo={got!r}")
    if not payload_ok: reds.append("payload: quote balanceada/smart não canonicalizou para basename exato")

    title("FASE 4 — DEFESA EM PROFUNDIDADE DO MERGE")
    merge_ok=True
    adversariais=[
        ({"intent":"CREATE_FILE","params":{"alvo":"nao txt"}}, {"intent":"CREATE_FILE","params":{"alvo":"“nao.txt"}}, "cria arquivo nao txt", 'cria arquivo “nao.txt', "nao txt"),
        ({"intent":"CREATE_FILE","params":{"alvo":"nao txt"}}, {"intent":"CREATE_FILE","params":{"alvo":"nao.txt”"}}, "cria arquivo nao txt", 'cria arquivo nao.txt”', "nao txt"),
        ({"intent":"CREATE_FILE","params":{"alvo":"nao txt"}}, {"intent":"DELETE_ITEM","params":{"alvo":"nao.txt"}}, "cria arquivo nao txt", 'apaga arquivo nao.txt', "nao txt"),
    ]
    for op,raw,top,traw,expected in adversariais:
        out,fields=reconciliar_rev4(op,raw,texto_op=top,texto_raw=traw,normalizar=normalizar_texto,extensoes=exts,rev3=rev3)
        got=str(_params(out).get("alvo") or ""); ok=bool(got==expected and fields==[]); merge_ok=merge_ok and ok
        print(f"{'PASS' if ok else 'FAIL'} malformed/mismatch -> alvo={got!r} fields={fields}")
    # Conteúdo continua OP; RAW só doa alvo.
    op={"intent":"CREATE_FILE","params":{"alvo":"nao txt","conteudo":"texto com ponto"}}
    raw={"intent":"CREATE_FILE","params":{"alvo":"“nao.txt”","conteudo":"texto.com.ponto"}}
    out,fields=reconciliar_rev4(op,raw,texto_op="cria arquivo nao txt contendo texto com ponto",texto_raw="cria arquivo “nao.txt” contendo texto.com.ponto",normalizar=normalizar_texto,extensoes=exts,rev3=rev3)
    ok=bool(_params(out).get("alvo")=="nao.txt" and _params(out).get("conteudo")=="texto com ponto" and fields==["alvo"]); merge_ok=merge_ok and ok
    print(f"{'PASS' if ok else 'FAIL'} conteúdo RAW não copiado -> {_params(out)} fields={fields}")
    if not merge_ok: reds.append("merge: malformed quote/intent/conteúdo furou allowlist")

    title("FASE 5 — executar_fluxo_intencao REAL / EXECUTOR RECORDER")
    flow_cases=[
        ('cria arquivo chamado “nao.txt”',"nao.txt",True),
        ('cria arquivo chamado "nao.txt"',"nao.txt",True),
        ('cria arquivo nao.txt',"nao.txt",True),
        ('cria arquivo chamado “nao.markdown”',"nao.markdown",True),
        ('cria arquivo chamado “nao.txt',"",False),
        ('cria arquivo chamado nao.txt”',"",False),
        ('cria arquivo chamado “nao.txt"',"",False),
        ('cria arquivo chamado "nao.txt fecha o opera"',"",False),
        ('cria arquivo chamado “nao.txt” contendo nao aumenta o volume',"",False),
    ]
    flow_ok=True
    for texto,alvo,deve in flow_cases:
        t=build_rev4(texto)
        ok,calls=executar_fluxo_rev4(t,texto,base=base,rev3=rev3,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts,executar_fluxo=executar_fluxo_intencao)
        if deve:
            this=bool(ok and len(calls)==1 and calls[0]["intent"]=="CREATE_FILE" and calls[0]["params"].get("alvo")==alvo and calls[0]["texto"]==texto)
        else:
            this=bool(not ok and calls==[] and base.turno_tem_veto_execucao(t))
        flow_ok=flow_ok and this
        print(f"{'PASS' if this else 'FAIL'} {texto!r} -> ok={ok} calls={calls}")
    if not flow_ok: reds.append("integração: quote-safe não sobreviveu ao fluxo real ou killer chegou ao executor")

    title("FASE 6 — RESTAURAÇÃO / INVARIANTES")
    restored=bool(base._marcador_em_atomo_arquivo.__name__=="_marcador_em_atomo_arquivo")
    print("baseline marker restaurado .............................", "PASS" if restored else "FAIL")
    if not restored:
        print("\n🟠 EXIT 1 — monkeypatch de marker vazou"); return 1
    inv={
        "4.33 reproduzido no REV3":precond,
        "helper quote-safe":helper_ok,
        "autoridade fail-closed":auth_ok,
        "smart quote payload exato":payload_ok,
        "merge defesa em profundidade":merge_ok,
        "fluxo real zero efeito":flow_ok,
        "baseline restaurado":restored,
    }
    for k,v in inv.items(): print(f"{k:<52} {'PASS' if v else 'FAIL'}")
    if reds:
        print("\n🔴 EXIT 2 — CANDIDATO V2.5.1-B REV4 FALSIFICADO")
        print("FIRST RED:",reds[0]); [print("❌",x) for x in reds]; return 2
    if not all(inv.values()):
        print("\n🔴 EXIT 2 — INVARIANTE FINAL FALHOU"); return 2
    print("\n🟢 EXIT 0 — CANDIDATO LAB V2.5.1-B REV4 QUOTE-SAFE GREEN")
    print("Quote só protege filename com estrutura apertada/balanceada; smart quotes não vazam para o basename.")
    print("Produção continua intacta; integração A+B continua bloqueada até segunda revisão do B REV4.")
    return 0

if __name__=="__main__": raise SystemExit(main())
