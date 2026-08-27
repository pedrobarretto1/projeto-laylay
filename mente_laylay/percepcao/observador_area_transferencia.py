"""Observação passiva e local da área de transferência.

O observador não recebe o texto bruto: a habilidade proprietária publica só
metadados sanitizados. Uma percepção relevante vira oportunidade para o modo
companhia, nunca comando e nunca memória permanente.
"""

from __future__ import annotations

import threading
import time
import re
import unicodedata
from collections import deque
from typing import Any, Callable, Mapping

from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)
from mente_laylay.autonomia.diretor_presenca import (
    decisao_presenca_aceita_para_entrega,
)


MODOS_OBSERVADOR = frozenset({"desligado", "sombra", "sugestao"})


def classificar_resposta_oferta(texto: str, acao_sugerida: str = "") -> str:
    """Reconhece resposta à oferta reutilizando a linguagem natural canônica.

    A área de transferência acrescenta somente verbos próprios da ação. A
    aceitação e a recusa comuns pertencem à mente única e não são mantidas em
    uma segunda lista de frases dentro desta habilidade.
    """
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    fala = " ".join("".join(c for c in base if not unicodedata.combining(c)).split())
    if not fala:
        return "ignorar"

    decisao_compartilhada = classificar_confirmacao_local(fala)
    if decisao_compartilhada is False:
        return "recusar"
    if decisao_compartilhada is True:
        return "aceitar"

    # Uma negação aplicada ao verbo da ação nunca pode virar aceite só porque
    # a frase também contém "investiga", "abre" ou "salva".
    if re.search(
        r"\bnao\b.{0,32}\b(?:investiga|pesquisa|procura|verifica|analisa|"
        r"abre|acessa|visita|entra|explica|resume|resuma|guarda|salva|anota)\b",
        fala,
    ):
        return "recusar"
    acoes = {
        "investigar_erro": r"\b(?:da uma olhada|olha|investiga|pesquisa|procura|verifica|analisa)\b",
        "abrir_link": r"\b(?:abre|acessa|visita|entra)\b",
        "explicar_codigo": r"\b(?:da uma olhada|olha|explica|verifica|analisa)\b",
        "resumir_texto": r"\b(?:resume|resuma|sintetiza|encurta)\b",
        "guardar_ideia": r"\b(?:guarda|salva|anota)\b",
    }
    acao = str(acao_sugerida or "").strip()
    padrao = acoes.get(acao) if acao else "|".join(f"(?:{item})" for item in acoes.values())
    if padrao and re.search(padrao, fala):
        return "aceitar"
    return "ignorar"


def oferta_deve_ceder_a_novo_comando(
    texto: str,
    acao_sugerida: str,
    *,
    texto_tem_comando_explicito: Callable[[str], bool] | None,
) -> bool:
    """Evita que uma oferta opcional capture um pedido operacional novo.

    Aceites, recusas e respostas que citam a ação sugerida continuam ligados à
    pendência. Só uma fala não relacionada e reconhecida pelo porteiro geral
    encerra silenciosamente a oferta para seguir pelo roteamento normal.
    """
    if classificar_resposta_oferta(texto, acao_sugerida) != "ignorar":
        return False
    if bool(
        callable(texto_tem_comando_explicito)
        and texto_tem_comando_explicito(texto)
    ):
        return True
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    fala = " ".join(
        "".join(c for c in base if not unicodedata.combining(c)).split()
    )
    # Uma pergunta com assunto próprio é uma nova interação, não uma resposta
    # contextual a "quer que eu...?". Aceites indiretos continuam disponíveis
    # ao classificador contextual porque não têm esse formato interrogativo.
    return bool(
        "?" in str(texto or "")
        or re.match(
            r"^(?:o que|quem|qual|quais|como|onde|quando|por que|porque)\b",
            fala,
        )
    )


