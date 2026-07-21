"""Política central para falas espontâneas sem interromper o usuário."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Callable, Dict


_BASE_UTILIDADE = {
    "alarme": 100,
    "lembrete": 92,
    "seguranca": 90,
    "erro_critico": 86,
    "briefing": 72,
    "abertura": 70,
    "horario": 56,
    "emails": 48,
    "rotina": 44,
    "musica": 38,
    "contexto_janela": 32,
    "observacao": 30,
}
_FUNCOES_SENSIVEIS = {
    "frustracao", "decepcao", "desabafo", "tristeza", "correcao", "encerramento",
}
_TIPOS_PRIORITARIOS = {"alarme", "seguranca", "erro_critico"}
_INTERVALO_BASE_S = {
    "lembrete": 300.0,
    "briefing": 14400.0,
    "abertura": 3600.0,
    "horario": 1800.0,
    "emails": 1800.0,
    "rotina": 2400.0,
    "musica": 1800.0,
    "contexto_janela": 1200.0,
    "observacao": 1200.0,
    "aprendizado": 1800.0,
}
_INTERVALO_MAX_S = 86400.0


def categoria_sugestao(comando: str, payload: Dict[str, Any] | None = None) -> str:
    """Traduz sugestões operacionais para as categorias usadas pelo porteiro."""
    nome = str(comando or "").strip().upper()
    dados = dict(payload or {})
    if nome.startswith("TIME_"):
        return "horario"
    if nome in {"SYS_MODE_CODE", "SYS_MODE_GAMER", "SYS_ORGANIZE_DOWNLOADS"}:
        return "rotina"
    if nome in {"EXPLAIN_ERROR", "RELOAD_PAGE", "OPEN_SITE_ALT"}:
        return "contexto_janela"
    if nome.startswith("LEARN_"):
        return "aprendizado"
    if nome == "EXECUTE_INTENT":
        interna = dados.get("intent") if isinstance(dados.get("intent"), dict) else {}
        intent = str(interna.get("intent") or "").strip().upper()
        if "MUSIC" in intent or "PLAYLIST" in intent or "MEDIA" in intent:
            return "musica"
        if "EMAIL" in intent:
            return "emails"
        if intent in {"IOT_CONTROL", "VOLUME", "APP_OPEN"}:
            return "rotina"
        if intent in {"OPEN_URL", "RESUMIR_PAGINA"}:
            return "contexto_janela"
    return str(comando or "observacao").strip().lower() or "observacao"


def _assinatura(tipo: str, texto: str) -> str:
    normalizado = re.sub(r"[^a-z0-9áàâãéêíóôõúç]+", " ", str(texto or "").casefold())
    palavras = " ".join(normalizado.split()[:18])
    return f"{str(tipo or '').strip().lower()}:{palavras}"


class PorteiroProatividadeRuntime:
    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        agora: Callable[[], float] = time.time,
        janela_repeticao_s: float = 600.0,
        validade_s: float = 180.0,
        perfil_getter: Callable[[], Dict[str, Any]] | None = None,
        perfil_setter: Callable[[Dict[str, Any]], Any] | None = None,
        registrar_decisao_cb: Callable[..., Any] | None = None,
    ) -> None:
        self._contexto_getter = contexto_getter
        self._agora = agora
        self.janela_repeticao_s = float(janela_repeticao_s)
        self.validade_s = float(validade_s)
        self._perfil_getter = perfil_getter
        self._perfil_setter = perfil_setter
        self._registrar_decisao_cb = registrar_decisao_cb
        self._historico: dict[str, float] = {}
        self._perfil_local: dict[str, Any] = {}
        self._lock = threading.Lock()

    def _contexto(self) -> Dict[str, Any]:
        try:
            valor = self._contexto_getter() or {}
            return valor if isinstance(valor, dict) else {}
        except Exception:
            return {}

    def _perfil(self) -> Dict[str, Any]:
        try:
            valor = self._perfil_getter() if callable(self._perfil_getter) else self._perfil_local
            return dict(valor) if isinstance(valor, dict) else {}
        except Exception:
            return dict(self._perfil_local)

    def _salvar_perfil(self, perfil: Dict[str, Any]) -> None:
        copia = dict(perfil or {})
        self._perfil_local = copia
        if callable(self._perfil_setter):
            try:
                self._perfil_setter(copia)
            except Exception:
                pass

    def registrar_feedback(
        self,
        tipo: str,
        aceito: bool,
        *,
        comando: str = "",
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Aprende a tolerância por categoria sem transformar uma recusa em regra eterna."""
        categoria = categoria_sugestao(comando, payload) if comando else str(tipo or "observacao").strip().lower()
        if categoria in _TIPOS_PRIORITARIOS:
            return {}
        agora = float(self._agora())
        with self._lock:
            perfil = self._perfil()
            registro = dict(perfil.get(categoria) or {})
            registro["feedbacks"] = int(registro.get("feedbacks") or 0) + 1
            registro["ultima_resposta_ts"] = agora
            if bool(aceito):
                registro["aceitas"] = int(registro.get("aceitas") or 0) + 1
                registro["recusas_consecutivas"] = max(
                    0, int(registro.get("recusas_consecutivas") or 0) - 1,
                )
                registro["ultima_aceitacao_ts"] = agora
            else:
                registro["recusas"] = int(registro.get("recusas") or 0) + 1
                registro["recusas_consecutivas"] = min(
                    8, int(registro.get("recusas_consecutivas") or 0) + 1,
                )
                registro["ultima_recusa_ts"] = agora
            base = float(_INTERVALO_BASE_S.get(categoria, 1200.0))
            sequencia = int(registro.get("recusas_consecutivas") or 0)
            registro["intervalo_s"] = min(_INTERVALO_MAX_S, base * (2 ** sequencia))
            perfil[categoria] = registro
            self._salvar_perfil(perfil)
            return dict(registro)

    def perfil_atual(self) -> Dict[str, Any]:
        with self._lock:
            return self._perfil()

    def _registrar_decisao(self, tipo: str, decisao: Dict[str, Any]) -> None:
        acao = str(decisao.get("acao") or "")
        if acao not in {"adiar", "descartar"} or not callable(self._registrar_decisao_cb):
            return
        try:
            self._registrar_decisao_cb(
                "proatividade", acao, decisao.get("motivos") or (), categoria=tipo,
            )
        except Exception:
            pass

    @staticmethod
    def _atividade_contextual(contexto: Dict[str, Any]) -> tuple[bool, bool, bool]:
        modo_jogo = bool(contexto.get("modo_jogo") or contexto.get("modo_jogo_ativo"))
        modo_foco = bool(contexto.get("modo_foco") or contexto.get("foco_ativo"))
        atividade = " ".join(str(contexto.get(chave) or "") for chave in (
            "atividade", "assunto", "titulo_janela", "funcao_comunicativa",
        )).casefold()
        reuniao = bool(contexto.get("reuniao_ativa")) or bool(re.search(
            r"\b(?:reuni[aã]o|videoconfer[eê]ncia|meeting|google meet|microsoft teams|zoom)\b",
            atividade,
        ))
        if re.search(r"\b(?:programa[cç][aã]o|estudo|escrita|trabalho focado|modo foco)\b", atividade):
            modo_foco = True
        return modo_jogo, reuniao, modo_foco

    def avaliar(
        self,
        *,
        tipo: str,
        texto: str,
        turno_ativo: bool = False,
        mesclar_turno: bool = False,
        inicio_forcado: bool = False,
        ultima_fala_normal_ts: float = 0.0,
    ) -> Dict[str, Any]:
        agora = self._agora()
        tipo_norm = str(tipo or "").strip().lower() or "observacao"
        contexto = self._contexto()
        if inicio_forcado:
            return {
                "acao": "emitir", "pontuacao": 100,
                "motivos": ["fala inicial explicitamente forçada"],
                "adiar_s": 0.0, "validade_s": self.validade_s,
            }

        pontos = int(_BASE_UTILIDADE.get(tipo_norm, 34))
        motivos = [f"utilidade base {pontos}"]
        prioritario = tipo_norm in _TIPOS_PRIORITARIOS
        assinatura = _assinatura(tipo_norm, texto)
        with self._lock:
            self._historico = {
                chave: ts for chave, ts in self._historico.items()
                if agora - float(ts or 0.0) <= self.janela_repeticao_s
            }
            repetida = assinatura in self._historico
        if repetida and not prioritario:
            decisao = {
                "acao": "descartar", "pontuacao": max(0, pontos - 55),
                "motivos": [*motivos, "sugestão equivalente já apareceu recentemente"],
                "adiar_s": 0.0, "validade_s": self.validade_s,
            }
            self._registrar_decisao(tipo_norm, decisao)
            return decisao

        if not prioritario:
            with self._lock:
                registro = dict(self._perfil().get(tipo_norm) or {})
            ultima_emissao = float(registro.get("ultima_emissao_ts") or 0.0)
            ultima_recusa = float(registro.get("ultima_recusa_ts") or 0.0)
            referencia = max(ultima_emissao, ultima_recusa)
            intervalo = float(registro.get("intervalo_s") or _INTERVALO_BASE_S.get(tipo_norm, 0.0))
            restante = intervalo - (agora - referencia) if referencia else 0.0
            if restante > 0.0:
                decisao = {
                    "acao": "descartar", "pontuacao": max(0, pontos - 35),
                    "motivos": [*motivos, f"intervalo adaptativo de {int(intervalo)} segundos ainda ativo"],
                    "adiar_s": round(restante, 2), "validade_s": self.validade_s,
                }
                self._registrar_decisao(tipo_norm, decisao)
                return decisao

        modo_chat = bool(contexto.get("modo_chat"))
        conversa_ativa = bool(contexto.get("conversa_ativa"))
        funcao = str(contexto.get("funcao_comunicativa") or "").strip().lower()
        ultima_entrada_ts = float(contexto.get("ultima_entrada_ts") or 0.0)
        idade_entrada = agora - ultima_entrada_ts if ultima_entrada_ts else 9999.0
        idade_fala = agora - float(ultima_fala_normal_ts or 0.0) if ultima_fala_normal_ts else 9999.0

        modo_jogo, reuniao_ativa, modo_foco = self._atividade_contextual(contexto)

        if turno_ativo and not prioritario:
            pontos -= 48
            motivos.append("resposta do usuário ainda está sendo construída")
        if (modo_chat or conversa_ativa) and not prioritario:
            pontos -= 35
            motivos.append("conversa ativa")
        if idade_entrada < 30.0 and not prioritario:
            pontos -= 28
            motivos.append("entrada recente do usuário")
        if idade_fala < 30.0 and not prioritario:
            pontos -= 24
            motivos.append("Laylay acabou de falar")
        if funcao in _FUNCOES_SENSIVEIS and not prioritario:
            pontos -= 45
            motivos.append(f"momento sensível: {funcao}")
        if modo_jogo and not prioritario:
            pontos -= 55
            motivos.append("jogo em andamento")
        if reuniao_ativa and not prioritario:
            pontos -= 65
            motivos.append("reunião em andamento")
        if modo_foco and not prioritario:
            pontos -= 40
            motivos.append("momento de foco")

        urgente = tipo_norm in {"alarme", "lembrete", "seguranca", "erro_critico"}
        if turno_ativo:
            if urgente and mesclar_turno and pontos >= 35:
                acao = "mesclar"
                adiar_s = 0.0
            else:
                acao = "adiar"
                adiar_s = 10.0
        elif (modo_chat or conversa_ativa or idade_entrada < 30.0 or idade_fala < 30.0) and not prioritario:
            acao = "adiar" if urgente or pontos >= 0 else "descartar"
            adiar_s = max(8.0, min(30.0, 30.0 - min(idade_entrada, idade_fala)))
        elif (modo_jogo or reuniao_ativa or modo_foco) and not prioritario:
            acao = "adiar" if urgente or pontos >= 30 else "descartar"
            adiar_s = 30.0 if acao == "adiar" else 0.0
        elif pontos >= 60:
            acao = "emitir"
            adiar_s = 0.0
        elif pontos >= 30:
            acao = "adiar"
            adiar_s = 8.0
        else:
            acao = "descartar"
            adiar_s = 0.0

        if acao in {"emitir", "mesclar"}:
            with self._lock:
                self._historico[assinatura] = agora
                if not prioritario:
                    perfil = self._perfil()
                    registro = dict(perfil.get(tipo_norm) or {})
                    registro["exibidas"] = int(registro.get("exibidas") or 0) + 1
                    registro["ultima_emissao_ts"] = agora
                    registro.setdefault(
                        "intervalo_s", float(_INTERVALO_BASE_S.get(tipo_norm, 0.0)),
                    )
                    perfil[tipo_norm] = registro
                    self._salvar_perfil(perfil)
        decisao = {
            "acao": acao,
            "pontuacao": max(0, min(100, pontos)),
            "motivos": motivos,
            "adiar_s": round(float(adiar_s), 2),
            "validade_s": self.validade_s,
        }
        self._registrar_decisao(tipo_norm, decisao)
        return decisao


def criar_porteiro_proatividade_runtime(**kwargs: Any) -> PorteiroProatividadeRuntime:
    return PorteiroProatividadeRuntime(**kwargs)
