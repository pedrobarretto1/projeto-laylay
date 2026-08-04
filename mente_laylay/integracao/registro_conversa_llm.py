"""Contratos tipados entre conversa, preparação de prompt e modelo de linguagem."""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable


def _copiar_mensagens(mensagens: Sequence[Mapping[str, Any]] | None) -> tuple[dict[str, Any], ...]:
    return tuple(dict(item) for item in (mensagens or ()) if isinstance(item, Mapping))


@dataclass(frozen=True)
class PacotePrompt:
    """Contexto conversacional pronto, sem expor a memória que o produziu."""

    mensagens: tuple[dict[str, Any], ...]
    prompt_sistema: str = field(default="", repr=False)


@dataclass(frozen=True)
class PedidoModelo:
    """Pedido imutável que a conversa entrega ao serviço de modelo."""

    mensagens: tuple[dict[str, Any], ...]
    com_tools: bool = False
    max_tokens: int = 1024
    modo_rapido: bool = False
    timeout: int | None = None
    permitir_conversa_modo_jogo: bool = False
    prioridade_interativa: bool = False
    permitir_durante_interacao: bool = False

    @classmethod
    def criar(
        cls,
        mensagens: Sequence[Mapping[str, Any]] | None,
        **opcoes: Any,
    ) -> "PedidoModelo":
        return cls(mensagens=_copiar_mensagens(mensagens), **opcoes)


@dataclass(frozen=True)
class ResultadoModelo:
    texto: str
    sucesso: bool
    rota: str = "principal"


@dataclass(frozen=True)
class RequisicaoTransporteLLM:
    """Payload já preparado; o cliente HTTP não conhece memória ou contexto."""

    payload: Mapping[str, Any] = field(repr=False)
    timeout: int | None = None
    permitir_conversa_modo_jogo: bool = False
    prioridade_interativa: bool = False
    permitir_durante_interacao: bool = False


@runtime_checkable
class PortaPreparacaoConversa(Protocol):
    def preparar_pacote(self, texto: str) -> PacotePrompt: ...
    def preparar_instrucao_rapida(self, texto: str) -> str: ...
    def diagnostico(self) -> dict[str, Any]: ...


@runtime_checkable
class PortaModeloLLM(Protocol):
    def executar(self, pedido: PedidoModelo) -> ResultadoModelo: ...
    def diagnostico(self) -> dict[str, Any]: ...


@runtime_checkable
class PortaEstadoConversa(Protocol):
    def mensagens(self) -> list[dict[str, Any]]: ...
    def substituir(self, mensagens: Sequence[Mapping[str, Any]]) -> None: ...
    def iniciar_turno(self, turno_id: Any, texto_usuario: str) -> list[dict[str, Any]]: ...
    def concluir_turno(self, turno_id: Any, fala_assistente: str) -> bool: ...
    def abortar_turno(self, turno_id: Any) -> bool: ...
    def diagnostico(self) -> dict[str, Any]: ...


def _validar(servico: Any, operacoes: tuple[str, ...], dominio: str) -> None:
    ausentes = tuple(
        nome for nome in operacoes if not callable(getattr(servico, nome, None))
    )
    if ausentes:
        raise RuntimeError(
            f"serviço de {dominio} inválido na composição; operações ausentes: "
            + ", ".join(ausentes)
        )


@dataclass(frozen=True)
class RegistroPreparacaoConversa:
    servico: PortaPreparacaoConversa = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroPreparacaoConversa":
        _validar(servico, ("preparar_pacote", "diagnostico"), "preparação da conversa")
        return cls(servico=servico)

    def preparar_pacote(self, texto: str) -> PacotePrompt:
        pacote = self.servico.preparar_pacote(texto)
        if not isinstance(pacote, PacotePrompt):
            raise RuntimeError("preparador da conversa devolveu um pacote inválido")
        return PacotePrompt(_copiar_mensagens(pacote.mensagens), pacote.prompt_sistema)

    def preparar_instrucao_rapida(self, texto: str) -> str:
        preparar = getattr(self.servico, "preparar_instrucao_rapida", None)
        if not callable(preparar):
            # Compatibilidade com preparadores anteriores. Na composição real
            # o método é obrigatório por comportamento, mas adaptadores de
            # teste e extensões antigas continuam seguros e sem autoridade.
            return ""
        return str(preparar(str(texto or "")) or "").strip()

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {
            chave: bruto[chave]
            for chave in (
                "disponivel", "preparacoes", "preparacoes_rapidas", "falhas",
                "memoria_exposta", "autoriza_execucao",
            )
            if chave in bruto
        }


