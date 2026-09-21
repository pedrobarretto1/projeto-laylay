# -*- coding: utf-8 -*-
"""Fotografia vermelha B1 — linguagem, autorização e contexto vivo de arquivos.

Baseline obrigatória:
    a619a71ff5d1976fb8a25561ab2512ec291e31e8  (teste 3.1)

Este arquivo NÃO corrige produção. Ele fotografa contratos desejados antes do
Patch B1. Os ``test_guard__*`` devem passar na baseline; os ``test_red__*``
devem falhar por AssertionError, sem erro de importação/coleta.

Escopo deliberado:
- B1A: alinhamento entre porteiro/modalidade/P0 e verbos de edição de arquivo;
- B1B: elipse de escrita/append usando SOMENTE arquivo recente tipado;
- B1C: leitura nominal resolvida contra arquivo recente equivalente;
- B1D: consulta de existência reutilizando FILE_SEARCH + referencia_caminho;
- cadeia real: CREATE_FILE publica referência e a etapa seguinte a consome.

Fora deste snapshot:
- repetição/``Leia de novo`` (B2);
- colisão caixa de entrada × nomes de arquivo (raiz separada);
- executores de arquivo, lixeira e política de replay.
"""

from __future__ import annotations

import os

import pytest

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.analise_comandos import processar_comandos_em_cadeia
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.memoria_mental.continuidade_contexto import (
    registrar_estrutura_arquivo_recente,
)


BASELINE_HEAD = "a619a71ff5d1976fb8a25561ab2512ec291e31e8"


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _params(**kwargs):
    return kwargs


def _estado_arquivo(caminho: str) -> dict:
    return registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "arquivo",
            "caminho": caminho,
            "arquivo_nome": os.path.basename(caminho),
            "tipo_arquivo": "texto",
        },
    )


def _estado_pasta(caminho: str) -> dict:
    return registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "pasta",
            "caminho": caminho,
            "nome": os.path.basename(caminho),
        },
    )


def _detectar(texto: str, estado: dict | None = None) -> dict | None:
    return detectar_intencao_arquivos(
        texto,
        params_cb=_params,
        estado_mental=estado or {},
        normalizar_texto=_normalizar,
    )


def _classificar_real(texto: str) -> dict:
    """Replica os callbacks que o orquestrador real entrega à modalidade."""
    return classificar_modalidade_turno(
        texto,
        normalizar_texto=_normalizar,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )


def _barreira(texto: str, turno: dict) -> bool:
    return bloqueia_execucao_operacional_prioritaria(
        texto,
        classificacao=turno,
        normalizar_texto=_normalizar,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )


def _runtime_arquivo(texto: str, estado_base: dict):
    turno = _classificar_real(texto)
    mental = dict(estado_base)
    mental["turno_atual"] = turno

    class Estado:
        def __init__(self, dados):
            self.mental = dados

    estado_runtime = Estado(mental)
    executados: list[dict] = []
    registros: list[tuple] = []

    ns = {
        "_estado_compartilhado_runtime": estado_runtime,
        "_normalizar_texto_com_apelidos": _normalizar,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "detectar_intencao_deterministica": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_registrar_resultado_execucao": (
            lambda *args, **kwargs: registros.append((args, kwargs))
        ),
        "executar_intencao": (
            lambda comando, _texto: executados.append(dict(comando)) or True
        ),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    return runtime, turno, executados, registros


# ---------------------------------------------------------------------------
# GUARDS — precisam continuar verdes antes e depois do futuro Patch B1.
# ---------------------------------------------------------------------------

def test_guard__criacao_de_arquivo_continua_sendo_comando_explicito() -> None:
    assert texto_tem_comando_explicito(
        "Cria um arquivo chamado caos seguro.txt."
    ) is True


def test_guard__leitura_nominal_ja_e_autorizada_pelo_ato_de_fala() -> None:
    texto = "Leia o caos seguro.txt."
    turno = _classificar_real(texto)
    assert turno["autoriza_execucao"] is True
    assert _barreira(texto, turno) is False


def test_guard__negacao_de_escrita_existente_continua_fail_closed() -> None:
    texto = "Não escreva primeira linha nele."
    turno = _classificar_real(texto)
    assert turno["autoriza_execucao"] is False
    assert _barreira(texto, turno) is True


