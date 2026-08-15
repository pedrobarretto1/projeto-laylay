"""Regressões P0.2A v4.1: fala com domínio e aba anterior real."""

from __future__ import annotations

# P0_NAVEGADOR_TESTES_V4_1_20260815

from dataclasses import dataclass
from typing import Any

from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    _executar_aba_anterior,
)
from mente_laylay.integracao.chrome_estado import ChromeEstadoRuntime
from mente_laylay.integracao.chrome_ws_handlers import handle_action
from mente_laylay.integracao.navegador_runtime import NavegadorLeituraRuntime
from mente_laylay.integracao.registro_navegador import registrar_navegador_leitura
from mente_laylay.personalidade.higiene_fala import limpar_fala_operacional


def test_volta_para_anterior_nao_apaga_fala_terminada_em_google_com() -> None:
    fala = "Voltei para no navegador nao pesquise nada - Pesquisa Google — google.com."
    assert limpar_fala_operacional(fala) == fala


def test_higiene_preserva_dominio_com_br_e_continua_removendo_conector_solto() -> None:
    assert (
        limpar_fala_operacional("Voltei para Notícias — globo.com.br.")
        == "Voltei para Notícias — globo.com.br."
    )
    assert limpar_fala_operacional("Eu estava falando com.") == ""


def _aplicar_evento(
    estado: ChromeEstadoRuntime,
    *,
    tab_id: int,
    titulo: str,
    url: str,
) -> dict[str, Any]:
    updates = handle_action(
        {
            "action": "active_tab_changed",
            "tabId": tab_id,
            "title": titulo,
            "url": url,
        },
        estado.contexto_handler(),
    )
    estado.aplicar_updates(updates)
    return updates


def test_active_tab_changed_guarda_a_aba_que_realmente_perdeu_o_foco() -> None:
    estado = ChromeEstadoRuntime()

    _aplicar_evento(
        estado, tab_id=1, titulo="Pesquisa Google", url="https://google.com/",
    )
    _aplicar_evento(
        estado, tab_id=2, titulo="Wikipédia", url="https://pt.wikipedia.org/",
    )
    _aplicar_evento(
        estado, tab_id=3, titulo="Prime Video", url="https://primevideo.com/",
    )

    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 3
    assert retrato["aba_anterior_id"] == 2


def test_evento_repetido_na_mesma_aba_nao_destroi_o_historico() -> None:
    estado = ChromeEstadoRuntime()
    _aplicar_evento(estado, tab_id=1, titulo="Google", url="https://google.com/")
    _aplicar_evento(
        estado, tab_id=2, titulo="Wikipédia", url="https://pt.wikipedia.org/",
    )
    _aplicar_evento(
        estado, tab_id=3, titulo="Prime Video", url="https://primevideo.com/",
    )

    _aplicar_evento(
        estado,
        tab_id=3,
        titulo="Prime Video - detalhe",
        url="https://primevideo.com/detail",
    )
    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 3
    assert retrato["aba_anterior_id"] == 2


def test_identidade_da_aba_muda_historico_mesmo_com_titulo_e_url_iguais() -> None:
    estado = ChromeEstadoRuntime()
    _aplicar_evento(
        estado, tab_id=10, titulo="Nova guia", url="https://example.com/",
    )
    _aplicar_evento(
        estado, tab_id=11, titulo="Nova guia", url="https://example.com/",
    )
    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 11
    assert retrato["aba_anterior_id"] == 10


class _SolicitacoesFake:
    def conectado(self) -> bool:
        return True

    def solicitar_aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        return {"tabId": 3, "title": "Prime Video", "url": "https://primevideo.com/"}


class _AmbienteFake:
    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return []


