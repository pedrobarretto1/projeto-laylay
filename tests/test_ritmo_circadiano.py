from __future__ import annotations

import unittest
from datetime import datetime

from mente_laylay.autonomia.sugestoes_sistema import (
    aplicar_preferencia_sugestao,
    processar_confirmacao_sugestao,
)
from mente_laylay.autonomia.fluxos_conversa import _parece_comando_novo
from mente_laylay.autonomia.pre_fluxo_contextual import processar_feedback_pendente
from mente_laylay.percepcao.ritmo_circadiano import (
    RitmoCircadianoRuntime,
    construir_contexto_temporal,
    detectar_consulta_horario,
    responder_consulta_horario,
)


def _considerar_presenca_aceita(eventos):
    def considerar(evento):
        eventos.append(dict(evento))
        return {
            "status": "proposta_cognitiva",
            "proposta_comunicativa": {
                "agendada": True,
                "autoriza_execucao": False,
            },
        }

    return considerar


class RitmoCircadianoTests(unittest.TestCase):
    def test_consulta_horario_usa_relogio_e_periodo_reais(self) -> None:
        self.assertTrue(detectar_consulta_horario("que horas são?"))
        self.assertTrue(detectar_consulta_horario("Lay, qual é a hora agora?"))
        self.assertFalse(detectar_consulta_horario("que horas o jogo começa?"))
        self.assertEqual(
            responder_consulta_horario(datetime(2026, 7, 22, 22, 47)),
            "São 22h47 agora. Já é noite por aqui.",
        )

    def test_periodos_e_fases_cobrem_o_dia_inteiro(self) -> None:
        casos = (
            (2, "madrugada", "noite_tardia", True),
            (6, "manha", "amanhecer", False),
            (10, "manha", "manha_ativa", False),
            (15, "tarde", "tarde", False),
            (19, "noite", "anoitecer", True),
            (22, "noite", "noite", True),
            (23, "noite", "noite_tardia", True),
        )
        for hora, periodo, fase, escuro in casos:
            with self.subTest(hora=hora):
                contexto = construir_contexto_temporal(datetime(2026, 7, 16, hora, 30))
                self.assertEqual(contexto["periodo"], periodo)
                self.assertEqual(contexto["fase"], fase)
                self.assertEqual(contexto["escuro_esperado"], escuro)

    def test_sugestao_so_vira_pendencia_depois_de_ser_falada(self) -> None:
        estado = {}
        continuidades = {"comando_sugerido_estado": "NONE"}
        agendadas = []

        runtime = RitmoCircadianoRuntime(
            estado_get=lambda: estado,
            estado_set=lambda novo: estado.update(novo),
            continuidades_get=lambda chave, padrao=None: continuidades.get(chave, padrao),
            continuidades_update=lambda **campos: continuidades.update(campos),
            considerar_presenca=_considerar_presenca_aceita(agendadas),
            interacao_iniciada=lambda: True,
            conversa_ativa=lambda: False,
            agora_cb=lambda: datetime(2026, 7, 16, 19, 10),
        )

        resultado = runtime.executar_ciclo()
        self.assertEqual(resultado["status"], "sugestao_agendada")
        self.assertEqual(continuidades["comando_sugerido_estado"], "NONE")
        self.assertEqual(agendadas[0]["acao_proposta"]["intent"], "TIME_LIGHT_ON")

        agendadas[0]["ao_concluir"](True, "entregue")
        self.assertEqual(continuidades["comando_sugerido"], "TIME_LIGHT_ON")
        self.assertEqual(continuidades["comando_sugerido_estado"], "PENDING_CONFIRM")
        self.assertEqual(estado["sugestoes_emitidas"]["luz_anoitecer"], "2026-07-16")

    def test_noite_tardia_recomenda_luz_e_volume_uma_vez_por_noite(self) -> None:
        estado = {}
        continuidades = {"comando_sugerido_estado": "NONE"}
        agendadas = []

        runtime = RitmoCircadianoRuntime(
            estado_get=lambda: estado,
            estado_set=lambda novo: estado.update(novo),
            continuidades_get=lambda chave, padrao=None: continuidades.get(chave, padrao),
            continuidades_update=lambda **campos: continuidades.update(campos),
            considerar_presenca=_considerar_presenca_aceita(agendadas),
            interacao_iniciada=lambda: True,
            conversa_ativa=lambda: False,
            agora_cb=lambda: datetime(2026, 7, 17, 0, 30),
        )
        runtime.executar_ciclo()
        self.assertEqual(agendadas[0]["acao_proposta"]["intent"], "TIME_WIND_DOWN")
        self.assertEqual(agendadas[0]["acao_proposta"]["params"]["volume"], 25)
        agendadas[0]["ao_concluir"](True, "entregue")
        self.assertEqual(estado["sugestoes_emitidas"]["modo_noite"], "2026-07-16")

        continuidades["comando_sugerido_estado"] = "NONE"
        self.assertEqual(runtime.executar_ciclo()["status"], "sem_sugestao")
        self.assertEqual(len(agendadas), 1)

    def test_confirmacao_temporal_chama_executor_especifico(self) -> None:
        agora = __import__("time").time()
        continuidades = {
            "comando_sugerido": "TIME_WIND_DOWN",
            "comando_sugerido_payload": {"alvo": "lampada_quarto", "volume": 25},
            "comando_sugerido_estado": "PENDING_CONFIRM",
            "comando_sugerido_ts": agora,
        }
        execucoes = []

        def resetar():
            continuidades["comando_sugerido_estado"] = "NONE"

        tratado = processar_confirmacao_sugestao(
            {
                "continuidades_get": lambda chave, padrao=None: continuidades.get(chave, padrao),
                "resetar_sugestao": resetar,
                "classificar_confirmacao_local": lambda _texto: True,
                "executar_sugestao_temporal": (
                    lambda comando, payload, texto: execucoes.append((comando, payload, texto))
                ),
            },
            "sim, pode fazer",
        )
        self.assertTrue(tratado)
        self.assertEqual(execucoes[0][0], "TIME_WIND_DOWN")
        self.assertEqual(execucoes[0][1]["volume"], 25)
        self.assertEqual(continuidades["comando_sugerido_estado"], "NONE")

    def test_contraproposta_substitui_acao_sem_executar_antes_da_confirmacao(self) -> None:
        agora = __import__("time").time()
        continuidades = {
            "comando_sugerido": "TIME_WIND_DOWN",
            "comando_sugerido_payload": {"alvo": "lampada_quarto", "volume": 25},
            "comando_sugerido_estado": "PENDING_CONFIRM",
            "comando_sugerido_ts": agora,
        }
        falas = []
        aprendidas = []
        executadas = []

        def resetar():
            continuidades.update({
                "comando_sugerido": None,
                "comando_sugerido_payload": None,
                "comando_sugerido_estado": "NONE",
            })

        contexto = {
            "continuidades_get": lambda chave, padrao=None: continuidades.get(chave, padrao),
            "continuidades_update": lambda **campos: continuidades.update(campos),
            "resetar_sugestao": resetar,
            "classificar_confirmacao_local": lambda texto: True if texto == "sim" else None,
            "interpretar_contraproposta": lambda *_args: {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ajustar_brilho",
                    "alvo": "lampada_quarto",
                    "valor": 50,
                },
            },
            "registrar_preferencia_sugestao": (
                lambda chave, registro: aprendidas.append((chave, registro))
            ),
            "falar": lambda texto, *_args: falas.append(texto),
            "executar_intencao": lambda intent, texto: executadas.append((intent, texto)) or True,
        }

        tratado = processar_confirmacao_sugestao(
            contexto,
            "é melhor apenas diminuir o brilho dela",
        )
        self.assertTrue(tratado)
        self.assertEqual(executadas, [])
        self.assertEqual(aprendidas[0][0], "TIME_WIND_DOWN")
        self.assertEqual(
            aprendidas[0][1]["alternativa"]["params"]["acao"],
            "ajustar_brilho",
        )
        self.assertEqual(continuidades["comando_sugerido"], "EXECUTE_INTENT")
        self.assertIn("Vou lembrar", falas[-1])
        self.assertIn("diminua o brilho", falas[-1])

        continuidades["comando_sugerido_ts"] = __import__("time").time()
        self.assertTrue(processar_confirmacao_sugestao(contexto, "sim"))
        self.assertEqual(len(executadas), 1)
        self.assertEqual(executadas[0][0]["intent"], "IOT_CONTROL")

    def test_preferencia_aprendida_reescreve_proxima_sugestao(self) -> None:
        preferencia = {
            "alternativa": {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ajustar_brilho",
                    "alvo": "lampada_quarto",
                    "valor": 50,
                },
            },
            "descricao": "diminuir o brilho da luz para 50 por cento",
            "fala_futura": "Já ficou tarde. Quer que eu diminua o brilho da luz para 50 por cento?",
        }
        comando, payload, fala = aplicar_preferencia_sugestao(
            "TIME_WIND_DOWN",
            {"alvo": "lampada_quarto", "volume": 25},
            "Quer que eu apague a luz e baixe o volume?",
            lambda _comando, _payload: preferencia,
        )
        self.assertEqual(comando, "EXECUTE_INTENT")
        self.assertEqual(payload["intent"]["params"]["acao"], "ajustar_brilho")
        self.assertNotIn("apague", fala.casefold())
        self.assertIn("brilho", fala.casefold())

    def test_contraproposta_operacional_tem_prioridade_sobre_comando_novo(self) -> None:
        texto = "é melhor apenas diminuir o volume"
        self.assertFalse(_parece_comando_novo(texto))
        chamadas = []
        tratado, etapa = processar_feedback_pendente(
            {
                "mente_integrada_estado": {"turno_atual": {"modalidade": "comando"}},
                "_handle_feedback_pendente_misto": lambda _texto: False,
                "_handle_feedback_pendente": lambda recebido: chamadas.append(recebido) or True,
            },
            texto,
        )
        self.assertTrue(tratado)
        self.assertEqual(etapa, "feedback_pendente")
        self.assertEqual(chamadas, [texto])


if __name__ == "__main__":
    unittest.main()