@dataclass(frozen=True)
class RegistroModeloLLM:
    servico: PortaModeloLLM = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroModeloLLM":
        _validar(servico, ("executar", "diagnostico"), "modelo de linguagem")
        return cls(servico=servico)

    def executar(self, pedido: PedidoModelo) -> ResultadoModelo:
        if not isinstance(pedido, PedidoModelo):
            raise TypeError("o modelo aceita somente PedidoModelo")
        resultado = self.servico.executar(pedido)
        if not isinstance(resultado, ResultadoModelo):
            raise RuntimeError("serviço de modelo devolveu um resultado inválido")
        return resultado

    def enviar(self, mensagens: Any, **opcoes: Any) -> str:
        """Compatibilidade temporária para habilidades anteriores à P3.9."""
        pedido = PedidoModelo.criar(
            mensagens if isinstance(mensagens, (list, tuple)) else (),
            com_tools=bool(opcoes.pop("_com_tools", True)),
            max_tokens=int(opcoes.pop("max_tokens", 1024) or 1024),
            modo_rapido=bool(opcoes.pop("modo_rapido", False)),
            timeout=opcoes.pop("timeout", None),
            permitir_conversa_modo_jogo=bool(opcoes.pop("_permitir_conversa_modo_jogo", False)),
            prioridade_interativa=bool(opcoes.pop("_prioridade_interativa", False)),
            permitir_durante_interacao=bool(opcoes.pop("_permitir_durante_interacao", False)),
        )
        return self.executar(pedido).texto

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {
            chave: bruto[chave]
            for chave in (
                "disponivel", "endpoint_local", "requisicoes", "sucessos", "falhas",
                "memoria_exposta", "credencial_exposta", "autoriza_execucao",
            )
            if chave in bruto
        }


class ModeloLLMDiferidoRuntime:
    """Porta estável para serviços compostos antes do transporte da LLM."""

    def __init__(self) -> None:
        self._registro: RegistroModeloLLM | None = None
        self._lock = threading.RLock()

    def conectar(self, servico: Any) -> None:
        registro = registrar_modelo_llm(servico)
        with self._lock:
            self._registro = registro

    def executar(self, pedido: PedidoModelo) -> ResultadoModelo:
        with self._lock:
            registro = self._registro
        if registro is None:
            raise RuntimeError("modelo de linguagem ainda não conectado")
        return registro.executar(pedido)

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            registro = self._registro
        if registro is None:
            return {
                "disponivel": False,
                "requisicoes": 0,
                "falhas": 0,
                "memoria_exposta": False,
                "credencial_exposta": False,
                "autoriza_execucao": False,
            }
        return registro.diagnostico()


