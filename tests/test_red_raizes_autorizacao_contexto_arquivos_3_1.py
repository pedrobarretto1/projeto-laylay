# -*- coding: utf-8 -*-
"""Fotografia vermelha R1/R2 — autorização e validade contextual de arquivos.

Baseline travada para estudo:
    a619a71ff5d1976fb8a25561ab2512ec291e31e8  (teste 3.1)

Objetivo:
- R1: provar que a fase prioritária não pode despachar uma intent com efeito
  quando o turno congelado não autorizou execução, mesmo que a intent só seja
  descoberta depois da barreira lexical P0.
- R2: provar que referências efêmeras de arquivo/pesquisa precisam respeitar o
  accessor canônico de frescor (timestamp + TTL), sem ler estado cru.
- Interseção: autorização ausente + referência vencida nunca pode virar mutação.

Os testes ``test_guard__*`` devem passar na baseline.
Os testes ``test_red__*`` devem falhar por AssertionError na baseline estudada.
Depois do patch de produção, esta mesma fotografia deve ficar verde.
"""

from __future__ import annotations

import os
import time
from copy import deepcopy

import pytest

import mente_laylay.autonomia.comandos_imediatos as comandos_imediatos_mod
import mente_laylay.autonomia.coordenador_intencao as coordenador_intencao_mod
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import INTENTS_SOMENTE_LEITURA
from mente_laylay.memoria_mental.continuidade_contexto import (
    estrutura_arquivo_recente,
    registrar_estrutura_arquivo_recente,
)


HEAD_ESTUDADO = "a619a71ff5d1976fb8a25561ab2512ec291e31e8"


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _params(**kwargs):
    return kwargs


def _detectar_arquivo(texto: str, estado: dict | None = None) -> dict | None:
    return detectar_intencao_arquivos(
        texto,
        params_cb=_params,
        estado_mental=estado or {},
        normalizar_texto=_normalizar,
    )


def _estado_arquivo_fresco(caminho: str) -> dict:
    return registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "arquivo",
            "caminho": caminho,
            "arquivo_nome": os.path.basename(caminho),
            "tipo_arquivo": "texto",
            "origem": "CREATE_FILE",
        },
    )


def _estado_pesquisa_fresca(caminho: str) -> dict:
    return registrar_estrutura_arquivo_recente(
        {},
        {
            "tipo": "pesquisa_semantica",
            "consulta": os.path.basename(caminho),
            "resultados": [caminho],
            "nomes": [os.path.basename(caminho)],
        },
    )


def _turno_fixo(texto: str, *, autoriza: bool) -> dict:
    modalidade = "comando" if autoriza else "conversa"
    return {
        "id": f"red-r1-r2-{'sim' if autoriza else 'nao'}",
        "texto": texto,
        "normalizado": _normalizar(texto),
        "modalidade": modalidade,
        "modalidade_geral": modalidade,
        "ato_principal": modalidade,
        "atos": [modalidade],
        "texto_operacional": texto if autoriza else "",
        "texto_conversacional": "" if autoriza else texto,
        "acao_explicita": bool(autoriza),
        "autoriza_execucao": bool(autoriza),
        "requer_esclarecimento": False,
        "depende_contexto": False,
        "natureza_acao": "ordem" if autoriza else "nenhuma",
        "motivo": "turno de teste autorizado" if autoriza else "turno de teste sem autorização",
        "motivo_decisao": "turno de teste autorizado" if autoriza else "turno de teste sem autorização",
    }


class _EstadoRuntime:
    def __init__(self, mental: dict):
        self.mental = dict(mental)

    def substituir(self, dominio: str, valor):
        if dominio == "mental":
            self.mental = dict(valor or {})

    def obter(self, dominio: str, chave: str, padrao=None):
        if dominio == "mental":
            return self.mental.get(chave, padrao)
        return padrao


