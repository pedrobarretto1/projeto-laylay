"""Regressões P0.2A v4.3: rótulo canônico preserva identidade da aba."""

from __future__ import annotations

# P0_NAVEGADOR_TESTES_V4_3_20260815

from typing import Any

from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    _executar_fechar_aba,
    _rotulo_aba,
    _selecionar_aba_observada,
)
from mente_laylay.autonomia.validacao_ambiente import ValidadorAmbiente


def _wikipedia(*, active: bool = True) -> dict[str, Any]:
    return {
        "id": 114,
        "tabId": 114,
        "windowId": 7,
        "active": active,
        "title": "Wikipédia, a enciclopédia livre",
        "url": "https://pt.wikipedia.org/",
        "lastAccessed": 100.0,
    }


def _prime(*, active: bool = False) -> dict[str, Any]:
    return {
        "id": 115,
        "tabId": 115,
        "windowId": 8,
        "active": active,
        "title": "Prime Video",
        "url": "https://www.primevideo.com/",
        "lastAccessed": 200.0,
    }


def test_rotulo_gerado_pela_propria_laylay_reencontra_a_mesma_aba() -> None:
    aba = _wikipedia()
    rotulo = _rotulo_aba(aba)
    assert rotulo == "Wikipédia, a enciclopédia livre — pt.wikipedia.org"
    selecionada = _selecionar_aba_observada([_prime(), aba], rotulo)
    assert selecionada["tabId"] == 114
    assert selecionada["url"] == "https://pt.wikipedia.org/"


def test_regressao_exata_target_composto_nao_perde_tab_id() -> None:
    alvo = "Wikipédia, a enciclopédia livre — pt.wikipedia.org"
    selecionada = _selecionar_aba_observada(
        [_wikipedia(active=True), _prime(active=False)], alvo
    )
    assert selecionada["tabId"] == 114


def test_match_legado_simples_continua_funcionando() -> None:
    abas = [
        {
            "id": 201,
            "tabId": 201,
            "active": True,
            "title": "3.14.7 Documentation",
            "url": "https://docs.python.org/3/",
        },
        _wikipedia(active=False),
    ]
    selecionada = _selecionar_aba_observada(abas, "python")
    assert selecionada["tabId"] == 201


def test_validador_preserva_rotulo_composto_quando_montador_vira_busca() -> None:
    alvo = "Wikipédia, a enciclopédia livre — pt.wikipedia.org"
    validador = ValidadorAmbiente(
        ctx={
            "_montar_url_site_ou_busca": lambda _valor: (
                "https://www.google.com/search?q="
                "Wikip%C3%A9dia%2C+a+enciclop%C3%A9dia+livre+%E2%80%94+pt.wikipedia.org"
            )
        }
    )
    assert validador.alvo_preciso_para_aba(alvo) == alvo


class _Leitura:
    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        return _wikipedia(active=True)

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return [_wikipedia(active=True), _prime(active=False)]


class _Operacoes:
    def __init__(self) -> None:
        self.fechamentos_por_id: list[list[int]] = []
        self.fechamentos_textuais: list[str] = []

    def fechar_abas(self, ids: list[int]) -> bool:
        self.fechamentos_por_id.append(list(ids))
        return True

    def fechar_aba(self, alvo: str) -> bool:
        self.fechamentos_textuais.append(str(alvo))
        return False

    def fechar_aba_atual(self) -> bool:
        raise AssertionError("o caso contextual deve ser reconciliado por tabId")


def _deps(resultados: list[dict[str, Any]]) -> DependenciasExecutorNavegador:
    return DependenciasExecutorNavegador(
        marcar_resultado=lambda status, **dados: resultados.append(
            {"status": status, **dados}
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        abrir_url_com_validacao=lambda *_args, **_kwargs: False,
        alvo_preciso_para_aba=lambda valor: str(valor),
        esperar_aba_fechar=lambda *_args, **_kwargs: False,
        esperar_programa_fechar=lambda *_args, **_kwargs: False,
        executar_recursivo=lambda *_args, **_kwargs: False,
    )


def test_fecha_essa_depois_de_voltar_para_wikipedia_fecha_por_tab_id() -> None:
    leitura = _Leitura()
    operacoes = _Operacoes()
    resultados: list[dict[str, Any]] = []
    alvo_contextual = _rotulo_aba(_wikipedia())

    retorno = _executar_fechar_aba(
        {"alvo": alvo_contextual},
        "Fecha essa.",
        "pc_a",
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
        },
        _deps(resultados),
    )

    assert retorno.tratado is True
    assert operacoes.fechamentos_por_id == [[114]]
    assert operacoes.fechamentos_textuais == []
    assert resultados[-1]["status"] == "aba_fechada"
    assert resultados[-1]["executou"] is True
    assert resultados[-1]["confirmado"] is True
    assert resultados[-1]["params_resolvidos"]["tab_id"] == 114


def test_outro_rotulo_canonico_tambem_faz_round_trip() -> None:
    aba = {
        "id": 300,
        "tabId": 300,
        "windowId": 12,
        "active": True,
        "title": "Exemplo de documentação",
        "url": "https://docs.exemplo.test/guia",
    }
    rotulo = _rotulo_aba(aba)
    assert _selecionar_aba_observada([aba], rotulo)["tabId"] == 300
