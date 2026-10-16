"""Atividade operacional observada, transitória e sem autoridade de execução.

O escopo representa tratamento em andamento. Não é um receipt do executor,
não confirma efeito e não nasce de uma intenção ou de uma emoção.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
import math
from threading import RLock
import time
from typing import Any, TypeVar

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, STATUS_RESULTADO_CANCELADO, inferir_confirmacao


APRESENTACAO_MINIMA_S = 0.8
VALIDADE_FALHA_S = 2.0
VALIDADE_SUCESSO_S = 3.0
_ORIGEM = "atividade_operacional_observada"
_T = TypeVar("_T")


def projetar_sucesso_operacional(estado: Mapping[str, Any] | None, *, agora: float | None = None) -> tuple[int, float] | None:
    """Ocorrência transitória do owner; não é autorização nem receipt novo."""
    if not isinstance(estado, Mapping) or estado.get("origem") != _ORIGEM:
        return None
    identidade, instante = estado.get("sucesso_id"), estado.get("sucesso_monotonic")
    if (type(identidade) is not int or identidade <= 0 or type(instante) not in (int, float)):
        return None
    idade = float(time.monotonic() if agora is None else agora) - instante
    return (identidade, float(instante)) if math.isfinite(idade) and 0 <= idade <= VALIDADE_SUCESSO_S else None


def _resultado_observado_concluiu(resultado: Any) -> bool:
    # Retornos dict de periféricos não entram aqui: evita comemorar os próprios
    # ACKs e permite distinguir proposta, emissão e resultado canônico aceito.
    if not isinstance(resultado, ResultadoAcao):
        return False
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    capacidade = consultar_capacidade(resultado.intent)
    return bool(resultado.origem == "executor" and resultado.id_solicitacao
                and resultado.ok is True and resultado.executou is True and resultado.confirmado is True
                and resultado.status not in STATUS_RESULTADO_CANCELADO
                and inferir_confirmacao(resultado.status, resultado.executou) is not False
                and capacidade.get("dominio") not in {"desconhecido", "corpo_motor"}
                and resultado.confirmacao_oferecida not in {"indisponivel", "envio_comando"})


def _resultado_observado_enviado(resultado: Any) -> bool:
    """Envio certificado, sem promover ausência de observação a sucesso."""
    if not isinstance(resultado, ResultadoAcao):
        return False
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    capacidade = consultar_capacidade(resultado.intent)
    return bool(resultado.origem == "executor" and resultado.id_solicitacao
                and resultado.ok is True and resultado.executou is True
                and resultado.confirmado is None
                and resultado.estado_final == "executado_sem_confirmacao"
                and inferir_confirmacao(resultado.status, resultado.executou) is None
                and capacidade.get("dominio") not in {"desconhecido", "corpo_motor"}
                and resultado.confirmacao_oferecida != "indisponivel")


def projetar_envio_operacional(estado: Mapping[str, Any] | None, *, agora: float | None = None) -> tuple[int, float] | None:
    """Sinal transitório de envio; não confirma efeito nem autoriza execução."""
    if not isinstance(estado, Mapping) or estado.get("origem") != _ORIGEM:
        return None
    identidade, instante = estado.get("envio_id"), estado.get("envio_monotonic")
    if type(identidade) is not int or identidade <= 0 or type(instante) not in (int, float):
        return None
    idade = float(time.monotonic() if agora is None else agora) - instante
    return (identidade, float(instante)) if math.isfinite(idade) and 0 <= idade <= VALIDADE_SUCESSO_S else None


def projetar_falha_operacional(
    estado: Mapping[str, Any] | None, *, agora: float | None = None,
) -> tuple[int, float] | None:
    """Retorna somente a ocorrência recente publicada por este owner."""
    if not isinstance(estado, Mapping) or estado.get("origem") != _ORIGEM:
        return None
    identidade, instante = estado.get("falha_id"), estado.get("falha_monotonic")
    if (not isinstance(identidade, int) or isinstance(identidade, bool)
        or identidade <= 0 or not isinstance(instante, (int, float))
        or isinstance(instante, bool)):
        return None
    try:
        idade = float(time.monotonic() if agora is None else agora) - float(instante)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(idade) or not 0.0 <= idade <= VALIDADE_FALHA_S:
        return None
    return identidade, float(instante)


def _resultado_observado_falhou(resultado: Any, *, retorno_executor: bool) -> bool:
    """Lê estados estruturados; ausência, recusa e pendência ficam neutras.

    Dicts só são elegíveis como retorno direto de um callback de execução.
    Publicações do ciclo exigem ResultadoAcao certificado pelo executor.
    """
    if isinstance(resultado, ResultadoAcao):
        dados = resultado.como_dict()
        if resultado.origem != "executor":
            return False
    elif retorno_executor and isinstance(resultado, Mapping):
        dados = resultado
        if dados.get("origem", "executor") != "executor":
            return False
    else:
        return False
    status = dados.get("status")
    if not isinstance(status, str) or not status:
        return False
    # Estes tokens são estados de decisão do contrato, nunca fala do usuário.
    # Não interpretar a narrativa do erro nem a emoção produzida depois.
    tokens = set(status.split("_"))
    if (status in STATUS_RESULTADO_CANCELADO
        or status in {"intent_nao_elegivel", "intent_nao_reconhecida", "tratado_sem_receipt"}
        or tokens.intersection({
            "aguardando", "pendencia", "pendente", "proposta", "recusa", "recusado", "recusada",
            "rejeitado", "rejeitada", "bloqueado", "bloqueada", "cancelado", "cancelada",
            "cancelamento", "ambiguo", "ambigua", "invalido", "invalida",
        })
        or dados.get("estado") in {"cancelado", "pendente", "bloqueado"}
        or dados.get("confirmado") is True):
        return False
    return any(dados.get(campo) is False for campo in ("ok", "executou", "confirmado"))


def projetar_execucao_operacional(estado: Mapping[str, Any] | None) -> bool:
    """Execução vigente do owner; não inclui a cauda de apresentação visual."""
    return bool(isinstance(estado, Mapping) and estado.get("origem") == _ORIGEM
                and type(estado.get("ativos")) is int and estado["ativos"] > 0)


def projetar_atividade_operacional(
    estado: Mapping[str, Any] | None, *, agora: float | None = None,
) -> bool:
    """Projeta somente o retrato deste owner; nunca interpreta um plano."""
    if not isinstance(estado, Mapping) or estado.get("origem") != _ORIGEM:
        return False
    if projetar_execucao_operacional(estado):
        return True
    inicio = estado.get("ultimo_inicio_monotonic")
    if inicio is None or isinstance(inicio, bool):
        return False
    try:
        idade = float(time.monotonic() if agora is None else agora) - float(inicio)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(idade) and 0.0 <= idade <= APRESENTACAO_MINIMA_S


class AtividadeOperacionalRuntime:
    """Owner único dos escopos visuais concorrentes, sem textos pessoais."""

    def __init__(
        self, *, publicar: Callable[[dict[str, Any]], Any],
        monotonic: Callable[[], float] = time.monotonic,
        relatar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self.publicar = publicar
        self.monotonic = monotonic
        self.relatar_falha = relatar_falha
        self._lock = RLock()
        self._ativos: set[object] = set()
        self._ultimo_inicio: float | None = None
        self._falha_id = 0
        self._falha_monotonic: float | None = None
        self._sucesso_id = 0
        self._sucesso_monotonic: float | None = None
        self._envio_id = 0
        self._envio_monotonic: float | None = None
        self._receipts_envio: dict[str, None] = {}
        self._envios_pendentes: set[object] = set()
        self._receipts_sucesso: dict[str, None] = {}
        self._escopo_resultado: ContextVar[object | None] = ContextVar("escopo_resultado_operacional", default=None)
        self._sucessos_pendentes: set[object] = set()
        self._escopos_sem_sucesso: set[object] = set()
        self._falhas_contexto: ContextVar[int] = ContextVar("falhas_atividade_operacional", default=0)
        self._receipts_falhos: dict[tuple[str, str], None] = {}
        # O estado é processual: reiniciar nunca restaura atividades antigas.
        self._publicar()

    def retrato(self) -> dict[str, Any]:
        with self._lock:
            return {
                "origem": _ORIGEM,
                "ativos": len(self._ativos),
                "ultimo_inicio_monotonic": self._ultimo_inicio,
                "falha_id": self._falha_id,
                "falha_monotonic": self._falha_monotonic,
                "sucesso_id": self._sucesso_id,
                "sucesso_monotonic": self._sucesso_monotonic,
                "envio_id": self._envio_id,
                "envio_monotonic": self._envio_monotonic,
                "autoriza_execucao": False,
                "confirma_efeito": False,
            }

    def _relatar(self, codigo: str, erro: Exception) -> None:
        try:
            if callable(self.relatar_falha):
                self.relatar_falha("atividade_operacional", codigo, erro=erro)
        except Exception:
            # Uma falha diagnóstica não altera o resultado operacional.
            pass

    def _publicar(self) -> None:
        try:
            self.publicar(self.retrato())
        except Exception as erro:
            self._relatar("falha_publicacao_visual", erro)

    def _iniciar(self) -> object:
        token = object()
        with self._lock:
            self._ativos.add(token)
            try:
                inicio = float(self.monotonic())
                self._ultimo_inicio = inicio if math.isfinite(inicio) else None
            except Exception as erro:
                self._ultimo_inicio = None
                self._relatar("falha_clock_visual", erro)
            self._publicar()
        return token

    def _concluir(self, token: object | None) -> None:
        with self._lock:
            self._ativos.discard(token)
            self._publicar()

    def _registrar_falha_observada(self, resultado: Any = None) -> bool:
        try:
            with self._lock:
                if isinstance(resultado, ResultadoAcao) and resultado.id_solicitacao:
                    chave = (resultado.id_solicitacao, resultado.status)
                    if chave in self._receipts_falhos:
                        return False
                    self._receipts_falhos[chave] = None
                    if len(self._receipts_falhos) > 128:
                        self._receipts_falhos.pop(next(iter(self._receipts_falhos)))
                instante = float(self.monotonic())
                self._falha_id += 1
                self._falha_monotonic = instante if math.isfinite(instante) else None
                self._falhas_contexto.set(self._falhas_contexto.get() + 1)
                self.invalidar_sucesso_do_escopo()
                self._publicar()
                return True
        except Exception as erro:
            self._relatar("falha_observacao_visual", erro)
            return False

    def invalidar_sucesso_do_escopo(self) -> None:
        """Falha parcial/recusa de etapa impede comemoração do lote inteiro."""
        with self._lock:
            raiz = self._escopo_resultado.get()
            if raiz is not None:
                self._escopos_sem_sucesso.add(raiz)
                self._sucessos_pendentes.discard(raiz)
                self._envios_pendentes.discard(raiz)

    def _publicar_envio(self) -> None:
        with self._lock:
            instante = float(self.monotonic())
            if math.isfinite(instante):
                self._envio_id += 1
                self._envio_monotonic = instante
                self._publicar()

    def _observar_envio(self, resultado: ResultadoAcao) -> bool:
        with self._lock:
            if resultado.id_solicitacao in self._receipts_envio or resultado.id_solicitacao in self._receipts_sucesso:
                return False
            self._receipts_envio[resultado.id_solicitacao] = None
            if len(self._receipts_envio) > 128:
                self._receipts_envio.pop(next(iter(self._receipts_envio)))
            raiz = self._escopo_resultado.get()
            if raiz is None:
                self._publicar_envio()
            elif raiz not in self._escopos_sem_sucesso:
                self._envios_pendentes.add(raiz)
            return True

    def _publicar_sucesso(self) -> None:
        with self._lock:
            instante = float(self.monotonic())
            if math.isfinite(instante):
                self._sucesso_id += 1
                self._sucesso_monotonic = instante
                self._publicar()

    def _observar_sucesso(self, resultado: ResultadoAcao) -> bool:
        with self._lock:
            if resultado.id_solicitacao in self._receipts_sucesso:
                return False
            self._receipts_sucesso[resultado.id_solicitacao] = None
            if len(self._receipts_sucesso) > 128:
                self._receipts_sucesso.pop(next(iter(self._receipts_sucesso)))
            raiz = self._escopo_resultado.get()
            if raiz is None:
                self._publicar_sucesso()
            elif raiz not in self._escopos_sem_sucesso:
                self._sucessos_pendentes.add(raiz)
            return True

    def observar_resultado(self, resultado: Any, *, retorno_executor: bool = False) -> bool:
        """Observa receipt aceito ou retorno atual, sem substituir seu resultado."""
        try:
            if isinstance(resultado, ResultadoAcao) and resultado.origem == "executor" and resultado.status in STATUS_RESULTADO_CANCELADO:
                self.invalidar_sucesso_do_escopo()
            if _resultado_observado_falhou(resultado, retorno_executor=retorno_executor):
                return self._registrar_falha_observada(resultado)
            if _resultado_observado_concluiu(resultado):
                return self._observar_sucesso(resultado)
            if _resultado_observado_enviado(resultado):
                return self._observar_envio(resultado)
        except Exception as erro:
            self._relatar("falha_leitura_receipt_visual", erro)
        return False

    @contextmanager
    def escopo(self) -> Iterator[None]:
        """Observa o tratamento sem substituir retorno ou exceção do executor."""
        token = None
        raiz_anterior = self._escopo_resultado.get()
        contexto_raiz = None
        falhas_antes = self._falhas_contexto.get()
        try:
            token = self._iniciar()
            if raiz_anterior is None:
                contexto_raiz = self._escopo_resultado.set(token)
        except Exception as erro:
            self._relatar("falha_inicio_visual", erro)
        try:
            yield
        except Exception:
            # CancelledError/BaseException não representam falha do executor.
            if self._falhas_contexto.get() == falhas_antes:
                self._registrar_falha_observada()
            raise
        except BaseException:
            # Cancelar o lote não é falha visual e também não é sucesso total.
            self.invalidar_sucesso_do_escopo()
            raise
        finally:
            try:
                self._concluir(token)
                if contexto_raiz is not None:
                    with self._lock:
                        comemorar = token in self._sucessos_pendentes and token not in self._escopos_sem_sucesso
                        enviado = token in self._envios_pendentes and token not in self._escopos_sem_sucesso
                        self._sucessos_pendentes.discard(token)
                        self._envios_pendentes.discard(token)
                        self._escopos_sem_sucesso.discard(token)
                        if enviado:
                            self._publicar_envio()
                        elif comemorar:
                            self._publicar_sucesso()
            except Exception as erro:
                self._relatar("falha_fim_visual", erro)
            finally:
                if contexto_raiz is not None:
                    self._escopo_resultado.reset(contexto_raiz)

    def executar(self, callback: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
        falhas_antes = self._falhas_contexto.get()
        with self.escopo():
            resultado = callback(*args, **kwargs)
            if self._falhas_contexto.get() == falhas_antes:
                self.observar_resultado(resultado, retorno_executor=True)
            return resultado

    async def executar_assincrono(
        self, callback: Callable[..., Awaitable[_T]], *args: Any, **kwargs: Any,
    ) -> _T:
        # O lock só protege início/conclusão; nunca permanece durante await.
        falhas_antes = self._falhas_contexto.get()
        with self.escopo():
            resultado = await callback(*args, **kwargs)
            if self._falhas_contexto.get() == falhas_antes:
                self.observar_resultado(resultado, retorno_executor=True)
            return resultado


def criar_atividade_operacional_runtime(
    *, estado: Any, **kwargs: Any,
) -> AtividadeOperacionalRuntime:
    return AtividadeOperacionalRuntime(
        publicar=lambda retrato: estado.atualizar_campos(
            "mental", atividade_operacional=retrato,
        ),
        **kwargs,
    )
