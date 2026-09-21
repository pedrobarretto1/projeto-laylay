# -*- coding: utf-8 -*-
"""Fotografia vermelha V2 — autoridade de turno e frescor de arquivos.

Baseline obrigatória:
    a619a71ff5d1976fb8a25561ab2512ec291e31e8  (teste 3.1)

TEST-ONLY. Este arquivo não corrige produção.

Objetivo:
- R1: provar que uma intent com efeito descoberta depois da barreira lexical
  não pode ganhar mais autoridade do que o turno congelado;
- R1/cadeia: provar que segmentar uma frase não pode fabricar autorização;
- R2: provar que contexto efêmero de arquivo só existe enquanto a fonte
  canônica está fresca e que entidades derivadas não podem rejuvenescer a fonte;
- R1 x R2: provar que contexto vencido + turno não autorizado nunca chega ao
  executor de mutação.

Convenção:
- ``test_guard__*`` deve PASSAR na baseline teste 3.1;
- ``test_red__*`` deve FALHAR por assert na baseline teste 3.1;
- um red que fica verde inesperadamente exige investigação, nunca adaptação
  automática do teste.

Deliberadamente fora deste snapshot:
- ergonomia B1 de escrita/append sem pronome;
- ``Leia de novo`` / replay FILE_READ (B2);
- colisão caixa de entrada x nomes de arquivo;
- fallbacks legados do executor sem reprodução própria;
- endurecimento de timestamps futuros (anotado, mas não misturado a R1/R2).
"""

from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest

import mente_laylay.autonomia.comandos_imediatos as comandos_imediatos_mod
import mente_laylay.autonomia.coordenador_intencao as coordenador_intencao_mod
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.continuidade_contexto import (
    estrutura_arquivo_recente,
    registrar_estrutura_arquivo_recente,
)


BASELINE_HEAD = "a619a71ff5d1976fb8a25561ab2512ec291e31e8"
TTL_ESTRUTURA_ARQUIVO_S = 900.0


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _params(**kwargs):
    return kwargs


def _estrutura_arquivo(caminho: str) -> dict:
    return {
        "tipo": "arquivo",
        "caminho": caminho,
        "arquivo_nome": os.path.basename(caminho),
        "tipo_arquivo": "texto",
    }


def _estrutura_pesquisa(*caminhos: str) -> dict:
    return {
        "tipo": "pesquisa_semantica",
        "resultados": list(caminhos),
        "nomes": [os.path.basename(caminho) for caminho in caminhos],
        "consulta": "resultado local de teste",
    }


def _estado_fonte(dados: dict, ts: float | None) -> dict:
    estado = {"ultima_estrutura_arquivo_params": dict(dados)}
    if ts is not None:
        estado["ultima_estrutura_arquivo_ts"] = float(ts)
    return estado


def _estado_arquivo_fresco(caminho: str) -> dict:
    return registrar_estrutura_arquivo_recente({}, _estrutura_arquivo(caminho))


def _detectar(texto: str, estado: dict | None = None) -> dict | None:
    return detectar_intencao_arquivos(
        texto,
        params_cb=_params,
        estado_mental=estado or {},
        normalizar_texto=_normalizar,
    )


def _turno(*, autoriza: bool, id_turno: int = 2001) -> dict:
    """Moldura congelada; autorização é dado de entrada, não inferência do teste."""
    return {
        "id": id_turno,
        "texto": "",
        "modalidade": "comando",
        "modalidade_geral": "comando",
        "ato_principal": "comando",
        "atos": ["comando"],
        "segmentos": [
            {
                "indice": 0,
                "texto": "",
                "modalidade": "comando",
                "autoriza_execucao": bool(autoriza),
                "acao_explicita": True,
                "requer_esclarecimento": False,
                "natureza_acao": "pedido_direto",
            }
        ],
        "acao_explicita": True,
        "autoriza_execucao": bool(autoriza),
        "requer_esclarecimento": False,
        "depende_contexto": not bool(autoriza),
        "natureza_acao": "pedido_direto",
    }


