from __future__ import annotations

import os
import tempfile
import unittest

from mente_laylay.integracao.chrome_estado import ChromeEstadoRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
    ListaEstadoSincronizada,
)
from mente_laylay.memoria_mental.estado_continuidades import estado_continuidades_inicial
from mente_laylay.memoria_mental.estado_musical import estado_musical_inicial
from mente_laylay.memoria_mental.estado_percepcao import estado_percepcao_inicial
from mente_laylay.memoria_mental.persistencia_memoria import (
    POLITICA_PERSISTENCIA_MENTE,
    PersistenciaMemoriaRuntime,
)
from mente_laylay.memoria_mental.saude_mente import SaudeMenteRuntime
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    normalizar_resultado_acao,
)
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta
from mente_laylay.personalidade.planejador_resposta import classificar_resultado, planejar_resposta_acao
from mente_laylay.integracao.contexto_execucao_ia import ContextoIntencaoRuntime
from mente_laylay.integracao.contexto_conversa import (
    montar_contexto_conversa_natural,
    montar_contexto_gate_conversa,
)
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt
from mente_laylay.memoria_mental.consciencia_temporal import estado_temporal_inicial
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.coordenador_intencao import resolver_referencias_da_intencao
from mente_laylay.autonomia.agendamento_mental import (
    extrair_agendamento_local,
    resolver_instante_lembrete,
)
from mente_laylay.memoria_mental.contexto_imediato import ContextoImediatoRuntime
from mente_laylay.percepcao.janelas_sistema import resolver_alvo_ambiente
from mente_laylay.memoria_mental.continuidade_semantica import (
    aprender_correcao_semantica,
    interpretar_continuidade_semantica_llm,
    registrar_decisao_semantica,
    resolver_continuidade_semantica,
)
from mente_laylay.memoria_mental.reparacao_conversacional import (
    detectar_reparacao_conversacional,
    registrar_correcao_alvo,
)
from mente_laylay.arquivos.transacao_arquivos import executar_transacao_arquivo
from mente_laylay.arquivos.roteador_arquivos import extrair_criacao_pasta_arquivo
from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_email_notificacao_briefing,
    detectar_volume_ou_midia,
)
from mente_laylay.autonomia.pre_fluxo_contextual import processar_execucao_pratica_precoce
from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.cognicao.pesquisa_contextual import pesquisar_contexto_tema
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.percepcao.ambiente_sistema import detectar_comando_saude
from mente_laylay.memoria_mental.musica_conversacional_runtime import MusicaConversacionalRuntime
from mente_laylay.personalidade.conversa_natural import (
    resposta_conversa_rapida_local,
    responder_conversa_curta_por_tipo,
)


def criar_estado() -> EstadoCompartilhadoRuntime:
    return EstadoCompartilhadoRuntime(
        continuidades=estado_continuidades_inicial(),
        musical=estado_musical_inicial(),
        percepcao=estado_percepcao_inicial(),
        mental=estado_mental_inicial(),
        conversacional={"current_emotion": "calma", "is_speaking": False},
        memoria_conversa={"messages": [], "memoria_fatos": [], "memoria_eventos": []},
    )