def _runtime_prioritario(
    texto: str,
    *,
    autoriza: bool,
    estado_extra: dict | None = None,
):
    mental = dict(estado_extra or {})
    mental["turno_atual"] = _turno_fixo(texto, autoriza=autoriza)
    estado_runtime = _EstadoRuntime(mental)
    executados: list[dict] = []
    registros: list[tuple] = []
    falas: list[str] = []

    ns = {
        "_estado_compartilhado_runtime": estado_runtime,
        "_normalizar_texto_com_apelidos": _normalizar,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "detectar_intencao_deterministica": lambda _texto: None,
        "resolver_comando_natural": lambda *_args, **_kwargs: (None, ""),
        "executar_intencao": (
            lambda comando, _texto: executados.append(deepcopy(comando)) or True
        ),
        "_registrar_resultado_execucao": (
            lambda *args, **kwargs: registros.append((args, kwargs))
        ),
        "falar_com_lipsync": lambda fala, *_args, **_kwargs: falas.append(str(fala)),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    return runtime, estado_runtime, executados, registros, falas


class _ContextoCadeia:
    def __init__(self, *, autoriza: bool):
        self.autoriza = bool(autoriza)

    def montar(self) -> dict:
        texto = "Adiciona segunda linha nele e adiciona terceira linha nele."
        return {
            "turno_atual": _turno_fixo(texto, autoriza=self.autoriza),
            "retrato_turno_atual": {},
            "continuidade_geral": {},
        }


def _capturar_autorizacao_cadeia(monkeypatch, *, autoriza_pai: bool) -> list[bool]:
    capturados: list[bool] = []

    def fluxo_fake(texto, origem, ctx, **_kwargs):
        turno = dict(ctx.get("turno_atual") or {})
        capturados.append(bool(turno.get("autoriza_execucao")))
        return True

    monkeypatch.setattr(
        coordenador_intencao_mod,
        "executar_fluxo_intencao",
        fluxo_fake,
    )
    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": _normalizar,
        },
        contexto_intencao_runtime=_ContextoCadeia(autoriza=autoriza_pai),
        log=lambda *_args, **_kwargs: None,
    )
    assert runtime.processar_cadeia(
        "Adiciona segunda linha nele e adiciona terceira linha nele.",
        "red-cadeia",
    ) is True
    return capturados


# ---------------------------------------------------------------------------
# GUARDS — contratos corretos que a correção não pode quebrar
# ---------------------------------------------------------------------------


def test_guard__catalogo_canonico_separa_leitura_de_efeito_em_arquivos() -> None:
    assert "FILE_SEARCH" in INTENTS_SOMENTE_LEITURA
    assert "FILE_READ" in INTENTS_SOMENTE_LEITURA

    for intent in {
        "FILE_OPEN_RESULT",
        "RESTORE_DELETED_ITEM",
        "CREATE_FILE",
        "DELETE_ITEM",
        "FILE_TRANSACTION",
    }:
        assert intent not in INTENTS_SOMENTE_LEITURA


def test_guard__accessor_canonico_rejeita_contexto_stale_e_sem_timestamp() -> None:
    caminho = "C:/tmp/caos seguro.txt"
    fresco = _estado_arquivo_fresco(caminho)

    stale = dict(fresco)
    stale["ultima_estrutura_arquivo_ts"] = 1.0
    assert estrutura_arquivo_recente(stale) is None

    sem_ts = dict(fresco)
    sem_ts.pop("ultima_estrutura_arquivo_ts", None)
    assert estrutura_arquivo_recente(sem_ts) is None


def test_guard__publisher_e_accessor_canonicos_preservam_contexto_fresco() -> None:
    caminho = "C:/tmp/caos seguro.txt"
    estado = _estado_arquivo_fresco(caminho)
    estrutura = estrutura_arquivo_recente(estado)
    assert estrutura is not None
    assert estrutura["tipo"] == "arquivo"
    assert estrutura["caminho"] == caminho
    assert float(estado["ultima_estrutura_arquivo_ts"]) > 0.0


@pytest.mark.parametrize(
    "candidato",
    [
        {
            "intent": "FILE_SEARCH",
            "params": {"query": "caos seguro.txt"},
        },
        {
            "intent": "FILE_READ",
            "params": {
                "caminho": "C:/tmp/caos seguro.txt",
                "alvo": "caos seguro.txt",
            },
        },
    ],
)
def test_guard__prioridade_preserva_consultas_read_only_sem_autorizar_mutacao(
    monkeypatch,
    candidato: dict,
) -> None:
    texto = "prossegue"
    runtime, _estado, executados, _registros, _falas = _runtime_prioritario(
        texto,
        autoriza=False,
    )
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "detectar_intencao_arquivos",
        lambda *_args, **_kwargs: deepcopy(candidato),
    )

    runtime.processar_prioritarios(texto)
    assert [item["intent"] for item in executados] == [candidato["intent"]]