def _turno_conversa_nao_autorizado(*, id_turno: int = 2002) -> dict:
    return {
        "id": id_turno,
        "texto": "",
        "modalidade": "conversa",
        "modalidade_geral": "conversa",
        "ato_principal": "conversa",
        "atos": ["conversa"],
        "segmentos": [],
        "acao_explicita": False,
        "autoriza_execucao": False,
        "requer_esclarecimento": False,
        "depende_contexto": False,
        "natureza_acao": "nenhuma",
    }


class _EstadoRuntime:
    def __init__(self, mental: dict):
        self.mental = mental

    def substituir(self, dominio: str, dados: dict) -> None:
        if dominio == "mental":
            self.mental = dict(dados)


def _runtime_prioritario(
    *,
    estado_base: dict | None,
    turno: dict,
    detector_deterministico=None,
):
    mental = dict(estado_base or {})
    mental["turno_atual"] = dict(turno)
    estado_runtime = _EstadoRuntime(mental)
    executados: list[dict] = []
    registros: list[tuple] = []

    ns = {
        "_estado_compartilhado_runtime": estado_runtime,
        "_normalizar_texto_com_apelidos": _normalizar,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "detectar_intencao_deterministica": (
            detector_deterministico if callable(detector_deterministico) else (lambda _texto: None)
        ),
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_comando_midia_contextual_forcado": lambda _texto: None,
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
    return runtime, estado_runtime, executados, registros


def _retrato(texto: str, estado: dict, *, agora: float) -> tuple[dict, dict]:
    return construir_retrato_turno(
        texto,
        turno={
            "id": 3001,
            "modalidade": "comando",
            "modalidade_geral": "comando",
            "ato_principal": "comando",
        },
        mente=estado,
        contexto_perceptivo={},
        playlist_state={},
        jogo_contexto={},
        agora=agora,
    )


def _ciclo_minimo(monkeypatch, turno_pai: dict):
    """Instala só as bordas usadas por ``processar_cadeia``; não executa produção."""
    ciclo = object.__new__(CicloComandosRuntime)
    ciclo.log = lambda *args, **kwargs: None
    ciclo._ns = lambda: {"_normalizar_texto_com_apelidos": _normalizar}
    ciclo._montar_contexto_resolucao = lambda: {
        "turno_atual": dict(turno_pai),
        "retrato_turno_atual": {},
    }
    ciclo.contexto_intencao_runtime = SimpleNamespace(montar=lambda: {})

    vistos: list[dict] = []

    def fluxo_falso(texto, origem, contexto, **_kwargs):
        vistos.append(
            {
                "texto": str(texto),
                "origem": str(origem),
                "turno": dict(contexto.get("turno_atual") or {}),
            }
        )
        return True

    monkeypatch.setattr(
        coordenador_intencao_mod,
        "executar_fluxo_intencao",
        fluxo_falso,
    )
    return ciclo, vistos


# ---------------------------------------------------------------------------
# GUARDS — precisam estar verdes na baseline e continuar verdes após o patch.
# ---------------------------------------------------------------------------


def test_guard__accessor_canonico_aceita_estrutura_fresca(tmp_path) -> None:
    caminho = str(tmp_path / "fresco.txt")
    estado = _estado_arquivo_fresco(caminho)

    assert estrutura_arquivo_recente(estado) == _estrutura_arquivo(caminho)


def test_guard__accessor_canonico_rejeita_estrutura_vencida(tmp_path) -> None:
    caminho = str(tmp_path / "velho.txt")
    agora = time.time()
    estado = _estado_fonte(
        _estrutura_arquivo(caminho),
        agora - TTL_ESTRUTURA_ARQUIVO_S - 30.0,
    )

    assert estrutura_arquivo_recente(estado) is None


def test_guard__accessor_canonico_rejeita_timestamp_ausente(tmp_path) -> None:
    caminho = str(tmp_path / "sem-ts.txt")
    estado = _estado_fonte(_estrutura_arquivo(caminho), None)

    assert estrutura_arquivo_recente(estado) is None


def test_guard__roteador_resolve_leitura_de_arquivo_fresco(tmp_path) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    resultado = _detectar("Leia ele.", _estado_arquivo_fresco(caminho))

    assert resultado == {
        "intent": "FILE_READ",
        "params": {
            "caminho": caminho,
            "alvo": "caos seguro.txt",
            "referencia_contextual": True,
        },
    }


def test_guard__pesquisa_semantica_fresca_resolve_ordinal(tmp_path) -> None:
    primeiro = str(tmp_path / "primeiro.txt")
    segundo = str(tmp_path / "segundo.txt")
    estado = registrar_estrutura_arquivo_recente(
        {},
        _estrutura_pesquisa(primeiro, segundo),
    )

    resultado = _detectar("o primeiro", estado)

    assert resultado == {
        "intent": "FILE_OPEN_RESULT",
        "params": {
            "caminho": primeiro,
            "alvo": "primeiro.txt",
            "indice": 1,
        },
    }


def test_guard__restore_so_nasce_de_exclusao_confirmada_recente(tmp_path) -> None:
    caminho = str(tmp_path / "apagado.txt")
    agora = time.time()
    recente = {
        "ultima_acao_contrato": {
            "intent": "CONFIRM_DELETE_ITEM",
            "executou": True,
            "confirmado": True,
            "status": "movido_para_lixeira",
            "alvo": caminho,
        },
        "ultima_acao_ts": agora,
    }
    antigo = dict(recente)
    antigo["ultima_acao_ts"] = agora - 600.0

    atual = _detectar("Restaura o último arquivo.", recente)
    expirado = _detectar("Restaura o último arquivo.", antigo)

    assert atual == {
        "intent": "RESTORE_DELETED_ITEM",
        "params": {
            "alvo": caminho,
            "referencia_exclusao_confirmada": True,
        },
    }
    assert expirado is None


def test_guard__prioridade_mantem_append_quando_turno_ja_autorizou(tmp_path) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    texto = "Acrescente segunda linha nele."
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base=_estado_arquivo_fresco(caminho),
        turno=_turno(autoriza=True),
    )

    assert runtime.processar_prioritarios(texto) is True
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


