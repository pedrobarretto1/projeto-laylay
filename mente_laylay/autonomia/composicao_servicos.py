"""Composição declarativa dos serviços usados pela entrada principal da Laylay."""

from __future__ import annotations

from functools import partial
import inspect
import time
from typing import Any, Callable, Mapping, Sequence


class ComposicaoServicosLaylayRuntime:
    """Monta inicialização e encerramento sem conhecer os estados da mente."""

    def __init__(
        self,
        *,
        gerenciador: Any,
        etapas: Mapping[str, Callable[[], Any]],
        etapas_diferidas: Mapping[str, Callable[[], Any]] | None = None,
        threads: Mapping[str, Callable[[], Any]],
        threads_com_parada: Mapping[str, Callable[..., Any]] | None = None,
        threads_com_espera: Mapping[str, Callable[..., Any]] | None = None,
        hotkeys: Sequence[tuple[str, Callable[[], Any]]] = (),
        encerramento: Sequence[tuple[str, Callable[[], Any]]] = (),
        registrar_falha: Callable[..., Any] | None = None,
        registrar_metrica: Callable[..., Any] | None = None,
        log: Callable[[str], Any] = print,
        monotonic: Callable[[], float] = time.monotonic,
        timeout_encerramento_s: float = 1.5,
        inicializacao_diferida: bool = True,
    ) -> None:
        self.gerenciador = gerenciador
        self.etapas = dict(etapas or {})
        self.etapas_diferidas = dict(etapas_diferidas or {})
        self.threads = dict(threads or {})
        self.threads_com_parada = dict(threads_com_parada or {})
        self.threads_com_espera = dict(threads_com_espera or {})
        self.hotkeys = tuple(hotkeys or ())
        self.encerramento = tuple(encerramento or ())
        self.registrar_falha = registrar_falha
        self.registrar_metrica = registrar_metrica
        self.log = log
        self.monotonic = monotonic
        self.timeout_encerramento_s = max(0.0, float(timeout_encerramento_s))
        self.inicializacao_diferida = bool(inicializacao_diferida)
        self._prontidao = {
            "fase": "nao_iniciada",
            "chat_pronto_ms": 0.0,
            "servicos_completos_ms": 0.0,
            "diferidas": {},
        }

    def _relatar(self, componente: str, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha(componente, codigo, erro=erro)

    def catalogo_threads(self) -> dict[str, Callable[[], Any]]:
        catalogo = dict(self.threads)
        for nome, target in self.threads_com_parada.items():
            catalogo[nome] = partial(
                target,
                deve_parar=self.gerenciador.deve_parar,
            )
        for nome, target in self.threads_com_espera.items():
            catalogo[nome] = partial(
                target,
                deve_parar=self.gerenciador.deve_parar,
                aguardar_fn=self.gerenciador.aguardar,
            )
        return catalogo

    def registrar_hotkeys(self) -> dict[str, bool]:
        resultados: dict[str, bool] = {}
        for nome, registrar in self.hotkeys:
            try:
                retorno = registrar()
                resultados[str(nome)] = retorno is not False
            except Exception as erro:
                resultados[str(nome)] = False
                self.log(
                    f"⚠️ [INICIALIZAÇÃO] hotkey {nome} indisponível: "
                    f"{type(erro).__name__}"
                )
                self._relatar("inicializacao", f"hotkey_{nome}", erro)
        return resultados

    def iniciar(self, orquestrador: Any) -> dict[str, dict[str, bool]]:
        inicio = self.monotonic()
        etapas_imediatas = dict(self.etapas)
        etapas_diferidas = dict(self.etapas_diferidas)
        if not self.inicializacao_diferida:
            etapas_imediatas.update(etapas_diferidas)
            etapas_diferidas = {}
        resultado = orquestrador.iniciar(
            etapas=etapas_imediatas,
            threads=self.catalogo_threads(),
            hotkeys=self.registrar_hotkeys,
        )
        chat_pronto_ms = max(0.0, (self.monotonic() - inicio) * 1000.0)
        self._prontidao = {
            "fase": "chat_pronto",
            "chat_pronto_ms": chat_pronto_ms,
            "servicos_completos_ms": 0.0,
            "diferidas": {},
        }
        self._registrar_metrica_startup(
            "startup_chat_pronto", chat_pronto_ms, True,
        )
        self.log(f"⚡ [INICIALIZAÇÃO] chat pronto em {chat_pronto_ms:.0f}ms")
        if not etapas_diferidas:
            self._marcar_servicos_completos(inicio, {})
            return resultado

        def concluir_etapas_diferidas() -> None:
            concluidas: dict[str, bool] = {}
            for descricao, target in etapas_diferidas.items():
                if bool(getattr(self.gerenciador, "deve_parar", lambda: False)()):
                    concluidas[descricao] = False
                    break
                parcial = orquestrador.executar_etapas({descricao: target})
                concluidas.update(parcial)
            self._marcar_servicos_completos(inicio, concluidas)

        agendada = bool(self.gerenciador.iniciar(
            "Laylay-Inicializacao-Diferida", concluir_etapas_diferidas,
        ))
        resultado["etapas_diferidas"] = {"agendada": agendada}
        if not agendada:
            self.log(
                "⚠️ [INICIALIZAÇÃO] fase de background indisponível; "
                "revertendo as etapas secundárias para o fluxo síncrono"
            )
            concluidas: dict[str, bool] = {}
            for descricao, target in etapas_diferidas.items():
                parcial = orquestrador.executar_etapas({descricao: target})
                concluidas.update(parcial)
            self._marcar_servicos_completos(inicio, concluidas)
            resultado["etapas_diferidas"]["revertida_sincrona"] = True
        return resultado

    def _registrar_metrica_startup(
        self, nome: str, duracao_ms: float, sucesso: bool,
    ) -> None:
        if not callable(self.registrar_metrica):
            return
        try:
            self.registrar_metrica(
                nome, duracao_ms, sucesso,
                rota="inicializacao", fase=self._prontidao.get("fase", "inicio"),
            )
        except TypeError:
            self.registrar_metrica(nome, duracao_ms, sucesso)

    def _marcar_servicos_completos(
        self, inicio: float, resultados: Mapping[str, bool],
    ) -> None:
        duracao_ms = max(0.0, (self.monotonic() - inicio) * 1000.0)
        sucesso = all(resultados.values()) if resultados else True
        self._prontidao = {
            **self._prontidao,
            "fase": "servicos_completos" if sucesso else "degradada",
            "servicos_completos_ms": duracao_ms,
            "diferidas": dict(resultados),
        }
        self._registrar_metrica_startup(
            "startup_servicos_completos", duracao_ms, sucesso,
        )
        self.log(
            "✅ [INICIALIZAÇÃO] serviços completos em "
            f"{duracao_ms:.0f}ms"
            if sucesso
            else "⚠️ [INICIALIZAÇÃO] serviços secundários degradados"
        )

    def estado_prontidao(self) -> dict[str, Any]:
        return {
            "fase": str(self._prontidao.get("fase") or "nao_iniciada"),
            "chat_pronto_ms": float(self._prontidao.get("chat_pronto_ms") or 0.0),
            "servicos_completos_ms": float(
                self._prontidao.get("servicos_completos_ms") or 0.0
            ),
            "diferidas": dict(self._prontidao.get("diferidas") or {}),
        }

    @staticmethod
    def _invocar_finalizador(finalizar: Callable[..., Any], restante_s: float) -> Any:
        try:
            assinatura = inspect.signature(finalizar)
            parametros = assinatura.parameters
            aceita_timeout = "timeout_s" in parametros or any(
                item.kind is inspect.Parameter.VAR_KEYWORD
                for item in parametros.values()
            )
        except (TypeError, ValueError):
            aceita_timeout = False
        if aceita_timeout:
            return finalizar(timeout_s=max(0.0, float(restante_s)))
        return finalizar()

    def encerrar(self, timeout_s: float | None = None) -> dict[str, bool]:
        """Sinaliza tudo e compartilha um único orçamento entre as esperas."""
        orcamento = self.timeout_encerramento_s if timeout_s is None else max(0.0, float(timeout_s))
        prazo = self.monotonic() + orcamento
        self.gerenciador.solicitar_encerramento()
        resultados: dict[str, bool] = {}
        for nome, finalizar in self.encerramento:
            try:
                restante = max(0.0, prazo - self.monotonic())
                self._invocar_finalizador(finalizar, restante)
                resultados[str(nome)] = True
            except Exception as erro:
                resultados[str(nome)] = False
                self.log(
                    f"⚠️ [ENCERRAMENTO] {nome} não encerrou corretamente: "
                    f"{type(erro).__name__}"
                )
                self._relatar("encerramento", str(nome), erro)
        encerrar_gerenciador = getattr(self.gerenciador, "encerrar", None)
        if callable(encerrar_gerenciador):
            try:
                restante = max(0.0, prazo - self.monotonic())
                encerrar_gerenciador(timeout_s=restante)
            except KeyboardInterrupt:
                self.log("🛑 Encerramento acelerado por novo Ctrl+C.")
            except Exception as erro:
                self.log(
                    "⚠️ [ENCERRAMENTO] supervisor não encerrou corretamente: "
                    f"{type(erro).__name__}"
                )
                self._relatar("encerramento", "supervisor", erro)
        return resultados


def criar_composicao_servicos_laylay_runtime(
    **kwargs: Any,
) -> ComposicaoServicosLaylayRuntime:
    return ComposicaoServicosLaylayRuntime(**kwargs)


def criar_composicao_servicos_padrao(
    namespace: Mapping[str, Any],
    *,
    gerenciador: Any,
    registrar_falha: Callable[..., Any] | None = None,
    registrar_metrica: Callable[..., Any] | None = None,
    log: Callable[[str], Any] = print,
    inicializacao_diferida: bool = True,
) -> ComposicaoServicosLaylayRuntime:
    """Resolve somente as conexões do ponto de entrada e valida nomes cedo."""
    ns = dict(namespace or {})

    def obrigatoria(nome: str) -> Callable[..., Any]:
        valor = ns.get(nome)
        if not callable(valor):
            raise RuntimeError(f"dependência de inicialização ausente: {nome}")
        return valor

    def metodo(nome_objeto: str, nome_metodo: str) -> Callable[..., Any]:
        objeto = ns.get(nome_objeto)
        valor = getattr(objeto, nome_metodo, None)
        if not callable(valor):
            raise RuntimeError(
                f"dependência de inicialização ausente: {nome_objeto}.{nome_metodo}"
            )
        return valor

    renovar_sessao = obrigatoria("_renovar_sessao_conversa")
    return ComposicaoServicosLaylayRuntime(
        gerenciador=gerenciador,
        etapas={
            "carregar memória": obrigatoria("carregar_memoria"),
            "ativar autonomia segura": obrigatoria("_preparar_autonomia_segura_padrao"),
            "iniciar nova sessão conversacional": lambda: renovar_sessao(
                "inicio_programa", True,
            ),
            "iniciar memória de contexto diária": obrigatoria("init_memoria_contexto_diaria"),
            "carregar playlists": obrigatoria("_carregar_playlists_para_memoria"),
            "iniciar worker de falas": obrigatoria("_iniciar_worker_de_falas"),
        },
        etapas_diferidas={
            "iniciar rede associativa": metodo("_rede_associativa_runtime", "iniciar"),
            "preparar sugestões no modo jogo": obrigatoria("_preparar_sugestoes_proativas_jogo"),
            "iniciar ponte Xbox Game Bar": metodo("_gamebar_bridge_runtime", "iniciar"),
            "iniciar avatar": metodo("_avatar_runtime", "iniciar"),
        },
        threads={
            "Laylay-WS": obrigatoria("run_ws_server_in_thread"),
            "Laylay-Gmail": obrigatoria("gmail_daemon"),
            "Laylay-Agenda": obrigatoria("_agenda_daemon"),
            "Laylay-Rotina": obrigatoria("monitor_rotina_daemon"),
            "Laylay-Porteiro": obrigatoria("_porteiro_daemon"),
            "Laylay-Saude": obrigatoria("_monitor_saude_daemon"),
            "Laylay-Ouvido": metodo("_ouvido_whisper_runtime", "executar"),
            "Laylay-Observador-Inventário-Jogo": metodo(
                "_observador_inventario_jogo_runtime", "executar",
            ),
            "Laylay-Observador-Presença-Jogo": metodo(
                "_observador_presenca_jogo_runtime", "executar",
            ),
            "Laylay-Diretor-Presença": metodo("_diretor_presenca_runtime", "executar"),
            "Laylay-Observador-Área-Transferência": metodo(
                "_observador_area_transferencia_runtime", "executar",
            ),
        },
        threads_com_parada={
            "Laylay-Chat-Terminal": obrigatoria("_escutar_texto_do_chat_terminal"),
            "Laylay-Monitor-Janelas": metodo("_monitor_janelas_runtime", "executar"),
        },
        threads_com_espera={
            "Laylay-Ritmo-Circadiano": metodo("_ritmo_circadiano_runtime", "executar"),
            "Laylay-Consciência-Temporal": metodo("_motor_temporal_runtime", "executar"),
            "Laylay-Aprendizado": metodo("_motor_aprendizado_runtime", "executar"),
        },
        hotkeys=(
            ("modo_chat", obrigatoria("registrar_hotkeys_modo_chat")),
            ("barra_comando", obrigatoria("registrar_hotkey_barra_comando")),
        ),
        encerramento=(
            # Interfaces têm afinidade de thread e precisam receber o sinal
            # enquanto o loop proprietário ainda pode processá-lo.
            ("barra_comando", metodo("_barra_comando_runtime", "encerrar")),
            ("avatar", metodo("_avatar_runtime", "parar")),
            ("gamebar", metodo("_gamebar_bridge_runtime", "parar")),
            ("voz", metodo("_voz_runtime", "encerrar")),
            ("rede_associativa", metodo("_rede_associativa_runtime", "encerrar")),
            ("memoria", obrigatoria("salvar_memoria")),
        ),
        registrar_falha=registrar_falha,
        registrar_metrica=registrar_metrica,
        log=log,
        inicializacao_diferida=inicializacao_diferida,
    )
