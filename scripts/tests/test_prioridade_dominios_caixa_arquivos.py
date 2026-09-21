"""RED dos turnos 085/089 — Caixa de Entrada x domínio de Arquivos.

Snapshot de produção estudado:
    81f398542dd1c64ed20e19ad7007ddfe4acf6003  ("teste 4.4")

Objetivo
--------
Provar a primeira fronteira RED sem tocar em arquivos reais:

1. O roteador canônico de arquivos já reconhece as falas problemáticas como
   DELETE_ITEM.
2. A fase prioritária NÃO pode entregar essas mesmas falas para a Caixa de
   Entrada só porque palavras como "ideia", "nota" ou "tarefa" aparecem dentro
   de um filename ou de uma moldura tipada de filesystem.
3. A Caixa de Entrada deve continuar sendo dona de "Apaga essa ideia." e deve
   manter o soft-delete com confirmação.

Este arquivo é propositalmente RED no snapshot acima. Não altere as expectativas
para "acompanhar" o comportamento atual: o objetivo é travar a raiz antes do
patch de produção.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

import pytest

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.especialistas.caixa_entrada_pessoal import (
    CaixaEntradaPessoalRuntime,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


SNAPSHOT_PRODUCAO = "81f398542dd1c64ed20e19ad7007ddfe4acf6003"


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _criar_caixa(tmp_path):
    falas: list[str] = []
    resultados: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    estado: dict[str, Any] = {}
    instante = dt.datetime(2026, 8, 22, 18, 30, 45)

    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        agora=lambda: instante.timestamp(),
        log=lambda *_args: None,
    )
    caixa = CaixaEntradaPessoalRuntime(
        caminho=tmp_path / "caixa.json",
        falar=lambda fala, *_args: falas.append(str(fala)),
        registrar_resultado=lambda *args, **kwargs: resultados.append(
            (args, kwargs)
        ),
        executar_intencao=lambda *_args, **_kwargs: True,
        contexto_getter=lambda: {"messages": []},
        clipboard_getter=lambda: "",
        pendencia_runtime=pendencia,
        agora=lambda: instante,
        log=lambda *_args: None,
    )
    return caixa, pendencia, falas, resultados


def _runtime_prioritario(caixa: CaixaEntradaPessoalRuntime) -> ComandosImediatosRuntime:
    """Composição real Caixa + fase prioritária, sem executor de arquivos.

    Se a Caixa ceder corretamente, a fase prioritária deve devolver False e
    permitir que o fluxo canônico posterior resolva o DELETE_ITEM. Nenhum mock
    substitui a Caixa que está sendo testada.
    """
    return ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_caixa_entrada_pessoal_runtime": caixa,
        },
        loop_getter=lambda: None,
    )


def _itens_caixa(tmp_path) -> list[dict[str, Any]]:
    caminho = tmp_path / "caixa.json"
    if not caminho.exists():
        return []
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [
        dict(item)
        for item in list(dados.get("itens") or [])
        if isinstance(item, dict)
    ]


CASOS_ARQUIVO_TIPADO = [
    (
        "Apaga o troca ideia.txt.",
        "troca ideia.txt",
        "",
    ),
    (
        "Apaga o ideias.md.",
        "ideias.md",
        "",
    ),
    (
        "Apaga o arquivo tarefa.",
        "tarefa.txt",
        "arquivo",
    ),
    (
        "Apaga a pasta ideia.",
        "ideia",
        "pasta",
    ),
]


@pytest.mark.parametrize(
    ("fala", "alvo_esperado", "tipo_esperado"),
    CASOS_ARQUIVO_TIPADO,
)
def test_guard_roteador_arquivos_ja_entende_o_alvo_tipado(
    fala: str,
    alvo_esperado: str,
    tipo_esperado: str,
) -> None:
    """GREEN guard: o defeito não nasce no parser de DELETE_ITEM."""
    resultado = detectar_intencao_arquivos(
        fala,
        params_cb=lambda **params: params,
        estado_mental={},
        normalizar_texto=_normalizar,
    )

    assert resultado is not None
    assert resultado["intent"] == "DELETE_ITEM"
    assert resultado["params"]["alvo"] == alvo_esperado
    if tipo_esperado:
        assert resultado["params"]["tipo"] == tipo_esperado


def test_red_085_089_filename_ideia_nao_pode_ser_consumido_pela_caixa_vazia(
    tmp_path,
) -> None:
    """Reprodução mínima dos turnos 085/089 do caos."""
    caixa, pendencia, falas, _ = _criar_caixa(tmp_path)
    runtime = _runtime_prioritario(caixa)

    tratado = runtime.processar_prioritarios("Apaga o troca ideia.txt.")

    # RED no snapshot 4.4:
    # hoje a Caixa responde "Não encontrei uma nota ativa..." e retorna True.
    # O comportamento correto é ceder o turno para o fluxo de arquivos.
    assert tratado is False
    assert pendencia.obter() in (None, {})
    assert not any("nota ativa" in fala.casefold() for fala in falas)


@pytest.mark.parametrize(
    ("fala", "_alvo_esperado", "_tipo_esperado"),
    CASOS_ARQUIVO_TIPADO,
)
def test_red_evidencia_tipificada_de_arquivo_vence_palavra_semantica_da_caixa(
    tmp_path,
    fala: str,
    _alvo_esperado: str,
    _tipo_esperado: str,
) -> None:
    """Safety RED: uma nota real não pode virar alvo por causa do filename."""
    caixa, pendencia, falas, _ = _criar_caixa(tmp_path)

    assert caixa.processar(
        "anota essa ideia: NOTA SENTINELA QUE NAO PODE SER APAGADA"
    ) is True
    itens_antes = _itens_caixa(tmp_path)
    assert len(itens_antes) == 1
    assert itens_antes[0]["status"] == "ativo"

    falas.clear()
    runtime = _runtime_prioritario(caixa)
    tratado = runtime.processar_prioritarios(fala)

    # A prioridade deve dizer apenas "não sou dona deste turno".
    assert tratado is False

    # Principal barreira de segurança: nenhum pedido de exclusão da Caixa foi
    # armado por causa de "ideia"/"nota"/"tarefa" dentro do alvo de arquivo.
    pendencia_atual = pendencia.obter()
    assert not (
        isinstance(pendencia_atual, dict)
        and pendencia_atual.get("origem") == "caixa_entrada_pessoal"
        and pendencia_atual.get("acao") == "excluir_nota"
    )

    itens_depois = _itens_caixa(tmp_path)
    assert len(itens_depois) == 1
    assert itens_depois[0]["status"] == "ativo"
    assert (
        itens_depois[0]["conteudo"]
        == "NOTA SENTINELA QUE NAO PODE SER APAGADA"
    )
    assert not any("Confirma que quer enviar essa nota" in fala for fala in falas)


def test_guard_apaga_essa_ideia_continua_sendo_da_caixa_e_exige_confirmacao(
    tmp_path,
) -> None:
    """GREEN safety guard: o patch não pode desativar a exclusão legítima."""
    caixa, pendencia, falas, _ = _criar_caixa(tmp_path)
    assert caixa.processar(
        "anota essa ideia: NOTA SENTINELA QUE PODE SER EXCLUIDA SE EU PEDIR"
    ) is True

    falas.clear()
    runtime = _runtime_prioritario(caixa)

    assert runtime.processar_prioritarios("Apaga essa ideia.") is True

    atual = pendencia.obter()
    assert isinstance(atual, dict)
    assert atual.get("origem") == "caixa_entrada_pessoal"
    assert atual.get("acao") == "excluir_nota"

    itens = _itens_caixa(tmp_path)
    assert len(itens) == 1
    # Soft delete só acontece depois do "sim".
    assert itens[0]["status"] == "ativo"
    assert any("Confirma" in fala for fala in falas)