@pytest.mark.parametrize(
    ("texto", "intent"),
    [
        ("Leia ele.", "FILE_READ"),
        ("Qual é o caminho desse arquivo?", "FILE_SEARCH"),
    ],
)
def test_guard__prioridade_preserva_consultas_legitimas_de_arquivo(
    tmp_path,
    texto: str,
    intent: str,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base=_estado_arquivo_fresco(caminho),
        turno=_turno(autoriza=True),
    )

    assert runtime.processar_prioritarios(texto) is True
    assert len(executados) == 1
    assert executados[0]["intent"] == intent


def test_guard__cadeia_com_pai_autorizado_preserva_autoridade(monkeypatch) -> None:
    ciclo, vistos = _ciclo_minimo(monkeypatch, _turno(autoriza=True))

    consumiu = ciclo.processar_cadeia(
        "Adiciona segunda linha nele e adiciona terceira linha nele.",
        "guard-v2-cadeia",
    )

    assert consumiu is True
    assert len(vistos) == 2
    assert all(item["turno"].get("autoriza_execucao") is True for item in vistos)


# ---------------------------------------------------------------------------
# REDS R1 — uma intent concreta não pode ultrapassar a autoridade do turno.
# ---------------------------------------------------------------------------


def test_red__candidato_com_efeito_descoberto_depois_da_p0_nao_executa_sem_autoridade(
    monkeypatch,
    tmp_path,
) -> None:
    caminho = str(tmp_path / "injetado.txt")
    candidato = {
        "intent": "CREATE_FILE",
        "params": {
            "alvo": caminho,
            "conteudo": "conteúdo",
            "editar_existente": True,
        },
    }
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "detectar_intencao_arquivos",
        lambda *_args, **_kwargs: dict(candidato),
    )
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base={},
        turno=_turno_conversa_nao_autorizado(),
    )

    runtime.processar_prioritarios("zibra contextual agora")

    assert executados == [], (
        "intent com efeito descoberta após a P0 não pode executar quando o "
        "turno congelado não concedeu autoridade"
    )


