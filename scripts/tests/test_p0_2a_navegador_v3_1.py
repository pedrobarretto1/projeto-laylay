# -*- coding: utf-8 -*-
"""Regressões puras da P0.2A v3.1; nenhum executor real é chamado."""

from __future__ import annotations

import re
import time
import unicodedata
import unittest

from mente_laylay.autonomia.comandos_imediatos import (
    texto_referencia_tipificada_prioritaria,
)
from mente_laylay.autonomia.roteador_deterministico import (
    extrair_intencao_abrir_app,
)
from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno
from mente_laylay.memoria_mental.contexto_imediato import (
    _dominio_restrito_referencia,
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)


class P02ANavegadorV3Tests(unittest.TestCase):
    @staticmethod
    def _normalizar_teste(valor):
        base = unicodedata.normalize(
            "NFKD", str(valor or "").casefold()
        )
        sem_acentos = "".join(
            ch for ch in base if not unicodedata.combining(ch)
        )
        sem_pontuacao = re.sub(r"[^a-z0-9\s]", " ", sem_acentos)
        return re.sub(r"\s+", " ", sem_pontuacao).strip()

    def _estado_site_com_percepcao_app(self):
        agora = time.time()
        return {
            "ultima_acao_ts": agora,
            "ultima_acao_contrato": {
                "intent": "OPEN_URL",
                "dominio": "site",
                "executou": True,
                "confirmado": True,
                "alvo": "prime video",
            },
            "continuidade_geral": {
                "dominio_ativo": "app",
                "dominios": {
                    "app": {
                        "ativa": True,
                        "ts": agora,
                        "expira_em": agora + 300.0,
                    },
                    "site": {
                        "ativa": True,
                        "ts": agora - 1.0,
                        "expira_em": agora + 300.0,
                    },
                },
            },
        }

    def test_contrato_web_confirmado_vence_janela_fisica_em_deitico(self):
        estado = self._estado_site_com_percepcao_app()
        self.assertEqual(
            _dominio_restrito_referencia("Fecha essa.", estado),
            "site",
        )
        self.assertEqual(
            _dominio_restrito_referencia("Volta para a anterior.", estado),
            "site",
        )

    def test_alvo_app_explicito_continua_vencendo_contrato_web(self):
        estado = self._estado_site_com_percepcao_app()
        self.assertEqual(
            _dominio_restrito_referencia("Fecha o Opera.", estado),
            "app",
        )

    def test_resolvedor_site_materializa_operacoes_de_aba(self):
        contexto = {
            "tipo": "site",
            "alvo": "prime video",
            "intencao": "OPEN_URL",
            "params": {"alvo": "prime video"},
        }
        anterior = resolver_comando_acao_geral_contextual(
            "Volta para a anterior.",
            contexto,
        )
        fechar = resolver_comando_acao_geral_contextual(
            "Fecha essa.",
            contexto,
        )
        self.assertEqual(anterior["intent"], "SWITCH_PREVIOUS_TAB")
        self.assertEqual(fechar["intent"], "CLOSE_TAB")
        self.assertEqual(fechar["params"]["alvo"], "prime video")

    def test_troca_observada_vira_referente_do_fecha_essa(self):
        agora = time.time()
        rotulo_observado = "Wikipédia — pt.wikipedia.org"
        estado = {
            "ts": agora,
            "ultima_acao_ts": agora,
            "ultima_acao_intent": "SWITCH_PREVIOUS_TAB",
            "ultima_intencao": "SWITCH_PREVIOUS_TAB",
            "ultima_acao_params": {"referencia_contextual": True},
            "ultima_acao_promovivel": True,
            "ultima_acao_contrato": {
                "intent": "SWITCH_PREVIOUS_TAB",
                "dominio": "site",
                "executou": True,
                "confirmado": True,
                "alvo": rotulo_observado,
            },
            # Mantém um site antigo e uma janela física concorrentes de
            # propósito: o contrato observado da troca deve vencer ambos.
            "ultimo_site_aba": "prime video",
            "ultimo_app_janela": "opera",
        }
        referencia = referencia_contextual_imediata(
            mente_integrada_estado=estado,
            foco_vivo={
                "habilidade": "janela",
                "alvo": "Opera",
                "ts": agora,
            },
            texto_atual="Fecha essa.",
            normalizar_texto=self._normalizar_teste,
        )
        self.assertEqual(referencia["tipo"], "site")
        self.assertEqual(referencia["alvo"], rotulo_observado)

        fechamento = resolver_comando_acao_geral_contextual(
            "Fecha essa.",
            referencia,
        )
        self.assertEqual(fechamento["intent"], "CLOSE_TAB")
        self.assertEqual(fechamento["params"]["alvo"], rotulo_observado)

    def test_porta_prioritaria_reconhece_volta_anterior(self):
        self.assertTrue(
            texto_referencia_tipificada_prioritaria("Volta para a anterior.")
        )
        self.assertTrue(
            texto_referencia_tipificada_prioritaria("Fecha essa.")
        )
        self.assertFalse(
            texto_referencia_tipificada_prioritaria("A anterior era melhor.")
        )

    def test_repeticao_nao_vira_parte_do_nome_do_site(self):
        normalizar = self._normalizar_teste
        limpar = lambda valor: str(valor or "").strip()
        sites = {
            "wikipedia": "https://pt.wikipedia.org/",
            "prime video": "https://www.primevideo.com/",
        }
        apps = {
            "opera": "opera.exe",
            "calculadora": "calc.exe",
        }

        casos = {
            "Abre a Wikipédia de novo.": ("OPEN_URL", "wikipedia"),
            "Abre o Prime Video novamente.": ("OPEN_URL", "prime video"),
            "Abre o Opera de novo.": ("APP_OPEN", "opera"),
            "Abre a Calculadora outra vez.": ("APP_OPEN", "calculadora"),
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                resultado = extrair_intencao_abrir_app(
                    texto,
                    normalizar_texto=normalizar,
                    limpar_destino=limpar,
                    apps_map=apps,
                    sites_diretos=sites,
                )
                self.assertIsInstance(resultado, dict)
                self.assertEqual(resultado["intent"], esperado[0])
                params = resultado["params"]
                alvo = params.get("alvo") or params.get("nome_app")
                self.assertEqual(alvo, esperado[1])

    def test_repeticao_sem_alvo_nao_inventa_app(self):
        for texto in (
            "Abre de novo.",
            "Abre novamente.",
            "Abre outra vez.",
        ):
            with self.subTest(texto=texto):
                resultado = extrair_intencao_abrir_app(
                    texto,
                    normalizar_texto=self._normalizar_teste,
                    limpar_destino=lambda valor: str(valor or "").strip(),
                    apps_map={"opera": "opera.exe"},
                    sites_diretos={"wikipedia": "https://pt.wikipedia.org/"},
                )
                self.assertIsNone(resultado)

    def test_seletor_central_trata_anterior_como_referencia(self):
        agora = time.time()
        mente = {
            "continuidade_geral": {
                "dominio_ativo": "site",
                "dominios": {
                    "site": {
                        "ativa": True,
                        "ts": agora,
                        "expira_em": agora + 300.0,
                    }
                },
            },
            "focos_por_dominio": {
                "site": {
                    "alvo": "prime video",
                    "topico": "prime video",
                    "ts": agora,
                }
            },
        }
        resultado = selecionar_contexto_turno(
            "Volta para a anterior.",
            turno={
                "texto_operacional": "volta para a anterior",
                "modalidade": "comando",
            },
            mente=mente,
            contexto_perceptivo={},
        )
        self.assertTrue(resultado["referencia_contextual"])


if __name__ == "__main__":
    unittest.main()
