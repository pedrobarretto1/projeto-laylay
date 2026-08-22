#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PÓS-GREEN V2.5.1 INTEGRADO — PRIORIDADE REAL / TESTE 4.32.

NÃO ALTERA PRODUÇÃO. EFEITO FÍSICO ZERO.

Fecha a lacuna da segunda revisão do integrado:
processar_consulta_sistema_local() roda antes da barreira prioritária real.
O candidato in-memory bloqueia essa consulta quando há sticky, preserva
capacidade estática, aplica a barreira sticky antes das demais prioridades e
mantém FILE_SEARCH positivo com RAW `nao.txt`.

EXIT 0 = GREEN; EXIT 1 = harness/lock inválido; EXIT 2 = integrado falsificado.
"""
from __future__ import annotations
import hashlib, importlib.util, subprocess, sys
from pathlib import Path

HEAD="5cd3582562291a947464c3bcdca3bc7b83e036d8"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
B_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"
B_SHA="29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab"
BLOBS={
"mente_laylay/autonomia/comandos_imediatos.py":"27706613cb505219479664a664db038cac78c037",
"mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
"mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
"mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
"mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
"mente_laylay/arquivos/roteador_arquivos.py":"36fc40861db60c0aabe324669272c28d1d89d2f5",
}

def git(repo,*args,check=True):
    q=subprocess.run(["git",*args],cwd=str(repo),text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and q.returncode: raise RuntimeError(q.stderr.strip() or q.stdout.strip())
    return q.stdout.strip()
def root():
    for s in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (s,*s.parents):
            if (x/".git").exists() and (x/"laylay.py").exists(): return x
    raise RuntimeError("execute dentro do repo Laylay")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m
def title(s): print("\n# "+s+"\n"+"="*94)

class Estado:
    def __init__(self,turno): self.mental={"turno_atual":dict(turno)}
    def substituir(self,chave,valor):
        if chave=="mental": self.mental=dict(valor or {})

def main():
    print("PÓS-GREEN V2.5.1 INTEGRADO — PRIORIDADE REAL / TESTE 4.32")
    print("="*94); print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=root()
    except Exception as e: print("\n🟠 EXIT 1 —",e); return 1
    title("GUARDS / LOCKS")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print("HEAD", "PASS" if h==HEAD else "FAIL",h)
    if h!=HEAD: bad.append("HEAD")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e; print(f"{f:<70} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f)
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print("produção causal limpa", "PASS" if clean else "FAIL")
    if not clean: bad.append("produção suja")
    for name,exp in ((BASE_FILE,BASE_SHA),(B_FILE,B_SHA)):
        path=repo/name; got=sha(path) if path.is_file() else ""; ok=got==exp; print(name, "PASS" if ok else "FAIL",got or "ausente")
        if not ok: bad.append(name)
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        base=imod("v25_432",repo/BASE_FILE); B=imod("v251b_432",repo/B_FILE)
        import mente_laylay.autonomia.comandos_imediatos as imed
        from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1
    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    def build(texto):
        return B.construir_turno_b(texto,base=base,extensoes=exts,resolver_revisao_real=resolver_revisao_intra_turno,classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito)[0]
    def montar(turno):
        estado=Estado(turno); falas=[]; execs=[]; regs=[]; dets=[]
        ns={
            "_estado_compartilhado_runtime":estado,
            "_normalizar_texto_com_apelidos":normalizar_texto,
            "_texto_tem_comando_explicito":texto_tem_comando_explicito,
            "_resolver_alvo_ambiente":lambda nome:{"programa_aberto":True,"programa_em_foco":False},
            "_emitir_resposta_curta":lambda texto,fala,**k: falas.append((texto,fala,k)) or True,
            "_responder_pergunta_capacidade_local":lambda texto:"Posso responder isso sem executar nenhuma ação.",
            "falar_com_lipsync":lambda fala,*a,**k: falas.append(("fala",str(fala),{})) or True,
            "executar_intencao":lambda r,t: execs.append({"intent":str((r or {}).get("intent") or "").upper(),"params":dict((r or {}).get("params") or {}),"texto":t}) or True,
            "_registrar_resultado_execucao":lambda *a,**k: regs.append((a,k)),
            "_registrar_autoaprimoramento":lambda *a,**k:None,
            "detectar_intencao_deterministica":lambda texto: dets.append(texto) or None,
            "resolver_comando_natural":lambda texto,origem:(None,""),
            "_detectar_pedido_diagnostico_mente":lambda texto:False,
            "_detectar_comando_governanca_iniciativa":lambda texto:None,
            "detectar_comando_saude":lambda texto:False,
        }
        return ComandosImediatosRuntime(namespace_getter=lambda:ns,loop_getter=lambda:None,memoria_pessoas=None,iot=None),falas,execs,dets
    old_read=imed.processar_consulta_sistema_local; old_bar=imed.bloqueia_execucao_operacional_prioritaria
    def instalar():
        def read_guard(ctx,texto):
            mente=(ctx or {}).get("mente_integrada_estado",{}) if isinstance(ctx,dict) else {}; turno=dict(mente.get("turno_atual") or {}) if isinstance(mente,dict) else {}
            if base.turno_tem_veto_execucao(turno): return False,""
            return old_read(ctx,texto)
        def bar_guard(texto,*,classificacao=None,normalizar_texto=None,texto_tem_comando_explicito=None,confirmacao_contextual_valida=False):
            return base.barreira_candidata(texto,classificacao=dict(classificacao or {}),barreira_real=old_bar,normalizar_texto=(normalizar_texto or (lambda x:x)),texto_tem_comando_explicito=(texto_tem_comando_explicito or (lambda x:False)))
        imed.processar_consulta_sistema_local=read_guard; imed.bloqueia_execucao_operacional_prioritaria=bar_guard
    try:
        title("FASE 1 — BASELINE LIVE FURA STICKY")
        tsticky=build("o opera continua aberto nao fecha ele")
        if not base.turno_tem_veto_execucao(tsticky): print("\n🟠 EXIT 1 — precondição sticky divergiu"); return 1
        rt,f,x,d=montar(tsticky); real=bool(rt.processar_prioritarios("o opera continua aberto")); red=bool(real and f and not x)
        print(f"baseline tratado={real} falas={f} exec={x}"); print("bypass live", "RED reproduzido" if red else "FAIL")
        if not red: print("\n🟠 EXIT 1 — bypass não reproduziu"); return 1
        title("FASE 2 — CANDIDATO STICKY BLOQUEIA LIVE")
        instalar(); rt2,f2,x2,d2=montar(tsticky); c=bool(rt2.processar_prioritarios("o opera continua aberto")); live=bool(not c and not f2 and not x2 and not d2)
        print(f"tratado={c} falas={f2} exec={x2} det={d2} {'PASS' if live else 'FAIL'}")
        title("FASE 3 — NEUTRO READ-ONLY CONTINUA VIVO")
        tn=build("o opera continua aberto?"); rtn,fn,xn,dn=montar(tn); n=bool(rtn.processar_prioritarios("o opera continua aberto?")); neutral=bool(not base.turno_tem_veto_execucao(tn) and n and fn and not xn)
        print(f"veto={base.turno_tem_veto_execucao(tn)} tratado={n} falas={fn} {'PASS' if neutral else 'FAIL'}")
        title("FASE 4 — CAPACIDADE ESTÁTICA SOB STICKY")
        tc=base.aplicar_veto_canonico({"texto_original":"voce consegue abrir arquivos?","texto":"voce consegue abrir arquivos?","modalidade":"recusa","modalidade_geral":"recusa","natureza_acao":"capacidade","autoriza_execucao":False,"acao_explicita":False,"segmentos":[]},texto="voce consegue abrir arquivos?",modalidade="recusa",natureza="capacidade",motivo="controle 4.32",requer_esclarecimento=False,origem_veto="teste4_32")
        rtc,fc,xc,dc=montar(tc); cap=bool(rtc.processar_prioritarios("voce consegue abrir arquivos?")); capok=bool(cap and fc and not xc)
        print(f"tratado={cap} falas={fc} exec={xc} {'PASS' if capok else 'FAIL'}")
        title("FASE 5 — ARQUIVO STICKY PARA ANTES DO DETECTOR")
        tf=build("procura arquivo nao.txt e nao fecha o opera"); rtf,ff,xf,df=montar(tf); fk=bool(rtf.processar_prioritarios("procura arquivo nao.txt e nao fecha o opera")); filek=bool(base.turno_tem_veto_execucao(tf) and not fk and not ff and not xf and not df)
        print(f"tratado={fk} falas={ff} exec={xf} det={df} {'PASS' if filek else 'FAIL'}")
        title("FASE 6 — ARQUIVO POSITIVO RAW PRESERVADO")
        tp=build("procura arquivo nao.txt"); rtp,fp,xp,dp=montar(tp); pos=bool(rtp.processar_prioritarios("procura arquivo nao.txt")); posok=bool(pos and len(xp)==1 and xp[0]["intent"]=="FILE_SEARCH" and xp[0]["params"].get("query")=="nao.txt")
        print(f"tratado={pos} exec={xp} {'PASS' if posok else 'FAIL'}")
        title("RESUMO")
        checks={"baseline live RED":red,"sticky live bloqueado":live,"neutro live preservado":neutral,"capacidade estática preservada":capok,"arquivo sticky bloqueado":filek,"arquivo positivo RAW":posok}
        for k,v in checks.items(): print(f"{k:<42} {'PASS' if v else 'FAIL'}")
        if not all(checks.values()): print("\n🔴 EXIT 2 — INTEGRADO FALSIFICADO NA PRIORIDADE REAL"); print("FIRST RED:",next(k for k,v in checks.items() if not v)); return 2
        print("\n🟢 EXIT 0 — PÓS-GREEN INTEGRADO / TESTE 4.32 GREEN"); return 0
    finally:
        imed.processar_consulta_sistema_local=old_read; imed.bloqueia_execucao_operacional_prioritaria=old_bar
if __name__=="__main__": raise SystemExit(main())