def test_red__append_concreto_nao_executa_com_turno_congelado_sem_autorizacao(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "caos seguro.txt")
    texto = "Acrescente segunda linha nele."
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base=_estado_arquivo_fresco(caminho),
        turno=_turno(autoriza=False),
    )

    runtime.processar_prioritarios(texto)

    assert executados == [], (
        "CREATE_FILE(edit_existing=True) não pode atravessar a prioridade com "
        "autoriza_execucao=False"
    )


def test_red__restore_concreto_nao_executa_com_turno_congelado_sem_autorizacao(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "apagado.txt")
    estado = {
        "ultima_acao_contrato": {
            "intent": "CONFIRM_DELETE_ITEM",
            "executou": True,
            "confirmado": True,
            "status": "movido_para_lixeira",
            "alvo": caminho,
        },
        "ultima_acao_ts": time.time(),
    }
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base=estado,
        turno=_turno(autoriza=False),
    )

    runtime.processar_prioritarios("Restaura o último arquivo.")

    assert executados == [], (
        "a prova de qual item restaurar não substitui a autoridade do turno atual"
    )


def test_red__file_open_result_injetado_nao_executa_sem_autoridade(
    monkeypatch,
    tmp_path,
) -> None:
    caminho = str(tmp_path / "resultado.txt")
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "detectar_intencao_arquivos",
        lambda *_args, **_kwargs: {
            "intent": "FILE_OPEN_RESULT",
            "params": {"caminho": caminho, "alvo": "resultado.txt", "indice": 1},
        },
    )
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base={},
        turno=_turno_conversa_nao_autorizado(id_turno=2003),
    )

    runtime.processar_prioritarios("quasar ordinal")

    assert executados == [], (
        "FILE_OPEN_RESULT é efeito operacional e não pode ganhar permissão só "
        "porque apareceu numa porta prioritária"
    )


def test_red__cadeia_nao_pode_fabricar_autorizacao_para_filhos(monkeypatch) -> None:
    ciclo, vistos = _ciclo_minimo(monkeypatch, _turno(autoriza=False))

    consumiu = ciclo.processar_cadeia(
        "Adiciona segunda linha nele e adiciona terceira linha nele.",
        "red-v2-cadeia",
    )

    assert consumiu is True
    assert not any(
        bool(item["turno"].get("autoriza_execucao")) for item in vistos
    ), "filho de cadeia nunca pode ter mais autoridade que o turno pai"


# ---------------------------------------------------------------------------
# REDS R2 — validade temporal da fonte é autoridade única do contexto de arquivo.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("timestamp_presente", [True, False])
def test_red__roteador_nao_resolve_arquivo_vencido_ou_sem_timestamp(
    monkeypatch,
    tmp_path,
    timestamp_presente: bool,
) -> None:
    relogio = {"agora": 50_000.0}
    monkeypatch.setattr(time, "time", lambda: relogio["agora"])
    caminho = str(tmp_path / "stale.txt")
    ts = relogio["agora"] - 1_200.0 if timestamp_presente else None
    estado = _estado_fonte(_estrutura_arquivo(caminho), ts)

    resultado = _detectar("Leia ele.", estado)

    assert resultado is None, (
        "roteador deve consumir a mesma política de frescor do accessor canônico"
    )


def test_red__pesquisa_semantica_vencida_nao_pode_abrir_ordinal(
    monkeypatch,
    tmp_path,
) -> None:
    relogio = {"agora": 60_000.0}
    monkeypatch.setattr(time, "time", lambda: relogio["agora"])
    primeiro = str(tmp_path / "primeiro.txt")
    segundo = str(tmp_path / "segundo.txt")
    estado = _estado_fonte(
        _estrutura_pesquisa(primeiro, segundo),
        relogio["agora"] - 1_200.0,
    )

    resultado = _detectar("o primeiro", estado)

    assert resultado is None, (
        "resultado ordinal só existe enquanto a pesquisa semântica fonte está fresca"
    )


