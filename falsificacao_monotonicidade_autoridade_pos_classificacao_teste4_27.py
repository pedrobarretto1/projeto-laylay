#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FALSIFICAÇÃO 4.27 — MONOTONICIDADE DA AUTORIDADE PÓS-CLASSIFICAÇÃO
=================================================================

Pergunta
--------
Se uma restrição operacional interna já colocou o turno em fail-closed,
alguma camada posterior consegue elevar a autoridade novamente?

Este teste NÃO implementa o patch final.
Ele faz duas coisas distintas e explicitamente separadas:

1) usa um veto P0 REAL já existente (`e nao fecha`) para medir o contrato atual;
2) injeta somente a SAÍDA desejada do V2.4 em uma forma bare/STT que a P0 atual
   não cobre, para falsificar a hipótese "basta corrigir modalidade_turno.py".

A intervenção V2.4 não é código de produção nem candidato completo. Ela apenas
representa o estado que qualquer correção conservadora teria de produzir:
`autoriza_execucao=False`, `acao_explicita=False`, `texto_operacional=''` e
natureza de cancelamento/restrição.

O teste procura a PRIMEIRA camada posterior alcançável que destrói esse veto.

Cobertura
---------
- classificador/P0 real;
- repetição real + resolvedor real;
- elipse espacial real;
- detector visual real;
- `aplicar_pedido_visual_ao_turno()` real;
- barreira prioritária real;
- árbitro real;
- filtro de comandos da LLM real;
- pré-fluxo determinístico real;
- orquestrador cooperativo real com executor final trocado por RECORDER.

Nenhum efeito físico é executado.
Produção não é modificada.

EXIT
----
2 = hipótese "patch só na modalidade" falsificada: após intervenção fail-closed
    uma camada posterior reautoriza e a rota cooperativa alcança o recorder.
0 = nenhuma reautorização alcançável foi reproduzida.
1 = lock, wiring, controle ou premissa do harness inválida.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


HEAD = "a4741bc57bc55a50ef2861dbaef09ab36397ff63"
BLOBS = {
    "mente_laylay/cognicao/modalidade_turno.py":
        "80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
    "mente_laylay/cognicao/orquestrador_turno_runtime.py":
        "9ea071daf1dbdc40e9677f5d65515e0ee4ec4c99",
    "mente_laylay/cognicao/intencao_visual_jogo.py":
        "c2ffb53b3aa218a6430369abca84240d2b11aafa",
    "mente_laylay/cognicao/arbitro_turno.py":
        "7756a15a8538291a118f8b4f3ab900157fa10927",
    "mente_laylay/cognicao/decisao_turno.py":
        "09b0dc8536eeef8ccd32d8a30165b6a9c32b71d9",
    "mente_laylay/memoria_mental/compatibilidade_contexto.py":
        "768944f808002d8c24f697c0b2769a31d536eb3e",
    "mente_laylay/autonomia/pre_fluxo_contextual.py":
        "8b75bed91862b85d777c97a91c4aaa141e9900d8",
    "mente_laylay/autonomia/comandos_imediatos.py":
        "27706613cb505219479664a664db038cac78c037",
    "mente_laylay/autonomia/orquestracao_cooperativa.py":
        "4150f749a9a0e1ec286fb600d95f33d057b356e0",
    "mente_laylay/autonomia/governanca_cooperacao.py":
        "97fb1d1b5cf14d347e031062a4752c0915aa4188",
    "mente_laylay/autonomia/porteiro_acoes.py":
        "19b5eaa9ddafd483eab92d46e92cca30813adbb6",
    "mente_laylay/autonomia/quadro_cooperacao.py":
        "3ba4f6a51c42138c794f8dbe4d594e5abf5b55e8",
}


REAL_P0 = "olha esse item e nao fecha o opera"
REAL_P0_NUNCA = "olha esse item e nunca fecha o opera"
BARE_V24 = "olha esse item nao fecha o opera"
ROOT_229 = "fecha o opera nao a microsoft store"
VISUAL_POS = "olha esse item"


