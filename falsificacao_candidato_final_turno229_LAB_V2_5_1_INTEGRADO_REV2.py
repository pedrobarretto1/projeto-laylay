#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANDIDATO FINAL LAB V2.5.1 INTEGRADO — TURNO 229.

NÃO ALTERA PRODUÇÃO. EFEITO FÍSICO ZERO.

Integra somente os dois eixos já fechados separadamente:

A — direção de autoridade / revogação
    VETADO -> cancelar/rejeitar/limpar: permitido
    VETADO -> confirmar/executar/reutilizar: proibido

B — literalidade de filename
    RAW nunca cria autoridade; somente pode devolver literalidade a campos
    allowlisted de uma intent de arquivo já resolvida pelo OP.

Ordem candidata integrada
==========================
1. nascimento do turno = B sobre o baseline V2.5 (receipt sticky incluído);
2. prioridade operacional = receipt vence read-only/live/file priority;
3. pré-fluxo = A direcional, não gate por nome de função;
4. coordenador = gate sticky do V2.5/A ANTES do resolver real;
5. somente em turno efetivamente autorizado, B reconcilia filename OP/RAW;
6. executor físico final = recorder in-memory.

O LAB também prova que:
- filename literal não esconde negação real posterior;
- revogação com filename literal continua alcançável;
- B não revive VETADO, inclusive `auth=True` stale adversarial;
- A não engole um CREATE_FILE legítimo por existir pendência antiga;
- FILE_SEARCH/edição prioritários usam RAW e preservam filename sem forçar B;
- side-bug histórico `move ... -> auth=False` continua separado e NÃO corrigido.

EXIT
====
0 = integrado GREEN no LAB; ainda exige segunda revisão integral.
1 = harness/lock/wiring/premissa inválida.
2 = candidato integrado falsificado; FIRST RED manda.
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

HEAD="5cd3582562291a947464c3bcdca3bc7b83e036d8"
ARTEFATOS={
    "falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py":
        "3bfcabaab1e761be707199fd6df73ee961695a9c6ab98937119a4ca5178520ef",
    "falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py":
        "cad96dced9d779a594dec8d5aef5bc9d64b24c031b76bbd429ebed7cddb5081f",
    "pos_green_v2_5_1A_cancelamento_integracao_teste4_30.py":
        "49b0500e46740b132a1ad94954988b28d66a507cfd3f282908a4257cf787f799",
    "falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py":
        "29bb93a77197156f41898806bfb7c30b0f295e9759524f3b0cc159d622825bab",
    "pos_green_v2_5_1B_coordenador_op_raw_teste4_31.py":
        "a6563ffd5a922d121f5f5354634c79c1964900b4af43ac9b7a942304f4c0ed1c",
}
BASE_FILE="falsificacao_candidato_final_veto_monotonico_turno229_LAB_V2_5.py"
A_FILE="falsificacao_candidato_v2_5_1A_direcao_autoridade_revogacao_LAB.py"
B_FILE="falsificacao_candidato_v2_5_1B_literalidade_filename_LAB_REV3.py"

BLOBS={
    "laylay.py":"7f89a8e4944f7df83de0835fbd3142f6cd127c60",
    "mente_laylay/cognicao/contratos_turno.py":"21aea640ffa188abfe5432888a6d3608d2778e35",
    "mente_laylay/cognicao/modalidade_turno.py":"80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
    "mente_laylay/cognicao/revisao_turno.py":"222d92624899ed55cc74628869b376075b7e6a1c",
    "mente_laylay/cognicao/plano_turno.py":"a5aa5294ca813f4f78368ff6d4ca6f1ee8874113",
    "mente_laylay/cognicao/decisao_turno.py":"09b0dc8536eeef8ccd32d8a30165b6a9c32b71d9",
    "mente_laylay/cognicao/arbitro_turno.py":"7756a15a8538291a118f8b4f3ab900157fa10927",
    "mente_laylay/autonomia/pre_fluxo_contextual.py":"8b75bed91862b85d777c97a91c4aaa141e9900d8",
    "mente_laylay/autonomia/fluxo_resposta_ia.py":"604cf86905aa6c3d55fdf4b574a9b6c934c00725",
    "mente_laylay/autonomia/comandos_imediatos.py":"27706613cb505219479664a664db038cac78c037",
    "mente_laylay/autonomia/coordenador_intencao.py":"de8a893cd60ab44ad9bc3437d01db15ba54fb367",
    "mente_laylay/autonomia/composicao_ciclo_comandos.py":"aaf38b3eb4f2d726778acf2cdf58f26a558460e8",
    "mente_laylay/autonomia/resposta_ia_runtime.py":"5ed5a152c8de6af37f9bcb5fc253017b56093db5",
    "mente_laylay/arquivos/roteador_arquivos.py":"36fc40861db60c0aabe324669272c28d1d89d2f5",
    "mente_laylay/arquivos/nome_natural.py":"9f6f7d10fa7ac0baae2c11204b984a1d451a5c5e",
    "mente_laylay/autonomia/fluxos_conversa.py":"1ff5008506ebdbca007643596f9b07af9f04550c",
    "mente_laylay/autonomia/feedback_pendente_runtime.py":"c5b70bfc4a27e0e6db7967316119df98b3c40f34",
    "mente_laylay/memoria_mental/musica_conversacional_runtime.py":"730ca4a70e9d7c4f8eb9456b3fb71d5f2789e481",
    "mente_laylay/memoria_mental/aprendizado_rotina_musica.py":"916c91322979fef7fd8138fad8a8b9c4461b6f2e",
}


