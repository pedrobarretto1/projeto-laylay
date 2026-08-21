#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDIDATO FINAL LAB V2.5 — VETO MONOTÔNICO / TURNO 229
======================================================

NÃO ALTERA PRODUÇÃO.

Este arquivo é um laboratório do menor contrato final sustentado pelos REDs
4.24, 4.25, 4.26 REV2, 4.27 e 4.28 REV2.

Objetivo
--------
Representar explicitamente a diferença entre:

    SEM AUTORIZAÇÃO / NEUTRO

versus

    VETO OPERACIONAL SOBERANO

com um receipt sticky:

    veto_execucao_operacional = True

Regras do candidato
--------------------
1. NEUTRO -> AUTORIZADO continua permitido para especializações legítimas.
2. AUTORIZADO -> VETADO continua permitido por proteção soberana.
3. VETADO -> AUTORIZADO é proibido no mesmo turno.
4. VETADO -> continuidade operacional anterior é proibido no mesmo turno.
5. `autoriza_execucao=False` sozinho NÃO implica veto.
6. O veto é representado em todo o contrato, não apenas no topo.
7. O executor global NÃO é alterado; serviços/background não herdam veto de
   conversa sem receipt de ownership.

O LAB também inclui o conserto conservador da raiz PONTUADA separada do 229:
plain `, não ALVO` / `mas não ALVO` deixa de ser reinterpretado como troca de
alvo. Correções explicitamente positivas, como `não, melhor Prime Video`,
continuam válidas.

Arquitetura de produção projetada pelo LAB
------------------------------------------
A) contratos_turno.py
   - `veto_execucao_operacional` como campo opcional de leitura/plano;
   - helpers puros `turno_tem_veto_execucao` e `autoriza_execucao_efetiva`;
   - helper canônico que reescreve topo + segmentos/atos em fail-closed.

B) gramatica_operacional.py
   - detector puro de negação standalone interna, sem lista privada de verbos;
   - exceção lexical estreita apenas para `nao.<ext>` / `não.<ext>` sob moldura
     explícita de arquivo/documento.

C) modalidade_turno.py
   - P0 histórica marca receipt apenas nas naturezas realmente soberanas;
   - P0 `informativa_sobre_acao` permanece auth=False NÃO-sticky para consultas
     read-only explícitas como "O Opera continua aberto?";
   - V2.4 bare/STT só participa quando baseline já autorizou;
   - barreira prioritária trata receipt como soberano e recompõe o predicado
     bare/STT no texto operacional efetivo antes de confiar em auth.

D) revisao_turno.py / orquestrador_turno_runtime.py
   - plain `não ALVO` não é prova suficiente de substituição de alvo;
   - revisão ambígua/cancelada usa o mesmo fail-closed canônico;
   - repetição e elipse não elevam turno vetado.

E) intencao_visual_jogo.py
   - pedido visual não eleva turno vetado.

F) plano_turno.py / decisao_turno.py
   - autoridade efetiva = `autoriza_execucao and not veto`;
   - atos não pedem execução quando o receipt é soberano;
   - filtro de comandos continua fail-closed.

G) fluxo_resposta_ia.py / pre_fluxo_contextual.py
   - o receipt não mata o pré-fluxo inteiro;
   - apenas etapas capazes de consumir/confirmar uma continuidade operacional
     anterior são omitidas quando VETADO;
   - comentário/opinião conversacional e proteção de playlist continuam vivos;
   - `nao` curto sem receipt continua podendo cancelar uma pendência legítima;
   - a fala vetada segue para resposta principal se nenhuma etapa segura a tratar.

H) comandos_imediatos.py
   - consultas live/read-only não furam veto antes da barreira;
   - resposta estática de capacidade pode continuar sendo emitida;
   - depois dessa exceção conversacional segura, veto encerra a fase prioritária.

I) coordenador_intencao.py / arbitro_turno.py
   - o resolvedor canônico consulta veto antes de agenda, continuidade, detector e IA-first;
   - o árbitro rejeita todo candidato operacional sob receipt, inclusive read-only;
   - isto impede que exceções de leitura convertam VETADO em uma decisão executável.

Escopo do LAB
-------------
- usa classificadores, produtores, planejador, decisão, barreira, pre-fluxo e
  cooperação REAIS como componentes sob teste;
- as mudanças propostas existem apenas como wrappers locais deste arquivo;
- nenhum efeito físico é executado;
- nenhuma captura de tela é feita;
- produção permanece intacta.

EXIT
----
0 = candidato LAB ficou GREEN em toda a matriz.
1 = lock, premissa ou controle positivo inválido.
2 = falsificação do candidato: alguma invariável falhou.

GREEN do LAB NÃO é aprovação para patch de produção. Segunda revisão integral
continua obrigatória.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


HEAD = "a4741bc57bc55a50ef2861dbaef09ab36397ff63"
BLOBS = {
    "laylay.py": "7f89a8e4944f7df83de0835fbd3142f6cd127c60",
    "mente_laylay/cognicao/contratos_turno.py":
        "21aea640ffa188abfe5432888a6d3608d2778e35",
    "mente_laylay/cognicao/gramatica_operacional.py":
        "3521978dca1f7b73b1c16aa1ff1e0788d41c64a9",
    "mente_laylay/cognicao/modalidade_turno.py":
        "80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
    "mente_laylay/cognicao/revisao_turno.py":
        "222d92624899ed55cc74628869b376075b7e6a1c",
    "mente_laylay/cognicao/orquestrador_turno_runtime.py":
        "9ea071daf1dbdc40e9677f5d65515e0ee4ec4c99",
    "mente_laylay/cognicao/intencao_visual_jogo.py":
        "c2ffb53b3aa218a6430369abca84240d2b11aafa",
    "mente_laylay/cognicao/plano_turno.py":
        "a5aa5294ca813f4f78368ff6d4ca6f1ee8874113",
    "mente_laylay/cognicao/decisao_turno.py":
        "09b0dc8536eeef8ccd32d8a30165b6a9c32b71d9",
    "mente_laylay/cognicao/arbitro_turno.py":
        "7756a15a8538291a118f8b4f3ab900157fa10927",
    "mente_laylay/memoria_mental/compatibilidade_contexto.py":
        "768944f808002d8c24f697c0b2769a31d536eb3e",
    "mente_laylay/autonomia/fluxo_resposta_ia.py":
        "604cf86905aa6c3d55fdf4b574a9b6c934c00725",
    "mente_laylay/autonomia/pre_fluxo_contextual.py":
        "8b75bed91862b85d777c97a91c4aaa141e9900d8",
    "mente_laylay/autonomia/pre_fluxo_musical.py":
        "7b3f7111f3c844c1b9676ad4f3101786ce500947",
    "mente_laylay/autonomia/comandos_imediatos.py":
        "27706613cb505219479664a664db038cac78c037",
    "mente_laylay/autonomia/coordenador_intencao.py":
        "de8a893cd60ab44ad9bc3437d01db15ba54fb367",
    "mente_laylay/especialistas/capacidades.py":
        "bfc031833b46d650fb6cc6cf4e07d44150c26710",
    "mente_laylay/autonomia/porteiro_acoes.py":
        "19b5eaa9ddafd483eab92d46e92cca30813adbb6",
    "mente_laylay/autonomia/orquestracao_cooperativa.py":
        "4150f749a9a0e1ec286fb600d95f33d057b356e0",
    "mente_laylay/autonomia/governanca_cooperacao.py":
        "97fb1d1b5cf14d347e031062a4752c0915aa4188",
    "mente_laylay/autonomia/quadro_cooperacao.py":
        "3ba4f6a51c42138c794f8dbe4d594e5abf5b55e8",
}


# ============================================================================
# INFRA / GUARDS
# ============================================================================

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


def localizar_repo() -> Path:
    vistos: set[Path] = set()
    for inicio in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (inicio, *inicio.parents):
            if p in vistos:
                continue
            vistos.add(p)
            if (p / ".git").exists() and (p / "laylay.py").exists():
                return p
    raise RuntimeError("execute este LAB dentro do repositório Laylay")


def literal_global(path: Path, nomes: Sequence[str]) -> Any:
    try:
        arvore = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    wanted = set(nomes)
    for node in arvore.body:
        if isinstance(node, ast.Assign):
            value = node.value
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            targets = [node.target]
        else:
            continue
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    return ast.literal_eval(value)
                except Exception:
                    return None
    return None


def titulo(t: str) -> None:
    print("\n" + t)
    print("=" * 88)


def b(v: Any) -> str:
    return "SIM" if bool(v) else "NÃO"


# ============================================================================
# CANDIDATO PURO — RECEIPT DE VETO
# ============================================================================

NEG_RE = re.compile(
    r"(?<![\wÀ-ÿ])(?P<neg>nao|não|nunca|jamais)(?![\wÀ-ÿ])",
    flags=re.IGNORECASE,
)
FILE_ATOM_RE = re.compile(
    r"(?P<atom>(?:nao|não)\.(?:txt|md|log|csv|json|yaml|yml|py|js|ts|html|css))"
    r"(?=$|[\s,;:!?\"'])",
    flags=re.IGNORECASE,
)
REVISAO_NAO_RE = re.compile(
    r"(?P<sep>\.\.\.|…|;|,\s*|\bmas\s+)\s*"
    r"(?P<marker>não|nao)\b(?P<resto>.*)$",
    flags=re.IGNORECASE,
)


def norm_sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    return "".join(ch for ch in base if not unicodedata.combining(ch))


def turno_tem_veto_execucao(turno: Mapping[str, Any] | None) -> bool:
    return bool(dict(turno or {}).get("veto_execucao_operacional"))


def autoriza_execucao_efetiva(turno: Mapping[str, Any] | None) -> bool:
    t = dict(turno or {})
    return bool(t.get("autoriza_execucao") and not turno_tem_veto_execucao(t))


