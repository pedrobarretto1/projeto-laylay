"""Observabilidade estruturada e somente leitura para o DEV Console.

Este runtime é uma porta de diagnóstico: captura o terminal legado, normaliza
eventos e responde consultas allowlist. Ele nunca executa comandos do sistema.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from datetime import datetime
import os
import re
import sys
import threading
import time
from typing import Any, TextIO

from mente_laylay.integracao.eventos_dev import classificar_categoria_evento_dev


_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_CREDENCIAL_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|senha|password|secret|authorization)"
    r"(\s*[=:]\s*)(?:bearer\s+)?[^\s|,;]+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_QUERY_CREDENCIAL_RE = re.compile(
    r"(?i)([?&](?:token|key|api_key|signature|secret)=)[^&#\s]+"
)
_TOKEN_SOLTO_RE = re.compile(
    r"(?i)\b(?:sk-(?:or-v1-)?[a-z0-9_-]{8,}|gh[pousr]_[a-z0-9]{16,}|"
    r"eyj[a-z0-9_-]{6,}\.[a-z0-9_-]{6,}\.[a-z0-9_-]{6,})\b"
)
_EMAIL_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"
)
_TRACE_RE = re.compile(
    r"(?i)\b(?:trace[#:\s-]*|turno[-_:#\s]*)([a-z0-9_.:-]+)"
)
_DURACAO_RE = re.compile(r"(?i)\b(?:dura(?:ç|c)ão|lat[eê]ncia)?\s*[=:]?\s*(\d+(?:[.,]\d+)?)\s*ms\b")
def sanitizar_texto_dev(valor: Any, limite: int = 1_200) -> str:
    """Remove controles e credenciais sem destruir informação diagnóstica."""
    texto = _ANSI_RE.sub("", str(valor or ""))
    texto = texto.replace("\x00", "")
    texto = "".join(
        caractere
        for caractere in texto
        if caractere in "\n\t" or ord(caractere) >= 32
    )
    texto = _CREDENCIAL_RE.sub(
        lambda achado: f"{achado.group(1)}{achado.group(2)}[protegido]",
        texto,
    )
    texto = _BEARER_RE.sub("Bearer [protegido]", texto)
    texto = _QUERY_CREDENCIAL_RE.sub(
        lambda achado: f"{achado.group(1)}[protegido]",
        texto,
    )
    texto = _TOKEN_SOLTO_RE.sub("[protegido]", texto)
    texto = _EMAIL_RE.sub("[email_protegido]", texto)
    pasta_usuario = os.path.expanduser("~")
    if pasta_usuario and pasta_usuario not in {"~", "/"}:
        texto = re.sub(
            re.escape(pasta_usuario),
            "%USERPROFILE%",
            texto,
            flags=re.IGNORECASE,
        )
    return texto.strip()[: max(32, int(limite))]


def _categoria(texto: str) -> str:
    return classificar_categoria_evento_dev(texto)


def _nivel(texto: str, origem: str) -> str:
    normalizado = texto.casefold()
    if origem == "stderr" or any(
        token in normalizado for token in ("❌", "traceback", "exception", "error")
    ):
        return "error"
    if any(token in normalizado for token in ("⚠", "warning", "falha", "timeout")):
        return "warning"
    if any(token in normalizado for token in ("✅", "sucesso", "confirmado", "pass")):
        return "success"
    return "info"


def _trace_id(texto: str) -> str:
    achado = _TRACE_RE.search(texto)
    if not achado:
        return ""
    identificador = re.sub(r"[^A-Za-z0-9_.:-]+", "", achado.group(1))
    if texto[achado.start():].casefold().startswith("turno"):
        return identificador if identificador.casefold().startswith("turno-") else f"turno-{identificador}"
    return identificador[:72]


def _duracao_ms(texto: str) -> float | None:
    achado = _DURACAO_RE.search(texto)
    if not achado:
        return None
    try:
        return round(min(600_000.0, float(achado.group(1).replace(",", "."))), 2)
    except ValueError:
        return None


def _identificador(valor: Any, limite: int = 80) -> str:
    return re.sub(r"[^A-Za-z0-9À-ÿ_.:/-]+", "_", str(valor or "").strip())[:limite]


def _formatar_instante(valor: Any) -> str:
    try:
        instante = float(valor or 0.0)
    except (TypeError, ValueError):
        return "desconhecido"
    if instante <= 0:
        return "desconhecido"
    try:
        return datetime.fromtimestamp(instante).astimezone().isoformat(
            timespec="milliseconds"
        )
    except (OSError, OverflowError, ValueError):
        return f"epoch:{instante:.3f}"


class DevConsoleRuntime:
    """Buffer thread-safe de eventos e consultas diagnósticas sem efeitos."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.time,
        limite_eventos: int = 1_000,
        estado_getter: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        self.clock = clock
        self.limite_eventos = max(100, min(10_000, int(limite_eventos)))
        self._estado_getter = estado_getter
        self._pressao_getter: Callable[[], Mapping[str, Any]] | None = None
        self._eventos: deque[dict[str, Any]] = deque(maxlen=self.limite_eventos)
        self._eventos_descartados = 0
        self._sequencia = 0
        self._lock = threading.RLock()

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    def configurar_estado_getter(
        self,
        getter: Callable[[], Mapping[str, Any]] | None,
    ) -> None:
        self._estado_getter = getter

    def configurar_pressao_getter(
        self,
        getter: Callable[[], Mapping[str, Any]] | None,
    ) -> None:
        """Conecta diagnóstico do transporte sem duplicar seu estado."""
        self._pressao_getter = getter

    def registrar_log_oculto(
        self,
        texto: str,
        *,
        origem: str = "stdout",
    ) -> dict[str, Any]:
        return self.registrar_linha(
            texto,
            origem=origem,
            profundidade="debug",
        )

    def registrar_linha(
        self,
        texto: Any,
        *,
        origem: str = "stdout",
        profundidade: str = "normal",
    ) -> dict[str, Any]:
        mensagem = sanitizar_texto_dev(texto)
        if not mensagem:
            return {}
        origem = origem if origem in {"stdout", "stderr", "runtime"} else "runtime"
        profundidade = (
            profundidade if profundidade in {"normal", "debug", "trace"}
            else "normal"
        )
        with self._lock:
            self._sequencia += 1
            evento: dict[str, Any] = {
                "id": f"dev-{self._sequencia:08d}",
                "sequence": self._sequencia,
                "timestamp": float(self.clock()),
                "level": _nivel(mensagem, origem),
                "category": _categoria(mensagem),
                "event": "terminal_line",
                "trace_id": _trace_id(mensagem),
                "message": mensagem,
                "source": origem,
                "depth": profundidade,
            }
            duracao = _duracao_ms(mensagem)
            if duracao is not None:
                evento["duration_ms"] = duracao
            if len(self._eventos) == self._eventos.maxlen:
                self._eventos_descartados += 1
            self._eventos.append(evento)
            return dict(evento)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "schema_version": 1,
                "sequence": self._sequencia,
                "event_limit": self.limite_eventos,
                "events_dropped": self._eventos_descartados,
                "events": [dict(item) for item in self._eventos],
            }

    def _estado(self) -> dict[str, Any]:
        if not callable(self._estado_getter):
            return {}
        try:
            bruto = self._estado_getter()
            return dict(bruto) if isinstance(bruto, Mapping) else {}
        except Exception:
            return {}

    @staticmethod
    def _estado_mental(estado: Mapping[str, Any]) -> dict[str, Any]:
        """Aceita o snapshot completo sem quebrar getters mentais legados."""
        mental = estado.get("mental")
        if isinstance(mental, Mapping):
            return dict(mental)
        return dict(estado)

    @staticmethod
    def _resultado(
        comando: str,
        tipo: str,
        linhas: list[str],
        *,
        ok: bool = True,
    ) -> dict[str, Any]:
        return {
            "ok": bool(ok),
            "kind": tipo,
            "command": comando,
            "lines": [sanitizar_texto_dev(linha, 500) for linha in linhas[:120]],
        }

    def consultar(self, comando: str) -> dict[str, Any]:
        comando = re.sub(r"\s+", " ", str(comando or "").strip().casefold())[:160]
        estado = self._estado()
        mental = self._estado_mental(estado)
        if comando == "status" or comando.startswith("status "):
            return self._consultar_status(comando, mental)
        if comando == "perf" or comando.startswith("perf "):
            return self._consultar_performance(comando, mental)
        if comando == "errors" or comando.startswith("errors "):
            return self._consultar_erros(comando, mental)
        if comando.startswith("trace "):
            return self._consultar_trace(comando, mental)
        if comando.startswith("inspect "):
            return self._consultar_estado(comando, estado)
        return self._resultado(
            comando,
            "maintenance",
            ["Consulta indisponível ou em manutenção; nenhum efeito foi executado."],
            ok=False,
        )

    def _consultar_status(self, comando: str, estado: Mapping[str, Any]) -> dict[str, Any]:
        servicos = estado.get("diagnostico_servicos")
        linhas = ["LAYLAY STATUS"]
        filtro = comando.removeprefix("status").strip()
        aliases = {"memory": "mem", "agents": "agent"}
        termo = aliases.get(filtro, filtro)
        if isinstance(servicos, Mapping) and servicos:
            for nome, valor in list(servicos.items())[:30]:
                if termo and termo != "all" and termo not in str(nome).casefold():
                    continue
                item = dict(valor) if isinstance(valor, Mapping) else {}
                situacao = _identificador(item.get("estado") or "desconhecido", 32)
                tentativas = int(item.get("tentativa") or 0)
                linhas.append(f"{_identificador(nome, 48):<30} {situacao:<16} tentativas={tentativas}")
        if len(linhas) == 1:
            linhas.append("Sem estados de serviço observados.")
        return self._resultado(comando, "status", linhas)

    def _consultar_performance(self, comando: str, estado: Mapping[str, Any]) -> dict[str, Any]:
        metricas_brutas = estado.get("diagnostico_metricas")
        metricas = dict(metricas_brutas) if isinstance(metricas_brutas, Mapping) else {}
        linhas = [
            "PERFORMANCE",
            "COMPONENTE                     ÚLTIMO      P50      P95   MÁXIMO   LIMITE",
        ]
        filtro = comando.removeprefix("perf").strip()
        grupos = {
            "llm": ("llm",),
            "memory": ("memoria", "memória", "prompt"),
            "actions": (
                "acao", "ação", "exec", "execucao", "execução",
                "dispatcher", "pos_processamento",
            ),
        }
        termos = grupos.get(filtro, (filtro,) if filtro else ())
        traces = [
            dict(item)
            for item in list(estado.get("diagnostico_traces_turno") or [])
            if isinstance(item, Mapping)
        ]
        lentas: list[str] = []

        def numero(item: Mapping[str, Any], chave: str) -> float:
            try:
                return max(0.0, float(item.get(chave) or 0.0))
            except (TypeError, ValueError):
                return 0.0

        for nome, bruto in sorted(metricas.items()):
            nome_normalizado = str(nome).casefold()
            if termos:
                if filtro in grupos:
                    corresponde = any(
                        nome_normalizado == termo
                        or nome_normalizado.startswith(f"{termo}_")
                        or nome_normalizado.endswith(f"_{termo}")
                        for termo in termos
                    )
                else:
                    corresponde = any(
                        termo in nome_normalizado for termo in termos
                    )
                if not corresponde:
                    continue
            item = dict(bruto) if isinstance(bruto, Mapping) else {}
            ultimo = numero(item, "ultimo_ms")
            p50 = numero(item, "p50_ms")
            p95 = numero(item, "p95_ms")
            maximo = numero(item, "max_ms")
            orcamento = numero(item, "orcamento_ms")
            excedeu_ultimo = bool(
                item.get("excedeu_orcamento") or (
                    orcamento and ultimo > orcamento
                )
            )
            excedeu_p95 = bool(orcamento and p95 > orcamento)
            excedeu_historico = bool(orcamento and maximo > orcamento)
            alerta = (
                " ⚠ EXCEDEU_ULTIMO" if excedeu_ultimo
                else " ⚠ EXCEDEU_P95" if excedeu_p95
                else " ⚠ EXCEDEU_HISTORICO" if excedeu_historico
                else ""
            )
            linhas.append(
                f"{_identificador(nome, 28):<28} "
                f"{ultimo:>7.1f} {p50:>8.1f} {p95:>8.1f} "
                f"{maximo:>8.1f} {orcamento:>8.1f} "
                f"amostras={int(item.get('amostras') or 0)} "
                f"excessos={int(item.get('excessos') or 0)}{alerta}"
            )
            if alerta:
                trace_id = ""
                observado = ultimo
                for trace in reversed(traces):
                    etapas = trace.get("etapas")
                    etapas = dict(etapas) if isinstance(etapas, Mapping) else {}
                    etapa = etapas.get(nome)
                    etapa = dict(etapa) if isinstance(etapa, Mapping) else {}
                    duracao_trace = numero(etapa, "duracao_ms")
                    if orcamento and duracao_trace > orcamento:
                        trace_id = _identificador(trace.get("turno_id"), 72)
                        observado = duracao_trace
                        break
                lentas.append(
                    f"FRONTEIRA_LENTA={_identificador(nome, 64)} "
                    f"limite_ms={orcamento:.1f} observado_ms={observado:.1f} "
                    f"trace={trace_id or 'nao_retido'} evidencia="
                    f"{'TRACE_ETAPA' if trace_id else 'METRICA_AGREGADA'}"
                )
        if len(linhas) == 2:
            linhas.append(
                "Nenhuma métrica corresponde ao filtro."
                if filtro and metricas
                else "Sem métricas observadas."
            )
        else:
            linhas.extend(lentas)
        if filtro in {"", "llm"}:
            orcamento_bruto = estado.get("diagnostico_orcamento_llm")
            orcamento_llm = (
                dict(orcamento_bruto)
                if isinstance(orcamento_bruto, Mapping)
                else {}
            )
            if orcamento_llm:
                turno_bruto = orcamento_llm.get("turno_atual")
                turno = dict(turno_bruto) if isinstance(turno_bruto, Mapping) else {}

                def inteiro(chave: str, fonte: Mapping[str, Any] = orcamento_llm) -> int:
                    try:
                        return max(0, int(fonte.get(chave) or 0))
                    except (TypeError, ValueError):
                        return 0

                bloqueios_brutos = orcamento_llm.get("bloqueios_por_motivo")
                bloqueios = (
                    dict(bloqueios_brutos)
                    if isinstance(bloqueios_brutos, Mapping)
                    else {}
                )
                resumo_bloqueios = ", ".join(
                    f"{_identificador(motivo, 48)}={inteiro(str(motivo), bloqueios)}"
                    for motivo in sorted(bloqueios, key=lambda item: str(item))
                ) or "nenhum"
                linhas.extend((
                    "ORÇAMENTO LLM",
                    f"turno={_identificador(turno.get('turno_id'), 72) or 'nenhum'} "
                    f"classe={_identificador(turno.get('classe'), 24) or 'desconhecida'} "
                    f"chamadas={inteiro('chamadas', turno)}/"
                    f"{inteiro('limite_chamadas_turno')}",
                    f"autorizadas={inteiro('chamadas_autorizadas')} "
                    f"bloqueadas={inteiro('chamadas_bloqueadas')} "
                    f"falhas_consecutivas={inteiro('falhas_consecutivas')}",
                    "circuito_aberto="
                    f"{'sim' if orcamento_llm.get('circuito_aberto') is True else 'não'} "
                    f"bloqueios={resumo_bloqueios}",
                ))
        if not filtro:
            with self._lock:
                eventos_retidos = len(self._eventos)
                eventos_limite = int(self._eventos.maxlen or 0)
                eventos_descartados = self._eventos_descartados
            linhas.extend((
                "PRESSÃO DOS BUFFERS",
                f"dev_console eventos={eventos_retidos}/{eventos_limite} "
                f"descartados={eventos_descartados}",
            ))
            pressao: Mapping[str, Any] = {}
            if callable(self._pressao_getter):
                try:
                    obtida = self._pressao_getter()
                    if isinstance(obtida, Mapping):
                        pressao = obtida
                except Exception:
                    pressao = {}
            if pressao:
                def inteiro_pressao(chave: str) -> int:
                    try:
                        return max(0, int(pressao.get(chave) or 0))
                    except (TypeError, ValueError):
                        return 0

                linhas.append(
                    "desktop_bridge "
                    f"eventos={inteiro_pressao('eventos_retidos')}/"
                    f"{inteiro_pressao('eventos_limite')} "
                    f"descartados={inteiro_pressao('eventos_descartados')} "
                    f"entradas={inteiro_pressao('entradas_pendentes')}/"
                    f"{inteiro_pressao('entradas_limite')} "
                    "entradas_descartadas="
                    f"{inteiro_pressao('entradas_descartadas')}"
                )
            else:
                linhas.append("desktop_bridge pressão não observada")
        return self._resultado(comando, "performance", linhas)

    def _consultar_erros(self, comando: str, estado: Mapping[str, Any]) -> dict[str, Any]:
        falhas = [
            dict(item) for item in list(estado.get("diagnostico_falhas") or [])
            if isinstance(item, Mapping)
        ]
        codigos_existentes = {
            str(item.get("error_code") or item.get("codigo") or "").upper()
            for item in falhas
        }
        falhas.extend(
            item for item in self._detectar_alertas_semanticos(estado)
            if str(item.get("error_code") or "").upper() not in codigos_existentes
        )
        seletor = comando.removeprefix("errors").strip()
        if seletor:
            return self._consultar_ocorrencias_erro(comando, falhas, seletor)
        linhas = ["FAILURE CENTER"]
        if not falhas:
            linhas.append("Nenhuma falha técnica observada.")
            return self._resultado(comando, "errors", linhas)
        traces = {
            str(item.get("turno_id") or ""): dict(item)
            for item in list(estado.get("diagnostico_traces_turno") or [])
            if isinstance(item, Mapping) and item.get("turno_id")
        }
        metricas = (
            dict(estado.get("diagnostico_metricas") or {})
            if isinstance(estado.get("diagnostico_metricas"), Mapping)
            else {}
        )
        grupos: dict[tuple[str, str], dict[str, Any]] = {}
        for falha in falhas:
            componente = _identificador(
                falha.get("componente") or "desconhecido", 64,
            )
            error_code = _identificador(
                falha.get("error_code") or falha.get("codigo") or "falha", 80,
            )
            chave = (componente, error_code)
            grupo = grupos.setdefault(chave, {
                "ocorrencias": 0,
                "registros": 0,
                "primeira": 0.0,
                "ultima": 0.0,
                "evento_mais_recente": {},
            })
            try:
                ocorrencias = max(1, int(falha.get("ocorrencias") or 1))
            except (TypeError, ValueError):
                ocorrencias = 1
            try:
                primeira = float(
                    falha.get("ts_primeira") or falha.get("ts") or 0.0
                )
                ultima = float(
                    falha.get("ts_ultima") or falha.get("ts") or primeira
                )
            except (TypeError, ValueError):
                primeira = ultima = 0.0
            grupo["ocorrencias"] += ocorrencias
            grupo["registros"] += 1
            if primeira and (
                not grupo["primeira"] or primeira < grupo["primeira"]
            ):
                grupo["primeira"] = primeira
            if ultima >= grupo["ultima"]:
                grupo["ultima"] = ultima
                grupo["evento_mais_recente"] = falha

        ordenados = sorted(
            grupos.items(),
            key=lambda item: (
                float(item[1].get("ultima") or 0.0),
                int(item[1].get("ocorrencias") or 0),
            ),
            reverse=True,
        )
        for (componente, error_code), grupo in ordenados[:30]:
            ultima = dict(grupo.get("evento_mais_recente") or {})
            metrica = (
                dict(metricas.get(componente) or {})
                if isinstance(metricas.get(componente), Mapping)
                else {}
            )
            trace_id = _identificador(ultima.get("turno_id"), 72)
            trace = traces.get(str(ultima.get("turno_id") or ""), {})
            primeira_red = ""
            etapas = trace.get("etapas") if isinstance(trace, Mapping) else {}
            if isinstance(etapas, Mapping):
                primeira_red = next((
                    str(nome) for nome, etapa in etapas.items()
                    if isinstance(etapa, Mapping) and etapa.get("sucesso") is False
                ), "")
            linhas.append(
                f"componente={componente} error_code={error_code} "
                f"tipo={_identificador(ultima.get('tipo') or 'desconhecido', 48)} "
                f"ocorrencias={int(grupo['ocorrencias'])} "
                f"registros={int(grupo['registros'])} "
                f"primeira={_formatar_instante(grupo['primeira'])} "
                f"ultima={_formatar_instante(grupo['ultima'])} "
                f"classe={_identificador(ultima.get('classe') or 'nao_classificada', 24)} "
                f"classe_origem={_identificador(ultima.get('classe_origem') or 'legado', 24)} "
                f"impacto={_identificador(ultima.get('impacto'), 20)} "
                f"fallback={_identificador(ultima.get('fallback') or 'nenhum', 36)} "
                f"ultimo_sucesso={_formatar_instante(metrica.get('ts_ultimo_sucesso'))} "
                f"trace={trace_id or 'ausente'} "
                f"primeira_red={_identificador(primeira_red, 48) or 'nao_observada'} "
                f"evidencia={_identificador(ultima.get('evidencia') or 'EVENTO_TECNICO', 48)} "
                "causa=NAO_PROVADA"
            )
        if len(ordenados) > 30:
            linhas.append(
                f"TRUNCADO grupos_exibidos=30 grupos_totais={len(ordenados)}"
            )
        return self._resultado(comando, "errors", linhas)

    def _detectar_alertas_semanticos(
        self,
        estado: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        bruto = estado.get("ultima_acao_contrato")
        acao = dict(bruto) if isinstance(bruto, Mapping) else {}
        if acao.get("executou") is not True or acao.get("confirmado") is True:
            return []
        confirmado = acao.get("confirmado")
        evidencia = str(acao.get("evidencia_confirmacao") or "").strip()
        if confirmado is False:
            error_code = "UNVERIFIED_SUCCESS"
        elif confirmado is None and not evidencia:
            error_code = "RECEIPT_MISSING"
        else:
            return []
        try:
            instante = float(estado.get("ultima_acao_ts") or self.clock())
        except (TypeError, ValueError):
            instante = float(self.clock())
        turno_id = _identificador(acao.get("id_solicitacao"), 72)
        ocorrencia = {
            "ts": instante,
            **({"turno_id": turno_id} if turno_id else {}),
        }
        return [{
            "componente": "contrato_execucao",
            "codigo": error_code,
            "error_code": error_code,
            "tipo": "semantic_warning",
            "classe": "defeito",
            "classe_origem": "detector_semantico",
            "impacto": "comando",
            "impacto_origem": "detector_semantico",
            "fallback": "nenhum",
            "fallback_origem": "ausente",
            "evidencia": "CONTRATO_ACAO",
            "turno_id": turno_id,
            "ts": instante,
            "ts_primeira": instante,
            "ts_ultima": instante,
            "ocorrencias": 1,
            "ocorrencias_recentes": [ocorrencia],
        }]

    def _consultar_ocorrencias_erro(
        self,
        comando: str,
        falhas: list[dict[str, Any]],
        seletor: str,
    ) -> dict[str, Any]:
        componente_alvo, _, codigo_alvo = seletor.partition(":")
        selecionadas = [
            falha for falha in falhas
            if str(falha.get("componente") or "").casefold() == componente_alvo
            and str(
                falha.get("error_code") or falha.get("codigo") or ""
            ).casefold() == codigo_alvo
        ]
        if not selecionadas:
            return self._resultado(
                comando,
                "errors",
                [f"FAILURE DETAIL {seletor}", "Nenhuma ocorrência retida."],
                ok=False,
            )

        ocorrencias: list[dict[str, Any]] = []
        total = 0
        for falha in selecionadas:
            try:
                total += max(1, int(falha.get("ocorrencias") or 1))
            except (TypeError, ValueError):
                total += 1
            recentes = [
                dict(item) for item in list(
                    falha.get("ocorrencias_recentes") or []
                )
                if isinstance(item, Mapping)
            ]
            if not recentes:
                recentes = [{
                    "ts": falha.get("ts_ultima") or falha.get("ts") or 0.0,
                    **(
                        {"turno_id": falha.get("turno_id")}
                        if falha.get("turno_id") else {}
                    ),
                }]
            ocorrencias.extend(recentes)

        def instante(item: Mapping[str, Any]) -> float:
            try:
                return float(item.get("ts") or 0.0)
            except (TypeError, ValueError):
                return 0.0

        ocorrencias.sort(key=instante)
        retidas = ocorrencias[-100:]
        linhas = [
            f"FAILURE DETAIL {seletor}",
            f"TOTAL={total} RETIDAS={len(retidas)} "
            f"NAO_RETIDAS={max(0, total - len(retidas))}",
        ]
        for indice, ocorrencia in enumerate(retidas, start=1):
            linhas.append(
                f"OCCURRENCE {indice} ts={_formatar_instante(instante(ocorrencia))} "
                f"trace={_identificador(ocorrencia.get('turno_id'), 72) or 'ausente'} "
                "evidencia=EVENTO_TECNICO causa=NAO_PROVADA"
            )
        return self._resultado(comando, "errors", linhas)

    def _consultar_trace(self, comando: str, estado: Mapping[str, Any]) -> dict[str, Any]:
        traces = [
            dict(item) for item in list(estado.get("diagnostico_traces_turno") or [])
            if isinstance(item, Mapping)
        ]
        argumento = comando.removeprefix("trace ").strip()
        if argumento == "errors":
            traces = [item for item in traces if item.get("sucesso") is False]
        elif argumento.startswith("turn "):
            numero = argumento.removeprefix("turn ").strip().lstrip("0") or "0"
            traces = [
                item for item in traces
                if str(item.get("turno_id") or "").split("-")[-1].lstrip("0") == numero
            ]
        elif argumento != "last":
            traces = [
                item for item in traces
                if str(item.get("turno_id") or "").casefold() == argumento
            ]
        if not traces:
            return self._resultado(
                comando, "trace", ["Nenhum trace correspondente foi observado."], ok=False,
            )
        trace = traces[-1]
        trace_id = _identificador(trace.get("turno_id") or "desconhecido", 72)
        linhas = [f"TRACE {trace_id}"]
        for chave in ("origem", "rota", "fase", "backend", "modelo"):
            if trace.get(chave):
                linhas.append(f"{chave:<10} {_identificador(trace.get(chave), 96)}")
        etapas = trace.get("etapas") if isinstance(trace.get("etapas"), Mapping) else {}
        primeira_red = ""
        for nome, bruto in etapas.items():
            etapa = dict(bruto) if isinstance(bruto, Mapping) else {}
            sucesso = etapa.get("sucesso")
            estado_etapa = (
                "GREEN" if sucesso is True
                else "RED" if sucesso is False
                else "UNVERIFIED"
            )
            if sucesso is False and not primeira_red:
                primeira_red = str(nome)
            linhas.append(
                f"[{estado_etapa:<5}] {_identificador(nome, 40):<40} "
                f"{float(etapa.get('duracao_ms') or 0):.1f} ms"
            )
        if primeira_red:
            linhas.append(f"PRIMEIRA FRONTEIRA RED: {_identificador(primeira_red, 48)}")
        resultado = (
            "CONFIRMED" if trace.get("sucesso") is True
            else "FAILED" if trace.get("sucesso") is False
            else "UNVERIFIED"
        )
        linhas.append(f"RESULT {resultado}")
        return self._resultado(comando, "trace", linhas)

    def _consultar_estado(self, comando: str, estado: Mapping[str, Any]) -> dict[str, Any]:
        alvo = comando.removeprefix("inspect ").strip()
        linhas = [f"INSPECT {alvo.upper()}"]
        mental = self._estado_mental(estado)
        if alvo == "pending":
            permitidos = (
                "id", "origem", "tipo", "acao", "dominio", "alvo",
                "referencia", "motivo", "status", "intencao", "foi_falada",
                "criada_em", "expira_em",
            )
            encontrou = False
            for rotulo, chave_estado in (
                ("CONVERSACIONAL", "pendencia_atual"),
                ("AÇÃO CANÔNICA", "pendencia_acao_canonica"),
            ):
                pendencia = mental.get(chave_estado)
                dados_pendencia = (
                    dict(pendencia) if isinstance(pendencia, Mapping) else {}
                )
                if not dados_pendencia:
                    continue
                encontrou = True
                linhas.append(f"-- {rotulo} --")
                try:
                    agora = float(self.clock())
                    criada_em = float(dados_pendencia.get("criada_em") or 0.0)
                    expira_em = float(dados_pendencia.get("expira_em") or 0.0)
                except (TypeError, ValueError):
                    agora = criada_em = expira_em = 0.0
                status = _identificador(
                    dados_pendencia.get("status") or "desconhecida", 40,
                ).upper()
                ciclo = "EXPIRADA" if expira_em and expira_em <= agora else status
                idade = (
                    f"{max(0.0, agora - criada_em):.1f}"
                    if criada_em and agora else "desconhecida"
                )
                ttl = (
                    f"{max(0.0, expira_em - agora):.1f}"
                    if expira_em and agora else "desconhecido"
                )
                confiabilidade = (
                    "ESTADO_CANONICO"
                    if dados_pendencia.get("id") and dados_pendencia.get("status")
                    else "INCOMPLETA"
                )
                linhas.append(
                    f"owner=mental.{chave_estado} idade_s={idade} "
                    f"ttl_restante_s={ttl} ciclo={ciclo} "
                    f"confiabilidade={confiabilidade}"
                )
                for chave in permitidos:
                    valor = dados_pendencia.get(chave)
                    if chave in dados_pendencia and (
                        isinstance(valor, (str, int, float, bool)) or valor is None
                    ):
                        linhas.append(
                            f"{chave:<28} {sanitizar_texto_dev(valor, 140)}"
                        )
            if not encontrou:
                linhas.append("Nenhuma pendência observada.")
            return self._resultado(comando, "inspect", linhas)
        if alvo == "context":
            turno_bruto = mental.get("turno_atual")
            turno = dict(turno_bruto) if isinstance(turno_bruto, Mapping) else {}
            try:
                ts = float(mental.get("ultima_entrada_ts") or 0.0)
                idade = f"{max(0.0, float(self.clock()) - ts):.1f}" if ts else "desconhecida"
            except (TypeError, ValueError):
                idade = "desconhecida"
            linhas.append(
                f"owner=mental.turno_atual idade_s={idade} "
                f"confiabilidade={'ESTADO_CANONICO' if turno else 'AUSENTE'}"
            )
            intencao = next((
                turno.get(chave) for chave in (
                    "intencao", "intent", "intencao_principal",
                ) if turno.get(chave)
            ), mental.get("ultima_intencao") or mental.get("ultima_acao_intent") or "NÃO OBSERVADA")
            if "autoriza_execucao" in turno:
                autorizacao = "SIM" if turno.get("autoriza_execucao") is True else "NÃO"
            else:
                autorizacao = "NÃO OBSERVADA"
            referencia = turno.get("referencia_resolvida")
            referencia = dict(referencia) if isinstance(referencia, Mapping) else {}
            alvo_resolvido = next((
                referencia.get(chave) for chave in (
                    "alvo", "referencia", "valor", "nome", "id",
                ) if referencia.get(chave)
            ), mental.get("ultima_acao_alvo") or "NÃO OBSERVADO")
            linhas.extend([
                f"INTENÇÃO RECONHECIDA: {sanitizar_texto_dev(intencao, 140)}",
                f"AUTORIZAÇÃO EXPLÍCITA: {autorizacao}",
                f"ALVO RESOLVIDO: {sanitizar_texto_dev(alvo_resolvido, 140)}",
            ])
            return self._resultado(comando, "inspect", linhas)
        if alvo in {"action last", "receipt last"}:
            objeto = mental.get("ultima_acao_contrato")
            dados = dict(objeto) if isinstance(objeto, Mapping) else {}
            try:
                ts = float(mental.get("ultima_acao_ts") or 0.0)
                idade = f"{max(0.0, float(self.clock()) - ts):.1f}" if ts else "desconhecida"
            except (TypeError, ValueError):
                idade = "desconhecida"
            linhas.append(
                f"owner=mental.ultima_acao_contrato idade_s={idade} "
                f"confiabilidade={'ESTADO_CANONICO' if dados else 'AUSENTE'}"
            )
            for chave in (
                "intent", "alvo", "status", "origem", "executou",
                "confirmado", "reexecutavel", "evidencia_confirmacao",
            ):
                valor = dados.get(chave)
                if chave in dados and (
                    isinstance(valor, (str, int, float, bool)) or valor is None
                ):
                    linhas.append(f"{chave:<28} {sanitizar_texto_dev(valor, 140)}")
            executou = dados.get("executou") is True
            linhas.append(f"EXECUTOR CHAMADO: {'SIM' if executou else 'NÃO'}")
            if alvo == "receipt last":
                recebeu = isinstance(dados.get("confirmado"), bool) or bool(
                    str(dados.get("evidencia_confirmacao") or "").strip()
                )
                confirmou = dados.get("confirmado") is True
                sucesso_permitido = executou and confirmou
                linhas.extend([
                    f"RECEIPT RECEBIDO: {'SIM' if recebeu else 'NÃO'}",
                    f"EFEITO CONFIRMADO: {'SIM' if confirmou else 'NÃO'}",
                    "RESPOSTA DE SUCESSO PERMITIDA: "
                    f"{'SIM' if sucesso_permitido else 'NÃO'}",
                ])
            return self._resultado(comando, "inspect", linhas)
        if alvo == "memory used":
            memoria_bruta = estado.get("memoria_conversa")
            memoria = (
                dict(memoria_bruta) if isinstance(memoria_bruta, Mapping) else {}
            )
            for chave, tipo in (
                ("messages", "CONTEXTO_TEMPORÁRIO"),
                ("memoria_fatos", "MEMÓRIA_DURÁVEL"),
                ("memoria_eventos", "MEMÓRIA_DURÁVEL"),
            ):
                itens = memoria.get(chave)
                quantidade = len(itens) if isinstance(itens, (list, tuple)) else 0
                uso = "DISPONÍVEL_AO_PROMPT" if chave == "messages" else "NAO_PROVADO"
                linhas.append(
                    f"owner=memoria_conversa.{chave} tipo={tipo} itens={quantidade} "
                    f"uso_no_turno={uso}"
                )
            fundamentacao_bruta = mental.get("fundamentacao_factual_turno")
            fundamentacao = (
                dict(fundamentacao_bruta)
                if isinstance(fundamentacao_bruta, Mapping) else {}
            )
            if fundamentacao:
                try:
                    ts = float(fundamentacao.get("ts") or 0.0)
                    idade = f"{max(0.0, float(self.clock()) - ts):.1f}" if ts else "desconhecida"
                except (TypeError, ValueError):
                    idade = "desconhecida"
                confiavel = (
                    fundamentacao.get("confiavel") is True
                    and fundamentacao.get("evidencia_dentro_validade") is not False
                )
                linhas.append(
                    "owner=mental.fundamentacao_factual_turno "
                    f"fonte={_identificador(fundamentacao.get('fonte') or 'ausente', 80)} "
                    f"idade_s={idade} confiabilidade="
                    f"{'CONFIRMADA' if confiavel else 'NÃO_CONFIRMADA'}"
                )
            linhas.append(
                "Conteúdo omitido: o inspetor expõe proveniência e contagens, não dados pessoais."
            )
            return self._resultado(comando, "inspect", linhas)
        if alvo.startswith("event "):
            evento_id = alvo.removeprefix("event ").strip()
            with self._lock:
                evento = next((
                    dict(item) for item in self._eventos
                    if str(item.get("id") or "").casefold() == evento_id
                ), {})
            if not evento:
                return self._resultado(
                    comando, "inspect", linhas + ["Evento não encontrado."], ok=False,
                )
            try:
                idade = max(
                    0.0, float(self.clock()) - float(evento.get("timestamp") or 0.0),
                )
            except (TypeError, ValueError):
                idade = 0.0
            linhas.append(
                f"owner=dev_console.events idade_s={idade:.1f} "
                "confiabilidade=EVENTO_RETIDO"
            )
            for chave in (
                "id", "timestamp", "level", "category", "event", "trace_id",
                "message", "source", "depth", "duration_ms",
            ):
                if chave in evento:
                    linhas.append(
                        f"{chave:<28} {sanitizar_texto_dev(evento[chave], 300)}"
                    )
            return self._resultado(comando, "inspect", linhas)
        return self._resultado(
            comando, "inspect", ["Inspeção indisponível ou em manutenção."], ok=False,
        )


class EspelhoStreamDev:
    """Espelha uma stream sem mudar sua saída e publica somente linhas completas."""

    def __init__(
        self,
        original: TextIO | None,
        runtime: DevConsoleRuntime,
        *,
        origem: str,
    ) -> None:
        self.original = original
        self.runtime = runtime
        self.origem = origem if origem in {"stdout", "stderr"} else "stdout"
        self._lock = threading.RLock()
        self._buffers: dict[int, str] = {}

    def write(self, texto: str) -> int:
        dado = str(texto or "")
        with self._lock:
            escrever = getattr(self.original, "write", None)
            if callable(escrever):
                try:
                    escrito = escrever(dado)
                except (BrokenPipeError, OSError, ValueError):
                    escrito = len(dado)
            else:
                escrito = len(dado)
            thread_id = threading.get_ident()
            acumulado = self._buffers.get(thread_id, "") + dado.replace("\r\n", "\n")
            partes = acumulado.split("\n")
            self._buffers[thread_id] = partes.pop()[-4_096:]
            for linha in partes:
                self.runtime.registrar_linha(linha, origem=self.origem)
            return int(escrito if escrito is not None else len(dado))

    def flush(self) -> None:
        flush = getattr(self.original, "flush", None)
        if callable(flush):
            try:
                flush()
            except (BrokenPipeError, OSError, ValueError):
                pass

    def isatty(self) -> bool:
        return bool(getattr(self.original, "isatty", lambda: False)())

    @property
    def encoding(self) -> str:
        return str(getattr(self.original, "encoding", "utf-8") or "utf-8")

    @property
    def errors(self) -> str:
        return str(getattr(self.original, "errors", "replace") or "replace")

    def fileno(self) -> int:
        fileno = getattr(self.original, "fileno", None)
        if not callable(fileno):
            raise OSError("stream original indisponível")
        return int(fileno())

    def __getattr__(self, nome: str) -> Any:
        return getattr(self.original, nome)


def instalar_espelhos_stream_dev(
    runtime: DevConsoleRuntime,
) -> tuple[EspelhoStreamDev, EspelhoStreamDev]:
    """Instala uma única camada e conserva a stream anterior em ``original``."""
    if isinstance(sys.stdout, EspelhoStreamDev) and isinstance(sys.stderr, EspelhoStreamDev):
        return sys.stdout, sys.stderr
    saida = EspelhoStreamDev(sys.stdout, runtime, origem="stdout")
    erro = EspelhoStreamDev(sys.stderr, runtime, origem="stderr")
    sys.stdout, sys.stderr = saida, erro
    return saida, erro


def criar_dev_console_runtime(**kwargs: Any) -> DevConsoleRuntime:
    return DevConsoleRuntime(**kwargs)


__all__ = [
    "DevConsoleRuntime",
    "EspelhoStreamDev",
    "criar_dev_console_runtime",
    "instalar_espelhos_stream_dev",
    "sanitizar_texto_dev",
]
