# -*- coding: utf-8 -*-
"""Regressões puras da ponte P0.2A v3.2."""

from __future__ import annotations

import re
import time
import unicodedata
import unittest

from mente_laylay.memoria_mental.contexto_imediato import (
    ContextoImediatoRuntime,
    _dominio_restrito_referencia,
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)


def _normalizar(valor):
    base = unicodedata.normalize("NFKD", str(valor or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _estado_site():
    agora = time.time()
    return {
        "ts": agora,
        "ultima_acao_ts": agora,
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultima_acao_contrato": {
            "intent": "OPEN_URL",
            "dominio": "site",
            "executou": True,
            "confirmado": True,
            "alvo": "prime video",
        },
        "ultimo_site_aba": "prime video",
        "ultimo_app_janela": "opera",
        "continuidade_geral": {
            "dominio_ativo": "app",
            "dominios": {
                "app": {
                    "dominio": "app",
                    "intent": "APP_OPEN",
                    "alvo": "opera",
                    "params": {"nome_app": "opera"},
                    "status": "executado",
                    "ativa": True,
                    "ts": agora,
                    "expira_em": agora + 300.0,
                },
                "site": {
                    "dominio": "site",
                    "intent": "OPEN_URL",
                    "alvo": "prime video",
                    "params": {"alvo": "prime video"},
                    "status": "executado",
                    "ativa": True,
                    "ts": agora - 1.0,
                    "expira_em": agora + 300.0,
                },
            },
            "historico": [],
            "ts": agora,
        },
    }


class EstadoFalso:
    def __init__(self, mental):
        self.mental = mental

    def musica_get(self, _chave):
        return ""

    def substituir(self, _chave, valor):
        self.mental = valor


class P02ANavegadorV32Tests(unittest.TestCase):
    def test_dominio_da_frase_continua_site(self):
        self.assertEqual(
            _dominio_restrito_referencia(
                "Volta para a anterior.",
                _estado_site(),
                ttl_s=300.0,
            ),
            "site",
        )

    def test_ponte_resolve_referencia_site_para_anterior(self):
        estado = _estado_site()
        referencia = referencia_contextual_imediata(
            mente_integrada_estado=estado,
            foco_vivo={
                "habilidade": "janela",
                "alvo": "Opera",
                "ts": time.time(),
            },
            texto_atual="Volta para a anterior.",
            normalizar_texto=_normalizar,
            ttl_s=300.0,
        )
        self.assertEqual(referencia["tipo"], "site")
        self.assertEqual(referencia["alvo"], "prime video")

        comando = resolver_comando_acao_geral_contextual(
            "Volta para a anterior.",
            referencia,
        )
        self.assertIsInstance(comando, dict)
        self.assertEqual(comando["intent"], "SWITCH_PREVIOUS_TAB")

    def test_runtime_completo_materializa_switch_previous_tab(self):
        estado = EstadoFalso(_estado_site())
        runtime = ContextoImediatoRuntime(
            estado_runtime_getter=lambda: estado,
            servicos_iniciais={
                "_normalizar_texto_com_apelidos": _normalizar,
                "_alvo_corrigido_atual": lambda: "",
                "_registrar_alvo_corrigido": lambda _alvo: None,
                "falar_com_lipsync": lambda *_args, **_kwargs: None,
                "_contexto_musical_ativo": lambda: True,
                "_estrutura_arquivo_recente": lambda _ttl: {},
                "_foco_vivo_atual": lambda **_kwargs: {
                    "habilidade": "janela",
                    "alvo": "Opera",
                    "ts": time.time(),
                },
                "enviar_mensagem": None,
            },
            iot=None,
        )
        comando = runtime.resolver("Volta para a anterior.")
        self.assertIsInstance(comando, dict)
        self.assertEqual(comando["intent"], "SWITCH_PREVIOUS_TAB")
        self.assertEqual(comando.get("_dominio_contextual"), "site")

    def test_fecha_essa_permanece_site(self):
        estado = _estado_site()
        referencia = referencia_contextual_imediata(
            mente_integrada_estado=estado,
            foco_vivo={
                "habilidade": "janela",
                "alvo": "Opera",
                "ts": time.time(),
            },
            texto_atual="Fecha essa.",
            normalizar_texto=_normalizar,
            ttl_s=300.0,
        )
        self.assertEqual(referencia["tipo"], "site")
        comando = resolver_comando_acao_geral_contextual(
            "Fecha essa.",
            referencia,
        )
        self.assertEqual(comando["intent"], "CLOSE_TAB")


if __name__ == "__main__":
    unittest.main()
