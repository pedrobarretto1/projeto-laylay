from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.sugestoes_sistema import processar_confirmacao_sugestao
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime


class MotorAprendizadoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.memoria = MemoriaSQLite(os.path.join(self.temp.name, "memoria.sqlite"))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_evidencias_acumulam_confianca_sem_virar_certeza_imediata(self) -> None:
        primeira = self.memoria.registrar_evidencia_aprendizado(
            chave="rotina:22:vscode", tipo="rotina", escopo="horario:22:00",
            valor={"app": "VS Code", "descricao_humana": "costuma abrir VS Code às 22h"},
            sinal=1.0, origem="observacao_rotina", evidencia="primeiro dia",
        )
        segunda = self.memoria.registrar_evidencia_aprendizado(
            chave="rotina:22:vscode", tipo="rotina", escopo="horario:22:00",
            valor={"app": "VS Code", "descricao_humana": "costuma abrir VS Code às 22h"},
            sinal=1.0, origem="observacao_rotina", evidencia="segundo dia",
        )
        self.assertEqual(primeira["status"], "candidata")
        self.assertGreater(segunda["confianca"], primeira["confianca"])
        self.assertEqual(segunda["evidencias_positivas"], 2)

    def test_motor_recusa_aprender_da_propria_fala(self) -> None:
        resultado = self.memoria.registrar_evidencia_aprendizado(
            chave="preferencia:inventada", tipo="preferencia", escopo="geral",
            valor={"descricao_humana": "gosta de algo"}, sinal=1.0,
            origem="resposta_ia", evidencia="a própria Laylay afirmou",
        )
        self.assertIsNone(resultado)
        self.assertIsNone(self.memoria.obter_hipotese_aprendizado("preferencia:inventada"))

    def test_contraproposta_explicita_vira_hipotese_ativa_e_contradicao_e_contada(self) -> None:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=self.memoria,
            contexto_getter=lambda: {"periodo": "noite"},
            log=lambda *_args: None,
        )
        primeira = motor.registrar_contraproposta("TIME_WIND_DOWN", {
            "alternativa": {"intent": "IOT_CONTROL", "params": {"acao": "ajustar_brilho", "valor": 50}},
            "descricao": "diminuir o brilho para 50 por cento",
            "evidencia": "prefiro diminuir o brilho",
        })
        segunda = motor.registrar_contraproposta("TIME_WIND_DOWN", {
            "alternativa": {"intent": "IOT_CONTROL", "params": {"acao": "ajustar_brilho", "valor": 30}},
            "descricao": "diminuir o brilho para 30 por cento",
            "evidencia": "agora prefiro 30 por cento",
        })
        self.assertEqual(primeira["status"], "ativa")
        self.assertEqual(segunda["valor"]["alternativa"]["params"]["valor"], 30)
        self.assertEqual(segunda["contradicoes"], 1)

    def test_revisao_enfraquece_padrao_abandonado(self) -> None:
        self.memoria.registrar_evidencia_aprendizado(
            chave="padrao:antigo", tipo="padrao", escopo="geral",
            valor={"descricao_humana": "repete um padrão antigo"}, sinal=1.0,
            origem="observacao", evidencia="registro antigo",
        )
        antes = self.memoria.obter_hipotese_aprendizado("padrao:antigo")
        alteradas = self.memoria.revisar_hipoteses_aprendizado(
            agora=datetime.now() + timedelta(days=120),
            inatividade_dias=30,
        )
        depois = self.memoria.obter_hipotese_aprendizado("padrao:antigo")
        self.assertEqual(alteradas, 1)
        self.assertLess(depois["confianca"], antes["confianca"])

    def test_curiosidade_so_cria_pendencia_depois_da_fala(self) -> None:
        valor = {"descricao_humana": "costuma querer música de foco à tarde"}
        for evidencia in ("dia um", "dia dois"):
            self.memoria.registrar_evidencia_aprendizado(
                chave="rotina:foco:tarde", tipo="rotina", escopo="tarde",
                valor=valor, sinal=1.0, origem="observacao", evidencia=evidencia,
            )
        continuidades = {"comando_sugerido_estado": "NONE"}
        agendadas = []
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=self.memoria,
            contexto_getter=lambda: {"periodo": "tarde"},
            agendar_fala=lambda *args, **kwargs: agendadas.append((args, kwargs)) or True,
            continuidades_get=lambda chave, padrao=None: continuidades.get(chave, padrao),
            continuidades_update=lambda **campos: continuidades.update(campos),
            interacao_iniciada=lambda: True,
            conversa_ativa=lambda: False,
            log=lambda *_args: None,
        )
        resultado = motor.revisar_e_exercitar_curiosidade()
        self.assertEqual(resultado["curiosidade"], "agendada")
        self.assertEqual(continuidades["comando_sugerido_estado"], "NONE")
        agendadas[0][1]["ao_concluir"](True, "entregue")
        self.assertEqual(continuidades["comando_sugerido"], "LEARN_CONFIRM")

        falas = []
        continuidades["comando_sugerido_ts"] = __import__("time").time()
        tratado = processar_confirmacao_sugestao(
            {
                "continuidades_get": lambda chave, padrao=None: continuidades.get(chave, padrao),
                "resetar_sugestao": lambda: continuidades.update(comando_sugerido_estado="NONE"),
                "classificar_confirmacao_local": lambda _texto: True,
                "confirmar_hipotese_aprendizado": motor.confirmar_hipotese,
                "falar": lambda texto, *_args: falas.append(texto),
            },
            "sim",
        )
        self.assertTrue(tratado)
        hipotese = self.memoria.obter_hipotese_aprendizado("rotina:foco:tarde")
        self.assertEqual(hipotese["status"], "ativa")
        self.assertGreaterEqual(hipotese["confianca"], 0.9)

    def test_lacuna_so_vira_conhecimento_com_fonte_confiavel(self) -> None:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=self.memoria,
            contexto_getter=lambda: {"periodo": "tarde"},
            pesquisar_conhecimento=lambda tema: {
                "ok": True,
                "tema": tema,
                "titulo": "Obra verificada",
                "resumo": "Resumo factual fornecido por uma fonte identificada.",
                "fonte": "wikipedia_pt",
                "confianca": 0.95,
            },
            log=lambda *_args: None,
        )
        motor.observar_interacao(
            "o que é esta obra?",
            "Eu não tenho informação verificada suficiente sobre isso.",
        )
        resultado = motor.pesquisar_uma_lacuna()
        self.assertEqual(resultado["status"], "aprendido")
        lacuna = self.memoria.obter_hipotese_aprendizado("lacuna:o que e esta obra")
        self.assertEqual(lacuna["status"], "resolvida")
        conhecimentos = [
            item for item in self.memoria.listar_aprendizados_semanticos(limit=20)
            if item.get("tipo") == "conhecimento"
        ]
        self.assertEqual(len(conhecimentos), 1)
        self.assertEqual(conhecimentos[0]["origem"], "pesquisa_autonoma_wikipedia_pt")

    def test_resultado_fraco_nao_vira_conhecimento(self) -> None:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=self.memoria,
            contexto_getter=lambda: {},
            pesquisar_conhecimento=lambda _tema: {
                "ok": True, "resumo": "Rumor sem base", "fonte": "duckduckgo", "confianca": 0.4,
            },
            log=lambda *_args: None,
        )
        motor.observar_interacao("quem é personagem desconhecido?", "Não sei esse detalhe.")
        self.assertEqual(motor.pesquisar_uma_lacuna()["status"], "nao_verificada")
        self.assertFalse(any(
            item.get("tipo") == "conhecimento"
            for item in self.memoria.listar_aprendizados_semanticos(limit=20)
        ))

    def test_observacao_passiva_precisa_se_repetir_para_ganhar_forca(self) -> None:
        motor = MotorAprendizadoRuntime(
            memoria_sqlite=self.memoria,
            contexto_getter=lambda: {"periodo": "noite"},
            log=lambda *_args: None,
        )
        motor.registrar_observacao_rotina("VS Code", "Programação", "22:00")
        primeira = self.memoria.obter_hipotese_aprendizado("rotina_observada:22:00:vs code")
        self.assertEqual(primeira["status"], "candidata")
        for _ in range(9):
            motor.registrar_observacao_rotina("VS Code", "Programação", "22:00")
        madura = self.memoria.obter_hipotese_aprendizado("rotina_observada:22:00:vs code")
        self.assertGreater(madura["confianca"], primeira["confianca"])
        self.assertEqual(madura["status"], "ativa")


if __name__ == "__main__":
    unittest.main()
