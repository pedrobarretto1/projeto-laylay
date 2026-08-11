"""Métricas e eventos técnicos sanitizados para o diagnóstico da mente."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Callable, Dict, Iterable

from mente_laylay.memoria_mental.implantacao_desempenho import (
    sinal_regressao_por_falha,
)


CLASSES_FALHA_TECNICA = frozenset({"esperada", "degradacao", "defeito"})
IMPACTOS_FALHA_TECNICA = frozenset({"nenhum", "turno", "comando", "fala", "servico"})

# Limites de diagnóstico, não timeouts. Excedê-los nunca cancela uma ação;
# apenas torna a degradação mensurável para uma otimização posterior segura.
ORCAMENTOS_LATENCIA_MS = {
    "startup_chat_pronto": 3_000.0,
    "startup_servicos_completos": 10_000.0,
    "interpretacao": 80.0,
    "interpretação": 80.0,
    "dispatcher": 120.0,
    "execucao": 1_500.0,
    "execução": 1_500.0,
    "preparacao_prompt": 120.0,
    "llm_http": 20_000.0,
    "llm_resposta_principal": 20_000.0,
    "visao_jogo": 8_000.0,
    "tts_sintese": 8_000.0,
    "tts_sintese_primeiro_trecho": 2_000.0,
    "tts_fila": 1_000.0,
    "tts_texto_visivel": 1_000.0,
    "tts_primeiro_audio": 10_000.0,
    "tts_reproducao": 20_000.0,
    "tts_total": 20_000.0,
    "turno_total": 25_000.0,
}

LIMITE_AMOSTRAS_PERCENTIL = 128
LIMITE_TRACES_TURNO = 40


def _codigo(valor: Any, padrao: str = "sem_detalhe", limite: int = 96) -> str:
    texto = str(valor or "").strip().casefold()
    texto = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[^a-z0-9áàâãéêíóôõúç_.: -]+", "", texto)
    texto = re.sub(r"\s+", "_", texto).strip("_.:-")
    return (texto or padrao)[:limite]


def _identificador_tecnico(valor: Any, padrao: str = "desconhecido", limite: int = 64) -> str:
    """Aceita somente identificadores; frases, caminhos e URLs nunca viram telemetria."""
    texto = str(valor or "").strip()
    if (
        not texto
        or re.search(r"https?://|\\|\s|(?:api[_-]?key|token|senha|secret)", texto, re.IGNORECASE)
        or not re.fullmatch(r"[A-Za-z0-9À-ÿ_.:/-]+", texto)
    ):
        return padrao
    return texto.casefold()[:limite]


def _percentil(amostras: Iterable[Any], percentual: int) -> float:
    valores = sorted(float(item) for item in amostras)
    if not valores:
        return 0.0
    posicao = max(0, min(len(valores) - 1, ((percentual * len(valores) + 99) // 100) - 1))
    return round(valores[posicao], 2)


def _inteiro_limitado(valor: Any, teto: int) -> int:
    try:
        return max(0, min(int(valor), teto))
    except (TypeError, ValueError):
        return 0


def _acumular_metrica(
    anterior: Dict[str, Any],
    *,
    duracao: float,
    sucesso: bool,
    orcamento: float,
) -> Dict[str, Any]:
    atual = dict(anterior or {})
    amostras = int(atual.get("amostras") or 0) + 1
    media_anterior = float(atual.get("media_ms") or 0.0)
    janela = [
        max(0.0, min(float(item), 600000.0))
        for item in list(atual.get("_janela_ms") or [])[-(LIMITE_AMOSTRAS_PERCENTIL - 1):]
        if isinstance(item, (int, float))
    ]
    janela.append(duracao)
    excedeu = bool(orcamento and duracao > orcamento)
    atual.update(
        ultimo_ms=round(duracao, 2),
        media_ms=round(media_anterior + (duracao - media_anterior) / amostras, 2),
        p50_ms=_percentil(janela, 50),
        p95_ms=_percentil(janela, 95),
        max_ms=round(max(float(atual.get("max_ms") or 0.0), duracao), 2),
        amostras=amostras,
        falhas=int(atual.get("falhas") or 0) + (0 if sucesso else 1),
        orcamento_ms=orcamento,
        excedeu_orcamento=excedeu,
        excessos=int(atual.get("excessos") or 0) + (1 if excedeu else 0),
        _janela_ms=janela,
    )
    return atual


def classificar_falha_tecnica(
    componente: Any,
    codigo: Any,
    *,
    erro: BaseException | type[BaseException] | None = None,
    classe: str = "",
    impacto: str = "",
    fallback: str = "",
) -> Dict[str, str]:
    """Classifica telemetria sem inspecionar nem persistir a mensagem do erro."""
    componente_limpo = _codigo(componente, "desconhecido", 64)
    codigo_limpo = _codigo(codigo, "falha", 80)
    tipo = ""
    if isinstance(erro, BaseException):
        tipo = _codigo(type(erro).__name__, "", 48)
    elif isinstance(erro, type) and issubclass(erro, BaseException):
        tipo = _codigo(erro.__name__, "", 48)

    classe_limpa = _codigo(classe, "", 24)
    if classe_limpa not in CLASSES_FALHA_TECNICA:
        assinatura = f"{componente_limpo} {codigo_limpo} {tipo}"
        if any(token in assinatura for token in (
            "cancel", "interrompid", "descartad", "bloquead", "adiad", "recusad",
        )):
            classe_limpa = "esperada"
        elif any(token in assinatura for token in (
            "timeout", "readtimeout", "connection", "conexao", "indispon",
            "ocupad", "temporari", "falha_audio", "queda_background",
            "servico", "api", "rede",
        )):
            classe_limpa = "degradacao"
        else:
            classe_limpa = "defeito"

    impacto_limpo = _codigo(impacto, "", 24)
    if impacto_limpo not in IMPACTOS_FALHA_TECNICA:
        if any(token in componente_limpo for token in ("tts", "voz", "audio", "fala")):
            impacto_limpo = "fala"
        elif any(token in componente_limpo for token in ("llm", "turno", "interpret")):
            impacto_limpo = "turno"
        elif any(token in componente_limpo for token in ("exec", "dispatcher", "arquivo", "iot")):
            impacto_limpo = "comando"
        else:
            impacto_limpo = "servico"

    return {
        "classe": classe_limpa,
        "impacto": impacto_limpo,
        "fallback": _codigo(fallback, "nenhum", 64),
    }


def relatar_falha_opcional(
    registrar: Callable[..., Any] | None,
    componente: str,
    codigo: str,
    *,
    erro: BaseException | type[BaseException] | None = None,
    classe: str = "",
    impacto: str = "",
    fallback: str = "",
    dominio: str = "",
    fase: str = "",
    turno_id: Any = None,
) -> bool:
    """Usa um relator opcional sem deixar a telemetria mascarar a falha original."""
    if not callable(registrar):
        return False
    try:
        registrar(
            componente,
            codigo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
            dominio=dominio,
            fase=fase,
            turno_id=turno_id,
        )
        return True
    except Exception:
        # Esta é a última fronteira de proteção: observabilidade defeituosa
        # nunca pode substituir o resultado que ela tentava registrar.
        return False


class ObservabilidadeMenteRuntime:
    """Atualiza somente telemetria técnica curta no domínio mental."""

    def __init__(
        self,
        *,
        estado_getter: Callable[[str, Any], Any],
        estado_setter: Callable[..., Any],
        clock: Callable[[], float] = time.time,
        limite_eventos: int = 20,
        log: Callable[[str], Any] | None = None,
        janela_repeticao_s: float = 30.0,
        observar_implantacao: Callable[[str], Any] | None = None,
    ) -> None:
        self.estado_getter = estado_getter
        self.estado_setter = estado_setter
        self.clock = clock
        self.limite_eventos = max(5, int(limite_eventos))
        self.log = log
        self.janela_repeticao_s = max(1.0, float(janela_repeticao_s))
        self.observar_implantacao = observar_implantacao
        self._lock = threading.RLock()
        self._falhas_auxiliares: Dict[tuple[str, ...], Dict[str, Any]] = {}
        self._trace_local = threading.local()

    def _obter(self, chave: str, padrao: Any) -> Any:
        try:
            return self.estado_getter(chave, padrao)
        except Exception:
            return padrao

    def _atualizar(self, **campos: Any) -> None:
        try:
            self.estado_setter(**campos)
        except Exception:
            pass

    def iniciar_trace_turno(
        self,
        turno_id: Any,
        *,
        origem: str = "desconhecida",
        rota: str = "roteamento",
    ) -> Dict[str, Any]:
        trace = {
            "turno_id": _identificador_tecnico(turno_id, "turno_desconhecido", 72),
            "origem": _identificador_tecnico(origem, "desconhecida", 32),
            "rota": _identificador_tecnico(rota, "roteamento", 48),
            "fase": "entrada",
            "backend": "desconhecido",
            "modelo": "desconhecido",
            "tipo_chamada": "nenhuma",
            "tamanho_prompt_chars": 0,
            "limite_saida_tokens": 0,
        }
        self._trace_local.atual = dict(trace)
        with self._lock:
            traces = list(self._obter("diagnostico_traces_turno", []) or [])
            traces.append({
                **trace,
                "etapas": {},
                "chamadas_llm": 0,
                "finalizado": False,
                "sucesso": None,
                "ts_inicio": float(self.clock()),
                "ts_atualizacao": float(self.clock()),
            })
            self._atualizar(diagnostico_traces_turno=traces[-LIMITE_TRACES_TURNO:])
        return dict(trace)

    def atualizar_trace_turno(self, turno_id: Any = None, **campos: Any) -> Dict[str, Any]:
        atual = dict(getattr(self._trace_local, "atual", {}) or {})
        id_limpo = _identificador_tecnico(
            turno_id or atual.get("turno_id"), "turno_desconhecido", 72,
        )
        permitidos = {
            "origem": ("desconhecida", 32),
            "rota": ("roteamento", 48),
            "backend": ("desconhecido", 48),
            "modelo": ("desconhecido", 80),
            "tipo_chamada": ("nenhuma", 48),
            "fase": ("entrada", 48),
        }
        atual["turno_id"] = id_limpo
        for chave, (padrao, limite) in permitidos.items():
            if chave in campos:
                atual[chave] = _identificador_tecnico(campos[chave], padrao, limite)
        for chave, teto in {
            "tamanho_prompt_chars": 2_000_000,
            "limite_saida_tokens": 100_000,
        }.items():
            if chave in campos:
                try:
                    atual[chave] = max(0, min(int(campos[chave]), teto))
                except (TypeError, ValueError):
                    atual[chave] = 0
        self._trace_local.atual = dict(atual)
        with self._lock:
            traces = list(self._obter("diagnostico_traces_turno", []) or [])
            for indice in range(len(traces) - 1, -1, -1):
                if str(traces[indice].get("turno_id") or "") == id_limpo:
                    traces[indice] = {
                        **dict(traces[indice]),
                        **atual,
                        "ts_atualizacao": float(self.clock()),
                    }
                    break
            self._atualizar(diagnostico_traces_turno=traces[-LIMITE_TRACES_TURNO:])
        return dict(atual)

    def obter_trace_corrente(self) -> Dict[str, Any]:
        return dict(getattr(self._trace_local, "atual", {}) or {})

    def finalizar_trace_turno(self, turno_id: Any = None, *, sucesso: bool = True) -> None:
        atual = self.atualizar_trace_turno(turno_id)
        id_limpo = str(atual.get("turno_id") or "")
        with self._lock:
            traces = list(self._obter("diagnostico_traces_turno", []) or [])
            for indice in range(len(traces) - 1, -1, -1):
                if str(traces[indice].get("turno_id") or "") == id_limpo:
                    traces[indice] = {
                        **dict(traces[indice]),
                        "finalizado": True,
                        "sucesso": bool(sucesso),
                        "ts_atualizacao": float(self.clock()),
                    }
                    break
            self._atualizar(diagnostico_traces_turno=traces[-LIMITE_TRACES_TURNO:])
        self._trace_local.atual = {}

    def registrar_metrica(
        self,
        componente: str,
        duracao_ms: float,
        sucesso: bool = True,
        **contexto: Any,
    ) -> Dict[str, Any]:
        nome = _codigo(componente, "desconhecido", 64)
        try:
            duracao = max(0.0, min(float(duracao_ms), 600000.0))
        except (TypeError, ValueError):
            duracao = 0.0
        with self._lock:
            trace_atual = dict(getattr(self._trace_local, "atual", {}) or {})
            contexto_trace = {
                **trace_atual,
                **{
                    chave: valor
                    for chave, valor in contexto.items()
                    if chave in {
                        "turno_id", "origem", "rota", "fase", "backend", "modelo", "tipo_chamada",
                        "tamanho_prompt_chars", "limite_saida_tokens",
                    }
                },
            }
            turno_id = _identificador_tecnico(
                contexto_trace.get("turno_id"), "", 72,
            )
            rota = _identificador_tecnico(contexto_trace.get("rota"), "", 48)
            backend = _identificador_tecnico(
                contexto_trace.get("backend"), "desconhecido", 48,
            )
            modelo = _identificador_tecnico(
                contexto_trace.get("modelo"), "desconhecido", 80,
            )
            tipo_chamada = _identificador_tecnico(
                contexto_trace.get("tipo_chamada"), "nenhuma", 48,
            )
            fase = _identificador_tecnico(
                contexto_trace.get("fase"), "entrada", 48,
            )
            if turno_id:
                self._trace_local.atual = {
                    **trace_atual,
                    "turno_id": turno_id,
                    "origem": _identificador_tecnico(
                        contexto_trace.get("origem"), "desconhecida", 32,
                    ),
                    "rota": rota or "roteamento",
                    "fase": fase,
                    "backend": backend,
                    "modelo": modelo,
                    "tipo_chamada": tipo_chamada,
                    "tamanho_prompt_chars": _inteiro_limitado(
                        contexto_trace.get("tamanho_prompt_chars"), 2_000_000,
                    ),
                    "limite_saida_tokens": _inteiro_limitado(
                        contexto_trace.get("limite_saida_tokens"), 100_000,
                    ),
                }
            metricas = dict(self._obter("diagnostico_metricas", {}) or {})
            orcamento = float(ORCAMENTOS_LATENCIA_MS.get(nome) or 0.0)
            atual = _acumular_metrica(
                dict(metricas.get(nome) or {}),
                duracao=duracao,
                sucesso=sucesso,
                orcamento=orcamento,
            )
            atual["ts"] = float(self.clock())
            metricas[nome] = atual

            metricas_rotas = dict(self._obter("diagnostico_metricas_rotas", {}) or {})
            if rota:
                por_rota = dict(metricas_rotas.get(rota) or {})
                metrica_rota = _acumular_metrica(
                    dict(por_rota.get(nome) or {}),
                    duracao=duracao,
                    sucesso=sucesso,
                    orcamento=orcamento,
                )
                metrica_rota["ts"] = float(self.clock())
                por_rota[nome] = metrica_rota
                metricas_rotas[rota] = por_rota

            traces = list(self._obter("diagnostico_traces_turno", []) or [])
            if turno_id:
                for indice in range(len(traces) - 1, -1, -1):
                    trace = dict(traces[indice] or {})
                    if str(trace.get("turno_id") or "") != turno_id:
                        continue
                    etapas = dict(trace.get("etapas") or {})
                    etapas[nome] = {
                        "duracao_ms": round(duracao, 2),
                        "sucesso": bool(sucesso),
                    }
                    trace.update(
                        rota=rota or str(trace.get("rota") or "roteamento"),
                        fase=fase,
                        backend=backend,
                        modelo=modelo,
                        tipo_chamada=tipo_chamada,
                        tamanho_prompt_chars=_inteiro_limitado(
                            contexto_trace.get("tamanho_prompt_chars"), 2_000_000,
                        ),
                        limite_saida_tokens=_inteiro_limitado(
                            contexto_trace.get("limite_saida_tokens"), 100_000,
                        ),
                        etapas=etapas,
                        ts_atualizacao=float(self.clock()),
                    )
                    if nome == "llm_http":
                        trace["chamadas_llm"] = int(trace.get("chamadas_llm") or 0) + 1
                        chamadas_por_tipo = dict(trace.get("chamadas_llm_por_tipo") or {})
                        chamadas_por_tipo[tipo_chamada] = (
                            int(chamadas_por_tipo.get(tipo_chamada) or 0) + 1
                        )
                        trace["chamadas_llm_por_tipo"] = chamadas_por_tipo
                    traces[indice] = trace
                    break
            self._atualizar(
                diagnostico_metricas=metricas,
                diagnostico_metricas_rotas=metricas_rotas,
                diagnostico_traces_turno=traces[-LIMITE_TRACES_TURNO:],
            )
            return dict(atual)

    def registrar_tamanho_prompt(self, origem: str, caracteres: int) -> Dict[str, Any]:
        """Registra somente contagens por origem; conteúdo do prompt nunca é persistido."""
        nome = _codigo(origem, "desconhecida", 64)
        try:
            tamanho = max(0, min(int(caracteres), 2_000_000))
        except (TypeError, ValueError):
            tamanho = 0
        with self._lock:
            tamanhos = dict(self._obter("diagnostico_prompts", {}) or {})
            atual = dict(tamanhos.get(nome) or {})
            amostras = int(atual.get("amostras") or 0) + 1
            media_anterior = float(atual.get("media_chars") or 0.0)
            atual.update(
                ultimo_chars=tamanho,
                media_chars=round(
                    media_anterior + (tamanho - media_anterior) / amostras, 2,
                ),
                max_chars=max(int(atual.get("max_chars") or 0), tamanho),
                amostras=amostras,
                ts=float(self.clock()),
            )
            tamanhos[nome] = atual
            self._atualizar(diagnostico_prompts=tamanhos)
            return dict(atual)

    def registrar_orcamento_prompt(
        self,
        *,
        etapa: str,
        brutos: int,
        selecionados: int,
        truncados: int,
        enviados: int,
        injetados: int = 0,
    ) -> Dict[str, Any]:
        """Registra o fechamento numérico do prompt sem guardar seu conteúdo."""
        def _inteiro(valor: Any) -> int:
            try:
                return max(0, min(int(valor), 2_000_000))
            except (TypeError, ValueError):
                return 0

        registro: Dict[str, Any] = {
            "etapa": _codigo(etapa, "desconhecida", 32),
            "brutos": _inteiro(brutos),
            "selecionados": _inteiro(selecionados),
            "truncados": _inteiro(truncados),
            "injetados": _inteiro(injetados),
            "enviados": _inteiro(enviados),
            "ts": float(self.clock()),
        }
        registro["fecha_selecao"] = (
            registro["brutos"]
            == registro["selecionados"] + registro["truncados"]
        )
        registro["fecha_envio"] = (
            registro["enviados"]
            == registro["selecionados"] + registro["injetados"]
        )
        with self._lock:
            atual = dict(self._obter("diagnostico_orcamento_prompt", {}) or {})
            etapas = dict(atual.get("etapas") or {})
            etapas[registro["etapa"]] = dict(registro)
            atual.update(
                etapas=etapas,
                ultima=dict(registro),
                inconsistencias=int(atual.get("inconsistencias") or 0)
                + (0 if registro["fecha_selecao"] and registro["fecha_envio"] else 1),
            )
            self._atualizar(diagnostico_orcamento_prompt=atual)
        return dict(registro)

    def registrar_falha(
        self,
        componente: str,
        codigo: str,
        *,
        erro: BaseException | type[BaseException] | None = None,
        classe: str = "",
        impacto: str = "",
        fallback: str = "",
        dominio: str = "",
        fase: str = "",
        turno_id: Any = None,
    ) -> Dict[str, Any]:
        tipo = ""
        if isinstance(erro, BaseException):
            tipo = type(erro).__name__
        elif isinstance(erro, type) and issubclass(erro, BaseException):
            tipo = erro.__name__
        classificacao = classificar_falha_tecnica(
            componente,
            codigo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
        )
        evento = {
            "componente": _codigo(componente, "desconhecido", 64),
            "codigo": _codigo(codigo, "falha", 80),
            "tipo": _codigo(tipo, "", 48) if tipo else "",
            **classificacao,
            "ts": float(self.clock()),
        }
        if dominio:
            evento["dominio"] = _codigo(dominio, "desconhecido", 48)
        if fase:
            evento["fase"] = _codigo(fase, "desconhecida", 48)
        if turno_id is not None and str(turno_id).strip():
            evento["turno_id"] = _codigo(turno_id, "desconhecido", 48)
        with self._lock:
            eventos = list(self._obter("diagnostico_falhas", []) or [])
            eventos.append(evento)
            self._atualizar(diagnostico_falhas=eventos[-self.limite_eventos:])
        sinal = sinal_regressao_por_falha(codigo, fallback)
        if (
            sinal
            and classificacao["classe"] != "esperada"
            and callable(self.observar_implantacao)
        ):
            try:
                self.observar_implantacao(sinal)
            except Exception:
                pass
        return dict(evento)

    def relatar_falha(
        self,
        componente: str,
        codigo: str,
        *,
        erro: BaseException | type[BaseException] | None = None,
        classe: str = "",
        impacto: str = "",
        fallback: str = "",
        dominio: str = "",
        fase: str = "",
        turno_id: Any = None,
    ) -> Dict[str, Any]:
        """Registra uma falha operacional sem repetir o mesmo aviso em cascata.

        Mensagens e caminhos do erro nunca entram no diagnóstico nem no terminal;
        apenas componente, código estável e tipo técnico são preservados.
        """
        componente_limpo = _codigo(componente, "desconhecido", 64)
        codigo_limpo = _codigo(codigo, "falha", 80)
        if isinstance(erro, BaseException):
            tipo = _codigo(type(erro).__name__, "", 48)
        elif isinstance(erro, type) and issubclass(erro, BaseException):
            tipo = _codigo(erro.__name__, "", 48)
        else:
            tipo = ""
        classificacao = classificar_falha_tecnica(
            componente_limpo,
            codigo_limpo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
        )
        agora = float(self.clock())
        dominio_limpo = _codigo(dominio, "", 48) if dominio else ""
        fase_limpa = _codigo(fase, "", 48) if fase else ""
        turno_limpo = _codigo(turno_id, "", 48) if turno_id is not None else ""
        metadados = {}
        if dominio_limpo:
            metadados["dominio"] = dominio_limpo
        if fase_limpa:
            metadados["fase"] = fase_limpa
        if turno_limpo:
            metadados["turno_id"] = turno_limpo
        chave = (componente_limpo, codigo_limpo, tipo, dominio_limpo, fase_limpa)
        with self._lock:
            anterior = dict(self._falhas_auxiliares.get(chave) or {})
            if anterior and agora - float(anterior.get("ts") or 0.0) < self.janela_repeticao_s:
                anterior["suprimidas"] = int(anterior.get("suprimidas") or 0) + 1
                self._falhas_auxiliares[chave] = anterior
                sinal = sinal_regressao_por_falha(codigo_limpo, fallback)
                if (
                    sinal
                    and classificacao["classe"] != "esperada"
                    and callable(self.observar_implantacao)
                ):
                    try:
                        self.observar_implantacao(sinal)
                    except Exception:
                        pass
                return {
                    "registrada": False,
                    "suprimidas": anterior["suprimidas"],
                    "componente": componente_limpo,
                    "codigo": codigo_limpo,
                    "tipo": tipo,
                    **classificacao,
                    **metadados,
                }
            suprimidas = int(anterior.get("suprimidas") or 0)
            self._falhas_auxiliares[chave] = {"ts": agora, "suprimidas": 0}

        evento = self.registrar_falha(
            componente_limpo,
            codigo_limpo,
            erro=erro,
            **classificacao,
            **metadados,
        )
        if callable(self.log):
            repeticao = f" | {suprimidas} repetição(ões) anterior(es) suprimida(s)" if suprimidas else ""
            tipo_texto = f" | tipo={tipo}" if tipo else ""
            try:
                self.log(
                    f"⚠️ [MENTE:FALHA] {componente_limpo}:{codigo_limpo}"
                    f" | classe={classificacao['classe']}"
                    f" | impacto={classificacao['impacto']}"
                    f"{tipo_texto}{repeticao}"
                )
            except Exception:
                # A observabilidade nunca pode derrubar o fluxo que está protegendo.
                pass
        return {**evento, "registrada": True, "suprimidas": suprimidas}

    def registrar_decisao(
        self,
        componente: str,
        acao: str,
        motivos: Iterable[Any] = (),
        *,
        categoria: str = "",
    ) -> Dict[str, Any]:
        evento = {
            "componente": _codigo(componente, "desconhecido", 64),
            "acao": _codigo(acao, "indefinida", 48),
            "categoria": _codigo(categoria, "", 64) if categoria else "",
            "motivos": [_codigo(item, limite=96) for item in list(motivos or ())[:4]],
            "ts": float(self.clock()),
        }
        with self._lock:
            eventos = list(self._obter("diagnostico_decisoes", []) or [])
            eventos.append(evento)
            self._atualizar(diagnostico_decisoes=eventos[-self.limite_eventos:])
        return dict(evento)

    def registrar_evento_servico(
        self,
        nome: str,
        estado: str,
        *,
        tentativa: int = 0,
        atraso_s: float = 0.0,
        fallback: str = "",
    ) -> Dict[str, Any]:
        """Mantém um retrato curto e sanitizado do ciclo de vida dos serviços."""
        nome_limpo = _codigo(nome, "desconhecido", 64)
        estado_limpo = _codigo(estado, "desconhecido", 32)
        try:
            tentativa_limpa = max(0, min(int(tentativa), 100000))
        except (TypeError, ValueError):
            tentativa_limpa = 0
        try:
            atraso_limpo = round(max(0.0, min(float(atraso_s), 3600.0)), 2)
        except (TypeError, ValueError):
            atraso_limpo = 0.0
        with self._lock:
            servicos = dict(self._obter("diagnostico_servicos", {}) or {})
            anterior = dict(servicos.get(nome_limpo) or {})
            registro = {
                "nome": nome_limpo,
                "estado": estado_limpo,
                "tentativa": tentativa_limpa,
                "atraso_s": atraso_limpo,
                "fallback": _codigo(fallback, "nenhum", 64),
                "quedas": int(anterior.get("quedas") or 0) + (1 if estado_limpo == "queda" else 0),
                "reinicios": int(anterior.get("reinicios") or 0) + (1 if estado_limpo == "reiniciando" else 0),
                "falhas_inicializacao": int(anterior.get("falhas_inicializacao") or 0)
                + (1 if estado_limpo == "falha_inicializacao" else 0),
                "orfaos": int(anterior.get("orfaos") or 0)
                + (1 if estado_limpo == "orfao" else 0),
                "ts": float(self.clock()),
            }
            servicos[nome_limpo] = registro
            self._atualizar(diagnostico_servicos=servicos)
            return dict(registro)


def criar_observabilidade_mente_runtime(**kwargs: Any) -> ObservabilidadeMenteRuntime:
    return ObservabilidadeMenteRuntime(**kwargs)
