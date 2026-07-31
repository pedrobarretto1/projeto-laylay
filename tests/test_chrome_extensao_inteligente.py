from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando
from mente_laylay.integracao.chrome_navegacao import abrir_url_reutilizando_aba
from mente_laylay.integracao.chrome_ws_handlers import (
    dispatch_event,
    handle_action,
    handle_command_result,
    handle_player_event,
    handle_user_context,
)
from mente_laylay.cognicao.erros_navegador import resumir_erro_navegador
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas


class ChromeExtensaoInteligenteTests(unittest.TestCase):
    def test_fechamento_especifico_exige_resultado_real_da_extensao(self) -> None:
        executados = []
        contexto = {
            "ALLOWED_ACTIONS": {"close_specific_tab"},
            "connected_extensions": {"extensao"},
            "ws_loop": object(),
            "broadcast_command": lambda *_args: None,
            "executar_chrome_confirmado": (
                lambda mensagem, timeout_s: executados.append((mensagem, timeout_s)) or False
            ),
        }

        self.assertFalse(validar_e_enviar_comando(
            contexto, "close_specific_tab", {"target": "iot.tuya.com"},
        ))
        self.assertEqual(executados[0][0], {
            "action": "close_specific_tab", "target": "iot.tuya.com",
        })

    def test_erro_oauth_e_resumido_sem_recitar_url_ou_client_id(self) -> None:
        url = (
            "https://discord.com/oauth2/authorize?client_id=1445298470863896667&"
            "redirect_uri=https%3A%2F%2Fbackend.accounts.hytale.com%2Fcallback"
        )
        fala = resumir_erro_navegador({"title": "Discord", "url": url})

        self.assertIn("Hytale com o Discord", fala)
        self.assertNotIn("client_id", fala)
        self.assertNotIn("144529", fala)
        self.assertNotIn("https://", fala)

    def test_percepcao_de_erro_do_chrome_fala_resumo_oral(self) -> None:
        estado = {}
        falas = []
        url = (
            "https://discord.com/oauth2/authorize?client_id=1445298470863896667&"
            "redirect_uri=https%3A%2F%2Fbackend.accounts.hytale.com%2Fcallback"
        )
        handle_user_context(
            {"kind": "nav", "title": "Discord 404", "url": url},
            {
                "_continuidades_get": lambda chave, padrao=None: estado.get(chave, padrao),
                "_continuidades_update": lambda **dados: estado.update(dados),
                "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
                "_ultimo_sugerido_ts": 0.0,
                "_ultimo_proativo_ts": 0.0,
                "is_speaking": False,
                "sugestao_bloqueada_ate": {},
                "ultimo_open_site": {},
            },
        )

        self.assertTrue(falas)
        self.assertIn("Hytale com o Discord", falas[-1])
        self.assertNotIn("client_id", falas[-1])
        self.assertNotIn("https://", falas[-1])

    def test_snapshot_vira_percepcao_da_mente_unica(self) -> None:
        percepcoes = {}
        snapshot = {
            "url": "https://example.com/form",
            "title": "Cadastro",
            "kind": "interactive",
            "elements": [{"id": "ll-1", "tag": "button", "label": "Continuar"}],
        }

        updates = handle_action(
            {"type": "PAGE_SNAPSHOT", "payload": snapshot},
            {"_percepcao_set": lambda chave, valor: percepcoes.__setitem__(chave, valor)},
        )

        self.assertTrue(updates["handled"])
        self.assertEqual(updates["aba_url_atual"], snapshot["url"])
        self.assertEqual(percepcoes["pagina_ativa"]["elements"][0]["label"], "Continuar")

    def test_snapshot_e_processado_sem_imprimir_payload_bruto(self) -> None:
        recebido = []
        snapshot = {
            "type": "PAGE_SNAPSHOT",
            "payload": {"title": "Privado", "url": "https://example.com/segredo"},
        }

        with patch("builtins.print") as imprimir:
            resultado = dispatch_event(snapshot, {"action": recebido.append})

        self.assertIsNone(resultado)
        self.assertEqual(recebido, [snapshot])
        imprimir.assert_not_called()

    def test_resultado_do_comando_resolve_pendencia(self) -> None:
        event = threading.Event()
        pending = {"req-1": {"event": event, "result": None}}
        data = {"type": "COMMAND_RESULT", "requestId": "req-1", "action": "click", "ok": True}

        handle_command_result(data, pending)

        self.assertTrue(event.is_set())
        self.assertEqual(pending["req-1"]["result"], data)

    def test_comando_dom_so_confirma_com_resultado_real(self) -> None:
        received = []
        ctx = {
            "ALLOWED_ACTIONS": {"click"},
            "connected_extensions": {object()},
            "ws_loop": object(),
            "broadcast_command": lambda _message: None,
            "executar_chrome_confirmado": lambda message, timeout_s: received.append((message, timeout_s)) or True,
            "solicitar_aba_ativa": lambda timeout_s: {"url": "https://example.com/a", "title": "A", "tabId": 7},
        }

        ok = validar_e_enviar_comando(ctx, "click", {"element_id": "ll-4"})

        self.assertTrue(ok)
        self.assertEqual(received[0][0]["expectedTabId"], 7)
        self.assertEqual(received[0][0]["expectedUrl"], "https://example.com/a")
        self.assertEqual(received[0][0]["element_id"], "ll-4")
        self.assertEqual(received[0][1], 3.0)

    def test_falha_real_do_dom_nao_e_tratada_como_sucesso(self) -> None:
        ctx = {
            "ALLOWED_ACTIONS": {"type"},
            "connected_extensions": {object()},
            "ws_loop": object(),
            "broadcast_command": lambda _message: None,
            "executar_chrome_confirmado": lambda _message, timeout_s: False,
        }

        self.assertFalse(validar_e_enviar_comando(ctx, "type", {"text": "teste"}))

    def test_pagina_percebida_entra_no_prompt_de_comando(self) -> None:
        texto = resumo_mente_integrada_para_prompt(
            texto_usuario="clica em continuar",
            ctx={
                "periodo": "tarde",
                "conteudo_atual": {
                    "tipo": "pagina",
                    "titulo": "Cadastro",
                    "url": "https://example.com",
                    "descricao": "controles=ll-1:Continuar",
                },
            },
            percepcao={},
            mente={"turno_atual": {"modalidade": "comando", "normalizado": "clica em continuar"}},
        )

        self.assertIn("Página percebida agora", texto)
        self.assertIn("ll-1:Continuar", texto)

    def test_site_inicial_existente_e_focado_sem_substituir_url(self) -> None:
        comandos = []
        ok = abrir_url_reutilizando_aba(
            "https://www.ifood.com.br/",
            conectado=lambda: True,
            solicitar_lista_abas=lambda: [
                {"id": 7, "url": "https://ifood.com.br/restaurantes", "title": "iFood"},
            ],
            enviar_comando=lambda acao, payload: comandos.append((acao, payload)) or True,
            abrir_fallback=lambda _url: True,
        )

        self.assertTrue(ok)
        self.assertEqual(comandos, [("focus_tab", {"tabId": 7, "url": "https://www.ifood.com.br/"})])

    def test_modo_jogo_reutiliza_site_sem_trocar_a_aba_visivel(self) -> None:
        comandos = []
        ok = abrir_url_reutilizando_aba(
            "https://www.ifood.com.br/",
            conectado=lambda: True,
            solicitar_lista_abas=lambda: [
                {"id": 7, "url": "https://ifood.com.br/restaurantes", "title": "iFood"},
            ],
            enviar_comando=lambda acao, payload: comandos.append((acao, payload)) or True,
            abrir_fallback=lambda _url: True,
            preservar_foco=True,
        )

        self.assertTrue(ok)
        self.assertEqual(comandos, [])

    def test_modo_jogo_cria_aba_em_segundo_plano(self) -> None:
        comandos = []
        abrir_url_reutilizando_aba(
            "https://example.com/novo",
            conectado=lambda: True,
            solicitar_lista_abas=lambda: [],
            enviar_comando=lambda acao, payload: comandos.append((acao, payload)) or True,
            abrir_fallback=lambda _url: True,
            preservar_foco=True,
        )

        self.assertEqual(comandos, [(
            "open_url",
            {"url": "https://example.com/novo", "auto_click": False, "background": True},
        )])

    def test_buscas_google_diferentes_criam_nova_aba(self) -> None:
        comandos = []
        abrir_url_reutilizando_aba(
            "https://www.google.com/search?q=receitas",
            conectado=lambda: True,
            solicitar_lista_abas=lambda: [
                {"id": 8, "url": "https://google.com/search?q=noticias", "title": "notícias"},
            ],
            enviar_comando=lambda acao, payload: comandos.append((acao, payload)) or True,
            abrir_fallback=lambda _url: True,
        )

        self.assertEqual(comandos[0][0], "open_url")
        self.assertEqual(comandos[0][1]["url"], "https://www.google.com/search?q=receitas")

    def test_site_mapeado_existente_retorna_status_de_foco(self) -> None:
        comandos = []
        resultado = executar_habilidade_janelas(
            "APP_OPEN",
            {"nome_app": "ifood"},
            {
                "APPS_MAP": {"ifood": "https://www.ifood.com.br/"},
                "_normalizar_texto_com_apelidos": lambda texto: str(texto).lower(),
                "_resolver_alvo_ambiente": lambda _nome: {"aba_aberta": True},
                "enviar_comando_chrome": lambda acao, payload: comandos.append((acao, payload)) or True,
            },
        )

        self.assertEqual(resultado["status"], "site_ja_aberto_focado")
        self.assertEqual(comandos[0][0], "open_url")

    def test_app_aberto_no_modo_jogo_nao_e_puxado_para_frente(self) -> None:
        focos = []
        resultado = executar_habilidade_janelas(
            "APP_OPEN",
            {"nome_app": "discord"},
            {
                "APPS_MAP": {"discord": "discord"},
                "_normalizar_texto_com_apelidos": lambda texto: str(texto).lower(),
                "_resolver_alvo_ambiente": lambda _nome: {
                    "programa_aberto": True,
                    "programa_em_foco": False,
                },
                "modo_jogo_ativo": lambda: True,
                "focar_janela_app": lambda app: focos.append(app) or True,
            },
        )

        self.assertEqual(resultado["status"], "app_aberto_segundo_plano")
        self.assertEqual(focos, [])

    def test_fim_de_video_duplicado_avanca_playlist_uma_vez(self) -> None:
        avancos = []
        state = {
            "name": "noite",
            "last_url": "https://youtube.com/watch?v=um",
            "user_intervened": False,
        }
        evento = {
            "event": "video_ended",
            "eventId": "ended:um:10",
            "url": "https://youtube.com/watch?v=um",
            "duration": 180,
            "tabId": 42,
        }

        for _ in range(2):
            handle_player_event(
                evento,
                playlist_state=state,
                yt_clean_url=lambda url: url,
                playlist_avancar_proxima=lambda: avancos.append(True) or True,
                falar_com_lipsync=None,
            )

        self.assertEqual(len(avancos), 1)
        self.assertEqual(state["tab_id"], 42)

    def test_faixa_curta_ou_duracao_indisponivel_tambem_avanca(self) -> None:
        for duration in (0, 42):
            with self.subTest(duration=duration):
                avancos = []
                state = {
                    "name": "curtas",
                    "last_url": "https://youtube.com/watch?v=curta",
                }
                handle_player_event(
                    {
                        "event": "video_ended",
                        "eventId": f"ended:curta:{duration}",
                        "url": state["last_url"],
                        "duration": duration,
                        "tabId": 7,
                    },
                    playlist_state=state,
                    yt_clean_url=lambda url: url,
                    playlist_avancar_proxima=lambda: avancos.append(True) or True,
                    falar_com_lipsync=None,
                )
                self.assertEqual(avancos, [True])

    def test_fim_de_anuncio_continua_sem_avancar_playlist(self) -> None:
        avancos = []
        state = {
            "name": "noite",
            "last_url": "https://youtube.com/watch?v=musica",
        }
        handle_player_event(
            {
                "event": "video_ended",
                "eventId": "ended:anuncio:1",
                "url": state["last_url"],
                "duration": 30,
                "isAd": True,
            },
            playlist_state=state,
            yt_clean_url=lambda url: url,
            playlist_avancar_proxima=lambda: avancos.append(True) or True,
            falar_com_lipsync=None,
        )
        self.assertEqual(avancos, [])

    def test_playlist_envia_proxima_faixa_para_mesma_aba(self) -> None:
        recebidos = []
        runtime = PlaylistRuntime(
            state_file="nao_usado.json",
            legacy_file="nao_usado_legacy.json",
            cache={},
            ultima_playlist_getter=lambda: "noite",
            playlist_state={"name": "noite", "tab_id": 19},
            youtube_play=lambda url, target_tab_id=None: recebidos.append((url, target_tab_id)) or True,
            log=lambda _linha: None,
        )

        self.assertTrue(runtime._abrir_youtube_item("https://youtube.com/watch?v=dois"))
        self.assertEqual(recebidos, [("https://youtube.com/watch?v=dois", 19)])

    def test_youtube_sem_confirmacao_nao_abre_segunda_aba_nativa(self) -> None:
        ctx = {
            "ALLOWED_ACTIONS": {"youtube_play"},
            "connected_extensions": {object()},
            "ws_loop": object(),
            "broadcast_command": lambda _message: None,
            "enviar_chrome_confirmado": lambda _message, timeout_s: False,
            "is_valid_url": lambda url: url.startswith("https://"),
        }

        with patch("mente_laylay.integracao.chrome_comandos.webbrowser.open") as abrir_nativo:
            ok = validar_e_enviar_comando(
                ctx,
                "youtube_play",
                {"url": "https://youtube.com/watch?v=dois", "target_tab_id": 19},
            )

        self.assertFalse(ok)
        abrir_nativo.assert_not_called()

    def test_youtube_play_recebe_background_automatico_no_modo_jogo(self) -> None:
        recebidos = []
        ctx = {
            "ALLOWED_ACTIONS": {"youtube_play"},
            "connected_extensions": {object()},
            "ws_loop": object(),
            "broadcast_command": lambda _message: None,
            "executar_chrome_confirmado": lambda message, timeout_s: recebidos.append(message) or True,
            "is_valid_url": lambda url: url.startswith("https://"),
            "modo_jogo_ativo": lambda: True,
        }

        ok = validar_e_enviar_comando(
            ctx,
            "youtube_play",
            {"url": "https://youtube.com/watch?v=dois", "target_tab_id": 19},
        )

        self.assertTrue(ok)
        self.assertTrue(recebidos[0]["background"])
        self.assertEqual(recebidos[0]["target_tab_id"], 19)


if __name__ == "__main__":
    unittest.main()
