"""Composição dos contextos vivos usados pelo fluxo de resposta e execução."""

from __future__ import annotations

import re
import urllib.parse
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.contexto_resposta_ia import criar_contexto_prompt_runtime
from mente_laylay.autonomia.execucao_ia import criar_contexto_exec_runtime
from mente_laylay.integracao.contexto_execucao_ia import (
    criar_contexto_dispatcher_runtime,
    criar_contexto_finalizacao_runtime,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PortaModeloLLM,
    PortaPreparacaoConversa,
    registrar_modelo_llm,
    registrar_preparacao_conversa,
)
from mente_laylay.integracao.registro_musica import (
    PortaMusicaLeitura,
    registrar_musica_leitura,
)
from mente_laylay.integracao.registro_operacoes_musicais import (
    PortaMusicaOperacoes,
    registrar_operacoes_musicais,
)
from mente_laylay.integracao.registro_navegador import (
    PortaNavegadorLeitura,
    PortaNavegadorOperacoes,
    registrar_navegador_leitura,
    registrar_navegador_operacoes,
)
from mente_laylay.integracao.registro_visao_jogo import (
    PortaVisaoJogoAnalise,
    PortaVisaoJogoLeitura,
    registrar_visao_jogo_analise,
    registrar_visao_jogo_leitura,
)


_EXECUCAO = (
    "ajustar_volume_sistema", "falar_com_lipsync",
    "abrir_programa", "fechar_programa", "APPS_MAP",
    "ativar_tela_cheia_robusta", "_eh_alvo_site_web",
    "_contexto_aponta_site_web", "is_valid_url", "formatar_url_ou_busca",
    "_autorizar_acao_pratica",
)

_DISPATCHER_GRUPOS = {
    "base": ("falar_com_lipsync", "salvar_memoria"),
    "navegacao": (
        "_enviar_pc_b", "interpretar_comando_local_rapido",
        "listar_programas_abertos",
        "organizar_janelas_robusto", "ativar_tela_cheia_robusta",
    ),
    "musica": (
        "_normalizar_query_musical", "_limpar_nome_playlist",
        "_buscar_primeiro_video_youtube", "_resolver_primeiro_video_youtube",
    ),
    "arquivos": ("executar_intencao",),
    "agenda_email": (
        "_agendamentos_load", "_agendamentos_save", "_agendamentos_transacionar",
        "_gmail_configurado", "_gmail_buscar_nao_lidos", "_gmail_falar_resumo_estiloso",
    ),
    "execucao": (
        "_executar_fechar_abas_paradas", "_executar_comando_conteudo",
        "processar_comando_deterministico",
    ),
    "autonomia": (
        "_autorizar_acao_pratica", "_autonomia_permite_execucao_musical",
    ),
}

_FINALIZACAO_GRUPOS = {
    "ia": ("limpar_resposta_da_ia",),
    "voz_memoria": (
        "falar_com_lipsync", "salvar_memoria", "memoria_inteligente",
    ),
    "autoaprimoramento": (
        "_registrar_autoaprimoramento", "_registrar_autocorrecao_virtual",
        "MAX_TENTATIVAS_AUTOCORRECAO",
    ),
}


def _sanitizar_aba_para_prompt(titulo: Any, url: Any) -> tuple[str, str]:
    titulo_seguro = re.sub(r"[\x00-\x1f\x7f]+", " ", str(titulo or ""))
    titulo_seguro = re.sub(r"\s+", " ", titulo_seguro).strip()[:160]
    try:
        partes = urllib.parse.urlsplit(str(url or "").strip())
        host = str(partes.hostname or "").strip().casefold()
        porta = f":{partes.port}" if partes.port else ""
        url_segura = f"{partes.scheme}://{host}{porta}" if host else ""
    except (TypeError, ValueError):
        url_segura = ""
    return titulo_seguro, url_segura


