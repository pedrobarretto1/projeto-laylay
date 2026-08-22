#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PÓS-GREEN V2.5.1 INTEGRADO — REVOGAÇÃO + FILENAME DOWNSTREAM / TESTE 4.32.

NÃO ALTERA PRODUÇÃO. ZERO efeito físico.

Fecha a lacuna entre:
- LAB integrado: build B + sticky + filename + CANCEL até executor curto recorder;
- teste 4.30: A/CANCEL até porta tipada real, sem build B.

Cadeia atravessada:
build B -> A.prefluxo_dir -> prefluxo real -> pendência real -> executor curto real
-> roteador_intencao real -> executor_integracoes real -> execucao_arquivos real
-> RegistroArquivosMutacao real -> porta IN-MEMORY.

EXIT 0 = interseção A+B fechada nesta fronteira.
EXIT 1 = lock/wiring/premissa/harness inválido.
EXIT 2 = integrado falsificado; FIRST RED manda.
"""
from __future__ import annotations
import hashlib, importlib.util, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

HEAD="5cd3582562291a947464c3bcdca3bc7b83e036d8"
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
BASE_SHA="3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef"
A_FILE="falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py"
A_SHA="cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f"
B_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"
B_SHA="29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab"
P430_FILE="pos_green_v2_5_1A_cancelamento_integracao_teste4_30.py"
P430_SHA="49b0500e46740b132a1ad94954988b28d66a507cfd3f282908a4257cf787f799"
P431_FILE="pos_green_v2_5_1B_coordenador_op_raw_teste4_31.py"
P431_SHA="a6563ffd5a922d121f5f5354634c79c1964900b4af43ac9b7a942304f4c0ed1c"
BLOBS={
"mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
"mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
"mente_laylay/autonomia/porteiro_acoes.py":"19b5eaa9ddafd483eab92d46e92cca30813adbb6",
"mente_laylay/autonomia/fluxo_resposta_ia.py":"604cf86905aa6c3d55fdf4b574a9b6c934c00725",
"mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
"mente_laylay/personalidade/resposta_conversacional_runtime.py":"f113db6edbd05e0ef276e65171bfe28de1068a2c",
"mente_laylay/autonomia/roteador_intencao.py":"570cfbec2adae8be4a795e70b5d90512ff944901",
"mente_laylay/autonomia/executor_integracoes.py":"28f0c71a54b6a9616365320eb31fd7f106a5d799",
"mente_laylay/arquivos/execucao_arquivos.py":"dd77e6ace02afa52dd71f8f957197c80d1c2d582",
"mente_laylay/integracao/registro_mutacoes_arquivos.py":"c1ed8cc0297f1f3733a4319d14970e7622847423",
"mente_laylay/arquivos/mutacoes.py":"2904f3881a73f4ce17ba9b52831e8b8f3b8a940d",
"mente_laylay/arquivos/lixeira_laylay.py":"b98ead854231c2ac3f8939498b7a0a990897ca2e",
"mente_laylay/arquivos/nome_natural.py":"9f6f7d10fa7ac0baae2c11204b984a1d451a5c5e",
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

def title(s): print("\n# "+s+"\n"+"="*96)

class MutacaoMemoria:
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

def main():
    print("PÓS-GREEN V2.5.1 INTEGRADO — REVOGAÇÃO + FILENAME / TESTE 4.32")
    print("="*96)
    print("produção: INTACTA | disco: ZERO | lixeira física: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=root()
    except Exception as e: print("\n🟠 EXIT 1 —",e); return 1
    title("GUARDS / LOCKS / PROVAS EXATAS")
    bad=[]; h=git(repo,"rev-parse","HEAD"); print("HEAD", "PASS" if h==HEAD else "FAIL", h)
    if h!=HEAD: bad.append("HEAD")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e; print(f"{f:<72} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f)
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False); clean=not dirty.strip(); print("produção causal limpa", "PASS" if clean else "FAIL")
    if not clean: print(dirty); bad.append("produção suja")
    for name,exp in [(BASE_FILE,BASE_SHA),(A_FILE,A_SHA),(B_FILE,B_SHA),(P430_FILE,P430_SHA),(P431_FILE,P431_SHA)]:
        path=repo/name; got=sha(path) if path.is_file() else ""; ok=got==exp; print(f"{name:<78} {'PASS' if ok else 'FAIL'} {got or 'ausente'}")
        if not ok: bad.append(name)
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA"); [print("❌",x) for x in bad]; return 1
    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        base=imod("v25_432",repo/BASE_FILE); A=imod("v251a_432",repo/A_FILE); B=imod("v251b_432",repo/B_FILE)
        import mente_laylay.autonomia.fluxo_resposta_ia as fluxo_mod
        import mente_laylay.autonomia.pre_fluxo_contextual as pre_mod
        from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
        from mente_laylay.personalidade.resposta_conversacional_runtime import RespostaConversacionalRuntime
        from mente_laylay.autonomia.roteador_intencao import executar_intencao as executar_intencao_real
        from mente_laylay.integracao.registro_mutacoes_arquivos import registrar_arquivos_mutacao
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
        from mente_laylay.autonomia.fluxos_conversa import _pendencia_combina_com_texto
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1
    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)
    def build(texto):
        return B.construir_turno_b(texto,base=base,extensoes=exts,resolver_revisao_real=resolver_revisao_intra_turno,classificar_real=classificar_modalidade_turno,p0_real=_protecao_p0_ato_fala,normalizar_texto=normalizar_texto,texto_tem_comando_explicito=texto_tem_comando_explicito)[0]
    def montar(turno):
        porta_mem=MutacaoMemoria(); porta=registrar_arquivos_mutacao(porta_mem)
        resultados=[]; auto=[]; falas=[]; mente=[]; coord=[]
        rctx={"_target_from_params":lambda p,t="":"pc_a","_registrar_mente_curta":lambda *a,**k:mente.append((a,k)),"_registrar_resultado_execucao":lambda *a,**k:resultados.append((a,k)),"_registrar_autoaprimoramento":lambda *a,**k:auto.append((a,k)),"falar_com_lipsync":lambda fala,*a,**k:falas.append(str(fala)) or True,"_registro_arquivos_mutacao_runtime":porta,"_registro_arquivos_leitura_runtime":None,"current_emotion":"calma","emotion_level":1,"modo_jogo_ativo":False,"_normalizar_texto_com_apelidos":lambda s:str(s or "").lower()}
        def dispatch(resultado,texto): return bool(executar_intencao_real(resultado,texto,rctx))
        ns={"executar_intencao":dispatch,"_registrar_resultado_execucao":lambda *a,**k:resultados.append((a,k)),"_registrar_autoaprimoramento":lambda *a,**k:auto.append((a,k))}
        rr=RespostaConversacionalRuntime(namespace_getter=lambda:ns,estado_runtime_getter=lambda:None,fallback_fala="",log=lambda *a,**k:None)
        c=A.base_ctx(turno,pendencia=A.pend_delete())
        c["_executar_intencao_curta_contextual"]=rr.executar_intencao_curta
        c["processar_comando_deterministico"]=lambda *a,**k:coord.append((a,k)) or False
        return c,porta_mem,coord
    def prefluxo(turno,texto):
        c,m,coord=montar(turno); blocks=[]
        tratado=A.prefluxo_dir(c,texto,fluxo=fluxo_mod,pre=pre_mod,inicio=processar_inicio_fluxo_resposta_ia,base=base,combina=_pendencia_combina_com_texto,bloqueios=blocks)
        return bool(tratado),m,blocks,coord
    reds=[]
    title("FASE 1 — B BUILD + A CANCEL + DOWNSTREAM REAL")
    texto="nao apaga o arquivo nao.txt"; t=build(texto); tratado,m,blocks,coord=prefluxo(t,texto)
    cancel_ok=bool(base.turno_tem_veto_execucao(t) and not base.autoriza_execucao_efetiva(t) and tratado and m.cancel==1 and m.confirm==0 and m.outras==[] and coord==[])
    print(f"veto={base.turno_tem_veto_execucao(t)} auth={base.autoriza_execucao_efetiva(t)} tratado={tratado} cancel={m.cancel} confirm={m.confirm} outras={m.outras} coord={coord}")
    print("cancel filename até porta tipada ........................", "PASS" if cancel_ok else "FAIL")
    if not cancel_ok: reds.append("CANCEL com filename não atravessou cadeia real integrada")
    title("FASE 2 — STICKY CONFIRM NÃO ALCANÇA PORTA")
    tsim=base.aplicar_veto_canonico({"texto_original":"sim","texto":"sim","modalidade":"recusa","modalidade_geral":"recusa","autoriza_execucao":False,"acao_explicita":False,"segmentos":[]},texto="sim",modalidade="recusa",natureza="teste432",motivo="sticky integrado 4.32",requer_esclarecimento=False,origem_veto="teste4_32")
    tratado2,m2,blocks2,coord2=prefluxo(tsim,"sim")
    confirm_block=bool(not tratado2 and m2.cancel==0 and m2.confirm==0 and m2.outras==[] and coord2==[] and any(b.get("intent")=="CONFIRM_DELETE_ITEM" for b in blocks2))
    print(f"tratado={tratado2} cancel={m2.cancel} confirm={m2.confirm} blocks={blocks2} coord={coord2}")
    print("confirm sticky -> zero porta ............................", "PASS" if confirm_block else "FAIL")
    if not confirm_block: reds.append("CONFIRM antigo atravessou sticky integrado")
    title("FASE 3 — CONTROLE NEUTRO CONFIRM USA MESMA CADEIA")
    tn=build("sim")
    if base.turno_tem_veto_execucao(tn): print("\n🟠 EXIT 1 — `sim` nasceu sticky inesperadamente"); return 1
    tratado3,m3,blocks3,coord3=prefluxo(tn,"sim")
    confirm_pos=bool(tratado3 and m3.confirm==1 and m3.cancel==0 and m3.outras==[] and coord3==[])
    print(f"tratado={tratado3} cancel={m3.cancel} confirm={m3.confirm} outras={m3.outras} coord={coord3}")
    print("confirm neutro preservado ...............................", "PASS" if confirm_pos else "FAIL")
    if not confirm_pos: reds.append("CONFIRM neutro quebrou na integração")
    title("FASE 4 — REVOGAÇÃO + NOVA AÇÃO NÃO ESCAPA")
    misto="nao apaga o arquivo nao.txt e depois cria arquivo relatorio.md"; tm=build(misto); tratado4,m4,blocks4,coord4=prefluxo(tm,misto)
    mixed_ok=bool(base.turno_tem_veto_execucao(tm) and tratado4 and m4.cancel==1 and m4.confirm==0 and m4.outras==[] and coord4==[])
    print(f"veto={base.turno_tem_veto_execucao(tm)} tratado={tratado4} cancel={m4.cancel} confirm={m4.confirm} outras={m4.outras} coord={coord4}")
    print("cancel permitido / ação positiva posterior não escapa ..", "PASS" if mixed_ok else "FAIL")
    if not mixed_ok: reds.append("revogação mista deixou nova autoridade escapar ou não cancelou")
    title("RESUMO")
    checks={"CANCEL filename -> porta real in-memory":cancel_ok,"CONFIRM sticky -> zero porta":confirm_block,"CONFIRM neutro -> porta":confirm_pos,"revogação mista não libera nova ação":mixed_ok}
    for k,v in checks.items(): print(f"{k:<52} {'PASS' if v else 'FAIL'}")
    if reds or not all(checks.values()):
        print("\n🔴 EXIT 2 — INTEGRADO FALSIFICADO NO TESTE 4.32"); print("FIRST RED:",reds[0] if reds else "invariante final"); return 2
    print("\n🟢 EXIT 0 — PÓS-GREEN V2.5.1 INTEGRADO / TESTE 4.32 GREEN")
    print("Revogação com filename atravessou até a porta tipada; confirmação sticky ficou inacessível e ação positiva posterior não escapou.")
    return 0

if __name__=="__main__": raise SystemExit(main())
