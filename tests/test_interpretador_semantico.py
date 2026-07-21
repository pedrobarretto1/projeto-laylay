import json
import threading
import unittest

from mente_laylay.cognicao.interpretador_semantico_runtime import (
    InterpretadorSemanticoRuntime,
)
from mente_laylay.cognicao.leitura_semantica_turno import (
    aplicar_leitura_conversacional,
    comparar_com_legado,
    normalizar_leitura_semantica,
)
from mente_laylay.autonomia.pre_fluxo_contextual import turno_tem_pergunta_nova_apos_trecho_social
from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_da_ia
from mente_laylay.autonomia.contexto_resposta_ia import criar_contexto_prompt_runtime
from mente_laylay.cognicao.orquestrador_turno_runtime import registrar_leitura_semantica_principal
from mente_laylay.personalidade.conversa_natural import classificar_conversa_curta_local


class LeituraSemanticaContratoTests(unittest.TestCase):
    def test_normaliza_turno_misto_sem_autorizar_execucao(self):
        leitura = normalizar_leitura_semantica(
            {
                "atos": [
                    {"tipo": "resposta_social", "conteudo": "estou bem", "confianca": 1.7},
                    {"tipo": "pergunta_opiniao", "tema": "Slipknot", "confianca": 0.91},
                ],
                "modalidade_geral": "misto",
                "operacional": {"pedido_real": True, "autoriza_execucao": True},
                "confianca": 2,
            },
            texto="estou bem, você gosta de Slipknot?",
        )

        self.assertTrue(leitura["valida"])
        self.assertEqual([ato["tipo"] for ato in leitura["atos"]], ["resposta_social", "pergunta_opiniao"])
        self.assertEqual(leitura["modalidade_geral"], "misto")
        self.assertEqual(leitura["confianca"], 1.0)
        self.assertFalse(leitura["operacional"]["autoriza_execucao"])
        self.assertTrue(leitura["somente_observacao"])

    def test_descarta_payload_malformado(self):
        self.assertEqual(normalizar_leitura_semantica([], texto="oi"), {})

    def test_comparacao_apenas_registra_divergencia(self):
        leitura = normalizar_leitura_semantica(
            {
                "atos": [{"tipo": "pergunta", "conteudo": "como funciona?"}],
                "modalidade_geral": "pergunta",
                "operacional": {"pedido_real": False},
                "confianca": 0.9,
            },
            texto="como funciona?",
        )
        comparacao = comparar_com_legado(
            leitura,
            {"modalidade": "comando", "autoriza_execucao": True},
        )
        self.assertTrue(comparacao["divergiu"])
        self.assertIn("modalidade", comparacao["divergencias"])
        self.assertIn("sinal_operacional", comparacao["divergencias"])

    def test_adaptador_marca_dois_atos_e_preserva_bloqueio_operacional(self):
        leitura = normalizar_leitura_semantica(
            {
                "atos": [
                    {"tipo": "resposta_social", "conteudo": "estou bem", "confianca": 0.96},
                    {"tipo": "pergunta_opiniao", "conteudo": "você gosta?", "tema": "Slipknot", "confianca": 0.95},
                ],
                "modalidade_geral": "misto",
                "ato_principal": "pergunta_opiniao",
                "operacional": {"pedido_real": False},
                "confianca": 0.96,
            },
            texto="estou bem, você gosta de Slipknot?",
        )
        turno = aplicar_leitura_conversacional(
            {"id": 10, "modalidade": "conversa", "autoriza_execucao": False},
            leitura,
        )
        self.assertEqual(turno["modalidade_geral"], "misto")
        self.assertFalse(turno["autoriza_execucao"])
        self.assertEqual(len(turno["segmentos"]), 2)
        self.assertTrue(turno_tem_pergunta_nova_apos_trecho_social(
            {"mente_integrada_estado": {"turno_atual": turno}},
            "estou bem, você gosta de Slipknot?",
        ))

    def test_adaptador_nunca_sobrescreve_comando_legado(self):
        leitura = normalizar_leitura_semantica(
            {
                "atos": [{"tipo": "pergunta", "conteudo": "abre?"}],
                "modalidade_geral": "pergunta",
                "operacional": {"pedido_real": False},
                "confianca": 0.99,
            },
            texto="abre o Opera",
        )
        legado = {"modalidade": "comando", "autoriza_execucao": True, "acao_explicita": True}
        self.assertEqual(aplicar_leitura_conversacional(legado, leitura), legado)

    def test_ato_social_semantico_tem_precedencia_sobre_palavra_solta(self):
        leitura = normalizar_leitura_semantica(
            {
                "atos": [{"tipo": "resposta_social", "conteudo": "tá tudo bem por aqui", "confianca": 0.97}],
                "modalidade_geral": "conversa",
                "operacional": {"pedido_real": False},
                "confianca": 0.97,
            },
            texto="tá tudo bem por aqui",
        )
        turno = aplicar_leitura_conversacional(
            {"modalidade": "conversa", "autoriza_execucao": False},
            leitura,
        )
        resultado = classificar_conversa_curta_local(
            {
                "mente_integrada_estado": {"turno_atual": turno},
                "normalizar_texto": lambda texto: texto.casefold(),
            },
            "tá tudo bem por aqui",
        )
        self.assertEqual(resultado["tipo"], "WELLBEING_REPLY")
        self.assertEqual(resultado["origem"], "leitura_semantica")

    def test_leitura_com_pedido_de_acao_nao_e_aplicada_na_conversa(self):
        leitura = normalizar_leitura_semantica(
            {
                "atos": [{"tipo": "pedido_acao", "conteudo": "apague a luz"}],
                "modalidade_geral": "comando",
                "operacional": {"pedido_real": True, "intent_candidato": "IOT_CONTROL"},
                "confianca": 0.98,
            },
            texto="apague a luz",
        )
        legado = {"modalidade": "conversa", "autoriza_execucao": False}
        self.assertEqual(aplicar_leitura_conversacional(legado, leitura), legado)

    def test_extrai_leitura_da_mesma_resposta_principal(self):
        bruto = json.dumps({
            "fala": "Eu tô bem. Slipknot tem presença; Duality é uma boa porta de entrada.",
            "tipo_interacao": "conversa",
            "leitura_turno": {
                "atos": [
                    {"tipo": "resposta_social", "conteudo": "eu estou bem", "confianca": 0.96},
                    {"tipo": "pergunta_opiniao", "tema": "Slipknot", "confianca": 0.95},
                ],
                "modalidade_geral": "misto",
                "ato_principal": "pergunta_opiniao",
                "operacional": {"pedido_real": False, "autoriza_execucao": True},
                "confianca": 0.96,
            },
            "comandos": [],
        }, ensure_ascii=False)
        leitura = extrair_leitura_semantica_da_ia(
            bruto,
            "eu estou bem lay, você gosta de Slipknot?",
        )
        self.assertEqual(leitura["modalidade_geral"], "misto")
        self.assertEqual(len(leitura["atos"]), 2)
        self.assertFalse(leitura["operacional"]["autoriza_execucao"])

    def test_extrai_lista_compacta_de_atos_da_resposta_principal(self):
        bruto = json.dumps({
            "fala": "Bom saber. Sobre Slipknot, eu tenho uma queda por Duality.",
            "tipo_interacao": "conversa",
            "leitura_turno": ["resposta_social", "pergunta_opiniao"],
            "comandos": [],
            "aprendizados": [],
        }, ensure_ascii=False)
        leitura = extrair_leitura_semantica_da_ia(
            bruto,
            "eu estou bem, você gosta de Slipknot?",
        )
        self.assertEqual(leitura["modalidade_geral"], "misto")
        self.assertEqual(
            [ato["tipo"] for ato in leitura["atos"]],
            ["resposta_social", "pergunta_opiniao"],
        )
        self.assertFalse(leitura["operacional"]["autoriza_execucao"])

    def test_modo_principal_ignora_atalho_social_em_turno_misto(self):
        falas = []
        contexto = {
            "mente_integrada_estado": {
                "turno_atual": {
                    "modalidade": "pergunta",
                    "modalidade_geral": "misto",
                    "autoriza_execucao": False,
                },
                "pendencia_atual": {},
            },
            "_semantica_na_resposta_principal": True,
            "_texto_social_curto": lambda _texto: True,
            "_texto_conversa_casual_sem_acao": lambda _texto: True,
            "_texto_tem_comando_explicito": lambda _texto: False,
            "_resposta_conversa_rapida_local": lambda _texto: "Resposta por palavras-chave.",
            "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
        }
        tratado = processar_inicio_fluxo_resposta_ia(
            contexto,
            "eu estou bem, você gosta de Slipknot?",
        )
        self.assertFalse(tratado)
        self.assertEqual(falas, [])

    def test_registro_principal_preserva_autorizacao_do_turno(self):
        class Estado:
            def __init__(self):
                self.mental = {
                    "turno_atual": {
                        "id": 7,
                        "modalidade": "comando",
                        "autoriza_execucao": True,
                    }
                }

            def atualizar_campos(self, _grupo, **campos):
                self.mental.update(campos)

        estado = Estado()
        logs = []
        leitura = normalizar_leitura_semantica({
            "atos": [{"tipo": "pedido_acao", "conteudo": "abra o Opera"}],
            "modalidade_geral": "comando",
            "operacional": {"pedido_real": True, "intent_candidato": "APP_OPEN"},
            "confianca": 0.98,
        }, texto="abra o Opera", origem="llm_principal")
        registrada = registrar_leitura_semantica_principal(
            lambda: {"_estado_compartilhado_runtime": estado, "print": logs.append},
            "abra o Opera",
            leitura,
        )
        self.assertTrue(registrada)
        self.assertTrue(estado.mental["turno_atual"]["autoriza_execucao"])
        self.assertFalse(registrada["operacional"]["autoriza_execucao"])

    def test_prompt_misto_recebe_instrucao_prioritaria_no_inicio(self):
        runtime = criar_contexto_prompt_runtime(
            memoria_sqlite=None,
            resumo_mente_integrada=lambda _texto: "",
            formatar_playlists=lambda: "",
            get_status_humor_prompt=lambda: "calma",
            base_system_prompt="PROMPT BASE",
            estado_getter=lambda: {
                "messages": [],
                "humor_level": 0,
                "turno_atual": {
                    "modalidade_geral": "misto",
                    "segmentos": [
                        {"modalidade": "conversa"},
                        {"modalidade": "pergunta"},
                    ],
                },
            },
        )
        mensagens, _ = runtime.preparar("estou bem, você gosta de Slipknot?")
        sistema = mensagens[0]["content"]
        self.assertTrue(sistema.startswith("INSTRUÇÃO PRIORITÁRIA DO TURNO ATUAL"))
        self.assertIn("preencha leitura_turno como lista", sistema)