def test_porta_leitura_expoe_historico_existente_sem_torna_lo_obrigatorio() -> None:
    estado = ChromeEstadoRuntime()
    estado.aplicar_updates({"aba_ativa_id": 3, "aba_anterior_id": 2})
    runtime = NavegadorLeituraRuntime(
        solicitacoes=_SolicitacoesFake(),
        ambiente=_AmbienteFake(),
        estado=estado,
    )
    registro = registrar_navegador_leitura(runtime)
    assert registro.aba_anterior_id() == 2

    class _ServicoLegado:
        def conectado(self) -> bool:
            return True

        def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
            return {}

        def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
            return []

        def diagnostico(self) -> dict[str, Any]:
            return {}

    legado = registrar_navegador_leitura(_ServicoLegado())
    assert legado.aba_anterior_id() is None


@dataclass
class _LeituraExecutorFake:
    anterior: int | None
    ativo: int = 3

    def conectado(self) -> bool:
        return True

    def aba_anterior_id(self) -> int | None:
        return self.anterior

    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        titulos = {
            1: ("Google", "https://google.com/"),
            2: ("Wikipédia", "https://pt.wikipedia.org/"),
            3: ("Prime Video", "https://primevideo.com/"),
        }
        titulo, url = titulos[self.ativo]
        return {
            "tabId": self.ativo,
            "windowId": 7,
            "active": True,
            "title": titulo,
            "url": url,
        }

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        # Google tem lastAccessed maior de propósito. O histórico canônico
        # precisa vencer essa heurística e escolher Wikipédia (id=2).
        return [
            {
                "id": 1, "windowId": 7, "active": False,
                "title": "Google", "url": "https://google.com/",
                "lastAccessed": 9999,
            },
            {
                "id": 2, "windowId": 7, "active": False,
                "title": "Wikipédia", "url": "https://pt.wikipedia.org/",
                "lastAccessed": 100,
            },
            {
                "id": 3, "windowId": 7, "active": True,
                "title": "Prime Video", "url": "https://primevideo.com/",
                "lastAccessed": 500,
            },
        ]


class _OperacoesExecutorFake:
    def __init__(self, leitura: _LeituraExecutorFake) -> None:
        self.leitura = leitura
        self.focados: list[int] = []

    def focar_aba(self, tab_id: int) -> bool:
        self.focados.append(tab_id)
        self.leitura.ativo = tab_id
        return True


def _deps_executor(resultados: list[dict[str, Any]]) -> DependenciasExecutorNavegador:
    def marcar_resultado(status: str, **dados: Any) -> None:
        resultados.append({"status": status, **dados})

    return DependenciasExecutorNavegador(
        marcar_resultado=marcar_resultado,
        falar_por_status=lambda *_args, **_kwargs: None,
        abrir_url_com_validacao=lambda *_args, **_kwargs: False,
        alvo_preciso_para_aba=lambda valor: str(valor),
        esperar_aba_fechar=lambda *_args, **_kwargs: False,
        esperar_programa_fechar=lambda *_args, **_kwargs: False,
        executar_recursivo=lambda *_args, **_kwargs: False,
    )


def test_volta_para_a_anterior_prefere_historico_canonico_a_last_accessed() -> None:
    leitura = _LeituraExecutorFake(anterior=2)
    operacoes = _OperacoesExecutorFake(leitura)
    resultados: list[dict[str, Any]] = []
    falas: list[str] = []

    retorno = _executar_aba_anterior(
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
            "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
        },
        _deps_executor(resultados),
    )

    assert retorno.tratado is True
    assert operacoes.focados == [2]
    assert resultados[-1]["status"] == "aba_anterior_focada"
    assert resultados[-1]["confirmado"] is True
    assert falas == ["Voltei para Wikipédia — pt.wikipedia.org."]


def test_sem_historico_canonico_last_accessed_permanece_fallback_compativel() -> None:
    leitura = _LeituraExecutorFake(anterior=None)
    operacoes = _OperacoesExecutorFake(leitura)
    resultados: list[dict[str, Any]] = []

    retorno = _executar_aba_anterior(
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
            "falar_com_lipsync": lambda *_args: None,
        },
        _deps_executor(resultados),
    )

    assert retorno.tratado is True
    assert operacoes.focados == [1]
    assert resultados[-1]["status"] == "aba_anterior_focada"