class MenteUnicaTests(unittest.TestCase):
    def test_ia_first_nao_executa_pronome_cru_em_busca_musical(self) -> None:
        retrato = {
            "referencia_resolvida": {
                "tipo": "referencia_nomeada", "nome": "Tim Maia", "origem": "nome_explicito",
            }
        }
        resolvida = resolver_referencias_da_intencao(
            {"intent": "MUSIC_SEARCH", "params": {"query": "uma musica dele"}},
            retrato,
        )
        assert resolvida is not None
        assert resolvida["params"]["query"] == "Tim Maia"
        assert resolvida["params"]["query_original"] == "uma musica dele"
        assert resolver_referencias_da_intencao(
            {"intent": "MUSIC_SEARCH", "params": {"query": "uma musica dele"}},
            {},
        ) is None

    def test_detector_deterministico_tambem_resolve_artista_antes_da_arbitragem(self) -> None:
        retrato = {
            "operacao_explicita": "musica_do_referente",
            "intents_permitidos": ["MUSIC_SEARCH"],
            "referencia_resolvida": {"tipo": "referencia_nomeada", "nome": "Tim Maia"},
        }
        ctx = {
            "normalizar_texto": lambda texto: texto.casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "MUSIC_SEARCH", "params": {"query": "uma musica dele"},
            },
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "turno_atual": {"modalidade": "comando"},
            "retrato_turno_atual": retrato,
        }
        intent, _rota = resolver_intencao(
            "coloca uma musica dele então", "pre-ia", ctx
        )
        assert intent is not None
        assert intent["params"]["query"] == "Tim Maia"

    def test_contestacao_rebaixa_confianca_da_resposta_anterior(self) -> None:
        estado = registrar_mente_curta(
            {
                "ultima_resposta": "Tim Maia foi deputado federal.",
                "assunto_da_fala": "Tim Maia",
            },
            texto_usuario="que papo é esse que ele foi para a política?",
            resposta_ia="Você tem razão de estranhar; retiro essa afirmação.",
        )
        contestada = estado["alegacao_contestada"]
        assert contestada["texto"] == "Tim Maia foi deputado federal."
        assert contestada["status"] == "nao_confiavel_ate_verificacao"

    def test_musica_dele_busca_artista_em_vez_de_repetir_faixa(self) -> None:
        decisao = resolver_continuidade_semantica(
            "coloca uma música dele para mim",
            mente={
                "ultima_acao_intent": "MEDIA_CONTROL",
                "ultima_acao_params": {"acao": "replay", "platform": "music"},
                "retrato_turno_atual": {
                    "referencia_resolvida": {
                        "tipo": "artista", "nome": "Seu Jorge", "origem": "nome_explicito",
                    }
                },
            },
        )
        assert decisao.intent == "MUSIC_SEARCH"
        assert decisao.params["query"] == "Seu Jorge"
        assert decisao.params.get("acao") != "replay"

    def test_contexto_conversa_liga_pesquisa_e_percepcao_atual(self) -> None:
        pesquisa = lambda tema: {"ok": True, "tema": tema}
        conteudo = lambda _texto="": {"tipo": "pagina"}
        contexto = montar_contexto_conversa_natural(
            current_emotion="calma",
            mente_integrada_estado={},
            ultimo_topico_conversa="anime",
            foco_vivo={},
            obter_conteudo_atual=conteudo,
            pesquisar_contexto_tema=pesquisa,
            normalizar_texto_curto=None,
            normalizar_texto_com_apelidos=None,
            resumo_mente_integrada_para_prompt=None,
            enviar_mensagem=None,
            extrair_json_da_ia=None,
            ajustar_fala_por_horario=None,
            fala_de_confirmacao_variada=None,
            texto_parece_navegacao_ou_janela_ia=None,
            fala_e_fallback_neutro=None,
            ajustar_tom_por_emocao=None,
        )
        self.assertIs(contexto["_pesquisar_contexto_tema"], pesquisa)
        self.assertIs(contexto["_obter_conteudo_atual"], conteudo)

    def test_playlist_legada_permanece_na_fonte_central(self) -> None:
        estado = criar_estado()
        playlist = estado.vincular_dict("musical", "playlist_state")

        playlist["name"] = "anime"
        playlist["index"] = 2

        atual = estado.obter("musical", "playlist_state")
        self.assertIs(atual, playlist)
        self.assertEqual(atual["name"], "anime")
        self.assertEqual(atual["index"], 2)

    def test_snapshot_nao_permite_mutar_a_mente(self) -> None:
        estado = criar_estado()
        playlist = estado.vincular_dict("musical", "playlist_state")
        playlist["name"] = "rock"

        snapshot = estado.snapshot()
        snapshot["musical"]["playlist_state"]["name"] = "trap"

        self.assertEqual(estado.obter("musical", "playlist_state")["name"], "rock")

    def test_historico_de_mensagens_permanece_unico_e_sincronizado(self) -> None:
        estado = criar_estado()
        mensagens = estado.memoria_conversa_get("messages")

        self.assertIsInstance(mensagens, ListaEstadoSincronizada)
        mensagens.append({"role": "user", "content": "oi"})
        estado.atualizar_campos(
            "memoria_conversa",
            messages=list(mensagens) + [{"role": "assistant", "content": "oi, Pedro"}],
        )

        atuais = estado.memoria_conversa_get("messages")
        self.assertIsInstance(atuais, ListaEstadoSincronizada)
        self.assertEqual([item["role"] for item in atuais], ["user", "assistant"])

    def test_estados_operacionais_legados_ficam_vinculados_a_mente_unica(self) -> None:
        estado = criar_estado()
        bloqueios = estado.vincular_dict("continuidades", "sugestoes_bloqueadas_ate")
        falhas = estado.vincular_dict("mental", "falhas_consecutivas_execucao")
        abas = estado.vincular_lista("percepcao", "abas_sugeridas_fechar")

        bloqueios["contexto_janela"] = 123.0
        falhas["OPEN_URL|youtube"] = 2
        abas.append("https://example.com/antiga")

        snapshot = estado.snapshot()
        self.assertEqual(
            snapshot["continuidades"]["sugestoes_bloqueadas_ate"]["contexto_janela"],
            123.0,
        )
        self.assertEqual(snapshot["mental"]["falhas_consecutivas_execucao"]["OPEN_URL|youtube"], 2)
        self.assertEqual(snapshot["percepcao"]["abas_sugeridas_fechar"], ["https://example.com/antiga"])

    def test_mesclagem_de_retrato_preserva_identidade_dos_estados_vinculados(self) -> None:
        estado = criar_estado()
        abas = estado.vincular_lista("percepcao", "abas_sugeridas_fechar")
        abas.append("https://example.com/antiga")
        retrato = estado.snapshot()["percepcao"]
        retrato["logs_navegador"] = ["Navegação atualizada"]

        estado.mesclar_campos("percepcao", **retrato)

        self.assertIs(estado.obter("percepcao", "abas_sugeridas_fechar"), abas)
        self.assertEqual(abas, ["https://example.com/antiga"])
        self.assertEqual(estado.obter_copia("percepcao", "logs_navegador"), ["Navegação atualizada"])

    def test_chrome_usa_aba_ativa_da_percepcao(self) -> None:
        estado = criar_estado()
        chrome = ChromeEstadoRuntime(
            aba_ativa_getter=lambda: estado.obter_copia("percepcao", "aba_ativa", {}),
            aba_ativa_setter=lambda aba: estado.percepcao_set("aba_ativa", aba),
        )

        chrome.aplicar_updates({
            "aba_titulo_atual": "iFood",
            "aba_url_atual": "https://www.ifood.com.br/",
        })

        aba = estado.obter("percepcao", "aba_ativa")
        self.assertEqual(aba["titulo"], "iFood")
        self.assertEqual(chrome.aba_url_atual, "https://www.ifood.com.br/")

        estado.percepcao_set(
            "aba_ativa",
            {"titulo": "YouTube", "url": "https://www.youtube.com/"},
        )
        self.assertEqual(chrome.aba_titulo_atual, "YouTube")
        self.assertEqual(chrome.aba_url_atual, "https://www.youtube.com/")

    def test_validador_detecta_contrato_completo(self) -> None:
        self.assertTrue(criar_estado().validar_estrutura()["ok"])

    def test_persistencia_nao_carrega_contexto_operacional_velho(self) -> None:
        estado = criar_estado()
        estado.atualizar_campos(
            "mental",
            ultima_acao_intent="CLOSE_APP",
            ultimo_app_janela="steam",
            ultima_decisao_semantica={"dominio": "app", "intent": "CLOSE_APP"},
            aprendizado_continuidade={
                "preferencias_conflito": {"iot>arquivo": 2},
                "correcoes": [],
            },
            registro_semantico={"versao": 1, "entidades": {"artista:tim_maia": {"nome": "Tim Maia"}}},
        )
        runtime = PersistenciaMemoriaRuntime(
            memoria_sqlite=object(),
            base_system_prompt="",
            estado_obter=estado.obter,
            estado_atualizar=estado.atualizar_campos,
        )

        snapshot = runtime.snapshot()

        self.assertNotIn("ultima_acao_intent", snapshot)
        self.assertNotIn("ultimo_app_janela", snapshot)
        self.assertNotIn("ultima_decisao_semantica", snapshot)
        self.assertEqual(
            snapshot["aprendizado_continuidade"]["preferencias_conflito"]["iot>arquivo"],
            2,
        )
        self.assertIn("continuidades", POLITICA_PERSISTENCIA_MENTE["efemero"])
        self.assertEqual(snapshot["politica_persistencia_versao"], 1)
        self.assertEqual(
            snapshot["registro_semantico"]["entidades"]["artista:tim_maia"]["nome"],
            "Tim Maia",
        )

    def test_monitor_saude_expoe_dependencias_ausentes(self) -> None:
        monitor = SaudeMenteRuntime()
        registro = monitor.validar_dependencias(
            "chrome",
            {"estado": object(), "falar": "nao executavel"},
            ("estado", "falar", "enviar"),
            callables=("falar", "enviar"),
        )

        self.assertEqual(registro["status"], "degradado")
        self.assertIn("enviar", registro["ausentes"])
        self.assertIn("falar:nao_callable", registro["ausentes"])

    def test_monitor_saude_reconhece_contrato_completo(self) -> None:
        monitor = SaudeMenteRuntime()
        registro = monitor.validar_dependencias(
            "voz",
            {"falar": lambda: None},
            ("falar",),
            callables=("falar",),
        )

        self.assertEqual(registro["status"], "saudavel")
        self.assertIn("voz=saudavel", monitor.resumo_terminal())

    def test_resultado_legado_vira_contrato_confirmado_quando_validado(self) -> None:
        resultado = normalizar_resultado_acao(
            {"intent": "CLOSE_APP", "params": {"nome_app": "steam"}},
            texto="fecha a steam",
            executou=True,
            status="app_fechado",
            origem="executor",
        )

        self.assertEqual(resultado.alvo, "steam")
        self.assertTrue(resultado.ok)
        self.assertTrue(resultado.confirmado)
        self.assertEqual(classificar_resultado(resultado), "sucesso")

    def test_midia_enviada_sem_validacao_permanece_incerta(self) -> None:
        resultado = normalizar_resultado_acao(
            {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}},
            executou=True,
            status="midia_next",
        )

        self.assertTrue(resultado.ok)
        self.assertIsNone(resultado.confirmado)
        self.assertEqual(classificar_resultado(resultado), "incerto")
        plano = planejar_resposta_acao(resultado, "Pulando pra seguinte.")
        self.assertIn("não consegui confirmar", plano.fala)

    def test_registro_generico_nao_apaga_confirmacao_do_executor(self) -> None:
        estado = estado_mental_inicial()
        preciso = ResultadoAcao(
            intent="IOT_CONTROL",
            status="ligado",
            alvo="ventilador",
            params={"acao": "ligar", "alvo": "ventilador"},
            executou=True,
            confirmado=True,
            origem="executor",
            texto_usuario="liga o ventilador",
        )
        estado = registrar_resultado_execucao(
            estado,
            preciso,
            "liga o ventilador",
            True,
            origem="executor",
            status="ligado",
        )
        estado = registrar_resultado_execucao(
            estado,
            {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "ventilador"}},
            "liga o ventilador",
            True,
            origem="roteador",
        )

        self.assertTrue(estado["ultima_acao_confirmada"])
        self.assertEqual(estado["ultima_acao_status"], "ligado")

    def test_fluxo_tratado_nao_transforma_falha_real_em_sucesso(self) -> None:
        estado = estado_mental_inicial()
        falha = ResultadoAcao(
            intent="IOT_CONTROL",
            status="falha_validacao",
            alvo="ventilador",
            params={"acao": "ligar", "alvo": "ventilador"},
            ok=False,
            executou=False,
            confirmado=False,
            origem="executor",
            detalhe="estado final nao mudou",
            texto_usuario="liga o ventilador",
        )
        estado = registrar_resultado_execucao(
            estado,
            falha,
            "liga o ventilador",
            False,
            origem="executor",
            status="falha_validacao",
        )
        estado = registrar_resultado_execucao(
            estado,
            {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "ventilador"}},
            "liga o ventilador",
            True,
            origem="roteador",
        )

        self.assertFalse(estado["ultima_acao_ok"])
        self.assertFalse(estado["ultima_acao_confirmada"])
        self.assertEqual(estado["ultima_acao_status"], "falha_validacao")
        self.assertEqual(estado["ultima_acao_detalhe"], "estado final nao mudou")

    def test_servicos_de_intencao_so_mantem_dinamico_o_que_nasce_tarde(self) -> None:
        alvo_inicial = lambda *_: "inicial"
        alvo_novo = lambda *_: "novo"
        abrir_inicial = lambda *_: "abrir-inicial"
        abrir_novo = lambda *_: "abrir-novo"
        namespace = {
            "_target_from_params": alvo_inicial,
            "abrir_programa": abrir_inicial,
        }
        runtime = ContextoIntencaoRuntime(
            namespace_getter=lambda: namespace,
            estado_getter=lambda: {"current_emotion": "calma"},
            dependencias_tardias=("abrir_programa",),
        )

        namespace["_target_from_params"] = alvo_novo
        namespace["abrir_programa"] = abrir_novo
        contexto = runtime.montar()

        self.assertIs(contexto["_target_from_params"], alvo_inicial)
        self.assertIs(contexto["abrir_programa"], abrir_novo)
        self.assertEqual(contexto["current_emotion"], "calma")

    def test_gate_conversa_recebe_percepcao_de_conteudo(self) -> None:
        obter = lambda *_: {"tipo": "pagina"}
        contexto = montar_contexto_gate_conversa(
            mente_integrada_estado={},
            foco_vivo={},
            obter_conteudo_atual=obter,
            ultimo_topico_conversa="teste",
        )
        self.assertIs(contexto["_obter_conteudo_atual"], obter)

    def test_resumo_temporal_recebe_texto_usuario_sem_name_error(self) -> None:
        resumo = resumo_mente_integrada_para_prompt(
            texto_usuario="estou falando de pasta",
            ctx={},
            percepcao={},
            mente={"consciencia_temporal": estado_temporal_inicial()},
        )
        self.assertIn("MENTE INTEGRADA", resumo)

    def test_comando_explicito_de_arquivo_vence_contexto_iot(self) -> None:
        ctx = {
            "normalizar_texto": lambda texto: texto.lower(),
            "refinar_contexto_mental": lambda *_: None,
            "extrair_acao_agendada": lambda *_: None,
            "texto_cancela_acao_agora": lambda *_: False,
            "texto_depende_de_contexto": lambda *_: True,
            "detectar_intencao_deterministica": lambda *_: {
                "intent": "DELETE_ITEM",
                "params": {"alvo": "teste", "tipo": "pasta"},
            },
            "resolver_comando_contextual_forcado": lambda *_: {
                "intent": "IOT_CONTROL",
                "params": {"acao": "desligar", "alvo": "tomada_ventilador"},
            },
        }
        resultado, rota = resolver_intencao("apaga a pasta teste", "pre-ia", ctx)
        self.assertEqual(resultado["intent"], "DELETE_ITEM")
        self.assertEqual(rota, "deterministico-explicito")

    def test_apaga_ela_prioriza_arquivo_recente_sobre_iot(self) -> None:
        class EstadoFake:
            mental = {"ultima_habilidade": "arquivos", "ultima_intencao": "CREATE_FOLDER"}

            def substituir(self, dominio, estado):
                self.mental = estado

        runtime = ContextoImediatoRuntime(
            namespace_getter=lambda: {
                "_normalizar_texto_com_apelidos": lambda texto: texto.lower(),
                "_estrutura_arquivo_recente": lambda *_: {"nome": "teste"},
            },
            estado_runtime_getter=lambda: EstadoFake(),
        )
        runtime.resolver_arquivo = lambda *_: {
            "intent": "DELETE_ITEM",
            "params": {"alvo": "teste", "tipo": "pasta"},
        }
        runtime.resolver_iot = lambda *_: {
            "intent": "IOT_CONTROL",
            "params": {"acao": "desligar", "alvo": "tomada_ventilador"},
        }
        runtime.resolver_janela = lambda *_: None
        runtime.resolver_midia = lambda *_: None
        runtime.resolver_acao_geral = lambda *_: None

        resultado = runtime.resolver("apaga ela")
        self.assertEqual(resultado["intent"], "DELETE_ITEM")

    def test_processo_auxiliar_nao_mantem_aplicativo_falsamente_aberto(self) -> None:
        somente_auxiliares = resolver_alvo_ambiente(
            "steam",
            ["Steamservice", "Steamwebhelper"],
            [],
        )
        principal = resolver_alvo_ambiente("steam", ["Steam"], [])

        self.assertFalse(somente_auxiliares["programa_aberto"])
        self.assertTrue(principal["programa_aberto"])

    def test_recriacao_semantica_nao_depende_de_frase_cadastrada(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "DELETE_ITEM",
            "ultima_intencao": "DELETE_ITEM",
            "ultima_habilidade": "arquivos",
            "ultima_estrutura_arquivo_ts": __import__("time").time(),
        })
        estrutura = {"nome": "teste", "arquivo_nome": "nota", "arquivo_conteudo": "oi"}

        for fala in ("cria ela de novo", "refaz aquilo", "traz isso de volta", "restaura ela novamente"):
            with self.subTest(fala=fala):
                decisao = resolver_continuidade_semantica(
                    fala,
                    mente=mente,
                    estrutura_arquivo=estrutura,
                )
                self.assertEqual(decisao.intent, "CREATE_FOLDER")
                self.assertEqual(decisao.params["nome"], "teste")
                self.assertGreaterEqual(decisao.confianca, 0.60)

    def test_repeticao_semantica_iot_reutiliza_acao_real(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "IOT_CONTROL",
            "ultima_acao_params": {"acao": "ligar", "alvo": "tomada_ventilador"},
            "ultimo_dispositivo_iot": "tomada_ventilador",
        })
        decisao = resolver_continuidade_semantica(
            "tenta isso de novo",
            mente=mente,
        )
        self.assertEqual(decisao.intent, "IOT_CONTROL")
        self.assertEqual(decisao.params["acao"], "ligar")

    def test_referencia_semantica_app_respeita_dominio(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "APP_OPEN",
            "ultima_acao_params": {"nome_app": "steam"},
            "ultimo_app_janela": "steam",
        })
        decisao = resolver_continuidade_semantica("fecha ele", mente=mente)
        self.assertEqual(decisao.intent, "CLOSE_APP")
        self.assertEqual(decisao.params["nome_app"], "steam")

    def test_comando_explicito_nao_e_sequestrado_pela_continuidade(self) -> None:
        decisao = resolver_continuidade_semantica(
            "apaga a pasta documentos",
            mente={"ultima_acao_intent": "IOT_CONTROL"},
            estrutura_arquivo={"nome": "teste"},
        )
        self.assertIsNone(decisao.para_intencao())

    def test_llm_semantico_classifica_mas_nao_inventa_alvo(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "DELETE_ITEM",
            "ultima_acao_params": {"alvo": "teste", "tipo": "pasta"},
        })

        def responder(*_args, **_kwargs):
            return '{"dominio":"arquivo","operacao":"REVERTER","acao":"CRIAR","confianca":0.91,"motivo":"pedido de restauracao"}'

        decisao = interpretar_continuidade_semantica_llm(
            "faz aquilo voltar",
            mente=mente,
            estrutura_arquivo={"nome": "teste"},
            enviar_mensagem=responder,
        )
        self.assertEqual(decisao.intent, "CREATE_FOLDER")
        self.assertEqual(decisao.alvo, "teste")

    def test_correcao_semantica_aprende_dominio_correto(self) -> None:
        import time

        mente = estado_mental_inicial()
        decisao = resolver_continuidade_semantica(
            "desliga ela",
            mente={
                **mente,
                "ultima_acao_intent": "IOT_CONTROL",
                "ultima_acao_params": {"acao": "ligar", "alvo": "tomada_ventilador"},
                "ultimo_dispositivo_iot": "tomada_ventilador",
            },
        )
        mente = registrar_decisao_semantica(mente, decisao, "desliga ela")
        mente["ultima_decisao_semantica"]["ts"] = time.time()

        aprendido, evento = aprender_correcao_semantica(
            mente,
            "não Lay, eu estava falando da pasta",
        )

        self.assertEqual(evento["dominio_escolhido"], "iot")
        self.assertEqual(evento["dominio_correto"], "arquivo")
        self.assertEqual(
            aprendido["aprendizado_continuidade"]["preferencias_conflito"]["iot>arquivo"],
            1,
        )
        self.assertEqual(aprendido["ultima_decisao_semantica"], {})

    def test_fala_neutra_nao_cria_aprendizado_semantico(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente["ultima_decisao_semantica"] = {
            "dominio": "iot",
            "intent": "IOT_CONTROL",
            "ts": time.time(),
        }
        aprendido, evento = aprender_correcao_semantica(mente, "tudo bem então")
        self.assertEqual(evento, {})
        self.assertEqual(
            aprendido["aprendizado_continuidade"]["preferencias_conflito"],
            {},
        )

    def test_correcao_semantica_aprende_operacao_no_mesmo_dominio(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente["ultima_decisao_semantica"] = {
            "dominio": "musica",
            "acao": "RETROCEDER",
            "intent": "MEDIA_CONTROL",
            "alvo": "musica",
            "ts": time.time(),
        }
        aprendido, evento = aprender_correcao_semantica(
            mente,
            "não era para voltar a música, era para repetir",
        )
        self.assertEqual(evento["acao_escolhida"], "RETROCEDER")
        self.assertEqual(evento["acao_correta"], "EXECUTAR")
        self.assertEqual(
            aprendido["aprendizado_continuidade"]["preferencias_operacao"]
            ["musica:RETROCEDER>EXECUTAR"],
            1,
        )

    def test_operacao_aprendida_ajuda_fala_implicita(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "MEDIA_CONTROL",
            "ultima_acao_params": {"acao": "prev", "platform": "music"},
            "musica_atual_titulo": "faixa atual",
            "aprendizado_continuidade": {
                "preferencias_conflito": {},
                "preferencias_operacao": {"musica:RETROCEDER>EXECUTAR": 1},
                "correcoes": [],
            },
        })
        decisao = resolver_continuidade_semantica("faz isso de novo", mente=mente)
        self.assertEqual(decisao.intent, "MEDIA_CONTROL")
        self.assertEqual(decisao.params["acao"], "replay")
        self.assertEqual(decisao.acao, "EXECUTAR")

    def test_acao_explicita_vence_preferencia_aprendida(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "MEDIA_CONTROL",
            "ultima_acao_params": {"acao": "prev", "platform": "music"},
            "musica_atual_titulo": "faixa atual",
            "aprendizado_continuidade": {
                "preferencias_conflito": {},
                "preferencias_operacao": {"musica:RETROCEDER>EXECUTAR": 5},
                "correcoes": [],
            },
        })
        decisao = resolver_continuidade_semantica("pausa ela", mente=mente)
        self.assertEqual(decisao.params["acao"], "pause")
        self.assertEqual(decisao.acao, "PAUSAR")

    def test_operacao_sem_executor_e_aprendida_mas_nao_executada(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente["ultima_decisao_semantica"] = {
            "dominio": "arquivo",
            "acao": "REMOVER",
            "intent": "DELETE_ITEM",
            "alvo": "teste.txt",
            "ts": time.time(),
        }
        aprendido, evento = aprender_correcao_semantica(
            mente,
            "não era para apagar o arquivo, era para mover",
        )
        self.assertEqual(evento["acao_correta"], "MOVER")
        aprendido.update({
            "ultima_acao_intent": "DELETE_ITEM",
            "ultima_acao_params": {"alvo": "teste.txt", "tipo": "arquivo"},
        })
        decisao = resolver_continuidade_semantica(
            "faz isso de novo",
            mente=aprendido,
            estrutura_arquivo={"arquivo_nome": "teste.txt"},
        )
        self.assertIsNone(decisao.para_intencao())

    def test_correcao_de_alvo_refaz_operacao_no_app_certo(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "MAXIMIZE_WINDOW",
            "ultima_acao_params": {"nome_app": "steam"},
        })
        reparacao = detectar_reparacao_conversacional(
            "não, o Discord em tela cheia",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
            extrair_app_explicito=lambda _texto: "",
        )
        self.assertEqual(reparacao["tipo"], "operacional")
        self.assertEqual(reparacao["dominio"], "app")
        self.assertEqual(reparacao["alvo_novo"].casefold(), "discord")
        self.assertEqual(reparacao["intencao"]["intent"], "MAXIMIZE_WINDOW")
        self.assertEqual(reparacao["intencao"]["params"]["nome_app"].casefold(), "discord")

        aprendido = registrar_correcao_alvo(mente, reparacao)
        self.assertEqual(
            aprendido["aprendizado_continuidade"]["correcoes_alvo"]
            ["app:steam>discord"],
            1,
        )

    def test_assunto_livre_nao_vira_correcao_de_app(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "APP_OPEN",
            "ultima_acao_params": {"nome_app": "steam"},
        })
        reparacao = detectar_reparacao_conversacional(
            "não Lay, eu estava falando do presidente Lula",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
            extrair_app_explicito=lambda _texto: "",
        )
        self.assertEqual(reparacao["tipo"], "conversacional")
        self.assertEqual(reparacao["alvo_novo"], "presidente lula")

    def test_correcao_combinada_troca_operacao_e_alvo(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "CLOSE_APP",
            "ultima_acao_params": {"nome_app": "steam"},
        })
        reparacao = detectar_reparacao_conversacional(
            "não era para fechar a Steam; era para maximizar o Opera",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
            extrair_app_explicito=lambda texto: "opera" if "opera" in texto else "",
        )
        self.assertEqual(reparacao["tipo"], "operacional")
        self.assertEqual(reparacao["alvo_novo"], "opera")
        self.assertEqual(reparacao["operacao_corrigida"], "MAXIMIZAR")
        self.assertEqual(reparacao["intencao"]["intent"], "MAXIMIZE_WINDOW")
        self.assertEqual(reparacao["intencao"]["params"]["nome_app"], "opera")

    def test_correcao_combinada_nao_executa_operacao_sem_suporte(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "CLOSE_APP",
            "ultima_acao_params": {"nome_app": "steam"},
        })
        reparacao = detectar_reparacao_conversacional(
            "não era para fechar a Steam; era para minimizar o Opera",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
            extrair_app_explicito=lambda texto: "opera" if "opera" in texto else "",
        )
        self.assertEqual(reparacao["tipo"], "nao_suportada")
        self.assertNotIn("intencao", reparacao)

    def test_correcao_de_volume_substitui_nivel_rejeitado(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "VOLUME",
            "ultima_acao_params": {"acao": "set", "nivel_volume": 30},
        })
        reparacao = detectar_reparacao_conversacional(
            "não coloca o volume em 30, coloca em 50",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
        )
        self.assertEqual(reparacao["tipo"], "operacional")
        self.assertEqual(reparacao["intencao"]["intent"], "VOLUME")
        self.assertEqual(reparacao["intencao"]["params"]["nivel_volume"], 50)
        aprendido = registrar_correcao_alvo(mente, reparacao)
        self.assertEqual(
            aprendido["aprendizado_continuidade"]["correcoes_parametros"]["volume:VOLUME"],
            1,
        )

    def test_correcao_de_timer_marca_substituicao_atomica(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "AGENDAR_ACAO",
            "ultima_acao_params": {
                "atraso_segundos": 600,
                "acao_agendada": {
                    "intent": "IOT_CONTROL",
                    "params": {"acao": "desligar", "alvo": "ventilador"},
                },
            },
        })
        reparacao = detectar_reparacao_conversacional(
            "não desliga daqui 10 minutos, desliga daqui 20 minutos",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
        )
        params = reparacao["intencao"]["params"]
        self.assertEqual(reparacao["tipo"], "operacional")
        self.assertEqual(reparacao["intencao"]["intent"], "AGENDAR_ACAO")
        self.assertEqual(params["atraso_segundos"], 1200)
        self.assertTrue(params["substituir_agendamento_anterior"])
        self.assertEqual(params["acao_agendada"]["params"]["alvo"], "ventilador")

    def test_correcao_de_destino_de_arquivo_cria_transacao_segura(self) -> None:
        import time

        mente = estado_mental_inicial()
        mente.update({
            "ts": time.time(),
            "ultima_acao_intent": "CREATE_FOLDER",
            "ultima_acao_params": {"nome": "teste", "pasta_pai": "Downloads"},
        })
        reparacao = detectar_reparacao_conversacional(
            "não cria em Downloads, cria na Área de Trabalho",
            mente,
            normalizar_texto=lambda texto: texto.casefold(),
        )
        self.assertEqual(reparacao["tipo"], "operacional")
        self.assertEqual(reparacao["intencao"]["intent"], "FILE_TRANSACTION")
        self.assertEqual(reparacao["intencao"]["params"]["operacao"], "mover")
        self.assertEqual(reparacao["intencao"]["params"]["destino"], "área de trabalho")

    def test_transacao_arquivo_move_e_valida_sem_sobrescrever(self) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as raiz:
            origem_dir = os.path.join(raiz, "origem")
            destino_dir = os.path.join(raiz, "destino")
            os.makedirs(origem_dir)
            os.makedirs(destino_dir)
            origem = os.path.join(origem_dir, "teste")
            os.makedirs(origem)
            resultado = executar_transacao_arquivo({
                "operacao": "mover",
                "origem": origem,
                "destino": destino_dir,
            })
            self.assertTrue(resultado.sucesso)
            self.assertFalse(os.path.exists(origem))
            self.assertTrue(os.path.isdir(os.path.join(destino_dir, "teste")))

            segunda_origem = os.path.join(origem_dir, "teste")
            os.makedirs(segunda_origem)
            colisao = executar_transacao_arquivo({
                "operacao": "mover",
                "origem": segunda_origem,
                "destino": destino_dir,
            })
            self.assertFalse(colisao.sucesso)
            self.assertEqual(colisao.status, "destino_ja_existe")
            self.assertTrue(os.path.isdir(segunda_origem))

    def test_transacao_arquivo_corrige_nome_e_conteudo(self) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as raiz:
            origem = os.path.join(raiz, "antigo.txt")
            with open(origem, "w", encoding="utf-8") as arquivo:
                arquivo.write("antigo")
            renomeado = executar_transacao_arquivo({
                "operacao": "renomear",
                "origem": origem,
                "novo_nome": "novo.txt",
            })
            self.assertTrue(renomeado.sucesso)
            atualizado = executar_transacao_arquivo({
                "operacao": "editar_conteudo",
                "origem": renomeado.destino,
                "conteudo": "conteúdo certo",
            })
            self.assertTrue(atualizado.sucesso)
            with open(renomeado.destino, "r", encoding="utf-8") as arquivo:
                self.assertEqual(arquivo.read(), "conteúdo certo")

    def test_correcao_natural_de_nome_e_conteudo_gera_transacao(self) -> None:
        import time

        base = estado_mental_inicial()
        base.update({
            "ts": time.time(),
            "ultima_acao_intent": "CREATE_FILE",
            "ultima_acao_params": {"alvo": "antigo.txt", "conteudo": "errado"},
        })
        renomear = detectar_reparacao_conversacional(
            "não chama antigo, chama novo.txt",
            base,
            normalizar_texto=lambda texto: texto.casefold(),
        )
        self.assertEqual(renomear["intencao"]["intent"], "FILE_TRANSACTION")
        self.assertEqual(renomear["intencao"]["params"]["operacao"], "renomear")
        self.assertEqual(renomear["intencao"]["params"]["novo_nome"], "novo.txt")

        conteudo = detectar_reparacao_conversacional(
            "não escreve errado, escreve conteúdo certo",
            base,
            normalizar_texto=lambda texto: texto.casefold(),
        )
        self.assertEqual(conteudo["intencao"]["intent"], "FILE_TRANSACTION")
        self.assertEqual(conteudo["intencao"]["params"]["operacao"], "editar_conteudo")
        self.assertEqual(conteudo["intencao"]["params"]["conteudo"], "conteúdo certo")

    def test_comando_completo_de_playlist_nao_vira_replay(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "MEDIA_CONTROL",
            "ultima_acao_params": {"acao": "replay", "platform": "music"},
            "musica_atual_titulo": "faixa atual",
        })
        decisao = resolver_continuidade_semantica(
            "coloca essa música na playlist anime",
            mente=mente,
        )
        self.assertIsNone(decisao.para_intencao())

    def test_parser_composto_aceita_arquivo_escrito(self) -> None:
        params = extrair_criacao_pasta_arquivo(
            "cria uma pasta chamada roberto e dentro dela um arquivo de texto chamado carlos escrito meu deus"
        )
        self.assertEqual(params["nome"], "roberto")
        self.assertEqual(params["arquivo_nome"], "carlos")
        self.assertEqual(params["arquivo_conteudo"], "meu deus")

    def test_parser_composto_tolera_testo_e_preserva_nome(self) -> None:
        params = extrair_criacao_pasta_arquivo(
            "cria uma pasta chamada teste e dentro dela um arquivo de testo chamado antonio escrito ai meu deus"
        )
        self.assertEqual(params["nome"], "teste")
        self.assertEqual(params["arquivo_nome"], "antonio")
        self.assertEqual(params["arquivo_conteudo"], "ai meu deus")

    def test_renomeia_pronome_usando_estrutura_recente(self) -> None:
        mente = estado_mental_inicial()
        mente.update({"ultima_acao_intent": "CREATE_FOLDER", "ultima_habilidade": "arquivos"})
        decisao = resolver_continuidade_semantica(
            "muda o nome dele para antonio",
            mente=mente,
            estrutura_arquivo={"nome": "teste", "target": "pc_a"},
        )
        self.assertEqual(decisao.intent, "FILE_TRANSACTION")
        self.assertEqual(decisao.params["operacao"], "renomear")
        self.assertEqual(decisao.params["novo_nome"], "antonio")
        self.assertTrue(decisao.params["origem"].endswith(os.path.join("Downloads", "teste")))

    def test_criacao_composta_emite_uma_unica_confirmacao_completa(self) -> None:
        falas = []
        with tempfile.TemporaryDirectory() as raiz:
            resolver = lambda valor: os.path.join(raiz, str(valor or "").strip())

            def criar_pasta(caminho):
                os.makedirs(caminho, exist_ok=True)
                return True

            def criar_arquivo(caminho, conteudo, _modo):
                os.makedirs(os.path.dirname(caminho), exist_ok=True)
                with open(caminho, "w", encoding="utf-8") as arquivo:
                    arquivo.write(conteudo)
                return True

            executou = executar_intencao_arquivos(
                "CREATE_FOLDER",
                {"nome": "teste", "arquivo_nome": "antonio", "arquivo_conteudo": "ai meu deus"},
                "pc_a",
                {
                    "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                    "criar_pasta": criar_pasta,
                    "criar_ou_editar_arquivo": criar_arquivo,
                    "resolver_caminho": resolver,
                    "_registrar_estrutura_arquivo_recente": lambda _dados: None,
                },
                texto_original="cria uma pasta teste e dentro dela um arquivo antonio escrito ai meu deus",
                marcar_resultado=lambda *_args: None,
                registrar_arquivo=lambda *_args: None,
                item_local_existe=lambda caminho, tipo: os.path.isdir(caminho) if tipo == "pasta" else os.path.isfile(caminho),
                resolver_caminho_local=resolver,
                resolver_referencia_arquivo_contextual=lambda alvo, _tipo: alvo,
            )
            self.assertTrue(executou)
            self.assertEqual(len(falas), 1)
            self.assertIn("teste", falas[0])
            self.assertIn("antonio.txt", falas[0])
            with open(os.path.join(raiz, "teste", "antonio.txt"), encoding="utf-8") as arquivo:
                self.assertEqual(arquivo.read(), "ai meu deus")

    def test_mute_desmute_e_email_sao_deterministicos(self) -> None:
        params = lambda **kwargs: kwargs
        mutar = detectar_volume_ou_midia("muta o volume", params_cb=params)
        desmutar = detectar_volume_ou_midia("desmuta", params_cb=params)
        emails = detectar_email_notificacao_briefing("quais meus emails", params_cb=params)
        self.assertEqual(mutar["params"]["acao"], "mute")
        self.assertEqual(desmutar["params"]["acao"], "unmute")
        self.assertEqual(emails["intent"], "EMAIL_READ")

    def test_saude_pc_e_correcao_fonetica_do_instagram(self) -> None:
        self.assertTrue(detectar_comando_saude("como está o meu pc"))
        self.assertTrue(detectar_comando_saude("qual a saúde dele"))
        self.assertEqual(normalizar_texto("abre o instgrm"), "abre o instagram")

    def test_comando_futuro_nao_executa_no_pre_fluxo(self) -> None:
        chamadas = []
        ctx = {
            "_resolver_comando_contextual_forcado": lambda texto: chamadas.append(texto) or {
                "intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "ventilador"}
            },
            "processar_comando_deterministico": lambda texto, origem: chamadas.append((texto, origem)) or True,
        }
        ok, _ = processar_execucao_pratica_precoce(
            ctx,
            "liga o ventilador daqui 20 segundos",
        )
        self.assertTrue(ok)
        self.assertEqual(chamadas, [("liga o ventilador daqui 20 segundos", "pre-ia")])

    def test_confirmacao_musical_usa_sugestao_pendente(self) -> None:
        falas = []
        execucoes = []
        runtime = MusicaConversacionalRuntime(
            estado_mental_getter=lambda: {},
            normalizar_texto=normalizar_texto,
            falar=lambda fala, *_args: falas.append(fala),
            registrar_mente_curta=lambda *_args, **_kwargs: None,
            executar_intencao=lambda intent, texto: execucoes.append((intent, texto)) or True,
            registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        )
        self.assertTrue(runtime.responder_pedido_direcao("me recomenda uma música nova"))
        self.assertTrue(runtime.processar_confirmacao("quero algo mais pesado"))
        self.assertTrue(runtime.processar_confirmacao("pode colocar"))
        self.assertEqual(execucoes[-1][0]["intent"], "MUSIC_SEARCH")
        self.assertIn(execucoes[-1][0]["params"]["query"], falas[-1] if falas else execucoes[-1][1])

    def test_recomendacao_respeita_artista_e_eu_quero_confirma(self) -> None:
        falas = []
        execucoes = []
        runtime = MusicaConversacionalRuntime(
            estado_mental_getter=lambda: {},
            normalizar_texto=normalizar_texto,
            falar=lambda fala, *_args: falas.append(fala),
            registrar_mente_curta=lambda *_args, **_kwargs: None,
            executar_intencao=lambda intent, texto: execucoes.append((intent, texto)) or True,
            registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        )
        self.assertTrue(runtime.responder_pedido_direcao("me recomenda uma música do Rubel"))
        self.assertIn("Rubel - ", falas[-1])
        self.assertTrue(runtime.processar_confirmacao("eu quero"))
        self.assertEqual(execucoes[-1][0]["params"]["query"], "Rubel - Quando Bate Aquela Saudade")

    def test_pergunta_sem_interrogacao_nao_responde_pendencia_antiga(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import (
            texto_parece_resposta_curta_a_pergunta,
        )

        self.assertFalse(texto_parece_resposta_curta_a_pergunta("como ta a vida lay", normalizar_texto))
        self.assertFalse(texto_parece_resposta_curta_a_pergunta("e como que ta a vida", normalizar_texto))
        self.assertTrue(texto_parece_resposta_curta_a_pergunta("estou bem sim", normalizar_texto))

    def test_desistencia_reverte_acao_iot_ja_confirmada(self) -> None:
        from mente_laylay.memoria_mental.continuidade_semantica import (
            resolver_continuidade_semantica,
        )

        mente = {
            "ultima_acao_intent": "IOT_CONTROL",
            "ultima_acao_params": {"acao": "ligar", "alvo": "tomada_ventilador"},
            "ultima_acao_alvo": "tomada_ventilador",
            "ultima_acao_confirmada": True,
            "ultima_acao_ok": True,
        }
        resultado = resolver_continuidade_semantica(
            "quero mais não", mente=mente
        ).para_intencao()
        self.assertEqual(resultado["intent"], "IOT_CONTROL")
        self.assertEqual(resultado["params"], {
            "acao": "desligar", "alvo": "tomada_ventilador",
        })
        self.assertEqual(resultado["_semantica"]["operacao"], "REVERTER")

    def test_desistencia_sem_acao_confirmada_continua_cancelamento(self) -> None:
        reversao_insegura = {
            "intent": "IOT_CONTROL",
            "params": {"acao": "desligar", "alvo": "ventilador"},
            "_semantica": {"operacao": "", "confianca": 0.45},
        }
        resultado, rota = resolver_intencao("quero mais não", "chat", {
            "normalizar_texto": normalizar_texto,
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: True,
            "resolver_comando_contextual_forcado": lambda _texto: reversao_insegura,
        })
        self.assertEqual(resultado["intent"], "CANCELAR_ACAO")
        self.assertEqual(rota, "imediato")

    def test_confirmacoes_e_recusas_nao_viram_topico_de_memoria(self) -> None:
        from mente_laylay.memoria_mental.continuidade_conversa import (
            extrair_topico_conversa,
            topico_memoria_valido,
        )

        self.assertFalse(topico_memoria_valido("quero sim", normalizar_texto))
        self.assertFalse(topico_memoria_valido("quero ele mais não", normalizar_texto))
        self.assertEqual(
            extrair_topico_conversa(
                "quero sim", "música do Rubel", normalizar_texto_curto=normalizar_texto,
            ),
            "música do Rubel",
        )
        self.assertEqual(
            extrair_topico_conversa(
                "quero ele mais não", "quero sim", normalizar_texto_curto=normalizar_texto,
            ),
            "",
        )

    def test_falha_tecnica_nao_fabrica_raiva(self) -> None:
        plano = planejar_resposta_acao(
            ResultadoAcao(
                status="indisponivel", alvo="ventilador",
                executou=False, confirmado=False,
            ),
            "O ventilador não respondeu agora.",
        )
        self.assertEqual(plano.classe, "falha")
        self.assertEqual(plano.emocao, "calma")
        self.assertEqual(plano.nivel, 1)

    def test_fala_proativa_nao_inventa_relacao_com_topico(self) -> None:
        from mente_laylay.personalidade.fala_proativa import compor_fala_proativa

        fala, _emocao, _nivel = compor_fala_proativa(
            [{"tipo": "rotina", "texto": "Você costuma usar Laylay.py agora.", "ts": 1}],
            obter_contexto_perceptivo=lambda: {
                "periodo": "tarde", "topico_ativo": "música", "humor": 0,
                "emocao": "calma",
            },
            normalizar_segmento_fala=lambda texto: str(texto),
            normalizar_texto_com_apelidos=normalizar_texto,
            ajustar_tom_por_emocao=lambda texto, *_args: texto,
            fallback_fala_neutra="Tô por aqui.",
        )
        self.assertIn("Você costuma usar Laylay.py agora", fala)
        self.assertNotIn("Isso conversa com", fala)
        self.assertNotIn("Seu cérebro", fala)
        self.assertNotIn("Seu horário tá puxando", fala)

    def test_modo_chat_usa_abertura_dinamica(self) -> None:
        from mente_laylay.autonomia.modo_chat import ModoChatRuntime

        runtime = ModoChatRuntime(
            estado_getter=lambda: {"modo_chat": False},
            estado_setter=lambda _ativo: None,
            messages_getter=lambda: [],
            fala_confirmacao=lambda *_args, **_kwargs: "abertura estática",
            gerar_abertura=lambda: "Hoje eu cheguei com outra energia.",
            falar=lambda *_args: None,
            salvar_memoria=lambda: None,
        )
        self.assertEqual(runtime._criar_fala(True), "Hoje eu cheguei com outra energia.")

    def test_pedido_natural_chega_limpo_ao_roteador(self) -> None:
        from mente_laylay.autonomia.roteador_deterministico import (
            normalizar_pedido_natural,
            preparar_entrada_deterministica,
        )

        casos = {
            "você pode ligar o ventilador": "ligar o ventilador",
            "será que dá pra você abrir o chrome": "abrir o chrome",
            "faz o favor de abaixar o volume": "abaixar o volume",
            "eu queria que você fechasse o opera": "fecha o opera",
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                limpo, modalidade = normalizar_pedido_natural(normalizar_texto(entrada))
                self.assertEqual(limpo, esperado)
                self.assertEqual(modalidade, "pedido")

        preparo = preparar_entrada_deterministica(
            "será que você pode abrir o Chrome?",
            normalizar_texto=normalizar_texto,
            texto_conversa_casual_sem_acao=lambda texto: texto.startswith("sera que"),
            texto_bloqueia_playlist_agora=lambda _texto: False,
            texto_social_curto=lambda _texto: False,
            ignorar_token_solto=lambda _texto: False,
            fluxo_prioritario_da_ia=lambda _texto: False,
            texto_expresso_melhor_no_deterministico=lambda _texto: True,
            texto_depende_de_contexto=lambda _texto: False,
            limpar_destino_pc_b=lambda texto: texto,
        )
        self.assertEqual(preparo["status"], "ok")
        self.assertEqual(preparo["texto_normalizado"], "abrir o chrome")

    def test_pensamento_nao_vira_comando_natural(self) -> None:
        from mente_laylay.autonomia.roteador_deterministico import normalizar_pedido_natural

        texto, modalidade = normalizar_pedido_natural("acho que vou ligar o ventilador")
        self.assertEqual(texto, "acho que vou ligar o ventilador")
        self.assertEqual(modalidade, "deliberativo")

    def test_pergunta_musical_com_duas_opcoes_preserva_continuidade(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import (
            classificar_pergunta_com_proposito,
        )
        from mente_laylay.memoria_mental.continuidade_conversa import (
            responder_pergunta_aberta,
        )

        classificada = classificar_pergunta_com_proposito("Quer ouvir um desses?")
        self.assertEqual(classificada["proposito"], "escolha")
        fala = responder_pergunta_aberta(
            "quero sim",
            pergunta_aberta={**classificada, "tipo": "resposta_curta", "topico": "música"},
            normalizar_texto_curto=normalizar_texto,
        )
        self.assertIn("escolher qual dos dois", fala)
        self.assertNotIn("próximo passo", fala)

    def test_oferta_e_feedback_musical_vivem_na_mente_unica(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import (
            estado_mental_inicial,
            oferta_pendente_ativa,
            registrar_feedback_musical_conversacional,
            registrar_oferta_pendente,
        )
        from mente_laylay.memoria_mental.musica_conversacional import (
            sugestao_musical_nova_conversacional,
        )

        mente = registrar_oferta_pendente(
            estado_mental_inicial(),
            'Eu tentaria "Recomeçar" de Tim Bernardes. Quer ouvir essa?',
        )
        oferta = oferta_pendente_ativa(mente)
        self.assertEqual(oferta["intent"], "MUSIC_SEARCH")
        self.assertEqual(
            oferta["opcoes"][0]["params"]["query"],
            "Tim Bernardes - Recomeçar",
        )

        mente = registrar_feedback_musical_conversacional(
            mente, "aí não, não gosto de Tim Bernardes"
        )
        self.assertLess(mente["preferencias_musicais"]["artistas"]["Tim Bernardes"], 0)
        self.assertFalse(mente["oferta_pendente"])
        for _ in range(20):
            sugestao = sugestao_musical_nova_conversacional(
                "algo calmo", normalizar_texto=normalizar_texto, estado_mental=mente,
            )
            self.assertNotIn("Tim Bernardes", sugestao)

    def test_fala_proativa_respeita_porteiro_final(self) -> None:
        from mente_laylay.personalidade.voz_runtime import VozRuntime

        class TimerFalso:
            daemon = False
            def __init__(self, _atraso, callback):
                self.callback = callback
            def is_alive(self):
                return False
            def start(self):
                return None

        runtime = VozRuntime(
            fallback_fala="fallback", voice="voz",
            edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda _itens: ("proativa", "calma", 1),
            ajustar_estado_fala_cb=lambda *_args: None,
            proativa_permitida_cb=lambda: False,
            interrupt_event=type("Evento", (), {"is_set": lambda self: False})(),
            timer_factory=TimerFalso,
        )
        self.assertFalse(runtime.agendar_fala_proativa("rotina", "abre Laylay.py"))
        self.assertEqual(runtime.proativa_buffer, [])

    def test_noite_chata_nao_e_saudacao(self) -> None:
        from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
        from mente_laylay.personalidade.conversa_natural import classificar_conversa_curta_local

        leitura = analisar_intencao_emocional(
            "que noite chata", normalizar_texto=normalizar_texto,
        )
        self.assertEqual(leitura["emocao"], "tedio")
        classificacao = classificar_conversa_curta_local({
            "_normalizar_texto_curto": normalizar_texto,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "_registrar_leitura_emocional_usuario": lambda _leitura: None,
        }, "noite chata")
        self.assertEqual(classificacao["tipo"], "EMOTIONAL_STATE")

    def test_tedio_recebe_resposta_concreta_sem_topico_velho(self) -> None:
        ctx = {
            "_normalizar_texto_curto": normalizar_texto,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "_registrar_leitura_emocional_usuario": lambda _leitura: None,
            "ultimo_topico_conversa": "não odeio pabllo",
            "foco_vivo": {"tipo": "conversa", "topico": "Laylay.py"},
            "mente_integrada_estado": {},
        }
        resposta = responder_conversa_curta_por_tipo(ctx, "EMOTIONAL_STATE", "noite chata")
        self.assertTrue(any(p in resposta.casefold() for p in ("música", "musica", "filme", "assistir")))
        self.assertNotIn("pabllo", resposta.casefold())
        self.assertNotIn("laylay.py", resposta.casefold())

    def test_recomendacao_generica_continua_tedio_recente(self) -> None:
        ctx = {
            "_normalizar_texto_curto": normalizar_texto,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "mente_integrada_estado": {"emocao_usuario": "tedio"},
            "ultimo_topico_conversa": "assunto velho",
            "foco_vivo": {},
        }
        resposta = responder_conversa_curta_por_tipo(ctx, "OPINION", "poderia me recomendar algo")
        self.assertIn("música", resposta.casefold())
        self.assertNotIn("assunto velho", resposta.casefold())

    def test_estilo_curto_responde_pergunta_musical_anterior(self) -> None:
        from mente_laylay.memoria_mental.musica_conversacional import (
            sugestao_musical_nova_conversacional,
            texto_pede_direcao_musical_generica,
        )
        estado = {
            "ultima_resposta": "Pra tirar essa noite do lugar, eu começaria por música. Você quer algo romântico, calmo ou mais pesado?"
        }
        self.assertTrue(texto_pede_direcao_musical_generica(
            "romântica", estado_mental=estado, normalizar_texto=normalizar_texto,
        ))
        sugestao = sugestao_musical_nova_conversacional(
            "romântica", estado_mental=estado, normalizar_texto=normalizar_texto,
        )
        self.assertTrue(any(artista in sugestao for artista in ("Tim Bernardes", "Rubel", "Cicero", "Ana Frango Eletrico")))

    def test_escolha_musica_consumida_sem_ia_e_tipo_o_que_nao_puxa_topico_velho(self) -> None:
        from mente_laylay.memoria_mental.musica_conversacional import texto_pede_direcao_musical_generica
        pergunta = "Noite assim se arrasta mesmo. Quer que eu puxe uma música, um filme curto ou alguma ideia pra gente fazer agora?"
        estado = {"ultima_resposta": pergunta}
        self.assertTrue(texto_pede_direcao_musical_generica(
            "pode ser uma música", estado_mental=estado, normalizar_texto=normalizar_texto,
        ))
        ctx = {
            "_normalizar_texto_curto": normalizar_texto,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "mente_integrada_estado": {
                "ultima_resposta": pergunta,
                "ultima_afirmacao": pergunta.split(".")[0],
                "continuidade_fala_ts": __import__("time").time(),
            },
            "ultimo_topico_conversa": "meu nome",
            "foco_vivo": {"tipo": "conversa", "topico": "meu nome"},
        }
        resposta = resposta_conversa_rapida_local(ctx, "tipo o que?")
        self.assertTrue(any(p in resposta.casefold() for p in ("música", "musica", "filme", "assistir")))
        self.assertNotIn("meu nome", resposta.casefold())

    def test_fila_emite_uma_resposta_por_turno(self) -> None:
        from mente_laylay.personalidade.voz_runtime import VozRuntime

        runtime = VozRuntime(
            fallback_fala="fallback", voice="voz",
            edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
            ajustar_estado_fala_cb=lambda *_args: None,
            chave_turno_cb=lambda: 123.0,
            interrupt_event=type("Evento", (), {"is_set": lambda self: False})(),
        )
        runtime.iniciar_worker = lambda: None
        self.assertTrue(runtime.falar("Pronto, desliguei o ventilador e confirmei o estado."))
        self.assertFalse(runtime.falar("Tô aqui."))
        self.assertEqual(runtime.fila.qsize(), 1)

    def test_fila_prefere_resultado_real_a_fala_generica_no_mesmo_turno(self) -> None:
        from mente_laylay.personalidade.voz_runtime import VozRuntime

        runtime = VozRuntime(
            fallback_fala="fallback", voice="voz",
            edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
            limpar_para_voz_cb=lambda texto: texto,
            formatar_mensagem_cb=lambda texto, **_kwargs: texto,
            ducking_volume_cb=lambda _ativo: None,
            modular_audio_params_cb=lambda *_args: ("", "", ""),
            compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
            ajustar_estado_fala_cb=lambda *_args: None,
            chave_turno_cb=lambda: 321.0,
            interrupt_event=type("Evento", (), {"is_set": lambda self: False})(),
        )
        runtime.iniciar_worker = lambda: None
        runtime.falar("Estou aqui. Me fala o próximo passo.")
        runtime.falar("Pronto, desliguei o ventilador e confirmei o estado.")
        runtime.falar("Tô aqui.")

        self.assertEqual(runtime.fila.qsize(), 1)
        pedido = runtime.fila.get_nowait()
        self.assertIn("desliguei o ventilador", pedido["texto"])

    def test_status_pc_e_dinamico_e_sem_palavrao(self) -> None:
        from mente_laylay.percepcao.ambiente_sistema import montar_status_saude

        class Memoria:
            percent = 72
        class Psutil:
            @staticmethod
            def cpu_percent(interval=1):
                return 97
            @staticmethod
            def virtual_memory():
                return Memoria()
            @staticmethod
            def process_iter(_campos):
                return []

        falas = {montar_status_saude(Psutil()) for _ in range(4)}
        self.assertGreater(len(falas), 1)
        for fala in falas:
            self.assertIn("97%", fala)
            self.assertIn("72%", fala)
            self.assertNotIn("caralho", fala.casefold())

    def test_nada_para_fazer_e_conversa_nao_comando(self) -> None:
        from mente_laylay.autonomia.porteiro_acoes import (
            texto_conversa_casual_sem_acao,
        )
        from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional

        texto = "tem nada para fazer nessa noite"
        self.assertTrue(texto_conversa_casual_sem_acao(texto))
        self.assertEqual(
            analisar_intencao_emocional(texto, normalizar_texto=normalizar_texto)["emocao"],
            "tedio",
        )
        self.assertFalse(texto_conversa_casual_sem_acao("liga o ventilador"))

    def test_nova_pergunta_nao_responde_pendencia_antiga(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import (
            texto_parece_resposta_curta_a_pergunta,
        )

        self.assertFalse(texto_parece_resposta_curta_a_pergunta(
            "vamos fazer o que hj", normalizar_texto,
        ))

    def test_resposta_sobre_dia_consumida_com_proposito_sem_perder_contexto(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import (
            classificar_pergunta_com_proposito,
            pergunta_aberta_ativa,
            registrar_pergunta_aberta,
        )
        from mente_laylay.memoria_mental.continuidade_conversa import responder_pergunta_aberta
        classificacao = classificar_pergunta_com_proposito("Qual foi a boa de hoje?")
        self.assertEqual(classificacao["proposito"], "dia_usuario")
        estado = registrar_pergunta_aberta({}, "Qual foi a boa de hoje?", topico="dia do Pedro")
        pendente = pergunta_aberta_ativa(estado)
        self.assertEqual(pendente["proposito"], "dia_usuario")
        resposta = responder_pergunta_aberta(
            "a de hoje nao tem anda demais",
            pergunta_aberta=pendente,
            normalizar_texto_curto=normalizar_texto,
        )
        self.assertTrue(any(p in resposta.casefold() for p in ("dia", "hoje", "noite")))
        self.assertNotIn("não anda demais", resposta.casefold())

    def test_o_que_aconteceu_cobra_promessa_imediata_nao_topico_antigo(self) -> None:
        import time
        ctx = {
            "_normalizar_texto_curto": normalizar_texto,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "mente_integrada_estado": {
                "ultima_promessa_tipo": "contar_experiencia",
                "ultima_promessa_texto": "Posso te contar uma coisa leve que aconteceu comigo hoje. Quer?",
                "ultima_promessa_ts": time.time(),
                "ultima_resposta": "Posso te contar uma coisa leve que aconteceu comigo hoje. Quer?",
                "continuidade_fala_ts": time.time(),
            },
            "ultimo_topico_conversa": "nao anda demais",
            "foco_vivo": {"tipo": "conversa", "topico": "nao anda demais"},
        }
        resposta = resposta_conversa_rapida_local(ctx, "o que aconteceu?")
        self.assertTrue(any(p in resposta.casefold() for p in ("não existia", "nao existia", "não quero inventar", "nada específico")))
        self.assertNotIn("ponto sobre nao anda demais", resposta.casefold())

    def test_filtro_rejeita_assunto_sem_relacao_com_a_fala(self) -> None:
        from mente_laylay.memoria_mental.continuidade_conversa import assunto_coerente_com_fala
        self.assertFalse(assunto_coerente_com_fala("nao anda demais", "Tô bem sim."))
        self.assertTrue(assunto_coerente_com_fala("música romântica", "Eu escolheria uma música romântica agora."))

    def test_prompt_nao_injeta_assunto_incoerente_nem_topicos_em_turno_novo(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "turno_atual": {
                "modalidade": "conversa", "normalizado": "quero falar de astronomia",
                "confianca": 0.96, "motivo": "novo assunto",
            },
            "assunto_da_fala": "nao anda demais",
            "ultima_afirmacao": "Tô bem sim.",
            "continuidade_fala_ts": __import__("time").time(),
        })
        resumo = resumo_mente_integrada_para_prompt(
            texto_usuario="quero falar de astronomia", ctx={}, percepcao={}, mente=mente,
            auto_resumo="RESUMO VELHO", memoria_quente="MEMORIA VELHA",
            topicos_prompt="TOPICO VELHO", aprendizados="PREFERENCIA RELEVANTE",
        )
        self.assertNotIn("assunto=nao anda demais", resumo)
        self.assertNotIn("RESUMO VELHO", resumo)
        self.assertNotIn("MEMORIA VELHA", resumo)
        self.assertNotIn("TOPICO VELHO", resumo)
        self.assertIn("PREFERENCIA RELEVANTE", resumo)

    def test_pergunta_de_referencia_filtra_topico_ativo_incoerente(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "turno_atual": {
                "modalidade": "pergunta", "normalizado": "o que aconteceu",
                "confianca": 0.96, "motivo": "referência à fala anterior",
            },
            "ultima_afirmacao": "Tô bem sim.",
            "assunto_da_fala": "nao anda demais",
            "foco_conversacional_topico": "nao anda demais",
            "foco_conversacional_tipo": "conversa",
        })
        resumo = resumo_mente_integrada_para_prompt(
            texto_usuario="o que aconteceu?",
            ctx={"topico_ativo": "nao anda demais"}, percepcao={}, mente=mente,
        )
        self.assertNotIn("Topico ativo: nao anda demais", resumo)
        self.assertNotIn("topico=nao anda demais", resumo)
        self.assertIn("afirmacao=Tô bem sim.", resumo)

    def test_seletor_central_explica_contexto_aceito_e_rejeitado(self) -> None:
        import time
        from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno
        mente = {
            "ultima_resposta": "Posso te contar uma coisa que aconteceu hoje. Quer?",
            "ultima_pergunta": "Quer?",
            "continuidade_fala_ts": time.time(),
            "ultima_promessa_texto": "Posso te contar uma coisa que aconteceu hoje. Quer?",
            "ultima_promessa_ts": time.time(),
            "foco_conversacional_topico": "meu nome",
            "foco_conversacional_ts": time.time() - 30,
        }
        selecao = selecionar_contexto_turno(
            "o que aconteceu?",
            turno={"modalidade": "pergunta", "texto": "o que aconteceu?"},
            mente=mente,
            contexto_perceptivo={"topico_ativo": "meu nome"},
        )
        origens = {item["origem"] for item in selecao["selecionados"]}
        self.assertIn("promessa", origens)
        self.assertNotIn("topico_ativo", origens)
        self.assertTrue(all("base=" in item["evidencia"] for item in selecao["selecionados"]))

    def test_vamos_ouvir_por_clima_e_comando_musical(self) -> None:
        from mente_laylay.autonomia.roteador_deterministico import (
            detectar_musica_ou_playlist_direta,
        )

        resultado = detectar_musica_ou_playlist_direta(
            "vamos ouvir uma romantica",
            texto_sem_destino="vamos ouvir uma romantica",
            texto_bruto="vamos ouvir uma romântica",
            params_cb=lambda **kwargs: kwargs,
            detectar_playlist_nome_direto=lambda _texto: "",
            normalizar_query_musical=lambda texto: texto,
        )
        self.assertEqual(resultado["intent"], "MUSIC_SEARCH")
        self.assertEqual(resultado["params"]["query"], "romantica")

    def test_resposta_funcional_nao_vira_topico(self) -> None:
        from mente_laylay.memoria_mental.continuidade_conversa import (
            extrair_topico_conversa,
            topico_memoria_valido,
        )

        self.assertFalse(topico_memoria_valido("pode escolher entao", normalizar_texto))
        self.assertEqual(extrair_topico_conversa(
            "pode escolher então", "música romântica",
            normalizar_texto_curto=normalizar_texto,
        ), "música romântica")

    def test_prompt_persistido_antigo_e_substituido_pelo_atual(self) -> None:
        from mente_laylay.memoria_mental.persistencia_memoria import carregar_memoria

        class Memoria:
            @staticmethod
            def carregar_estado():
                return {"messages": [
                    {"role": "system", "content": "prompt antigo"},
                    {"role": "user", "content": "oi"},
                ], "registro_semantico": {"versao": 1, "correcoes": [{"texto": "correção durável"}]}}

        dados = carregar_memoria(Memoria(), "prompt atual")
        sistemas = [m for m in dados["messages"] if m["role"] == "system"]
        self.assertEqual(sistemas, [{"role": "system", "content": "prompt atual"}])
        self.assertEqual(dados["messages"][1]["content"], "oi")
        self.assertEqual(dados["registro_semantico"]["correcoes"][0]["texto"], "correção durável")

    def test_mas_o_que_segue_para_contexto_completo(self) -> None:
        from mente_laylay.personalidade.conversa_natural import (
            responder_conversa_curta_por_tipo,
        )

        self.assertEqual(
            responder_conversa_curta_por_tipo({}, "QUESTION", "vamos sim, mas o que?"),
            "",
        )

    def test_conversa_comum_nao_rejeita_sugestao_invisivel(self) -> None:
        from mente_laylay.autonomia.fluxos_conversa import _pendencia_combina_com_texto

        contexto = {"foco_vivo": {}}
        self.assertFalse(_pendencia_combina_com_texto(
            contexto, "rotina", "noite chata", "Laylay.py",
        ))
        self.assertTrue(_pendencia_combina_com_texto(
            contexto, "rotina", "nao", "Laylay.py",
        ))

    def test_pergunta_negativa_nao_abre_aplicativo_interrogativo(self) -> None:
        from mente_laylay.autonomia.roteador_deterministico import (
            extrair_intencao_abrir_app,
            preparar_entrada_deterministica,
        )

        self.assertIsNone(extrair_intencao_abrir_app(
            "não abre o que?", normalizar_texto=normalizar_texto,
            limpar_destino=lambda texto: texto, apps_map={}, sites_diretos={},
        ))
        preparo = preparar_entrada_deterministica(
            "não abre o que?", normalizar_texto=normalizar_texto,
            texto_conversa_casual_sem_acao=lambda _texto: False,
            texto_bloqueia_playlist_agora=lambda _texto: False,
            texto_social_curto=lambda _texto: False,
            ignorar_token_solto=lambda _texto: False,
            fluxo_prioritario_da_ia=lambda _texto: False,
            texto_expresso_melhor_no_deterministico=lambda _texto: False,
            texto_depende_de_contexto=lambda _texto: False,
            limpar_destino_pc_b=lambda texto: texto,
        )
        self.assertEqual(preparo["status"], "ignorar")
        self.assertEqual(preparo["modalidade"], "pergunta_negativa")

    def test_modalidade_unica_protege_conversa_e_pergunta(self) -> None:
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

        classificar = lambda texto: classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=lambda valor: any(
                termo in valor for termo in ("liga o ventilador", "abre o chrome")
            ),
        )["modalidade"]
        self.assertEqual(classificar("noite chata"), "conversa")
        self.assertEqual(classificar("não abre o que?"), "pergunta")
        self.assertEqual(classificar("como assim"), "pergunta")
        self.assertEqual(classificar("liga o ventilador"), "comando")
        self.assertEqual(classificar("acho que vou ligar o ventilador"), "deliberacao")
        self.assertEqual(classificar("quero sim"), "confirmacao")
        self.assertEqual(classificar("agora não"), "recusa")
        self.assertEqual(classificar("me lembra de pegar um refri daqui 5 minutos"), "comando")

    def test_turno_misto_preserva_conversa_e_comando(self) -> None:
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
        turno = classificar_modalidade_turno(
            "tô cansado, coloca uma música calma",
            normalizar_texto=normalizar_texto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
        self.assertEqual(turno["modalidade_geral"], "misto")
        self.assertEqual(turno["ato_principal"], "comando")
        self.assertEqual(turno["atos"], ["conversa", "comando"])
        self.assertEqual(turno["texto_conversacional"], "to cansado")
        self.assertEqual(turno["texto_operacional"], "coloca uma musica calma")

    def test_resposta_de_acao_reconhece_contexto_humano_do_turno_misto(self) -> None:
        plano = planejar_resposta_acao(ResultadoAcao(
            intent="IOT_CONTROL", status="ligado", alvo="ventilador",
            executou=True, confirmado=True,
            texto_usuario="essa noite tá quente demais, liga o ventilador pra mim",
        ), "Pronto, liguei o ventilador.")
        self.assertIn("quente", plano.fala.casefold())
        self.assertIn("liguei", plano.fala.casefold())

    def test_pre_fluxo_misto_detecta_so_comando_mas_preserva_fala_inteira(self) -> None:
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_comando_deterministico_precoce
        chamadas = []
        ctx = {
            "mente_integrada_estado": {
                "turno_atual": {
                    "ato_principal": "comando",
                    "modalidade_geral": "misto",
                    "texto_operacional": "liga o ventilador",
                    "texto_conversacional": "essa noite ta quente demais",
                }
            },
            "processar_comando_deterministico": lambda deteccao, origem, original: chamadas.append(
                (deteccao, origem, original)
            ) or True,
        }
        ok, _ = processar_comando_deterministico_precoce(
            ctx, "essa noite tá quente demais, liga o ventilador", origem="pre-ia",
        )
        self.assertTrue(ok)
        self.assertEqual(chamadas, [(
            "liga o ventilador", "pre-ia", "essa noite tá quente demais, liga o ventilador"
        )])

    def test_correcao_de_nome_e_local_e_nao_chama_ia(self) -> None:
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_identidade_usuario
        falas = []
        mente = {"nome_usuario": "Pedro"}
        ctx = {
            "mente_integrada_estado": mente,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
        }
        self.assertTrue(processar_identidade_usuario(ctx, "meu nome não é antonio")[0])
        self.assertIn("Pedro", falas[-1])
        self.assertIn("não Antonio", falas[-1])
        self.assertTrue(processar_identidade_usuario(ctx, "meu nome é pedro")[0])
        self.assertEqual(mente["nome_usuario"], "Pedro")
        self.assertEqual(len(falas), 2)

    def test_json_malformado_nunca_vira_fala_literal(self) -> None:
        from mente_laylay.autonomia.processamento_resposta_ia import limpar_resposta_da_ia
        bruto = '{"comandos": ["chamada": "Pedro"], "aprendizados": ["corrigir nome: Pedro"], "humor": "carinhoso"}'
        fala, comandos = limpar_resposta_da_ia(bruto, fallback_fala="Não entendi direito.")
        self.assertEqual(fala, "Não entendi direito.")
        self.assertEqual(comandos, [])
        self.assertNotIn("comandos", fala)

    def test_sugestao_sem_acao_pratica_e_rejeitada(self) -> None:
        from mente_laylay.cognicao.interpretacao_intencao import sugestao_acao_valida

        invalida = {
            "intent": "SUGGEST_ACTION",
            "params": {"tipo": "conversa", "assunto": "nota máxima em IA"},
        }
        valida = {
            "intent": "SUGGEST_ACTION",
            "params": {
                "acao_sugerida": {
                    "intent": "IOT_CONTROL",
                    "params": {"acao": "ligar", "alvo": "ventilador"},
                }
            },
        }
        self.assertFalse(sugestao_acao_valida(invalida))
        self.assertTrue(sugestao_acao_valida(valida))

    def test_sugestao_invalida_nao_engole_conversa(self) -> None:
        from mente_laylay.autonomia.comandos_imediatos import processar_comandos_imediatos

        resultado = {
            "intent": "SUGGEST_ACTION",
            "params": {"tipo": "conversa", "assunto": "nota máxima em IA"},
        }
        contexto = {
            "_normalizar_texto_com_apelidos": lambda texto: texto.lower(),
            "_texto_social_curto": lambda _texto: False,
            "_texto_conversa_casual_sem_acao": lambda _texto: False,
            "_texto_tem_comando_explicito": lambda _texto: False,
            "_texto_conversa_contextual_sem_comando": lambda _texto: False,
            "analisar_intencao": lambda _texto: resultado,
            "executar_intencao": lambda _resultado, _texto: False,
        }
        self.assertFalse(processar_comandos_imediatos(
            contexto,
            "eu tirei nota maxima, e era sobre modelos personalizados de IA",
        ))

    def test_lembrete_daqui_minutos_e_resolvido_antes_da_ia(self) -> None:
        extrair = lambda texto: extrair_agendamento_local(texto, normalizar_texto)
        parsed = extrair("me lembra de ir pegar um refri daqui 5 minutos")
        self.assertEqual(parsed, {
            "intent": "AGENDAR_LEMBRETE",
            "params": {"descricao": "ir pegar um refri", "minutos": 5},
        })
        chamadas_ia = []
        intent, rota = resolver_intencao(
            "me lembra de ir pegar um refri daqui 5 minutos",
            "chat",
            {
                "normalizar_texto": normalizar_texto,
                "refinar_contexto_mental": lambda _texto: None,
                "extrair_agendamento": extrair,
                "tentar_intencao_ai_primeiro": lambda texto: chamadas_ia.append(texto),
            },
        )
        self.assertEqual(rota, "agenda")
        self.assertEqual(intent, parsed)
        self.assertEqual(chamadas_ia, [])

    def test_relato_de_evento_futuro_nao_vira_lembrete_por_decisao_da_ia(self) -> None:
        texto = "sabia que sexta eu vou participar de um campeonato de arremesso de peso"
        intent, rota = resolver_intencao(
            texto,
            "chat",
            {
                "normalizar_texto": normalizar_texto,
                "refinar_contexto_mental": lambda _texto: None,
                "extrair_agendamento": lambda _texto: None,
                "tentar_intencao_ai_primeiro": lambda _texto: {
                    "intent": "AGENDAR_LEMBRETE",
                    "params": {"data_hora": "sexta", "evento": "campeonato"},
                },
            },
        )
        self.assertIsNone(intent)
        self.assertEqual(rota, "")

    def test_pedido_explicito_sem_hora_preserva_evento_e_dia(self) -> None:
        resultado = extrair_agendamento_local(
            "me lembra de participar do campeonato sexta",
            normalizar_texto,
        )
        self.assertEqual(resultado["intent"], "AGENDAR_LEMBRETE")
        self.assertEqual(resultado["params"]["descricao"], "participar campeonato")
        self.assertEqual(resultado["params"]["data_hora"], "sexta")
        self.assertNotIn("hora_alvo", resultado["params"])

    def test_sexta_as_seis_e_convertida_em_instante_futuro_correto(self) -> None:
        from datetime import datetime

        agora = datetime(2026, 7, 15, 20, 0)  # quarta-feira
        instante, rotulo = resolver_instante_lembrete("06:00", "sexta", agora=agora)
        self.assertEqual(instante, datetime(2026, 7, 17, 6, 0))
        self.assertEqual(rotulo, "sexta às 06:00")

    def test_pendencia_so_consume_modalidade_compativel(self) -> None:
        from mente_laylay.autonomia.pre_fluxo_contextual import processar_feedback_pendente

        chamadas = []
        base = {
            "_handle_feedback_pendente_misto": lambda texto: chamadas.append(texto) or True,
            "_handle_feedback_pendente": lambda texto: chamadas.append(texto) or True,
        }
        conversa = {**base, "mente_integrada_estado": {"turno_atual": {"modalidade": "conversa"}}}
        self.assertEqual(processar_feedback_pendente(conversa, "noite chata"), (False, ""))
        self.assertEqual(chamadas, [])
        confirmacao = {**base, "mente_integrada_estado": {"turno_atual": {"modalidade": "confirmacao"}}}
        self.assertTrue(processar_feedback_pendente(confirmacao, "sim")[0])

    def test_prompt_de_conversa_nao_recebe_acao_antiga_como_assunto(self) -> None:
        mente = estado_mental_inicial()
        mente.update({
            "turno_atual": {"modalidade": "conversa", "confianca": 0.9, "motivo": "fala casual"},
            "ultima_acao_intent": "APP_OPEN",
            "ultima_acao_status": "app_aberto",
            "ultima_acao_alvo": "chrome",
            "pergunta_aberta_texto": "Quer abrir o Chrome?",
            "pergunta_aberta_ts": 9999999999,
        })
        resumo = resumo_mente_integrada_para_prompt(
            texto_usuario="noite chata", ctx={}, percepcao={}, mente=mente,
        )
        self.assertIn("modalidade=conversa", resumo)
        self.assertIn("pendencias e acoes antigas não são o assunto", resumo)
        self.assertNotIn("Ultima acao real", resumo)
        self.assertNotIn("Pergunta aberta pendente", resumo)

        mente["turno_atual"] = {"modalidade": "pergunta", "confianca": 0.9, "motivo": "pergunta"}
        resumo_contextual = resumo_mente_integrada_para_prompt(
            texto_usuario="ele está aberto?", ctx={}, percepcao={}, mente=mente,
        )
        self.assertIn("Ultima acao real", resumo_contextual)

    def test_confirmacao_musical_prioritaria_nao_chega_ao_ia_first(self) -> None:
        chamadas = []
        ctx = {
            "_processar_confirmacao_sugestao_musical": (
                lambda texto: chamadas.append(texto) or texto == "pode colocar"
            ),
        }
        self.assertTrue(processar_inicio_fluxo_resposta_ia(ctx, "pode colocar"))
        self.assertEqual(chamadas, ["pode colocar"])

    def test_pesquisa_contextual_consulta_obra_diretamente_pelo_titulo(self) -> None:
        class Resposta:
            def __init__(self, dados):
                self._dados = dados

            def raise_for_status(self):
                return None

            def json(self):
                return self._dados

        chamadas = []

        def get(_url, params=None, timeout=None):
            chamadas.append(dict(params or {}))
            return Resposta({
                "query": {
                    "pages": {
                        "1": {
                            "title": "Smoking Behind the Supermarket with You",
                            "extract": (
                                "Smoking Behind the Supermarket with You is a Japanese manga "
                                "series written and illustrated by Jinushi."
                            ),
                        }
                    }
                }
            })

        resultado = pesquisar_contexto_tema(
            "Smoking Behind the Supermarket with You",
            cache={},
            requests_get=get,
        )
        self.assertTrue(resultado["ok"])
        self.assertIn("Japanese manga", resultado["resumo"])
        self.assertEqual(chamadas[0]["titles"], "Smoking Behind the Supermarket with You")

    def test_falha_de_pesquisa_nao_fica_presa_no_cache_longo(self) -> None:
        class Falha:
            def raise_for_status(self):
                raise RuntimeError("offline")

            def json(self):
                return {}

        cache = {}
        resultado = pesquisar_contexto_tema(
            "obra desconhecida",
            cache=cache,
            requests_get=lambda *_args, **_kwargs: Falha(),
        )
        self.assertFalse(resultado["ok"])
        item = next(iter(cache.values()))
        self.assertEqual(item["ttl_s"], 30.0)

    def test_pesquisa_preserva_data_original_quando_reutiliza_cache(self) -> None:
        class Resposta:
            def raise_for_status(self):
                return None

            def json(self):
                return {"query": {"pages": {"1": {
                    "title": "Tema atual",
                    "extract": "Tema atual possui uma descrição verificável.",
                }}}}

        relogio = [100.0]
        chamadas = []
        cache = {}

        def get(*_args, **_kwargs):
            chamadas.append(True)
            return Resposta()

        primeira = pesquisar_contexto_tema(
            "Tema atual", cache=cache, requests_get=get, clock=lambda: relogio[0],
        )
        relogio[0] = 120.0
        segunda = pesquisar_contexto_tema(
            "Tema atual", cache=cache, requests_get=get, clock=lambda: relogio[0],
        )

        self.assertEqual(len(chamadas), 1)
        self.assertEqual(primeira["evidencia_obtida_em"], 100.0)
        self.assertEqual(segunda["evidencia_obtida_em"], 100.0)
        self.assertEqual(segunda["evidencia_idade_s"], 20.0)
        self.assertFalse(primeira["evidencia_cache"])
        self.assertTrue(segunda["evidencia_cache"])

    def test_opiniao_com_tema_na_mesma_fala_nao_cai_em_generico(self) -> None:
        titulo = "Smoking Behind the Supermarket with You"
        resposta = resposta_conversa_rapida_local(
            {
                "normalizar_texto": normalizar_texto,
                "enviar_mensagem": lambda *_args, **_kwargs: "",
                "_pesquisar_contexto_tema": lambda _tema: {},
                "mente_integrada_estado": {},
            },
            f"estou assistindo um anime novo, o nome dele é {titulo}. O que você acha dele?",
        )
        self.assertIn(titulo.casefold(), resposta.casefold())
        self.assertNotIn("menos acertar de primeira", resposta.casefold())

    def test_vies_aprendido_desempata_contextos_sem_vencer_explicito(self) -> None:
        import time

        agora = time.time()
        mente = estado_mental_inicial()
        mente.update({
            "ultima_acao_intent": "IOT_CONTROL",
            "ultima_acao_params": {"acao": "desligar", "alvo": "tomada_ventilador"},
            "ultimo_dispositivo_iot": "tomada_ventilador",
            "ultima_estrutura_arquivo_ts": agora - 5,
            "focos_por_dominio": {
                "iot": {"alvo": "tomada_ventilador", "ts": agora},
                "arquivo": {"alvo": "teste", "ts": agora - 5},
            },
            "aprendizado_continuidade": {
                "preferencias_conflito": {"iot>arquivo": 1},
                "correcoes": [],
            },
        })
        decisao = resolver_continuidade_semantica(
            "apaga ela",
            mente=mente,
            estrutura_arquivo={"nome": "teste"},
        )
        explicita = resolver_continuidade_semantica(
            "desliga esse ventilador",
            mente=mente,
            estrutura_arquivo={"nome": "teste"},
        )
        self.assertEqual(decisao.dominio, "arquivo")
        self.assertEqual(decisao.intent, "DELETE_ITEM")
        self.assertEqual(explicita.dominio, "iot")
        self.assertEqual(explicita.intent, "IOT_CONTROL")

    def test_pendencia_so_existe_depois_de_ser_falada(self) -> None:
        from mente_laylay.memoria_mental.pendencia import (
            criar_pendencia,
            pendencia_ativa,
            registrar_pendencia,
        )

        estado = estado_mental_inicial()
        rascunho = criar_pendencia(
            origem="planejador",
            tipo="escolha",
            conteudo="Quer ouvir uma música?",
            foi_falada=False,
        )
        estado = registrar_pendencia(estado, rascunho)
        self.assertIsNone(pendencia_ativa(estado))

        falada = criar_pendencia(
            origem="planejador",
            tipo="escolha",
            conteudo="Quer ouvir uma música?",
            foi_falada=True,
        )
        estado = registrar_pendencia(estado, falada)
        self.assertEqual(pendencia_ativa(estado)["conteudo"], "Quer ouvir uma música?")

    def test_pergunta_promessa_e_oferta_usam_a_mesma_pendencia(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import (
            limpar_oferta_pendente,
            registrar_oferta_pendente,
            registrar_pergunta_aberta,
            registrar_promessa_conversacional,
        )

        estado = registrar_pergunta_aberta(
            estado_mental_inicial(), "Qual foi a boa de hoje?", topico="dia"
        )
        self.assertEqual(estado["pendencia_atual"]["origem"], "pergunta_aberta")

        estado = registrar_promessa_conversacional(
            estado, "Posso te contar uma coisa que aconteceu comigo hoje?"
        )
        self.assertEqual(estado["pendencia_atual"]["tipo"], "promessa")

        estado = registrar_oferta_pendente(
            estado, 'Eu tentaria "Recomeçar" de Tim Bernardes. Quer ouvir essa?'
        )
        self.assertEqual(estado["pendencia_atual"]["dominio"], "musica")
        self.assertEqual(estado["pendencia_atual"]["intencao"], "MUSIC_SEARCH")
        estado = limpar_oferta_pendente(estado)
        self.assertFalse(estado["pendencia_atual"])
        self.assertEqual(estado["ultima_pendencia_encerrada"]["status"], "resolvida")

    def test_arbitro_prefere_comando_explicito_ao_contexto_antigo(self) -> None:
        from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno

        resultado = arbitrar_turno("fecha a steam", [
            CandidatoDecisao(
                tipo="comando_contextual",
                valor={"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": "opera"}},
                origem="contexto",
                confianca=0.94,
            ),
            CandidatoDecisao(
                tipo="comando_explicito",
                valor={"intent": "CLOSE_APP", "params": {"nome_app": "steam"}},
                origem="deterministico",
                confianca=0.90,
            ),
        ])
        self.assertEqual(resultado["decisao"]["intent"], "CLOSE_APP")
        self.assertEqual(len(resultado["rejeitados"]), 1)

    def test_arbitro_nao_executa_inferencia_contextual_em_pergunta(self) -> None:
        from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno

        resultado = arbitrar_turno("não abre o quê?", [
            CandidatoDecisao(
                tipo="comando_contextual",
                valor={"intent": "APP_OPEN", "params": {"nome_app": "que"}},
                origem="contexto",
                confianca=0.92,
            ),
        ])
        self.assertIsNone(resultado["decisao"])
        self.assertIn("nao autoriza", resultado["rejeitados"][0]["motivo"])

    def test_ciclo_de_vida_expira_contexto_efemero_sem_apagar_aprendizado(self) -> None:
        from mente_laylay.memoria_mental.ciclo_vida_contexto import aplicar_ciclo_vida_contexto

        agora = 10_000.0
        estado = estado_mental_inicial()
        estado.update({
            "pergunta_aberta_texto": "Quer ouvir algo?",
            "pergunta_aberta_ts": agora - 121,
            "oferta_pendente": {"intent": "MUSIC_SEARCH", "ts": agora - 301},
            "pendencia_atual": {
                "id": "p1", "tipo": "escolha", "status": "ativa",
                "foi_falada": True, "expira_em": agora - 1,
            },
            "foco_conversacional_topico": "noite chata",
            "foco_conversacional_ts": agora - 481,
            "aprendizado_continuidade": {"preferencias_conflito": {"iot>arquivo": 2}},
        })
        atualizado = aplicar_ciclo_vida_contexto(estado, agora=agora)

        self.assertEqual(atualizado["pergunta_aberta_texto"], "")
        self.assertFalse(atualizado["oferta_pendente"])
        self.assertFalse(atualizado["pendencia_atual"])
        self.assertEqual(atualizado["ultima_pendencia_encerrada"]["status"], "expirada")
        self.assertEqual(atualizado["foco_conversacional_topico"], "")
        self.assertEqual(
            atualizado["aprendizado_continuidade"]["preferencias_conflito"]["iot>arquivo"], 2
        )

    def test_correcao_temporal_responde_ao_relogio_e_ajusta_fala_pronta(self) -> None:
        from mente_laylay.cognicao.coerencia_temporal import (
            ajustar_fala_ao_periodo,
            responder_correcao_temporal,
        )

        resposta = responder_correcao_temporal("mas tá de dia ainda?", "tarde")
        self.assertIn("ainda é tarde", resposta.casefold())
        self.assertIn("me adiantei", resposta.casefold())
        ajustada = ajustar_fala_ao_periodo(
            "Quer deixar a noite mais interessante comigo?", "tarde"
        )
        self.assertIn("tarde", ajustada.casefold())
        self.assertNotIn("noite", ajustada.casefold())

    def test_recomendacao_implicita_cria_pendencia_musical_unificada(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import registrar_oferta_pendente

        estado = registrar_oferta_pendente(
            estado_mental_inicial(),
            "Minha aposta agora é Far From Alaska - Thievery. Se não bater, eu troco.",
        )
        self.assertEqual(estado["pendencia_atual"]["dominio"], "musica")
        self.assertEqual(
            estado["pendencia_atual"]["opcoes"][0]["params"]["query"],
            "Far From Alaska - Thievery",
        )

    def test_rejeicao_musical_explicita_aprende_mesmo_sem_oferta(self) -> None:
        from mente_laylay.memoria_mental.contexto_compartilhado import registrar_feedback_musical_conversacional

        estado = registrar_feedback_musical_conversacional(
            estado_mental_inicial(), "aí não, odeio Pabllo Vittar"
        )
        self.assertLess(estado["preferencias_musicais"]["artistas"]["Pabllo Vittar"], 0)

    def test_pre_fluxo_reconstroi_retrato_depois_do_refinamento(self) -> None:
        from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia

        contexto_novo = {
            "mente_integrada_estado": {"ultima_habilidade": "atualizada"},
        }
        ctx = {
            "mente_integrada_estado": {"ultima_habilidade": "antiga"},
            "_refinar_contexto_mental": lambda _texto: None,
            "_recarregar_contexto_inicio": lambda: dict(contexto_novo),
        }
        tratado = processar_inicio_fluxo_resposta_ia(ctx, "frase sem atalho conhecido")
        self.assertFalse(tratado)
        self.assertEqual(ctx["mente_integrada_estado"]["ultima_habilidade"], "atualizada")

    def test_pre_fluxo_nao_registra_o_mesmo_turno_temporal_duas_vezes(self) -> None:
        from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia

        chamadas = []
        ctx = {
            "_refinar_contexto_mental": lambda texto: chamadas.append(("refino", texto)) or {},
            "_registrar_interacao_temporal": lambda texto: chamadas.append(("fallback", texto)) or {},
            "_recarregar_contexto_inicio": lambda: dict(ctx),
            "mente_integrada_estado": {},
        }

        self.assertFalse(processar_inicio_fluxo_resposta_ia(ctx, "comecei um projeto novo"))
        self.assertEqual(chamadas, [("refino", "comecei um projeto novo")])

    def test_como_assim_nao_repete_fallback_vazio(self) -> None:
        import time
        from mente_laylay.personalidade.conversa_natural import resposta_pergunta_curta_dependente_topico

        fala_ruim = "Eu acho que tem uma ideia boa aí, só tá meio embrulhada. Eu puxaria pelo lado mais humano disso primeiro."
        resposta = resposta_pergunta_curta_dependente_topico({
            "mente_integrada_estado": {
                "ultima_resposta": fala_ruim,
                "ultima_afirmacao": fala_ruim,
                "continuidade_fala_ts": time.time(),
            },
            "_normalizar_texto_curto": normalizar_texto,
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "ultimo_topico_conversa": "",
            "foco_vivo": {},
        }, "como assim?")
        self.assertIn("ficou vaga", resposta.casefold())
        self.assertNotIn("ideia boa", resposta.casefold())

    def test_fala_descartada_nao_e_gravada_como_conversa(self) -> None:
        from mente_laylay.personalidade.resposta_conversacional_runtime import (
            RespostaConversacionalRuntime,
        )

        class EstadoFalso:
            memoria_conversa = {"messages": []}
            conversacional = {"current_emotion": "calma", "emotion_level": 1}

            def atualizar_campos(self, _dominio, **campos):
                self.memoria_conversa.update(campos)

        estado = EstadoFalso()
        chamadas = []
        runtime = RespostaConversacionalRuntime(
            namespace_getter=lambda: {
                "falar_com_lipsync": lambda *_args: False,
                "_registrar_mente_curta": lambda *_args, **_kwargs: chamadas.append("mente"),
                "memoria_inteligente": type(
                    "Memoria", (), {"adicionar_interacao": lambda self, *_args: chamadas.append("historico")}
                )(),
                "salvar_memoria": lambda: chamadas.append("salvar"),
            },
            estado_runtime_getter=lambda: estado,
            fallback_fala="fallback",
            log=lambda *_args: None,
        )

        self.assertFalse(runtime.emitir_resposta_curta("oi", "fala inferior"))
        self.assertEqual(estado.memoria_conversa["messages"], [])
        self.assertEqual(chamadas, [])

    def test_monitor_de_janelas_respeita_fala_inicial(self) -> None:
        from mente_laylay.percepcao.monitor_janelas import MonitorJanelasRuntime

        falas = []
        contextos = []
        runtime = MonitorJanelasRuntime(
            capturar_janela=lambda: {
                "win": object(), "title": "laylay.py - PyCharm", "hwnd": 10,
                "exe": "pycharm64.exe", "assunto": "Programação",
            },
            atualizar_contexto=contextos.append,
            continuidade_get=lambda _chave, padrao=None: padrao,
            continuidade_update=lambda **_campos: None,
            esta_falando=lambda: False,
            conversa_ativa=lambda: False,
            ultimo_proativo_get=lambda: 0.0,
            ultimo_proativo_set=lambda _valor: None,
            sugestoes_bloqueadas_get=lambda: {},
            janela_em_tela_cheia=lambda _janela: False,
            detectar_gatilho=lambda *_args: ("SYS_MODE_CODE", {}),
            fala_gatilho=lambda _gatilho: "Ativo Modo Code?",
            falar=lambda *args: falas.append(args),
            interacao_iniciada=lambda: False,
            clock=lambda: 100.0,
        )

        resultado = runtime.executar_ciclo()
        self.assertEqual(resultado["status"], "aguardando_primeira_interacao")
        self.assertEqual(len(contextos), 1)
        self.assertEqual(falas, [])


if __name__ == "__main__":
    unittest.main()