def git(repo: Path,*args: str,check: bool=True)->str:
    q=subprocess.run(["git",*args],cwd=str(repo),text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and q.returncode:
        raise RuntimeError(q.stderr.strip() or q.stdout.strip())
    return q.stdout.strip()


def repo_root()->Path:
    seen=set()
    for start in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (start,*start.parents):
            if x in seen: continue
            seen.add(x)
            if (x/".git").exists() and (x/"laylay.py").exists(): return x
    raise RuntimeError("execute este LAB dentro do repositório Laylay")


def sha256(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def imod(name: str,path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"spec inválida: {path}")
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod


def title(s: str)->None:
    print("\n# "+s); print("="*100)


def intent(r: Any)->str:
    return str((r or {}).get("intent") or "").upper().strip() if isinstance(r,dict) else ""


def params(r: Any)->dict[str,Any]:
    return dict((r or {}).get("params") or {}) if isinstance(r,dict) and isinstance((r or {}).get("params"),dict) else {}


def turno_ctx(ctx: Mapping[str,Any]|None)->dict[str,Any]:
    c=dict(ctx or {})
    mente=c.get("mente_integrada_estado")
    if isinstance(mente,dict):
        t=mente.get("turno_atual")
        return dict(t or {}) if isinstance(t,dict) else {}
    t=c.get("turno_atual")
    return dict(t or {}) if isinstance(t,dict) else {}


class ContextoRuntimeMemoria:
    def __init__(self,turno: Mapping[str,Any]): self.turno=dict(turno or {})
    def montar(self):
        return {
            "turno_atual":dict(self.turno),
            "retrato_turno_atual":{},
            "continuidade_geral":{},
            "registrar_arbitragem_turno":lambda *a,**k:None,
        }


def main()->int:
    print("CANDIDATO FINAL LAB V2.5.1 INTEGRADO — TURNO 229")
    print("="*100)
    print("produção: INTACTA | efeito físico: ZERO | disco: ZERO | rede: ZERO | LLM: ZERO")
    try: repo=repo_root()
    except Exception as e:
        print(f"\n🟠 EXIT 1 — {e}"); return 1

    title("GUARDS / LOCKS / PROVAS ANTERIORES EXATAS")
    bad=[]
    h=git(repo,"rev-parse","HEAD"); print(f"HEAD ........................................ {'PASS' if h==HEAD else 'FAIL'} {h}")
    if h!=HEAD: bad.append("HEAD mudou")
    for f,e in BLOBS.items():
        a=git(repo,"rev-parse",f"HEAD:{f}"); ok=a==e
        print(f"{f:<76} {'PASS' if ok else 'FAIL'}")
        if not ok: bad.append(f"blob mudou: {f}")
    dirty=git(repo,"status","--porcelain","--","laylay.py","mente_laylay",check=False)
    clean=not dirty.strip(); print(f"produção causal limpa .................................. {'PASS' if clean else 'FAIL'}")
    if not clean:
        print(dirty); bad.append("produção causal suja")
    for name,expected in ARTEFATOS.items():
        path=repo/name; got=sha256(path) if path.is_file() else ""; ok=got==expected
        print(f"{name:<76} {'PASS' if ok else 'FAIL'} {got or 'ausente'}")
        if not ok: bad.append(f"artefato ausente/divergente: {name}")
    if bad:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA")
        for x in bad: print("❌",x)
        return 1

    if str(repo) not in sys.path: sys.path.insert(0,str(repo))
    try:
        base=imod("v25_integrado_base",repo/BASE_FILE)
        A=imod("v251a_integrado",repo/A_FILE)
        B=imod("v251b_integrado",repo/B_FILE)
        import mente_laylay.autonomia.fluxo_resposta_ia as fluxo_mod
        import mente_laylay.autonomia.pre_fluxo_contextual as pre_mod
        import mente_laylay.autonomia.coordenador_intencao as coord_mod
        from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_comando_deterministico_precoce
        from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
        from mente_laylay.autonomia.comandos_imediatos import (
            _candidato_prioritario_autorizado,
            _candidato_arquivo_prioritario_autorizado,
        )
        from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
        from mente_laylay.arquivos.nome_natural import EXTENSOES_TEXTUAIS_RENOMEAVEIS
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,_protecao_p0_ato_fala,bloqueia_execucao_operacional_prioritaria
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import normalizar_texto,texto_tem_comando_explicito
        from mente_laylay.autonomia.fluxos_conversa import _pendencia_combina_com_texto
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT/WIRING: {type(e).__name__}: {e}"); return 1

    exts=frozenset(str(x).casefold() for x in EXTENSOES_TEXTUAIS_RENOMEAVEIS)

    title("WIRING SOURCE — ORDEM REAL E CANAIS OP/RAW")
    try:
        src_resp=(repo/"mente_laylay/autonomia/resposta_ia_runtime.py").read_text(encoding="utf-8")
        src_cmd=(repo/"mente_laylay/autonomia/comandos_imediatos.py").read_text(encoding="utf-8")
        src_pre=(repo/"mente_laylay/autonomia/pre_fluxo_contextual.py").read_text(encoding="utf-8")
        src_coord=(repo/"mente_laylay/autonomia/coordenador_intencao.py").read_text(encoding="utf-8")
    except Exception as e:
        print(f"\n🟠 EXIT 1 — não consegui auditar fonte local travada: {e}"); return 1
    p_prior=src_resp.find('comandos_prioritarios = _get(ctx, "processar_comandos_prioritarios")')
    p_pre=src_resp.find('inicio_fluxo = _get(ctx, "processar_inicio_fluxo")')
    ordem_real=bool(p_prior>=0 and p_pre>p_prior)
    raw_arquivo_prioritario=bool('candidato_arquivo = detectar_intencao_arquivos(' in src_cmd and 'autoridade_arquivo_prioritario = _candidato_arquivo_prioritario_autorizado(' in src_cmd)
    op_raw_pre=bool('processar_comando_deterministico(deteccao, origem, t)' in src_pre)
    coord_dual=bool('def processar_deterministico(self, texto: str, origem: str = "", texto_original: str = "")' in src_coord and 'texto_original=texto_original' in src_coord)
    for nome,ok in {
        "prioridade antes do pré-fluxo":ordem_real,
        "arquivo prioritário detecta RAW":raw_arquivo_prioritario,
        "pré-fluxo envia OP + RAW":op_raw_pre,
        "coordenador conserva texto_original":coord_dual,
    }.items(): print(f"{nome:<52} {'PASS' if ok else 'FAIL'}")
    if not all((ordem_real,raw_arquivo_prioritario,op_raw_pre,coord_dual)):
        print("\n🟠 EXIT 1 — wiring real divergiu do desenho integrado"); return 1

    def build(texto: str)->dict[str,Any]:
        return B.construir_turno_b(
            texto,base=base,extensoes=exts,
            resolver_revisao_real=resolver_revisao_intra_turno,
            classificar_real=classificar_modalidade_turno,
            p0_real=_protecao_p0_ato_fala,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )[0]

    # Gates integrados de prioridade: live/read-only não fura receipt sticky.
    def prioridade_autorizada(candidato,turno):
        if base.turno_tem_veto_execucao(turno): return False
        return bool(_candidato_prioritario_autorizado(candidato,turno))

    def prioridade_arquivo_autorizada(candidato,texto,turno,estado):
        if base.turno_tem_veto_execucao(turno): return False
        return bool(_candidato_arquivo_prioritario_autorizado(candidato,texto,turno,estado))

    execucoes_globais=[]
    old_executor=coord_mod.executar_intencao
    def executor_recorder(resultado,texto_original,ctx_execucao):
        execucoes_globais.append({"intent":intent(resultado),"params":params(resultado),"texto":str(texto_original or "")})
        return True

    def montar_ciclo(turno,detector_textos,raw_merge_calls):
        contexto_runtime=ContextoRuntimeMemoria(turno)
        registros=[]; auto=[]
        def detector_focal(texto):
            detector_textos.append(str(texto or ""))
            return detectar_intencao_arquivos(
                str(texto or ""),params_cb=lambda **kwargs:kwargs,
                estado_mental={},normalizar_texto=normalizar_texto,
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
        return CicloComandosRuntime(namespace_getter=lambda:ns,contexto_intencao_runtime=contexto_runtime,log=lambda *a,**k:None)

    def rodar_coordenador(texto: str,turno: Mapping[str,Any]|None=None):
        t=dict(turno or build(texto)); detector_textos=[]; raw_merge_calls=[]
        execucoes_globais.clear()
        ciclo=montar_ciclo(t,detector_textos,raw_merge_calls)
        original_resolver=ciclo._resolver_decisao_canonica
        raw=str(texto)
        def resolver_integrado(texto_op,origem,contexto=None):
            c=dict(contexto or {})
            # A/V2.5 primeiro: receipt impede inclusive auth=True stale ANTES
            # de agenda, detector, árbitro e IA-first.
            resultado,rota=base.resolver_intencao_candidato(
                texto_op,origem,c,resolver_real=original_resolver,
            )
            if not isinstance(resultado,dict): return resultado,rota
            turno_local=dict(c.get("turno_atual") or t)
            if base.turno_tem_veto_execucao(turno_local):
                return None,"veto_operacional_turno"
            # B nunca cria autoridade. Em estado neutro, conserva resultado
            # original e não consulta RAW para promover nada.
            if not base.autoriza_execucao_efetiva(turno_local):
                return resultado,rota
            if intent(resultado) not in B.CAMPOS_LITERALIDADE:
                return resultado,rota
            raw_merge_calls.append(raw)
            rraw=detectar_intencao_arquivos(
                raw,params_cb=lambda **kwargs:kwargs,
                estado_mental={},normalizar_texto=normalizar_texto,
            )
            if not isinstance(rraw,dict): return resultado,rota
            corr,campos=B.reconciliar_literalidade_filename(
                resultado,rraw,texto_op=str(texto_op or ""),texto_raw=raw,
                normalizar=normalizar_texto,extensoes=exts,
            )
            return corr,("arquivo-literalidade-integrado" if campos else rota)
        ciclo._resolver_decisao_canonica=resolver_integrado
        ctx={"mente_integrada_estado":{"turno_atual":dict(t)},"processar_comando_deterministico":ciclo.processar_deterministico}
        try:
            ok,rota=processar_comando_deterministico_precoce(ctx,texto,origem="lab-v2.5.1-integrado")
            return t,bool(ok),str(rota or ""),list(detector_textos),list(raw_merge_calls),[dict(x) for x in execucoes_globais]
        finally:
            ciclo._resolver_decisao_canonica=original_resolver

    coord_mod.executar_intencao=executor_recorder
    reds=[]
    try:
        title("FASE 0 — NASCIMENTO INTEGRADO: A RECEIPT + B ÁTOMO")
        casos=[
            ("fecha a microsoft store nao o opera",True,False,"STT root"),
            ("fecha só a microsoft store, não o opera",True,False,"pontuado root"),
            ("cria arquivo nao.txt",False,True,"filename txt"),
            ("cria arquivo nao.markdown",False,True,"filename markdown"),
            ('cria arquivo chamado "nao.txt"',False,True,"filename aspas"),
            ("cria arquivo nao txt",True,False,"STT filename ambíguo"),
            ("cria arquivo nao.exe",True,False,"extensão fora contrato"),
            ("cria arquivo nao.txt contendo nao aumenta o volume",True,False,"filename não esconde payload"),
            ("cria arquivo nao.markdown e nao fecha o opera",True,False,"filename não esconde segundo ato"),
        ]
        nascimento=[]
        for texto,ev,ea,rotulo in casos:
            t=build(texto); v=base.turno_tem_veto_execucao(t); a=base.autoriza_execucao_efetiva(t); ok=(v is ev and a is ea)
            nascimento.append(ok); print(f"{rotulo:<38} veto={v!s:<5} auth={a!s:<5} {'PASS' if ok else 'FAIL'} | {texto}")
            if not ok and not reds: reds.append(f"nascimento integrado: {rotulo}")
        tfresh=build("cria arquivo relatorio.md")
        fresh_ok=not base.turno_tem_veto_execucao(tfresh) and base.autoriza_execucao_efetiva(tfresh)
        print(f"fresh turn não herda receipt ......................... {'PASS' if fresh_ok else 'FAIL'}")
        if not fresh_ok and not reds: reds.append("receipt vazou para fresh turn")

        title("FASE 1 — PRIORIDADE DE ARQUIVO: BASELINE READ-ONLY RED / GATE INTEGRADO")
        cand_query={"intent":"FILE_SEARCH","params":{"query":"nao.txt","somente_projeto":False}}
        tsticky=build("procura arquivo nao.txt e nao fecha o opera")
        if not base.turno_tem_veto_execucao(tsticky):
            print("\n🟠 EXIT 1 — precondição sticky da prioridade de arquivo divergiu"); return 1
        real_bypass=bool(_candidato_arquivo_prioritario_autorizado(cand_query,"procura arquivo nao.txt",tsticky,{}))
        integrado_block=not prioridade_arquivo_autorizada(cand_query,"procura arquivo nao.txt",tsticky,{})
        print(f"real FILE_SEARCH read-only sob sticky ................ {'RED reproduzido' if real_bypass else 'NÃO reproduziu'}")
        print(f"integrado FILE_SEARCH sob sticky ..................... {'PASS' if integrado_block else 'FAIL'}")
        if not real_bypass:
            print("\n🟠 EXIT 1 — baseline read-only de arquivo não reproduziu bypass conhecido pela fonte"); return 1
        if not integrado_block and not reds: reds.append("prioridade FILE_SEARCH furou sticky")

        cand_live={"intent":"IOT_STATUS","params":{"alvo":"ventilador"}}
        real_live=bool(_candidato_prioritario_autorizado(cand_live,tsticky))
        integrado_live=not prioridade_autorizada(cand_live,tsticky)
        live_ok=bool(real_live and integrado_live)
        print(f"real read-only geral sob sticky ....................... {'RED reproduzido' if real_live else 'NÃO reproduziu'}")
        print(f"integrado read-only geral sob sticky .................. {'PASS' if integrado_live else 'FAIL'}")
        if not live_ok and not reds: reds.append("prioridade read-only geral furou sticky")

        tq=build("procura arquivo nao.txt")
        rq=detectar_intencao_arquivos("procura arquivo nao.txt",params_cb=lambda **k:k,estado_mental={},normalizar_texto=normalizar_texto)
        q_ok=bool(intent(rq)=="FILE_SEARCH" and params(rq).get("query")=="nao.txt" and prioridade_arquivo_autorizada(rq,"procura arquivo nao.txt",tq,{}))
        print(f"query positiva RAW preserva nao.txt .................. {'PASS' if q_ok else 'FAIL'} {rq}")
        if not q_ok and not reds: reds.append("prioridade positiva de arquivo quebrou")

        te=build("escreve ola dentro do arquivo nao.txt")
        redit=detectar_intencao_arquivos("escreve ola dentro do arquivo nao.txt",params_cb=lambda **k:k,estado_mental={},normalizar_texto=normalizar_texto)
        edit_ok=bool(intent(redit)=="CREATE_FILE" and params(redit).get("alvo")=="nao.txt" and params(redit).get("editar_existente") is True and prioridade_arquivo_autorizada(redit,"escreve ola dentro do arquivo nao.txt",te,{}))
        print(f"edição prioritária RAW preserva nao.txt ............... {'PASS' if edit_ok else 'FAIL'} {redit}")
        if not edit_ok and not reds: reds.append("edição prioritária filename quebrou")

        title("FASE 2 — COORDENADOR INTEGRADO: STICKY ANTES DO RESOLVER, B DEPOIS")
        positivos=[
            ("cria arquivo nao.txt","nao.txt"),
            ("cria arquivo de texto nao.txt","nao.txt"),
            ('cria arquivo chamado "nao.txt"',"nao.txt"),
            ("cria arquivo nao.markdown","nao.markdown"),
            ("cria arquivo nao.txt contendo teste","nao.txt"),
            ("cria arquivo relatorio.md","relatorio.md"),
        ]
        coord_pos=[]
        for texto,alvo in positivos:
            t,ok,rota,dets,rawcalls,execs=rodar_coordenador(texto)
            this=bool(ok and len(execs)==1 and execs[0]["intent"]=="CREATE_FILE" and execs[0]["params"].get("alvo")==alvo and execs[0]["texto"]==texto and not base.turno_tem_veto_execucao(t))
            coord_pos.append(this)
            print(f"{'PASS' if this else 'FAIL'} {texto!r} -> rota={rota!r} det={dets} rawmerge={rawcalls} exec={execs}")
            if not this and not reds: reds.append(f"coordenador positivo perdeu {alvo}")

        killers=[
            "cria arquivo nao txt",
            "cria arquivo nao.exe",
            "cria arquivo nao.txt contendo nao aumenta o volume",
            "cria arquivo nao.markdown e nao fecha o opera",
        ]
        coord_k=[]
        for texto in killers:
            t,ok,rota,dets,rawcalls,execs=rodar_coordenador(texto)
            this=bool(base.turno_tem_veto_execucao(t) and not base.autoriza_execucao_efetiva(t) and not ok and dets==[] and rawcalls==[] and execs==[])
            coord_k.append(this); print(f"{'PASS' if this else 'FAIL'} killer {texto!r} -> det={dets} rawmerge={rawcalls} exec={execs}")
            if not this and not reds: reds.append(f"killer alcançou coordenador: {texto}")

        # Adversarial: top-level auth stale=True não pode superar receipt.
        stale=build("cria arquivo nao.txt")
        stale["veto_execucao_operacional"]=True
        stale["autoriza_execucao"]=True
        stale["acao_explicita"]=True
        stale["atos"]=[{"tipo":"comando","autoriza_execucao":True,"acao_explicita":True,"texto_operacional":"cria arquivo nao txt"}]
        ts,oks,rotas,dets,rawcalls,execs=rodar_coordenador("cria arquivo nao.txt",stale)
        stale_ok=bool(base.turno_tem_veto_execucao(ts) and not base.autoriza_execucao_efetiva(ts) and not oks and dets==[] and rawcalls==[] and execs==[])
        print(f"stale auth=True + receipt -> resolver/detector zero ...... {'PASS' if stale_ok else 'FAIL'} det={dets} raw={rawcalls} exec={execs}")
        if not stale_ok and not reds: reds.append("B/coordenador reviveu auth stale sob receipt")

        title("FASE 3 — A DIRECIONAL + B FILENAME: REVOGAÇÃO CONTINUA ALCANÇÁVEL")
        tcancel=build("nao apaga o arquivo nao.txt")
        cancel_calls=[]; blocos=[]
        c=A.base_ctx(tcancel,pendencia=A.pend_delete())
        c["_executar_intencao_curta_contextual"]=lambda r,t,**k: cancel_calls.append(intent(r)) or True
        tratado_cancel=A.prefluxo_dir(
            c,"nao apaga o arquivo nao.txt",
            fluxo=fluxo_mod,pre=pre_mod,inicio=processar_inicio_fluxo_resposta_ia,
            base=base,combina=_pendencia_combina_com_texto,bloqueios=blocos,
        )
        cancel_ok=bool(base.turno_tem_veto_execucao(tcancel) and tratado_cancel and cancel_calls==["CANCEL_DELETE_ITEM"])
        print(f"sticky + filename + CANCEL -> tratado={tratado_cancel} calls={cancel_calls} receipt={base.turno_tem_veto_execucao(tcancel)} {'PASS' if cancel_ok else 'FAIL'}")
        if not cancel_ok and not reds: reds.append("revogação com filename literal morreu")

        tsim=base.aplicar_veto_canonico({"texto_original":"sim","texto":"sim","modalidade":"recusa","modalidade_geral":"recusa","autoriza_execucao":False,"acao_explicita":False,"segmentos":[]},texto="sim",modalidade="recusa",natureza="integrado_adversarial",motivo="sticky integrado",requer_esclarecimento=False,origem_veto="lab_integrado")
        confirm_calls=[]; c2=A.base_ctx(tsim,pendencia=A.pend_delete()); c2["_executar_intencao_curta_contextual"]=lambda r,t,**k:confirm_calls.append(intent(r)) or True
        tratado_confirm=A.prefluxo_dir(c2,"sim",fluxo=fluxo_mod,pre=pre_mod,inicio=processar_inicio_fluxo_resposta_ia,base=base,combina=_pendencia_combina_com_texto,bloqueios=[])
        confirm_block=bool(not tratado_confirm and confirm_calls==[])
        print(f"sticky + CONFIRM antigo -> calls zero ................... {'PASS' if confirm_block else 'FAIL'}")
        if not confirm_block and not reds: reds.append("confirmação antiga atravessou sticky")

        title("FASE 4 — A NÃO ENGLOBA B: PENDÊNCIA ANTIGA NÃO CONSOME CREATE_FILE NOVO")
        tfile=build("cria arquivo nao.txt")
        pcalls=[]; cp=A.base_ctx(tfile,pendencia=A.pend_delete()); cp["_executar_intencao_curta_contextual"]=lambda r,t,**k:pcalls.append(intent(r)) or True
        tratado_pre=A.prefluxo_dir(cp,"cria arquivo nao.txt",fluxo=fluxo_mod,pre=pre_mod,inicio=processar_inicio_fluxo_resposta_ia,base=base,combina=_pendencia_combina_com_texto,bloqueios=[])
        _,okf,rotaf,detsf,rawf,execsf=rodar_coordenador("cria arquivo nao.txt",tfile) if not tratado_pre else (tfile,False,"",[],[],[])
        novo_cmd_ok=bool(not tratado_pre and pcalls==[] and okf and len(execsf)==1 and execsf[0]["params"].get("alvo")=="nao.txt")
        print(f"pendência delete + novo CREATE_FILE -> pre={tratado_pre} pending_calls={pcalls} exec={execsf} {'PASS' if novo_cmd_ok else 'FAIL'}")
        if not novo_cmd_ok and not reds: reds.append("A consumiu comando B legítimo por pendência antiga")

        title("FASE 5 — VISUAL A CONTINUA MONOTÔNICO COM BUILD B")
        tvn=build("olha esse item"); vcalls=[]; cv=A.base_ctx(tvn); cv["_continuar_visao_jogo_pendente"]=lambda t:vcalls.append(t) or True
        vpos=A.prefluxo_dir(cv,"olha esse item",fluxo=fluxo_mod,pre=pre_mod,inicio=processar_inicio_fluxo_resposta_ia,base=base,combina=_pendencia_combina_com_texto,bloqueios=[])
        visual_pos=bool(vpos and len(vcalls)==1 and not base.turno_tem_veto_execucao(tvn))
        print(f"visual neutro continua vivo ............................. {'PASS' if visual_pos else 'FAIL'} calls={vcalls}")
        if not visual_pos and not reds: reds.append("visual neutro quebrou na integração")

        tvk=build("olha esse item nao fecha o opera"); vkcalls=[]; cvk=A.base_ctx(tvk); cvk["_continuar_visao_jogo_pendente"]=lambda t:vkcalls.append(t) or True
        vneg=A.prefluxo_dir(cvk,"olha esse item nao fecha o opera",fluxo=fluxo_mod,pre=pre_mod,inicio=processar_inicio_fluxo_resposta_ia,base=base,combina=_pendencia_combina_com_texto,bloqueios=[])
        visual_neg=bool(not vneg and vkcalls==[] and base.turno_tem_veto_execucao(tvk))
        print(f"visual sticky continua bloqueado ......................... {'PASS' if visual_neg else 'FAIL'} calls={vkcalls}")
        if not visual_neg and not reds: reds.append("visual sticky atravessou integração")

        title("FASE 6 — RECEIPT > CONTRATO STALE / B NÃO ALTERA EIXO DE AUTORIDADE")
        fake_cmd={"intent":"CREATE_FILE","params":{"alvo":"nao.txt"}}
        filtrado=base.filtrar_comandos_candidato([fake_cmd],turno=stale,plano={"autoriza_execucao":True,"requer_execucao":True},retrato={},filtrar_real=lambda *a,**k:{"comandos":list(a[0]),"autoriza_execucao":True})
        nested_ok=bool(filtrado.get("comandos")==[] and filtrado.get("autoriza_execucao") is False and filtrado.get("veto_execucao_operacional") is True)
        print(f"filtro nested stale -> comandos=[] ....................... {'PASS' if nested_ok else 'FAIL'} {filtrado}")
        if not nested_ok and not reds: reds.append("contrato nested stale sobreviveu ao integrado")

        title("FASE 7 — SIDE-BUG `move` PERMANECE SEPARADO")
        tm=build("move arquivo nao.txt para pasta teste")
        rm=detectar_intencao_arquivos("move arquivo nao.txt para pasta teste",params_cb=lambda **k:k,estado_mental={},normalizar_texto=normalizar_texto)
        move_ok=bool(not base.turno_tem_veto_execucao(tm) and not base.autoriza_execucao_efetiva(tm) and intent(rm)=="FILE_TRANSACTION" and params(rm).get("origem")=="nao.txt")
        print(f"move -> veto={base.turno_tem_veto_execucao(tm)} auth={base.autoriza_execucao_efetiva(tm)} router={rm} {'PASS' if move_ok else 'FAIL'}")
        if not move_ok:
            print("\n🟠 EXIT 1 — side-bug `move` mudou; não atribuir ao integrado")
            return 1

        title("FASE 8 — RESTAURAÇÃO / INVARIANTES FINAIS")
        wiring_restored=bool(
            fluxo_mod.processar_resposta_pendencia_prioritaria is getattr(A,"processar_resposta_pendencia_prioritaria",fluxo_mod.processar_resposta_pendencia_prioritaria)
            if False else True
        )
        # A.prefluxo_dir restaura os seis símbolos; verificamos pelas funções
        # importadas no módulo de fluxo contra o módulo pre_fluxo_contextual.
        nomes=("processar_continuacao_visao_jogo","processar_reparacao_conversacional","processar_resposta_pendencia_prioritaria","processar_feedback_pendente","processar_confirmacao_musical_pendente","processar_pergunta_curta_contextual")
        wiring_restored=all(getattr(fluxo_mod,n,None) is getattr(pre_mod,n,None) for n in nomes)
        print(f"monkeypatches A restaurados .............................. {'PASS' if wiring_restored else 'FAIL'}")
        if not wiring_restored:
            print("\n🟠 EXIT 1 — wiring do pré-fluxo não foi restaurado"); return 1

        inv={
            "nascimento A+B":all(nascimento),
            "fresh turn sem vazamento":fresh_ok,
            "wiring prioridade->prefluxo OP/RAW":all((ordem_real,raw_arquivo_prioritario,op_raw_pre,coord_dual)),
            "priority file sticky bloqueado":integrado_block,
            "priority live geral sticky bloqueado":live_ok,
            "priority query positiva":q_ok,
            "priority edit positiva":edit_ok,
            "coordenador filenames":all(coord_pos),
            "killers antes do coordenador":all(coord_k),
            "stale auth bloqueado antes detector":stale_ok,
            "revogação filename sob sticky":cancel_ok,
            "confirm antigo sticky bloqueado":confirm_block,
            "novo CREATE_FILE vence pendência antiga":novo_cmd_ok,
            "visual neutro":visual_pos,
            "visual sticky":visual_neg,
            "nested stale":nested_ok,
            "side-bug move separado":move_ok,
            "wiring restaurado":wiring_restored,
        }
        for k,v in inv.items(): print(f"{k:<58} {'PASS' if v else 'FAIL'}")
        if reds:
            print("\n🔴 EXIT 2 — CANDIDATO FINAL V2.5.1 INTEGRADO FALSIFICADO")
            print("FIRST RED:",reds[0])
            for x in reds: print("❌",x)
            return 2
        if not all(inv.values()):
            print("\n🔴 EXIT 2 — INVARIANTE FINAL FALHOU")
            return 2
        print("\n🟢 EXIT 0 — CANDIDATO FINAL LAB V2.5.1 INTEGRADO GREEN")
        print("A e B coexistiram: revogação permaneceu possível, sticky continuou soberano e RAW só restaurou literalidade em filename autorizado.")
        print("Produção continua intacta. GREEN integrado ainda exige segunda revisão integral antes de patch real.")
        return 0
    finally:
        coord_mod.executar_intencao=old_executor

if __name__=="__main__":
    raise SystemExit(main())
