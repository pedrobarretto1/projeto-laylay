from __future__ import annotations

from collections import UserDict
import threading

import pytest

from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


def _estado() -> EstadoCompartilhadoRuntime:
    return EstadoCompartilhadoRuntime(
        mental={"geracao": 1, "dados": {"itens": ["original"]}},
        conversacional={"geracao": 1, "current_emotion": "calma"},
    )


def _transacao(estado: EstadoCompartilhadoRuntime):
    atualizar = getattr(estado, "atualizar_dominios", None)
    assert callable(atualizar), "o estado compartilhado precisa oferecer commit conjunto de domínios"
    return atualizar


def test_transacao_publica_dominios_canonicos_com_aliases() -> None:
    estado = _estado()
    recebidos = []

    def derivar(retratos):
        recebidos.append(set(retratos))
        retratos["mental"]["geracao"] = 2
        retratos["conversacional"]["geracao"] = 2
        return UserDict({nome: UserDict(dados) for nome, dados in retratos.items()})

    assert _transacao(estado)(("mente", "conversa"), derivar) is True
    assert recebidos == [{"mental", "conversacional"}]
    snapshot = estado.snapshot()
    assert snapshot["mental"]["geracao"] == snapshot["conversacional"]["geracao"] == 2
    assert snapshot["mental"]["pendencia_acao_canonica"] == {}


@pytest.mark.parametrize("recusa", [None, {}])
def test_recusa_nao_publica_mutacoes_do_snapshot_isolado(recusa) -> None:
    estado = _estado()
    antes = estado.snapshot()

    def recusar(retratos):
        retratos["mental"]["dados"]["itens"].append("candidato")
        retratos["conversacional"]["current_emotion"] = "envergonhada"
        return recusa

    assert _transacao(estado)(("mental", "conversacional"), recusar) is False
    assert estado.snapshot() == antes


def test_excecao_no_callback_nao_publica_mutacao_isolada() -> None:
    estado = _estado()
    antes = estado.snapshot()

    def falhar(retratos):
        retratos["mental"]["dados"]["itens"].clear()
        raise RuntimeError("falha na derivação")

    with pytest.raises(RuntimeError, match="falha na derivação"):
        _transacao(estado)(("mental", "conversacional"), falhar)
    assert estado.snapshot() == antes


@pytest.mark.parametrize("dominios,erro", [
    (("mental", "mente"), ValueError),
    (("desconhecido", "conversacional"), KeyError),
    (("mental", 42), TypeError),
    ((), ValueError),
    ("mental", TypeError),
])
def test_dominios_invalidos_abortam_antes_do_callback(dominios, erro) -> None:
    estado = _estado()
    antes = estado.snapshot()
    chamadas = []
    atualizar = _transacao(estado)
    with pytest.raises(erro):
        atualizar(dominios, lambda retratos: chamadas.append(retratos))
    assert chamadas == []
    assert estado.snapshot() == antes


@pytest.mark.parametrize("retorno", [
    {"mental": {}},
    {"mental": {}, "conversacional": {}, "percepcao": {}},
    {"mente": {}, "conversa": {}},
    {"mental": {}, "conversacional": []},
    [],
    False,
])
def test_retorno_invalido_nao_produz_commit_parcial(retorno) -> None:
    estado = _estado()
    antes = estado.snapshot()
    atualizar = _transacao(estado)
    with pytest.raises((TypeError, ValueError)):
        atualizar(("mental", "conversacional"), lambda _retratos: retorno)
    assert estado.snapshot() == antes


def test_falha_na_preparacao_do_segundo_dominio_preserva_os_dois(monkeypatch) -> None:
    estado = _estado()
    antes = estado.snapshot()
    preparar_real = estado._preparar_dominio
    preparados = []

    def preparar(dados):
        preparados.append(dados["geracao"])
        if "current_emotion" in dados:
            raise RuntimeError("segundo domínio não preparável")
        return preparar_real(dados)

    atualizar = _transacao(estado)
    monkeypatch.setattr(estado, "_preparar_dominio", preparar)
    with pytest.raises(RuntimeError, match="segundo domínio não preparável"):
        atualizar(("mental", "conversacional"), lambda retratos: {
            nome: {**dados, "geracao": 2} for nome, dados in retratos.items()
        })
    assert preparados == [2, 2], "o RED precisa alcançar a preparação do segundo domínio"
    assert estado.snapshot() == antes


def test_snapshot_concorrente_observa_commit_conjunto() -> None:
    estado = _estado()
    atualizar = _transacao(estado)
    antes = estado.snapshot()
    entrou = threading.Event()
    tentou_ler = threading.Event()
    liberar = threading.Event()
    leitura_concluida = threading.Event()
    leituras = []
    resultados = []

    def derivar(retratos):
        retratos["mental"]["geracao"] = 2
        entrou.set()
        assert liberar.wait(5), "o controle precisa liberar a transação"
        retratos["conversacional"]["geracao"] = 2
        return retratos

    def escrever():
        resultados.append(atualizar(("mental", "conversacional"), derivar))

    def ler():
        tentou_ler.set()
        leituras.append(estado.snapshot())
        leitura_concluida.set()

    escritor = threading.Thread(target=escrever)
    leitor = threading.Thread(target=ler)
    escritor.start()
    try:
        assert entrou.wait(5)
        leitor.start()
        assert tentou_ler.wait(5)
        assert not leitura_concluida.wait(0.05), "snapshot não pode atravessar um commit em preparação"
    finally:
        liberar.set()
        escritor.join(5)
        if leitor.ident is not None:
            leitor.join(5)

    assert not escritor.is_alive() and not leitor.is_alive()
    assert antes["mental"]["geracao"] == antes["conversacional"]["geracao"] == 1
    assert resultados == [True]
    assert len(leituras) == 1
    assert leituras[0]["mental"]["geracao"] == leituras[0]["conversacional"]["geracao"] == 2