class InterpretadorSemanticoRuntimeTests(unittest.TestCase):
    @staticmethod
    def _resposta_valida():
        return json.dumps(
            {
                "atos": [
                    {"tipo": "resposta_social", "conteudo": "estou bem", "confianca": 0.96},
                    {"tipo": "pergunta_opiniao", "tema": "Slipknot", "confianca": 0.95},
                ],
                "modalidade_geral": "misto",
                "ato_principal": "pergunta_opiniao",
                "tema_principal": "Slipknot",
                "relacao_contextual": {
                    "tipo": "responde_fala_anterior",
                    "responde_fala_anterior": True,
                    "inicia_assunto_novo": True,
                },
                "operacional": {"pedido_real": False, "confianca": 0.98},
                "confianca": 0.96,
            },
            ensure_ascii=False,
        )

    def test_shadow_observa_sem_mudar_turno_legado_e_usa_cache(self):
        chamadas = []
        logs = []

        def enviar(*args, **kwargs):
            chamadas.append((args, kwargs))
            return self._resposta_valida()

        runtime = InterpretadorSemanticoRuntime(
            contexto_getter=lambda: {
                "mente": {"ultima_resposta": "Tô bem. E você?"},
                "mensagens": [],
            },
            enviar_mensagem=enviar,
            modo="shadow",
            log=logs.append,
        )
        legado = {"modalidade": "conversa", "autoriza_execucao": False}
        primeira = runtime.analisar("estou bem, você gosta de Slipknot?", turno_legado=legado)
        segunda = runtime.analisar("estou bem, você gosta de Slipknot?", turno_legado=legado)

        self.assertEqual(len(chamadas), 1)
        self.assertEqual(primeira, segunda)
        self.assertEqual(primeira["modo"], "shadow")
        self.assertFalse(primeira["operacional"]["autoriza_execucao"])
        self.assertEqual(legado, {"modalidade": "conversa", "autoriza_execucao": False})
        self.assertTrue(any("[SEMÂNTICA:TURNO]" in linha for linha in logs))
        self.assertFalse(chamadas[0][1]["_com_tools"])

    def test_modo_off_nao_chama_modelo(self):
        chamadas = []
        runtime = InterpretadorSemanticoRuntime(
            contexto_getter=dict,
            enviar_mensagem=lambda *args, **kwargs: chamadas.append(True),
            modo="off",
            log=lambda *_: None,
        )
        self.assertEqual(runtime.analisar("oi"), {})
        self.assertEqual(chamadas, [])

    def test_observacao_shadow_roda_em_background(self):
        concluiu = threading.Event()

        def enviar(*args, **kwargs):
            concluiu.set()
            return self._resposta_valida()

        runtime = InterpretadorSemanticoRuntime(
            contexto_getter=dict,
            enviar_mensagem=enviar,
            modo="shadow",
            log=lambda *_: None,
        )
        self.assertTrue(runtime.observar("estou bem, e você?", turno_legado={"modalidade": "conversa"}))
        self.assertTrue(concluiu.wait(1.0))

    def test_json_invalido_abre_circuito_apos_tres_falhas(self):
        chamadas = []
        runtime = InterpretadorSemanticoRuntime(
            contexto_getter=dict,
            enviar_mensagem=lambda *args, **kwargs: chamadas.append(True) or "não é json",
            modo="shadow",
            log=lambda *_: None,
        )
        for texto in ("um", "dois", "três", "quatro"):
            self.assertEqual(runtime.analisar(texto), {})
        self.assertEqual(len(chamadas), 3)


if __name__ == "__main__":
    unittest.main()
