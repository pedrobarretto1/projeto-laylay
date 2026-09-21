from __future__ import annotations

import pytest

from mente_laylay.autonomia.comandos_imediatos import (
    _candidato_arquivo_prioritario_autorizado,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.continuidade_contexto import (
    registrar_estrutura_arquivo_recente,
)


def _turno(autoriza: bool) -> dict:
    return {
        "id": 22001,
        "modalidade": "comando" if autoriza else "conversa",
        "modalidade_geral": "comando" if autoriza else "conversa",
        "ato_principal": "comando" if autoriza else "conversa",
        "autoriza_execucao": bool(autoriza),
        "acao_explicita": bool(autoriza),
    }


def test_patch20_restore_direto_autoriza_sem_liberar_molduras_protegidas() -> None:
    direto = classificar_modalidade_turno("Restaura o último arquivo.")
    negativo = classificar_modalidade_turno("Não restaura o último arquivo.")
    instrucao = classificar_modalidade_turno("Como eu restauraria esse arquivo?")
    capacidade = classificar_modalidade_turno("Você consegue restaurar arquivos?")

    assert direto["autoriza_execucao"] is True
    assert str(direto["modalidade"]) == "comando"
    assert negativo["autoriza_execucao"] is False
    assert instrucao["autoriza_execucao"] is False
    assert capacidade["autoriza_execucao"] is False


def test_patch20_readonly_prioritario_nao_depende_de_autorizacao_de_mutacao() -> None:
    candidato = {
        "intent": "FILE_READ",
        "params": {"caminho": "C:/tmp/seguro.txt", "alvo": "seguro.txt"},
    }
    assert _candidato_arquivo_prioritario_autorizado(
        candidato,
        "Leia ele.",
        _turno(False),
        {},
    ) is True


def test_patch20_efeito_prioritario_nao_ganha_autoridade_do_detector() -> None:
    candidato = {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": "C:/tmp/seguro.txt",
            "conteudo": "linha",
            "editar_existente": True,
            "modo_escrita": "append",
        },
    }
    assert _candidato_arquivo_prioritario_autorizado(
        candidato,
        "Acrescente linha nele.",
        _turno(False),
        {},
    ) is False


def test_patch20_ordinal_fresco_exige_prova_textual_indice_e_caminho(tmp_path) -> None:
    primeiro = str(tmp_path / "primeiro.txt")
    segundo = str(tmp_path / "segundo.txt")
    estado = registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "pesquisa_semantica",
            "consulta": "documentacao python",
            "resultados": [primeiro, segundo],
            "nomes": ["primeiro.txt", "segundo.txt"],
        },
    )
    candidato = {
        "intent": "FILE_OPEN_RESULT",
        "params": {
            "caminho": primeiro,
            "alvo": "primeiro.txt",
            "indice": 1,
        },
    }

    assert _candidato_arquivo_prioritario_autorizado(
        candidato,
        "o primeiro",
        _turno(False),
        estado,
    ) is True
    assert _candidato_arquivo_prioritario_autorizado(
        candidato,
        "abre o primeiro resultado",
        _turno(False),
        estado,
    ) is True
    assert _candidato_arquivo_prioritario_autorizado(
        candidato,
        "quasar ordinal",
        _turno(False),
        estado,
    ) is False

    divergente = {
        **candidato,
        "params": {**candidato["params"], "caminho": segundo},
    }
    assert _candidato_arquivo_prioritario_autorizado(
        divergente,
        "o primeiro",
        _turno(False),
        estado,
    ) is False


@pytest.mark.parametrize(
    "texto",
    [
        "foi meu primeiro jogo",
        "não foi o primeiro",
        "eu fiquei em 1 lugar",
    ],
)
def test_patch20_ordinal_narrativo_nao_ganha_autoridade(
    tmp_path,
    texto: str,
) -> None:
    primeiro = str(tmp_path / "primeiro.txt")
    segundo = str(tmp_path / "segundo.txt")
    estado = registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "pesquisa_semantica",
            "consulta": "documentacao python",
            "resultados": [primeiro, segundo],
            "nomes": ["primeiro.txt", "segundo.txt"],
        },
    )
    candidato = {
        "intent": "FILE_OPEN_RESULT",
        "params": {
            "caminho": primeiro,
            "alvo": "primeiro.txt",
            "indice": 1,
        },
    }

    assert _candidato_arquivo_prioritario_autorizado(
        candidato,
        texto,
        _turno(False),
        estado,
    ) is False