def _marcador_em_atomo_arquivo(
    raw: str, start: int, end: int,
) -> tuple[bool, str]:
    texto = str(raw or "")
    if norm_sem_acento(texto[start:end]) != "nao":
        return False, ""
    m = FILE_ATOM_RE.match(texto, start)
    if not m:
        return False, ""
    prefixo = texto[:start]
    if not re.search(
        r"\b(?:arquivo|documento)\b"
        r"(?:\s+(?:chamado|chamada|de\s+nome|com\s+nome))?\s*$",
        prefixo,
        flags=re.IGNORECASE,
    ):
        return False, ""
    return True, str(m.group("atom") or "")


def analisar_negacao_interna_conservadora(raw: str) -> dict[str, Any]:
    """Predicado puro do V2.5; detector não concede autoridade."""
    texto = re.sub(r"\s+", " ", str(raw or "")).strip()
    marcadores: list[dict[str, Any]] = []
    for m in NEG_RE.finditer(texto):
        prefixo = texto[:m.start("neg")].strip()
        cauda = texto[m.end("neg"):].strip()
        atomo, valor = _marcador_em_atomo_arquivo(
            texto, m.start("neg"), m.end("neg"),
        )
        marcadores.append({
            "marcador": m.group("neg"),
            "inicio": m.start("neg"),
            "fim": m.end("neg"),
            "prefixo": prefixo,
            "cauda": cauda,
            "interno": bool(prefixo),
            "atomo_arquivo": bool(atomo),
            "atomo_valor": valor,
        })
    bloqueantes = [
        item for item in marcadores
        if item["interno"] and not item["atomo_arquivo"]
    ]
    return {
        "texto": texto,
        "marcadores": marcadores,
        "bloqueia": bool(bloqueantes),
        "primeiro": dict(bloqueantes[0]) if bloqueantes else {},
        "atomos_liberados": [
            dict(item) for item in marcadores if item["atomo_arquivo"]
        ],
    }


def aplicar_veto_canonico(
    turno: Mapping[str, Any] | None,
    *,
    texto: str,
    modalidade: str,
    natureza: str,
    motivo: str,
    requer_esclarecimento: bool,
    origem_veto: str,
) -> dict[str, Any]:
    """Reescreve o contrato inteiro; não deixa autoridade stale em segmentos."""
    novo = dict(turno or {})
    modal = str(modalidade or "recusa").strip().casefold() or "recusa"
    normalizado = re.sub(r"\s+", " ", str(texto or "")).strip()
    segmento = {
        "indice": 0,
        "texto": normalizado[:300],
        "modalidade": modal,
        "confianca": max(0.99, float(novo.get("confianca") or 0.0)),
        "motivo": str(motivo or "veto operacional soberano"),
        "autoriza_execucao": False,
        "acao_explicita": False,
        "requer_esclarecimento": bool(requer_esclarecimento),
        "natureza_acao": str(natureza or "nenhuma"),
        "veto_execucao_operacional": True,
    }
    novo.update(
        modalidade=modal,
        modalidade_geral=modal,
        ato_principal=modal,
        atos=[modal],
        segmentos=[segmento],
        texto_operacional="",
        texto_conversacional=normalizado[:500],
        acao_explicita=False,
        autoriza_execucao=False,
        requer_esclarecimento=bool(requer_esclarecimento),
        natureza_acao=str(natureza or "nenhuma"),
        motivo=str(motivo or "veto operacional soberano"),
        motivo_decisao=str(motivo or "veto operacional soberano"),
        veto_execucao_operacional=True,
        origem_veto_execucao_operacional=str(origem_veto or "proteção_operacional"),
        motivo_veto_execucao_operacional=str(motivo or "veto operacional soberano"),
        confianca=max(0.99, float(novo.get("confianca") or 0.0)),
    )
    return novo


def estrutura_vetada_coerente(turno: Mapping[str, Any]) -> bool:
    t = dict(turno or {})
    segs = [x for x in list(t.get("segmentos") or []) if isinstance(x, dict)]
    if not (
        turno_tem_veto_execucao(t)
        and t.get("autoriza_execucao") is False
        and t.get("acao_explicita") is False
        and str(t.get("texto_operacional") or "") == ""
        and str(t.get("ato_principal") or "") != "comando"
    ):
        return False
    if not segs:
        return False
    return all(
        seg.get("autoriza_execucao") is False
        and seg.get("acao_explicita") is False
        and str(seg.get("modalidade") or "") != "comando"
        for seg in segs
    )


# ============================================================================
# CANDIDATO — REVISÃO PONTUADA CONSERVADORA
# ============================================================================

def revisar_candidato(texto: str, resolver_real: Callable[[str], Mapping[str, Any]]) -> dict[str, Any]:
    """Preserva correção discursiva explícita; não apaga escopo negativo.

    Distinção estrutural mínima:
    - `não, FAÇA C`  -> marcador discursivo de correção; o resolver real pode
      consolidar C (vírgula/;/:/- logo DEPOIS do `não` é evidência literal).
    - `não FAÇA B`   -> negação da nova operação; não pode virar FAÇA B.
    - `não O B`      -> restrição elíptica; não pode virar troca positiva de alvo.

    O wrapper só intervém depois que o resolver REAL detectou uma revisão, logo
    não inventa uma nova raiz de revisão por conta própria.
    """
    rev = dict(resolver_real(texto) or {})
    if not (rev.get("detectada") and rev.get("resolvida")):
        return rev
    if rev.get("cancelada"):
        return rev

    achado = REVISAO_NAO_RE.search(str(texto or ""))
    if not achado:
        return rev

    resto_raw = str(achado.group("resto") or "")
    # A pontuação imediatamente posterior ao marcador é o receipt literal de
    # que "não" encerra a proposta anterior e NÃO nega semanticamente C.
    correcao_discursiva_explicita = bool(
        re.match(r"^\s*[,;:\-]\s*\S", resto_raw)
    )
    if correcao_discursiva_explicita:
        return rev

    # Sem esse boundary, manter qualquer saída operacional consolidada seria
    # destruir a polaridade. Isso inclui tanto `substituicao_alvo` quanto
    # `substituicao_comando/acao` (ex.: `não feche o Opera`).
    rev.update(
        resolvida=False,
        cancelada=False,
        tipo="ambigua",
        texto_operacional_efetivo="",
        motivo=(
            "negação após proposta operacional sem separador discursivo posterior "
            "não prova correção positiva"
        ),
    )
    return rev


# ============================================================================
# WRAPPERS DO CANDIDATO SOBRE COMPONENTES REAIS
# ============================================================================

def classificar_sem_revisao_candidato(
    texto: str,
    *,
    classificar_real: Callable[..., Mapping[str, Any]],
    p0_real: Callable[..., Mapping[str, Any] | None],
    normalizar_texto: Callable[[str], str],
    texto_tem_comando_explicito: Callable[[str], bool],
) -> dict[str, Any]:
    base = dict(classificar_real(
        texto,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=False,
    ) or {})

    p0 = p0_real(texto, normalizar_texto=normalizar_texto)
    if p0:
        natureza_p0 = str(
            p0.get("natureza_acao") or base.get("natureza_acao") or "nenhuma"
        ).casefold()
        # Nem todo fail-closed histórico é um veto monotônico. Perguntas
        # informativas/read-only precisam continuar podendo consultar estado
        # atual (ex.: "O Opera continua aberto?"). O receipt sticky nasce
        # somente quando a P0 representa proibição/ausência soberana de
        # autoridade que uma especialização posterior não pode substituir.
        naturezas_sticky = {
            "cancelamento",
            "capacidade",
            "hipotetica",
            "mencao_operacional",
            "instrucao_ou_explicacao",
            "decepcao",
        }
        if natureza_p0 in naturezas_sticky:
            return aplicar_veto_canonico(
                base,
                texto=texto,
                modalidade=str(p0.get("modalidade") or base.get("modalidade") or "conversa"),
                natureza=natureza_p0,
                motivo=str(p0.get("motivo") or base.get("motivo") or "P0 operacional"),
                requer_esclarecimento=bool(p0.get("requer_esclarecimento")),
                origem_veto="p0_ato_fala",
            )
        return base

    # Recusas operacionais históricas que não passaram pela P0 formal também
    # precisam de receipt sticky. Isso cobre, por exemplo, adiamentos/negações
    # que o classificador base já fechou sem dar crédito ao detector V2.5.
    # Recusa curta como "nao" não tem comando explícito e continua apenas
    # auth=False neutra para que possa cancelar uma pendência legítima.
    if (
        base.get("autoriza_execucao") is not True
        and str(base.get("modalidade") or "").casefold() == "recusa"
        and bool(texto_tem_comando_explicito(texto))
    ):
        return aplicar_veto_canonico(
            base,
            texto=texto,
            modalidade="recusa",
            natureza=str(base.get("natureza_acao") or "cancelamento"),
            motivo=str(base.get("motivo") or "recusa operacional histórica"),
            requer_esclarecimento=bool(base.get("requer_esclarecimento")),
            origem_veto="recusa_operacional_historica",
        )

    # Soberania histórica: o detector V2.5 só GANHA crédito quando a
    # classificação anterior tinha realmente concedido autoridade.
    if base.get("autoriza_execucao") is not True:
        return base

    analise = analisar_negacao_interna_conservadora(texto)
    if not analise.get("bloqueia"):
        return base

    return aplicar_veto_canonico(
        base,
        texto=texto,
        modalidade="recusa",
        natureza="ambiguidade_polaridade_interna",
        motivo=(
            "V2.5 LAB: negação interna standalone sem decomposição operacional "
            "segura; execução não presumida"
        ),
        requer_esclarecimento=True,
        origem_veto="negacao_interna_stt",
    )


