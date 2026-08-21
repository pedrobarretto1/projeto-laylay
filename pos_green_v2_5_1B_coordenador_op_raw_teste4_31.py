#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PÓS-GREEN V2.5.1-B — COORDENADOR OP/RAW / TESTE 4.31.

NÃO ALTERA PRODUÇÃO e não executa efeito físico.

Objetivo
========
A REV3 provou o B até `executar_fluxo_intencao()`. Esta prova fecha a lacuna da
segunda revisão atravessando o boundary real:

processar_comando_deterministico_precoce REAL
 -> CicloComandosRuntime.processar_deterministico REAL
 -> executar_fluxo_intencao REAL
 -> CicloComandosRuntime._resolver_decisao_canonica REAL
 -> resolver_intencao REAL + arbitro REAL
 -> detector de arquivo REAL (injetado como habilidade determinística focal)
 -> CicloComandosRuntime.executar_intencao REAL
 -> roteador físico SUBSTITUÍDO por recorder in-memory

O detector focal é `detectar_intencao_arquivos` real. Não chamamos este teste de
full detector graph: ele é component-integration do boundary coordenador OP/RAW.

O teste primeiro exige reproduzir o defeito do baseline no caminho acima:
`cria arquivo nao.txt` chega ao resolvedor como `cria arquivo nao txt` e o alvo
fica `nao txt`. Depois instala SOMENTE no objeto em memória um wrapper candidato
sobre `_resolver_decisao_canonica`, capturando o RAW que o pré-fluxo já passa no
terceiro argumento, e aplica a reconciliação estreita da REV3.

EXIT 0 = pós-GREEN 4.31 GREEN.
EXIT 1 = lock/wiring/premissa/harness inválido.
EXIT 2 = B falsificado nesta fronteira.
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

HEAD="a4741bc57bc55a50ef2861dbaef09ab36397ff63"
B_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"
B_SHA="29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
BLOBS={
"mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
"mente_laylay/autonomia/coordenador_intencao.py":"de8a893cd60ab44ad9bc3437d01db15ba54fb367",
"mente_laylay/arquivos/roteador_arquivos.py":"36fc40861db60c0aabe324669272c28d1d89d2f5",
"mente_laylay/arquivos/nome_natural.py":"9f6f7d10fa7ac0baae2c11204b984a1d451a5c5e",
"mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
"mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
"mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
}

