"""Registro allowlist dos serviços publicados pela raiz de composição."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from mente_laylay.autonomia.coordenador_intencao import DEPENDENCIAS_CICLO_COMANDOS
from mente_laylay.autonomia.preferencias_sugestoes_runtime import (
    DEPENDENCIAS_PREFERENCIAS_SUGESTOES,
)
from mente_laylay.cognicao.composicao_turno import DEPENDENCIAS_ORQUESTRACAO_TURNO
from mente_laylay.integracao.ambiente_navegacao import DEPENDENCIAS_AMBIENTE_NAVEGACAO
from mente_laylay.integracao.chrome_ws_contexto import ChromeWsContextoRuntime
from mente_laylay.integracao.composicao_contextos_ia import (
    _DISPATCHER_GRUPOS,
    _EXECUCAO,
    _FINALIZACAO_GRUPOS,
)
from mente_laylay.integracao.composicao_entrada_interacao import (
    DEPENDENCIAS_COMANDOS_IMEDIATOS,
    DEPENDENCIAS_CONTEXTO_CHAT,
    DEPENDENCIAS_DETECCAO,
)
from mente_laylay.integracao.composicao_estado_aplicacao import (
    DEPENDENCIAS_ADAPTADORES_APLICACAO,
    DEPENDENCIAS_ESTADO_CONTEXTO,
)
from mente_laylay.integracao.contexto_execucao_ia import (
    DEPENDENCIAS_EXECUCAO_INTENCAO,
)
from mente_laylay.personalidade.composicao_resposta_conversacional import (
    DEPENDENCIAS_RESPOSTA_CONVERSACIONAL,
)
from mente_laylay.personalidade.orquestrador_fala_runtime import (
    DEPENDENCIAS_ORQUESTRADOR_FALA,
)


DEPENDENCIAS_CONTEXTO_IMEDIATO = (
    "_normalizar_texto_com_apelidos", "_alvo_corrigido_atual",
    "_registrar_alvo_corrigido", "falar_com_lipsync",
    "_contexto_musical_ativo", "_estrutura_arquivo_recente",
    "_foco_vivo_atual", "enviar_mensagem",
)

DEPENDENCIAS_CONTEXTO_IA = (
    "_resumo_mente_integrada_para_prompt", "get_status_humor_prompt",
    "_executar_captura_tela_intent",
    *_EXECUCAO,
    *tuple(nome for grupo in _DISPATCHER_GRUPOS.values() for nome in grupo),
    *tuple(nome for grupo in _FINALIZACAO_GRUPOS.values() for nome in grupo),
)

DEPENDENCIAS_INICIALIZACAO = (
    "_renovar_sessao_conversa", "carregar_memoria", "_rede_associativa_runtime",
    "_preparar_autonomia_segura_padrao", "_preparar_sugestoes_proativas_jogo",
    "init_memoria_contexto_diaria", "_carregar_playlists_para_memoria",
    "_iniciar_worker_de_falas", "_gamebar_bridge_runtime", "_avatar_runtime",
    "run_ws_server_in_thread", "gmail_daemon", "_agenda_daemon",
    "monitor_rotina_daemon", "_porteiro_daemon", "_monitor_saude_daemon",
    "_ouvido_whisper_runtime", "_observador_inventario_jogo_runtime",
    "_observador_presenca_jogo_runtime", "_diretor_presenca_runtime",
    "_observador_area_transferencia_runtime", "_escutar_texto_do_chat_terminal",
    "_monitor_janelas_runtime", "_ritmo_circadiano_runtime",
    "_motor_temporal_runtime", "_motor_aprendizado_runtime",
    "registrar_hotkeys_modo_chat", "registrar_hotkey_barra_comando",
    "_barra_comando_runtime", "_voz_runtime", "salvar_memoria",
)


def _uniao_dependencias() -> frozenset[str]:
    grupos = (
        DEPENDENCIAS_CICLO_COMANDOS,
        DEPENDENCIAS_EXECUCAO_INTENCAO,
        DEPENDENCIAS_PREFERENCIAS_SUGESTOES,
        DEPENDENCIAS_ORQUESTRACAO_TURNO,
        DEPENDENCIAS_AMBIENTE_NAVEGACAO,
        ChromeWsContextoRuntime.DEPENDENCIAS_COMPLETAS,
        DEPENDENCIAS_COMANDOS_IMEDIATOS,
        DEPENDENCIAS_CONTEXTO_CHAT,
        DEPENDENCIAS_DETECCAO,
        DEPENDENCIAS_ADAPTADORES_APLICACAO,
        DEPENDENCIAS_ESTADO_CONTEXTO,
        DEPENDENCIAS_RESPOSTA_CONVERSACIONAL,
        DEPENDENCIAS_ORQUESTRADOR_FALA,
        DEPENDENCIAS_CONTEXTO_IMEDIATO,
        DEPENDENCIAS_CONTEXTO_IA,
        DEPENDENCIAS_INICIALIZACAO,
    )
    return frozenset(nome for grupo in grupos for nome in grupo)


SERVICOS_APLICACAO_PERMITIDOS = _uniao_dependencias()


class RegistroServicosAplicacaoRuntime:
    """Congela somente serviços conhecidos; nunca retém o namespace recebido."""

    def __init__(
        self,
        namespace: Mapping[str, Any],
        *,
        permitidos: Iterable[str] = SERVICOS_APLICACAO_PERMITIDOS,
    ) -> None:
        self._permitidos = frozenset(str(nome) for nome in permitidos)
        self._servicos = {
            nome: namespace[nome] for nome in self._permitidos if nome in namespace
        }

    def publicar(self, **servicos: Any) -> None:
        desconhecidos = sorted(set(servicos).difference(self._permitidos))
        if desconhecidos:
            raise RuntimeError(
                "serviços fora do contrato de composição: "
                + ", ".join(desconhecidos)
            )
        self._servicos.update(servicos)

    def snapshot(
        self, *, obrigatorios: Iterable[str] = (),
    ) -> dict[str, Any]:
        faltantes = [
            str(nome) for nome in obrigatorios if str(nome) not in self._servicos
        ]
        if faltantes:
            raise RuntimeError(
                "serviços obrigatórios ausentes na composição: "
                + ", ".join(sorted(faltantes))
            )
        return dict(self._servicos)

    @property
    def nomes(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))


def criar_registro_servicos_aplicacao_runtime(
    namespace: Mapping[str, Any],
    **kwargs: Any,
) -> RegistroServicosAplicacaoRuntime:
    return RegistroServicosAplicacaoRuntime(namespace, **kwargs)
