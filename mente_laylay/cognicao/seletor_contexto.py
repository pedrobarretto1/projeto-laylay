"""Seleção central e explicável do contexto de cada turno."""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ContextoCandidato:
    origem: str
    dominio: str
    conteudo: str
    idade_s: float
    relacao: str
    pontuacao: float
    aceito: bool
    evidencia: str


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    bruto = "".join(ch for ch in bruto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_\s.-]", " ", bruto)).strip()


def _tokens(texto: str) -> set[str]:
    stop = {
        "para", "pra", "com", "uma", "uns", "das", "dos", "que", "qual",
        "isso", "esse", "essa", "ele", "ela", "dele", "dela", "aqui", "agora",
        "meu", "minha", "seu", "sua", "voce", "voces", "sobre", "mais", "nao",
    }
    return {t for t in re.findall(r"[a-z0-9_]{3,}", _normalizar(texto)) if t not in stop}


def _sobreposicao(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


def _idade(mente: Dict[str, Any], chave: str, padrao: float = 999999.0) -> float:
    try:
        ts = float(mente.get(chave) or 0.0)
        return max(0.0, time.time() - ts) if ts else padrao
    except Exception:
        return padrao


def _dominio_texto(texto: str) -> str:
    t = _normalizar(texto)
    mapas = {
        "iot": ("ventilador", "tomada", "lampada", "luz", "dispositivo"),
        "musica": ("musica", "playlist", "faixa", "som", "tocar"),
        "arquivo": ("arquivo", "pasta", "documento", "txt"),
        "app": ("app", "programa", "janela", "chrome", "opera", "steam"),
        "site": ("site", "pagina", "aba", "youtube", "google"),
    }
    for dominio, sinais in mapas.items():
        if any(re.search(rf"\b{re.escape(s)}\b", t) for s in sinais):
            return dominio
    return "conversa"


def selecionar_contexto_turno(
    texto_usuario: str,
    *,
    turno: Dict[str, Any] | None,
    mente: Dict[str, Any] | None,
    contexto_perceptivo: Dict[str, Any] | None = None,
    limite: int = 3,
) -> Dict[str, Any]:
    """Pontua fontes de contexto e devolve somente as justificadas."""
    turno = dict(turno or {})
    mente = dict(mente or {})
    ctx = dict(contexto_perceptivo or {})
    texto = str(texto_usuario or turno.get("texto") or "").strip()
    modalidade = str(turno.get("modalidade") or "conversa").lower()
    dominio_atual = _dominio_texto(str(turno.get("texto_operacional") or texto))
    referencia = bool(re.search(
        # P0_NAVEGADOR_SUBTIPO_V3_1_20260815
        r"\b(?:ele|ela|isso|esse|essa|dele|dela|anterior|de antes|como assim|o que aconteceu|tipo o que|e depois|"
        r"tem certeza|entao voce|então você|mas voce|mas você)\b",
        _normalizar(texto),
    ))
    novo_assunto = modalidade in {"conversa", "pergunta"} and not referencia and len(_tokens(texto)) >= 2

    # P0_ISOLAMENTO_CONTEXTO_20260814
    dominio_referencia = dominio_atual
    if referencia and dominio_atual == "conversa":
        continuidade = dict(mente.get("continuidade_geral") or {})
        ativo = str(continuidade.get("dominio_ativo") or "").strip().casefold()
        registro_ativo = dict(dict(continuidade.get("dominios") or {}).get(ativo) or {})
        try:
            idade_ativo = time.time() - float(registro_ativo.get("ts") or 0.0)
            expira_ativo = float(registro_ativo.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            idade_ativo, expira_ativo = 999999.0, 0.0
        if (
            ativo
            and registro_ativo.get("ativa", True) is not False
            and idade_ativo <= 300.0
            and (not expira_ativo or time.time() < expira_ativo)
        ):
            dominio_referencia = {
                "arquivos": "arquivo",
                "playlist_laylay": "musica",
            }.get(ativo, ativo)

    associacoes = [
        dict(item) for item in list(ctx.get("associacoes_continuidade") or [])[:3]
        if isinstance(item, dict)
    ]
    candidatos: list[ContextoCandidato] = []

    def adicionar(
        origem: str,
        dominio: str,
        conteudo: str,
        idade_s: float,
        relacao: str,
        base: float,
    ) -> None:
        conteudo = re.sub(r"\s+", " ", str(conteudo or "")).strip()
        if not conteudo:
            return
        overlap = _sobreposicao(texto, conteudo)
        recencia = 0.18 if idade_s <= 60 else 0.10 if idade_s <= 300 else 0.0
        if referencia:
            dominio_ok = (
                dominio == "conversa"
                or (dominio_referencia != "conversa" and dominio == dominio_referencia)
            )
        else:
            dominio_ok = (
                dominio in {"conversa", dominio_referencia}
                or dominio_referencia == "conversa"
            )
        score = base + recencia + min(0.25, overlap * 0.35)
        reforco_associativo = 0.0
        if referencia and modalidade != "comando" and associacoes:
            compatibilidades = [
                _sobreposicao(conteudo, str(item.get("rotulo") or ""))
                for item in associacoes
                if int(item.get("evidencias") or 0) >= 5
                and float(item.get("confianca") or 0.0) >= 0.65
            ]
            compatibilidade = max(compatibilidades, default=0.0)
            if compatibilidade >= 0.6:
                reforco_associativo = min(0.18, 0.12 + compatibilidade * 0.06)
                score += reforco_associativo
        if referencia and dominio_ok and dominio != "conversa":
            # O domínio ativo tipado é evidência positiva para a referência.
            score += 0.12
        if referencia and origem in {"ultima_fala", "pergunta_aberta", "promessa"}:
            score += 0.22
        if modalidade == "comando" and dominio != dominio_referencia and dominio != "conversa":
            score -= 0.35
        if novo_assunto and origem in {"topico_ativo", "foco_conversacional", "memoria_historica"}:
            score -= 0.45
        if not dominio_ok:
            score -= 0.30
        score = max(0.0, min(1.0, score))
        limiar = 0.52 if origem in {"pergunta_aberta", "promessa", "ultima_fala"} else 0.58
        aceito = score >= limiar and dominio_ok
        evidencia = (
            f"base={base:.2f}; recencia={recencia:.2f}; sobreposicao={overlap:.2f}; "
            f"dominio={'ok' if dominio_ok else 'incompativel'}; "
            f"turno={'novo' if novo_assunto else 'continuacao'}; "
            f"associacao={reforco_associativo:.2f}"
        )
        candidatos.append(ContextoCandidato(
            origem, dominio, conteudo[:500], idade_s, relacao,
            round(score, 3), aceito, evidencia,
        ))

    # A fala efetivamente entregue vence rótulos semânticos mais antigos.
    # Antes, uma afirmação velha podia ocultar uma explicação operacional
    # recém-falada e quebrar continuidades como "explica isso melhor".
    ultima_fala = str(mente.get("ultima_resposta") or "").strip() or " ".join(
        filter(None, [
            str(mente.get("ultima_afirmacao") or ""),
            str(mente.get("ultima_pergunta") or ""),
        ])
    )
    adicionar("ultima_fala", "conversa", ultima_fala, _idade(mente, "continuidade_fala_ts"), "fala_imediata", 0.40)
    adicionar("pergunta_aberta", "conversa", str(mente.get("pergunta_aberta_texto") or ""), _idade(mente, "pergunta_aberta_ts"), "resposta_esperada", 0.56)
    adicionar("promessa", "conversa", str(mente.get("ultima_promessa_texto") or ""), _idade(mente, "ultima_promessa_ts"), "divida_conversacional", 0.60)
    adicionar("topico_ativo", "conversa", str(ctx.get("topico_ativo") or ""), _idade(mente, "ultimo_topico_ts"), "topico_historico", 0.24)
    adicionar("foco_conversacional", "conversa", str(mente.get("foco_conversacional_topico") or ""), _idade(mente, "foco_conversacional_ts"), "foco", 0.28)

    for dominio, foco in dict(mente.get("focos_por_dominio") or {}).items():
        if not isinstance(foco, dict):
            continue
        alvo = str(foco.get("alvo") or foco.get("topico") or "")
        try:
            idade = max(0.0, time.time() - float(foco.get("ts") or 0.0))
        except Exception:
            idade = 999999.0
        adicionar(f"foco_{dominio}", str(dominio), alvo, idade, "referente_operacional", 0.38)

    ordenados = sorted(candidatos, key=lambda c: c.pontuacao, reverse=True)
    aceitos = [c for c in ordenados if c.aceito][:max(1, int(limite or 1))]
    influencia_associativa = any(
        "associacao=" in item.evidencia
        and "associacao=0.00" not in item.evidencia
        for item in aceitos
    )
    if influencia_associativa:
        registrar_influencia = ctx.get("registrar_influencia_associativa")
        if callable(registrar_influencia):
            try:
                registrar_influencia()
            except Exception:
                pass
    return {
        "dominio_atual": dominio_atual,
        "modalidade": modalidade,
        "referencia_contextual": referencia,
        "novo_assunto": novo_assunto,
        "influencia_associativa": influencia_associativa,
        "selecionados": [asdict(c) for c in aceitos],
        "rejeitados": [asdict(c) for c in ordenados if not c.aceito],
    }
