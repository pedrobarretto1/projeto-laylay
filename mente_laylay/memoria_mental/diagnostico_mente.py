"""Retrato seguro e legível do funcionamento atual da mente única."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Mapping


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base.casefold()).strip()


def _codigo_seguro(valor: Any, limite: int = 96) -> str:
    texto = _normalizar(str(valor or ""))
    texto = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", texto)
    texto = re.sub(r"[^a-z0-9_.: -]+", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_.:-")[:limite]


def detectar_pedido_diagnostico_mente(texto: str) -> bool:
    """Aceita pedidos explícitos sem confundir conversa emocional com diagnóstico."""
    t = _normalizar(texto)
    if t in {"/diagnostico", "/diagnostico mente", "/status interno", "/status mente"}:
        return True
    expressoes = (
        "diagnostico da mente",
        "diagnostico interno",
        "status interno da laylay",
        "status dos modulos",
        "verifique seus modulos",
        "verifica seus modulos",
        "mostre seus modulos",
        "mostra seus modulos",
    )
    return any(expressao in t for expressao in expressoes)


def construir_diagnostico_mente(
    estado: Mapping[str, Any] | None,
    saude: Mapping[str, Any] | None,
) -> dict[str, Any]:
    dominios = dict(estado or {})
    mental = dict(dominios.get("mental") or {})
    conversa = dict(dominios.get("conversacional") or {})
    percepcao = dict(dominios.get("percepcao") or {})
    continuidades = dict(dominios.get("continuidades") or {})
    turno = dict(mental.get("turno_atual") or {})
    plano = dict(mental.get("plano_turno_atual") or {})
    modulos = {str(nome): dict(registro or {}) for nome, registro in dict(saude or {}).items()}
    totais = {"saudavel": 0, "degradado": 0, "indisponivel": 0}
    problemas = []
    for nome, registro in sorted(modulos.items()):
        status = str(registro.get("status") or "indisponivel")
        if status not in totais:
            status = "indisponivel"
        totais[status] += 1
        if status != "saudavel":
            problemas.append({
                "modulo": nome,
                "status": status,
                "ausentes": list(registro.get("ausentes") or []),
            })

    ultima_acao = {
        "intent": mental.get("ultima_acao_intent") or mental.get("ultima_intencao") or "",
        "alvo": mental.get("ultima_acao_alvo") or mental.get("ultimo_alvo") or "",
        "status": mental.get("ultima_acao_status") or "",
        "confirmado": mental.get("ultima_acao_confirmada"),
    }

    pendencias = sum(
        1
        for valor in continuidades.values()
        if bool(valor) and valor not in ({}, [], "", "NONE", "none")
    )
    contexto_sistema = dict(percepcao.get("contexto_sistema") or {})
    aba_ativa = dict(percepcao.get("aba_ativa") or {})
    metricas_brutas = dict(mental.get("diagnostico_metricas") or {})
    latencias = {}
    for nome, registro in metricas_brutas.items():
        if not isinstance(registro, Mapping):
            continue
        chave = _codigo_seguro(nome, 64)
        if not chave:
            continue
        latencias[chave] = {
            "ultimo_ms": round(float(registro.get("ultimo_ms") or 0.0), 2),
            "media_ms": round(float(registro.get("media_ms") or 0.0), 2),
            "max_ms": round(float(registro.get("max_ms") or 0.0), 2),
            "amostras": int(registro.get("amostras") or 0),
            "falhas": int(registro.get("falhas") or 0),
        }
    falhas = []
    for item in list(mental.get("diagnostico_falhas") or [])[-8:]:
        if not isinstance(item, Mapping):
            continue
        falhas.append({
            "componente": _codigo_seguro(item.get("componente"), 64),
            "codigo": _codigo_seguro(item.get("codigo"), 80),
            "tipo": _codigo_seguro(item.get("tipo"), 48),
        })
    decisoes = []
    for item in list(mental.get("diagnostico_decisoes") or [])[-8:]:
        if not isinstance(item, Mapping):
            continue
        decisoes.append({
            "componente": _codigo_seguro(item.get("componente"), 64),
            "acao": _codigo_seguro(item.get("acao"), 48),
            "categoria": _codigo_seguro(item.get("categoria"), 64),
            "motivos": [
                _codigo_seguro(motivo, 96)
                for motivo in list(item.get("motivos") or [])[:4]
                if _codigo_seguro(motivo, 96)
            ],
        })
    return {
        "saude": {**totais, "problemas": problemas},
        "interacao": {
            "emocao": conversa.get("current_emotion") or "calma",
            "nivel": int(conversa.get("emotion_level") or 1),
            "fala_reservada": bool(conversa.get("is_speaking", False)),
            "audio_reproduzindo": bool(conversa.get("audio_playing", False)),
            "modo_chat": bool(conversa.get("modo_chat", False)),
        },
        "turno": {
            "fase": plano.get("fase") or turno.get("fase") or "ocioso",
            "modalidade": turno.get("modalidade_geral") or turno.get("modalidade") or "",
            "autoriza_execucao": bool(turno.get("autoriza_execucao", False)),
            "erros": [_codigo_seguro(item) for item in list(plano.get("erros") or [])[:5]],
        },
        "ultima_acao": ultima_acao,
        "percepcao": {
            "janela": contexto_sistema.get("title") or contexto_sistema.get("exe") or "",
            "site": aba_ativa.get("url") or "",
        },
        "pendencias": pendencias,
        "latencias": latencias,
        "falhas_recentes": falhas,
        "decisoes_recentes": decisoes,
    }


def formatar_diagnostico_terminal(diagnostico: Mapping[str, Any]) -> str:
    saude = dict(diagnostico.get("saude") or {})
    interacao = dict(diagnostico.get("interacao") or {})
    turno = dict(diagnostico.get("turno") or {})
    acao = dict(diagnostico.get("ultima_acao") or {})
    problemas = list(saude.get("problemas") or [])
    latencias = dict(diagnostico.get("latencias") or {})
    falhas = list(diagnostico.get("falhas_recentes") or [])
    decisoes = list(diagnostico.get("decisoes_recentes") or [])
    linhas = [
        "🩺 [DIAGNÓSTICO:MENTE]",
        (
            f"  módulos: saudáveis={saude.get('saudavel', 0)} "
            f"degradados={saude.get('degradado', 0)} indisponíveis={saude.get('indisponivel', 0)}"
        ),
        (
            f"  interação: emoção={interacao.get('emocao')} nível={interacao.get('nivel')} "
            f"fala_reservada={interacao.get('fala_reservada')} áudio={interacao.get('audio_reproduzindo')}"
        ),
        (
            f"  turno: fase={turno.get('fase')} modalidade={turno.get('modalidade') or '-'} "
            f"execução_autorizada={turno.get('autoriza_execucao')}"
        ),
        (
            f"  última ação: intent={acao.get('intent') or '-'} alvo={acao.get('alvo') or '-'} "
            f"status={acao.get('status') or '-'} confirmada={acao.get('confirmado')}"
        ),
        f"  pendências contextuais: {diagnostico.get('pendencias', 0)}",
    ]
    if latencias:
        resumo_latencias = []
        for nome, metrica in sorted(latencias.items()):
            resumo_latencias.append(
                f"{nome}={float(metrica.get('ultimo_ms') or 0.0):.0f}ms"
                f" (média {float(metrica.get('media_ms') or 0.0):.0f}ms/{int(metrica.get('amostras') or 0)})"
            )
        linhas.append("  latências: " + " | ".join(resumo_latencias))
    if decisoes:
        ultima = decisoes[-1]
        motivos = ",".join(ultima.get("motivos") or []) or "sem_motivo"
        linhas.append(
            f"  decisão recente: {ultima.get('componente') or '-'}={ultima.get('acao') or '-'} "
            f"categoria={ultima.get('categoria') or '-'} motivo={motivos}"
        )
    linhas.append(f"  falhas técnicas recentes: {len(falhas)}")
    for falha in falhas[-5:]:
        linhas.append(
            f"  falha: {falha.get('componente') or '-'}={falha.get('codigo') or '-'} "
            f"tipo={falha.get('tipo') or '-'}"
        )
    for problema in problemas:
        ausentes = ",".join(problema.get("ausentes") or []) or "sem detalhe"
        linhas.append(f"  atenção: {problema.get('modulo')}={problema.get('status')} ({ausentes})")
    return "\n".join(linhas)


class DiagnosticoMenteRuntime:
    def __init__(
        self,
        *,
        estado_getter: Callable[[], Mapping[str, Any]],
        saude_getter: Callable[[], Mapping[str, Any]],
        falar: Callable[[str, str, int], Any],
        log: Callable[[str], Any] = print,
    ) -> None:
        self.estado_getter = estado_getter
        self.saude_getter = saude_getter
        self.falar = falar
        self.log = log

    def snapshot(self) -> dict[str, Any]:
        return construir_diagnostico_mente(self.estado_getter(), self.saude_getter())

    def mostrar(self) -> dict[str, Any]:
        diagnostico = self.snapshot()
        self.log(formatar_diagnostico_terminal(diagnostico))
        saude = dict(diagnostico.get("saude") or {})
        problemas = int(saude.get("degradado") or 0) + int(saude.get("indisponivel") or 0)
        falhas = len(diagnostico.get("falhas_recentes") or [])
        if problemas or falhas:
            partes = []
            if problemas:
                partes.append(f"{problemas} módulo{'s' if problemas != 1 else ''} pedindo atenção")
            if falhas:
                partes.append(f"{falhas} falha{'s' if falhas != 1 else ''} técnica{'s' if falhas != 1 else ''} recente{'s' if falhas != 1 else ''}")
            fala = f"Encontrei {' e '.join(partes)}. Deixei o diagnóstico seguro no terminal."
            emocao, nivel = "focada", 2
        else:
            fala = "Minha mente está conectada e os módulos auditados estão saudáveis. Deixei o retrato no terminal."
            emocao, nivel = "calma", 1
        self.falar(fala, emocao, nivel)
        return diagnostico


def criar_diagnostico_mente_runtime(**kwargs: Any) -> DiagnosticoMenteRuntime:
    return DiagnosticoMenteRuntime(**kwargs)