class ComposicaoContextosIARuntime:
    """Mantém uma mente viva por trás de contratos estáticos e auditáveis."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        base_system_prompt: str,
        servicos: Mapping[str, Any],
        messages_getter: Callable[[], Any],
        conversa_getter: Callable[[str, Any], Any],
        mente_getter: Callable[[], Mapping[str, Any]],
        aba_getter: Callable[[], tuple[str, str]],
        musica_leitura: PortaMusicaLeitura,
        musica_operacoes: PortaMusicaOperacoes,
        navegador_leitura: PortaNavegadorLeitura,
        navegador_operacoes: PortaNavegadorOperacoes,
        visao_jogo_leitura: PortaVisaoJogoLeitura,
        visao_jogo_analise: PortaVisaoJogoAnalise,
        modelo_llm: PortaModeloLLM,
        gmail_cache_getter: Callable[[], Any],
        falhas_getter: Callable[[], Mapping[str, Any]],
        verificar_fala_turno: Callable[..., Any],
        executar_conteudo_cb: Callable[..., bool],
        mapa_habilidades_prompt: Callable[..., str] | None = None,
        mapa_recursos_prompt: Callable[[str], str] | None = None,
        registrar_tamanho_prompt: Callable[[str, int], Any] | None = None,
        otimizacao_prompt_ativa: bool = True,
        registrar_falha: Callable[..., Any] | None = None,
        prompt_factory: Callable[..., Any] = criar_contexto_prompt_runtime,
        exec_factory: Callable[..., Any] = criar_contexto_exec_runtime,
        dispatcher_factory: Callable[..., Any] = criar_contexto_dispatcher_runtime,
        finalizacao_factory: Callable[..., Any] = criar_contexto_finalizacao_runtime,
        log: Callable[..., Any] = print,
    ) -> None:
        self._servicos = dict(servicos or {})
        self.messages_getter = messages_getter
        self.conversa_getter = conversa_getter
        self.mente_getter = mente_getter
        self.aba_getter = aba_getter
        self.musica_leitura = registrar_musica_leitura(musica_leitura)
        self.musica_operacoes = registrar_operacoes_musicais(musica_operacoes)
        self.navegador_leitura = registrar_navegador_leitura(navegador_leitura)
        self.navegador_operacoes = registrar_navegador_operacoes(navegador_operacoes)
        self.visao_jogo_leitura = registrar_visao_jogo_leitura(visao_jogo_leitura)
        self.visao_jogo_analise = registrar_visao_jogo_analise(visao_jogo_analise)
        self.modelo_llm = registrar_modelo_llm(modelo_llm)
        self.gmail_cache_getter = gmail_cache_getter
        self.falhas_getter = falhas_getter

        self.prompt: PortaPreparacaoConversa = registrar_preparacao_conversa(prompt_factory(
            memoria_sqlite=memoria_sqlite,
            resumo_mente_integrada=self._obter("_resumo_mente_integrada_para_prompt"),
            formatar_playlists=self.musica_leitura.formatar_prompt,
            get_status_humor_prompt=self._obter("get_status_humor_prompt"),
            base_system_prompt=base_system_prompt,
            estado_getter=self._estado_prompt,
            mapa_habilidades_prompt=mapa_habilidades_prompt,
            mapa_recursos_prompt=mapa_recursos_prompt,
            registrar_tamanho_prompt=registrar_tamanho_prompt,
            otimizacao_prompt_ativa=otimizacao_prompt_ativa,
        ))
        execucao = self._grupo(_EXECUCAO)
        execucao["_registro_musica_leitura_runtime"] = self.musica_leitura
        execucao["_registro_musica_operacoes_runtime"] = self.musica_operacoes
        execucao["_registro_navegador_leitura_runtime"] = self.navegador_leitura
        execucao["_registro_navegador_operacoes_runtime"] = self.navegador_operacoes
        execucao["_registro_visao_jogo_leitura_runtime"] = self.visao_jogo_leitura
        execucao["_registro_visao_jogo_analise_runtime"] = self.visao_jogo_analise
        self.execucao = exec_factory(
            contexto_getter=lambda: dict(execucao),
            executar_conteudo_cb=executar_conteudo_cb,
            log=log,
        )
        grupos = {
            nome: self._grupo(chaves)
            for nome, chaves in _DISPATCHER_GRUPOS.items()
        }
        grupos["navegacao"]["_registro_navegador_leitura_runtime"] = self.navegador_leitura
        grupos["navegacao"]["_registro_navegador_operacoes_runtime"] = self.navegador_operacoes
        grupos["percepcao"] = {
            "_executar_captura_tela_intent": lambda destino: self._obter(
                "_executar_captura_tela_intent"
            )(destino, registrar_memoria=True),
            "_registro_visao_jogo_leitura_runtime": self.visao_jogo_leitura,
            "_registro_visao_jogo_analise_runtime": self.visao_jogo_analise,
        }
        self.dispatcher = dispatcher_factory(
            **grupos,
            estado_getter=self._estado_dispatcher,
            registrar_falha=registrar_falha,
        )
        finalizacao = {
            nome: self._grupo(chaves)
            for nome, chaves in _FINALIZACAO_GRUPOS.items()
        }
        finalizacao["ia"]["modelo_llm"] = self.modelo_llm
        finalizacao["voz_memoria"]["verificar_fala_turno"] = verificar_fala_turno
        self.finalizacao = finalizacao_factory(
            **finalizacao,
            estado_getter=self._estado_finalizacao,
            registrar_falha=registrar_falha,
        )

        usados = {
            "_resumo_mente_integrada_para_prompt",
            "get_status_humor_prompt", "_executar_captura_tela_intent",
        }
        usados.update(_EXECUCAO)
        for grupo in (*_DISPATCHER_GRUPOS.values(), *_FINALIZACAO_GRUPOS.values()):
            usados.update(grupo)
        self._servicos = {
            nome: self._servicos[nome] for nome in usados if nome in self._servicos
        }

    def _obter(self, nome: str) -> Any:
        if nome not in self._servicos:
            raise RuntimeError(f"serviço obrigatório ausente no contexto da IA: {nome}")
        return self._servicos[nome]

    def _grupo(self, nomes: tuple[str, ...]) -> dict[str, Any]:
        return {nome: self._obter(nome) for nome in nomes}

    def _estado_prompt(self) -> dict[str, Any]:
        titulo, url = self.aba_getter()
        titulo, url = _sanitizar_aba_para_prompt(titulo, url)
        mente = dict(self.mente_getter() or {})
        return {
            "messages": self.messages_getter(),
            "humor_level": self.conversa_getter("humor_level", 0),
            "aba_titulo_atual": titulo,
            "aba_url_atual": url,
            "turno_atual": dict(mente.get("turno_atual") or {}),
            "contrato_fala_atual": dict(mente.get("contrato_fala_atual") or {}),
            "nome_usuario": str(mente.get("nome_usuario") or "").strip(),
        }

    def _estado_dispatcher(self) -> dict[str, Any]:
        return {
            "messages": self.messages_getter(),
            "current_emotion": self.conversa_getter("current_emotion", "calma"),
            "emotion_level": self.conversa_getter("emotion_level", 1),
            "playlists_carregadas": self.musica_leitura.indice_usuario(),
            "_gmail_nao_lidos_cache": self.gmail_cache_getter(),
        }

    def _estado_finalizacao(self) -> dict[str, Any]:
        return {
            "messages": self.messages_getter(),
            "current_emotion": self.conversa_getter("current_emotion", "calma"),
            "emotion_level": self.conversa_getter("emotion_level", 1),
            "_falhas_consecutivas": self.falhas_getter(),
        }

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))


def criar_composicao_contextos_ia_runtime(**kwargs: Any) -> ComposicaoContextosIARuntime:
    return ComposicaoContextosIARuntime(**kwargs)
