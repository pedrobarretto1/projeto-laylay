from __future__ import annotations

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
import mente_laylay.autonomia.roteador_intencao as roteador


EXECUTORES_NA_ORDEM = [
    "janelas",
    "navegador",
    "audio",
    "agenda",
    "informacoes",
    "sistema",
    "musical",
    "playlists",
    "cancelamentos",
    "integracoes",
]


def _substituir_executores(monkeypatch, chamadas: list[str], tratado: str = "") -> None:
    for nome in EXECUTORES_NA_ORDEM:
        def executar(*_args, _nome=nome, **_kwargs):
            chamadas.append(_nome)
            if _nome == tratado:
                return ResultadoDespacho.concluido()
            return ResultadoDespacho.nao_tratado()

        monkeypatch.setattr(roteador, f"_executar_intencao_{nome}", executar)


def test_roteador_percorre_executores_na_ordem_de_precedencia(monkeypatch) -> None:
    chamadas: list[str] = []
    falas: list[tuple] = []
    _substituir_executores(monkeypatch, chamadas)

    retorno = roteador.executar_intencao(
        {"intent": "INTENT_DESCONHECIDA", "params": {}},
        "pedido desconhecido",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
    )

    assert retorno is True
    assert chamadas == EXECUTORES_NA_ORDEM
    assert len(falas) == 1


def test_primeiro_executor_que_trata_interrompe_a_cadeia(monkeypatch) -> None:
    chamadas: list[str] = []
    _substituir_executores(monkeypatch, chamadas, tratado="sistema")

    retorno = roteador.executar_intencao(
        {"intent": "SCREEN_CAPTURE", "params": {}},
        "tira um print",
        {"_target_from_params": lambda *_args: "pc_a"},
    )

    assert retorno is True
    assert chamadas == [
        "janelas",
        "navegador",
        "audio",
        "agenda",
        "informacoes",
        "sistema",
    ]


def test_bloqueio_emocional_acontece_antes_de_qualquer_executor(monkeypatch) -> None:
    chamadas: list[str] = []
    _substituir_executores(monkeypatch, chamadas)

    retorno = roteador.executar_intencao(
        {"intent": "MUSIC_SEARCH", "params": {"query": "Duality"}},
        "toca Duality",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_bloqueio_por_emocao": lambda *_args: True,
        },
    )

    assert retorno is True
    assert chamadas == []
