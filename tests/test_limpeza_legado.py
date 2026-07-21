from __future__ import annotations

import unittest

from mente_laylay.autonomia.dispatcher_comandos_json import (
    adaptar_acao_json_para_intencao,
    executar_comandos_json,
)
from mente_laylay.autonomia.execucao_ia import ContextoExecRuntime, executar_exec
from mente_laylay.memoria_mental.contexto_imediato import _normalizar_com_callback


class LimpezaLegadoTests(unittest.TestCase):
    def test_acoes_json_sao_convertidas_para_intencoes_canonicas(self) -> None:
        casos = (
            ({"acao": "open_url", "alvo": "https://example.com"}, "OPEN_URL"),
            ({"acao": "open_app", "alvo": "discord"}, "APP_OPEN"),
            ({"acao": "youtube_search", "alvo": "Rubel"}, "MUSIC_SEARCH"),
            ({"acao": "youtube_control", "alvo": "pause"}, "MEDIA_CONTROL"),
            ({"acao": "ler_emails"}, "EMAIL_READ"),
            ({"acao": "ler_emails_urgentes"}, "EMAIL_READ"),
            ({"acao": "sincronizar_emails"}, "EMAIL_SYNC"),
            ({"acao": "lock_pc"}, "LOCK_PC"),
            ({"acao": "tocar_playlist", "alvo": "rock"}, "PLAYLIST_PLAY"),
        )
        for comando, intent in casos:
            with self.subTest(comando=comando):
                resultado = adaptar_acao_json_para_intencao(comando)
                self.assertEqual(resultado["intent"], intent)

        urgente = adaptar_acao_json_para_intencao({"acao": "ler_emails_urgentes"})
        self.assertTrue(urgente["params"]["urgentes"])

    def test_dispatcher_delega_email_sem_engolir_sincronizacao(self) -> None:
        executadas = []
        for acao in ("ler_emails", "ler_emails_urgentes", "sincronizar_emails"):
            resultado = executar_comandos_json(
                {"executar_intencao": lambda intent, texto: executadas.append((intent, texto)) or True},
                "pedido explícito de email",
                [{"acao": acao}],
                "",
                "acao",
                False,
                False,
                False,
            )
            self.assertEqual(resultado["erros"], [])
        self.assertEqual([item[0]["intent"] for item in executadas], [
            "EMAIL_READ", "EMAIL_READ", "EMAIL_SYNC",
        ])

    def test_executor_legado_nao_repete_comandos_modulares(self) -> None:
        chrome = []
        self.assertFalse(executar_exec(
            "YOUTUBE",
            "música",
            {"enviar_comando_chrome": lambda *args: chrome.append(args)},
        ))
        self.assertEqual(chrome, [])

    def test_recusa_modular_nao_cai_no_fallback_legado(self) -> None:
        legado = []
        runtime = ContextoExecRuntime(
            contexto_getter=lambda: {},
            executar_conteudo_cb=lambda *_args: False,
            executar_legado_cb=lambda *args: legado.append(args) or True,
            log=lambda _msg: None,
        )
        self.assertFalse(runtime.executar("YOUTUBE", "música"))
        self.assertEqual(legado, [])

    def test_fallback_permanece_para_comando_ainda_legado(self) -> None:
        abertos = []
        runtime = ContextoExecRuntime(
            contexto_getter=lambda: {"abrir_programa": lambda alvo: abertos.append(alvo) or True},
            executar_conteudo_cb=lambda *_args: False,
            executar_legado_cb=executar_exec,
            log=lambda _msg: None,
        )
        self.assertTrue(runtime.executar("OPEN_APP", "discord"))
        self.assertEqual(abertos, ["discord"])

    def test_normalizacao_contextual_tem_uma_fonte_unica(self) -> None:
        self.assertEqual(_normalizar_com_callback("  ABC  ", lambda valor: valor.casefold()), "abc")
        self.assertEqual(_normalizar_com_callback("  ABC  ", None), "abc")


if __name__ == "__main__":
    unittest.main()
