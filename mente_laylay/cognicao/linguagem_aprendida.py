"""Linguagem aprendida da Laylay: apelidos, aliases e ensino leve."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any


APELIDOS_STOPWORDS = {
    "hoje", "amanha", "amanhã", "ontem", "agora", "depois", "antes",
    "segunda", "terca", "terça", "quarta", "quinta", "sexta", "sabado", "sábado", "domingo",
    "janeiro", "fevereiro", "marco", "março", "abril", "maio", "junho", "julho", "agosto",
    "setembro", "outubro", "novembro", "dezembro",
    "sim", "nao", "não", "talvez", "isso", "aquilo", "isto", "aqui", "ali", "lá",
    "eu", "voce", "você", "ele", "ela", "eles", "elas", "meu", "minha", "seu", "sua",
}


class LinguagemAprendidaRuntime:
    """Mantém a cognição de linguagem ensinada conectada à memória central."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        normalizar_texto: Callable[[str], str],
        texto_social_curto: Callable[[str], bool],
        falar: Callable[[str, str, int], Any],
        log: Callable[..., Any] = print,
    ) -> None:
        self.memoria_sqlite = memoria_sqlite
        self.normalizar_texto = normalizar_texto
        self.texto_social_curto = texto_social_curto
        self.falar = falar
        self.log = log
        self._apelidos_cache: dict[str, Any] = {"ts": 0.0, "mapa": {}}

    def carregar_apelidos(self, force: bool = False) -> dict:
        """Carrega apelidos aprendidos do banco e mantém cache leve em memória."""
        agora = time.time()
        cache = self._apelidos_cache
        if not force and cache.get("mapa") and agora - float(cache.get("ts") or 0.0) < 180:
            return dict(cache.get("mapa") or {})

        mapa = {}
        try:
            itens = self.memoria_sqlite.listar_aprendizados_semanticos(limit=300)
            for item in itens:
                if str(item.get("tipo") or "").strip().lower() not in {"apelido", "alias"}:
                    continue
                alias = self.normalizar_texto(item.get("gatilho") or "")
                alvo = str(item.get("valor") or "").strip()
                if not alias or not alvo:
                    continue
                alias_norm = self.normalizar_texto(alias)
                alvo_norm = self.normalizar_texto(alvo)
                if not alias_norm or not alvo_norm or alias_norm == alvo_norm:
                    continue
                mapa[alias_norm] = alvo
        except Exception as e:
            self.log(f"⚠️ [APELIDOS] falha ao carregar cache: {e}")

        self._apelidos_cache["ts"] = agora
        self._apelidos_cache["mapa"] = mapa
        return dict(mapa)

    def aplicar_apelidos(self, texto: str) -> str:
        t = str(texto or "").strip()
        if not t:
            return t
        mapa = self.carregar_apelidos()
        if not mapa:
            return t

        t_norm = self.normalizar_texto(t)
        for alias_norm, alvo in sorted(mapa.items(), key=lambda kv: len(kv[0]), reverse=True):
            alvo_norm = self.normalizar_texto(alvo)
            if not alias_norm or not alvo_norm:
                continue
            padrao = rf"\b{re.escape(alias_norm)}\b"
            t_norm = re.sub(padrao, alvo_norm, t_norm, flags=re.IGNORECASE)
        return t_norm

    def normalizar_com_apelidos(self, texto: str) -> str:
        return self.aplicar_apelidos(self.normalizar_texto(texto))

    def extrair_apelido_ensinavel(self, texto: str):
        bruto = str(texto or "").strip()
        if not bruto or "?" in bruto:
            return None
        t = self.normalizar_com_apelidos(bruto)
        if not t or len(t.split()) > 9:
            return None

        marcadores_ensino = [
            "apelido", "alias", "quer dizer", "significa", "vira",
            "chama", "chamado de", "pra voce", "pra você",
            "quando eu falar", "quando eu disser", "quero te ensinar",
        ]
        if not any(m in t for m in marcadores_ensino):
            return None

        padroes = [
            r"^(?:meu|minha|o|a|um|uma|esse|essa|esse aqui|essa aqui)?\s*(?:apelido|alias)\s+(?P<alias>.+?)\s+(?:e|eh|é|quer dizer|significa|vira|chama|chamado de|apelido de)\s+(?P<alvo>.+)$",
            r"^(?P<alias>.+?)\s+(?:quer dizer|significa|vira|chama|é chamado de|eh chamado de|apelido de)\s+(?P<alvo>.+)$",
            r"^(?:quando eu falar|quando eu disser)\s+(?P<alias>.+?)\s+(?:e|eh|é)\s+(?P<alvo>.+)$",
        ]
        for padrao in padroes:
            m = re.match(padrao, t, flags=re.IGNORECASE)
            if not m:
                continue
            tem_marcador_explicito = any(
                marcador in padrao
                for marcador in ("apelido", "alias", "quer dizer", "significa", "vira", "chama", "chamado de")
            )
            alias = self.normalizar_texto(m.group("alias") or "")
            alvo = self.normalizar_texto(m.group("alvo") or "")
            if not alias or not alvo:
                continue
            alias_tokens = alias.split()
            alvo_tokens = alvo.split()
            if len(alias_tokens) > 4 or len(alvo_tokens) > 6:
                continue
            if alias in APELIDOS_STOPWORDS or alvo in APELIDOS_STOPWORDS:
                continue
            if alias.startswith("playlist ") or alvo.startswith("playlist "):
                continue
            if not any(ch.isalpha() for ch in alias) or not any(ch.isalpha() for ch in alvo):
                continue
            if not tem_marcador_explicito and max(len(alias), len(alvo)) < 6:
                continue
            if len(alias_tokens) == len(alvo_tokens) and len(alias_tokens) > 1:
                continue
            if alias == alvo:
                continue
            return {"apelido": alias, "alvo": alvo, "texto": bruto}
        return None

    def aprender_apelido(self, alias: str, alvo: str, contexto: str = "") -> bool:
        alias_limpo = self.normalizar_texto(alias or "")
        alvo_limpo = self.normalizar_texto(alvo or "")
        if not alias_limpo or not alvo_limpo or alias_limpo == alvo_limpo:
            return False
        try:
            salvo = self.memoria_sqlite.salvar_aprendizado_semantico(
                tipo="apelido",
                gatilho=alias_limpo,
                valor=alvo_limpo,
                regra=f'Apelido "{alias_limpo}" aponta para "{alvo_limpo}".',
                texto_original=str(contexto or f"{alias_limpo} é {alvo_limpo}"),
                confianca=0.96,
            )
            self.carregar_apelidos(force=True)
            if salvo:
                self.log(f"🏷️ [APELIDO] '{alias_limpo}' aprendido como '{alvo_limpo}'")
                return True
        except Exception as e:
            self.log(f"⚠️ [APELIDO] falha ao salvar apelido: {e}")
        return False

    def processar_aprendizado_imediato(self, texto: str) -> bool:
        if self.texto_social_curto(texto):
            return False
        info = self.extrair_apelido_ensinavel(texto)
        if not info:
            return False
        alias = str(info.get("apelido") or "").strip()
        alvo = str(info.get("alvo") or "").strip()
        contexto = str(info.get("texto") or texto or "").strip()
        if not alias or not alvo:
            return False
        if self.aprender_apelido(alias, alvo, contexto):
            fala = f"Beleza, vou lembrar que {alias} é {alvo}."
            self.log(f"🏷️ [APELIDO] {fala}")
            self.falar(fala, "calma", 1)
            return True
        return False


def criar_linguagem_aprendida_runtime(**kwargs) -> LinguagemAprendidaRuntime:
    return LinguagemAprendidaRuntime(**kwargs)
