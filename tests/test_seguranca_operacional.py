import datetime as dt
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mente_laylay.arquivos.lixeira_laylay import LixeiraLaylay
from mente_laylay.autonomia.agenda_windows import sincronizar_despertares_windows
from mente_laylay.cognicao.memoria_visual import executar_captura_tela
from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando
from mente_laylay.integracao.gmail_mental import GmailMental
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _lixeira(raiz: str) -> LixeiraLaylay:
    estado: dict = {}

    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )
    return LixeiraLaylay(raiz, pendencia_runtime=pendencia)


class SegurancaOperacionalTests(unittest.TestCase):
    def test_lixeira_confirma_pasta_nao_vazia_e_desfaz(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "pasta"
            alvo.mkdir()
            (alvo / "dado.txt").write_text("seguro", encoding="utf-8")
            lixeira = _lixeira(str(Path(tmp) / "lixeira"))

            primeira = lixeira.mover(str(alvo))
            self.assertTrue(primeira.requer_confirmacao)
            self.assertTrue(alvo.exists())

            movido = lixeira.confirmar_pendente()
            self.assertTrue(movido.sucesso)
            self.assertFalse(alvo.exists())

            restaurado = lixeira.restaurar_ultimo(str(alvo))
            self.assertTrue(restaurado.sucesso)
            self.assertEqual((alvo / "dado.txt").read_text(encoding="utf-8"), "seguro")

    def test_lixeira_nao_restaura_item_diferente_da_referencia_confirmada(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "correto.txt"
            outro = Path(tmp) / "outro.txt"
            alvo.write_text("preservar", encoding="utf-8")
            lixeira = _lixeira(str(Path(tmp) / "lixeira"))
            lixeira.mover(str(alvo))
            movido = lixeira.confirmar_pendente()
            self.assertTrue(movido.sucesso)

            restaurado = lixeira.restaurar_ultimo(str(outro))

            self.assertFalse(restaurado.sucesso)
            self.assertEqual(restaurado.status, "exclusao_vinculada_nao_encontrada")
            self.assertFalse(alvo.exists())

    def test_lixeira_tambem_confirma_arquivo_simples(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "anotacao.txt"
            alvo.write_text("não apagar sem confirmar", encoding="utf-8")
            lixeira = _lixeira(str(Path(tmp) / "lixeira"))

            primeira = lixeira.mover(str(alvo))
            self.assertTrue(primeira.requer_confirmacao)
            self.assertTrue(alvo.exists())

            confirmado = lixeira.confirmar_pendente()
            self.assertTrue(confirmado.sucesso)
            self.assertFalse(alvo.exists())

    def test_chrome_bloqueia_digitacao_sensivel_e_javascript(self):
        enviados = []
        ctx = {
            "ALLOWED_ACTIONS": {"type"},
            "connected_extensions": {object()},
            "ws_loop": object(),
            "executar_chrome_confirmado": lambda msg, timeout_s: enviados.append(msg) or True,
            "solicitar_aba_ativa": lambda timeout_s: {
                "url": "https://banco.example/login", "title": "Login", "tabId": 4,
            },
        }
        self.assertFalse(validar_e_enviar_comando(ctx, "type", {"selector": "#senha", "text": "x"}))
        self.assertFalse(validar_e_enviar_comando(ctx, "execute_js", {"code": "alert(1)"}))
        self.assertEqual(enviados, [])

    def test_visao_recusa_contexto_sensivel_sem_capturar(self):
        falas = []
        capturas = []
        ok = executar_captura_tela(
            "pc_a",
            enviar_pc_b=lambda payload: True,
            capturar_tela=lambda: capturas.append(True) or "imagem",
            analisar_imagem=lambda imagem, pergunta: "descricao",
            falar=lambda texto, *args: falas.append(texto),
            estado_emocional=lambda: ("calma", 1),
            obter_contexto=lambda: {"url": "https://site.example/checkout/pagamento"},
        )
        self.assertTrue(ok)
        self.assertEqual(capturas, [])
        self.assertTrue(any("sensível" in fala for fala in falas))

    def test_agenda_windows_cria_tarefa_com_despertar(self):
        chamadas = []

        class Resultado:
            returncode = 0

        def executar(args, **kwargs):
            chamadas.append((args, kwargs))
            return Resultado()

        with tempfile.TemporaryDirectory() as tmp, patch("mente_laylay.autonomia.agenda_windows.os.name", "nt"):
            futuro = dt.datetime.now() + dt.timedelta(hours=1)
            ok = sincronizar_despertares_windows(
                [{"id": "teste", "tipo": "once", "ativo": True, "ts_execucao": futuro.timestamp()}],
                estado_path=str(Path(tmp) / "tarefas.json"),
                executar=executar,
            )
        self.assertTrue(ok)
        self.assertTrue(any("/Create" in args for args, _ in chamadas))

    def test_gmail_detecta_dominio_e_possivel_golpe(self):
        with tempfile.TemporaryDirectory() as tmp:
            gmail = GmailMental(arquivo_estado=str(Path(tmp) / "gmail.json"))
            golpe = gmail.analisar_remetente(
                '"Nubank" <suporte@nubank-seguranca.example>',
                "Urgente: confirme sua senha",
                "spf=fail smtp.mailfrom=evil.example",
            )
            legitimo = gmail.analisar_remetente(
                '"Nubank" <aviso@nubank.com.br>',
                "Aviso de compra",
                "spf=pass smtp.mailfrom=nubank.com.br; dkim=pass header.d=nubank.com.br",
            )
        self.assertTrue(golpe["possivel_golpe"])
        self.assertTrue(legitimo["autenticado"])
        self.assertFalse(legitimo["possivel_golpe"])

    def test_gmail_encaminha_falha_de_estado_sem_expor_conteudo(self):
        falhas = []
        with tempfile.TemporaryDirectory() as tmp:
            estado = Path(tmp) / "gmail.json"
            estado.write_text("{json quebrado com dado privado", encoding="utf-8")
            gmail = GmailMental(
                arquivo_estado=str(estado),
                registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
                log=lambda *_: None,
            )
            gmail.carregar_estado()

        self.assertEqual(falhas[0][0], ("gmail", "estado_leitura"))
        self.assertIsInstance(falhas[0][1]["erro"], Exception)


if __name__ == "__main__":
    unittest.main()
