#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PÓS-GREEN V2.5.1-A — CANCELAMENTO COMPONENT-INTEGRATION / TESTE 4.30.

Não altera produção, não toca em disco do usuário e não chama lixeira física.
Atravessa:

processar_resposta_pendencia_prioritaria REAL
 -> RespostaConversacionalRuntime.executar_intencao_curta REAL
 -> roteador_intencao.executar_intencao REAL
 -> executor_integracoes REAL
 -> execucao_arquivos REAL
 -> RegistroArquivosMutacao REAL
 -> porta de mutação IN-MEMORY

Objetivo: fechar a lacuna da segunda revisão do A. O LAB 2.5.1-A usou recorder
no executor curto; este teste prova que CANCEL_DELETE_ITEM também atravessa os
consumidores reais até a fronteira física tipada, enquanto CONFIRM sob sticky
continua bloqueado pelo candidato A.

EXIT 0 = confirmação component-integration GREEN.
EXIT 1 = lock/wiring/premissa inválida.
EXIT 2 = A falsificado nesta fronteira.
"""
from __future__ import annotations

import hashlib, importlib.util, subprocess, sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

HEAD="a4741bc57bc55a50ef2861dbaef09ab36397ff63"
A_FILE="falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py"
A_SHA="cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
BLOBS={
"mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
"mente_laylay/personalidade/resposta_conversacional_runtime.py":"f113db6edbd05e0ef276e65171bfe28de1068a2c",
"mente_laylay/autonomia/roteador_intencao.py":"570cfbec2adae8be4a795e70b5d90512ff944901",
"mente_laylay/autonomia/executor_integracoes.py":"28f0c71a54b6a9616365320eb31fd7f106a5d799",
"mente_laylay/arquivos/execucao_arquivos.py":"dd77e6ace02afa52dd71f8f957197c80d1c2d582",
"mente_laylay/integracao/registro_mutacoes_arquivos.py":"c1ed8cc0297f1f3733a4319d14970e7622847423",
"mente_laylay/arquivos/mutacoes.py":"2904f3881a73f4ce17ba9b52831e8b8f3b8a940d",
"mente_laylay/arquivos/lixeira_laylay.py":"b98ead854231c2ac3f8939498b7a0a990897ca2e",
"mente_laylay/autonomia/adaptador_resultado.py":"e5c9abc23dbc803f5a39e2ad700649c8409848ed",
"mente_laylay/autonomia/validacao_ambiente.py":"098d3c5675e2332198d79f37ab86922d9453a96f",
"mente_laylay/autonomia/rota_musical.py":"090e1721fa05be891bd6e80801bd77dc89aaf6d7",
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
    raise RuntimeError("execute na raiz/árvore do repo Laylay")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def imod(name,p):
    sp=importlib.util.spec_from_file_location(name,p)
    if sp is None or sp.loader is None: raise RuntimeError(f"spec inválida: {p}")
    m=importlib.util.module_from_spec(sp); sys.modules[name]=m; sp.loader.exec_module(m); return m

def title(s): print("\n# "+s+"\n"+"="*92)

class MutacaoMemoria:
    """Implementa a porta completa, mas só registra chamadas em memória."""
    def __init__(self): self.cancel=0; self.confirm=0; self.outras=[]
    def resolver_caminho(self,v): return str(v or "")
    def criar_pasta(self,c): self.outras.append("criar_pasta"); return False
    def criar_arquivo(self,c,conteudo,modo="w"): self.outras.append("criar_arquivo"); return False
    def escrever_texto_seguro(self,c,conteudo,*,sobrescrever=False): self.outras.append("escrever"); return {"ok":False}
    def mover_item(self,o,d): self.outras.append("mover"); return False
    def transacionar(self,p): self.outras.append("transacionar"); return SimpleNamespace(status="bloqueado",sucesso=False,origem="",destino="")
    def buscar_itens(self,a): return []
    def solicitar_exclusao(self,c): self.outras.append("solicitar_exclusao"); return None
    def confirmar_exclusao(self):
        self.confirm+=1
        return SimpleNamespace(status="confirmacao_fixture",sucesso=True,caminho="C:/fixture/arquivo.txt",destino="")
    def cancelar_exclusao(self): self.cancel+=1
    def restaurar_ultimo(self,caminho_esperado=""): self.outras.append("restaurar"); return SimpleNamespace(status="nao",sucesso=False,caminho="",destino="")
    def diagnostico(self): return {"somente_raizes_autorizadas":True,"escrita_segura_disponivel":True,"lixeira_reversivel":True,"confirmacao_exclusao_pendente":True}

def pendencia():
    return {"id":"del-430","origem":"lixeira_laylay","tipo":"confirmacao_exclusao","acao":"confirmar_exclusao","status":"ativa","foi_falada":True}

def ctx_turno(turno): return {"mente_integrada_estado":{"turno_atual":dict(turno),"pendencia_atual":pendencia()}}

def main():
    print("PÓS-GREEN V2.5.1-A — CANCELAMENTO COMPONENT-INTEGRATION / TESTE 4.30")
    print("="*92); print("produção: INTACTA | disco: ZERO | lixeira física: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=root()
    except Exception as e: print("\n🟠 EXIT 1 —",e); return 1
    title("GUARDS / LOCKS / ARTEFATOS EXATOS")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print("HEAD", "PASS" if h==HEAD else "FAIL", h)
    if h!=HEAD: bad.append("HEAD")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e; print(f"{f:<68} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f)
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print("produção causal limpa", "PASS" if clean else "FAIL")
    if not clean: bad.append("produção suja")
    ap=repo/A_FILE; bp=repo/BASE_FILE; ah=sha(ap) if ap.is_file() else ""; bh=sha(bp) if bp.is_file() else ""
    print("A exato", "PASS" if ah==A_SHA else "FAIL", ah or "ausente")
    print("baseline exato", "PASS" if bh==BASE_SHA else "FAIL", bh or "ausente")
    if ah!=A_SHA: bad.append("A ausente/divergente")
    if bh!=BASE_SHA: bad.append("baseline ausente/divergente")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        A=imod("v251a_exact",ap); base=imod("v25_exact_430",bp)
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_resposta_pendencia_prioritaria
        from mente_laylay.personalidade.resposta_conversacional_runtime import RespostaConversacionalRuntime
        from mente_laylay.autonomia.roteador_intencao import executar_intencao as executar_intencao_real
        from mente_laylay.integracao.registro_mutacoes_arquivos import registrar_arquivos_mutacao
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT: {type(e).__name__}: {e}"); return 1

    def vetado(texto):
        return base.aplicar_veto_canonico({"texto_original":texto,"texto":texto,"modalidade":"recusa","modalidade_geral":"recusa","autoriza_execucao":False,"acao_explicita":False,"segmentos":[]},texto=texto,modalidade="recusa",natureza="teste430",motivo="integração pós-green",requer_esclarecimento=False,origem_veto="teste4_30")
    neutro={"texto_original":"sim","modalidade":"confirmacao","modalidade_geral":"confirmacao","autoriza_execucao":False,"acao_explicita":False,"veto_execucao_operacional":False}

    def montar(turno):
        porta_mem=MutacaoMemoria(); porta=registrar_arquivos_mutacao(porta_mem)
        resultados=[]; auto=[]; falas=[]; mente=[]
        rctx={
          "_target_from_params":lambda p,t="":"pc_a",
          "_registrar_mente_curta":lambda *a,**k: mente.append((a,k)),
          "_registrar_resultado_execucao":lambda *a,**k: resultados.append((a,k)),
          "_registrar_autoaprimoramento":lambda *a,**k: auto.append((a,k)),
          "falar_com_lipsync":lambda fala,*a,**k: falas.append(str(fala)) or True,
          "_registro_arquivos_mutacao_runtime":porta,
          "_registro_arquivos_leitura_runtime":None,
          "current_emotion":"calma","emotion_level":1,
          "modo_jogo_ativo":False,
          "_normalizar_texto_com_apelidos":lambda s:str(s or "").lower(),
        }
        def dispatch(resultado,texto): return bool(executar_intencao_real(resultado,texto,rctx))
        ns={"executar_intencao":dispatch,"_registrar_resultado_execucao":lambda *a,**k: resultados.append((a,k)),"_registrar_autoaprimoramento":lambda *a,**k:auto.append((a,k))}
        rr=RespostaConversacionalRuntime(namespace_getter=lambda:ns,estado_runtime_getter=lambda:None,fallback_fala="",log=lambda *a,**k:None)
        c=ctx_turno(turno); c["_executar_intencao_curta_contextual"]=rr.executar_intencao_curta
        return c,porta_mem,resultados,falas,mente

    title("FASE 1 — STICKY CANCEL ATRAVESSA COMPONENTES REAIS")
    c,m,res,falas,mente=montar(vetado("nao apaga o arquivo")); blocks=[]
    ok,rota=A.pendencia_dir(c,"nao apaga o arquivo",real=processar_resposta_pendencia_prioritaria,base=base,bloqueios=blocks)
    cancel_ok=bool(ok and rota=="cancelamento_exclusao" and m.cancel==1 and m.confirm==0 and not m.outras)
    print(f"rota={rota!r} tratado={ok} cancel={m.cancel} confirm={m.confirm} outras={m.outras}")
    print("cancelamento até porta in-memory", "PASS" if cancel_ok else "FAIL")

    title("FASE 2 — STICKY CONFIRM CONTINUA INALCANÇÁVEL")
    c2,m2,res2,falas2,mente2=montar(vetado("sim")); blocks2=[]
    ok2,rota2=A.pendencia_dir(c2,"sim",real=processar_resposta_pendencia_prioritaria,base=base,bloqueios=blocks2)
    conf_block=bool(not ok2 and m2.cancel==0 and m2.confirm==0 and not m2.outras and any(b.get("intent")=="CONFIRM_DELETE_ITEM" for b in blocks2))
    print(f"rota={rota2!r} tratado={ok2} cancel={m2.cancel} confirm={m2.confirm} blocks={blocks2}")
    print("confirm sticky bloqueado antes da porta", "PASS" if conf_block else "FAIL")

    title("FASE 3 — CONTROLE NEUTRO CONFIRM USA MESMA CADEIA")
    c3,m3,res3,falas3,mente3=montar(neutro); blocks3=[]
    ok3,rota3=A.pendencia_dir(c3,"sim",real=processar_resposta_pendencia_prioritaria,base=base,bloqueios=blocks3)
    conf_pos=bool(ok3 and rota3=="confirmacao_exclusao" and m3.confirm==1 and m3.cancel==0 and not m3.outras)
    print(f"rota={rota3!r} tratado={ok3} cancel={m3.cancel} confirm={m3.confirm} outras={m3.outras}")
    print("confirmação neutra preservada", "PASS" if conf_pos else "FAIL")

    title("RESUMO")
    checks={"CANCEL sticky -> porta":cancel_ok,"CONFIRM sticky -> zero porta":conf_block,"CONFIRM neutro -> porta":conf_pos}
    for k,v in checks.items(): print(f"{k:<44} {'PASS' if v else 'FAIL'}")
    if not all(checks.values()):
        print("\n🔴 EXIT 2 — V2.5.1-A FALSIFICADO NA INTEGRAÇÃO PÓS-GREEN")
        return 2
    print("\n🟢 EXIT 0 — PÓS-GREEN V2.5.1-A / TESTE 4.30 GREEN")
    print("Cancelamento atravessou componentes reais até a porta tipada in-memory; confirmação sticky ficou inacessível.")
    return 0

if __name__=="__main__": raise SystemExit(main())