def test_red__retrato_nao_publica_fonte_de_arquivo_ja_vencida(
    monkeypatch,
    tmp_path,
) -> None:
    relogio = {"agora": 70_000.0}
    monkeypatch.setattr(time, "time", lambda: relogio["agora"])
    caminho = str(tmp_path / "velho.txt")
    estado = _estado_fonte(
        _estrutura_arquivo(caminho),
        relogio["agora"] - 1_200.0,
    )

    retrato, recentes = _retrato("Leia esse arquivo.", estado, agora=relogio["agora"])

    assert "arquivo" not in recentes
    assert str((retrato.get("referencia_resolvida") or {}).get("tipo") or "") != "arquivo"


def test_red__retrato_nao_rejuvenesce_entidade_derivada_ao_cruzar_ttl(
    monkeypatch,
    tmp_path,
) -> None:
    relogio = {"agora": 80_000.0}
    monkeypatch.setattr(time, "time", lambda: relogio["agora"])
    caminho = str(tmp_path / "quase-vencido.txt")
    fonte_ts = relogio["agora"] - 899.0
    estado = _estado_fonte(_estrutura_arquivo(caminho), fonte_ts)

    _retrato1, recentes1 = _retrato(
        "Leia esse arquivo.",
        estado,
        agora=relogio["agora"],
    )
    assert "arquivo" in recentes1, "pré-condição: fonte com 899s ainda é válida"

    relogio["agora"] += 2.0
    estado2 = dict(estado)
    estado2["entidades_recentes"] = recentes1
    retrato2, recentes2 = _retrato(
        "Leia esse arquivo.",
        estado2,
        agora=relogio["agora"],
    )

    assert "arquivo" not in recentes2, (
        "entidade derivada não pode ganhar um novo TTL ao ser copiada pelo retrato"
    )
    assert str((retrato2.get("referencia_resolvida") or {}).get("tipo") or "") != "arquivo"


@pytest.mark.parametrize("fonte", ["vencida", "ausente"])
def test_red__cache_legado_derivado_morre_quando_fonte_canonica_nao_e_valida(
    monkeypatch,
    tmp_path,
    fonte: str,
) -> None:
    relogio = {"agora": 90_000.0}
    monkeypatch.setattr(time, "time", lambda: relogio["agora"])
    caminho = str(tmp_path / "legado.txt")
    entidade_legada = {
        "tipo": "arquivo",
        "nome": "legado.txt",
        "origem": "estrutura_arquivo_confirmada",
        "ts": relogio["agora"] - 1.0,
        "dados": {
            **_estrutura_arquivo(caminho),
            "caminho": caminho,
        },
    }
    estado = {"entidades_recentes": {"arquivo": entidade_legada}}
    if fonte == "vencida":
        estado.update(
            _estado_fonte(
                _estrutura_arquivo(caminho),
                relogio["agora"] - 1_200.0,
            )
        )

    retrato, recentes = _retrato("Leia esse arquivo.", estado, agora=relogio["agora"])

    assert "arquivo" not in recentes, (
        "cache derivado de estrutura_arquivo_confirmada não pode sobreviver à fonte"
    )
    assert str((retrato.get("referencia_resolvida") or {}).get("tipo") or "") != "arquivo"


# ---------------------------------------------------------------------------
# RED R1 x R2 — combinação que poderia escolher e mutar um alvo stale.
# ---------------------------------------------------------------------------


def test_red__contexto_stale_e_turno_nao_autorizado_resultam_em_zero_execucoes(
    monkeypatch,
    tmp_path,
) -> None:
    relogio = {"agora": 100_000.0}
    monkeypatch.setattr(time, "time", lambda: relogio["agora"])
    caminho = str(tmp_path / "alvo-stale.txt")
    estado = _estado_fonte(
        _estrutura_arquivo(caminho),
        relogio["agora"] - 1_200.0,
    )
    runtime, _estado, executados, _registros = _runtime_prioritario(
        estado_base=estado,
        turno=_turno(autoriza=False, id_turno=2004),
    )

    runtime.processar_prioritarios("Acrescente segunda linha nele.")

    assert executados == [], (
        "nem frescor vencido nem bypass prioritário podem produzir mutação"
    )