def git(repo: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def repo_root() -> Path:
    for start in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (start, *start.parents):
            if (p / ".git").exists() and (p / "laylay.py").exists():
                return p
    raise RuntimeError("execute dentro do repositório Laylay")


def source(repo: Path, file: str) -> str:
    return git(repo, "show", f"HEAD:{file}")


def idx(src: str, token: str) -> int:
    try:
        return src.index(token)
    except ValueError:
        return -1


def resumo_turno(t: dict[str, Any]) -> str:
    return (
        f"modalidade={t.get('modalidade')} geral={t.get('modalidade_geral')} "
        f"auth={bool(t.get('autoriza_execucao'))} "
        f"acao={bool(t.get('acao_explicita'))} "
        f"natureza={t.get('natureza_acao')} "
        f"op={t.get('texto_operacional')!r} "
        f"motivo={t.get('motivo_decisao') or t.get('motivo')!r}"
    )


def intervir_fail_closed_v24(turno: dict[str, Any], texto: str) -> dict[str, Any]:
    """Intervenção causal mínima: representa a SAÍDA exigida do V2.4.

    Não é implementação candidata. Não tenta detectar nada.
    """
    novo = dict(turno or {})
    novo.update(
        modalidade="recusa",
        modalidade_geral="recusa",
        ato_principal="recusa",
        atos=["recusa"],
        segmentos=[{
            "indice": 0,
            "texto": str(texto or "")[:300],
            "modalidade": "recusa",
            "confianca": 0.99,
            "motivo": "INTERVENCAO_V24: restricao operacional interna",
            "autoriza_execucao": False,
            "acao_explicita": False,
            "requer_esclarecimento": False,
            "natureza_acao": "cancelamento",
        }],
        texto_operacional="",
        texto_conversacional=str(texto or "")[:500],
        autoriza_execucao=False,
        acao_explicita=False,
        requer_esclarecimento=False,
        natureza_acao="cancelamento",
        motivo="INTERVENCAO_V24: restricao operacional interna",
        motivo_decisao="INTERVENCAO_V24: restricao operacional interna",
    )
    return novo


def main() -> int:
    print("FALSIFICAÇÃO V2.4 — MONOTONICIDADE / TESTE 4.27")
    print("=" * 76)
    falhas_premissa: list[str] = []

    try:
        repo = repo_root()
    except Exception as e:
        print(f"❌ EXIT 1 — {e}")
        return 1

    print("\n## GUARDS / LOCKS")
    print("-" * 76)
    head = git(repo, "rev-parse", "HEAD")
    print(f"HEAD {'PASS' if head == HEAD else 'FAIL'} {head}")
    if head != HEAD:
        falhas_premissa.append("HEAD mudou")

    for file, expected in BLOBS.items():
        actual = git(repo, "rev-parse", f"HEAD:{file}")
        ok = actual == expected
        print(f"{file:<64} {'PASS' if ok else 'FAIL'} {actual}")
        if not ok:
            falhas_premissa.append(f"blob mudou: {file}")

    dirty = git(repo, "status", "--porcelain", "--", *BLOBS.keys(), check=False)
    print(f"worktree causal {'PASS' if not dirty.strip() else 'FAIL'}")
    if dirty.strip():
        print(dirty)
        falhas_premissa.append("worktree causal suja")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — LOCK/PREMISSA INVÁLIDA")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    print("\n## WIRING PÓS-CLASSIFICAÇÃO — FONTE TRAVADA")
    print("-" * 76)
    src_turno = source(repo, "mente_laylay/cognicao/orquestrador_turno_runtime.py")
    src_imed = source(repo, "mente_laylay/autonomia/comandos_imediatos.py")
    p_cls = idx(src_turno, "turno = ns['_classificar_modalidade_turno_mente']")
    p_elipse = idx(src_turno, "turno = aplicar_elipse_espacial_autorizada_ao_turno(")
    p_rep = idx(src_turno, "turno = aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)")
    p_det_vis = idx(src_turno, "pedido_visao_jogo = detectar_pedido_visao_jogo(texto_cognitivo, jogo_contexto)")
    p_apply_vis = idx(src_turno, "turno = aplicar_pedido_visual_ao_turno(turno, pedido_visao_jogo)")
    ordem = (
        p_cls >= 0
        and p_elipse > p_cls
        and p_rep > p_elipse
        and p_det_vis > p_rep
        and p_apply_vis > p_det_vis
    )
    print(f"classificação -> elipse -> repetição -> detectar visão -> aplicar visão: {'PASS' if ordem else 'FAIL'}")
    if not ordem:
        falhas_premissa.append("ordem pós-classificação mudou")

    p_bar = idx(src_imed, "if bloqueia_execucao_operacional_prioritaria(")
    p_coop = idx(src_imed, "orquestrador_cooperativo.processar(texto)")
    ordem2 = p_bar >= 0 and p_coop > p_bar
    print(f"barreira prioritária -> cooperação: {'PASS' if ordem2 else 'FAIL'}")
    if not ordem2:
        falhas_premissa.append("ordem barreira/cooperacao mudou")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — WIRING/PREMISSA INVÁLIDA")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    try:
        from mente_laylay.cognicao.modalidade_turno import (
            bloqueia_execucao_operacional_prioritaria,
            classificar_modalidade_turno,
        )
        from mente_laylay.autonomia.porteiro_acoes import (
            autorizar_acao_pratica,
            normalizar_texto,
            texto_tem_comando_explicito,
        )
        from mente_laylay.cognicao.intencao_visual_jogo import (
            aplicar_pedido_visual_ao_turno,
            detectar_pedido_visao_jogo,
        )
        from mente_laylay.cognicao.orquestrador_turno_runtime import (
            aplicar_elipse_espacial_autorizada_ao_turno,
            aplicar_repeticao_operacional_ao_turno,
        )
        from mente_laylay.memoria_mental.compatibilidade_contexto import (
            resolver_repeticao_ultima_acao,
        )
        from mente_laylay.cognicao.arbitro_turno import (
            CandidatoDecisao,
            arbitrar_turno,
        )
        from mente_laylay.cognicao.decisao_turno import (
            filtrar_comandos_pelo_turno,
        )
        from mente_laylay.autonomia.pre_fluxo_contextual import (
            processar_comando_deterministico_precoce,
        )
        from mente_laylay.autonomia.quadro_cooperacao import (
            QuadroCooperacaoRuntime,
        )
        from mente_laylay.autonomia.orquestracao_cooperativa import (
            OrquestradorCooperativoRuntime,
        )
    except Exception as e:
        print(f"\n❌ EXIT 1 — IMPORT REAL FALHOU: {type(e).__name__}: {e}")
        return 1

    def classificar(texto: str) -> dict[str, Any]:
        return classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )

    contexto_jogo = {
        "ativo": True,
        "titulo": "Minecraft",
        "processo": "javaw.exe",
        "analise_visual_recente": False,
    }

    def detectar_visual(texto: str):
        return detectar_pedido_visao_jogo(texto, contexto_jogo)

    print("\n## FASE 0 — CONTROLES: NEUTRO, P0 REAL E ROOT ORIGINAL")
    print("-" * 76)
    t_neutro = classificar(VISUAL_POS)
    t_p0 = classificar(REAL_P0)
    t_p0_nunca = classificar(REAL_P0_NUNCA)
    t_bare_base = classificar(BARE_V24)
    t_root = classificar(ROOT_229)
    for nome, texto, turno in (
        ("NEUTRO_VISUAL", VISUAL_POS, t_neutro),
        ("P0_REAL", REAL_P0, t_p0),
        ("P0_NUNCA", REAL_P0_NUNCA, t_p0_nunca),
        ("BARE_BASE", BARE_V24, t_bare_base),
        ("ROOT_229", ROOT_229, t_root),
    ):
        print(f"{nome:<14} {texto!r}")
        print(f"  {resumo_turno(turno)}")

    p0_ok = (
        not bool(t_p0.get("autoriza_execucao"))
        and str(t_p0.get("modalidade") or "") == "recusa"
        and str(t_p0.get("natureza_acao") or "") == "cancelamento"
        and not bool(t_p0_nunca.get("autoriza_execucao"))
    )
    neutro_ok = not bool(t_neutro.get("autoriza_execucao"))
    if not p0_ok:
        falhas_premissa.append("P0 real não produziu veto esperado")
    if not neutro_ok:
        falhas_premissa.append("controle visual neutro já veio autorizado pelo classificador")

    pedido_root = detectar_visual(ROOT_229)
    print(f"detector visual no ROOT_229 -> {pedido_root!r}")
    if pedido_root is not None:
        falhas_premissa.append("root CLOSE original virou pedido visual; controle de isolamento inválido")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — CONTROLES INVÁLIDOS")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    print("\n## FASE 1 — PRODUTORES ANTERIORES À VISÃO NO BARE V2.4")
    print("-" * 76)
    veto_bare = intervir_fail_closed_v24(t_bare_base, BARE_V24)
    print("intervenção fail-closed:")
    print(f"  {resumo_turno(veto_bare)}")

    estado_rep = {
        "ultima_acao_reexecutavel": True,
        "ultima_acao_intent": "CLOSE_APP",
        "ultima_acao_params": {"nome_app": "opera"},
    }
    repeticao_bare = resolver_repeticao_ultima_acao(
        BARE_V24,
        estado_rep,
        normalizar_texto,
    )
    print(f"resolver_repeticao_ultima_acao(BARE) -> {repeticao_bare!r}")
    if repeticao_bare is not None:
        falhas_premissa.append("bare visual foi confundido com repetição")

    pos_rep = aplicar_repeticao_operacional_ao_turno(veto_bare, repeticao_bare)
    print(f"após repetição -> auth={bool(pos_rep.get('autoriza_execucao'))}")
    if bool(pos_rep.get("autoriza_execucao")):
        falhas_premissa.append("repetição reautorizou bare sem contrato de repetição")

    pos_elipse = aplicar_elipse_espacial_autorizada_ao_turno(
        BARE_V24,
        turno=pos_rep,
        pendencia_turno={},
    )
    print(f"após elipse -> auth={bool(pos_elipse.get('autoriza_execucao'))}")
    if bool(pos_elipse.get("autoriza_execucao")):
        falhas_premissa.append("elipse espacial reautorizou texto não espacial")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — PRODUTOR ANTERIOR INESPERADO")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    print("\n## FASE 2 — VISÃO: NEUTRO PODE SUBIR; VETO NÃO DEVERIA")
    print("-" * 76)
    pedido_neutro = detectar_visual(VISUAL_POS)
    pedido_p0 = detectar_visual(REAL_P0)
    pedido_bare = detectar_visual(BARE_V24)
    for nome, pedido in (
        ("NEUTRO", pedido_neutro),
        ("P0_REAL", pedido_p0),
        ("BARE_V24", pedido_bare),
    ):
        print(f"{nome:<10} pedido_visual={pedido!r}")
        if not (
            isinstance(pedido, dict)
            and str(pedido.get("intent") or "").upper() == "GAME_VISION"
            and str((pedido.get("params") or {}).get("tipo") or "") == "avaliacao_item"
        ):
            falhas_premissa.append(f"detector visual não reconheceu {nome}")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — DETECTOR VISUAL/PREMISSA INVÁLIDA")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    pos_neutro = aplicar_pedido_visual_ao_turno(t_neutro, pedido_neutro)
    pos_p0 = aplicar_pedido_visual_ao_turno(t_p0, pedido_p0)
    pos_bare = aplicar_pedido_visual_ao_turno(pos_elipse, pedido_bare)

    print("NEUTRO antes -> depois")
    print(f"  {resumo_turno(t_neutro)}")
    print(f"  {resumo_turno(pos_neutro)}")
    print("P0 REAL antes -> depois")
    print(f"  {resumo_turno(t_p0)}")
    print(f"  {resumo_turno(pos_p0)}")
    print("BARE V2.4 antes -> depois")
    print(f"  {resumo_turno(pos_elipse)}")
    print(f"  {resumo_turno(pos_bare)}")

    controle_neutro_sobe = bool(pos_neutro.get("autoriza_execucao"))
    p0_reautorizado = bool(pos_p0.get("autoriza_execucao"))
    bare_reautorizado = bool(pos_bare.get("autoriza_execucao"))
    if not controle_neutro_sobe:
        falhas_premissa.append("controle neutro não foi autorizado pela visão")

    print(f"controle neutro autorizado pela especialização ... {'PASS' if controle_neutro_sobe else 'FAIL'}")
    print(f"P0 real teve veto apagado pela visão ............. {'RED' if p0_reautorizado else 'PASS'}")
    print(f"intervenção V2.4 teve veto apagado pela visão .... {'RED' if bare_reautorizado else 'PASS'}")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — CONTROLE POSITIVO QUEBROU")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    print("\n## FASE 3 — BARREIRA PRIORITÁRIA: P0 REAL × BARE V2.4")
    print("-" * 76)
    bloqueia_p0 = bloqueia_execucao_operacional_prioritaria(
        REAL_P0,
        classificacao=pos_p0,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    bloqueia_bare = bloqueia_execucao_operacional_prioritaria(
        BARE_V24,
        classificacao=pos_bare,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    print(f"P0 REAL após reautorização -> bloqueia={bloqueia_p0}")
    print(f"BARE V2.4 após reautorização -> bloqueia={bloqueia_bare}")
    print("interpretação:")
    print("  P0 real ainda pode ser salvo pela reanálise lexical da barreira.")
    print("  bare/STT depende da autoridade congelada; se visão a elevou, a P0 atual não recompõe o veto.")

    if not bloqueia_p0:
        falhas_premissa.append("barreira não preservou P0 real; premissa do contraste mudou")

    print("\n## FASE 4 — CONSUMIDORES QUE RESPEITAM O VETO DIRETO")
    print("-" * 76)
    cand = CandidatoDecisao(
        tipo="comando_explicito",
        valor={"intent": "CLOSE_APP", "params": {"nome_app": "opera"}},
        origem="controle_4_27",
        confianca=0.99,
        evidencia=("controle mutante",),
    )
    arb = arbitrar_turno(
        BARE_V24,
        [cand],
        turno=veto_bare,
        retrato={},
    )
    arb_bloqueou = not isinstance(arb.get("decisao"), dict)
    print(f"árbitro com veto direto -> decisao={arb.get('decisao')!r} | bloqueou={arb_bloqueou}")

    plano = {
        "requer_execucao": True,
        "decisao_turno": {"permite_acao": False, "proprietario": "conversa"},
    }
    filtro = filtrar_comandos_pelo_turno(
        [{"intent": "CLOSE_APP", "params": {"nome_app": "opera"}}],
        turno=veto_bare,
        plano=plano,
        retrato={},
    )
    llm_bloqueou = not list(filtro.get("comandos") or [])
    print(f"filtro LLM com veto -> {filtro!r}")

    chamadas_det: list[Any] = []

    def det_recorder(*args: Any, **kwargs: Any) -> bool:
        chamadas_det.append((args, kwargs))
        return True

    ctx_pre = {
        "mente_integrada_estado": {"turno_atual": dict(veto_bare)},
        "processar_comando_deterministico": det_recorder,
    }
    pre_ok, pre_nome = processar_comando_deterministico_precoce(
        ctx_pre,
        BARE_V24,
        origem="teste_4_27",
    )
    pre_bloqueou = (not pre_ok) and not chamadas_det
    print(f"pré-fluxo determinístico -> ok={pre_ok} nome={pre_nome!r} chamadas={chamadas_det!r}")

    if not arb_bloqueou:
        falhas_premissa.append("árbitro não respeitou veto direto")
    if not llm_bloqueou:
        falhas_premissa.append("filtro LLM não respeitou veto direto")
    if not pre_bloqueou:
        falhas_premissa.append("pré-fluxo determinístico não respeitou veto direto")

    if falhas_premissa:
        print("\n🟠 EXIT 1 — CONTROLE DE CONSUMIDOR INVÁLIDO")
        for x in falhas_premissa:
            print(f"❌ {x}")
        return 1

    print("\n## FASE 5 — CADEIA BARE V2.4 -> VISÃO -> BARREIRA -> COOPERAÇÃO")
    print("-" * 76)
    chamadas_exec: list[tuple[dict[str, Any], str]] = []
    auth_trace: list[bool] = []
    falas: list[str] = []

    def exec_recorder(resultado: dict[str, Any], texto_original: str) -> bool:
        chamadas_exec.append((dict(resultado or {}), str(texto_original or "")))
        return True

    def porteiro_trace(
        acao: str,
        texto: str = "",
        contexto=None,
        *,
        confirmado: bool = False,
        origem: str = "",
    ):
        auth_trace.append(bool(confirmado))
        return autorizar_acao_pratica(
            acao,
            texto,
            contexto,
            confirmado=confirmado,
            origem=origem,
        )

    quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda *_: None)
    orq = OrquestradorCooperativoRuntime(
        quadro=quadro,
        clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "",
        executar_intencao=exec_recorder,
        resolver_caminho=lambda p: str(p or ""),
        falar=lambda fala, *_args: falas.append(str(fala)),
        detectar_visao_jogo=detectar_visual,
        estado_getter=lambda: {},
        autorizar_acao=porteiro_trace,
        log=lambda *_: None,
    )

    tratado_coop = False
    if not bloqueia_bare:
        tratado_coop = bool(orq.processar(BARE_V24))
    game_calls = [
        x for x in chamadas_exec
        if str((x[0] or {}).get("intent") or "").upper() == "GAME_VISION"
    ]
    coop_reach = bool(tratado_coop and game_calls)
    print(f"barreira bare bloqueia? ............ {bloqueia_bare}")
    print(f"coop processar ...................... {tratado_coop}")
    print(f"auth_trace confirmado ............... {auth_trace!r}")
    print(f"recorder ............................ {chamadas_exec!r}")
    print(f"falas ............................... {falas!r}")
    print(f"GAME_VISION alcançou recorder ....... {coop_reach}")

    print("\n## RESUMO CAUSAL")
    print("-" * 76)
    print(f"repetição alcançável no bare ............ {'NÃO' if repeticao_bare is None else 'SIM'}")
    print(f"elipse reautorizou bare .................. {'SIM' if bool(pos_elipse.get('autoriza_execucao')) else 'NÃO'}")
    print(f"visão reautorizou veto P0 real ........... {'SIM' if p0_reautorizado else 'NÃO'}")
    print(f"visão reautorizou intervenção V2.4 ....... {'SIM' if bare_reautorizado else 'NÃO'}")
    print(f"barreira salvou P0 real .................. {'SIM' if bloqueia_p0 else 'NÃO'}")
    print(f"barreira salvou bare V2.4 ................ {'SIM' if bloqueia_bare else 'NÃO'}")
    print(f"árbitro respeitou veto direto ............. {'SIM' if arb_bloqueou else 'NÃO'}")
    print(f"filtro LLM respeitou veto direto .......... {'SIM' if llm_bloqueou else 'NÃO'}")
    print(f"pré-fluxo respeitou veto direto ........... {'SIM' if pre_bloqueou else 'NÃO'}")
    print(f"cooperação alcançou recorder .............. {'SIM' if coop_reach else 'NÃO'}")

    # A falsificação principal exige a cadeia inteira do candidato conceitual:
    # veto -> primeira reautorização visual -> barreira não recompõe -> coop chega
    # ao recorder. O P0 real serve como controle de contraste e não recebe crédito
    # de reachability se a barreira o bloquear.
    falsificou_patch_so_modalidade = bool(
        bare_reautorizado
        and not bloqueia_bare
        and coop_reach
    )

    if falsificou_patch_so_modalidade:
        print("\n🔴 EXIT 2 — HIPÓTESE 'PATCH SÓ NA MODALIDADE' FALSIFICADA")
        print("FIRST REAUTH REACHABLE no cenário bare/V2.4 = aplicar_pedido_visual_ao_turno().")
        print("A barreira histórica recompõe P0 real, mas não conhece o novo veto bare/STT depois que a visão o apagou.")
        print("A cooperação então alcança GAME_VISION no recorder. Nenhum efeito físico foi executado.")
        print("Conclusão arquitetural: o fail-closed precisa sobreviver como veto monotônico ao restante do turno.")
        return 2

    if p0_reautorizado:
        print("\n🟡 EXIT 0 — CONTRATO VISUAL AINDA CORROMPE P0, MAS CADEIA BARE NÃO FECHOU")
        print("Não aprovar patch; estudar a primeira fronteira que impediu a reachability.")
        return 0

    print("\n🟢 EXIT 0 — REAUTORIZAÇÃO PÓS-VETO NÃO REPRODUZIDA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