def test_guard__roteador_consume_referencia_de_arquivo_fresca() -> None:
    caminho = "C:/tmp/caos seguro.txt"
    resultado = _detectar_arquivo(
        "Escreve primeira linha nele.",
        _estado_arquivo_fresco(caminho),
    )
    assert resultado is not None
    assert resultado["intent"] == "CREATE_FILE"
    assert resultado["params"]["alvo"] == caminho
    assert resultado["params"]["editar_existente"] is True


def test_guard__pesquisa_semantica_fresca_ainda_resolve_o_primeiro_resultado() -> None:
    caminho = "C:/tmp/caos seguro.txt"
    resultado = _detectar_arquivo(
        "o primeiro",
        _estado_pesquisa_fresca(caminho),
    )
    assert resultado is not None
    assert resultado["intent"] == "FILE_OPEN_RESULT"
    assert resultado["params"]["caminho"] == caminho


def test_guard__cadeia_de_turno_realmente_autorizado_preserva_autorizacao(
    monkeypatch,
) -> None:
    capturados = _capturar_autorizacao_cadeia(
        monkeypatch,
        autoriza_pai=True,
    )
    assert capturados == [True, True]


@pytest.mark.parametrize(
    "fala",
    [
        "Não acrescente segunda linha nele.",
        "Se eu pedir para acrescentar segunda linha nele, você consegue?",
        "Não restaura o último arquivo.",
        "Se eu pedir para restaurar o último arquivo, você consegue?",
    ],
)
def test_guard__negacao_e_hipotese_continuam_sem_autorizar_efeito(fala: str) -> None:
    turno = classificar_modalidade_turno(
        fala,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno["autoriza_execucao"] is False


# ---------------------------------------------------------------------------
# REDS — R1: autoridade do turno
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fala",
    [
        "Acrescente segunda linha nele.",
        "Acrescenta segunda linha nele.",
        "Adicione segunda linha nele.",
        "Adiciona segunda linha nele.",
    ],
)
def test_red__classificador_autoriza_imperativos_append_que_o_router_ja_aceita(
    fala: str,
) -> None:
    turno = classificar_modalidade_turno(
        fala,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno["autoriza_execucao"] is True


def test_red__classificador_autoriza_restore_direto_que_o_router_ja_aceita() -> None:
    fala = "Restaura o último arquivo."
    turno = classificar_modalidade_turno(
        fala,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    assert turno["autoriza_execucao"] is True


@pytest.mark.parametrize(
    "candidato",
    [
        {
            "intent": "CREATE_FILE",
            "params": {
                "alvo": "C:/tmp/caos seguro.txt",
                "conteudo": "segunda linha",
                "editar_existente": True,
                "modo_escrita": "append",
            },
        },
        {
            "intent": "RESTORE_DELETED_ITEM",
            "params": {
                "alvo": "C:/tmp/caos seguro.txt",
                "referencia_exclusao_confirmada": True,
            },
        },
        {
            "intent": "FILE_OPEN_RESULT",
            "params": {
                "caminho": "C:/tmp/caos seguro.txt",
                "alvo": "caos seguro.txt",
            },
        },
    ],
)
def test_red__prioridade_nao_despacha_efeito_descoberto_depois_da_p0_sem_autorizacao(
    monkeypatch,
    candidato: dict,
) -> None:
    texto = "prossegue"
    runtime, _estado, executados, _registros, _falas = _runtime_prioritario(
        texto,
        autoriza=False,
    )
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "detectar_intencao_arquivos",
        lambda *_args, **_kwargs: deepcopy(candidato),
    )

    runtime.processar_prioritarios(texto)

    # Contrato central: uma intent com efeito que só apareceu DEPOIS da
    # barreira lexical não ganha autorização por ter sido detectada.
    assert executados == []


def test_red__append_real_nao_chega_ao_executor_com_turno_nao_autorizado() -> None:
    texto = "Acrescente segunda linha nele."
    caminho = "C:/tmp/caos seguro.txt"
    estado = _estado_arquivo_fresco(caminho)

    candidato = _detectar_arquivo(texto, estado)
    assert candidato is not None
    assert candidato["intent"] == "CREATE_FILE"
    assert candidato["params"]["editar_existente"] is True

    runtime, _estado, executados, _registros, _falas = _runtime_prioritario(
        texto,
        autoriza=False,
        estado_extra=estado,
    )
    runtime.processar_prioritarios(texto)
    assert executados == []


def test_red__restore_real_nao_chega_ao_executor_com_turno_nao_autorizado() -> None:
    texto = "Restaura o último arquivo."
    caminho = "C:/tmp/caos seguro.txt"
    estado = {
        "ultima_acao_contrato": {
            "intent": "DELETE_ITEM",
            "alvo": caminho,
            "status": "movido_para_lixeira",
            "executou": True,
            "confirmado": True,
            "origem": "teste",
        },
        "ultima_acao_alvo": caminho,
        "ultima_acao_ts": time.time(),
    }

    candidato = _detectar_arquivo(texto, estado)
    assert candidato is not None
    assert candidato["intent"] == "RESTORE_DELETED_ITEM"

    runtime, _estado, executados, _registros, _falas = _runtime_prioritario(
        texto,
        autoriza=False,
        estado_extra=estado,
    )
    runtime.processar_prioritarios(texto)
    assert executados == []


def test_red__cadeia_nao_fabrica_autorizacao_que_o_turno_pai_nao_deu(
    monkeypatch,
) -> None:
    capturados = _capturar_autorizacao_cadeia(
        monkeypatch,
        autoriza_pai=False,
    )
    # Uma implementação correta pode recusar a cadeia inteira ([]) ou manter
    # a etapa sem autorização. O que não pode acontecer é promover False->True.
    assert not capturados or all(valor is False for valor in capturados)


# ---------------------------------------------------------------------------
# REDS — R2: validade do referente efêmero
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("modo", ["stale", "sem_timestamp"])
def test_red__roteador_rejeita_arquivo_que_accessor_canonico_considera_invalido(
    modo: str,
) -> None:
    caminho = "C:/tmp/caos seguro.txt"
    estado = _estado_arquivo_fresco(caminho)
    if modo == "stale":
        estado["ultima_estrutura_arquivo_ts"] = 1.0
    else:
        estado.pop("ultima_estrutura_arquivo_ts", None)

    # Prova primeiro que a política canônica já considera o referente morto.
    assert estrutura_arquivo_recente(estado) is None

    resultado = _detectar_arquivo("Escreve primeira linha nele.", estado)
    assert not (
        isinstance(resultado, dict)
        and resultado.get("intent") == "CREATE_FILE"
        and (resultado.get("params") or {}).get("alvo") == caminho
    )


def test_red__pesquisa_semantica_stale_nao_pode_abrir_resultado_ordinal() -> None:
    caminho = "C:/tmp/caos seguro.txt"
    estado = _estado_pesquisa_fresca(caminho)
    estado["ultima_estrutura_arquivo_ts"] = 1.0

    assert estrutura_arquivo_recente(estado) is None

    resultado = _detectar_arquivo("o primeiro", estado)
    assert not (
        isinstance(resultado, dict)
        and resultado.get("intent") == "FILE_OPEN_RESULT"
        and (resultado.get("params") or {}).get("caminho") == caminho
    )


# ---------------------------------------------------------------------------
# RED — encontro R1 + R2
# ---------------------------------------------------------------------------


def test_red__turno_nao_autorizado_e_referencia_stale_jamais_viram_mutacao() -> None:
    texto = "Acrescente segunda linha nele."
    caminho = "C:/tmp/caos seguro.txt"
    estado = _estado_arquivo_fresco(caminho)
    estado["ultima_estrutura_arquivo_ts"] = 1.0

    assert estrutura_arquivo_recente(estado) is None

    # A correção final elimina o candidato já no roteador: a barreira de
    # autoridade abaixo permanece como segunda defesa, não como única defesa.
    candidato = _detectar_arquivo(texto, estado)
    assert candidato is None

    runtime, _estado, executados, _registros, _falas = _runtime_prioritario(
        texto,
        autoriza=False,
        estado_extra=estado,
    )
    runtime.processar_prioritarios(texto)

    assert executados == []