@pytest.mark.parametrize(
    ("fala", "modo"),
    [
        ("Escreve primeira linha nele.", "overwrite"),
        ("Acrescente segunda linha nele.", "append"),
    ],
)
def test_guard__roteador_ja_sabe_editar_quando_pronome_nomeia_o_arquivo(
    tmp_path,
    fala: str,
    modo: str,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar(fala, _estado_arquivo(caminho))
    assert resultado is not None
    assert resultado["intent"] == "CREATE_FILE"
    assert resultado["params"]["alvo"] == caminho
    assert resultado["params"]["editar_existente"] is True
    if modo == "append":
        assert resultado["params"]["modo_escrita"] == "append"
    else:
        assert "modo_escrita" not in resultado["params"]


def test_guard__elipse_sem_arquivo_recente_nao_inventa_alvo() -> None:
    for fala in (
        "Escreve primeira linha.",
        "Grave primeira linha.",
        "Acrescente segunda linha.",
        "Adicione segunda linha.",
    ):
        assert _detectar(fala, {}) is None


def test_guard__pasta_recente_nao_pode_ser_promovida_a_arquivo_por_elipse(
    tmp_path,
) -> None:
    estado = _estado_pasta(str(tmp_path / "pasta recente"))
    assert _detectar("Escreve primeira linha.", estado) is None
    assert _detectar("Acrescente segunda linha.", estado) is None


def test_guard__alvo_nomeado_diferente_nao_vira_conteudo_eliptico(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar(
        "Acrescente segunda linha no arquivo outro.txt.",
        _estado_arquivo(caminho),
    )
    assert not (
        isinstance(resultado, dict)
        and resultado.get("intent") == "CREATE_FILE"
        and str((resultado.get("params") or {}).get("alvo") or "") == caminho
    )


def test_guard__consulta_de_caminho_ja_reusa_arquivo_tipado(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar("Onde ele fica?", _estado_arquivo(caminho))
    assert resultado == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "caos seguro.txt",
            "referencia_caminho": caminho,
            "alvo": "caos seguro.txt",
        },
    }


def test_guard__nome_diferente_nao_pode_hijackar_caminho_recente_como_leitura(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar("Leia o outro arquivo.txt.", _estado_arquivo(caminho))
    assert not (
        isinstance(resultado, dict)
        and resultado.get("intent") == "FILE_READ"
        and str((resultado.get("params") or {}).get("caminho") or "") == caminho
    )


def test_guard__existencia_sem_referencia_nao_inventa_caminho() -> None:
    resultado = _detectar("O arquivo ainda existe?", {})
    assert not (
        isinstance(resultado, dict)
        and str((resultado.get("params") or {}).get("referencia_caminho") or "")
    )


# ---------------------------------------------------------------------------
# REDS B1A — autorização e vocabulário operacional precisam concordar.
# ---------------------------------------------------------------------------

def test_red__p0_alinha_escrita_contextual_com_o_porteiro() -> None:
    texto = "Escreve primeira linha nele."
    turno = _classificar_real(texto)

    assert texto_tem_comando_explicito(texto) is True
    assert turno["autoriza_execucao"] is True
    assert _barreira(texto, turno) is False


@pytest.mark.parametrize(
    "texto",
    [
        "Acrescente segunda linha nele.",
        "Acrescenta segunda linha nele.",
        "Adicione segunda linha nele.",
        "Adiciona segunda linha nele.",
    ],
)
def test_red__p0_alinha_verbos_append_com_autorizacao(
    texto: str,
) -> None:
    turno = _classificar_real(texto)

    assert texto_tem_comando_explicito(texto) is True
    assert turno["autoriza_execucao"] is True
    assert _barreira(texto, turno) is False


@pytest.mark.parametrize(
    "texto",
    [
        "Não acrescente segunda linha nele.",
        "Como eu acrescentaria uma linha nele?",
        "Você consegue acrescentar uma linha nele?",
        "Se eu quisesse acrescentar uma linha nele?",
    ],
)
def test_red__p0_bloqueia_molduras_nao_autorizadas_de_append(
    texto: str,
) -> None:
    turno = _classificar_real(texto)

    assert turno["autoriza_execucao"] is False
    assert _barreira(texto, turno) is True


def test_red__runtime_nao_bloqueia_escrita_pronominal_legitima(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    texto = "Escreve primeira linha nele."
    runtime, turno, executados, _registros = _runtime_arquivo(
        texto,
        _estado_arquivo(caminho),
    )

    tratado = runtime.processar_prioritarios(texto)

    # A baseline deve expor a causa real pela rota, não falhar antes dela:
    # hoje o P0 barra "escreve ... nele" antes que o roteador já-capaz atue.
    assert tratado is True
    assert executados == [
        {
            "intent": "CREATE_FILE",
            "params": {
                "alvo": caminho,
                "conteudo": "primeira linha",
                "editar_existente": True,
            },
        }
    ]
    assert turno["autoriza_execucao"] is True


def test_red__runtime_append_nao_chega_a_mutacao_com_turno_nao_autorizado(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    texto = "Acrescente segunda linha nele."
    runtime, turno, executados, _registros = _runtime_arquivo(
        texto,
        _estado_arquivo(caminho),
    )

    # A baseline 3.1 consegue chegar ao roteador por essa forma, mas o contrato
    # do turno ainda não reconhece o verbo. O futuro patch deve alinhar os dois:
    # execução prática só pode coexistir com autorização explícita verdadeira.
    assert runtime.processar_prioritarios(texto) is True
    assert executados
    assert executados[-1]["intent"] == "CREATE_FILE"
    assert turno["autoriza_execucao"] is True


def test_red__turno_69_append_eliptico_chega_a_execucao_autorizada(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    texto = "Acrescente segunda linha."
    runtime, turno, executados, _registros = _runtime_arquivo(
        texto,
        _estado_arquivo(caminho),
    )

    assert runtime.processar_prioritarios(texto) is True
    assert turno["autoriza_execucao"] is True
    assert executados == [
        {
            "intent": "CREATE_FILE",
            "params": {
                "alvo": caminho,
                "conteudo": "segunda linha",
                "editar_existente": True,
                "modo_escrita": "append",
            },
        }
    ]


# ---------------------------------------------------------------------------
# REDS B1B — elipse segura depende EXCLUSIVAMENTE do arquivo tipado recente.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fala",
    [
        "Escreve primeira linha.",
        "Escreva primeira linha.",
        "Grava primeira linha.",
        "Grave primeira linha.",
    ],
)
def test_red__escrita_eliptica_usa_unico_arquivo_recente_tipado(
    tmp_path,
    fala: str,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar(fala, _estado_arquivo(caminho))

    assert resultado == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": caminho,
            "conteudo": "primeira linha",
            "editar_existente": True,
        },
    }


@pytest.mark.parametrize(
    "fala",
    [
        "Acrescente segunda linha.",
        "Acrescenta segunda linha.",
        "Adicione segunda linha.",
        "Adiciona segunda linha.",
    ],
)
def test_red__append_eliptico_usa_unico_arquivo_recente_tipado(
    tmp_path,
    fala: str,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar(fala, _estado_arquivo(caminho))

    assert resultado == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": caminho,
            "conteudo": "segunda linha",
            "editar_existente": True,
            "modo_escrita": "append",
        },
    }


def test_red__cadeia_cria_publica_e_segunda_etapa_consume_contexto_vivo(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    estado: dict = {}
    planos: list[dict | None] = []
    falhas: list[tuple[str, int, int]] = []

    def executar_trecho(trecho: str, _origem: str) -> bool:
        nonlocal estado
        plano = _detectar(trecho, estado)
        planos.append(plano)
        if not isinstance(plano, dict):
            return False
        if len(planos) == 1 and plano.get("intent") == "CREATE_FILE":
            # Simula somente o contrato oficial publicado após CREATE_FILE.
            # Não inventamos campo paralelo nem usamos ``ultimo_alvo``.
            estado = registrar_estrutura_arquivo_recente(
                estado,
                {
                    "tipo": "arquivo",
                    "caminho": caminho,
                    "arquivo_nome": "caos seguro.txt",
                    "tipo_arquivo": "texto",
                    "origem": "CREATE_FILE",
                },
            )
        return True

    consumiu = processar_comandos_em_cadeia(
        "Cria um arquivo chamado caos seguro.txt e escreve primeira linha.",
        "red-b1-cadeia",
        normalizar_texto=_normalizar,
        executar_trecho=executar_trecho,
        relatar_falha=lambda trecho, indice, concluidas: falhas.append(
            (trecho, indice, concluidas)
        ),
    )

    assert consumiu is True
    assert len(planos) == 2
    assert planos[0] is not None
    assert planos[0]["intent"] == "CREATE_FILE"
    assert planos[1] == {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": caminho,
            "conteudo": "primeira linha",
            "editar_existente": True,
        },
    }
    assert falhas == []


# ---------------------------------------------------------------------------
# REDS B1C/B1D — leitura nominal e consulta de existência.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fala",
    [
        "Leia o caos seguro.txt.",
        "Leia o caos seguro.",
    ],
)
def test_red__leitura_por_nome_reusa_arquivo_recente_equivalente(
    tmp_path,
    fala: str,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar(fala, _estado_arquivo(caminho))

    assert resultado == {
        "intent": "FILE_READ",
        "params": {
            "caminho": caminho,
            "alvo": "caos seguro.txt",
            "referencia_contextual": True,
        },
    }


def test_red__consulta_existencia_reusa_file_search_com_referencia_caminho(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar(
        "O arquivo ainda existe?",
        _estado_arquivo(caminho),
    )

    assert resultado == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "caos seguro.txt",
            "referencia_caminho": caminho,
            "alvo": "caos seguro.txt",
        },
    }
