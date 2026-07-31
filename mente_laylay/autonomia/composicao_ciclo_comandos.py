"""Composição tardia do contexto e do ciclo central de comandos."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from mente_laylay.autonomia.coordenador_intencao import (
    DEPENDENCIAS_CICLO_COMANDOS,
    criar_ciclo_comandos_runtime,
)
from mente_laylay.integracao.contexto_execucao_ia import (
    DEPENDENCIAS_EXECUCAO_INTENCAO,
    criar_contexto_intencao_runtime,
)
from mente_laylay.integracao.registro_iot import registrar_iot
from mente_laylay.integracao.registro_arquivos import registrar_arquivos_leitura
from mente_laylay.integracao.registro_mutacoes_arquivos import registrar_arquivos_mutacao
from mente_laylay.integracao.registro_musica import registrar_musica_leitura


class ComposicaoCicloComandosRuntime:
    """Oferece callbacks estáveis antes de congelar o registro de serviços."""

    def __init__(
        self,
        *,
        log: Callable[..., Any] = print,
        monitor_saude: Any = None,
        registrar_metrica: Callable[..., Any] | None = None,
        registrar_falha: Callable[..., Any] | None = None,
        registrar_decisao: Callable[..., Any] | None = None,
        contexto_factory: Callable[..., Any] = criar_contexto_intencao_runtime,
        ciclo_factory: Callable[..., Any] = criar_ciclo_comandos_runtime,
    ) -> None:
        self.log = log
        self.monitor_saude = monitor_saude
        self.registrar_metrica = registrar_metrica
        self.registrar_falha = registrar_falha
        self.registrar_decisao = registrar_decisao
        self.contexto_factory = contexto_factory
        self.ciclo_factory = ciclo_factory
        self._servicos: dict[str, Any] = {}
        self._contexto = None
        self._ciclo = None
        self._iot = None
        self._arquivos_leitura = None
        self._arquivos_mutacao = None
        self._musica_leitura = None

    def conectar(
        self,
        *,
        servicos: Mapping[str, Any],
        estado_getter: Callable[[], dict[str, Any]],
    ) -> tuple[Any, Any]:
        if self._ciclo is not None:
            return self._contexto, self._ciclo
        if "_registro_iot_runtime" not in servicos:
            raise RuntimeError("dependência obrigatória ausente na composição: IoT")
        registro_iot = registrar_iot(servicos["_registro_iot_runtime"])
        self._iot = registro_iot
        if "_registro_arquivos_leitura_runtime" not in servicos:
            raise RuntimeError(
                "dependência obrigatória ausente na composição: leitura de arquivos"
            )
        registro_arquivos = registrar_arquivos_leitura(
            servicos["_registro_arquivos_leitura_runtime"]
        )
        self._arquivos_leitura = registro_arquivos
        if "_registro_arquivos_mutacao_runtime" not in servicos:
            raise RuntimeError(
                "dependência obrigatória ausente na composição: mutação de arquivos"
            )
        registro_mutacoes = registrar_arquivos_mutacao(
            servicos["_registro_arquivos_mutacao_runtime"]
        )
        self._arquivos_mutacao = registro_mutacoes
        if "_registro_musica_leitura_runtime" not in servicos:
            raise RuntimeError(
                "dependência obrigatória ausente na composição: leitura musical"
            )
        registro_musica = registrar_musica_leitura(
            servicos["_registro_musica_leitura_runtime"]
        )
        self._musica_leitura = registro_musica
        permitidos = set(DEPENDENCIAS_EXECUCAO_INTENCAO).union(
            DEPENDENCIAS_CICLO_COMANDOS
        )
        self._servicos = {
            nome: servicos[nome]
            for nome in permitidos
            if nome in servicos
        }
        snapshot = lambda: dict(self._servicos)
        self._contexto = self.contexto_factory(
            namespace_getter=snapshot,
            estado_getter=estado_getter,
            monitor_saude=self.monitor_saude,
            iot=registro_iot,
            arquivos_leitura=registro_arquivos,
            arquivos_mutacao=registro_mutacoes,
            musica_leitura=registro_musica,
        )
        self._ciclo = self.ciclo_factory(
            namespace_getter=snapshot,
            contexto_intencao_runtime=self._contexto,
            log=self.log,
            monitor_saude=self.monitor_saude,
            registrar_metrica_cb=self.registrar_metrica,
            registrar_falha_cb=self.registrar_falha,
            registrar_decisao_cb=self.registrar_decisao,
        )
        self._contexto.validar_conexoes()
        self._ciclo.validar_conexoes()
        return self._contexto, self._ciclo

    def _obter_ciclo(self) -> Any:
        if self._ciclo is None:
            raise RuntimeError("ciclo de comandos ainda não conectado aos serviços")
        return self._ciclo

    @property
    def contexto(self) -> Any:
        if self._contexto is None:
            raise RuntimeError("contexto de intenção ainda não conectado aos serviços")
        return self._contexto

    @property
    def ciclo(self) -> Any:
        return self._obter_ciclo()

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))

    @property
    def servicos_tipados_registrados(self) -> tuple[str, ...]:
        registrados = []
        if self._arquivos_leitura is not None:
            registrados.append("arquivos_leitura")
        if self._arquivos_mutacao is not None:
            registrados.append("arquivos_mutacao")
        if self._iot is not None:
            registrados.append("iot")
        if self._musica_leitura is not None:
            registrados.append("musica_leitura")
        return tuple(registrados)

    def executar_intencao(self, resultado: dict, texto_original: str) -> bool:
        return bool(self._obter_ciclo().executar_intencao(resultado, texto_original))

    def executar_texto(self, texto: str, origem: str = "") -> bool:
        return bool(self._obter_ciclo().executar_texto(texto, origem))

    def processar_cadeia(self, texto: str, origem: str = "") -> bool:
        return bool(self._obter_ciclo().processar_cadeia(texto, origem))

    def processar_deterministico(
        self, texto: str, origem: str = "", texto_original: str = "",
    ) -> bool:
        return bool(self._obter_ciclo().processar_deterministico(
            texto, origem, texto_original,
        ))

    def tentar_intencao_ai_primeiro(self, texto: str) -> Any:
        return self._obter_ciclo().tentar_intencao_ai_primeiro(texto)

    def resolver_comando_natural(
        self, texto: str, origem: str = "",
    ) -> tuple[dict[str, Any] | None, str]:
        """Expõe a decisão canônica sem duplicar roteamento ou execução."""
        return self._obter_ciclo().resolver_comando_natural(texto, origem)

    def decisao_comando_ja_avaliada(self, texto: str) -> bool:
        """Evita que outra fase reclassifique o texto no mesmo turno."""
        return bool(self._obter_ciclo().decisao_ja_avaliada(texto))

    def diagnostico_linguagem_natural(self) -> dict[str, Any]:
        return dict(self._obter_ciclo().diagnostico_linguagem_natural())


def criar_composicao_ciclo_comandos_runtime(
    **kwargs: Any,
) -> ComposicaoCicloComandosRuntime:
    return ComposicaoCicloComandosRuntime(**kwargs)