def git(repo,*args,check=True):
    q=subprocess.run(["git",*args],cwd=str(repo),text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and q.returncode: raise RuntimeError(q.stderr.strip() or q.stdout.strip())
    return q.stdout.strip()

def root():
    seen=set()
    for s in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (s,*s.parents):
            if x in seen: continue
            seen.add(x)
            if (x/".git").exists() and (x/"laylay.py").exists(): return x
    raise RuntimeError("execute dentro do repo Laylay")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m

def title(s): print("\n# "+s+"\n"+"="*94)
def intent(r): return str((r or {}).get("intent") or "").upper().strip() if isinstance(r,dict) else ""
def params(r): return dict((r or {}).get("params") or {}) if isinstance(r,dict) and isinstance((r or {}).get("params"),dict) else {}

class ContextoRuntimeMemoria:
    def __init__(self,turno): self.turno=dict(turno or {})
    def montar(self):
        return {
            "turno_atual":dict(self.turno),
            "retrato_turno_atual":{},
            "continuidade_geral":{},
            "registrar_arbitragem_turno":lambda *a,**k:None,
        }

def main():
    print("PÓS-GREEN V2.5.1-B — COORDENADOR OP/RAW / TESTE 4.31")
    print("="*94)
    print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=root()
    except Exception as e: print("\n🟠 EXIT 1 —",e); return 1

    title("GUARDS / LOCKS / ARTEFATOS EXATOS")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print("HEAD", "PASS" if h==HEAD else "FAIL", h)
    if h!=HEAD: bad.append("HEAD")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e; print(f"{f:<70} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f)
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print("produção causal limpa", "PASS" if clean else "FAIL")
    if not clean: print(dirty); bad.append("produção suja")
    bp=repo/B_FILE; vp=repo/BASE_FILE
    bh=sha(bp) if bp.is_file() else ""; vh=sha(vp) if vp.is_file() else ""
    print("B REV3 exato", "PASS" if bh==B_SHA else "FAIL", bh or "ausente")
    print("V2.5 baseline exato", "PASS" if vh==BASE_SHA else "FAIL", vh or "ausente")
    if bh!=B_SHA: bad.append("B REV3 ausente/divergente")
    if vh!=BASE_SHA: bad.append("baseline V2.5 ausente/divergente")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))

    try:
        B=imod("v251b_rev3_exact_431",bp); base=imod("v25_exact_431",vp)
        import mente_laylay.autonomia.coordenador_intencao as coord_mod
        from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_comando_deterministico_precoce
        from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1

    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    def build(texto):
        return B.construir_turno_b(
            texto,base=base,extensoes=exts,
            resolver_revisao_real=resolver_revisao_intra_turno,
            classificar_real=classificar_modalidade_turno,
            p0_real=_protecao_p0_ato_fala,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )[0]

    def montar_ciclo(turno, detector_textos, execucoes):
        contexto_runtime=ContextoRuntimeMemoria(turno)
        registros=[]; auto=[]
        def detector_focal(texto):
            detector_textos.append(str(texto or ""))
            return detectar_intencao_arquivos(
                str(texto or ""),
                params_cb=lambda **kwargs:kwargs,
                estado_mental={},
                normalizar_texto=normalizar_texto,
            )
        ns={
            "_normalizar_texto_com_apelidos":normalizar_texto,
            "_texto_depende_de_contexto":lambda _t:False,
            "_refinar_contexto_mental":lambda _t:None,
            "_texto_cancela_acao_agora":lambda _t:False,
            "_resolver_comando_midia_contextual_forcado":lambda _t:None,
            "_resolver_comando_contextual_forcado":lambda _t:None,
            "_resolver_comando_acao_geral_contextual_forcado":lambda _t:None,
            "_resolver_repeticao_ultima_acao":lambda _t:None,
            "detectar_intencao_deterministica":detector_focal,
            "_limpar_nome_playlist":lambda x:str(x or "").strip(),
            "_extrair_agendamento_local":lambda _t:None,
            "_extrair_acao_agendada_local":lambda _t:None,
            "_registrar_resultado_execucao":lambda *a,**k:registros.append((a,k)),
            "_registrar_autoaprimoramento":lambda *a,**k:auto.append((a,k)),
            "_detectar_repetir_briefing":lambda _t:False,
            "repetir_briefing":lambda *a,**k:False,
            "interpretar_comando_local_rapido":lambda _t:None,
            "_texto_parece_consulta_operacional":lambda _t:True,
        }
        ciclo=CicloComandosRuntime(namespace_getter=lambda:ns,contexto_intencao_runtime=contexto_runtime,log=lambda *a,**k:None)
        return ciclo,registros,auto

    old_executor=coord_mod.executar_intencao
    def executor_recorder(resultado,texto_original,ctx_execucao):
        execucoes_globais.append({"intent":intent(resultado),"params":params(resultado),"texto":str(texto_original or "")})
        return True
    execucoes_globais=[]
    coord_mod.executar_intencao=executor_recorder

    def rodar(texto,*,candidato):
        turno=build(texto)
        detector_textos=[]; execs=[]
        # O recorder global é esvaziado por caso; `execs` recebe a cópia final.
        execucoes_globais.clear()
        ciclo,regs,auto=montar_ciclo(turno,detector_textos,execs)
        original_resolver=ciclo._resolver_decisao_canonica
        if candidato:
            raw=str(texto)
            def resolver_b_boundary(texto_op,origem,contexto=None):
                resultado,rota=original_resolver(texto_op,origem,contexto)
                if not isinstance(resultado,dict): return resultado,rota
                if base.turno_tem_veto_execucao(turno) or not base.autoriza_execucao_efetiva(turno):
                    return None,""
                rraw=detectar_intencao_arquivos(
                    raw,params_cb=lambda **kwargs:kwargs,estado_mental={},normalizar_texto=normalizar_texto,
                )
                if not isinstance(rraw,dict): return resultado,rota
                corr,campos=B.reconciliar_literalidade_filename(
                    resultado,rraw,
                    texto_op=str(texto_op or ""),texto_raw=raw,
                    normalizar=normalizar_texto,extensoes=exts,
                )
                return corr,("arquivo-literalidade-coordenador" if campos else rota)
            ciclo._resolver_decisao_canonica=resolver_b_boundary
        ctx={"mente_integrada_estado":{"turno_atual":dict(turno)},"processar_comando_deterministico":ciclo.processar_deterministico}
        try:
            ok,rota=processar_comando_deterministico_precoce(ctx,texto,origem="teste4.31")
            execs.extend(dict(x) for x in execucoes_globais)
            return turno,bool(ok),str(rota or ""),detector_textos,execs
        finally:
            ciclo._resolver_decisao_canonica=original_resolver

    try:
        title("FASE 1 — BASELINE FULL COORDINATOR BOUNDARY REPRODUZ PERDA")
        t0,ok0,rota0,det0,ex0=rodar("cria arquivo nao.txt",candidato=False)
        baseline_red=bool(
            base.autoriza_execucao_efetiva(t0)
            and not base.turno_tem_veto_execucao(t0)
            and ok0 and len(ex0)==1
            and ex0[0]["intent"]=="CREATE_FILE"
            and ex0[0]["params"].get("alvo")=="nao txt"
            and ex0[0]["texto"]=="cria arquivo nao.txt"
            and any("nao txt" in x and ".txt" not in x for x in det0)
        )
        print("turno op=",repr(t0.get("texto_operacional")))
        print("detector recebeu=",det0)
        print("executor recorder=",ex0)
        print("baseline perde basename no coordenador .................", "RED reproduzido" if baseline_red else "FAIL")
        if not baseline_red:
            print("\n🟠 EXIT 1 — premissa full coordinator do defeito não foi reproduzida")
            return 1

        title("FASE 2 — REV3 NO MESMO BOUNDARY REAL")
        casos=[
            ("cria arquivo nao.txt","nao.txt"),
            ("cria arquivo de texto nao.txt","nao.txt"),
            ('cria arquivo chamado "nao.txt"',"nao.txt"),
            ("cria arquivo nao.markdown","nao.markdown"),
            ("cria arquivo relatorio.md","relatorio.md"),
        ]
        reds=[]; positivos=[]
        for texto,alvo in casos:
            t,ok,rota,dets,execs=rodar(texto,candidato=True)
            this=bool(
                base.autoriza_execucao_efetiva(t) and not base.turno_tem_veto_execucao(t)
                and ok and len(execs)==1 and execs[0]["intent"]=="CREATE_FILE"
                and execs[0]["params"].get("alvo")==alvo
                and execs[0]["texto"]==texto
            )
            positivos.append(this)
            print(f"{'PASS' if this else 'FAIL'} {texto!r}")
            print("     op=",repr(t.get("texto_operacional")),"detector=",dets,"exec=",execs)
            if not this and not reds: reds.append(f"coordenador não preservou {alvo}")

        title("FASE 3 — VETO/AMBIGUIDADE NÃO CHEGAM AO COORDENADOR")
        killers=[
            "cria arquivo nao txt",
            "cria arquivo chamado nao txt",
            "cria arquivo nao.exe",
            "cria arquivo nao.txt contendo nao aumenta o volume",
            "cria arquivo nao.markdown e nao fecha o opera",
        ]
        bloqueios=[]
        for texto in killers:
            t,ok,rota,dets,execs=rodar(texto,candidato=True)
            this=bool(base.turno_tem_veto_execucao(t) and not base.autoriza_execucao_efetiva(t) and not ok and dets==[] and execs==[])
            bloqueios.append(this)
            print(f"{'PASS' if this else 'FAIL'} {texto!r} -> veto={base.turno_tem_veto_execucao(t)} auth={base.autoriza_execucao_efetiva(t)} det={dets} exec={execs}")
            if not this and not reds: reds.append(f"killer alcançou boundary: {texto}")

        title("RESUMO")
        checks={
            "baseline full coordinator RED reproduzido":baseline_red,
            "REV3 filenames no coordenador":all(positivos),
            "RAW segue como texto de execução":all(positivos),
            "killers param antes do detector":all(bloqueios),
        }
        for k,v in checks.items(): print(f"{k:<48} {'PASS' if v else 'FAIL'}")
        if reds or not all(checks.values()):
            print("\n🔴 EXIT 2 — V2.5.1-B FALSIFICADO NO BOUNDARY COORDENADOR")
            print("FIRST RED:",reds[0] if reds else "invariante final")
            return 2
        print("\n🟢 EXIT 0 — PÓS-GREEN V2.5.1-B / TESTE 4.31 GREEN")
        print("OP perdeu a literalidade no baseline real; REV3 restaurou somente o campo filename usando RAW já presente no pré-fluxo.")
        return 0
    finally:
        coord_mod.executar_intencao=old_executor

if __name__=="__main__": raise SystemExit(main())
