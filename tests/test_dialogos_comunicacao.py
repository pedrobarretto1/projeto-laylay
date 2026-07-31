from __future__ import annotations

import asyncio
import threading
import time
import unittest
from datetime import datetime

from mente_laylay.autonomia.agendamento_mental import extrair_agendamento_local
from mente_laylay.autonomia.execucao_ia import remover_prefixo_exec
from mente_laylay.autonomia.roteador_deterministico import (
    corrigir_verbo_operacional_digitado,
    detectar_email_notificacao_briefing,
    detectar_musica_ou_playlist_direta,
    detectar_volume_ou_midia,
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
from mente_laylay.arquivos.roteador_arquivos import extrair_criacao_pasta_arquivo
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_compartilhado import (
    classificar_pergunta_com_proposito,
    estado_mental_inicial,
    limpar_pergunta_aberta,
    registrar_mente_curta,
    registrar_oferta_pendente,
    registrar_pergunta_aberta,
    texto_parece_pergunta_aberta,
)
from mente_laylay.memoria_mental.pendencia import pendencia_ativa
from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno
from mente_laylay.cognicao.plano_turno import (
    atualizar_plano_turno,
    planejar_turno,
    verificar_fala_turno,
)
from mente_laylay.autonomia.finalizacao_execucao_ia import finalizar_execucao_resposta_ia
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.personalidade.conversa_natural import (
    classificar_conversa_curta_local,
    resposta_curta_contextual,
    resposta_pergunta_curta_dependente_topico,
    responder_relato_esportivo,
    responder_conversa_curta_por_tipo,
)
from mente_laylay.autonomia.porteiro_acoes import texto_conversa_casual_sem_acao
from mente_laylay.autonomia.pre_fluxo_contextual import analisar_intencao_com_porteiro
from mente_laylay.percepcao.ambiente_sistema import (
    AmbienteSistemaRuntime,
    executar_briefing_matinal,
    lapidar_fala_briefing,
    montar_briefing_matinal,
    naturalizar_clima_resumido,
)
from mente_laylay.cognicao.resumo_conteudo import (
    _recortar_texto_para_resumo,
    resumir_pagina_ou_video,
)
from mente_laylay.integracao.chrome_page_data import processar_page_data
from mente_laylay.integracao.llm_http import (
    FALHA_LLM_OCUPADA,
    FALHA_LLM_TIMEOUT,
    post_chat_llm,
)
from mente_laylay.personalidade.abertura_chat import AberturaChatRuntime, abertura_soa_natural
from mente_laylay.personalidade.fala_proativa import compor_fala_proativa
from mente_laylay.emocoes.perfil_emocional import ajustar_tom_por_emocao
from mente_laylay.personalidade.voz_runtime import VozRuntime
from mente_laylay.memoria_mental.continuidade_conversa import responder_pergunta_aberta


class DialogosComunicacaoTests(unittest.TestCase):
    @staticmethod
    def _ctx_conversa_minimo() -> dict:
        return {
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
            "_normalizar_texto_curto": lambda texto: str(texto).casefold(),
            "_ajustar_fala_por_horario": lambda fala, *_args: fala,
            "mente_integrada_estado": {},
            "foco_vivo": {},
        }

    def test_emocao_forte_nao_corta_fala_no_meio_da_frase(self) -> None:
        fala = (
            "Atenção: apareceu um aviso de segurança de Zenless Zone Zero: "
            "A celebração de segundo aniversário começou. Vale conferir antes de abrir links."
        )

        self.assertEqual(ajustar_tom_por_emocao(fala, "irritada"), fala)
        self.assertEqual(ajustar_tom_por_emocao(fala, "brava"), fala)

    def test_lote_proativo_nao_contamina_todas_as_falas_com_primeira_emocao(self) -> None:
        emocoes = []
        fala, _emocao, _nivel = compor_fala_proativa(
            [
                {
                    "tipo": "seguranca", "emocao": "irritada", "nivel": 2,
                    "texto": "Atenção: apareceu um aviso de segurança.", "ts": 1,
                },
                {
                    "tipo": "presenca_jogo", "emocao": "curiosa", "nivel": 1,
                    "texto": "O menu de pausa está aberto e a área parece segura.", "ts": 2,
                },
            ],
            obter_contexto_perceptivo=lambda: {
                "periodo": "noite", "topico_ativo": "jogo",
                "humor": 0, "emocao": "calma",
            },
            normalizar_segmento_fala=lambda texto: str(texto),
            normalizar_texto_com_apelidos=lambda texto: str(texto).casefold(),
            ajustar_tom_por_emocao=lambda texto, emocao, *_: (
                emocoes.append(emocao) or texto
            ),
            fallback_fala_neutra="Estou aqui.",
        )

        self.assertEqual(emocoes, ["irritada", "curiosa"])
        self.assertIn("aviso de segurança", fala)
        self.assertIn("área parece segura", fala)

    def test_horario_em_relato_de_viagem_nao_vira_comando(self) -> None:
        texto = "é em Santana de Parnaíba os jogos, eu vou para lá às 17:30"
        self.assertTrue(texto_conversa_casual_sem_acao(texto))

    def test_relato_esportivo_recebe_continuidade_em_vez_de_acao(self) -> None:
        ctx = self._ctx_conversa_minimo()
        viagem = responder_relato_esportivo(
            ctx,
            "é em santan de Parnaíba os jogos, eu vou para lá às 17:30",
        )
        competicao = responder_relato_esportivo(
            ctx,
            "na verdade vai ser eu que vou jogar neles kkk, vou de arremessamento de peso",
        )
        self.assertIn("Santana de Parnaíba", viagem)
        self.assertIn("17:30", viagem)
        self.assertIn("você que vai competir", competicao)
        self.assertIn("arremesso de peso", competicao)

    def test_porteiro_recusa_close_app_e_resumo_sem_sinal_no_turno(self) -> None:
        base = {
            "_texto_social_curto": lambda _texto: False,
            "_texto_conversa_casual_sem_acao": lambda _texto: False,
            "_texto_conversa_contextual_sem_comando": lambda _texto: False,
            "_texto_tem_comando_explicito": lambda _texto: False,
        }
        for intent in ("CLOSE_APP", "RESUMIR_PAGINA"):
            ctx = {**base, "analisar_intencao": lambda _texto, intent=intent: {"intent": intent, "params": {}}}
            status, resultado = analisar_intencao_com_porteiro(ctx, "estou contando sobre os jogos")
            self.assertEqual(status, "evitar")
            self.assertIsNone(resultado)

    def test_pedido_de_papo_tem_resposta_local_sem_duas_perguntas(self) -> None:
        ctx = self._ctx_conversa_minimo()
        leitura = classificar_conversa_curta_local(ctx, "quero só bater um papo com você")
        self.assertEqual(leitura["tipo"], "CHAT_ONLY")
        fala = responder_conversa_curta_por_tipo(ctx, "CHAT_ONLY", "quero só bater um papo com você")
        self.assertEqual(fala.count("?"), 0)
        self.assertIn("sem comando", fala.casefold())

    def test_que_bom_nao_inventa_que_havia_problema_entre_os_dois(self) -> None:
        ctx = self._ctx_conversa_minimo()
        for _ in range(6):
            fala = responder_conversa_curta_por_tipo(ctx, "POSITIVE_ACK", "que bom lay")
            self.assertNotIn("tudo certo entre nós", fala.casefold())

    def test_pergunta_pessoal_com_o_que_nao_vira_explicacao_da_fala_anterior(self) -> None:
        ctx = self._ctx_conversa_minimo()
        ctx["mente_integrada_estado"] = {
            "ultima_resposta": "Tô bem sim. Cabeça no lugar e curiosa pelo que vem.",
            "ultima_afirmacao": "Cabeça no lugar e curiosa pelo que vem.",
            "continuidade_fala_ts": time.time(),
            "ultima_habilidade": "conversa",
        }
        for pergunta in (
            "o que voce anda fazendo de bom?",
            "quer conversar sobre o que?",
        ):
            self.assertEqual(resposta_pergunta_curta_dependente_topico(ctx, pergunta), "")
            leitura = classificar_conversa_curta_local(ctx, pergunta)
            self.assertEqual(leitura["tipo"], "PERSONAL_CHAT")
            fala = responder_conversa_curta_por_tipo(ctx, "PERSONAL_CHAT", pergunta)
            self.assertNotIn("eu quis dizer", fala.casefold())
            self.assertNotIn("cabeça no lugar", fala.casefold())

    def test_bem_estar_devolve_cuidado_sem_criar_pendencia(self) -> None:
        ctx = self._ctx_conversa_minimo()
        fala = responder_conversa_curta_por_tipo(ctx, "WELLBEING", "como que voce ta lay?")
        self.assertIn("?", fala)
        self.assertTrue(any(p in fala.casefold() for p in ("e você", "e voce", "teu lado")))

        classificacao = classificar_pergunta_com_proposito(fala)
        self.assertEqual(classificacao["proposito"], "cortesia_social")
        self.assertFalse(texto_parece_pergunta_aberta(fala))

        estado = registrar_mente_curta(
            estado_mental_inicial(),
            texto_usuario="como que voce ta lay?",
            resposta_ia=fala,
            habilidade="conversa",
            texto_parece_pergunta_aberta_cb=texto_parece_pergunta_aberta,
            registrar_pergunta_aberta_cb=registrar_pergunta_aberta,
            limpar_pergunta_aberta_cb=limpar_pergunta_aberta,
        )
        self.assertEqual(estado.get("pergunta_aberta_texto"), "")
        self.assertEqual(estado.get("ultima_pergunta"), "")
        self.assertFalse(pendencia_ativa(estado.get("pendencia_atual")))

        proximo = classificar_modalidade_turno(
            "abre o youtube",
            texto_tem_comando_explicito=lambda _texto: True,
        )
        self.assertEqual(proximo["modalidade"], "comando")

        resposta_opcional = classificar_conversa_curta_local(ctx, "estou bem sim")
        self.assertEqual(resposta_opcional["tipo"], "WELLBEING_REPLY")

    def test_ue_isolado_continua_pedindo_explicacao(self) -> None:
        ctx = self._ctx_conversa_minimo()
        ctx["mente_integrada_estado"] = {
            "ultima_resposta": "Minha ideia foi curta.",
            "ultima_afirmacao": "Minha ideia foi curta.",
            "continuidade_fala_ts": time.time(),
            "ultima_habilidade": "conversa",
        }
        fala = resposta_pergunta_curta_dependente_topico(ctx, "ué?")
        self.assertTrue(fala)
        self.assertIn("ideia", fala.casefold())

    def test_item_adicionado_a_timer_proativo_existente_retorna_sucesso(self) -> None:
        class TimerAtivo:
            daemon = True
            def __init__(self, _atraso, callback):
                self.callback = callback
                self.ativo = False
            def is_alive(self):
                return self.ativo
            def start(self):
                self.ativo = True

        runtime = VozRuntime(
            fallback_fala="fallback", voice="voz",
            edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda _itens: ("fala", "calma", 1),
            ajustar_estado_fala_cb=lambda *_args: None,
            proativa_permitida_cb=lambda: True,
            interrupt_event=threading.Event(),
            timer_factory=TimerAtivo,
        )
        self.assertTrue(runtime.agendar_fala_proativa("rotina", "Rotina"))
        self.assertTrue(runtime.agendar_fala_proativa("briefing", "Clima", forcar_inicio=True))
        self.assertEqual(len(runtime.proativa_buffer), 2)

    def test_autonomia_durante_turno_entra_na_mesma_fala_da_resposta(self) -> None:
        chave = [42.0]
        runtime = VozRuntime(
            fallback_fala="fallback", voice="voz",
            edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
            ajustar_estado_fala_cb=lambda *_args: None,
            proativa_permitida_cb=lambda: False,
            chave_turno_cb=lambda: chave[0],
            interrupt_event=threading.Event(),
        )
        # Mantém o pedido inspecionável sem iniciar áudio no teste.
        runtime.worker_started = True
        runtime.iniciar_turno_resposta()

        self.assertTrue(runtime.agendar_fala_proativa(
            "contexto_janela",
            "Vejo que o código tá rendendo. Quer uma música de foco?",
            mesclar_turno=True,
        ))
        self.assertTrue(runtime.falar("Entendo a animação com o jogo."))

        pedido = runtime.fila.get_nowait()
        self.assertIn("Entendo a animação com o jogo.", pedido["texto"])
        self.assertIn("código tá rendendo", pedido["texto"])
        self.assertEqual(len(pedido["proativas_mescladas"]), 1)
        self.assertEqual(runtime.proativa_buffer, [])

    def test_canal_de_voz_do_turno_e_liberado_mesmo_com_retorno_antecipado(self) -> None:
        eventos = []

        class ModoChat:
            @staticmethod
            def processar_texto(_texto):
                return True

        runtime = RespostaIARuntime(
            contexto_getter=lambda: {
                "iniciar_turno_voz": lambda: eventos.append("inicio"),
                "finalizar_turno_voz": lambda: eventos.append("fim"),
                "marcar_inicio_turno": lambda _texto: None,
                "modo_chat_runtime": ModoChat(),
            },
            log=lambda *_args: None,
        )
        runtime.processar("oi")
        self.assertEqual(eventos, ["inicio", "fim"])

    def test_emocao_da_llm_e_aplicada_depois_da_execucao_e_antes_da_fala(self) -> None:
        eventos = []

        class Contexto:
            @staticmethod
            def montar():
                return {}

        runtime = RespostaIARuntime(
            contexto_getter=lambda: {
                "usar_modo_rapido": lambda _texto: True,
                "processar_comandos_imediatos": lambda *_args, **_kwargs: False,
                "get_messages": lambda: [],
                "enviar_mensagem": lambda *_args, **_kwargs: '{"fala":"Aí sim!","comandos":[]}',
                "preparar_resposta": lambda *_args: {
                    "resposta_bruta": "{}", "fala": "Aí sim!", "comandos": [],
                    "tipo_interacao": "conversa", "leitura_semantica": {},
                    "emocao": "alegre", "nivel_emocao": 2,
                },
                "processar_comando_deterministico": lambda *_args: False,
                "contexto_dispatch_runtime": Contexto(),
                "executar_comandos_json": lambda *_args: eventos.append("execucao") or {
                    "erros": [], "fala_ja_emitida": False,
                    "fala_emitida_por_acao": False, "fala_salva_no_inicio": False,
                },
                "definir_emocao_resposta": lambda emocao, nivel, _motivo: eventos.append(
                    ("emocao", emocao, nivel)
                ),
                "contexto_finalizacao_runtime": Contexto(),
                "finalizar_execucao": lambda *_args: eventos.append("fala"),
            },
            log=lambda *_args: None,
        )

        runtime.processar("terminei o projeto!")

        self.assertEqual(eventos, ["execucao", ("emocao", "alegre", 2), "fala"])

    def test_autonomia_tardia_ainda_entra_na_resposta_enfileirada(self) -> None:
        runtime = VozRuntime(
            fallback_fala="fallback", voice="voz",
            edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
            ajustar_estado_fala_cb=lambda *_args: None,
            proativa_permitida_cb=lambda: False,
            chave_turno_cb=lambda: 8.0,
            interrupt_event=threading.Event(),
        )
        runtime.worker_started = True
        runtime.iniciar_turno_resposta()
        runtime.falar("Esta é a resposta principal.")
        pedido = runtime.fila.get_nowait()

        self.assertTrue(runtime.agendar_fala_proativa(
            "contexto_janela",
            "Também reparei no projeto aberto.",
            mesclar_turno=True,
        ))
        self.assertIn("resposta principal", pedido["texto"])
        self.assertIn("projeto aberto", pedido["texto"])
        self.assertEqual(len(pedido["proativas_mescladas"]), 1)

    def test_briefing_inadequado_cai_em_fallback_curto_e_factual(self) -> None:
        fala = montar_briefing_matinal(
            cidade="Boituva",
            clima="Limpo 10 C umidade 81 por cento",
            enviar_mensagem_cb=lambda *_args, **_kwargs: (
                "A umidade trouxe desejo e meu coração úmido fez o mundo inteiro começar a tremer."
            ),
            limpar_resposta_cb=lambda texto: texto,
            remover_prefixo_exec_cb=lambda texto: texto,
        )
        self.assertIn("Boituva", fala)
        self.assertIn("10 C", fala)
        self.assertNotIn("desejo", fala.casefold())
        self.assertLess(len(fala.split()), 40)

    def test_briefing_nunca_fala_sentinela_tecnica_da_llm(self) -> None:
        fala = montar_briefing_matinal(
            cidade="Boituva",
            clima="céu limpo, com 17 graus Celsius",
            enviar_mensagem_cb=lambda *_args, **_kwargs: FALHA_LLM_TIMEOUT,
            limpar_resposta_cb=lambda texto: str(texto).replace("_", ""),
            remover_prefixo_exec_cb=lambda texto: texto,
        )

        self.assertNotIn("LAYLAYLLM", fala.upper())
        self.assertIn("Boituva", fala)
        self.assertIn("17 graus", fala)

    def test_repeticao_de_briefing_nunca_fala_sentinela_tecnica(self) -> None:
        falas = []
        runtime = AmbienteSistemaRuntime()
        retorno = runtime.repetir_briefing_atual(
            cidade="Boituva",
            obter_clima=lambda: "céu limpo, com 17 graus Celsius",
            enviar_mensagem=lambda *_args, **_kwargs: FALHA_LLM_TIMEOUT,
            limpar_resposta=lambda texto: str(texto).replace("_", ""),
            remover_prefixo_exec=lambda texto: texto,
            falar=lambda texto, *_args: falas.append(texto),
            print_fn=lambda *_args: None,
        )

        self.assertEqual(retorno, falas[0])
        self.assertNotIn("LAYLAYLLM", retorno.upper())
        self.assertIn("Boituva", retorno)

    def test_briefing_sem_clima_nao_injeta_erro_em_frase_de_sucesso(self) -> None:
        chamadas_ia = []
        fala = montar_briefing_matinal(
            cidade="Boituva",
            clima="Não consegui pegar o clima agora.",
            enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas_ia.append(True) or "não deveria chamar",
            limpar_resposta_cb=lambda texto: texto,
            remover_prefixo_exec_cb=lambda texto: texto,
        )
        self.assertEqual(chamadas_ia, [])
        self.assertIn("clima de Boituva não respondeu", fala)
        self.assertIn("não vou inventar previsão", fala)
        self.assertNotIn("clima está Não consegui", fala)

    def test_briefing_seco_e_artificial_ganha_voz_da_laylay(self) -> None:
        fala = lapidar_fala_briefing(
            "Boa manhã! Em Boituva é ensolarado e 17 graus Celsius, vento de 10 "
            "quilômetros/h do sul. O que vocês planejam 'destruir' hoje no PC?.",
            cidade="Boituva",
            clima="ensolarado e 17 graus Celsius",
        )
        self.assertNotIn("Boa manhã", fala)
        self.assertNotIn("vocês", fala)
        self.assertNotIn("'destruir'", fala)
        self.assertNotIn("?.", fala)
        self.assertIn("o tempo está ensolarado", fala)
        self.assertIn("qual projeto vai perder a paz primeiro hoje?", fala.casefold())

    def test_clima_compacto_do_wttr_vira_frase_pronunciavel(self) -> None:
        fala = naturalizar_clima_resumido(
            "Ensolarado +17°C umidade:52% vento: ↙10km/h"
        )
        self.assertEqual(
            fala,
            "ensolarado, com 17 graus Celsius, umidade em 52 por cento e vento de 10 quilômetros por hora",
        )

    def test_repetir_briefing_sem_clima_nao_chama_llm(self) -> None:
        falas = []
        runtime = AmbienteSistemaRuntime()
        retorno = runtime.repetir_briefing_atual(
            cidade="Boituva",
            obter_clima=lambda: "Clima não disponível no momento.",
            enviar_mensagem=lambda *_args, **_kwargs: self.fail("LLM não deveria ser chamada"),
            limpar_resposta=lambda texto: texto,
            remover_prefixo_exec=lambda texto: texto,
            falar=lambda texto, *_args: falas.append(texto),
            print_fn=lambda *_args: None,
        )
        self.assertEqual(retorno, falas[0])
        self.assertIn("não respondeu", retorno)
        self.assertNotIn("clima está Clima", retorno)

    def test_recusa_curta_responde_a_oferta_proativa_de_abrir(self) -> None:
        fala = responder_pergunta_aberta(
            "quero nao",
            pergunta_aberta={
                "pergunta": "Quer que eu abra Laylay.py?",
                "tipo": "confirmacao",
                "proposito": "confirmacao",
                "topico": "Laylay.py",
            },
            normalizar_texto_curto=lambda texto: str(texto).casefold(),
        )
        self.assertTrue("não abro" in fala.casefold() or "deixo fechado" in fala.casefold() or "não mexo" in fala.casefold())

    def test_mente_unica_funde_briefing_e_rotina_sem_abertura_redundante(self) -> None:
        fala, _emocao, _nivel = compor_fala_proativa(
            [
                {"tipo": "abertura", "texto": "Oi, Pedro. Cheguei.", "ts": 1},
                {"tipo": "briefing", "texto": "Em Boituva faz 10 graus.", "ts": 2},
                {"tipo": "rotina", "texto": "Você costuma usar Laylay.py agora.", "ts": 3},
            ],
            obter_contexto_perceptivo=lambda: {
                "periodo": "manhã", "topico_ativo": "", "humor": 0, "emocao": "calma",
            },
            normalizar_segmento_fala=lambda texto: str(texto),
            normalizar_texto_com_apelidos=lambda texto: str(texto).casefold(),
            ajustar_tom_por_emocao=lambda texto, *_args: texto,
            fallback_fala_neutra="Oi, Pedro.",
        )
        self.assertNotIn("Cheguei", fala)
        self.assertIn("10 graus", fala)
        self.assertIn("Laylay.py", fala)

    def test_lote_proativo_confirma_todos_os_sinais_so_depois_da_fala(self) -> None:
        confirmacoes = []
        falas_registradas = []
        runtime = VozRuntime(
            fallback_fala="fallback",
            voice="voz",
            edge_tts_mod=None,
            sounddevice_mod=None,
            soundfile_mod=None,
            pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda itens: (
                " ".join(str(item["texto"]) for item in itens), "calma", 1,
            ),
            ajustar_estado_fala_cb=lambda *_args: None,
            proativa_permitida_cb=lambda: True,
            interrupt_event=threading.Event(),
            registrar_fala_emitida_cb=lambda fala, itens: falas_registradas.append((fala, len(itens))),
        )
        runtime.falar = lambda *_args, **_kwargs: True
        runtime.proativa_buffer = [
            {
                "tipo": "briefing", "texto": "Clima.", "forcar_inicio": True,
                "ao_concluir": lambda ok, motivo: confirmacoes.append((ok, motivo)),
            },
            {"tipo": "rotina", "texto": "Rotina.", "forcar_inicio": False},
        ]
        runtime.flush_fala_proativa()
        self.assertEqual(confirmacoes, [(True, "entregue")])
        self.assertEqual(falas_registradas, [("Clima. Rotina.", 2)])

    def test_briefing_so_salva_estado_depois_de_entrega_confirmada(self) -> None:
        salvos = []
        base = {
            "ja_executado": False,
            "cidade": "Boituva",
            "carregar_estado": lambda: "",
            "salvar_estado": lambda: salvos.append(True),
            "obter_clima": lambda: "ensolarado, 19 C",
            "montar_fala": lambda _clima: "Bom dia. Hoje faz 19 graus.",
            "agora": lambda: datetime(2026, 7, 13, 8, 0),
            "sleep_fn": lambda _segundos: None,
            "print_fn": lambda *_args: None,
        }
        recusado = executar_briefing_matinal(
            **base,
            agendar_fala=lambda *_args: False,
        )
        self.assertFalse(recusado)
        self.assertEqual(salvos, [])

        entregue = executar_briefing_matinal(
            **base,
            agendar_fala=lambda *_args: True,
        )
        self.assertTrue(entregue)
        self.assertEqual(salvos, [True])

        salvos.clear()
        pendente = executar_briefing_matinal(
            **base,
            agendar_fala=lambda *_args: {"entregue": False, "pendente": True},
        )
        self.assertTrue(pendente)
        self.assertEqual(salvos, [])

    def test_abertura_rejeita_reacao_fisica_inventada_e_cumprimenta(self) -> None:
        runtime = AberturaChatRuntime(
            estado_getter=lambda: {"current_emotion": "envergonhada", "emotion_level": 3},
            enviar_mensagem=lambda *_args, **_kwargs: "Vi que você me olhou e fiquei com o nariz quente.",
            limpar_resposta=lambda texto: texto,
            remover_prefixo_exec=lambda texto: texto,
        )
        fala = runtime.gerar("inicio")
        fala_norm = fala.casefold()
        self.assertTrue(fala_norm.startswith(("oi", "olá", "ola", "ei", "bom dia", "boa tarde", "boa noite")))
        self.assertNotIn("me olhou", fala_norm)
        self.assertNotIn("nariz quente", fala_norm)

    def test_abertura_rejeita_portugues_traduzido_e_tom_de_atendente(self) -> None:
        self.assertFalse(abertura_soa_natural("Olá! Como está a noite sendo pra você?"))
        self.assertFalse(abertura_soa_natural("Olá! Como posso te ajudar hoje?"))
        self.assertTrue(abertura_soa_natural("Boa noite! Como tá sua noite?"))

        runtime = AberturaChatRuntime(
            estado_getter=lambda: {},
            enviar_mensagem=lambda *_args, **_kwargs: "Olá! Como está a noite sendo pra você?",
            limpar_resposta=lambda texto: texto,
            remover_prefixo_exec=lambda texto: texto,
        )
        fala = runtime.gerar("inicio")
        self.assertNotIn("noite sendo", fala.casefold())

    def test_erro_de_digitacao_liag_e_corrigido_so_em_comando_iot(self) -> None:
        self.assertEqual(
            corrigir_verbo_operacional_digitado("liag o ventilador"),
            "liga o ventilador",
        )
        self.assertEqual(
            corrigir_verbo_operacional_digitado("liag uma conversa"),
            "liag uma conversa",
        )

        roteado = detectar_intencao_deterministica_mente(
            "liag o ventilador",
            {
                "normalizar_texto": lambda texto: str(texto).casefold(),
                "detectar_intencao_iot": lambda texto, _estado: (
                    {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "tomada_ventilador"}}
                    if texto.startswith("liga ") else None
                ),
            },
        )
        self.assertEqual(roteado["intent"], "IOT_CONTROL")
        self.assertEqual(roteado["params"]["acao"], "ligar")

    def test_comando_json_intent_ligar_chega_ao_executor_iot(self) -> None:
        executados = []
        resultado = executar_comandos_json(
            {
                "executar_intencao": lambda intencao, texto: executados.append((intencao, texto)) or True,
            },
            "liag o ventilador",
            [{"intent": "ligar", "alvo": "ventilador"}],
            "",
            "comando",
            False,
            False,
            False,
        )
        self.assertEqual(executados[0][0], {
            "intent": "IOT_CONTROL",
            "params": {"acao": "ligar", "alvo": "ventilador"},
        })
        self.assertEqual(resultado["erros"], [])
        self.assertTrue(resultado["fala_emitida_por_acao"])

    def test_page_data_nao_dispara_resumo_llm_concorrente(self) -> None:
        resumos_automaticos = []
        paginas = []
        resultado = processar_page_data(
            {
                "type": "PAGE_DATA",
                "payload": {"url": "https://exemplo.test", "title": "Exemplo", "content": "Texto"},
            },
            {
                "armazenar_contexto_pagina": lambda *args: paginas.append(args),
                "resumir_pagina_no_dicionario": lambda url: resumos_automaticos.append(url),
            },
        )
        self.assertTrue(resultado["handled"])
        self.assertEqual(len(paginas), 1)
        self.assertEqual(resumos_automaticos, [])

    def test_modelo_local_ocupado_nao_espera_trava_sem_limite(self) -> None:
        lock = threading.Lock()
        lock.acquire()
        chamadas_http = []
        try:
            resposta, _ = post_chat_llm(
                {},
                {"messages": [{"role": "user", "content": "resuma"}]},
                base_url="http://127.0.0.1:1234/v1",
                local_timeout=120,
                remote_timeout=30,
                bad_request_until=0,
                lock=lock,
                requests_post=lambda *_args, **_kwargs: chamadas_http.append(True),
                print_fn=lambda *_args: None,
                timeout=0.1,
            )
        finally:
            lock.release()
        self.assertEqual(chamadas_http, [])
        self.assertEqual(
            resposta.json()["choices"][0]["message"]["content"],
            FALHA_LLM_OCUPADA,
        )

    def test_resumo_de_pagina_recorta_conteudo_grande_sem_perder_o_final(self) -> None:
        texto = "A" * 12000 + "FINAL-IMPORTANTE"
        recortado, mudou = _recortar_texto_para_resumo(texto, limite=1000)
        self.assertTrue(mudou)
        self.assertIn("trecho intermediário omitido", recortado)
        self.assertTrue(recortado.endswith("FINAL-IMPORTANTE"))
        self.assertLess(len(recortado), 1100)

    def test_resumo_de_pagina_tira_chamada_llm_do_loop_websocket(self) -> None:
        falas = []
        thread_principal = threading.get_ident()
        thread_llm = []

        def enviar(_mensagens, **_kwargs):
            thread_llm.append(threading.get_ident())
            return "fala:A página explica o assunto e destaca o ponto principal."

        resultado = asyncio.run(resumir_pagina_ou_video(
            websocket_disponivel=lambda: True,
            solicitar_conteudo=lambda: asyncio.sleep(0, result={
                "success": True,
                "data": {
                    "url": "https://exemplo.test/artigo",
                    "title": "Artigo de teste",
                    "content": "Conteúdo relevante da página. " * 10,
                },
            }),
            falar=lambda fala, *_args: falas.append(fala),
            enviar_mensagem=enviar,
            limpar_resposta=lambda texto: texto,
            remover_prefixo_exec=remover_prefixo_exec,
            transcript_api=object(),
        ))
        self.assertTrue(resultado)
        self.assertEqual(len(thread_llm), 1)
        self.assertNotEqual(thread_llm[0], thread_principal)
        self.assertEqual(len(falas), 1)
        self.assertIn("ponto principal", falas[-1])

    def test_prefixos_internos_repetidos_nao_vazam_na_fala(self) -> None:
        self.assertEqual(
            remover_prefixo_exec("fala:fala:O clima está ensolarado."),
            "O clima está ensolarado.",
        )

    def test_repeticao_do_briefing_retorna_e_fala_texto_limpo(self) -> None:
        falas = []
        runtime = AmbienteSistemaRuntime()
        retorno = runtime.repetir_briefing_atual(
            cidade="Boituva",
            obter_clima=lambda: "ensolarado, 19 C",
            enviar_mensagem=lambda *_args, **_kwargs: "fala:fala:Sol em Boituva hoje.",
            limpar_resposta=lambda texto: texto,
            remover_prefixo_exec=remover_prefixo_exec,
            falar=lambda fala, *_args: falas.append(fala),
        )
        self.assertEqual(retorno, "Sol em Boituva hoje.")
        self.assertEqual(falas, ["Sol em Boituva hoje."])

    def test_protesto_brincalhao_nao_vira_acolhimento_emocional_generico(self) -> None:
        ctx = {
            "mente_integrada_estado": {
                "ultima_resposta": "O céu quer saber se o Pedro vai sair do celular.",
            },
        }
        texto = "falando que sou viciado em celular, vacilo"
        leitura = classificar_conversa_curta_local(ctx, texto)
        self.assertEqual(leitura.get("tipo"), "PLAYFUL_PROTEST")

        fala = responder_conversa_curta_por_tipo(ctx, "PLAYFUL_PROTEST", texto)
        fala_normalizada = fala.casefold()
        self.assertTrue(any(p in fala_normalizada for p in ("celular", "viciado", "vício")))
        self.assertNotIn("entendi teu estado", fala_normalizada)
        self.assertNotIn("abaixo o ritmo", fala_normalizada)

    def test_volume_maximo_explicito_e_contextual_vira_cem(self) -> None:
        params = lambda **kwargs: kwargs
        explicito = detectar_volume_ou_midia(
            "coloca o volume no maximo",
            params_cb=params,
        )
        contextual = detectar_volume_ou_midia(
            "aumenta para o maximo",
            params_cb=params,
            contexto_volume_ativo=True,
        )
        corrigido = detectar_volume_ou_midia(
            "nao lay o volume no maximo",
            params_cb=params,
        )
        for resultado in (explicito, contextual, corrigido):
            self.assertEqual(resultado["intent"], "VOLUME")
            self.assertEqual(resultado["params"]["acao"], "set")
            self.assertEqual(resultado["params"]["nivel_volume"], 100)

    def test_continuidade_de_volume_chega_ao_roteador_antes_da_ia(self) -> None:
        resultado = detectar_intencao_deterministica_mente(
            "aumenta para o máximo",
            {
                "mente_integrada_estado": {
                    "ultima_acao_intent": "VOLUME",
                    "ultima_acao_params": {"acao": "set", "nivel_volume": 40},
                }
            },
        )
        self.assertEqual(resultado, {
            "intent": "VOLUME",
            "params": {
                "acao": "set",
                "nivel_volume": 100,
                "referencia_contextual": True,
            },
        })

    def test_confirmacao_de_volume_informa_o_nivel_aplicado(self) -> None:
        falas = []
        niveis = []
        self.assertTrue(executar_intencao(
            {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 40}},
            "coloca o volume em 40",
            {
                "_target_from_params": lambda *_args: "pc_a",
                "ajustar_volume_sistema": lambda nivel: niveis.append(nivel),
                "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            },
        ))
        self.assertEqual(niveis, [40])
        self.assertEqual(len(falas), 1)
        self.assertIn("40", falas[0])

    def test_complemento_de_horario_reaproveita_lembrete_pendente(self) -> None:
        registros = []
        falas = []
        agenda = []
        contexto_base = {
            "_target_from_params": lambda *_args: "pc_a",
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "_registrar_mente_curta": lambda *args: registros.append(args),
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_agendamentos_transacionar": lambda mutador: (mutador(agenda) is None),
        }
        self.assertTrue(executar_intencao(
            {
                "intent": "AGENDAR_LEMBRETE",
                "params": {"evento": "campeonato de arremesso de peso", "data_hora": "sexta"},
            },
            "me lembra do campeonato sexta",
            contexto_base,
        ))
        self.assertEqual(agenda, [])
        self.assertEqual(registros[-1][2:], (
            "AGENDAR_LEMBRETE", "campeonato de arremesso de peso", "sexta", "agenda"
        ))

        contexto_com_pendencia = {
            **contexto_base,
            "ultima_intencao": "AGENDAR_LEMBRETE",
            "ultima_habilidade": "agenda",
            "ultimo_alvo": "campeonato de arremesso de peso",
            "ultimo_escopo": "sexta",
        }
        self.assertTrue(executar_intencao(
            {"intent": "AGENDAR_LEMBRETE", "params": {"hora": "06:00"}},
            "às 6:00",
            contexto_com_pendencia,
        ))
        self.assertEqual(len(agenda), 1)
        self.assertEqual(agenda[0]["descricao"], "campeonato de arremesso de peso")
        self.assertEqual(datetime.fromtimestamp(agenda[0]["ts_execucao"]).weekday(), 4)
        self.assertTrue(any("campeonato de arremesso de peso" in fala for fala in falas))

    def test_disso_resolve_relato_futuro_recente_sem_criar_lembrete_generico(self) -> None:
        agenda = []
        resultado = extrair_agendamento_local(
            "me lembra disso as 6:00",
            lambda texto: texto.casefold(),
        )
        self.assertEqual(resultado["params"]["descricao"], "disso")
        self.assertTrue(executar_intencao(
            resultado,
            "me lembra disso as 6:00",
            {
                "_target_from_params": lambda *_args: "pc_a",
                "falar_com_lipsync": lambda *_args: None,
                "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
                "_agendamentos_transacionar": lambda mutador: (mutador(agenda) is None),
                "ultimas_entradas": [
                    "estou bem sim lay, sabia que sexta eu vou participa de um campeonato de arremessamento de peso",
                    "me lembra disso as 6:00",
                ],
            },
        ))
        self.assertEqual(agenda[0]["descricao"], "participar de um campeonato de arremessamento de peso")
        self.assertEqual(datetime.fromtimestamp(agenda[0]["ts_execucao"]).weekday(), 4)

    def test_cancelamento_de_lembrete_extrai_apenas_o_assunto(self) -> None:
        resultado = extrair_agendamento_local(
            "cancela o lembrete de beber água",
            lambda texto: texto.casefold().replace("á", "a"),
        )
        self.assertEqual(resultado, {
            "intent": "CANCELAR_AGENDAMENTO",
            "params": {"alvo": "beber agua"},
        })

    def test_volume_maximo_nunca_vira_busca_musical(self) -> None:
        resultado = detectar_musica_ou_playlist_direta(
            "coloca o volume no maximo",
            "coloca o volume no maximo",
            "coloca o volume no maximo",
            params_cb=lambda **kwargs: kwargs,
            detectar_playlist_nome_direto=lambda _texto: "",
            normalizar_query_musical=lambda texto: texto,
        )
        self.assertIsNone(resultado)

    def test_email_em_fala_mista_e_prioritario_ao_ia_first(self) -> None:
        texto = "estou bem tambem, pode ler meus emails"
        turno = classificar_modalidade_turno(texto)
        resultado = detectar_email_notificacao_briefing(
            texto,
            params_cb=lambda **kwargs: kwargs,
        )
        self.assertEqual(turno["modalidade_geral"], "misto")
        self.assertEqual(turno["ato_principal"], "comando")
        self.assertEqual(resultado["intent"], "EMAIL_READ")
        self.assertTrue(texto_expresso_melhor_no_deterministico(
            texto,
            normalizar_texto=lambda valor: valor.casefold(),
        ))

    def test_leitura_email_solicitada_emite_resumo_imediato_uma_vez(self) -> None:
        falas = []
        resultado = executar_intencao(
            {"intent": "EMAIL_READ", "params": {}},
            "leia meus emails",
            {
                "_target_from_params": lambda *_args: "pc_a",
                "_gmail_nao_lidos_cache": [],
                "_gmail_buscar_nao_lidos": lambda: [],
                "_gmail_falar_resumo_estiloso": lambda *_args, **_kwargs: (
                    "Nada novo no email. A caixa está quieta."
                ),
                "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            },
        )
        self.assertTrue(resultado)
        self.assertEqual(falas, ["Nada novo no email. A caixa está quieta."])

    def test_parser_composto_aceita_coloca_arquivo_dentro_dela(self) -> None:
        resultado = extrair_criacao_pasta_arquivo(
            "cria uma pasta chamada antonio e dentro dela coloca um arquivo de texto "
            "chamado carlos escrito ai ai"
        )
        self.assertEqual(resultado, {
            "nome": "antonio",
            "arquivo_nome": "carlos",
            "arquivo_conteudo": "ai ai",
        })

    def test_comando_iot_confirmado_ganha_personalidade_sem_perder_resultado(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                intent="IOT_CONTROL",
                status="ligado",
                alvo="ventilador",
                executou=True,
                confirmado=True,
                texto_usuario="liga o ventilador",
            ),
            "Pronto, liguei ventilador.",
        )
        fala = plano.fala.casefold()
        self.assertIn("ventilador", fala)
        self.assertTrue("liguei" in fala or "ligado" in fala)
        self.assertNotEqual(fala, "pronto, liguei ventilador.")
        self.assertNotRegex(fala, r"\b(?:caralho|porra|merda)\b")

    def test_falas_operacionais_variam_sem_repetir_a_mesma_abertura(self) -> None:
        resultado = ResultadoAcao(
            status="desligado",
            alvo="ventilador",
            executou=True,
            confirmado=True,
            texto_usuario="desliga o ventilador",
        )
        falas = {
            planejar_resposta_acao(resultado, "Pronto, desliguei ventilador.").fala
            for _ in range(3)
        }
        self.assertGreaterEqual(len(falas), 2)
        for fala in falas:
            self.assertIn("ventilador", fala.casefold())
            self.assertTrue("desliguei" in fala.casefold() or "desligado" in fala.casefold())

    def test_confirmacao_generica_de_midia_ganha_carisma_e_preserva_resultado(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                intent="MEDIA_CONTROL",
                status="midia_next",
                alvo="música",
                executou=True,
                confirmado=True,
                texto_usuario="próxima música",
            ),
            "Feito.",
        )
        fala = plano.fala.casefold()
        self.assertRegex(fala, r"(?:próxima|troquei|música)")
        self.assertNotEqual(fala, "feito.")

    def test_personalidade_nao_transforma_falha_em_sucesso(self) -> None:
        base = "Ventilador não respondeu agora. Não vou fingir que o comando foi."
        plano = planejar_resposta_acao(
            ResultadoAcao(
                status="indisponivel",
                alvo="ventilador",
                executou=False,
                confirmado=False,
            ),
            base,
        )
        self.assertEqual(plano.fala, base)
        self.assertEqual(plano.classe, "falha")

    def test_fala_criativa_de_comando_recebe_ancora_de_sucesso(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                status="ligado",
                alvo="ventilador",
                executou=True,
                confirmado=True,
            ),
            "Agora o calor ganhou um adversário à altura.",
        )

        fala = plano.fala.casefold()
        self.assertIn("ventilador", fala)
        self.assertRegex(fala, r"(?:está ligado|esta ligado|liguei|confirmei)")
        self.assertIn("calor", fala)
        self.assertTrue(plano.personalidade_permitida)

    def test_fala_criativa_de_falha_diz_que_pedido_nao_foi_feito(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                status="falha_execucao",
                alvo="playlist noite",
                executou=False,
                confirmado=False,
            ),
            "Ela resolveu fazer greve justo agora.",
        )

        fala = plano.fala.casefold()
        self.assertIn("não consegui", fala)
        self.assertIn("playlist noite", fala)
        self.assertIn("greve", fala)
        self.assertTrue(plano.personalidade_permitida)

    def test_resultado_incerto_nao_vira_confirmacao_disfarcada(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                status="midia_next",
                alvo="próxima música",
                executou=True,
                confirmado=None,
            ),
            "A fila andou com elegância.",
        )

        self.assertIn("não consegui confirmar", plano.fala.casefold())
        self.assertNotIn("confirmei o resultado", plano.fala.casefold())

    def test_consulta_iot_descreve_estado_sem_fingir_que_executou(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                intent="IOT_STATUS",
                status="ligado",
                alvo="ventilador",
                executou=True,
                confirmado=True,
            ),
            "O ventilador está ligado.",
        )
        fala = plano.fala.casefold()
        self.assertIn("está ligado", fala)
        self.assertNotIn("liguei", fala)

    def test_comando_misto_preserva_reconhecimento_humano_e_resultado(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                status="ligado",
                alvo="ventilador",
                executou=True,
                confirmado=True,
                texto_usuario="tá muito quente, liga o ventilador",
            ),
            "Liguei o ventilador.",
        )
        fala = plano.fala.casefold()
        self.assertIn("quente", fala)
        self.assertIn("ventilador", fala)

    def test_jornada_noite_chata_ate_musica_nao_puxa_memoria_sem_relacao(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_resposta": "Seu nome é Pedro.",
            "continuidade_fala_ts": 1.0,
            "topico_explicito_atual": "Pabllo Vittar",
            "topico_explicito_ts": 1.0,
        })
        selecao = selecionar_contexto_turno(
            "noite chata",
            turno=classificar_modalidade_turno("noite chata"),
            mente=mente,
        )
        self.assertFalse(selecao["selecionados"])

        mente = registrar_pergunta_aberta(
            mente,
            "Quer que eu puxe uma música, um filme curto ou alguma ideia pra gente fazer agora?",
            topico="noite chata",
        )
        pendencia = pendencia_ativa(mente)
        self.assertEqual(pendencia["origem"], "pergunta_aberta")
        self.assertEqual(pendencia["dominio"], "conversa")

        mente = registrar_oferta_pendente(
            mente,
            'Eu tentaria "Quando Bate Aquela Saudade" de Rubel. Quer ouvir essa?',
        )
        pendencia = pendencia_ativa(mente)
        self.assertEqual(pendencia["dominio"], "musica")
        self.assertEqual(
            pendencia["opcoes"][0]["params"]["query"],
            "Rubel - Quando Bate Aquela Saudade",
        )

    def test_jornada_comando_misto_preserva_conversa_e_executa_so_a_acao(self) -> None:
        turno = classificar_modalidade_turno("tô cansado, coloca uma música calma")
        self.assertEqual(turno["ato_principal"], "comando")
        self.assertEqual(turno["texto_conversacional"], "tô cansado")
        self.assertEqual(turno["texto_operacional"], "coloca uma música calma")

        intencao = detectar_musica_ou_playlist_direta(
            turno["texto_operacional"],
            texto_sem_destino=turno["texto_operacional"],
            texto_bruto=turno["texto_operacional"],
            params_cb=lambda **kwargs: kwargs,
            detectar_playlist_nome_direto=lambda _texto: "",
            normalizar_query_musical=lambda texto: texto,
        )
        self.assertEqual(intencao["intent"], "MUSIC_SEARCH")

    def test_jornada_pergunta_sobre_comando_nao_vira_comando(self) -> None:
        turno = classificar_modalidade_turno("não abre o quê?")
        self.assertEqual(turno["modalidade_geral"], "pergunta")
        decisao = arbitrar_turno("não abre o quê?", [
            CandidatoDecisao(
                tipo="comando_contextual",
                valor={"intent": "APP_OPEN", "params": {"nome_app": "que"}},
                origem="memoria_antiga",
                confianca=0.99,
            )
        ], turno=turno)
        self.assertIsNone(decisao["decisao"])

    def test_jornada_lembrete_natural_nao_cai_na_conversa_livre(self) -> None:
        resultado = extrair_agendamento_local(
            "me lembra de ir pegar um refri daqui 5 minutos",
            lambda texto: texto.casefold(),
        )
        self.assertEqual(resultado["intent"], "AGENDAR_LEMBRETE")
        self.assertIn("pegar um refri", resultado["params"]["descricao"])

    def test_plano_unico_preserva_conversa_e_execucao_no_turno_misto(self) -> None:
        texto = "tô cansado, coloca uma música calma"
        turno = classificar_modalidade_turno(texto)
        plano = planejar_turno(texto, turno=turno, mente=estado_mental_inicial(), periodo="noite")

        self.assertTrue(plano["misto"])
        self.assertTrue(plano["requer_execucao"])
        self.assertEqual(plano["dominio"], "musica")
        self.assertEqual([ato["tipo"] for ato in plano["atos"]], ["conversa", "comando"])
        self.assertIn("preferencias_musicais", plano["contexto_necessario"])
        self.assertIn("uma única fala", plano["resposta_esperada"])

    def test_confirmacao_curta_planeja_consulta_da_pendencia(self) -> None:
        turno = classificar_modalidade_turno("quero sim")
        plano = planejar_turno(
            "quero sim",
            turno=turno,
            mente={"pendencia_atual": {"status": "ativa", "dominio": "musica"}},
        )
        self.assertEqual(plano["ato_principal"], "confirmacao")
        self.assertEqual(plano["dominio"], "musica")
        self.assertIn("pendencia_ativa", plano["contexto_necessario"])

    def test_verificador_bloqueia_vazamento_do_contrato_interno(self) -> None:
        plano = planejar_turno(
            "meu nome é Pedro",
            turno=classificar_modalidade_turno("meu nome é Pedro"),
        )
        verificacao = verificar_fala_turno(
            '{"comandos": [], "aprendizados": ["nome: Pedro"]}',
            plano=plano,
            periodo="tarde",
        )
        self.assertFalse(verificacao["aceita"])
        self.assertIn("vazamento_formato_interno", verificacao["problemas"])
        self.assertEqual(verificacao["fala"], "")

    def test_verificador_nao_deixa_comando_nao_executado_parecer_sucesso(self) -> None:
        texto = "liga o ventilador"
        plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
        plano = atualizar_plano_turno(plano, fase="resposta_planejada", comandos=[])
        verificacao = verificar_fala_turno(
            "Pronto, liguei o ventilador.",
            plano=plano,
            origem="ia_final",
        )
        self.assertIn("comando_sem_execucao_confirmada", verificacao["problemas"])
        self.assertIn("não executei", verificacao["fala"].casefold())

    def test_verificador_nao_reescreve_escolha_temporal_conversacional(self) -> None:
        plano = planejar_turno(
            "nada demais hoje",
            turno=classificar_modalidade_turno("nada demais hoje"),
            periodo="tarde",
        )
        verificacao = verificar_fala_turno(
            "Quer deixar a noite mais interessante comigo?",
            plano=plano,
            periodo="tarde",
        )
        self.assertNotIn("incoerencia_temporal_corrigida", verificacao["problemas"])
        self.assertEqual(
            verificacao["fala"],
            "Quer deixar a noite mais interessante comigo?",
        )

    def test_plano_unico_entra_no_prompt_da_mente(self) -> None:
        texto = "tô cansado, coloca uma música calma"
        plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
        prompt = resumo_mente_integrada_para_prompt(
            texto_usuario=texto,
            ctx={},
            percepcao={},
            mente={"plano_turno_atual": plano},
        )
        self.assertIn("PLANO ÚNICO DESTE TURNO", prompt)
        self.assertIn("requer_execucao=True", prompt)
        self.assertIn("reconheça a parte humana", prompt)

    def test_finalizacao_verifica_fala_antes_de_emitir(self) -> None:
        falas = []
        mensagens = []
        finalizar_execucao_resposta_ia(
            {
                "messages": mensagens,
                "current_emotion": "calma",
                "emotion_level": 1,
                "enviar_mensagem": lambda *_args, **_kwargs: "",
                "limpar_resposta_da_ia": lambda texto: (texto, []),
                "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                "verificar_fala_turno": lambda _fala, **_kwargs: {
                    "aceita": True,
                    "fala": "Resposta ajustada ao turno.",
                },
                "_falhas_consecutivas": {},
            },
            [],
            [],
            "Resposta vaga.",
            False,
            False,
            False,
        )
        self.assertEqual(falas, ["Resposta ajustada ao turno."])
        self.assertEqual(mensagens[-1]["content"], "Resposta ajustada ao turno.")

    def test_correcao_conversacional_nao_vaza_nome_interno_game_vision(self) -> None:
        ctx = self._ctx_conversa_minimo()
        ctx["foco_vivo"] = {
            "tipo": "contexto",
            "topico": "GAME_VISION",
            "resposta": "Leitura dos atributos do personagem.",
        }

        fala = resposta_curta_contextual(
            ctx, "não lay, estou falando dos atributos", "CONTINUE",
        )

        self.assertNotIn("GAME_VISION", fala)
        self.assertIn("tela do jogo", fala)


if __name__ == "__main__":
    unittest.main()
