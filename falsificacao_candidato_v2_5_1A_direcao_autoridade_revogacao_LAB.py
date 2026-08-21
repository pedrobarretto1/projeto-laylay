#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANDIDATO LAB V2.5.1-A — DIREÇÃO DE AUTORIDADE / REVOGAÇÃO.

NÃO ALTERA PRODUÇÃO.

Princípio: veto sticky é monotônico no eixo de autoridade, não no eixo de toda
mutação. Sob `veto_execucao_operacional=True`:
- confirmar/executar/reutilizar autoridade: PROIBIDO;
- cancelar/rejeitar/limpar autoridade antiga: PERMITIDO;
- conversa sem autoridade: PERMITIDA.

Este LAB importa o V2.5 GREEN exato por SHA, reproduz o RED 4.29 do gate por
nome de função e testa um desenho direcional usando os helpers reais. Filename
/ nao.txt NÃO é corrigido aqui.

EXIT 0 = LAB GREEN; 1 = harness/lock inválido; 2 = candidato falsificado.
"""
from __future__ import annotations

import hashlib, importlib.util, re, subprocess, sys, time
from pathlib import Path
from typing import Any, Callable, Mapping

HEAD="a4741bc57bc55a50ef2861dbaef09ab36397ff63"
BASELINE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASELINE_SHA256="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
BLOBS={
"laylay.py":"7f89a8e4944f7df83de0835fbd3142f6cd127c60",
"mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
"mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
"mente_laylay/cognicao/normalizacao_linguagem.py":"92d9a30435a4401c487e991ed793223eb215aeb7",
"mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
"mente_laylay/autonomia/fluxo_resposta_ia.py":"604cf86905aa6c3d55fdf4b574a9b6c934c00725",
"mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
"mente_laylay/autonomia/pre_fluxo_musical.py":"7b3f7111f3c844c1b9676ad4f3101786ce500947",
"mente_laylay/autonomia/feedback_pendente_runtime.py":"c5b70bfc4a27e0e6db7967316119df98b3c40f34",
"mente_laylay/autonomia/fluxos_conversa.py":"1ff5008506ebdbca007643596f9b07af9f04550c",
"mente_laylay/memoria_mental/musica_conversacional_runtime.py":"730ca4a70e9d7c4f8eb9456b3fb71d5f2789e481",
"mente_laylay/memoria_mental/aprendizado_rotina_musica.py":"916c91322979fef7fd8138fad8a8b9c4461b6f2e",
"mente_laylay/arquivos/lixeira_laylay.py":"b98ead854231c2ac3f8939498b7a0a990897ca2e",
}
REVOGATORIAS=frozenset({"CANCEL_DELETE_ITEM"})

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

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def title(s): print("\n# "+s+"\n"+"="*94)
def imod(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"spec inválida: {path}")
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

def turno_ctx(ctx):
    mente=(ctx or {}).get("mente_integrada_estado",{}) if isinstance(ctx,dict) else {}
    t=mente.get("turno_atual",{}) if isinstance(mente,dict) else {}
    return dict(t or {}) if isinstance(t,dict) else {}
def intent(r): return str((r or {}).get("intent") or "").upper().strip() if isinstance(r,dict) else ""
def bound(fn): return getattr(fn,"__self__",None)

def visual_dir(ctx,texto,*,real,base):
    if base.turno_tem_veto_execucao(turno_ctx(ctx)): return False,""
    return real(ctx,texto)
def curta_dir(ctx,texto,*,real,base):
    if base.turno_tem_veto_execucao(turno_ctx(ctx)): return False,""
    return real(ctx,texto)

def pendencia_dir(ctx,texto,*,real,base,bloqueios):
    if not base.turno_tem_veto_execucao(turno_ctx(ctx)): return real(ctx,texto)
    c=dict(ctx); curto=c.get("_executar_intencao_curta_contextual"); fallback=c.get("executar_intencao")
    def guard(fn,boundary):
        def f(r,t,*a,**k):
            i=intent(r)
            if i not in REVOGATORIAS:
                bloqueios.append({"boundary":boundary,"intent":i,"texto":t}); return False
            return bool(fn(r,t,*a,**k)) if callable(fn) else False
        return f
    c["_executar_intencao_curta_contextual"]=guard(curto,"pendencia_curta")
    c["executar_intencao"]=guard(fallback,"pendencia_fallback")
    if callable(c.get("_recomendar_musica_verificada")):
        c["_recomendar_musica_verificada"]=lambda *a,**k: bloqueios.append({"boundary":"oferta_musical"}) or False
    return real(c,texto)

def direcao_feedback(hctx,texto,*,combina):
    cl=hctx.get("_classificar_confirmacao_local"); local=cl(texto) if callable(cl) else None
    if local is not None: return bool(local)
    cc=hctx.get("_classificar_confirmacao_contextual")
    if not callable(cc): return None
    t=re.sub(r"\s+"," ",str(texto or "").strip().lower())
    e=hctx.get("_email_sugestao_pendente")
    if isinstance(e,dict):
        a=str(e.get("remetente") or "").strip()
        if combina(hctx,"email",t,a): return cc(texto,f"ver os emails de {a}" if a else "ver os emails")
    p=hctx.get("_playlist_sugestao_pendente")
    if isinstance(p,dict):
        a=str(p.get("playlist") or "").strip()
        if combina(hctx,"playlist",t,a): return cc(texto,f"salvar a musica na playlist {a}")
    r=hctx.get("_rotina_sugestao_pendente")
    if isinstance(r,dict):
        a=str(r.get("app") or "").strip()
        if combina(hctx,"rotina",t,a): return cc(texto,f"abrir {a}")
    return None

def feedback_dir(ctx,texto,*,real,base,combina,bloqueios):
    if not base.turno_tem_veto_execucao(turno_ctx(ctx)): return real(ctx,texto)
    rt=bound(ctx.get("_handle_feedback_pendente")); getter=getattr(rt,"_contexto_getter",None)
    if rt is None or not callable(getter): return False,""
    def cg():
        b=getter(); b=dict(b or {}) if isinstance(b,dict) else {}; hr=b.get("handle_feedback_pendente")
        def hd(hctx,t):
            d=direcao_feedback(hctx,t,combina=combina)
            if d is False: return bool(hr(hctx,t)) if callable(hr) else False
            if d is True: bloqueios.append({"boundary":"feedback_confirmacao","texto":t})
            return False
        def ex(r,t,*a,**k):
            bloqueios.append({"boundary":"feedback_continuacao","intent":intent(r),"texto":t}); return False
        b["handle_feedback_pendente"]=hd
        if callable(b.get("executar_intencao")): b["executar_intencao"]=ex
        return b
    rt._contexto_getter=cg
    try: return real(ctx,texto)
    finally: rt._contexto_getter=getter

def musica_dir(ctx,texto,*,real,base,bloqueios):
    if not base.turno_tem_veto_execucao(turno_ctx(ctx)): return real(ctx,texto)
    rt=bound(ctx.get("_processar_confirmacao_sugestao_musical")); ex=getattr(rt,"executar_intencao",None); reg=getattr(rt,"registrar_resultado_execucao",None)
    if rt is None or not callable(ex): return False,""
    tentou={"v":False}
    def eb(r,t): tentou["v"]=True; bloqueios.append({"boundary":"musica_execucao","intent":intent(r),"texto":t}); return False
    rt.executar_intencao=eb
    if callable(reg): rt.registrar_resultado_execucao=lambda *a,**k: None
    try: ok,rota=real(ctx,texto)
    finally:
        rt.executar_intencao=ex
        if callable(reg): rt.registrar_resultado_execucao=reg
    return (False,"") if tentou["v"] else (bool(ok),str(rota or ""))

def reparacao_dir(ctx,texto,*,real,base,pre,bloqueios):
    if not base.turno_tem_veto_execucao(turno_ctx(ctx)): return real(ctx,texto)
    old=pre.executar_resultado_contextual
    def blocked(c,r,t,**k): bloqueios.append({"boundary":"reparacao_operacional","intent":intent(r),"texto":t}); return False
    pre.executar_resultado_contextual=blocked
    try: return real(ctx,texto)
    finally: pre.executar_resultado_contextual=old

def prefluxo_dir(ctx,texto,*,fluxo,pre,inicio,base,combina,bloqueios):
    names=("processar_continuacao_visao_jogo","processar_reparacao_conversacional","processar_resposta_pendencia_prioritaria","processar_feedback_pendente","processar_confirmacao_musical_pendente","processar_pergunta_curta_contextual")
    old={}
    for n in names:
        r=getattr(fluxo,n,None)
        if not callable(r): continue
        old[n]=r
        if n=="processar_continuacao_visao_jogo": w=lambda c,t,_r=r: visual_dir(c,t,real=_r,base=base)
        elif n=="processar_reparacao_conversacional": w=lambda c,t,_r=r: reparacao_dir(c,t,real=_r,base=base,pre=pre,bloqueios=bloqueios)
        elif n=="processar_resposta_pendencia_prioritaria": w=lambda c,t,_r=r: pendencia_dir(c,t,real=_r,base=base,bloqueios=bloqueios)
        elif n=="processar_feedback_pendente": w=lambda c,t,_r=r: feedback_dir(c,t,real=_r,base=base,combina=combina,bloqueios=bloqueios)
        elif n=="processar_confirmacao_musical_pendente": w=lambda c,t,_r=r: musica_dir(c,t,real=_r,base=base,bloqueios=bloqueios)
        else: w=lambda c,t,_r=r: curta_dir(c,t,real=_r,base=base)
        setattr(fluxo,n,w)
    try: return bool(inicio(ctx,texto))
    finally:
        for n,r in old.items(): setattr(fluxo,n,r)


def base_ctx(turno,pendencia=None):
    mente={"turno_atual":dict(turno or {})}
    if pendencia is not None: mente["pendencia_atual"]=dict(pendencia)
    return {"mente_integrada_estado":mente,"_contexto_horario_atual":lambda:"teste"}
def pend_delete():
    return {"id":"del-v251a","origem":"lixeira_laylay","tipo":"confirmacao_exclusao","acao":"confirmar_exclusao","status":"ativa","foi_falada":True}

class PendMusica:
    def __init__(self,titulo="Numb",aceita_titulo=False):
        a=time.time(); self.atual={"id":"music-v251a","origem":"musica_conversacional","acao":"confirmar_sugestao_musical","criada_em":a,"metadados":{"titulo":titulo,"ts":a,"aceita_titulo":bool(aceita_titulo)}}; self.eventos=[]
    def obter(self): return dict(self.atual or {})
    def registrar(self,**k):
        n={"id":f"music-{len(self.eventos)+2}","origem":k.get("origem"),"acao":k.get("acao"),"criada_em":time.time(),"metadados":dict(k.get("metadados") or {})}; self.atual=n; self.eventos.append(("registrar",n["id"])); return dict(n)
    def concluir(self,pid,status):
        if self.atual and str(self.atual.get("id"))==str(pid): self.eventos.append(("concluir",str(status))); self.atual=None; return True
        return False

def main():
    print("CANDIDATO LAB V2.5.1-A — DIREÇÃO DE AUTORIDADE / REVOGAÇÃO")
    print("="*94); print("produção: INTACTA | efeito físico: ZERO | rede: ZERO | LLM real: ZERO")
    try: repo=repo_root()
    except Exception as e: print(f"\n🟠 EXIT 1 — {e}"); return 1
    title("GUARDS / LOCKS / BASELINE V2.5 EXATO")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print(f"HEAD ........................................ {'PASS' if h==HEAD else 'FAIL'} {h}")
    if h!=HEAD: bad.append("HEAD mudou")
    for f,exp in BLOBS.items():
        cur=git(repo,"rev-parse",f"HEAD:{f}"); ok=cur==exp; print(f"{f:<70} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f"blob mudou: {f}")
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print(f"produção rastreada limpa ............................... {'PASS' if clean else 'FAIL'}")
    if not clean: print(dirty); bad.append("produção suja")
    bp=repo/BASELINE_FILE; bh=sha256(bp) if bp.is_file() else ""; bok=bh==BASELINE_SHA256; print(f"baseline V2.5 GREEN exato .............................. {'PASS' if bok else 'FAIL'} {bh or 'ausente'}")
    if not bok: bad.append("baseline V2.5 ausente/divergente")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        base=imod("laylay_v25_green_baseline",bp)
        import mente_laylay.autonomia.fluxo_resposta_ia as fluxo
        import mente_laylay.autonomia.pre_fluxo_contextual as pre
        from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia as inicio
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_resposta_pendencia_prioritaria,processar_feedback_pendente,processar_confirmacao_musical_pendente,processar_reparacao_conversacional,processar_continuacao_visao_jogo,processar_pergunta_curta_contextual
        from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente,_pendencia_combina_com_texto
        from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
        from mente_laylay.memoria_mental.musica_conversacional_runtime import MusicaConversacionalRuntime
        from mente_laylay.memoria_mental.aprendizado_rotina_musica import normalizar_confirmacao_texto
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
    except Exception as e: print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1
    wiring={
      "baseline broad gate contém DELETE":"processar_resposta_pendencia_prioritaria" in set(base.ETAPAS_PRE_FLUXO_VETADAS),
      "baseline broad gate contém feedback":"processar_feedback_pendente" in set(base.ETAPAS_PRE_FLUXO_VETADAS),
      "fluxo usa helper real DELETE":fluxo.processar_resposta_pendencia_prioritaria is processar_resposta_pendencia_prioritaria,
      "fluxo usa helper real feedback":fluxo.processar_feedback_pendente is processar_feedback_pendente,
      "fluxo usa helper real música":fluxo.processar_confirmacao_musical_pendente is processar_confirmacao_musical_pendente,
      "fluxo usa helper real reparação":fluxo.processar_reparacao_conversacional is processar_reparacao_conversacional,
      "fluxo usa helper real visão":fluxo.processar_continuacao_visao_jogo is processar_continuacao_visao_jogo,
      "fluxo usa helper real curta":fluxo.processar_pergunta_curta_contextual is processar_pergunta_curta_contextual,
    }
    for k,v in wiring.items(): print(f"{k:<58} {'PASS' if v else 'FAIL'}")
    if not all(wiring.values()): print("\n🟠 EXIT 1 — WIRING DIVERGIU"); return 1
    def construir(texto):
        t,_,_=base.construir_turno_candidato(texto,resolver_revisao_real=resolver_revisao_intra_turno,classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito); return dict(t or {})
    def vetado(texto,modalidade="recusa"):
        return base.aplicar_veto_canonico({"texto_original":texto,"texto":texto,"modalidade":modalidade,"modalidade_geral":modalidade,"autoriza_execucao":False,"acao_explicita":False,"segmentos":[{"indice":0,"texto":texto,"modalidade":modalidade,"autoriza_execucao":False,"acao_explicita":False}]},texto=texto,modalidade=modalidade,natureza="controle_adversarial_v251a",motivo="receipt adversarial LAB V2.5.1-A",requer_esclarecimento=False,origem_veto="lab_v2_5_1a")
    reds=[]
    title("FASE 0 — RECEIPT BASELINE / NÃO VAZA ENTRE TURNOS")
    tn=construir("olha esse item"); tv=construir("fecha o opera nao a microsoft store"); tp=construir("fecha o opera")
    f0=(not base.turno_tem_veto_execucao(tn) and tn.get("autoriza_execucao") is False and base.turno_tem_veto_execucao(tv) and not base.autoriza_execucao_efetiva(tv) and not base.turno_tem_veto_execucao(tp) and base.autoriza_execucao_efetiva(tp))
    print(f"NEUTRO veto={base.turno_tem_veto_execucao(tn)} auth={tn.get('autoriza_execucao')}")
    print(f"VETADO veto={base.turno_tem_veto_execucao(tv)} auth={tv.get('autoriza_execucao')}")
    print(f"NOVO TURNO veto={base.turno_tem_veto_execucao(tp)} auth={tp.get('autoriza_execucao')}")
    print(f"receipt não vaza ....................................... {'PASS' if f0 else 'FAIL'}")
    if not f0: print("\n🟠 EXIT 1 — baseline do receipt divergiu"); return 1

    def feedback_fixture(turno,llm_true=False):
        cont={"rotina_sugestao_pendente":{"ts":time.time(),"app":"opera","hora":"23:00"},"playlist_sugestao_pendente":None,"email_sugestao_pendente":None}; ev=[]; ex=[]; regs=[]; falas=[]
        def get(k): return cont.get(k)
        def upd(**k): cont.update(k)
        def illm(texto,sug): return False if "nao" in normalizar_confirmacao_texto(texto).split() else bool(llm_true)
        def resolver(resto,origem): return ({"intent":"CLOSE_APP","params":{"alvo":"Opera"}},"fixture")
        def executar(r,t): ex.append({"intent":intent(r),"texto":t}); return True
        rctx={"continuidades_get":get,"continuidades_update":upd,"normalizar_texto_com_apelidos":normalizar_confirmacao_texto,"interpretar_confirmacao_llm":illm,"handle_feedback_pendente":handle_feedback_pendente,"handle_sugestao_confirmacao":lambda t:False,"musica_operacoes":None,"extrair_nome_playlist":lambda t:"","yt_clean_title":lambda s:str(s or ""),"falar_com_lipsync":lambda fala,*a,**k:falas.append(str(fala)),"rotina_registrar_feedback":lambda **k:ev.append(dict(k)),"gmail_buscar_nao_lidos":lambda:[],"gmail_falar_resumo_estiloso":lambda *a,**k:None,"registrar_feedback_proatividade":lambda *a,**k:ev.append({"tipo":"proatividade","args":a,"kwargs":k}),"registrar_feedback_aprendizado":lambda *a,**k:ev.append({"tipo":"aprendizado","args":a,"kwargs":k}),"resolver_comando_natural":resolver,"executar_intencao":executar,"registrar_resultado_execucao":lambda *a,**k:regs.append({"args":a,"kwargs":k}),"mente_integrada_estado":{"turno_atual":dict(turno or {})}}
        rt=FeedbackPendenteRuntime(contexto_getter=lambda:rctx); c=base_ctx(turno); c["_handle_feedback_pendente"]=rt.handle_feedback_pendente; c["_handle_feedback_pendente_misto"]=rt.handle_feedback_pendente_misto
        return c,rt,cont,ev,ex,regs,falas

    title("FASE 1 — CONTRASTE V2.5 ANTIGO: RED 4.29 REPRODUZIDO")
    tc=construir("nao apaga o arquivo")
    if not base.turno_tem_veto_execucao(tc): print("🟠 EXIT 1 — precondição 'nao apaga o arquivo' não sticky"); return 1
    old_calls=[]; co=base_ctx(tc,pend_delete()); co["_executar_intencao_curta_contextual"]=lambda r,t,**k:old_calls.append(intent(r)) or True
    old_tr=bool(base.prefluxo_candidato(co,"nao apaga o arquivo",fluxo_modulo=fluxo,processar_inicio_real=inicio)); old_del=(not old_tr and "CANCEL_DELETE_ITEM" not in old_calls)
    print(f"V2.5 antigo DELETE -> tratado={old_tr} calls={old_calls} {'RED reproduzido' if old_del else 'NÃO reproduziu'}")
    if not old_del: print("\n🟠 EXIT 1 — baseline não reproduziu RED DELETE conhecido"); return 1
    tf=construir("nao abre o opera")
    if not base.turno_tem_veto_execucao(tf): print("🟠 EXIT 1 — precondição 'nao abre o opera' não sticky"); return 1
    cfo,rtfo,conto,evo,exo,rgo,fao=feedback_fixture(tf)
    old_ftr=bool(base.prefluxo_candidato(cfo,"nao abre o opera",fluxo_modulo=fluxo,processar_inicio_real=inicio)); old_fb=(not old_ftr and isinstance(conto.get("rotina_sugestao_pendente"),dict) and not exo)
    print(f"V2.5 antigo feedback -> tratado={old_ftr} pendente_viva={isinstance(conto.get('rotina_sugestao_pendente'),dict)} {'RED reproduzido' if old_fb else 'NÃO reproduziu'}")
    if not old_fb: print("\n🟠 EXIT 1 — baseline não reproduziu RED feedback conhecido"); return 1

    title("FASE 2 — DELETE: REVOGAR PASSA / CONFIRMAR NÃO")
    bd=[]; cc=[]; c=base_ctx(tc,pend_delete()); c["_executar_intencao_curta_contextual"]=lambda r,t,**k:cc.append(intent(r)) or True
    tr=prefluxo_dir(c,"nao apaga o arquivo",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bd); ok_cancel=(tr and cc==["CANCEL_DELETE_ITEM"])
    print(f"sticky CANCEL -> tratado={tr} calls={cc} {'PASS' if ok_cancel else 'FAIL'}")
    if not ok_cancel: reds.append("DELETE: CANCEL_DELETE_ITEM não sobreviveu ao sticky")
    tconf={"modalidade":"confirmacao","modalidade_geral":"confirmacao","autoriza_execucao":False,"acao_explicita":False,"veto_execucao_operacional":False}
    cp=[]; c=base_ctx(tconf,pend_delete()); c["_executar_intencao_curta_contextual"]=lambda r,t,**k:cp.append(intent(r)) or True
    trp=prefluxo_dir(c,"sim",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bd); ok_conf_pos=(trp and cp==["CONFIRM_DELETE_ITEM"])
    print(f"NEUTRO confirmação -> tratado={trp} calls={cp} {'PASS' if ok_conf_pos else 'FAIL'}")
    if not ok_conf_pos: reds.append("DELETE: confirmação neutra legítima quebrou")
    tsv=vetado("sim"); cv=[]; c=base_ctx(tsv,pend_delete()); c["_executar_intencao_curta_contextual"]=lambda r,t,**k:cv.append(intent(r)) or True
    trv=prefluxo_dir(c,"sim",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bd); ok_conf_v=(not trv and not cv)
    print(f"VETADO confirmação -> tratado={trv} calls={cv} {'PASS' if ok_conf_v else 'FAIL'}")
    if not ok_conf_v: reds.append("DELETE: CONFIRM_DELETE_ITEM atravessou sticky")
    tk=construir("olha esse item nao fecha o opera"); ck=[]; c=base_ctx(tk,pend_delete()); c["_executar_intencao_curta_contextual"]=lambda r,t,**k:ck.append(intent(r)) or True
    trk=prefluxo_dir(c,"olha esse item nao fecha o opera",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bd); ok_kdel=(not trk and not ck)
    print(f"killer não relacionado -> tratado={trk} calls={ck} {'PASS' if ok_kdel else 'FAIL'}")
    if not ok_kdel: reds.append("DELETE: pendência sequestrou killer")

    title("FASE 3 — FEEDBACK: REJEITAR/LIMPAR PASSA; ACEITAR/CONTINUAR NÃO")
    bf=[]; cf,rtf,cont,ev,ex,rg,fa=feedback_fixture(tf)
    fr=prefluxo_dir(cf,"nao abre o opera",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bf)
    ok_fneg=(fr and cont.get("rotina_sugestao_pendente") is None and not ex and any(e.get("aceito") is False for e in ev if isinstance(e,dict)))
    print(f"feedback negativo sticky -> tratado={fr} pendente={cont.get('rotina_sugestao_pendente')!r} exec={ex} {'PASS' if ok_fneg else 'FAIL'}")
    if not ok_fneg: reds.append("feedback: rejeição contextual não limpou pendência")
    cfp,rtfp,contp,evp,exp,rgp,fap=feedback_fixture(tconf,llm_true=True)
    frp=prefluxo_dir(cfp,"sim",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bf)
    ok_fpos=(frp and contp.get("rotina_sugestao_pendente") is None and any(e.get("aceito") is True for e in evp if isinstance(e,dict)))
    print(f"feedback NEUTRO positivo -> tratado={frp} {'PASS' if ok_fpos else 'FAIL'}")
    if not ok_fpos: reds.append("feedback: positivo neutro quebrou")
    cfv,rtfv,contv,evv,exv,rgv,fav=feedback_fixture(tsv,llm_true=True)
    frv=prefluxo_dir(cfv,"sim",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bf)
    ok_fv=(not frv and isinstance(contv.get("rotina_sugestao_pendente"),dict) and not exv and not any(e.get("aceito") is True for e in evv if isinstance(e,dict)))
    print(f"feedback VETADO positivo -> tratado={frv} pendente_viva={isinstance(contv.get('rotina_sugestao_pendente'),dict)} {'PASS' if ok_fv else 'FAIL'}")
    if not ok_fv: reds.append("feedback: confirmação positiva atravessou sticky")
    tmix=vetado("nao e depois fecha o opera"); cfm,rtfm,contm,evm,exm,rgm,fam=feedback_fixture(tmix)
    frm=prefluxo_dir(cfm,"nao e depois fecha o opera",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bf)
    ok_fmix=(frm and contm.get("rotina_sugestao_pendente") is None and not exm and any(b.get("boundary")=="feedback_continuacao" and b.get("intent")=="CLOSE_APP" for b in bf))
    print(f"feedback misto -> tratado={frm} pendente={contm.get('rotina_sugestao_pendente')!r} exec_real={exm} {'PASS' if ok_fmix else 'FAIL'}")
    if not ok_fmix: reds.append("feedback misto: revogação/resto operacional não separados")
    cfk,rtfk,contk,evk,exk,rgk,fak=feedback_fixture(tk)
    frk=prefluxo_dir(cfk,"olha esse item nao fecha o opera",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bf)
    ok_fk=(not frk and isinstance(contk.get("rotina_sugestao_pendente"),dict) and not exk)
    print(f"feedback killer -> tratado={frk} pendente_viva={isinstance(contk.get('rotina_sugestao_pendente'),dict)} {'PASS' if ok_fk else 'FAIL'}")
    if not ok_fk: reds.append("feedback: killer foi sequestrado")

    title("FASE 4 — MÚSICA: CONVERSA PASSA / MUSIC_SEARCH NÃO")
    def musica_fixture(turno,aceita_titulo=False):
        pend=PendMusica("Numb",aceita_titulo); falas=[]; ex=[]; res=[]; mc=[]; estado={}
        def executar(r,t): ex.append({"intent":intent(r),"texto":t}); return True
        rt=MusicaConversacionalRuntime(estado_mental_getter=lambda:estado,normalizar_texto=normalizar_confirmacao_texto,falar=lambda fala,*a,**k:falas.append(str(fala)),registrar_mente_curta=lambda *a,**k:mc.append({"args":a,"kwargs":k}),executar_intencao=executar,registrar_resultado_execucao=lambda *a,**k:res.append({"args":a,"kwargs":k}),registrar_autoaprimoramento=lambda *a,**k:None,enviar_mensagem=None,buscar_resultados_musicais=None,pendencia_runtime=pend,log=lambda *a,**k:None)
        c=base_ctx(turno); c["_processar_confirmacao_sugestao_musical"]=rt.processar_confirmacao
        return c,rt,pend,falas,ex,res,mc
    bm=[]
    cm,rpm,ppm,fpm,xpm,zpm,mpm=musica_fixture(tconf)
    mr=prefluxo_dir(cm,"pode tocar",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bm)
    ok_mpos=(mr and [x["intent"] for x in xpm]==["MUSIC_SEARCH"])
    print(f"música NEUTRA confirma -> tratado={mr} exec={xpm} {'PASS' if ok_mpos else 'FAIL'}")
    if not ok_mpos: reds.append("música: confirmação neutra quebrou")
    tmc=construir("cade a musica nao toca ainda")
    if not base.turno_tem_veto_execucao(tmc): tmc=vetado("cade a musica nao toca ainda")
    cmc,rmc,pmc,fmc,xmc,zmc,mmc=musica_fixture(tmc)
    mrc=prefluxo_dir(cmc,"cade a musica nao toca ainda",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bm)
    ok_mconv=(mrc and bool(fmc) and not xmc)
    print(f"música VETADA conversacional -> tratado={mrc} falas={len(fmc)} exec={xmc} {'PASS' if ok_mconv else 'FAIL'}")
    if not ok_mconv: reds.append("música: conversa segura morreu sob sticky")
    tmv=vetado("pode tocar")
    cmv,rmv,pmv,fmv,xmv,zmv,mmv=musica_fixture(tmv)
    mrv=prefluxo_dir(cmv,"pode tocar",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bm)
    ok_mv=(not mrv and not xmv and pmv.atual is not None)
    print(f"música VETADA confirma -> tratado={mrv} exec_real={xmv} pendente_viva={pmv.atual is not None} {'PASS' if ok_mv else 'FAIL'}")
    if not ok_mv: reds.append("música: MUSIC_SEARCH atravessou sticky/consumiu pendência")
    tmt=vetado("Numb")
    cmt,rmt,pmt,fmt,xmt,zmt,mmt=musica_fixture(tmt,aceita_titulo=True)
    mrt=prefluxo_dir(cmt,"Numb",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bm)
    ok_mt=(not mrt and not xmt and pmt.atual is not None)
    print(f"título musical VETADO -> tratado={mrt} exec_real={xmt} {'PASS' if ok_mt else 'FAIL'}")
    if not ok_mt: reds.append("música: título pendente criou MUSIC_SEARCH sob sticky")

    title("FASE 5 — REPARAÇÃO: CONVERSA PASSA / INTENT PRÁTICA NÃO")
    def reparo_fixture(turno,operacional):
        falas=[]; ex=[]; regs=[]
        rep={"tipo":"operacional","alvo_anterior":"Microsoft Store","alvo_novo":"Opera","operacao_corrigida":"CLOSE_APP","intencao":{"intent":"CLOSE_APP","params":{"alvo":"Opera"}}} if operacional else {"tipo":"conversacional","alvo_anterior":"um assunto","alvo_novo":"o item certo"}
        c=base_ctx(turno); c["_resolver_reparacao_conversacional"]=lambda t:dict(rep); c["falar_com_lipsync"]=lambda fala,*a,**k:falas.append(str(fala)); c["executar_intencao"]=lambda r,t:ex.append(intent(r)) or True; c["_registrar_resultado_execucao"]=lambda *a,**k:regs.append({"args":a,"kwargs":k}); c["_registrar_autoaprimoramento"]=lambda *a,**k:None
        return c,falas,ex,regs
    br=[]; trp_v=vetado("corrige isso")
    crc,frc,xrc,rrc=reparo_fixture(trp_v,False)
    rrcase=prefluxo_dir(crc,"corrige isso",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=br)
    ok_rc=(rrcase and bool(frc) and not xrc); print(f"reparação conversacional VETADA -> tratado={rrcase} fala={bool(frc)} exec={xrc} {'PASS' if ok_rc else 'FAIL'}")
    if not ok_rc: reds.append("reparação: conversa segura morreu sob sticky")
    cro,fro,xro,rro=reparo_fixture(trp_v,True)
    rrocase=prefluxo_dir(cro,"corrige isso",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=br)
    ok_ro=(not rrocase and not xro and any(b.get("boundary")=="reparacao_operacional" and b.get("intent")=="CLOSE_APP" for b in br)); print(f"reparação operacional VETADA -> tratado={rrocase} exec_real={xro} {'PASS' if ok_ro else 'FAIL'}")
    if not ok_ro: reds.append("reparação: intent prática atravessou sticky/falso tratado")
    trp_pos={"modalidade":"correcao","modalidade_geral":"correcao","autoriza_execucao":True,"acao_explicita":True,"veto_execucao_operacional":False}
    crp,frp2,xrp,rrp=reparo_fixture(trp_pos,True)
    rrpos=prefluxo_dir(crp,"corrige isso",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=br)
    ok_rp=(rrpos and xrp==["CLOSE_APP"]); print(f"reparação operacional positiva -> tratado={rrpos} exec={xrp} {'PASS' if ok_rp else 'FAIL'}")
    if not ok_rp: reds.append("reparação: controle positivo quebrou")

    title("FASE 6 — VISÃO / PERGUNTA CURTA: SEM RAMO REVOGATÓRIO")
    bv=[]; vn=[]; cvn=base_ctx(tn); cvn["_continuar_visao_jogo_pendente"]=lambda t:vn.append(t) or True
    vrn=prefluxo_dir(cvn,"olha esse item",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bv); ok_vn=(vrn and len(vn)==1)
    print(f"visão NEUTRA -> tratado={vrn} calls={len(vn)} {'PASS' if ok_vn else 'FAIL'}")
    if not ok_vn: reds.append("visão: continuação neutra quebrou")
    vv=[]; cvv=base_ctx(tk); cvv["_continuar_visao_jogo_pendente"]=lambda t:vv.append(t) or True
    vrv=prefluxo_dir(cvv,"olha esse item nao fecha o opera",fluxo=fluxo,pre=pre,inicio=inicio,base=base,combina=_pendencia_combina_com_texto,bloqueios=bv); ok_vv=(not vrv and not vv)
    print(f"visão VETADA -> tratado={vrv} calls={len(vv)} {'PASS' if ok_vv else 'FAIL'}")
    if not ok_vv: reds.append("visão: sticky alcançou continuação")
    sp=[]; csp=base_ctx(tn); csp["_resolver_pergunta_curta_contextual_intencao"]=lambda t:{"intent":"CLOSE_APP","params":{"alvo":"Opera"}}; csp["_executar_intencao_curta_contextual"]=lambda r,t,**k:sp.append(intent(r)) or True
    sok,srota=curta_dir(csp,"ele?",real=processar_pergunta_curta_contextual,base=base); ok_sp=(sok and sp==["CLOSE_APP"])
    print(f"curta NEUTRA -> rota={srota!r} exec={sp} {'PASS' if ok_sp else 'FAIL'}")
    if not ok_sp: reds.append("pergunta curta: controle neutro quebrou")
    sv=[]; csv=base_ctx(tk); csv["_resolver_pergunta_curta_contextual_intencao"]=lambda t:{"intent":"CLOSE_APP","params":{"alvo":"Opera"}}; csv["_executar_intencao_curta_contextual"]=lambda r,t,**k:sv.append(intent(r)) or True
    svok,svrota=curta_dir(csv,"ele?",real=processar_pergunta_curta_contextual,base=base); ok_sv=(not svok and not sv)
    print(f"curta VETADA -> rota={svrota!r} exec={sv} {'PASS' if ok_sv else 'FAIL'}")
    if not ok_sv: reds.append("pergunta curta: reuso atravessou sticky")

    title("FASE 7 — RESTAURAÇÃO / INVARIANTES")
    restored=(fluxo.processar_resposta_pendencia_prioritaria is processar_resposta_pendencia_prioritaria and fluxo.processar_feedback_pendente is processar_feedback_pendente and fluxo.processar_confirmacao_musical_pendente is processar_confirmacao_musical_pendente and fluxo.processar_reparacao_conversacional is processar_reparacao_conversacional and fluxo.processar_continuacao_visao_jogo is processar_continuacao_visao_jogo and fluxo.processar_pergunta_curta_contextual is processar_pergunta_curta_contextual)
    print(f"wiring restaurado ....................................... {'PASS' if restored else 'FAIL'}")
    if not restored: print("\n🟠 EXIT 1 — monkeypatch não restaurou símbolos reais"); return 1
    inv={"V2.5 RED DELETE reproduzido":old_del,"V2.5 RED feedback reproduzido":old_fb,"CANCEL sticky permitido":ok_cancel,"CONFIRM neutro preservado":ok_conf_pos,"CONFIRM sticky bloqueado":ok_conf_v,"DELETE não sequestra killer":ok_kdel,"feedback negativo limpa":ok_fneg,"feedback positivo neutro":ok_fpos,"feedback positivo sticky bloqueado":ok_fv,"feedback misto direcional":ok_fmix,"feedback não sequestra killer":ok_fk,"música positiva":ok_mpos,"música conversacional sticky":ok_mconv,"MUSIC_SEARCH sticky bloqueado":ok_mv,"título musical sticky bloqueado":ok_mt,"reparação conversa sticky":ok_rc,"reparação operacional sticky":ok_ro,"reparação positiva":ok_rp,"visão neutra":ok_vn,"visão sticky":ok_vv,"curta neutra":ok_sp,"curta sticky":ok_sv,"receipt não vaza":f0}
    for k,v in inv.items(): print(f"{k:<52} {'PASS' if v else 'FAIL'}")
    if reds:
        print("\n🔴 EXIT 2 — CANDIDATO V2.5.1-A FALSIFICADO"); print("FIRST RED:",reds[0]); [print("❌",x) for x in reds]; return 2
    if not all(inv.values()): print("\n🔴 EXIT 2 — INVARIANTE FINAL FALHOU"); return 2
    print("\n🟢 EXIT 0 — CANDIDATO LAB V2.5.1-A GREEN")
    print("Direção de autoridade/revogação sobreviveu à matriz; produção continua intacta.")
    print("Ainda exige segunda revisão integral antes do eixo B ou de patch real.")
    return 0

if __name__=="__main__": raise SystemExit(main())