def construir_turno_candidato(
    texto: str,
    *,
    resolver_revisao_real: Callable[[str], Mapping[str, Any]],
    classificar_real: Callable[..., Mapping[str, Any]],
    p0_real: Callable[..., Mapping[str, Any] | None],
    normalizar_texto: Callable[[str], str],
    texto_tem_comando_explicito: Callable[[str], bool],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    rev = revisar_candidato(texto, resolver_revisao_real)
    detectada = bool(rev.get("detectada"))
    resolvida = bool(rev.get("resolvida"))
    cancelada = bool(rev.get("cancelada"))
    efetivo = str(rev.get("texto_operacional_efetivo") or "").strip()

    if detectada and resolvida and not cancelada and efetivo:
        turno = classificar_sem_revisao_candidato(
            efetivo,
            classificar_real=classificar_real,
            p0_real=p0_real,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
        turno.update(
            texto_original=str(texto or "")[:500],
            texto=str(texto or "")[:500],
            revisao_intra_turno=dict(rev),
            texto_operacional_efetivo=efetivo,
        )
        if autoriza_execucao_efetiva(turno):
            turno["texto_operacional"] = efetivo
        return turno, rev, efetivo

    base = classificar_sem_revisao_candidato(
        texto,
        classificar_real=classificar_real,
        p0_real=p0_real,
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    if not detectada:
        return base, rev, texto

    if not resolvida:
        turno = aplicar_veto_canonico(
            base,
            texto=texto,
            modalidade="correcao",
            natureza="revisao_ambigua",
            motivo=str(rev.get("motivo") or "revisão ambígua sem forma operacional segura"),
            requer_esclarecimento=True,
            origem_veto="revisao_ambigua",
        )
    else:
        turno = aplicar_veto_canonico(
            base,
            texto=texto,
            modalidade="recusa",
            natureza="cancelamento_revisao",
            motivo=str(rev.get("motivo") or "usuário cancelou a proposta antes da execução"),
            requer_esclarecimento=False,
            origem_veto="revisao_cancelada",
        )
    turno.update(
        texto_original=str(texto or "")[:500],
        texto=str(texto or "")[:500],
        revisao_intra_turno=dict(rev),
        texto_operacional_efetivo="",
    )
    return turno, rev, texto


def aplicar_repeticao_candidato(
    turno: Mapping[str, Any],
    repeticao: object,
    aplicar_real: Callable[[dict, object], dict],
) -> dict[str, Any]:
    if turno_tem_veto_execucao(turno):
        return dict(turno)
    return dict(aplicar_real(dict(turno), repeticao) or {})


def aplicar_elipse_candidato(
    texto: str,
    *,
    turno: Mapping[str, Any],
    pendencia_turno: object,
    aplicar_real: Callable[..., dict],
) -> dict[str, Any]:
    if turno_tem_veto_execucao(turno):
        return dict(turno)
    return dict(aplicar_real(
        texto,
        turno=dict(turno),
        pendencia_turno=pendencia_turno,
    ) or {})


def aplicar_visual_candidato(
    turno: Mapping[str, Any],
    pedido: Mapping[str, Any] | None,
    aplicar_real: Callable[[dict, Mapping[str, Any]], dict],
) -> dict[str, Any]:
    if turno_tem_veto_execucao(turno):
        return dict(turno)
    if not isinstance(pedido, Mapping):
        return dict(turno)
    return dict(aplicar_real(dict(turno), dict(pedido)) or {})


def barreira_candidata(
    texto: str,
    *,
    classificacao: Mapping[str, Any],
    barreira_real: Callable[..., bool],
    normalizar_texto: Callable[[str], str],
    texto_tem_comando_explicito: Callable[[str], bool],
) -> bool:
    if turno_tem_veto_execucao(classificacao):
        return True
    # Defesa redundante no boundary operacional: recompõe o predicado bare/STT
    # no texto efetivo antes de confiar em uma classificação que possa ter sido
    # reescrita por camada posterior.
    if analisar_negacao_interna_conservadora(texto).get("bloqueia"):
        return True
    return bool(barreira_real(
        texto,
        classificacao=dict(classificacao),
        normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=False,
    ))


def planejar_candidato(
    texto: str,
    *,
    turno: Mapping[str, Any],
    planejar_real: Callable[..., Mapping[str, Any]],
    criar_decisao_candidato: Callable[[Mapping[str, Any], Mapping[str, Any]], dict],
) -> dict[str, Any]:
    plano = dict(planejar_real(
        texto,
        turno=dict(turno),
        mente={},
        periodo="teste",
    ) or {})
    if not turno_tem_veto_execucao(turno):
        return plano

    atos = []
    for ato in list(plano.get("atos") or []):
        if not isinstance(ato, dict):
            continue
        item = dict(ato)
        item["requer_execucao"] = False
        atos.append(item)
    plano.update(
        atos=atos,
        requer_execucao=False,
        autoriza_execucao=False,
        turno_sem_autorizacao=True,
        veto_execucao_operacional=True,
    )
    plano["decisao_turno"] = criar_decisao_candidato(turno, plano)
    return plano


def criar_decisao_candidato(
    turno: Mapping[str, Any],
    plano: Mapping[str, Any],
    criar_real: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    contrato = dict(criar_real(dict(turno), dict(plano)) or {})
    if turno_tem_veto_execucao(turno):
        contrato.update(
            proprietario="conversa",
            permite_acao=False,
            intencao="",
            status="sem_acao",
            veto_execucao_operacional=True,
        )
    return contrato


def filtrar_comandos_candidato(
    comandos: Sequence[Mapping[str, Any]],
    *,
    turno: Mapping[str, Any],
    plano: Mapping[str, Any],
    retrato: Mapping[str, Any],
    filtrar_real: Callable[..., Mapping[str, Any]],
) -> dict[str, Any]:
    if turno_tem_veto_execucao(turno):
        rejeitados = []
        for item in comandos:
            intent = str(dict(item).get("intent") or dict(item).get("acao") or "").upper()
            rejeitados.append({
                "intent": intent,
                "motivo": "veto operacional soberano do turno",
            })
        return {
            "comandos": [],
            "rejeitados": rejeitados,
            "autoriza_execucao": False,
            "proprietario": "conversa",
            "veto_execucao_operacional": True,
        }
    return dict(filtrar_real(
        [dict(x) for x in comandos],
        turno=dict(turno),
        plano=dict(plano),
        retrato=dict(retrato),
    ) or {})


def prioridade_readonly_sistema_candidata(
    turno: Mapping[str, Any],
    candidato: Mapping[str, Any] | None,
    autorizador_real: Callable[[dict | None, dict | None], bool],
) -> bool:
    """Live read-only não é conversa: receipt soberano vence a exceção atual."""
    if turno_tem_veto_execucao(turno):
        return False
    return bool(autorizador_real(
        dict(candidato or {}) if isinstance(candidato, Mapping) else None,
        dict(turno or {}),
    ))


def processar_readonly_prioritario_candidato(
    ctx: dict[str, Any],
    texto: str,
    *,
    turno: Mapping[str, Any],
    processar_real: Callable[[dict[str, Any], str], tuple[bool, str]],
) -> tuple[bool, str]:
    """Modela o gate que precisa anteceder a consulta live do sistema."""
    if turno_tem_veto_execucao(turno):
        return False, ""
    return processar_real(ctx, texto)


def prioridade_pode_responder_capacidade_candidata(turno: Mapping[str, Any]) -> bool:
    """Catálogo estático de capacidade pode responder sem criar intent prática."""
    t = dict(turno or {})
    return bool(
        turno_tem_veto_execucao(t)
        and str(t.get("natureza_acao") or "").casefold() == "capacidade"
        and not autoriza_execucao_efetiva(t)
    )


def arbitrar_turno_candidato(
    texto: str,
    candidatos: Sequence[Any],
    *,
    turno: Mapping[str, Any],
    retrato: Mapping[str, Any],
    arbitrar_real: Callable[..., Mapping[str, Any]],
    criar_decisao_real: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """O árbitro também respeita receipt; read-only não vira exceção de veto."""
    if not turno_tem_veto_execucao(turno):
        return dict(arbitrar_real(
            texto,
            candidatos,
            turno=dict(turno),
            retrato=dict(retrato),
        ) or {})

    rejeitados = []
    for candidato in candidatos:
        rejeitados.append({
            "origem": str(getattr(candidato, "origem", "") or ""),
            "tipo": str(getattr(candidato, "tipo", "") or ""),
            "motivo": "veto operacional soberano do turno",
        })
    contrato = criar_decisao_candidato(
        turno,
        {},
        criar_real=criar_decisao_real,
    )
    return {
        "decisao": None,
        "origem": "",
        "tipo": "",
        "confianca": 0.0,
        "modalidade": str(
            dict(turno).get("modalidade_geral")
            or dict(turno).get("modalidade")
            or "conversa"
        ),
        "evidencias": [],
        "rejeitados": rejeitados,
        "retrato_id": dict(retrato).get("id"),
        "referencia_resolvida": dict(dict(retrato).get("referencia_resolvida") or {}),
        "contrato_decisao": contrato,
        "veto_execucao_operacional": True,
    }


def resolver_intencao_candidato(
    texto: str,
    origem: str,
    ctx: dict[str, Any],
    resolver_real: Callable[[str, str, dict[str, Any]], tuple[Any, str]],
) -> tuple[Any, str]:
    """Gate do coordenador precede agenda, continuidade, detector e IA-first."""
    turno = dict(ctx.get("turno_atual") or {}) if isinstance(ctx, dict) else {}
    if turno_tem_veto_execucao(turno):
        return None, "veto_operacional_turno"
    return resolver_real(texto, origem, ctx)


ETAPAS_PRE_FLUXO_VETADAS = frozenset({
    # 4.28 provou visual como FIRST RED. A segunda revisão de fonte mostrou a
    # mesma classe de risco em outras continuidades capazes de produzir intent
    # ou chamar handlers operacionais a partir de estado anterior.
    "processar_continuacao_visao_jogo",
    "processar_reparacao_conversacional",
    "processar_resposta_pendencia_prioritaria",
    "processar_feedback_pendente",
    "processar_confirmacao_musical_pendente",
    "processar_pergunta_curta_contextual",
})


def etapa_prefluxo_operacional_candidata(
    ctx: dict[str, Any],
    texto: str,
    processar_real: Callable[[dict[str, Any], str], tuple[bool, str]],
) -> tuple[bool, str]:
    """Receipt impede só continuidades capazes de produzir trabalho operacional."""
    mente = ctx.get("mente_integrada_estado") if isinstance(ctx, dict) else {}
    turno = dict((mente or {}).get("turno_atual") or {}) if isinstance(mente, dict) else {}
    if turno_tem_veto_execucao(turno):
        return False, ""
    return processar_real(ctx, texto)


def processar_continuacao_visual_candidato(
    ctx: dict[str, Any],
    texto: str,
    processar_real: Callable[[dict[str, Any], str], tuple[bool, str]],
) -> tuple[bool, str]:
    """Alias explícito do boundary FIRST RED provado no 4.28."""
    return etapa_prefluxo_operacional_candidata(ctx, texto, processar_real)


def prefluxo_candidato(
    ctx: dict[str, Any],
    texto: str,
    *,
    fluxo_modulo: Any,
    processar_inicio_real: Callable[[dict[str, Any], str], bool],
) -> bool:
    """Atravessa o pré-fluxo REAL com um filtro seletivo de continuidades.

    Não bloqueia o pipeline inteiro. Apenas os símbolos da classe operacional
    acima recebem o receipt. Proteção de playlist, comentário de resultado e
    opinião conversacional continuam usando a implementação real.

    O monkeypatch existe apenas no processo do LAB e todos os símbolos são
    restaurados no `finally`; nenhum arquivo de produção é alterado.
    """
    originais: dict[str, Any] = {}

    for nome in ETAPAS_PRE_FLUXO_VETADAS:
        real = getattr(fluxo_modulo, nome, None)
        if not callable(real):
            continue
        originais[nome] = real

        def etapa(
            local_ctx: dict[str, Any],
            local_texto: str,
            _real: Callable[[dict[str, Any], str], tuple[bool, str]] = real,
        ) -> tuple[bool, str]:
            return etapa_prefluxo_operacional_candidata(
                local_ctx,
                local_texto,
                _real,
            )

        setattr(fluxo_modulo, nome, etapa)

    try:
        return bool(processar_inicio_real(ctx, texto))
    finally:
        for nome, real in originais.items():
            setattr(fluxo_modulo, nome, real)


# ============================================================================
# CASOS
# ============================================================================

@dataclass(frozen=True)
class Caso:
    id: str
    texto: str
    esperado: str  # block | preserve


ROOT_STT = [
    Caso("R1", "fecha a microsoft store nao o opera", "block"),
    Caso("R1B", "fecha só a microsoft store nao o opera", "block"),
    Caso("R1C", "fecha só a microsoft store não o opera", "block"),
    Caso("R2", "fecha o opera nao a microsoft store", "block"),
    Caso("R3", "fecha o opera nao feche a microsoft store", "block"),
    Caso("R3B", "fecha a microsoft store nao feche o opera", "block"),
    Caso("R4", "fecha o opera não a microsoft store", "block"),
    Caso("R5", "fecha o opera nunca a microsoft store", "block"),
    Caso("R6", "fecha o opera jamais a microsoft store", "block"),
]

PAYLOADS = [
    Caso("P0", "toca nao existe amor em sp", "block"),
    Caso("P1", "pesquisa nao abaixa o volume", "block"),
    Caso("P2", "pesquisa gatos nao aumenta o volume", "block"),
    Caso("P3", "toca nao abaixa o volume", "block"),
    Caso("P4", "escreve nao abaixa o volume no arquivo teste.txt", "block"),
    Caso("P5", "cria arquivo teste.txt contendo nao aumenta o volume", "block"),
    Caso("P6", "cria arquivo nao abaixa volume.txt", "block"),
    Caso("P7", 'pesquisa "nao feche o opera"', "block"),
    Caso("P8", 'fecha o opera "nao a microsoft store', "block"),
]

ATOMOS_POSITIVOS = [
    Caso("A1", "cria arquivo nao.txt", "preserve"),
    Caso("A2", "abre o arquivo nao.txt", "preserve"),
    Caso("A3", "cria arquivo não.md", "preserve"),
]

POSITIVOS = [
    Caso("C1", "fecha o opera", "preserve"),
    Caso("C2", "abaixa o volume", "preserve"),
    Caso("C3", "aumenta o volume", "preserve"),
    Caso("C4", "pesquisa gatos", "preserve"),
    Caso("C5", "toca rock", "preserve"),
    Caso("C6", "abre o opera e fecha a calculadora", "preserve"),
    Caso("C7", "cria arquivo nao.txt e abre o opera", "preserve"),
]

HISTORICOS_VETO = [
    Caso("H1", "nao fecha o opera", "block"),
    Caso("H2", "não fecha o opera", "block"),
    Caso("H3", "fecha a microsoft store e nao feche o opera", "block"),
    Caso("H4", "fecha o opera nao agora", "block"),
    Caso("H5", 'a frase "nao feche o opera" e so um exemplo', "block"),
]

BOUNDARY = [
    Caso("B1", "cria arquivo nao.txt e fecha o opera nao a microsoft store", "block"),
    Caso("B2", "cria arquivo nao.txt e nao fecha o opera", "block"),
    Caso("B3", "abre o opera e fecha a calculadora nao a microsoft store", "block"),
]

PONTUADOS_BLOCK = [
    "fecha só a microsoft store, não o opera",
    "fecha a microsoft store, não o opera",
    "fecha a microsoft store mas nao o opera",
    "fecha a microsoft store, não feche o opera",
    "fecha a microsoft store mas nao feche o opera",
]

REVISOES_POSITIVAS = [
    ("Abre Wikipédia... não, melhor Prime Video.", "abre Prime Video"),
    ("Pausa a música... não, continua tocando.", "continua a música"),
    ("Liga a lâmpada... não, deixa desligada.", "desliga lâmpada"),
    ("Cria um arquivo chamado erro.txt... não, chama correcao.txt.", "Cria um arquivo chamado correcao.txt"),
]


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    print("CANDIDATO FINAL LAB V2.5 — VETO MONOTÔNICO / TURNO 229")
    print("=" * 88)
    print("produção: INTACTA | efeito físico: ZERO | LLM: ZERO")

    try:
        repo = localizar_repo()
    except Exception as e:
        print(f"\n🟠 EXIT 1 — {e}")
        return 1

    titulo("GUARDS / LOCKS")
    premissas: list[str] = []
    falhas: list[str] = []
    head = git(repo, "rev-parse", "HEAD")
    print(f"HEAD ........ {'PASS' if head == HEAD else 'FAIL'} {head}")
    if head != HEAD:
        premissas.append("HEAD mudou")

    for arquivo, esperado in BLOBS.items():
        atual = git(repo, "rev-parse", f"HEAD:{arquivo}")
        ok = atual == esperado
        print(f"{arquivo:<62} {'PASS' if ok else 'FAIL'}")
        if not ok:
            premissas.append(f"blob mudou: {arquivo}")

    dirty = git(repo, "status", "--porcelain", "--", "laylay.py", "mente_laylay", check=False)
    print(f"produção limpa {'PASS' if not dirty.strip() else 'FAIL'}")
    if dirty.strip():
        print(dirty)
        premissas.append("produção está suja")

    # WIRING/ORDEM REAL — o LAB não ganha autoridade apenas porque os imports
    # encaixam. Ele prova as fronteiras que está modelando no HEAD travado.
    try:
        src_turno = git(repo, "show", "HEAD:mente_laylay/cognicao/orquestrador_turno_runtime.py")
        src_imed = git(repo, "show", "HEAD:mente_laylay/autonomia/comandos_imediatos.py")
        src_coord = git(repo, "show", "HEAD:mente_laylay/autonomia/coordenador_intencao.py")
        src_fluxo = git(repo, "show", "HEAD:mente_laylay/autonomia/fluxo_resposta_ia.py")
    except Exception as e:
        premissas.append(f"falha ao reler wiring real: {type(e).__name__}")
    else:
        p_cls = src_turno.find("turno = ns['_classificar_modalidade_turno_mente']")
        p_elipse = src_turno.find("turno = aplicar_elipse_espacial_autorizada_ao_turno(")
        p_rep = src_turno.find("turno = aplicar_repeticao_operacional_ao_turno(turno, repeticao_operacional)")
        p_vis = src_turno.find("turno = aplicar_pedido_visual_ao_turno(turno, pedido_visao_jogo)")
        p_plan = src_turno.find("plano = ns['_planejar_turno_mente'](")
        ordem_produtores = bool(
            p_cls >= 0 and p_elipse > p_cls and p_rep > p_elipse
            and p_vis > p_rep and p_plan > p_vis
        )
        p_read = src_imed.find("processar_consulta_sistema_local(")
        p_bar = src_imed.find("if bloqueia_execucao_operacional_prioritaria(")
        readonly_antes_barreira = bool(p_read >= 0 and p_bar > p_read)
        p_agenda = src_coord.find('lembrete = _call(ctx, "extrair_agendamento", texto)')
        p_arb = src_coord.find("arbitragem = arbitrar_turno(")
        agenda_antes_arbitro = bool(p_agenda >= 0 and p_arb > p_agenda)
        continuidade_primeira = (
            "etapas = [lambda: processar_continuacao_visao_jogo(ctx, t)]"
            in src_fluxo
        )
        print(f"ordem produtores pós-classificação ........ {'PASS' if ordem_produtores else 'FAIL'}")
        print(f"read-only prioritário antes da barreira .... {'PASS' if readonly_antes_barreira else 'FAIL'}")
        print(f"agenda do coordenador antes do árbitro ..... {'PASS' if agenda_antes_arbitro else 'FAIL'}")
        print(f"continuação visual abre o pré-fluxo ........ {'PASS' if continuidade_primeira else 'FAIL'}")
        if not ordem_produtores:
            premissas.append("ordem dos produtores pós-classificação mudou")
        if not readonly_antes_barreira:
            premissas.append("ordem read-only/barreira prioritária mudou")
        if not agenda_antes_arbitro:
            premissas.append("ordem agenda/árbitro no coordenador mudou")
        if not continuidade_primeira:
            premissas.append("ordem do pré-fluxo mudou")

    if premissas:
        print("\n🟠 EXIT 1 — LOCK/WIRING/PREMISSA INVÁLIDA")
        for x in premissas:
            print(f"❌ {x}")
        return 1

    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    try:
        from mente_laylay.cognicao.modalidade_turno import (
            classificar_modalidade_turno,
            bloqueia_execucao_operacional_prioritaria,
            _protecao_p0_ato_fala,
        )
        from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
        from mente_laylay.autonomia.porteiro_acoes import (
            normalizar_texto,
            texto_tem_comando_explicito,
            autorizar_acao_pratica,
        )
        from mente_laylay.cognicao.orquestrador_turno_runtime import (
            aplicar_repeticao_operacional_ao_turno,
            aplicar_elipse_espacial_autorizada_ao_turno,
        )
        from mente_laylay.cognicao.intencao_visual_jogo import (
            detectar_pedido_visao_jogo,
            aplicar_pedido_visual_ao_turno,
        )
        from mente_laylay.memoria_mental.compatibilidade_contexto import (
            resolver_repeticao_ultima_acao,
        )
        from mente_laylay.cognicao.plano_turno import planejar_turno
        from mente_laylay.cognicao.decisao_turno import (
            criar_contrato_decisao,
            filtrar_comandos_pelo_turno,
        )
        from mente_laylay.cognicao.arbitro_turno import (
            CandidatoDecisao,
            arbitrar_turno,
        )
        from mente_laylay.autonomia.comandos_imediatos import (
            _candidato_prioritario_autorizado,
        )
        from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_consulta_sistema_local
        import mente_laylay.autonomia.fluxo_resposta_ia as fluxo_resposta_ia_mod
        from mente_laylay.autonomia.fluxo_resposta_ia import (
            processar_inicio_fluxo_resposta_ia,
        )
        from mente_laylay.autonomia.pre_fluxo_contextual import (
            processar_continuacao_visao_jogo,
            processar_feedback_pendente,
            processar_pergunta_curta_contextual,
            processar_confirmacao_musical_pendente,
        )
        from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
        from mente_laylay.autonomia.orquestracao_cooperativa import (
            OrquestradorCooperativoRuntime,
        )
    except Exception as e:
        print(f"\n🟠 EXIT 1 — IMPORT REAL FALHOU: {type(e).__name__}: {e}")
        return 1

    def construir(texto: str) -> tuple[dict[str, Any], dict[str, Any], str]:
        return construir_turno_candidato(
            texto,
            resolver_revisao_real=resolver_revisao_intra_turno,
            classificar_real=classificar_modalidade_turno,
            p0_real=_protecao_p0_ato_fala,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )

    def barreira(texto: str, turno: Mapping[str, Any]) -> bool:
        return barreira_candidata(
            texto,
            classificacao=turno,
            barreira_real=bloqueia_execucao_operacional_prioritaria,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )

    def criar_dec(turno: Mapping[str, Any], plano: Mapping[str, Any]) -> dict:
        return criar_decisao_candidato(
            turno,
            plano,
            criar_real=criar_contrato_decisao,
        )

    # ------------------------------------------------------------------
    titulo("FASE 0 — ESTADO DE AUTORIDADE: FALSE NEUTRO != VETO")
    neutro, _, _ = construir("olha esse item")
    negacao_curta, _, _ = construir("nao")
    print(f"olha esse item -> auth={neutro.get('autoriza_execucao')} veto={turno_tem_veto_execucao(neutro)}")
    print(f"nao            -> auth={negacao_curta.get('autoriza_execucao')} veto={turno_tem_veto_execucao(negacao_curta)}")
    if turno_tem_veto_execucao(neutro) or turno_tem_veto_execucao(negacao_curta):
        premissas.append("candidato congelou todo auth=False em vez de distinguir veto")

    # ------------------------------------------------------------------
    titulo("FASE 1 — RAIZ PONTUADA SEPARADA / REVISÃO")
    for texto in PONTUADOS_BLOCK:
        rev_real = dict(resolver_revisao_intra_turno(texto) or {})
        turno, rev_cand, efetivo = construir(texto)
        print(f"{texto!r}")
        print(f"  real -> tipo={rev_real.get('tipo')} resolvida={rev_real.get('resolvida')} efetivo={rev_real.get('texto_operacional_efetivo')!r}")
        print(f"  cand -> tipo={rev_cand.get('tipo')} resolvida={rev_cand.get('resolvida')} auth={turno.get('autoriza_execucao')} veto={turno_tem_veto_execucao(turno)}")
        if not (
            rev_real.get("detectada")
            and rev_real.get("resolvida")
            and not rev_real.get("cancelada")
            and str(rev_real.get("texto_operacional_efetivo") or "").strip()
            and rev_cand.get("detectada")
            and rev_cand.get("resolvida") is False
            and str(rev_cand.get("texto_operacional_efetivo") or "") == ""
            and estrutura_vetada_coerente(turno)
            and barreira(efetivo, turno)
        ):
            falhas.append(f"pontuado não ficou fail-closed: {texto}")

    print("\nControles de revisão positiva:")
    for texto, esperado in REVISOES_POSITIVAS:
        turno, rev, efetivo = construir(texto)
        ok = bool(
            rev.get("detectada")
            and rev.get("resolvida")
            and not rev.get("cancelada")
            and not turno_tem_veto_execucao(turno)
            and autoriza_execucao_efetiva(turno)
            and norm_sem_acento(efetivo).casefold() == norm_sem_acento(esperado).casefold()
        )
        print(f"  {'PASS' if ok else 'FAIL'} {texto!r} -> {efetivo!r}")
        if not ok:
            falhas.append(f"revisão positiva regrediu: {texto}")

    # ------------------------------------------------------------------
    titulo("FASE 2 — ROOT STT / PAYLOAD / ÁTOMO / BOUNDARY")
    for grupo_nome, grupo in (
        ("ROOT", ROOT_STT),
        ("PAYLOAD", PAYLOADS),
        ("ATOM", ATOMOS_POSITIVOS),
        ("POSITIVO", POSITIVOS),
        ("HISTORICO", HISTORICOS_VETO),
        ("BOUNDARY", BOUNDARY),
    ):
        print(f"\n-- {grupo_nome} --")
        for caso in grupo:
            turno, rev, efetivo = construir(caso.texto)
            veto = turno_tem_veto_execucao(turno)
            auth = autoriza_execucao_efetiva(turno)
            atomos = analisar_negacao_interna_conservadora(efetivo).get("atomos_liberados") or []
            print(
                f"{caso.id:<4} veto={str(veto):<5} auth={str(auth):<5} "
                f"mod={turno.get('modalidade')} op={turno.get('texto_operacional')!r} "
                f"atomos={[x.get('atomo_valor') for x in atomos]}"
            )
            if caso.esperado == "block":
                if not (
                    veto
                    and not auth
                    and estrutura_vetada_coerente(turno)
                    and barreira(efetivo, turno)
                ):
                    falhas.append(f"{caso.id}: não fechou veto estrutural")
            else:
                if veto or not auth:
                    falhas.append(f"{caso.id}: positivo/átomo foi bloqueado")

    # ------------------------------------------------------------------
    titulo("FASE 3 — PRODUTORES PÓS-CLASSIFICAÇÃO / MONOTONICIDADE")
    jogo = {
        "ativo": True,
        "titulo": "Minecraft",
        "processo": "javaw.exe",
        "analise_visual_recente": False,
    }

    # Controle visual neutro precisa continuar subindo.
    t_visual, _, _ = construir("olha esse item")
    pedido_visual = detectar_pedido_visao_jogo("olha esse item", jogo)
    t_visual_pos = aplicar_visual_candidato(
        t_visual,
        pedido_visual,
        aplicar_pedido_visual_ao_turno,
    )
    visual_pos_ok = bool(
        pedido_visual
        and not turno_tem_veto_execucao(t_visual)
        and autoriza_execucao_efetiva(t_visual_pos)
    )
    print(f"visual neutro -> autorizado ........ {'PASS' if visual_pos_ok else 'FAIL'}")
    if not visual_pos_ok:
        premissas.append("controle NEUTRO -> AUTORIZADO visual quebrou")

    # Killer visual não pode subir.
    killer_visual = "olha esse item nao fecha o opera"
    t_killer, _, _ = construir(killer_visual)
    pedido_killer = detectar_pedido_visao_jogo(killer_visual, jogo)
    t_killer_pos = aplicar_visual_candidato(
        t_killer,
        pedido_killer,
        aplicar_pedido_visual_ao_turno,
    )
    visual_veto_ok = bool(
        pedido_killer
        and estrutura_vetada_coerente(t_killer)
        and estrutura_vetada_coerente(t_killer_pos)
        and not autoriza_execucao_efetiva(t_killer_pos)
    )
    print(f"visual VETADO -> autorizado ........ {'FAIL' if not visual_veto_ok else 'PASS (bloqueado)'}")
    if not visual_veto_ok:
        falhas.append("visual reautorizou turno vetado")

    # Defesa redundante: mesmo o helper REAL inseguro não pode furar a barreira
    # se o receipt sticky sobreviveu à cópia do dict.
    t_real_reauth = aplicar_pedido_visual_ao_turno(dict(t_killer), dict(pedido_killer or {}))
    defesa_barreira = bool(
        t_real_reauth.get("autoriza_execucao") is True
        and turno_tem_veto_execucao(t_real_reauth)
        and barreira(killer_visual, t_real_reauth)
    )
    print(f"barreira sobre reauth real/stale ... {'PASS' if defesa_barreira else 'FAIL'}")
    if not defesa_barreira:
        falhas.append("barreira não tornou receipt soberano sobre auth stale")

    # Repetição legítima continua funcionando.
    estado_rep = {
        "ultima_acao_reexecutavel": True,
        "ultima_acao_intent": "CLOSE_APP",
        "ultima_acao_params": {"nome_app": "opera"},
    }
    rep = resolver_repeticao_ultima_acao("tenta de novo", estado_rep, normalizar_texto)
    t_rep, _, _ = construir("tenta de novo")
    t_rep_pos = aplicar_repeticao_candidato(
        t_rep, rep, aplicar_repeticao_operacional_ao_turno,
    )
    rep_ok = bool(rep and autoriza_execucao_efetiva(t_rep_pos) and not turno_tem_veto_execucao(t_rep_pos))
    print(f"repetição neutra -> autorizada ..... {'PASS' if rep_ok else 'FAIL'}")
    if not rep_ok:
        premissas.append("controle positivo de repetição quebrou")

    t_rep_veto = aplicar_veto_canonico(
        t_rep,
        texto="tenta de novo",
        modalidade="recusa",
        natureza="teste_veto",
        motivo="controle monotônico",
        requer_esclarecimento=True,
        origem_veto="controle",
    )
    t_rep_block = aplicar_repeticao_candidato(
        t_rep_veto, rep, aplicar_repeticao_operacional_ao_turno,
    )
    if not estrutura_vetada_coerente(t_rep_block):
        falhas.append("repetição elevou turno vetado")

    # Elipse legítima continua funcionando e também respeita veto.
    t_esq, _, _ = construir("esquerda")
    t_esq_pos = aplicar_elipse_candidato(
        "esquerda",
        turno=t_esq,
        pendencia_turno={},
        aplicar_real=aplicar_elipse_espacial_autorizada_ao_turno,
    )
    esq_ok = autoriza_execucao_efetiva(t_esq_pos)
    print(f"elipse neutra -> autorizada ........ {'PASS' if esq_ok else 'FAIL'}")
    if not esq_ok:
        premissas.append("controle positivo de elipse quebrou")

    t_esq_veto = aplicar_veto_canonico(
        t_esq,
        texto="esquerda",
        modalidade="recusa",
        natureza="teste_veto",
        motivo="controle monotônico",
        requer_esclarecimento=True,
        origem_veto="controle",
    )
    t_esq_block = aplicar_elipse_candidato(
        "esquerda",
        turno=t_esq_veto,
        pendencia_turno={},
        aplicar_real=aplicar_elipse_espacial_autorizada_ao_turno,
    )
    if not estrutura_vetada_coerente(t_esq_block):
        falhas.append("elipse elevou turno vetado")

    # ------------------------------------------------------------------
    titulo("FASE 4 — PLANO / DECISÃO / FILTRO / SEGMENTOS")
    t_block, _, eff_block = construir("fecha o opera nao a microsoft store")
    p_block = planejar_candidato(
        eff_block,
        turno=t_block,
        planejar_real=planejar_turno,
        criar_decisao_candidato=criar_dec,
    )
    decisao_block = criar_dec(t_block, p_block)
    filtro_block = filtrar_comandos_candidato(
        [{"intent": "CLOSE_APP", "params": {"nome_app": "Microsoft Store"}}],
        turno=t_block,
        plano={**p_block, "decisao_turno": decisao_block},
        retrato={},
        filtrar_real=filtrar_comandos_pelo_turno,
    )
    plano_ok = bool(
        estrutura_vetada_coerente(t_block)
        and p_block.get("veto_execucao_operacional") is True
        and p_block.get("autoriza_execucao") is False
        and p_block.get("requer_execucao") is False
        and p_block.get("turno_sem_autorizacao") is True
        and all(not bool(a.get("requer_execucao")) for a in p_block.get("atos") or [] if isinstance(a, dict))
        and decisao_block.get("permite_acao") is False
        and not list(filtro_block.get("comandos") or [])
    )
    print(f"contrato vetado inteiro coerente ... {'PASS' if plano_ok else 'FAIL'}")
    if not plano_ok:
        falhas.append("plano/decisão/filtro não preservou veto")

    # Defesa contra objeto propositalmente inconsistente: receipt vence bool stale.
    stale = dict(t_block)
    stale["autoriza_execucao"] = True
    stale["acao_explicita"] = True
    stale["modalidade"] = "comando"
    stale["modalidade_geral"] = "comando"
    stale["ato_principal"] = "comando"
    stale["segmentos"] = [{
        "indice": 0,
        "texto": "fecha o opera",
        "modalidade": "comando",
        "autoriza_execucao": True,
        "acao_explicita": True,
    }]
    p_stale = planejar_candidato(
        "fecha o opera",
        turno=stale,
        planejar_real=planejar_turno,
        criar_decisao_candidato=criar_dec,
    )
    d_stale = criar_dec(stale, p_stale)
    stale_ok = bool(
        p_stale.get("requer_execucao") is False
        and p_stale.get("autoriza_execucao") is False
        and all(not bool(a.get("requer_execucao")) for a in p_stale.get("atos") or [] if isinstance(a, dict))
        and d_stale.get("permite_acao") is False
    )
    print(f"receipt vence contrato stale ....... {'PASS' if stale_ok else 'FAIL'}")
    if not stale_ok:
        falhas.append("receipt não venceu autoridade stale no plano")

    t_pos, _, eff_pos = construir("fecha o opera")
    p_pos = planejar_candidato(
        eff_pos,
        turno=t_pos,
        planejar_real=planejar_turno,
        criar_decisao_candidato=criar_dec,
    )
    d_pos = criar_dec(t_pos, p_pos)
    positivo_plano_ok = bool(
        autoriza_execucao_efetiva(t_pos)
        and p_pos.get("requer_execucao") is True
        and p_pos.get("autoriza_execucao") is True
        and d_pos.get("permite_acao") is True
    )
    print(f"plano positivo continua executável . {'PASS' if positivo_plano_ok else 'FAIL'}")
    if not positivo_plano_ok:
        premissas.append("plano positivo de CLOSE_APP não permaneceu executável")

    # ------------------------------------------------------------------
    titulo("FASE 5 — BARREIRA + COOPERAÇÃO REAL")

    def cooperacao(texto: str, turno: Mapping[str, Any]) -> tuple[bool, list[Any]]:
        chamadas: list[Any] = []

        def recorder(resultado: dict[str, Any], original: str) -> bool:
            chamadas.append((dict(resultado or {}), str(original or "")))
            return True

        detectar = lambda fala: detectar_pedido_visao_jogo(fala, jogo)
        quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda *_: None)
        orq = OrquestradorCooperativoRuntime(
            quadro=quadro,
            clipboard_snapshot=lambda: {},
            clipboard_getter=lambda: "",
            executar_intencao=recorder,
            resolver_caminho=lambda p: str(p or ""),
            falar=lambda *_a, **_k: None,
            detectar_visao_jogo=detectar,
            estado_getter=lambda: {},
            autorizar_acao=autorizar_acao_pratica,
            log=lambda *_: None,
        )
        bloqueada = barreira(texto, turno)
        tratado = False if bloqueada else bool(orq.processar(texto))
        return tratado, chamadas

    tratado_pos, calls_pos = cooperacao("olha esse item", t_visual_pos)
    coop_pos_ok = bool(tratado_pos and calls_pos)
    print(f"cooperação positiva alcança recorder {'PASS' if coop_pos_ok else 'FAIL'}")
    if not coop_pos_ok:
        premissas.append("controle cooperativo visual positivo quebrou")

    tratado_neg, calls_neg = cooperacao(killer_visual, t_killer_pos)
    coop_neg_ok = bool(not tratado_neg and not calls_neg and barreira(killer_visual, t_killer_pos))
    print(f"cooperação vetada fica inalcançável . {'PASS' if coop_neg_ok else 'FAIL'}")
    if not coop_neg_ok:
        falhas.append("turno vetado alcançou cooperação")

    # ------------------------------------------------------------------
    titulo("FASE 6 — READ-ONLY PRIORITÁRIO / ÁRBITRO / COORDENADOR")

    candidato_ro = {"intent": "GAME_VISION", "params": {"tipo": "avaliacao_item"}}
    ro_real = _candidato_prioritario_autorizado(candidato_ro, t_killer)
    ro_cand = prioridade_readonly_sistema_candidata(
        t_killer,
        candidato_ro,
        _candidato_prioritario_autorizado,
    )
    print(f"prioritário read-only real sob veto . {'RED esperado' if ro_real else 'NÃO reproduziu'}")
    print(f"prioritário read-only candidato ..... {'PASS' if not ro_cand else 'FAIL'}")
    if not ro_real:
        premissas.append("baseline read-only prioritário já respeitou receipt; hipótese do controle mudou")
    if ro_cand:
        falhas.append("read-only prioritário furou veto no candidato")

    # Prova funcional da exceção que hoje roda ANTES da barreira prioritária.
    texto_sys_vetado = "quais programas estao abertos nao fecha o opera"
    t_sys_vetado, _, _ = construir(texto_sys_vetado)
    falas_sys_real: list[str] = []
    ctx_sys = {
        "mente_integrada_estado": {"turno_atual": dict(t_sys_vetado)},
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Opera", "VS Code"],
            "processos_segundo_plano": [],
        },
        "_emitir_resposta_curta": lambda _u, fala, **_k: falas_sys_real.append(str(fala)) or True,
    }
    sys_real, _rota_sys_real = processar_consulta_sistema_local(
        dict(ctx_sys), texto_sys_vetado,
    )
    falas_sys_cand: list[str] = []
    ctx_sys_cand = dict(ctx_sys)
    ctx_sys_cand["_emitir_resposta_curta"] = (
        lambda _u, fala, **_k: falas_sys_cand.append(str(fala)) or True
    )
    sys_cand, _rota_sys_cand = processar_readonly_prioritario_candidato(
        ctx_sys_cand,
        texto_sys_vetado,
        turno=t_sys_vetado,
        processar_real=processar_consulta_sistema_local,
    )
    sys_red = bool(sys_real and falas_sys_real)
    sys_ok = bool(
        turno_tem_veto_execucao(t_sys_vetado)
        and not sys_cand
        and not falas_sys_cand
    )
    print(f"consulta live real antes da barreira  {'RED esperado' if sys_red else 'NÃO reproduziu'}")
    print(f"consulta live candidata sob veto .... {'PASS' if sys_ok else 'FAIL'}")
    if not sys_red:
        premissas.append("baseline funcional de consulta live não reproduziu")
    if not sys_ok:
        falhas.append("consulta live prioritária consumiu turno vetado")

    # Positivos verdadeiros: read-only explícito sem conflito continua livre.
    ro_neutro = prioridade_readonly_sistema_candidata(
        neutro,
        candidato_ro,
        _candidato_prioritario_autorizado,
    )
    print(f"prioritário read-only neutro ....... {'PASS' if ro_neutro else 'FAIL'}")
    if not ro_neutro:
        premissas.append("controle positivo do prioritário read-only quebrou")

    texto_sys_pos = "quais programas estao abertos"
    t_sys_pos, _, _ = construir(texto_sys_pos)
    falas_sys_pos: list[str] = []
    ctx_sys_pos = {
        "mente_integrada_estado": {"turno_atual": dict(t_sys_pos)},
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Opera", "VS Code"],
            "processos_segundo_plano": [],
        },
        "_emitir_resposta_curta": lambda _u, fala, **_k: falas_sys_pos.append(str(fala)) or True,
    }
    sys_pos, _rota_sys_pos = processar_readonly_prioritario_candidato(
        ctx_sys_pos,
        texto_sys_pos,
        turno=t_sys_pos,
        processar_real=processar_consulta_sistema_local,
    )
    sys_pos_ok = bool(
        not turno_tem_veto_execucao(t_sys_pos)
        and sys_pos
        and falas_sys_pos
    )
    print(f"consulta live neutra continua viva . {'PASS' if sys_pos_ok else 'FAIL'}")
    if not sys_pos_ok:
        premissas.append("controle positivo da consulta live foi bloqueado")

    # Uma pergunta de estado com verbo operacional é P0 informativa, não veto.
    texto_estado_pos = "o opera continua aberto?"
    t_estado_pos, _, _ = construir(texto_estado_pos)
    falas_estado_pos: list[str] = []
    ctx_estado_pos = {
        "mente_integrada_estado": {"turno_atual": dict(t_estado_pos)},
        "_resolver_alvo_ambiente": lambda _nome: {
            "programa_aberto": True,
            "programa_em_foco": False,
        },
        "_emitir_resposta_curta": lambda _u, fala, **_k: falas_estado_pos.append(str(fala)) or True,
    }
    estado_pos, _rota_estado_pos = processar_readonly_prioritario_candidato(
        ctx_estado_pos,
        texto_estado_pos,
        turno=t_estado_pos,
        processar_real=processar_consulta_sistema_local,
    )
    estado_readonly_ok = bool(
        not turno_tem_veto_execucao(t_estado_pos)
        and estado_pos
        and falas_estado_pos
    )
    print(f"P0 informativa read-only preservada  {'PASS' if estado_readonly_ok else 'FAIL'}")
    if not estado_readonly_ok:
        premissas.append("P0 informativa virou veto monotônico indevidamente")

    # Capacidade é resposta estática/conversacional, não uma intent live.
    t_cap, _, _ = construir("voce consegue fechar o opera?")
    cap_ok = bool(
        turno_tem_veto_execucao(t_cap)
        and str(t_cap.get("natureza_acao") or "").casefold() == "capacidade"
        and prioridade_pode_responder_capacidade_candidata(t_cap)
    )
    print(f"capacidade estática sob veto ....... {'PASS' if cap_ok else 'FAIL'}")
    if not cap_ok:
        premissas.append("controle de capacidade estática não ficou preservado")

    # O árbitro atual isenta INTENTS_SOMENTE_LEITURA do bool de autorização.
    # O receipt monotônico precisa vencer essa exceção.
    cand_arb = CandidatoDecisao(
        tipo="comando_explicito",
        valor={"intent": "GAME_VISION", "params": {"tipo": "avaliacao_item"}},
        origem="lab-readonly",
        confianca=0.99,
        evidencia=("controle read-only",),
    )
    arb_real_veto = arbitrar_turno(
        killer_visual,
        [cand_arb],
        turno=dict(t_killer),
        retrato={},
    )
    arb_cand_veto = arbitrar_turno_candidato(
        killer_visual,
        [cand_arb],
        turno=t_killer,
        retrato={},
        arbitrar_real=arbitrar_turno,
        criar_decisao_real=criar_contrato_decisao,
    )
    arb_red = isinstance(arb_real_veto.get("decisao"), dict)
    arb_ok = bool(
        not isinstance(arb_cand_veto.get("decisao"), dict)
        and not bool(dict(arb_cand_veto.get("contrato_decisao") or {}).get("permite_acao"))
    )
    print(f"árbitro real read-only sob veto .... {'RED esperado' if arb_red else 'NÃO reproduziu'}")
    print(f"árbitro candidato sob veto ......... {'PASS' if arb_ok else 'FAIL'}")
    if not arb_red:
        premissas.append("baseline do árbitro read-only não reproduziu")
    if not arb_ok:
        falhas.append("árbitro candidato aceitou intent sob veto")

    # Controle positivo do árbitro: sem receipt, o mesmo read-only continua válido.
    arb_neutro = arbitrar_turno_candidato(
        "olha esse item",
        [cand_arb],
        turno=neutro,
        retrato={},
        arbitrar_real=arbitrar_turno,
        criar_decisao_real=criar_contrato_decisao,
    )
    arb_pos_ok = isinstance(arb_neutro.get("decisao"), dict)
    print(f"árbitro read-only neutro ........... {'PASS' if arb_pos_ok else 'FAIL'}")
    if not arb_pos_ok:
        premissas.append("controle positivo do árbitro read-only quebrou")

    # O coordenador possui retornos de agenda antes da arbitragem. O callback
    # abaixo é somente uma precondição controlada; nenhum executor é chamado.
    texto_agenda_vetado = "me lembra de beber agua daqui 5 minutos nao fecha o opera"
    t_agenda_veto, _, _ = construir(texto_agenda_vetado)
    ctx_agenda = {
        "turno_atual": dict(t_agenda_veto),
        "retrato_turno_atual": {},
        "normalizar_texto": normalizar_texto,
        "refinar_contexto_mental": lambda _t: None,
        "extrair_agendamento": lambda _t: {
            "intent": "AGENDAR_LEMBRETE",
            "params": {"descricao": "beber agua", "quando": "5 minutos"},
        },
    }
    coord_real, rota_real = resolver_intencao(texto_agenda_vetado, "lab", dict(ctx_agenda))
    coord_cand, rota_cand = resolver_intencao_candidato(
        texto_agenda_vetado,
        "lab",
        dict(ctx_agenda),
        resolver_intencao,
    )
    coord_red = isinstance(coord_real, dict) and str(coord_real.get("intent") or "").upper() == "AGENDAR_LEMBRETE"
    coord_ok = coord_cand is None and rota_cand == "veto_operacional_turno"
    print(f"coordenador real agenda sob veto ... {'RED esperado' if coord_red else 'NÃO reproduziu'} rota={rota_real!r}")
    print(f"coordenador candidato sob veto ..... {'PASS' if coord_ok else 'FAIL'}")
    if not coord_red:
        premissas.append("baseline estrutural do coordenador/agenda não reproduziu")
    if not coord_ok:
        falhas.append("coordenador candidato resolveu intent sob veto")

    texto_agenda_pos = "me lembra de beber agua daqui 5 minutos"
    t_agenda_pos, _, _ = construir(texto_agenda_pos)
    ctx_agenda_pos = {
        "turno_atual": dict(t_agenda_pos),
        "retrato_turno_atual": {},
        "normalizar_texto": normalizar_texto,
        "refinar_contexto_mental": lambda _t: None,
        "extrair_agendamento": lambda _t: {
            "intent": "AGENDAR_LEMBRETE",
            "params": {"descricao": "beber agua", "quando": "5 minutos"},
        },
    }
    coord_pos, rota_pos = resolver_intencao_candidato(
        texto_agenda_pos,
        "lab",
        ctx_agenda_pos,
        resolver_intencao,
    )
    coord_pos_ok = bool(
        not turno_tem_veto_execucao(t_agenda_pos)
        and isinstance(coord_pos, dict)
        and str(coord_pos.get("intent") or "").upper() == "AGENDAR_LEMBRETE"
        and rota_pos == "agenda"
    )
    print(f"coordenador agenda positiva ......... {'PASS' if coord_pos_ok else 'FAIL'}")
    if not coord_pos_ok:
        premissas.append("controle positivo do coordenador/agenda quebrou")

    # ------------------------------------------------------------------
    titulo("FASE 7 — PRÉ-FLUXO / CONTINUIDADE")

    def ctx_pre(turno: Mapping[str, Any], chamadas: list[str]) -> dict[str, Any]:
        return {
            "mente_integrada_estado": {
                "turno_atual": dict(turno),
                "pendencia_atual": {
                    "id": "lab-v25",
                    "origem": "visao_jogo",
                    "tipo": "complemento_visual",
                    "dominio": "jogo",
                    "intencao": "GAME_VISION_CONTINUE",
                    "status": "ativa",
                    "foi_falada": True,
                },
            },
            "_continuar_visao_jogo_pendente": lambda t: chamadas.append(str(t)) or True,
            "_contexto_horario_atual": lambda: "teste",
        }

    # NEUTRO continua podendo consumir a pendência legítima.
    chamadas_neutras: list[str] = []
    ctx_n = ctx_pre(neutro, chamadas_neutras)
    pre_n = prefluxo_candidato(
        ctx_n,
        "ela tem 15 de evasao",
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    pre_pos_ok = bool(pre_n and chamadas_neutras == ["ela tem 15 de evasao"])
    print(f"continuidade NEUTRA legítima ....... {'PASS' if pre_pos_ok else 'FAIL'}")
    if not pre_pos_ok:
        premissas.append("controle positivo de continuidade quebrou")

    # VETO bloqueia a continuidade visual comprovadamente perigosa; demais
    # etapas seguras do pré-fluxo continuam disponíveis.
    chamadas_veto: list[str] = []
    ctx_v = ctx_pre(t_killer, chamadas_veto)
    pre_v = prefluxo_candidato(
        ctx_v,
        killer_visual,
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    pre_veto_ok = bool(not pre_v and not chamadas_veto)
    print(f"continuidade VETADA bloqueada ...... {'PASS' if pre_veto_ok else 'FAIL'}")
    if not pre_veto_ok:
        falhas.append("pre-fluxo consumiu turno vetado")

    # Segunda revisão: outras continuidades operacionais têm o mesmo problema
    # de contrato, embora visual tenha sido o FIRST RED do 4.28.
    feedback_real_calls: list[str] = []
    ctx_feedback_real = {
        "mente_integrada_estado": {"turno_atual": dict(t_killer)},
        "_handle_feedback_pendente": lambda t: feedback_real_calls.append(str(t)) or True,
    }
    feedback_real, _ = processar_feedback_pendente(ctx_feedback_real, killer_visual)

    feedback_cand_calls: list[str] = []
    ctx_feedback_cand = {
        "mente_integrada_estado": {"turno_atual": dict(t_killer)},
        "_contexto_horario_atual": lambda: "teste",
        "_handle_feedback_pendente": lambda t: feedback_cand_calls.append(str(t)) or True,
    }
    feedback_cand = prefluxo_candidato(
        ctx_feedback_cand,
        killer_visual,
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    feedback_gate_ok = bool(
        feedback_real
        and feedback_real_calls == [killer_visual]
        and not feedback_cand
        and not feedback_cand_calls
    )
    print(f"feedback pendente sob veto .......... {'PASS' if feedback_gate_ok else 'FAIL'}")
    if not feedback_gate_ok:
        falhas.append("feedback pendente consumiu turno vetado")

    musica_real_calls: list[str] = []
    ctx_musica_real = {
        "mente_integrada_estado": {"turno_atual": dict(t_killer)},
        "_processar_confirmacao_sugestao_musical": (
            lambda t: musica_real_calls.append(str(t)) or True
        ),
    }
    musica_real, _ = processar_confirmacao_musical_pendente(
        ctx_musica_real, killer_visual,
    )
    musica_cand_calls: list[str] = []
    ctx_musica_cand = {
        "mente_integrada_estado": {"turno_atual": dict(t_killer)},
        "_contexto_horario_atual": lambda: "teste",
        "_processar_confirmacao_sugestao_musical": (
            lambda t: musica_cand_calls.append(str(t)) or True
        ),
    }
    musica_cand = prefluxo_candidato(
        ctx_musica_cand,
        killer_visual,
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    musica_gate_ok = bool(
        musica_real
        and musica_real_calls == [killer_visual]
        and not musica_cand
        and not musica_cand_calls
    )
    print(f"confirmação musical sob veto ........ {'PASS' if musica_gate_ok else 'FAIL'}")
    if not musica_gate_ok:
        falhas.append("confirmação musical consumiu turno vetado")

    curta_real_calls: list[dict[str, Any]] = []
    ctx_curta_real = {
        "mente_integrada_estado": {"turno_atual": dict(t_killer)},
        "_resolver_pergunta_curta_contextual_intencao": (
            lambda _t: {"intent": "GAME_VISION", "params": {"tipo": "avaliacao_item"}}
        ),
        "_executar_intencao_curta_contextual": (
            lambda intent, _texto, **_k: curta_real_calls.append(dict(intent)) or True
        ),
    }
    curta_real, _ = processar_pergunta_curta_contextual(ctx_curta_real, killer_visual)
    curta_cand_calls: list[dict[str, Any]] = []
    ctx_curta_cand = {
        "mente_integrada_estado": {"turno_atual": dict(t_killer)},
        "_contexto_horario_atual": lambda: "teste",
        "_resolver_pergunta_curta_contextual_intencao": (
            lambda _t: {"intent": "GAME_VISION", "params": {"tipo": "avaliacao_item"}}
        ),
        "_executar_intencao_curta_contextual": (
            lambda intent, _texto, **_k: curta_cand_calls.append(dict(intent)) or True
        ),
    }
    curta_cand = prefluxo_candidato(
        ctx_curta_cand,
        killer_visual,
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    curta_gate_ok = bool(
        curta_real
        and curta_real_calls
        and not curta_cand
        and not curta_cand_calls
    )
    print(f"continuidade curta sob veto ......... {'PASS' if curta_gate_ok else 'FAIL'}")
    if not curta_gate_ok:
        falhas.append("pergunta curta contextual executou sob veto")

    # O gate NÃO pode desligar o pré-fluxo inteiro. Uma proteção de playlist
    # continua autorizada a atualizar a preferência do usuário, mesmo que o turno
    # carregue receipt soberano por conter uma recusa operacional explícita.
    t_playlist = aplicar_veto_canonico(
        dict(negacao_curta),
        texto="nao toca playlist agora",
        modalidade="recusa",
        natureza="cancelamento",
        motivo="controle de proteção de playlist",
        requer_esclarecimento=False,
        origem_veto="controle",
    )
    bloqueios_playlist: list[bool] = []
    falas_playlist: list[str] = []
    ctx_playlist = {
        "mente_integrada_estado": {"turno_atual": t_playlist},
        "_continuar_visao_jogo_pendente": lambda _t: False,
        "_contexto_horario_atual": lambda: "teste",
        "_texto_bloqueia_playlist_agora": lambda t: "playlist" in str(t).casefold(),
        "_bloquear_playlist_temporariamente": lambda: bloqueios_playlist.append(True),
        "_emitir_resposta_curta": lambda _u, fala, **_k: falas_playlist.append(str(fala)) or True,
    }
    pre_playlist = prefluxo_candidato(
        ctx_playlist,
        "nao toca playlist agora",
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    pre_narrow_ok = bool(pre_playlist and bloqueios_playlist == [True] and falas_playlist)
    print(f"gate visual não mata proteção ........ {'PASS' if pre_narrow_ok else 'FAIL'}")
    if not pre_narrow_ok:
        falhas.append("gate de veto ficou amplo demais e matou proteção do pré-fluxo")

    # auth=False sem receipt NÃO é congelado: 'nao' continua fora do gate sticky.
    chamadas_nao: list[str] = []
    ctx_nao = ctx_pre(negacao_curta, chamadas_nao)
    _ = prefluxo_candidato(
        ctx_nao,
        "nao",
        fluxo_modulo=fluxo_resposta_ia_mod,
        processar_inicio_real=processar_inicio_fluxo_resposta_ia,
    )
    false_neutro_ok = not turno_tem_veto_execucao(negacao_curta)
    print(f"recusa curta sem receipt não congela {'PASS' if false_neutro_ok else 'FAIL'}")
    if not false_neutro_ok:
        falhas.append("auth=False simples foi promovido indevidamente a veto sticky")

    # ------------------------------------------------------------------
    titulo("FASE 8 — INVARIANTES FINAIS")
    invariantes = {
        "NEUTRO != VETO": not turno_tem_veto_execucao(neutro),
        "PONTUADO fail-closed": all(estrutura_vetada_coerente(construir(t)[0]) for t in PONTUADOS_BLOCK),
        "STT fail-closed": all(estrutura_vetada_coerente(construir(c.texto)[0]) for c in ROOT_STT),
        "nao.txt preservado": all(not turno_tem_veto_execucao(construir(c.texto)[0]) for c in ATOMOS_POSITIVOS),
        "visual positivo": visual_pos_ok,
        "visual monotônico": visual_veto_ok,
        "repetição positiva": rep_ok,
        "elipse positiva": esq_ok,
        "plano veto coerente": plano_ok,
        "receipt > stale": stale_ok,
        "coop vetada": coop_neg_ok,
        "prioridade read-only vetada": (not ro_cand),
        "prioridade read-only positiva": ro_neutro,
        "consulta live vetada": sys_ok,
        "consulta live positiva": sys_pos_ok,
        "P0 informativa read-only": estado_readonly_ok,
        "árbitro read-only vetado": arb_ok,
        "coordenador vetado": coord_ok,
        "coordenador positivo": coord_pos_ok,
        "capacidade estática preservada": cap_ok,
        "prefluxo visual vetado": pre_veto_ok,
        "feedback pendente vetado": feedback_gate_ok,
        "confirmação musical vetada": musica_gate_ok,
        "continuidade curta vetada": curta_gate_ok,
        "gate prefluxo é estreito": pre_narrow_ok,
        "boundary atom não vaza": all(turno_tem_veto_execucao(construir(c.texto)[0]) for c in BOUNDARY),
    }
    for nome, ok in invariantes.items():
        print(f"{nome:<34} {'PASS' if ok else 'FAIL'}")
        if not ok:
            falhas.append(f"invariante final falhou: {nome}")

    if premissas:
        print("\n🟠 EXIT 1 — CONTROLE/PREMISSA INVÁLIDA")
        for x in premissas:
            print(f"❌ {x}")
        return 1

    if falhas:
        print("\n🔴 EXIT 2 — CANDIDATO V2.5 FALSIFICADO")
        for x in falhas:
            print(f"❌ {x}")
        return 2

    print("\n🟢 EXIT 0 — CANDIDATO FINAL LAB V2.5 GREEN")
    print("Produção continua intacta. GREEN de LAB ainda exige segunda revisão integral.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
