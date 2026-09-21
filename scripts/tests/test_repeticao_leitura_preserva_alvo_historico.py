"""RED arquitetural — repetição de leitura preserva o alvo histórico.

Contrato protegido:

FILE_READ(A)
    -> outra operação de arquivo torna B o arquivo saliente
    -> "Leia de novo."
    -> FILE_READ(A)

O arquivo atualmente saliente NÃO pode substituir o alvo da operação
de leitura que o usuário pediu para repetir.

Este teste não define ainda como o recibo histórico deve ser armazenado.
Ele prova somente a semântica necessária.
"""

from __future__ import annotations

from typing import Any

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_contexto import (
    estrutura_arquivo_recente,
    registrar_estrutura_arquivo_recente,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    selecionar_continuidade_reexecutavel,
)


CAMINHO_A = r"C:\Users\teste\Downloads\r1_c1_a.txt"
CAMINHO_B = r"C:\Users\teste\Downloads\r1_c1_b.txt"

NOME_A = "r1_c1_a.txt"
NOME_B = "r1_c1_b.txt"


def _registrar_leitura_a(
    estado: dict[str, Any],
) -> dict[str, Any]:
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "FILE_READ",
            "params": {
                "caminho": CAMINHO_A,
                "alvo": NOME_A,
            },
            "alvo": CAMINHO_A,
            "status": "executado",
            "executou": True,
            "confirmado": True,
            "origem": "executor",
        },
        f"Leia o {NOME_A}.",
        True,
        origem="executor",
        status="executado",
    )

    # Publica A pelo mesmo contrato canônico de estrutura de arquivo.
    return registrar_estrutura_arquivo_recente(
        estado,
        {
            "tipo": "arquivo",
            "caminho": CAMINHO_A,
            "arquivo_nome": NOME_A,
            "nome_arquivo": NOME_A,
        },
    )


def _registrar_criacao_b(
    estado: dict[str, Any],
) -> dict[str, Any]:
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "CREATE_FILE",
            "params": {
                "caminho": CAMINHO_B,
                "alvo": NOME_B,
                "nome_arquivo": NOME_B,
            },
            "alvo": CAMINHO_B,
            "status": "executado",
            "executou": True,
            "confirmado": True,
            "origem": "executor",
        },
        f"Cria um arquivo chamado {NOME_B}.",
        True,
        origem="executor",
        status="executado",
    )

    # B passa propositalmente a ser o arquivo saliente.
    # Isso impede uma futura correção de "funcionar" reconstruindo
    # o alvo de "Leia de novo." pelo contexto atual.
    return registrar_estrutura_arquivo_recente(
        estado,
        {
            "tipo": "arquivo",
            "caminho": CAMINHO_B,
            "arquivo_nome": NOME_B,
            "nome_arquivo": NOME_B,
        },
    )


def _rotear_arquivo(
    texto: str,
    estado: dict[str, Any],
) -> dict[str, Any] | None:
    return detectar_intencao_arquivos(
        texto,
        params_cb=lambda **kwargs: kwargs,
        estado_mental=estado,
        normalizar_texto=normalizar_texto_basico,
    )


def test_guard_file_read_a_e_reexecutavel_antes_do_sombreamento() -> None:
    """Sanidade: FILE_READ(A) nasce como operação reexecutável."""
    estado = _registrar_leitura_a(estado_mental_inicial())

    repetivel = selecionar_continuidade_reexecutavel(
        estado,
        classe="operacional",
        ttl_s=900.0,
    )

    assert repetivel
    assert repetivel["intent"] == "FILE_READ"
    assert repetivel["reexecutavel"] is True
    assert repetivel["params"]["caminho"] == CAMINHO_A


def test_guard_b_realmente_vira_o_arquivo_saliente() -> None:
    """B precisa dominar o contexto atual para o RED ser causal."""
    estado = _registrar_leitura_a(estado_mental_inicial())
    estado = _registrar_criacao_b(estado)

    assert estado["ultima_acao_intent"] == "CREATE_FILE"

    estrutura = estrutura_arquivo_recente(
        estado,
        ttl_s=900.0,
    )

    assert estrutura
    assert estrutura["tipo"] == "arquivo"
    assert estrutura["caminho"] == CAMINHO_B
    assert estrutura["caminho"] != CAMINHO_A


def test_guard_leia_de_novo_nao_pode_inventar_b_pela_saliencia() -> None:
    """Sem recibo de repetição, o roteador de arquivo não pode escolher B."""
    estado = _registrar_leitura_a(estado_mental_inicial())
    estado = _registrar_criacao_b(estado)

    candidato_direto = _rotear_arquivo(
        "Leia de novo.",
        estado,
    )

    assert candidato_direto is None


def test_red_repeticao_de_leitura_preserva_o_alvo_historico_a() -> None:
    """R1-C1: arquivo saliente atual != alvo da leitura a repetir."""
    estado = _registrar_leitura_a(estado_mental_inicial())
    estado = _registrar_criacao_b(estado)

    repeticao = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao is not None
    assert repeticao["intent"] == "FILE_READ"

    params = dict(repeticao.get("params") or {})

    assert params["caminho"] == CAMINHO_A
    assert params["caminho"] != CAMINHO_B