class EstadoConversaRuntime:
    """Fronteira mínima para o histórico temporário da conversa."""

    def __init__(self, *, getter: Any, setter: Any) -> None:
        if not callable(getter) or not callable(setter):
            raise RuntimeError("estado da conversa exige leitura e escrita explícitas")
        self._getter = getter
        self._setter = setter
        self._lock = threading.RLock()
        self._turnos: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _chave_turno(turno_id: Any) -> str:
        chave = str(turno_id or "").strip()
        if not chave:
            raise ValueError("turno da conversa exige identificador")
        return chave

    def _mensagens_sem_lock(self) -> list[dict[str, Any]]:
        bruto = self._getter()
        return [
            dict(item) for item in bruto if isinstance(item, Mapping)
        ] if isinstance(bruto, list) else []

    def _substituir_sem_lock(
        self,
        mensagens: Sequence[Mapping[str, Any]],
    ) -> None:
        self._setter([
            dict(item) for item in mensagens if isinstance(item, Mapping)
        ])

    def _limitar_turnos(self) -> None:
        while len(self._turnos) > 128:
            primeira = next(iter(self._turnos))
            del self._turnos[primeira]

    def mensagens(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._mensagens_sem_lock()

    def substituir(self, mensagens: Sequence[Mapping[str, Any]]) -> None:
        with self._lock:
            self._substituir_sem_lock(mensagens)

    def iniciar_turno(
        self,
        turno_id: Any,
        texto_usuario: str,
    ) -> list[dict[str, Any]]:
        """Publica a entrada uma única vez antes de chamar o modelo."""
        chave = self._chave_turno(turno_id)
        texto = str(texto_usuario or "").strip()
        if not texto:
            raise ValueError("turno da conversa exige texto do usuário")
        with self._lock:
            existente = self._turnos.get(chave)
            if existente is not None:
                if existente.get("texto_usuario") != texto:
                    raise RuntimeError(
                        "identificador de turno reutilizado com outro texto"
                    )
                if existente.get("status") == "abortado":
                    existente["status"] = "iniciado"
                return self._mensagens_sem_lock()

            mensagens = self._mensagens_sem_lock()
            mensagens.append({"role": "user", "content": texto})
            self._substituir_sem_lock(mensagens)
            self._turnos[chave] = {
                "status": "iniciado",
                "texto_usuario": texto,
                "fala_assistente": "",
            }
            self._limitar_turnos()
            # O pedido ao modelo usa exatamente o lote que acabou de ser
            # publicado. Isso mantém o turno íntegro mesmo quando um adaptador
            # de estado confirma a escrita de forma diferida.
            return [dict(item) for item in mensagens]

    def concluir_turno(self, turno_id: Any, fala_assistente: str) -> bool:
        """Publica no máximo uma resposta final para a entrada do turno."""
        chave = self._chave_turno(turno_id)
        fala = str(fala_assistente or "").strip()
        if not fala:
            return False
        with self._lock:
            existente = self._turnos.get(chave)
            if existente is None:
                raise RuntimeError("turno concluído sem entrada registrada")
            if existente.get("status") == "concluido":
                return False

            mensagens = self._mensagens_sem_lock()
            mensagens.append({"role": "assistant", "content": fala})
            self._substituir_sem_lock(mensagens)
            existente["status"] = "concluido"
            existente["fala_assistente"] = fala
            return True

    def abortar_turno(self, turno_id: Any) -> bool:
        """Encerra uma tentativa sem fabricar uma fala da assistente."""
        chave = self._chave_turno(turno_id)
        with self._lock:
            existente = self._turnos.get(chave)
            if existente is None or existente.get("status") == "concluido":
                return False
            existente["status"] = "abortado"
            return True

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            estados = [str(item.get("status") or "") for item in self._turnos.values()]
            return {
                "disponivel": True,
                "mensagens": len(self._mensagens_sem_lock()),
                "turnos_iniciados": estados.count("iniciado"),
                "turnos_concluidos": estados.count("concluido"),
                "turnos_abortados": estados.count("abortado"),
                "memoria_duravel": False,
                "autoriza_execucao": False,
            }


def registrar_preparacao_conversa(servico: Any) -> RegistroPreparacaoConversa:
    return servico if isinstance(servico, RegistroPreparacaoConversa) else RegistroPreparacaoConversa.criar(servico)


def registrar_modelo_llm(servico: Any) -> RegistroModeloLLM:
    return servico if isinstance(servico, RegistroModeloLLM) else RegistroModeloLLM.criar(servico)


def resolver_enviador_modelo(
    *,
    modelo_llm: Any = None,
    enviar_mensagem: Callable[..., Any] | None = None,
) -> Callable[..., Any] | None:
    """Prioriza a porta tipada e isola a compatibilidade com callbacks antigos."""
    if modelo_llm is not None:
        return registrar_modelo_llm(modelo_llm).enviar
    return enviar_mensagem if callable(enviar_mensagem) else None


def criar_estado_conversa_runtime(**kwargs: Any) -> EstadoConversaRuntime:
    return EstadoConversaRuntime(**kwargs)


def criar_modelo_llm_diferido_runtime() -> ModeloLLMDiferidoRuntime:
    return ModeloLLMDiferidoRuntime()
