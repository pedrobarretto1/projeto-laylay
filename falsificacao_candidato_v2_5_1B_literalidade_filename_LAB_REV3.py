#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANDIDATO LAB V2.5.1-B REV3 — LITERALIDADE DE FILENAME / `nao.txt`.

NÃO ALTERA PRODUÇÃO.

Objetivo
========
Fechar o eixo B separado do eixo A:
- autoridade reconhece átomos literais `nao.<ext>` usando a lista CANÔNICA de
  extensões da produção, sem lista privada divergente;
- `texto_operacional` continua soberano para estrutura/autoridade;
- RAW serve SOMENTE como evidência literal para campos filename/path de uma
  intent de arquivo já resolvida pelo OP;
- RAW nunca substitui o contrato inteiro, nunca cria intent, nunca remove veto;
- `nao txt` sem ponto permanece ambíguo/fail-closed;
- `.exe` não ganha exceção;
- conteúdo/segundo ato com negação real continua produzindo veto.

Princípio de reconciliação
==========================
Só se permite copiar um campo do resultado RAW para o resultado OP quando:
1. o turno já está AUTORIZADO e não está VETADO;
2. OP e RAW produzem o MESMO intent canônico de arquivo;
3. o campo é explicitamente permitido para esse intent;
4. o valor RAW contém extensão textual suportada pela produção;
5. esse basename pontuado aparece literalmente no RAW original;
6. normalizar(valor_raw) == normalizar(valor_op);
7. somente esse campo é substituído; conteúdo, destino, pasta, modo, tipo e
   qualquer outro parâmetro permanecem do resultado OP.

Escopo
======
- CREATE_FILE: alvo
- CREATE_FOLDER: arquivo_nome
- FILE_SEARCH: query/alvo
- DELETE_ITEM: alvo
- FILE_TRANSACTION: origem

FILE_OPEN_RESULT/FILE_READ por referência concreta não são reescritos.

EXIT
====
0 = B GREEN no LAB; ainda exige segunda revisão integral.
1 = lock/wiring/premissa/harness inválido.
2 = candidato B falsificado; FIRST RED manda.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

HEAD="a4741bc57bc55a50ef2861dbaef09ab36397ff63"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
BLOBS={
"laylay.py":"7f89a8e4944f7df83de0835fbd3142f6cd127c60",
"mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
"mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
"mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
"mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
"mente_laylay/autonomia/coordenador_intencao.py":"de8a893cd60ab44ad9bc3437d01db15ba54fb367",
"mente_laylay/autonomia/roteador_deterministico.py":"a011d0da655c2f00c1d9d75e723ae559107f31e5",
"mente_laylay/autonomia/orquestrador_deterministico.py":"5e1134128c2abdca9e22ec566796bb86159fd007",
"mente_laylay/arquivos/roteador_arquivos.py":"36fc40861db60c0aabe324669272c28d1d89d2f5",
"mente_laylay/arquivos/nome_natural.py":"9f6f7d10fa7ac0baae2c11204b984a1d451a5c5e",
}

CAMPOS_LITERALIDADE={
    "CREATE_FILE": ("alvo",),
    "CREATE_FOLDER": ("arquivo_nome",),
    "FILE_SEARCH": ("query","alvo"),
    "DELETE_ITEM": ("alvo",),
    "FILE_TRANSACTION": ("origem",),
}

