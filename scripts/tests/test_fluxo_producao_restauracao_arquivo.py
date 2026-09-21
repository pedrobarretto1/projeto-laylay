"""Fluxo operacional de produção para restauração contextual de arquivo.

Valida a ROOT C acima do parser isolado, sem chamar diretamente
``detectar_intencao_arquivos`` nem ``executar_intencao_arquivos``.

Caminho:
fala
→ classificador real
→ P0 / ComandosImediatosRuntime
→ detector determinístico
→ CicloComandosRuntime
→ roteador principal
→ executor de integrações
→ ArquivosMutacaoRuntime
→ LixeiraLaylay
→ filesystem físico isolado
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

import mente_laylay.arquivos.lixeira_laylay as lixeira_modulo
from mente_laylay.arquivos.lixeira_laylay import LixeiraLaylay
from mente_laylay.arquivos.mutacoes import ArquivosMutacaoRuntime
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.orquestrador_deterministico import criar_deteccao_deterministica_runtime
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.integracao.contexto_execucao_ia import ContextoIntencaoRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


@pytest.fixture
def pilha_producao_restauracao(tmp_path, monkeypatch):
    area = tmp_path / "arquivos"
    area.mkdir()

    estado = EstadoCompartilhadoRuntime(mental=estado_mental_inicial())
    instante = 1_787_433_600.0

    def atualizar_mental(mutador):
        return estado.atualizar("mental", mutador)

    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado.mental,
        estado_atualizar=atualizar_mental,
        agora=lambda: instante,
        log=lambda *_args: None,
    )

    lixeira = LixeiraLaylay(
        raiz=str(tmp_path / "lixeira"),
        pendencia_runtime=pendencia,
        agora=lambda: instante,
    )
    monkeypatch.setattr(lixeira_modulo, "_RUNTIME", lixeira)

    def resolver_local(valor: str) -> str:
        bruto = str(valor or "").strip()
        if not bruto:
            return ""
        candidato = Path(bruto)
        if candidato.is_absolute():
            return str(candidato)
        return str(area / bruto)

    def buscar_isolado(alvo: str) -> list[str]:
        nome = os.path.basename(str(alvo or "").strip())
        if not nome:
            return []
        return [str(item) for item in area.rglob("*") if item.name == nome]

    mutacoes = ArquivosMutacaoRuntime(
        resolver_caminho_cb=resolver_local,
        buscar_itens_cb=buscar_isolado,
        solicitar_exclusao_cb=lixeira.mover,
        confirmar_exclusao_cb=lixeira.confirmar_pendente,
        cancelar_exclusao_cb=lixeira.cancelar_pendente,
        restaurar_ultimo_cb=lixeira.restaurar_ultimo,
        exclusao_pendente_cb=lixeira.tem_confirmacao_pendente,
    )

    falas: list[str] = []
    publicacoes: list[dict[str, Any]] = []

    def registrar_resultado(
        resultado,
        texto: str = "",
        executou: bool | None = None,
        *,
        origem: str = "",
        status: str = "",
        **_kwargs: Any,
    ):
        novo = registrar_resultado_execucao(
            dict(estado.mental),
            resultado,
            texto,
            executou,
            origem=origem,
            status=status,
        )
        estado.substituir("mental", novo)
        publicacoes.append({
            "intent": str(
                getattr(resultado, "intent", "")
                or (resultado.get("intent") if isinstance(resultado, dict) else "")
                or ""
            ),
            "status": str(getattr(resultado, "status", "") or status or ""),
            "texto": str(texto or ""),
            "executou": executou,
            "origem": str(origem or ""),
        })
        return novo

    servicos: dict[str, Any] = {
        "_normalizar_texto_com_apelidos": normalizar_texto_basico,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "_target_from_params": lambda params, _texto="": str((params or {}).get("target") or "pc_a"),
        "_pendencia_acao_runtime": pendencia,
        "_registrar_resultado_execucao": registrar_resultado,
        "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        "falar_com_lipsync": lambda fala, *_args: falas.append(str(fala)),
    }

    deteccao = criar_deteccao_deterministica_runtime(
        namespace_getter=lambda: servicos,
        estado_getter=lambda: estado.mental,
        sites_diretos={},
        apps_map={},
    )
    servicos["detectar_intencao_deterministica"] = deteccao.detectar

    contexto_intencao = ContextoIntencaoRuntime(
        namespace_getter=lambda: servicos,
        estado_getter=lambda: dict(estado.mental),
        arquivos_mutacao=mutacoes,
    )
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: servicos,
        contexto_intencao_runtime=contexto_intencao,
        log=lambda *_args: None,
    )

    servicos.update({
        "executar_intencao": ciclo.executar_intencao,
        "resolver_comando_natural": ciclo.resolver_comando_natural,
        "processar_comando_deterministico": ciclo.processar_deterministico,
        "processar_comandos_em_cadeia": ciclo.processar_cadeia,
        "decisao_comando_ja_avaliada": ciclo.decisao_ja_avaliada,
    })

    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: servicos,
        loop_getter=lambda: None,
    )

    def processar_turno(texto: str, *, confirmacao: bool = False):
        turno = classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto_basico,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao,
        )
        estado.atualizar_campos("mental", turno_atual=dict(turno))
        prioridade = imediato.processar_prioritarios(texto)
        executou = None
        if not prioridade:
            executou = ciclo.executar_texto(texto, origem="terminal")
        return dict(turno), prioridade, executou

    return {
        "area": area,
        "estado": estado,
        "lixeira": lixeira,
        "falas": falas,
        "publicacoes": publicacoes,
        "processar_turno": processar_turno,
    }


@pytest.mark.parametrize(
    "fala_restore",
    [
        "Quero ele de volta.",
        "Quero o arquivo de volta.",
        "Traz ele de volta.",
    ],
)
def test_fluxo_producao_restauracao_usa_autoridade_atual_e_recibo_confirmado(
    pilha_producao_restauracao,
    fala_restore: str,
) -> None:
    ambiente = pilha_producao_restauracao
    area: Path = ambiente["area"]
    estado: EstadoCompartilhadoRuntime = ambiente["estado"]
    lixeira: LixeiraLaylay = ambiente["lixeira"]
    processar_turno = ambiente["processar_turno"]

    arquivo = area / "caos seguro.txt"
    conteudo = "conteudo fisico preservado pela ROOT C\n"
    arquivo.write_text(conteudo, encoding="utf-8")

    turno_delete, prioridade_delete, executou_delete = processar_turno(
        "Apaga o caos seguro.txt."
    )
    assert turno_delete.get("autoriza_execucao") is True
    assert (prioridade_delete, executou_delete) in {(True, None), (False, True)}
    assert estado.mental.get("ultima_acao_intent") == "DELETE_ITEM"
    assert estado.mental.get("ultima_acao_status") == "aguardando_confirmacao"
    assert arquivo.is_file()
    assert lixeira.tem_confirmacao_pendente() is True

    turno_sim, prioridade_sim, executou_sim = processar_turno("sim", confirmacao=True)
    assert turno_sim.get("autoriza_execucao") is True
    assert prioridade_sim is True or executou_sim is True
    assert estado.mental.get("ultima_acao_intent") == "CONFIRM_DELETE_ITEM"
    assert estado.mental.get("ultima_acao_status") == "movido_para_lixeira"
    assert estado.mental.get("ultima_acao_confirmada") is True
    assert not arquivo.exists()

    itens_lixeira = list((Path(lixeira.raiz) / "itens").rglob(arquivo.name))
    assert len(itens_lixeira) == 1
    assert itens_lixeira[0].read_text(encoding="utf-8") == conteudo

    turno_restore, prioridade_restore, executou_restore = processar_turno(fala_restore)
    assert turno_restore.get("modalidade_geral") in {"comando", "misto"}
    assert turno_restore.get("autoriza_execucao") is True
    assert turno_restore.get("depende_contexto") is True
    assert (prioridade_restore, executou_restore) in {(True, None), (False, True)}

    assert estado.mental.get("ultima_acao_intent") == "RESTORE_DELETED_ITEM"
    assert estado.mental.get("ultima_acao_status") == "restaurado"
    assert estado.mental.get("ultima_acao_confirmada") is True
    assert os.path.normcase(str(estado.mental.get("ultima_acao_alvo") or "")) == os.path.normcase(str(arquivo))

    assert arquivo.is_file()
    assert arquivo.read_text(encoding="utf-8") == conteudo
    assert list((Path(lixeira.raiz) / "itens").rglob(arquivo.name)) == []

    registros = lixeira._carregar()
    assert len(registros) == 1
    assert registros[0].get("restaurado_em") is not None


@pytest.mark.parametrize(
    "fala_restore",
    [
        "Quero ele de volta.",
        "Quero o arquivo de volta.",
        "Traz ele de volta.",
    ],
)
def test_fluxo_producao_restauracao_sem_recibo_permanece_fail_closed(
    pilha_producao_restauracao,
    fala_restore: str,
) -> None:
    ambiente = pilha_producao_restauracao
    estado: EstadoCompartilhadoRuntime = ambiente["estado"]

    turno, prioridade, executou = ambiente["processar_turno"](fala_restore)

    assert turno.get("modalidade_geral") in {"comando", "misto"}
    assert turno.get("autoriza_execucao") is True
    assert turno.get("depende_contexto") is True

    assert estado.mental.get("ultima_acao_intent") != "RESTORE_DELETED_ITEM"
    assert estado.mental.get("ultima_acao_status") != "restaurado"

    assert [
        item for item in ambiente["publicacoes"]
        if item.get("intent") == "RESTORE_DELETED_ITEM"
    ] == []

    assert list(Path(ambiente["lixeira"].raiz).rglob("*")) == []
    assert prioridade in {True, False}
    assert executou in {True, False, None}
