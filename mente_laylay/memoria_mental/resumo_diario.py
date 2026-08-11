"""Memória textual curta que consolida as interações do dia da Laylay."""

from __future__ import annotations

import os
import threading
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
        self._pasta_memoria = os.path.abspath(pasta_memoria)
        self._lock = threading.RLock()
        self._ultima_tentativa_resumo_em: datetime | None = None
        self._intervalo_retentativa_s = 30.0
        self.data_atual = self._agora().strftime("%d-%m-%Y")
        self.arquivo_diario = self._caminho_do_dia(self.data_atual)
        self.carregar_resumo_diario()

    def _caminho_do_dia(self, data: str) -> str:
        return os.path.join(self._pasta_memoria, f"memoria_{data}.txt")

    def _garantir_dia_atual(self) -> None:
        data_agora = self._agora().strftime("%d-%m-%Y")
        if data_agora == self.data_atual:
            return
        # O lote antigo já está materializado no arquivo do dia anterior. A
        # troca não depende da LLM e, portanto, não perde memória se ela estiver
        # lenta justamente à meia-noite.
        self.salvar_resumo_diario()
        self.data_atual = data_agora
        self.arquivo_diario = self._caminho_do_dia(data_agora)
        self.contador = 0
        self.historico_recente = []
        self.resumo_do_dia = ""
        self.carregar_resumo_diario()

    def carregar_resumo_diario(self) -> None:
        if not os.path.exists(self.arquivo_diario):
            return
        try:
            with open(self.arquivo_diario, "r", encoding="utf-8") as arquivo:
                conteudo = arquivo.read()
            marcador_pendentes = "\n\nINTERAÇÕES PENDENTES DE CONSOLIDAÇÃO:\n"
            cabecalho = f"RESUMO DO DIA {self.data_atual}:\n\n"
            corpo = conteudo[len(cabecalho):] if conteudo.startswith(cabecalho) else conteudo
            resumo, separador, pendentes = corpo.partition(marcador_pendentes)
            resumo = resumo.strip()
            self.resumo_do_dia = "" if resumo == "Resumo ainda em formação." else resumo
            if separador:
                self.historico_recente = [
                    linha.strip()
                    for linha in pendentes.splitlines()
                    if linha.strip()
                ][-50:]
                self.contador = len(self.historico_recente)
            self._log(f"📂 [MEMÓRIA] Resumo do dia {self.data_atual} carregado")
        except Exception as erro:
            self.resumo_do_dia = ""
            self.historico_recente = []
            self.contador = 0
            self._log(f"⚠️ [MEMÓRIA] não consegui carregar o resumo diário: {erro}")

    def salvar_resumo_diario(self) -> None:
        try:
            os.makedirs(self._pasta_memoria, exist_ok=True)
            resumo = self.resumo_do_dia.strip() or "Resumo ainda em formação."
            conteudo = f"RESUMO DO DIA {self.data_atual}:\n\n{resumo}"
            if self.historico_recente:
                conteudo += (
                    "\n\nINTERAÇÕES PENDENTES DE CONSOLIDAÇÃO:\n"
                    + "\n".join(self.historico_recente[-50:])
                )
            temporario = self.arquivo_diario + ".tmp"
            with open(temporario, "w", encoding="utf-8") as arquivo:
                arquivo.write(conteudo)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, self.arquivo_diario)
            self._log(f"💾 [MEMÓRIA] Resumo salvo em {self.arquivo_diario}")
        except Exception as erro:
            self._log(f"⚠️ Erro ao salvar resumo: {erro}")

    def adicionar_interacao(self, usuario: str, resposta_ia: str) -> None:
        usuario = " ".join(str(usuario or "").split()).strip()
        resposta_ia = " ".join(str(resposta_ia or "").split()).strip()
        if not usuario or not resposta_ia:
            return
        with self._lock:
            self._garantir_dia_atual()
            self.contador += 1
            horario = self._agora().strftime("%H:%M")
            self.historico_recente.append(
                f"[{horario}] Usuário: {usuario[:2000]} | Laylay: {resposta_ia[:2000]}"
            )
            self.historico_recente = self.historico_recente[-50:]
            # Materializa o turno antes de chamar a LLM. Assim, encerramento,
            # timeout ou queda de energia não apagam o lote ainda não resumido.
            self.salvar_resumo_diario()
            if self.contador >= 5:
                self.atualizar_resumo_diario()

    def contexto_do_dia_para_prompt(self, limite_chars: int = 1800) -> str:
        """Expõe resumo e lote pendente apenas quando o turno pedir o dia.

        O lote já está persistido no arquivo diário. Usá-lo como recuperação
        evita a falsa resposta "não tenho memória" enquanto a LLM de
        consolidação ainda não terminou, sem promover essas falas a fatos
        duráveis separados.
        """
        with self._lock:
            self._garantir_dia_atual()
            partes: list[str] = []
            if self.resumo_do_dia.strip():
                partes.append("Resumo consolidado:\n" + self.resumo_do_dia.strip())
            if self.historico_recente:
                cabecalho = "Interações recentes ainda não consolidadas:"
                disponivel = max(200, int(limite_chars) - len("\n\n".join(partes)) - len(cabecalho) - 2)
                escolhidas_reverso: list[str] = []
                usados = 0
                for linha in reversed(self.historico_recente):
                    linha = str(linha or "").strip()
                    if not linha:
                        continue
                    if escolhidas_reverso and usados + len(linha) + 1 > disponivel:
                        break
                    escolhidas_reverso.append(linha)
                    usados += len(linha) + 1
                if escolhidas_reverso:
                    partes.append(cabecalho + "\n" + "\n".join(reversed(escolhidas_reverso)))
            return "\n\n".join(partes)[: max(200, int(limite_chars))].strip()

    def atualizar_resumo_diario(self) -> None:
        with self._lock:
            if not self.historico_recente:
                return
            agora = self._agora()
            if self._ultima_tentativa_resumo_em is not None:
                try:
                    decorrido = (agora - self._ultima_tentativa_resumo_em).total_seconds()
                except Exception:
                    decorrido = self._intervalo_retentativa_s
                if decorrido < self._intervalo_retentativa_s:
                    return
            self._ultima_tentativa_resumo_em = agora
            self._log(f"🚀 [MEMÓRIA] Gerando resumo das últimas {len(self.historico_recente)} interações...")
            texto_para_resumir = "\n".join(self.historico_recente)
            prompt = (
                f"Resumo atual do dia:\n{self.resumo_do_dia}\n\n"
                f"Novas interações:\n{texto_para_resumir}\n\n"
                "Atualize o resumo do dia de forma concisa, mantendo apenas os fatos importantes, "
                "pedidos do usuário, preferências e eventos relevantes. Escreva em português."
            )
            mensagens = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Resuma tudo acima em um texto coeso e curto."},
            ]
            try:
                novo_resumo = str(self._enviar_mensagem(mensagens) or "").strip()
            except Exception as erro:
                self._log(
                    "⚠️ [MEMÓRIA] resumo diário adiado; interações preservadas: "
                    f"{type(erro).__name__}: {erro}"
                )
                return
            if not novo_resumo or "LAYLAY_LLM_INDISPONIVEL" in novo_resumo:
                self._log("⚠️ [MEMÓRIA] resumo diário adiado; LLM indisponível e lote preservado")
                return
            self.resumo_do_dia = novo_resumo
            self.historico_recente = []
            self.contador = 0
            self.salvar_resumo_diario()
