"""Memória textual curta que consolida as interações do dia da Laylay."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Callable


class MemoriaLaylay:
    def __init__(
        self,
        *,
        pasta_memoria: str,
        enviar_mensagem: Callable[[list[dict]], str],
        agora: Callable[[], datetime] = datetime.now,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.contador = 0
        self.historico_recente: list[str] = []
        self.resumo_do_dia = ""
        self._enviar_mensagem = enviar_mensagem
        self._agora = agora
        self._log = log
        self.data_atual = self._agora().strftime("%d-%m-%Y")
        self.arquivo_diario = os.path.join(pasta_memoria, f"memoria_{self.data_atual}.txt")
        self.carregar_resumo_diario()

    def carregar_resumo_diario(self) -> None:
        if not os.path.exists(self.arquivo_diario):
            return
        try:
            with open(self.arquivo_diario, "r", encoding="utf-8") as arquivo:
                self.resumo_do_dia = arquivo.read().strip()
            self._log(f"📂 [MEMÓRIA] Resumo do dia {self.data_atual} carregado")
        except Exception:
            self.resumo_do_dia = ""

    def salvar_resumo_diario(self) -> None:
        try:
            with open(self.arquivo_diario, "w", encoding="utf-8") as arquivo:
                arquivo.write(f"RESUMO DO DIA {self.data_atual}:\n\n{self.resumo_do_dia}")
            self._log(f"💾 [MEMÓRIA] Resumo salvo em {self.arquivo_diario}")
        except Exception as erro:
            self._log(f"⚠️ Erro ao salvar resumo: {erro}")

    def adicionar_interacao(self, usuario: str, resposta_ia: str) -> None:
        self.contador += 1
        horario = self._agora().strftime("%H:%M")
        self.historico_recente.append(f"[{horario}] Usuário: {usuario} | Laylay: {resposta_ia}")
        if self.contador % 5 == 0:
            self.atualizar_resumo_diario()

    def atualizar_resumo_diario(self) -> None:
        self._log(f"🚀 [MEMÓRIA] Gerando resumo das últimas {len(self.historico_recente)} interações...")
        texto_para_resumir = "\n".join(self.historico_recente)
        prompt = (
            f"Resumo atual do dia:\n{self.resumo_do_dia}\n\n"
            f"Novas interações:\n{texto_para_resumir}\n\n"
            "Atualize o resumo do dia de forma concisa, mantendo apenas os fatos importantes, "
            "pedidos do Pedro, preferências e eventos relevantes. Escreva em português."
        )
        mensagens = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Resuma tudo acima em um texto coeso e curto."},
        ]
        novo_resumo = self._enviar_mensagem(mensagens)
        self.resumo_do_dia = str(novo_resumo or "").strip()
        self.salvar_resumo_diario()
        self.historico_recente = []
