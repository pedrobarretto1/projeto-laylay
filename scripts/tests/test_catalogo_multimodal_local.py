"""O catálogo visual reflete o backend local, sem converter leitura em efeito."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.composicao_inteligencia_externa import (
    ComposicaoInteligenciaExternaRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import EstadoConversaRuntime
from mente_laylay.integracao.registro_visao_jogo import (
    registrar_visao_jogo_analise,
    registrar_visao_jogo_leitura,
)
from mente_laylay.memoria_mental.disponibilidade_operacional import (
    DisponibilidadeOperacionalRuntime,
)
from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
from mente_laylay.percepcao.visao_jogo.portas_runtime import (
    criar_visao_jogo_analise_runtime,
    criar_visao_jogo_leitura_runtime,
)
from mente_laylay.percepcao.visao_jogo.runtime import VisaoJogoRuntime


class _RespostaMetadados:
    def __init__(self, status: int, capacidades: list[str]) -> None:
        self.status_code = status
        self._capacidades = capacidades

    def json(self) -> dict[str, Any]:
        return {"capabilities": self._capacidades}


def _compor_catalogo(
    tmp_path: Path, *, status: int = 200, capacidades: list[str] | None = None,
    backend: str = "ollama", chave_gemini: str = "", gratuito: str = "0",
) -> dict[str, Any]:
    chamadas_http: list[tuple[str, dict[str, Any]]] = []
    capturas: list[dict[str, Any]] = []
    falas: list[tuple[Any, ...]] = []

    def post(url: str, **opcoes: Any) -> _RespostaMetadados:
        chamadas_http.append((url, opcoes))
        assert url == "http://localhost:11434/api/show", (
            "Consultar o catálogo não deve iniciar geração nem enviar imagens."
        )
        assert opcoes["json"] == {"model": "qwen3-vl:4b"}
        return _RespostaMetadados(status, capacidades or [])

    def get(*_args: Any, **_opcoes: Any) -> None:
        pytest.fail("Consultar capacidades não deve iniciar pesquisa externa.")

    composicao = ComposicaoInteligenciaExternaRuntime(
        base_url="http://localhost:11434/v1",
        model="qwen3-vl:4b",
        api_key="ollama",
        http_referer="http://localhost",
        app_title="Laylay",
        normalizar_texto_curto=str.casefold,
        requests_get=get,
        requests_post=post,
        ao_finalizar_conversa_modo_jogo=lambda: None,
        env_getter=lambda nome, padrao="": {
            "LAYLAY_VISAO_BACKEND": backend,
            "GEMINI_API_KEY": chave_gemini,
            "LAYLAY_GEMINI_FREE_TIER_CONFIRMADO": gratuito,
            "LAYLAY_VISAO_MODEL": "qwen3-vl:4b",
            "GROQ_API_KEY": "",
            "LAYLAY_CONVERSA_JOGO_REMOTA_ATIVA": "0",
        }.get(nome, padrao),
        log=lambda *_args: None,
    )
    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path / "resumo"),
        enviar_mensagem=lambda mensagens: composicao.cliente.enviar(mensagens),
        log=lambda *_args: None,
    )
    modelo = composicao.conectar_cliente(
        memoria_inteligente=memoria,
        normalizar_texto=str.casefold,
        mapear_pastas=lambda: {},
        contexto_logs_getter=lambda: [],
        contexto_navegador_relevante=lambda *_args: False,
        contexto_sistema_getter=lambda: {},
        obter_contexto_paginas=lambda: "",
        resumo_mente_integrada=lambda: "",
    )
    mensagens: list[dict[str, Any]] = []
    estado = EstadoConversaRuntime(
        getter=lambda: mensagens,
        setter=lambda novas: mensagens.__setitem__(slice(None), novas),
    )

    def diagnostico_conversa() -> dict[str, Any]:
        diagnostico = modelo.diagnostico()
        return {
            **diagnostico,
            "modelo_disponivel": diagnostico["disponivel"],
            "estado_disponivel": estado.diagnostico()["disponivel"],
        }

    def capturar(contexto: Any) -> str:
        capturas.append(dict(contexto))
        pytest.fail("Percepção e catálogo não autorizam uma captura nova.")

    visao = VisaoJogoRuntime(
        contexto_jogo=lambda: {"ativo": True, "titulo": "Meu Jogo", "hwnd": 0},
        analisar_imagem=composicao.analisar_imagem_jogo,
        sintetizar_texto=composicao.sintetizar_pesquisa_jogo,
        credencial_disponivel=composicao.credencial_visual_disponivel,
        capturar=capturar,
        falar=lambda *args: falas.append(args),
        log=lambda *_args: None,
    )
    leitura = registrar_visao_jogo_leitura(criar_visao_jogo_leitura_runtime(visao=visao))
    analise = registrar_visao_jogo_analise(criar_visao_jogo_analise_runtime(visao=visao))
    disponibilidade = DisponibilidadeOperacionalRuntime(
        conversa_llm_getter=diagnostico_conversa,
        visao_leitura_getter=leitura.diagnostico,
        visao_analise_getter=analise.diagnostico,
    )
    mapa = MapaHabilidadesRuntime(operacional_getter=disponibilidade.snapshot)
    return {
        "composicao": composicao, "modelo": modelo, "mapa": mapa,
        "leitura": leitura, "analise": analise,
        "http": chamadas_http, "capturas": capturas, "falas": falas,
    }


@pytest.mark.parametrize("chave,gratuito,disponivel", [
    ("chave-teste", "1", True), ("", "1", False), ("chave-teste", "0", False),
])
def test_catalogo_gemini_reflete_configuracao_sem_capturar_ou_enviar(
    tmp_path: Path, chave: str, gratuito: str, disponivel: bool,
) -> None:
    componentes = _compor_catalogo(tmp_path, backend="gemini", chave_gemini=chave, gratuito=gratuito)
    mapa = componentes["mapa"]
    for intent in ("GAME_VISION", "VISION_QUERY"):
        assert mapa.consultar(intent)["disponivel"] is disponivel
    pergunta = "Você consegue acompanhar o jogo e comentar o que aparece na tela?"
    turno = classificar_modalidade_turno(pergunta)
    assert mapa.evidencia_conversacional(pergunta, turno=turno)["autoriza_execucao"] is False
    resposta = mapa.responder_pergunta_capacidade(pergunta)
    assert resposta
    if not disponivel:
        assert "indisponível" in resposta.casefold() or "não está disponível" in resposta.casefold()
    assert componentes["http"] == []
    assert componentes["capturas"] == []
    assert componentes["falas"] == []


def _conferir_sem_efeitos(componentes: dict[str, Any]) -> None:
    assert len(componentes["http"]) == 1  # Apenas o metadado do modelo local.
    assert componentes["capturas"] == []
    assert componentes["falas"] == []
    assert componentes["modelo"].diagnostico()["requisicoes"] == 0
    assert componentes["analise"].diagnostico()["solicitacoes"] == 0
    for registro in (componentes["leitura"], componentes["analise"]):
        assert registro.diagnostico()["autoriza_execucao"] is False
    assert componentes["leitura"].diagnostico()["captura_persistida"] is False


def test_composicao_local_sem_groq_publica_visao_e_conversa_no_catalogo(tmp_path: Path) -> None:
    componentes = _compor_catalogo(tmp_path, capacidades=["completion", "vision"])
    composicao = componentes["composicao"]
    mapa = componentes["mapa"]

    assert composicao.groq_api_key == ""
    assert composicao.credencial_visual_disponivel is True
    assert mapa.snapshot()["dominios"]["visao"]["estado"] == "disponivel"
    assert mapa.snapshot()["dominios"]["conversa"]["estado"] == "disponivel"
    for intent in ("GAME_VISION", "VISION_QUERY"):
        assert mapa.consultar(intent)["disponivel"] is True

    for pergunta in (
        "Lay, você consegue analisar um item do jogo para a minha build?",
        "Você consegue acompanhar o jogo e comentar o que aparece na tela?",
        "Lay, você consegue conversar e explicar coisas?",
    ):
        turno = classificar_modalidade_turno(pergunta)
        antes = deepcopy(turno)
        assert turno["autoriza_execucao"] is False
        evidencia = mapa.evidencia_conversacional(pergunta, turno=turno)
        assert evidencia["autoriza_execucao"] is False
        assert turno == antes
        resposta = mapa.responder_pergunta_capacidade(pergunta)
        assert resposta and "indisponível" not in resposta.casefold()
    assert "- visao [disponivel]" in mapa.contexto_para_prompt("você consegue analisar um item do jogo?")
    assert "- conversa [disponivel]" in mapa.contexto_para_prompt("você consegue conversar?")

    componentes["leitura"].observar_texto_usuario("ainda estou no menu")
    _conferir_sem_efeitos(componentes)


@pytest.mark.parametrize(
    "status,capacidades", [(200, ["completion"]), (404, ["completion", "vision"])],
    ids=["modelo_sem_visao", "metadados_indisponiveis"],
)
def test_catalogo_nao_promete_visao_sem_metadados_locais_validos(
    tmp_path: Path, status: int, capacidades: list[str],
) -> None:
    componentes = _compor_catalogo(tmp_path, status=status, capacidades=capacidades)
    composicao = componentes["composicao"]
    mapa = componentes["mapa"]

    assert composicao.groq_api_key == ""
    assert composicao.credencial_visual_disponivel is False
    assert mapa.snapshot()["dominios"]["visao"]["estado"] == "indisponivel"
    for intent in ("GAME_VISION", "VISION_QUERY"):
        assert mapa.consultar(intent)["disponivel"] is False
    for pergunta in (
        "Lay, você consegue analisar um item do jogo para a minha build?",
        "Você consegue acompanhar o jogo e comentar o que aparece na tela?",
    ):
        turno = classificar_modalidade_turno(pergunta)
        assert turno["autoriza_execucao"] is False
        assert mapa.evidencia_conversacional(pergunta, turno=turno)["autoriza_execucao"] is False
        assert "- visao [indisponivel]" in mapa.contexto_para_prompt(pergunta)
        resposta = mapa.responder_pergunta_capacidade(pergunta)
        assert "não está disponível" in resposta.casefold() or "indisponível" in resposta.casefold()
    componentes["leitura"].observar_texto_usuario("ainda estou no menu")
    _conferir_sem_efeitos(componentes)
