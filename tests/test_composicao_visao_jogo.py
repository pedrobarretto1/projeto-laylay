from __future__ import annotations

import pytest

from mente_laylay.percepcao.visao_jogo.composicao import (
    ComposicaoVisaoJogoRuntime,
)


class _PesquisaFake:
    def pesquisar_item(self, *_args, **_kwargs):
        return {}


class _VisaoFake:
    em_andamento = False

    def capturar(self, _contexto):
        return "imagem"

    def executar(self, _pedido):
        return True


def _montar(ambiente=None, **extras):
    criacoes = {}
    log = extras.pop("log", lambda *_: None)
    memoria = object()
    pesquisa = _PesquisaFake()
    visao = _VisaoFake()

    def factory(nome, retorno):
        def criar(*args, **kwargs):
            criacoes[nome] = {"args": args, "kwargs": kwargs}
            return retorno
        return criar

    runtime = ComposicaoVisaoJogoRuntime(
        db_path="memoria.sqlite",
        env_getter=lambda nome, padrao="": dict(ambiente or {}).get(nome, padrao),
        memoria_factory=factory("memoria", memoria),
        pesquisa_factory=factory("pesquisa", pesquisa),
        visao_factory=factory("visao", visao),
        observador_inventario_factory=factory("inventario", object()),
        observador_presenca_factory=factory("presenca", object()),
        sessoes_factory=factory("sessoes", object()),
        identificar_jogo_fn=lambda _contexto: {"chave": "path-of-exile-2"},
        log=log,
        **extras,
    )
    return runtime, criacoes


def _conectar(runtime, *, credencial=True):
    return runtime.conectar_visao(
        contexto_jogo=lambda: {"ativo": True},
        analisar_imagem=lambda *_: "análise",
        falar=lambda *_: None,
        sintetizar_texto=lambda texto: texto,
        ao_mapear_inventario=lambda *_: None,
        processar_sugestao_proativa=lambda *_: False,
        registrar_analise=lambda *_: None,
        credencial_disponivel=credencial,
        permitido_presenca=lambda: True,
        interacao_iniciada=lambda: True,
        stop_event=object(),
        progresso_cooperativo=lambda *_: None,
    )


def test_composicao_compartilha_memoria_sessao_visao_e_observadores() -> None:
    runtime, criacoes = _montar(ambiente={
        "LAYLAY_JOGO_PROATIVO_INTERVALO": "30",
        "LAYLAY_JOGO_PROATIVO_DURACAO": "900",
        "LAYLAY_JOGO_PROATIVO_MAX_ANALISES": "9",
        "LAYLAY_PRESENCA_VISUAL_INTERVALO": "75",
        "LAYLAY_PRESENCA_VISUAL_MAX": "4",
    })

    assert _conectar(runtime) is runtime.visao
    assert criacoes["sessoes"]["kwargs"]["memoria"] is runtime.memoria
    assert criacoes["visao"]["kwargs"]["memoria_jogos"] is runtime.memoria
    assert criacoes["visao"]["kwargs"]["pesquisar_item"] == runtime.pesquisa.pesquisar_item
    assert callable(criacoes["visao"]["kwargs"]["progresso_cooperativo_cb"])
    inventario = criacoes["inventario"]["kwargs"]
    presenca = criacoes["presenca"]["kwargs"]
    assert inventario["capturar"] == runtime.visao.capturar
    assert inventario["intervalo_s"] == 30.0
    assert inventario["duracao_s"] == 900.0
    assert inventario["max_analises"] == 9
    assert inventario["jogo_chave_atual"]({}) == "path-of-exile-2"
    assert presenca["intervalo_s"] == 75.0
    assert presenca["max_analises_sessao"] == 4
    assert presenca["janela_analises_s"] == 900.0
    assert presenca["habilitado"] is True


def test_composicao_desliga_presenca_sem_credencial_visual() -> None:
    runtime, criacoes = _montar()
    _conectar(runtime, credencial=False)

    assert criacoes["visao"]["kwargs"]["credencial_disponivel"] is False
    assert criacoes["presenca"]["kwargs"]["habilitado"] is False


def test_composicao_corrige_configuracoes_numericas_invalidas() -> None:
    falhas, logs = [], []
    runtime, criacoes = _montar(
        ambiente={
            "LAYLAY_JOGO_PROATIVO_INTERVALO": "rápido",
            "LAYLAY_JOGO_PROATIVO_MAX_ANALISES": "muitas",
            "LAYLAY_PRESENCA_VISUAL_INTERVALO": "depois",
        },
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=logs.append,
    )
    _conectar(runtime)

    assert criacoes["inventario"]["kwargs"]["intervalo_s"] == 25.0
    assert criacoes["inventario"]["kwargs"]["max_analises"] == 12
    assert criacoes["presenca"]["kwargs"]["intervalo_s"] == 35.0
    assert len(falhas) == 3
    assert len(logs) == 3


def test_composicao_exige_conexao_antes_dos_observadores() -> None:
    runtime, _ = _montar()
    with pytest.raises(RuntimeError, match="ainda não conectada"):
        _ = runtime.visao
    with pytest.raises(RuntimeError, match="ainda não conectado"):
        _ = runtime.observador_inventario