def git(repo,*args,check=True):
    q=subprocess.run(["git",*args],cwd=str(repo),text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and q.returncode: raise RuntimeError(q.stderr.strip() or q.stdout.strip())
    return q.stdout.strip()

def repo_root():
    seen=set()
    for s in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (s,*s.parents):
            if x in seen: continue
            seen.add(x)
            if (x/".git").exists() and (x/"laylay.py").exists(): return x
    raise RuntimeError("execute este LAB dentro do repositório Laylay")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def title(s): print("\n# "+s+"\n"+"="*96)
def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m

def _intent(r): return str((r or {}).get("intent") or "").upper().strip() if isinstance(r,dict) else ""
def _params(r): return dict((r or {}).get("params") or {}) if isinstance(r,dict) and isinstance((r or {}).get("params"),dict) else {}

def regex_atomo_producao(extensoes):
    nomes=sorted({str(e).strip().casefold().removeprefix(".") for e in extensoes if str(e).strip()},key=len,reverse=True)
    return re.compile(rf"\b(?:nao|não)\.(?:{'|'.join(re.escape(x) for x in nomes)})\b",re.IGNORECASE)

def extensao_literal_suportada(valor,raw,extensoes):
    v=str(valor or "").strip().strip('"\'')
    if not v: return False
    base=os.path.basename(v.replace("\\","/"))
    ext=os.path.splitext(base)[1].casefold()
    if ext not in set(extensoes): return False
    # A evidência literal precisa existir no RAW; não basta o parser tê-la inferido.
    return bool(re.search(rf"(?<![\w.]){re.escape(base)}(?![\w.])",str(raw or ""),re.IGNORECASE))

def reconciliar_literalidade_filename(resultado_op,resultado_raw,*,texto_op,texto_raw,normalizar,extensoes):
    """Copia somente campos filename comprovadamente literais do RAW."""
    if not isinstance(resultado_op,dict) or not isinstance(resultado_raw,dict): return resultado_op,[]
    iop=_intent(resultado_op); iraw=_intent(resultado_raw)
    if not iop or iop!=iraw or iop not in CAMPOS_LITERALIDADE: return copy.deepcopy(resultado_op),[]
    # RAW só pode doar literalidade se for comprovadamente a mesma fala que
    # originou o OP. Diferença lexical/estrutural inteira aborta o merge.
    try:
        if str(normalizar(texto_op) or "").strip() != str(normalizar(texto_raw) or "").strip():
            return copy.deepcopy(resultado_op),[]
    except Exception:
        return copy.deepcopy(resultado_op),[]
    pop=_params(resultado_op); praw=_params(resultado_raw); out=copy.deepcopy(resultado_op); pout=dict(pop); alterados=[]
    for campo in CAMPOS_LITERALIDADE[iop]:
        vo=str(pop.get(campo) or "").strip(); vr=str(praw.get(campo) or "").strip()
        if not vo or not vr or vo==vr: continue
        if not extensao_literal_suportada(vr,texto_raw,extensoes): continue
        try: nop=str(normalizar(vo) or "").strip(); nraw=str(normalizar(vr) or "").strip()
        except Exception: continue
        if not nop or nop!=nraw: continue
        pout[campo]=vr; alterados.append(campo)
    out["params"]=pout
    return out,alterados




def marcador_atom_b(raw,start,end,*,regex):
    texto=str(raw or "")
    trecho=texto[start:end].casefold().replace("ã","a")
    # O marcador protegido continua sendo SOMENTE nao/não literal.
    if trecho not in {"nao","não"}: return False,""
    m=regex.match(texto,start)
    if not m: return False,""
    prefixo=texto[:start]
    # Slot estreito derivado das molduras aceitas pelos parsers de arquivo.
    # Não protege conteúdo, alvo genérico nem qualquer `nao` sem filename.
    if not re.search(
        r"\b(?:arquivo|documento)(?:\s+de\s+(?:texto|txt))?\b"
        r"(?:\s+(?:chamado|chamada|de\s+nome|com\s+nome))?\s*[\"'“”]?\s*$",
        prefixo,
        flags=re.IGNORECASE,
    ):
        return False,""
    gd=m.groupdict() if hasattr(m,"groupdict") else {}
    return True,str(gd.get("atom") or m.group(0) or "")

def construir_turno_b(texto,*,base,extensoes,resolver_revisao_real,classificar_real,p0_real,normalizar_texto,texto_tem_comando_explicito):
    """V2.5 exato + única mudança de autoridade do B: regex deriva da produção."""
    old=base.FILE_ATOM_RE
    old_marker=base._marcador_em_atomo_arquivo
    regex=regex_atomo_producao(extensoes)
    base.FILE_ATOM_RE=regex
    base._marcador_em_atomo_arquivo=lambda raw,start,end: marcador_atom_b(raw,start,end,regex=regex)
    try:
        turno,rev,efetivo=base.construir_turno_candidato(
            texto,
            resolver_revisao_real=resolver_revisao_real,
            classificar_real=classificar_real,
            p0_real=p0_real,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
        return dict(turno or {}),dict(rev or {}) if isinstance(rev,dict) else rev,str(efetivo or "")
    finally:
        base.FILE_ATOM_RE=old
        base._marcador_em_atomo_arquivo=old_marker

def detectar_arquivo_real(texto,*,detectar,normalizar_texto,estado=None):
    return detectar(
        str(texto or ""),
        params_cb=lambda **kwargs: kwargs,
        estado_mental=dict(estado or {}),
        normalizar_texto=normalizar_texto,
    )

def resolver_b(turno,texto_raw,*,base,detectar,normalizar_texto,extensoes,estado=None):
    """Autoridade vem do turno; OP resolve intent; RAW só fornece literalidade."""
    if not isinstance(turno,dict): return None,"turno_invalido",[]
    if base.turno_tem_veto_execucao(turno) or not base.autoriza_execucao_efetiva(turno):
        return None,"sem_autoridade",[]
    op=str(turno.get("texto_operacional") or "").strip()
    if not op: return None,"sem_texto_operacional",[]
    rop=detectar_arquivo_real(op,detectar=detectar,normalizar_texto=normalizar_texto,estado=estado)
    if not isinstance(rop,dict): return None,"op_sem_intent_arquivo",[]
    rraw=detectar_arquivo_real(texto_raw,detectar=detectar,normalizar_texto=normalizar_texto,estado=estado)
    if not isinstance(rraw,dict): return copy.deepcopy(rop),"op_sem_raw_equivalente",[]
    corrigido,campos=reconciliar_literalidade_filename(
        rop,rraw,texto_op=op,texto_raw=texto_raw,normalizar=normalizar_texto,extensoes=extensoes,
    )
    return corrigido,"arquivo_literalidade" if campos else "arquivo_op",campos

def executar_fluxo_b(turno,texto_raw,*,base,executar_fluxo,detectar,normalizar_texto,extensoes,estado=None):
    """Usa executar_fluxo_intencao REAL, com executor final recorder in-memory."""
    chamadas=[]; registros=[]; auto=[]
    if base.turno_tem_veto_execucao(turno) or not base.autoriza_execucao_efetiva(turno):
        return False,chamadas,registros,auto
    op=str(turno.get("texto_operacional") or "").strip()
    def resolvedor(segmento,origem,ctx):
        # O executor real entrega o mesmo OP ao resolver. Não consultamos RAW
        # para criar intent; só depois da detecção OP bem-sucedida.
        rop=detectar_arquivo_real(segmento,detectar=detectar,normalizar_texto=normalizar_texto,estado=estado)
        if not isinstance(rop,dict): return None,""
        rraw=detectar_arquivo_real(texto_raw,detectar=detectar,normalizar_texto=normalizar_texto,estado=estado)
        if not isinstance(rraw,dict): return rop,"arquivo-op"
        corr,campos=reconciliar_literalidade_filename(
            rop,rraw,texto_op=segmento,texto_raw=texto_raw,normalizar=normalizar_texto,extensoes=extensoes,
        )
        return corr,"arquivo-literalidade" if campos else "arquivo-op"
    ctx={
        "executar_intencao":lambda r,t: chamadas.append({"intent":_intent(r),"params":_params(r),"texto":t}) or True,
        "registrar_resultado_execucao":lambda *a,**k: registros.append({"args":a,"kwargs":k}),
        "registrar_autoaprimoramento":lambda *a,**k: auto.append({"args":a,"kwargs":k}),
    }
    ok=bool(executar_fluxo(op,"lab-v2.5.1-b",ctx,texto_original=texto_raw,resolver_cb=resolvedor))
    return ok,chamadas,registros,auto

def campo(resultado,nome): return str(_params(resultado).get(nome) or "")

def main():
    print("CANDIDATO LAB V2.5.1-B REV3 — LITERALIDADE DE FILENAME / `nao.txt`")
    print("="*96)
    print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=repo_root()
    except Exception as e: print(f"\n🟠 EXIT 1 — {e}"); return 1

    title("GUARDS / LOCKS / BASELINE V2.5 EXATO")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print(f"HEAD ........................................ {'PASS' if h==HEAD else 'FAIL'} {h}")
    if h!=HEAD: bad.append("HEAD mudou")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e; print(f"{f:<72} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f"blob mudou: {f}")
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print(f"produção causal limpa .................................. {'PASS' if clean else 'FAIL'}")
    if not clean: print(dirty); bad.append("produção suja")
    bp=repo/BASE_FILE; bh=sha(bp) if bp.is_file() else ""; bok=bh==BASE_SHA; print(f"baseline V2.5 exato .................................... {'PASS' if bok else 'FAIL'} {bh or 'ausente'}")
    if not bok: bad.append("baseline ausente/divergente")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        base=imod("v25_exact_b",bp)
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS,limpar_nome_arquivo_natural
        from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
        from mente_laylay.autonomia.coordenador_intencao import executar_fluxo_intencao
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1

    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    expected_exts=frozenset({".txt",".md",".markdown",".log",".csv",".json",".yaml",".yml",".py",".js",".ts",".html",".css"})
    ext_ok=exts==expected_exts and limpar_nome_arquivo_natural("nao markdown")=="nao.markdown"
    print(f"extensões canônicas produção ........................... {'PASS' if ext_ok else 'FAIL'} {sorted(exts)}")
    if not ext_ok: print("\n🟠 EXIT 1 — contrato de extensões da produção divergiu"); return 1

    def build_b(texto):
        return construir_turno_b(texto,base=base,extensoes=exts,resolver_revisao_real=resolver_revisao_intra_turno,classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito)[0]
    def build_v25(texto):
        t,_,_=base.construir_turno_candidato(texto,resolver_revisao_real=resolver_revisao_intra_turno,classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito); return dict(t or {})
    reds=[]

    title("FASE 0 — REPRODUÇÃO DO RED 4.29 + DRIFT `.markdown`")
    v25_txt=build_v25("cria arquivo nao.txt")
    op_txt=str(v25_txt.get("texto_operacional") or "")
    rop_txt=detectar_arquivo_real(op_txt,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto)
    rraw_txt=detectar_arquivo_real("cria arquivo nao.txt",detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto)
    red429=bool(
        not base.turno_tem_veto_execucao(v25_txt)
        and base.autoriza_execucao_efetiva(v25_txt)
        and _intent(rop_txt)==_intent(rraw_txt)=="CREATE_FILE"
        and campo(rop_txt,"alvo")=="nao txt"
        and campo(rraw_txt,"alvo")=="nao.txt"
    )
    print(f"V2.5 op={op_txt!r}")
    print(f"router(OP)  -> {rop_txt}")
    print(f"router(RAW) -> {rraw_txt}")
    print(f"RED 4.29 basename reproduzido ......................... {'PASS' if red429 else 'FAIL'}")
    if not red429:
        print("\n🟠 EXIT 1 — baseline/roteador não reproduziu a premissa do 4.29")
        return 1

    v25_markdown=build_v25("cria arquivo nao.markdown")
    drift_markdown=bool(
        ".markdown" in exts
        and base.turno_tem_veto_execucao(v25_markdown)
        and not base.autoriza_execucao_efetiva(v25_markdown)
    )
    print(f"produção suporta .markdown; V2.5 privado veta ........ {'PASS' if drift_markdown else 'FAIL'}")
    if not drift_markdown:
        print("\n🟠 EXIT 1 — drift `.markdown` esperado não foi reproduzido")
        return 1

    title("FASE 0B — SIDE-BUG SEPARADO: `move` NÃO GANHA AUTORIDADE NO B")
    move_plain=build_v25("move arquivo teste.txt para pasta teste")
    move_atom=build_b("move arquivo nao.txt para pasta teste")
    move_plain_veto=base.turno_tem_veto_execucao(move_plain)
    move_plain_auth=base.autoriza_execucao_efetiva(move_plain)
    move_atom_veto=base.turno_tem_veto_execucao(move_atom)
    move_atom_auth=base.autoriza_execucao_efetiva(move_atom)
    move_router_plain=detectar_arquivo_real("move arquivo teste.txt para pasta teste",detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto)
    side_move=bool(
        move_plain_veto is False and move_plain_auth is False
        and move_atom_veto is False and move_atom_auth is False
        and _intent(move_router_plain)=="FILE_TRANSACTION"
    )
    print(f"baseline move normal -> veto={move_plain_veto} auth={move_plain_auth}")
    print(f"B move nao.txt       -> veto={move_atom_veto} auth={move_atom_auth}")
    print(f"roteador direto move -> {move_router_plain}")
    print(f"side-bug pré-B isolado ................................. {'PASS' if side_move else 'FAIL'}")
    if not side_move:
        print("\n🟠 EXIT 1 — premissa do side-bug `move` divergiu; não reclassificar como B")
        return 1

    title("FASE 1 — AUTORIDADE: ÁTOMO LITERAL ESTREITO / SEM DESVETAR STT")
    casos_aut=[
        ("cria arquivo nao.txt",False,True,"literal txt"),
        ("cria arquivo chamado não.md",False,True,"literal acentuado md"),
        ("cria arquivo nao.markdown",False,True,"literal markdown canônico"),
        ("cria arquivo de texto nao.txt",False,True,"moldura arquivo de texto"),
        ('cria arquivo chamado "nao.txt"',False,True,"literal entre aspas"),
        ("abre o arquivo nao.txt",False,True,"open literal"),
        ("escreve ola dentro do arquivo nao.txt",False,True,"edit literal"),
        ("procura arquivo nao.txt",False,True,"search literal"),
        ("cria arquivo nao.exe",True,False,"extensão não suportada"),
        ("cria arquivo nao txt",True,False,"STT sem ponto ambíguo"),
        ("cria arquivo chamado nao txt",True,False,"frame sem ponto ainda ambíguo"),
        ("cria arquivo nao.txt contendo nao aumenta o volume",True,False,"boundary conteúdo/ato negativo"),
        ("cria arquivo nao.markdown e nao fecha o opera",True,False,"boundary segundo ato negativo"),
    ]
    aut_ok=True
    turnos={}
    for texto,eveto,eauth,rotulo in casos_aut:
        t=build_b(texto); turnos[texto]=t
        veto=base.turno_tem_veto_execucao(t); auth=base.autoriza_execucao_efetiva(t)
        ok=(veto is eveto and auth is eauth)
        aut_ok=aut_ok and ok
        print(f"{rotulo:<38} veto={veto!s:<5} auth={auth!s:<5} {'PASS' if ok else 'FAIL'} | {texto}")
    if not aut_ok: reds.append("autoridade: literalidade estreita ou fail-closed STT divergiu")

    # A mudança de regex/helper no módulo baseline precisa sempre ser restaurada.
    restore_atom=bool("markdown" not in base.FILE_ATOM_RE.pattern and base._marcador_em_atomo_arquivo.__name__=="_marcador_em_atomo_arquivo")
    print(f"baseline restaurado após cada classificação ........... {'PASS' if restore_atom else 'FAIL'}")
    if not restore_atom:
        print("\n🟠 EXIT 1 — monkeypatch de autoridade não foi restaurado")
        return 1

    title("FASE 2 — ROTEADOR REAL OP/RAW + RECONCILIAÇÃO SOMENTE DE CAMPO")
    casos_rotas=[
        {"texto":"cria arquivo nao.txt","intent":"CREATE_FILE","expect":{"alvo":"nao.txt"}},
        {"texto":"cria arquivo de texto nao.txt","intent":"CREATE_FILE","expect":{"alvo":"nao.txt","tipo_arquivo":"texto"}},
        {"texto":"cria arquivo chamado não.md","intent":"CREATE_FILE","expect":{"alvo":"não.md"}},
        {"texto":'cria arquivo chamado "nao.txt"',"intent":"CREATE_FILE","expect":{"alvo":"nao.txt"}},
        {"texto":"cria arquivo nao.markdown","intent":"CREATE_FILE","expect":{"alvo":"nao.markdown"}},
        {"texto":"cria arquivo nao.txt contendo teste","intent":"CREATE_FILE","expect":{"alvo":"nao.txt","conteudo":"teste"}},
        {"texto":"cria pasta teste e dentro dela arquivo nao.txt","intent":"CREATE_FOLDER","expect":{"nome":"teste","arquivo_nome":"nao.txt"}},
        {"texto":"escreve ola dentro do arquivo nao.txt","intent":"CREATE_FILE","expect":{"alvo":"nao.txt","conteudo":"ola","editar_existente":True}},
        {"texto":"abre arquivo nao.txt","intent":"FILE_SEARCH","expect":{"query":"nao.txt"}},
        {"texto":"apaga arquivo nao.txt","intent":"DELETE_ITEM","expect":{"alvo":"nao.txt"}},
        {"texto":"procura arquivo nao.txt","intent":"FILE_SEARCH","expect":{"query":"nao.txt"}},
    ]
    rotas_ok=True
    rota_detalhes=[]
    for c in casos_rotas:
        texto=c["texto"]; t=build_b(texto)
        r,rota,campos=resolver_b(t,texto,base=base,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts)
        params=_params(r)
        ok=bool(_intent(r)==c["intent"] and all(params.get(k)==v for k,v in c["expect"].items()))
        rotas_ok=rotas_ok and ok
        rota_detalhes.append((texto,r,campos,ok))
        print(f"{'PASS' if ok else 'FAIL'} {texto!r}")
        print(f"     intent={_intent(r)} rota={rota!r} campos_raw={campos} params={params}")
    if not rotas_ok: reds.append("roteamento: campo literal não sobreviveu em uma rota de arquivo")

    # `move` tem um side-bug de autoridade anterior ao B. Portanto o B NÃO
    # fabrica um turno autorizado para ele. A literalidade de FILE_TRANSACTION
    # é provada somente no boundary real do parser + merge, que já é alcançável
    # como componente e continua sem efeito físico.
    move_op=detectar_arquivo_real("move arquivo nao txt para pasta teste",detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto)
    move_raw=detectar_arquivo_real("move arquivo nao.txt para pasta teste",detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto)
    move_corr,move_campos=reconciliar_literalidade_filename(
        move_op,move_raw,
        texto_op="move arquivo nao txt para pasta teste",
        texto_raw="move arquivo nao.txt para pasta teste",
        normalizar=normalizar_texto,extensoes=exts,
    )
    # Para FILE_TRANSACTION, o roteador real já canonicaliza a origem
    # com limpar_nome_arquivo_natural(). Portanto o OP pode chegar aqui já como
    # `nao.txt`; nesse caso o merge correto é NO-OP (campos=[]). Exigir um merge
    # artificial falsificaria o harness, não o candidato.
    move_component_ok=bool(
        _intent(move_op)==_intent(move_raw)==_intent(move_corr)=="FILE_TRANSACTION"
        and campo(move_op,"origem")=="nao.txt"
        and campo(move_raw,"origem")=="nao.txt"
        and campo(move_corr,"origem")=="nao.txt"
        and campo(move_corr,"destino")==campo(move_op,"destino")
        and move_campos==[]
        and move_atom_veto is False and move_atom_auth is False
    )
    print(f"FILE_TRANSACTION OP   -> {move_op}")
    print(f"FILE_TRANSACTION RAW  -> {move_raw}")
    print(f"FILE_TRANSACTION merge-> {move_corr} campos={move_campos}")
    print(f"move literal parser-canon / merge NO-OP / sem auth .... {'PASS' if move_component_ok else 'FAIL'}")
    if not move_component_ok: reds.append("FILE_TRANSACTION: parser/merge literal divergiu no side-bug `move`")

    # CREATE_FILE de texto nunca pode virar `nao txt.txt` ou `nao.txt.txt`.
    r_texto=next((x[1] for x in rota_detalhes if x[0]=="cria arquivo de texto nao.txt"),None)
    no_double=campo(r_texto,"alvo")=="nao.txt" and not campo(r_texto,"alvo").endswith(".txt.txt")
    print(f"sem dupla extensão `.txt.txt` .......................... {'PASS' if no_double else 'FAIL'}")
    if not no_double: reds.append("CREATE_FILE texto: dupla extensão criada")

    title("FASE 3 — FALSIFICAÇÕES DE MERGE / RAW NÃO GANHA AUTORIDADE")
    adv=[]
    def chk(nome,cond,detalhe=""):
        adv.append((nome,bool(cond))); print(f"{nome:<58} {'PASS' if cond else 'FAIL'} {detalhe}")

    # Intent diferente: RAW jamais troca a ação escolhida pelo OP.
    op={"intent":"CREATE_FILE","params":{"alvo":"nao txt"}}
    raw={"intent":"DELETE_ITEM","params":{"alvo":"nao.txt"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria arquivo nao txt",texto_raw="apaga arquivo nao.txt",normalizar=normalizar_texto,extensoes=exts)
    chk("intent mismatch não faz merge",_intent(out)=="CREATE_FILE" and campo(out,"alvo")=="nao txt" and fields==[],str(out))

    op={"intent":"CREATE_FILE","params":{"alvo":"nao txt"}}
    raw={"intent":"CREATE_FILE","params":{"alvo":"nao.txt"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria arquivo nao txt",texto_raw="cria arquivo nao.txt e fecha o opera",normalizar=normalizar_texto,extensoes=exts)
    chk("texto inteiro divergente não faz merge",campo(out,"alvo")=="nao txt" and fields==[],str(out))

    # Mesmo intent, alvo semanticamente diferente: não copiar.
    op={"intent":"CREATE_FILE","params":{"alvo":"relatorio txt"}}
    raw={"intent":"CREATE_FILE","params":{"alvo":"nao.txt"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria arquivo relatorio txt",texto_raw="cria arquivo nao.txt",normalizar=normalizar_texto,extensoes=exts)
    chk("alvo não equivalente não faz merge",campo(out,"alvo")=="relatorio txt" and fields==[],str(out))

    # Extensão fora do contrato textual da produção não recebe exceção.
    op={"intent":"CREATE_FILE","params":{"alvo":"nao exe"}}
    raw={"intent":"CREATE_FILE","params":{"alvo":"nao.exe"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria arquivo nao exe",texto_raw="cria arquivo nao.exe",normalizar=normalizar_texto,extensoes=exts)
    chk(".exe não faz merge",campo(out,"alvo")=="nao exe" and fields==[],str(out))

    # Mesmo target inferido por parser, mas sem basename pontuado literal no RAW.
    op={"intent":"CREATE_FILE","params":{"alvo":"nao txt"}}
    raw={"intent":"CREATE_FILE","params":{"alvo":"nao.txt"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria arquivo nao txt",texto_raw="cria arquivo nao txt",normalizar=normalizar_texto,extensoes=exts)
    chk("sem ponto literal RAW não faz merge",campo(out,"alvo")=="nao txt" and fields==[],str(out))

    # Conteúdo não pertence à allowlist: mesmo que RAW preserve pontuação, fica OP.
    op={"intent":"CREATE_FILE","params":{"alvo":"nao txt","conteudo":"texto com ponto","tipo_arquivo":"texto"}}
    raw={"intent":"CREATE_FILE","params":{"alvo":"nao.txt","conteudo":"texto.com.ponto","tipo_arquivo":"texto"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria arquivo nao txt contendo texto com ponto",texto_raw="cria arquivo nao.txt contendo texto.com.ponto",normalizar=normalizar_texto,extensoes=exts)
    chk("conteúdo RAW nunca é copiado",campo(out,"alvo")=="nao.txt" and _params(out).get("conteudo")=="texto com ponto" and fields==["alvo"],str(out))

    # Destino de move não é filename de origem; não pode ser reescrito pelo RAW.
    op={"intent":"FILE_TRANSACTION","params":{"operacao":"mover","origem":"nao txt","destino":"pasta teste"}}
    op={"intent":"FILE_TRANSACTION","params":{"operacao":"mover","origem":"nao txt","destino":"pasta literal"}}
    raw={"intent":"FILE_TRANSACTION","params":{"operacao":"mover","origem":"nao.txt","destino":"pasta.literal"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="move arquivo nao txt para pasta literal",texto_raw="move arquivo nao.txt para pasta.literal",normalizar=normalizar_texto,extensoes=exts)
    chk("destino RAW nunca é copiado",campo(out,"origem")=="nao.txt" and campo(out,"destino")=="pasta literal" and fields==["origem"],str(out))

    # Turno vetado não chama nem o reconciliador operacional do B.
    killer="cria arquivo nao.txt contendo nao aumenta o volume"
    tk=build_b(killer)
    rk,rota_k,fields_k=resolver_b(tk,killer,base=base,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts)
    chk("RAW não revive turno VETADO",rk is None and rota_k=="sem_autoridade" and fields_k==[],f"veto={base.turno_tem_veto_execucao(tk)}")

    # STT sem ponto continua fail-closed, mesmo que o cleaner de arquivo saiba
    # restaurar extensão falada em outro contexto.
    tstt=build_b("cria arquivo nao txt")
    rs,rota_s,fields_s=resolver_b(tstt,"cria arquivo nao txt",base=base,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts)
    chk("STT `nao txt` não recebe autoridade",rs is None and rota_s=="sem_autoridade" and base.turno_tem_veto_execucao(tstt),rota_s)

    # Campo não allowlisted em CREATE_FOLDER (nome da pasta) não muda.
    op={"intent":"CREATE_FOLDER","params":{"nome":"pasta literal","arquivo_nome":"nao txt"}}
    raw={"intent":"CREATE_FOLDER","params":{"nome":"pasta.literal","arquivo_nome":"nao.txt"}}
    out,fields=reconciliar_literalidade_filename(op,raw,texto_op="cria pasta literal arquivo nao txt",texto_raw="cria pasta.literal arquivo nao.txt",normalizar=normalizar_texto,extensoes=exts)
    chk("nome da pasta RAW não é copiado",campo(out,"nome")=="pasta literal" and campo(out,"arquivo_nome")=="nao.txt" and fields==["arquivo_nome"],str(out))

    if not all(v for _,v in adv): reds.append("merge: RAW ganhou campo/autoridade fora da allowlist estreita")

    title("FASE 4 — `executar_fluxo_intencao` REAL / EXECUTOR FINAL RECORDER")
    casos_fluxo=[
        ("cria arquivo nao.txt","CREATE_FILE",{"alvo":"nao.txt"},True),
        ("cria arquivo de texto nao.txt","CREATE_FILE",{"alvo":"nao.txt","tipo_arquivo":"texto"},True),
        ("cria pasta teste e dentro dela arquivo nao.txt","CREATE_FOLDER",{"arquivo_nome":"nao.txt"},True),
        ("procura arquivo nao.txt","FILE_SEARCH",{"query":"nao.txt"},True),
        ("cria arquivo nao.exe","",{},False),
        ("cria arquivo nao txt","",{},False),
        ("cria arquivo nao.txt contendo nao aumenta o volume","",{},False),
    ]
    fluxo_ok=True
    for texto,ei,ep,deve in casos_fluxo:
        t=build_b(texto)
        ok,calls,regs,auto=executar_fluxo_b(t,texto,base=base,executar_fluxo=executar_fluxo_intencao,detectar=detectar_intencao_arquivos,normalizar_texto=normalizar_texto,extensoes=exts)
        if deve:
            c0=calls[0] if len(calls)==1 else {}
            this=bool(ok and len(calls)==1 and c0.get("intent")==ei and all(c0.get("params",{}).get(k)==v for k,v in ep.items()) and c0.get("texto")==texto)
        else:
            this=bool(not ok and calls==[])
        fluxo_ok=fluxo_ok and this
        print(f"{'PASS' if this else 'FAIL'} {texto!r} -> ok={ok} calls={calls}")
    if not fluxo_ok: reds.append("integração: executar_fluxo_intencao não preservou a fronteira OP/RAW")

    title("FASE 5 — WIRING FONTE OP/RAW + INVARIANTES FINAIS")
    try:
        coord_src=(repo/"mente_laylay/autonomia/coordenador_intencao.py").read_text(encoding="utf-8")
        pre_src=(repo/"mente_laylay/autonomia/pre_fluxo_contextual.py").read_text(encoding="utf-8")
    except Exception as e:
        print(f"\n🟠 EXIT 1 — não consegui auditar fonte local travada: {e}")
        return 1
    wiring_source=bool(
        "original = str(texto_original or texto)" in coord_src
        and "intent, rota = resolvedor(texto, origem, ctx)" in coord_src
        and "texto_execucao = str(texto_original or texto)" in coord_src
        and "texto_original=texto_original" in coord_src
        and "processar_comando_deterministico(deteccao, origem, t)" in pre_src
    )
    print(f"OP resolve / RAW sobrevive separado na fonte ........... {'PASS' if wiring_source else 'FAIL'}")
    if not wiring_source:
        print("\n🟠 EXIT 1 — wiring OP/RAW divergiu do boundary estudado")
        return 1

    # O B não pode deixar alterações temporárias no baseline importado.
    restored_final=bool(
        "markdown" not in base.FILE_ATOM_RE.pattern
        and base._marcador_em_atomo_arquivo.__name__=="_marcador_em_atomo_arquivo"
    )
    print(f"baseline V2.5 restaurado ............................... {'PASS' if restored_final else 'FAIL'}")
    if not restored_final:
        print("\n🟠 EXIT 1 — estado temporário do candidato vazou")
        return 1

    invariantes={
        "4.29 basename RED reproduzido":red429,
        "drift .markdown reproduzido":drift_markdown,
        "side-bug move isolado":side_move,
        "move parser canoniza / merge no-op / sem auth":move_component_ok,
        "autoridade literal estreita":aut_ok,
        "baseline restaurado após classificação":restore_atom,
        "rotas de arquivo preservam filename":rotas_ok,
        "sem dupla extensão":no_double,
        "falsificações de merge":all(v for _,v in adv),
        "fluxo real até executor recorder":fluxo_ok,
        "wiring OP/RAW fonte":wiring_source,
        "baseline restaurado final":restored_final,
    }
    for nome,ok in invariantes.items(): print(f"{nome:<56} {'PASS' if ok else 'FAIL'}")
    if reds:
        print("\n🔴 EXIT 2 — CANDIDATO V2.5.1-B FALSIFICADO")
        print("FIRST RED:",reds[0])
        for x in reds: print("❌",x)
        return 2
    if not all(invariantes.values()):
        print("\n🔴 EXIT 2 — INVARIANTE FINAL FALHOU")
        return 2
    print("\n🟢 EXIT 0 — CANDIDATO LAB V2.5.1-B REV3 GREEN")
    print("Literalidade de filename sobreviveu à matriz; FILE_TRANSACTION canonizou no parser, merge ficou no-op e o side-bug `move` não ganhou autoridade.")
    print("Produção continua intacta; GREEN ainda exige segunda revisão integral antes da integração A+B.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