class ObservadorAreaTransferenciaRuntime:
    def __init__(
        self,
        *,
        snapshot_getter: Callable[[], Mapping[str, Any]],
        considerar_presenca: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        contexto_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        oferta_entregue: Callable[[Mapping[str, Any]], Any] | None = None,
        modo: str = "sugestao",
        intervalo_s: float = 1.0,
        estabilidade_s: float = 3.0,
        clock: Callable[[], float] = time.monotonic,
        stop_event: threading.Event | None = None,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.snapshot_getter = snapshot_getter
        self.considerar_presenca = considerar_presenca
        self.contexto_getter = contexto_getter
        self.oferta_entregue = oferta_entregue
        modo_limpo = str(modo or "sugestao").casefold().strip()
        self.modo = modo_limpo if modo_limpo in MODOS_OBSERVADOR else "sombra"
        self.intervalo_s = max(0.25, float(intervalo_s))
        self.estabilidade_s = max(0.5, float(estabilidade_s))
        self.clock = clock
        self.stop_event = stop_event or threading.Event()
        self.log = log
        self._lock = threading.RLock()
        self._baseline_definida = False
        self._assinatura_atual = ""
        self._pendente: dict[str, Any] = {}
        self._processadas: deque[str] = deque(maxlen=128)
        self._processadas_set: set[str] = set()
        self._conteudos_ofertados: dict[str, float] = {}
        self._cooldown_conteudo_s = 1800.0
        self._diagnostico = {
            "modo": self.modo, "mudancas": 0, "relevantes": 0,
            "bloqueadas": 0, "ignoradas": 0, "publicadas": 0,
            "reagendadas": 0,
            "ultimo_tipo": "", "ultima_decisao": "inicio",
        }

    @staticmethod
    def _assinatura_snapshot(snapshot: Mapping[str, Any]) -> str:
        conteudo = str(snapshot.get("assinatura") or "")
        try:
            sequencia = max(0, int(snapshot.get("sequencia_evento") or 0))
        except (TypeError, ValueError):
            sequencia = 0
        return f"{conteudo}:{sequencia}" if conteudo and sequencia else conteudo

    def preparar_baseline(self) -> dict[str, Any]:
        """Fotografa apenas a assinatura inicial antes de iniciar a thread."""
        try:
            snapshot = dict(self.snapshot_getter() or {})
        except Exception as erro:
            self.log(f"⚠️ [CLIPBOARD:OBSERVADOR] baseline isolada: {type(erro).__name__}")
            return {"status": "falha"}
        assinatura = self._assinatura_snapshot(snapshot)
        if snapshot.get("status") != "ok" or not assinatura:
            return {"status": "sem_texto"}
        with self._lock:
            self._baseline_definida = True
            self._assinatura_atual = assinatura
            self._diagnostico["ultima_decisao"] = "baseline_preparada"
        return {"status": "baseline"}

    def marcar_conteudo_consumido(self, snapshot: Mapping[str, Any] | None = None) -> bool:
        """Silencia a oferta passiva quando o usuário já usou o conteúdo.

        Observação e execução vivem em threads distintas. Sem esta marca, o
        mesmo texto podia ser salvo num arquivo e logo depois gerar a pergunta
        "quer que eu faça um resumo?". Só a assinatura sanitizada atravessa a
        fronteira; o conteúdo bruto permanece dentro da habilidade.
        """
        dados = dict(snapshot or {})
        assinatura_conteudo = str(dados.get("assinatura") or "").strip()
        assinatura_evento = self._assinatura_snapshot(dados)
        if not assinatura_conteudo:
            return False
        agora = float(self.clock())
        with self._lock:
            self._conteudos_ofertados[assinatura_conteudo] = agora
            if assinatura_evento:
                self._assinatura_atual = assinatura_evento
                self._lembrar(assinatura_evento)
                if str(self._pendente.get("assinatura") or "") in {
                    assinatura_evento,
                    assinatura_conteudo,
                }:
                    self._pendente = {}
            self._diagnostico["ultima_decisao"] = "conteudo_consumido_explicitamente"
        return True

    def _finalizar_assinatura(self, assinatura: str) -> None:
        with self._lock:
            if str(self._pendente.get("assinatura") or "") == assinatura:
                self._pendente = {}
            self._lembrar(assinatura)

    def _reagendar(self, pendente: Mapping[str, Any], *, motivo: str, atraso_s: float = 8.0) -> None:
        agora = float(self.clock())
        item = dict(pendente or {})
        primeira = float(item.get("primeira_deteccao") or item.get("desde") or agora)
        if agora - primeira >= 300.0:
            self._finalizar_assinatura(str(item.get("assinatura") or ""))
            self._diagnostico["ultima_decisao"] = "expirada"
            return
        item["primeira_deteccao"] = primeira
        item["proxima_tentativa"] = agora + max(2.0, float(atraso_s))
        item["tentativas"] = int(item.get("tentativas") or 0) + 1
        with self._lock:
            self._pendente = item
            self._diagnostico["reagendadas"] += 1
            self._diagnostico["ultima_decisao"] = f"aguardando:{motivo}"
        self.log(
            "📋 [CLIPBOARD:OBSERVADOR] conteúdo relevante detectado; "
            f"aguardando um momento livre | motivo={motivo}"
        )

    def _lembrar(self, assinatura: str) -> None:
        if assinatura in self._processadas_set:
            return
        if len(self._processadas) == self._processadas.maxlen:
            antiga = self._processadas.popleft()
            self._processadas_set.discard(antiga)
        self._processadas.append(assinatura)
        self._processadas_set.add(assinatura)

    def _contexto(self) -> dict[str, Any]:
        try:
            valor = self.contexto_getter() or {}
            return dict(valor) if isinstance(valor, Mapping) else {}
        except Exception:
            return {}

    @staticmethod
    def _evento(snapshot: Mapping[str, Any], contexto: Mapping[str, Any]) -> dict[str, Any]:
        tipo = str(snapshot.get("tipo") or "").casefold()
        tamanho = max(0, int(snapshot.get("tamanho") or 0))
        titulo = str(contexto.get("titulo_janela") or "").strip()
        dominio = "jogo" if contexto.get("modo_jogo_ativo") else "rotina"
        base = {
            "origem": "observador_area_transferencia",
            "dominio": dominio,
            "momento_seguro": bool(contexto.get("momento_seguro", not contexto.get("modo_jogo_ativo"))),
            "executar_automaticamente": False,
            "validade_s": 90.0,
            "chave": f"clipboard_{tipo}_{ObservadorAreaTransferenciaRuntime._assinatura_snapshot(snapshot)[-24:]}",
        }
        janela = titulo[:80] if titulo else "janela atual"
        if tipo == "erro":
            return {**base, "categoria": "dica", "confianca": 0.92,
                "utilidade": 82, "fundamentada": True,
                "evidencias": ["mensagem de erro copiada", janela],
                "acao_sugerida": "investigar_erro",
                "fala": "Vi que você copiou uma mensagem de erro. Quer que eu investigue?"}
        if tipo == "link":
            host = str(snapshot.get("host") or "um site")[:80]
            return {**base, "categoria": "curiosidade", "confianca": 0.88,
                "utilidade": 65, "evidencias": ["link copiado", host],
                "acao_sugerida": "abrir_link",
                "fala": f"Você copiou um link de {host}. Quer que eu abra?"}
        if tipo == "codigo":
            return {**base, "categoria": "curiosidade", "confianca": 0.84,
                "utilidade": 64, "evidencias": ["trecho de código copiado", janela],
                "acao_sugerida": "explicar_codigo",
                "fala": "Esse trecho copiado parece código. Quer que eu dê uma olhada?"}
        if tipo == "texto_longo":
            return {**base, "categoria": "curiosidade", "confianca": 0.82,
                "utilidade": 60, "evidencias": ["texto longo copiado", f"{tamanho} caracteres"],
                "acao_sugerida": "resumir_texto",
                "fala": "Você copiou um texto grandinho. Quer que eu faça um resumo?"}
        if tipo == "ideia_pessoal":
            return {**base, "categoria": "companhia", "confianca": 0.82,
                "utilidade": 62, "evidencias": ["ideia pessoal copiada", janela],
                "acao_sugerida": "guardar_ideia",
                "fala": "Isso que você copiou parece uma ideia sua. Quer que eu guarde?"}
        return {}

    def observar_uma_vez(self) -> dict[str, Any]:
        if self.modo == "desligado":
            return {"status": "desligado"}
        try:
            snapshot = dict(self.snapshot_getter() or {})
        except Exception as erro:
            self.log(f"⚠️ [CLIPBOARD:OBSERVADOR] leitura isolada: {type(erro).__name__}")
            return {"status": "falha"}
        if snapshot.get("status") != "ok":
            return {"status": "sem_texto"}
        assinatura = self._assinatura_snapshot(snapshot)
        if not assinatura:
            return {"status": "sem_assinatura"}
        agora = float(self.clock())
        assinatura_conteudo = str(snapshot.get("assinatura") or "")
        ultima_oferta = float(self._conteudos_ofertados.get(assinatura_conteudo) or 0.0)
        if assinatura_conteudo and ultima_oferta and agora - ultima_oferta < self._cooldown_conteudo_s:
            # O contador do clipboard muda quando um aplicativo republica o
            # mesmo texto. Isso não transforma um erro já oferecido numa nova
            # oportunidade de interromper o usuário.
            with self._lock:
                self._assinatura_atual = assinatura
                self._pendente = {}
                self._lembrar(assinatura)
                self._diagnostico["ultima_decisao"] = "conteudo_ja_ofertado"
            return {"status": "duplicada_conteudo", "tipo": str(snapshot.get("tipo") or "")}
        with self._lock:
            if not self._baseline_definida:
                self._baseline_definida = True
                self._assinatura_atual = assinatura
                self._diagnostico["ultima_decisao"] = "baseline"
                return {"status": "baseline"}
            if assinatura != self._assinatura_atual:
                self._assinatura_atual = assinatura
                self._pendente = {
                    "assinatura": assinatura,
                    "desde": agora,
                    "primeira_deteccao": agora,
                    "snapshot": snapshot,
                }
                self._diagnostico["mudancas"] += 1
                return {"status": "estabilizando"}
            pendente = dict(self._pendente)
            if not pendente or pendente.get("assinatura") != assinatura:
                return {"status": "sem_mudanca"}
            proxima_tentativa = float(pendente.get("proxima_tentativa") or 0.0)
            if proxima_tentativa and agora < proxima_tentativa:
                return {"status": "aguardando_contexto"}
            desde = pendente.get("desde")
            if agora - float(agora if desde is None else desde) < self.estabilidade_s:
                return {"status": "estabilizando"}
            if assinatura in self._processadas_set:
                self._pendente = {}
                return {"status": "duplicada"}

        dados = dict(pendente.get("snapshot") or snapshot)
        tipo = str(dados.get("tipo") or "")
        self._diagnostico["ultimo_tipo"] = tipo
        if dados.get("bloqueado") or tipo == "sensivel":
            self._finalizar_assinatura(assinatura)
            self._diagnostico["bloqueadas"] += 1
            self._diagnostico["ultima_decisao"] = "sensivel_ignorado"
            self.log("🛡️ [CLIPBOARD:OBSERVADOR] conteúdo sensível ignorado localmente.")
            return {"status": "bloqueada", "motivo": "sensivel"}
        if dados.get("escrita_propria") or not dados.get("relevante"):
            self._finalizar_assinatura(assinatura)
            self._diagnostico["ignoradas"] += 1
            self._diagnostico["ultima_decisao"] = "ignorada"
            return {"status": "ignorada", "tipo": tipo}
        self._diagnostico["relevantes"] += 1
        evento = self._evento(dados, self._contexto())
        if not evento:
            self._finalizar_assinatura(assinatura)
            self._diagnostico["ignoradas"] += 1
            return {"status": "ignorada", "tipo": tipo}
        contexto = self._contexto()
        acao_sugerida = str(evento.get("acao_sugerida") or "")
        silenciadas = dict(contexto.get("clipboard_ofertas_silenciadas") or {})
        try:
            silenciada_ate = float(silenciadas.get(acao_sugerida) or 0.0)
        except (TypeError, ValueError):
            silenciada_ate = 0.0
        if acao_sugerida and silenciada_ate > time.time():
            self._finalizar_assinatura(assinatura)
            self._diagnostico["ignoradas"] += 1
            self._diagnostico["ultima_decisao"] = "silenciada_por_recusa"
            return {
                "status": "silenciada_por_recusa",
                "tipo": tipo,
                "acao_sugerida": acao_sugerida,
            }
        if self.modo == "sombra" or not callable(self.considerar_presenca):
            self._finalizar_assinatura(assinatura)
            self._diagnostico["ultima_decisao"] = "sombra"
            self.log(f"📋 [CLIPBOARD:OBSERVADOR] sombra | tipo={tipo} tamanho={dados.get('tamanho', 0)}")
            return {"status": "sombra", "tipo": tipo, "evento": evento}
        if callable(self.oferta_entregue) and evento.get("acao_sugerida"):
            oferta = {
                "origem": "observador_area_transferencia",
                "tipo": tipo,
                "acao_sugerida": str(evento.get("acao_sugerida") or ""),
                "fala": str(evento.get("fala") or ""),
                # Somente a assinatura sanitizada cruza o observador. O texto
                # bruto continua restrito ao runtime do clipboard.
                "assinatura": str(dados.get("assinatura") or ""),
            }
            fala_iniciada = {"valor": False}

            def _ao_materializar_fala(fala: str) -> None:
                oferta["fala"] = str(fala or "").strip()

            def _ao_iniciar() -> None:
                # A pergunta passa a existir na mente antes de ficar audível.
                # Assim, uma resposta curta e imediata já encontra a pendência.
                assinatura_base = str(dados.get("assinatura") or "")
                if assinatura_base:
                    self._conteudos_ofertados[assinatura_base] = float(self.clock())
                fala_iniciada["valor"] = True
                self.oferta_entregue(oferta)

            def _ao_concluir(entregue: bool, motivo: str) -> None:
                if entregue:
                    self._finalizar_assinatura(assinatura)
                elif fala_iniciada["valor"]:
                    # A pergunta já chegou ao terminal/áudio. Uma resposta do
                    # usuário pode interromper a reprodução e ainda assim deve
                    # conservar a autorização pendente.
                    self._finalizar_assinatura(assinatura)
                else:
                    self.oferta_entregue({**oferta, "cancelada": True})
                    self._reagendar(pendente, motivo=motivo or "fala_nao_entregue")

            evento["ao_iniciar"] = _ao_iniciar
            evento["ao_concluir"] = _ao_concluir
            evento["ao_materializar_fala"] = _ao_materializar_fala
        try:
            decisao = dict(self.considerar_presenca(evento) or {})
        except Exception as erro:
            self.log(f"⚠️ [CLIPBOARD:OBSERVADOR] presença isolada: {type(erro).__name__}")
            self._reagendar(pendente, motivo="falha_presenca")
            return {"status": "falha_presenca", "tipo": tipo}
        self._diagnostico["publicadas"] += 1
        self._diagnostico["ultima_decisao"] = str(decisao.get("status") or "publicada")
        status_decisao = str(decisao.get("status") or "")
        if not decisao_presenca_aceita_para_entrega(decisao):
            self._reagendar(
                pendente,
                motivo=str(decisao.get("motivo") or status_decisao or "nao_emitida"),
            )
            return {"status": "aguardando_contexto", "tipo": tipo, "decisao": decisao}
        if not callable(self.oferta_entregue):
            self._finalizar_assinatura(assinatura)
        else:
            # A fila aceitou, mas a confirmação real virá por `ao_concluir`.
            # Evita publicar a mesma oferta a cada segundo enquanto ela espera.
            with self._lock:
                atual = dict(self._pendente)
                if str(atual.get("assinatura") or "") == assinatura:
                    atual["proxima_tentativa"] = agora + 60.0
                    self._pendente = atual
        self.log(f"📋 [CLIPBOARD:OBSERVADOR] oferta agendada | tipo={tipo}")
        return {"status": "publicada", "tipo": tipo, "decisao": decisao}

    def executar(self) -> None:
        self.log(
            "📋 [CLIPBOARD:OBSERVADOR] ativo | "
            f"modo={self.modo} intervalo={self.intervalo_s:g}s "
            f"estabilidade={self.estabilidade_s:g}s"
        )
        while not self.stop_event.is_set():
            self.observar_uma_vez()
            self.stop_event.wait(self.intervalo_s)

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._diagnostico)


def criar_observador_area_transferencia_runtime(**kwargs: Any) -> ObservadorAreaTransferenciaRuntime:
    return ObservadorAreaTransferenciaRuntime(**kwargs)
