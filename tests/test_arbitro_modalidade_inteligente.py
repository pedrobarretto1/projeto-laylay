from __future__ import annotations

import unittest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.autonomia.pre_fluxo_contextual import (
    analisar_intencao_com_porteiro,
    processar_consulta_sistema_local,
)
from mente_laylay.autonomia.processamento_resposta_ia import filtrar_comandos_sem_pedido_atual
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.operacional import construir_parecer_operacional


class ArbitroModalidadeInteligenteTests(unittest.TestCase):
    def classificar(self, texto: str, *, confirmacao_valida: bool = False) -> dict:
        return classificar_modalidade_turno(
            texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao_valida,
        )

    def test_pergunta_de_conhecimento_nao_executa_acao_relacionada(self) -> None:
        turno = self.classificar("você já ouviu falar do GTA 6?")
        self.assertEqual(turno["modalidade_geral"], "pergunta")
        self.assertFalse(turno["autoriza_execucao"])
        self.assertEqual(turno["natureza_acao"], "capacidade")

    def test_comando_direto_autoriza_e_pergunta_instrucional_nao(self) -> None:
        comando = self.classificar("abre o YouTube")
        self.assertEqual(comando["modalidade_geral"], "comando")
        self.assertTrue(comando["autoriza_execucao"])

        instrucao = self.classificar("como abrir o YouTube?")
        self.assertEqual(instrucao["modalidade_geral"], "pergunta")
        self.assertFalse(instrucao["autoriza_execucao"])
        self.assertEqual(instrucao["natureza_acao"], "instrucao_ou_explicacao")

    def test_correcao_e_hipotese_nao_viram_comando_por_conter_verbo(self) -> None:
        for texto, modalidade in (
            ("eu não pedi para abrir o YouTube", "correcao"),
            ("estou pensando em abrir o YouTube", "deliberacao"),
            ("seria legal abrir o YouTube", "deliberacao"),
        ):
            with self.subTest(texto=texto):
                turno = self.classificar(texto)
                self.assertEqual(turno["modalidade_geral"], modalidade)
                self.assertFalse(turno["autoriza_execucao"])
                self.assertEqual(turno["texto_operacional"], "")

    def test_pedido_de_capacidade_ambiguo_pede_esclarecimento(self) -> None:
        ambiguo = self.classificar("você consegue abrir o YouTube?")
        self.assertEqual(ambiguo["modalidade_geral"], "pergunta")
        self.assertFalse(ambiguo["autoriza_execucao"])
        self.assertTrue(ambiguo["requer_esclarecimento"])

        pedido = self.classificar("você consegue abrir o YouTube para mim?")
        self.assertEqual(pedido["modalidade_geral"], "comando")
        self.assertTrue(pedido["autoriza_execucao"])

    def test_comando_sem_alvo_nao_e_executado(self) -> None:
        turno = self.classificar("abre")
        self.assertEqual(turno["modalidade_geral"], "comando")
        self.assertFalse(turno["autoriza_execucao"])
        self.assertTrue(turno["requer_esclarecimento"])

    def test_continuacao_aditiva_chega_ao_roteador_como_comando_contextual(self) -> None:
        turno = self.classificar("essa também")

        self.assertEqual(turno["modalidade_geral"], "comando")
        self.assertTrue(turno["autoriza_execucao"])
        self.assertTrue(turno["depende_contexto"])

    def test_turno_misto_separa_conversa_de_comando(self) -> None:
        turno = self.classificar("estou cansado, desliga a luz")
        self.assertEqual(turno["modalidade_geral"], "misto")
        self.assertEqual(turno["texto_conversacional"], "estou cansado")
        self.assertEqual(turno["texto_operacional"], "desliga a luz")
        self.assertTrue(turno["autoriza_execucao"])

    def test_resposta_social_nao_esconde_pergunta_em_nova_frase(self) -> None:
        turno = self.classificar("Eu estou bem também. Você gosta de Slipknot?")
        self.assertEqual(turno["modalidade_geral"], "misto")
        self.assertIn("slipknot", turno["texto_conversacional"].casefold())
        self.assertFalse(turno["autoriza_execucao"])

    def test_consultas_locais_e_controle_de_midia_sao_operacionais(self) -> None:
        for texto in (
            "qual o estado da lâmpada?",
            "quais programas estão abertos?",
            "quais são os meus emails?",
            "para a música",
            "volta a tocar",
            "deixa a luz mais clara",
        ):
            with self.subTest(texto=texto):
                turno = self.classificar(texto)
                self.assertEqual(turno["modalidade_geral"], "comando")
                self.assertTrue(turno["autoriza_execucao"])

    def test_lista_de_programas_vem_do_sistema_e_nao_da_llm(self) -> None:
        falas = []
        tratado, etapa = processar_consulta_sistema_local({
            "listar_programas_abertos": lambda: ["Steam", "Discord"],
            "falar_com_lipsync": lambda texto, *_: falas.append(texto),
        }, "quais programas estão abertos?")

        self.assertTrue(tratado)
        self.assertEqual(etapa, "consulta_programas_abertos")
        self.assertEqual(falas, ["Estão abertos agora: Steam, Discord."])

    def test_comandos_deterministicos_comuns_continuam_autorizados(self) -> None:
        for texto in (
            "pesquisa no Google sobre Python",
            "pula esse anúncio",
            "próxima música",
            "captura minha tela",
            "trava o computador",
            "volume máximo",
        ):
            with self.subTest(texto=texto):
                turno = self.classificar(texto)
                self.assertEqual(turno["modalidade_geral"], "comando")
                self.assertTrue(turno["autoriza_execucao"])

    def test_confirmacao_so_autoriza_com_pendencia_acionavel(self) -> None:
        solta = self.classificar("sim")
        vinculada = self.classificar("sim", confirmacao_valida=True)
        self.assertEqual(solta["modalidade"], "confirmacao")
        self.assertFalse(solta["autoriza_execucao"])
        self.assertTrue(vinculada["autoriza_execucao"])

    def test_especialista_operacional_respeita_decisao_unificada(self) -> None:
        pergunta = self.classificar("como abrir o YouTube?")
        parecer = construir_parecer_operacional(
            "como abrir o YouTube?",
            turno=pergunta,
            retrato={"operacao_explicita": "abrir_site"},
        )
        self.assertFalse(parecer["autoriza_execucao"])
        self.assertEqual(parecer["motivo_bloqueio"], "modalidade_nao_autorizada")

    def test_porteiro_nao_chama_analisador_em_turno_protegido(self) -> None:
        chamadas: list[str] = []
        turno = self.classificar("eu não pedi para abrir o YouTube")
        status, resultado = analisar_intencao_com_porteiro(
            {
                "mente_integrada_estado": {"turno_atual": turno},
                "_texto_tem_comando_explicito": texto_tem_comando_explicito,
                "_texto_social_curto": lambda _texto: False,
                "_texto_conversa_casual_sem_acao": lambda _texto: False,
                "_texto_conversa_contextual_sem_comando": lambda _texto: False,
                "analisar_intencao": lambda texto: chamadas.append(texto),
            },
            "eu não pedi para abrir o YouTube",
        )
        self.assertEqual(status, "evitar")
        self.assertIsNone(resultado)
        self.assertEqual(chamadas, [])

    def test_saida_final_da_ia_tambem_respeita_modalidade(self) -> None:
        comando = {"acao": "open_url", "url": "https://example.com"}
        permitidos, bloqueados = filtrar_comandos_sem_pedido_atual(
            "você consegue abrir o site?",
            [comando],
            tipo_interacao="acao",
        )
        self.assertEqual(permitidos, [])
        self.assertEqual(bloqueados, ["open_url"])


if __name__ == "__main__":
    unittest.main()
