"""Regressão física da exclusão segura de arquivos.

Este teste não usa os números dos turnos como contrato. Ele valida a arquitetura:

fala natural
→ DELETE_ITEM canônico com basename exato
→ executor real de arquivos
→ ArquivosMutacaoRuntime real
→ LixeiraLaylay real
→ confirmação pendente
→ CONFIRM_DELETE_ITEM
→ movimento físico para a lixeira isolada
→ RESTORE_DELETED_ITEM
→ restauração física do arquivo

A busca/resolução é deliberadamente confinada ao ``tmp_path`` do pytest para
que nenhum arquivo real do usuário possa ser selecionado durante a regressão.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.arquivos.lixeira_laylay import LixeiraLaylay
from mente_laylay.arquivos.mutacoes import ArquivosMutacaoRuntime
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


@pytest.fixture
def ambiente_exclusao(tmp_path):
    """Monta produção real abaixo da fronteira de descoberta do fixture."""
    area = tmp_path / "arquivos"
    area.mkdir()
    raiz_lixeira = tmp_path / "lixeira"

    estado_pendencia: dict[str, Any] = {}
    agora = 1_787_433_600.0

    def atualizar(mutador):
        novo = mutador(dict(estado_pendencia))
        estado_pendencia.clear()
        estado_pendencia.update(novo)
        return dict(estado_pendencia)

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado_pendencia,
        estado_atualizar=atualizar,
        agora=lambda: agora,
        log=lambda *_args: None,
    )

    lixeira = LixeiraLaylay(
        raiz=str(raiz_lixeira),
        pendencia_runtime=pendencia,
        agora=lambda: agora,
    )

    def resolver_local(valor: str) -> str:
        bruto = str(valor or "").strip()
        if not bruto:
            return ""
        candidato = Path(bruto)
        if candidato.is_absolute():
            return str(candidato)
        return str(area / bruto)

    def buscar_isolado(alvo: str) -> list[str]:
        """Mesma semântica de nome exato, limitada ao fixture."""
        nome = os.path.basename(str(alvo or "").strip())
        if not nome:
            return []
        return [
            str(item)
            for item in area.rglob("*")
            if item.name == nome
        ]

    def existe_local(caminho: str, tipo: str = "") -> bool:
        resolvido = Path(resolver_local(caminho))
        if tipo == "arquivo":
            return resolvido.is_file()
        if tipo == "pasta":
            return resolvido.is_dir()
        return resolvido.exists()

    mutacoes = ArquivosMutacaoRuntime(
        resolver_caminho_cb=resolver_local,
        buscar_itens_cb=buscar_isolado,
        solicitar_exclusao_cb=lixeira.mover,
        confirmar_exclusao_cb=lixeira.confirmar_pendente,
        cancelar_exclusao_cb=lixeira.cancelar_pendente,
        restaurar_ultimo_cb=lixeira.restaurar_ultimo,
        exclusao_pendente_cb=lixeira.tem_confirmacao_pendente,
    )

    return {
        "area": area,
        "lixeira": lixeira,
        "pendencia": pendencia,
        "mutacoes": mutacoes,
        "resolver_local": resolver_local,
        "existe_local": existe_local,
    }


def _executar(
    ambiente: dict[str, Any],
    *,
    intent: str,
    params: dict[str, Any],
    texto: str,
) -> list[dict[str, Any]]:
    resultados: list[dict[str, Any]] = []

    def marcar_resultado(
        status: str,
        executou: bool | None,
        **kwargs: Any,
    ) -> None:
        resultados.append({
            "status": status,
            "executou": executou,
            **kwargs,
        })

    tratado = executar_intencao_arquivos(
        intent,
        params,
        "pc_local",
        {
            # Evita qualquer TTS/LLM externo; não substitui executor/mutação.
            "falar_com_lipsync": lambda *_args, **_kwargs: None,
        },
        texto_original=texto,
        marcar_resultado=marcar_resultado,
        registrar_arquivo=lambda *_args: None,
        item_local_existe=ambiente["existe_local"],
        resolver_caminho_local=ambiente["resolver_local"],
        resolver_referencia_arquivo_contextual=lambda alvo, _tipo: str(alvo or ""),
        arquivos_leitura=None,
        arquivos_mutacao=ambiente["mutacoes"],
    )

    assert tratado is True
    assert resultados, "executor tratou o intent sem publicar resultado"
    return resultados


@pytest.mark.parametrize(
    ("fala", "nome"),
    [
        ("Apaga o troca ideia.txt.", "troca ideia.txt"),
        ("Apaga o caos seguro.txt.", "caos seguro.txt"),
    ],
)
def test_exclusao_confirmada_e_restaurada_atravessa_lixeira_real(
    ambiente_exclusao,
    fala: str,
    nome: str,
) -> None:
    area: Path = ambiente_exclusao["area"]
    lixeira: LixeiraLaylay = ambiente_exclusao["lixeira"]

    arquivo = area / nome
    conteudo_original = f"fixture seguro para {nome}\n"
    arquivo.write_text(conteudo_original, encoding="utf-8")

    # 1. Linguagem natural -> intent canônico e basename sem pontuação de frase.
    candidato = detectar_intencao_arquivos(
        fala,
        params_cb=lambda **params: params,
        estado_mental={},
        normalizar_texto=_normalizar,
    )
    assert candidato is not None
    assert candidato["intent"] == "DELETE_ITEM"
    assert candidato["params"]["alvo"] == nome

    # 2. DELETE_ITEM real deve SOMENTE preparar a confirmação.
    resultado_delete = _executar(
        ambiente_exclusao,
        intent="DELETE_ITEM",
        params=dict(candidato["params"]),
        texto=fala,
    )[-1]

    assert resultado_delete["status"] == "aguardando_confirmacao"
    assert resultado_delete["executou"] is False
    assert arquivo.is_file(), "arquivo foi removido antes da confirmação"
    assert lixeira.tem_confirmacao_pendente() is True

    # 3. Confirmação real move fisicamente para a lixeira isolada.
    resultado_confirmacao = _executar(
        ambiente_exclusao,
        intent="CONFIRM_DELETE_ITEM",
        params={},
        texto="sim",
    )[-1]

    assert resultado_confirmacao["status"] == "movido_para_lixeira"
    assert resultado_confirmacao["executou"] is True
    assert resultado_confirmacao.get("confirmado") is True
    assert not arquivo.exists()
    assert lixeira.tem_confirmacao_pendente() is False

    # Confirma que não foi um simples delete/unlink: existe item físico na
    # lixeira da Laylay antes da restauração.
    itens_lixeira = list((Path(lixeira.raiz) / "itens").rglob(nome))
    assert len(itens_lixeira) == 1
    assert itens_lixeira[0].read_text(encoding="utf-8") == conteudo_original

    # 4. RESTORE_DELETED_ITEM usa a exclusão confirmada e traz o mesmo arquivo.
    resultado_restore = _executar(
        ambiente_exclusao,
        intent="RESTORE_DELETED_ITEM",
        params={
            "alvo": str(arquivo),
            "referencia_exclusao_confirmada": True,
        },
        texto="Quero ele de volta.",
    )[-1]

    assert resultado_restore["status"] == "restaurado"
    assert resultado_restore["executou"] is True
    assert resultado_restore.get("confirmado") is True
    assert arquivo.is_file()
    assert arquivo.read_text(encoding="utf-8") == conteudo_original
    assert list((Path(lixeira.raiz) / "itens").rglob(nome)) == []
