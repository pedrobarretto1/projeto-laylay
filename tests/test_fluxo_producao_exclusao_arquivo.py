"""Fluxo de produção focado para exclusão de arquivo com confirmação.

Objetivo arquitetural
---------------------
Validar a cadeia real que interessa à colisão Caixa x Arquivos sem chamar
diretamente ``detectar_intencao_arquivos`` nem ``executar_intencao_arquivos``:

classificador de modalidade real
→ P0 / ComandosImediatosRuntime real
→ CaixaEntradaPessoalRuntime real
→ DeteccaoDeterministicaRuntime real
→ CicloComandosRuntime real
→ roteador principal de intents real
→ ArquivosMutacaoRuntime real
→ LixeiraLaylay real
→ confirmação real em um segundo turno

Serviços externos que não participam desta habilidade não são iniciados.
A descoberta física de arquivos é confinada ao ``tmp_path`` do pytest para que
a regressão nunca selecione arquivos reais do usuário.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

import mente_laylay.arquivos.lixeira_laylay as lixeira_modulo
from mente_laylay.arquivos.lixeira_laylay import LixeiraLaylay
from mente_laylay.arquivos.mutacoes import ArquivosMutacaoRuntime
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.orquestrador_deterministico import (
    criar_deteccao_deterministica_runtime,
)
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.especialistas.caixa_entrada_pessoal import (
    CaixaEntradaPessoalRuntime,
)
from mente_laylay.integracao.contexto_execucao_ia import ContextoIntencaoRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _itens_caixa(caminho: Path) -> list[dict[str, Any]]:
    if not caminho.exists():
        return []
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [
        dict(item)
        for item in list(dados.get("itens") or [])
        if isinstance(item, dict)
    ]


@pytest.fixture
def pilha_producao_exclusao(tmp_path, monkeypatch):
    """Monta as classes reais do caminho crítico com filesystem isolado."""
    area = tmp_path / "arquivos"
    area.mkdir()
    caminho_caixa = tmp_path / "caixa.json"

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

    # O roteador de arquivos ainda mantém uma ponte legada para o singleton da
    # lixeira ao interpretar "sim"/"não". Apontamos essa ponte para A MESMA
    # LixeiraLaylay real deste fixture; não substituímos detector nem executor.
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
        return [
            str(item)
            for item in area.rglob("*")
            if item.name == nome
        ]

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
        antes = dict(estado.mental)
        novo = registrar_resultado_execucao(
            antes,
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
            "status": str(
                getattr(resultado, "status", "")
                or status
                or ""
            ),
            "texto": texto,
            "executou": executou,
            "origem": origem,
        })
        return novo

    caixa = CaixaEntradaPessoalRuntime(
        caminho=caminho_caixa,
        falar=lambda fala, *_args: falas.append(str(fala)),
        registrar_resultado=lambda *args, **kwargs: None,
        pendencia_runtime=pendencia,
        agora=lambda: __import__("datetime").datetime.fromtimestamp(instante),
        log=lambda *_args: None,
    )

    # Sentinela real: se a jurisdição regredir, existe algo concreto que a
    # Caixa poderia tentar apagar.
    assert caixa.processar(
        "anota essa ideia: SENTINELA DE JURISDICAO NAO APAGAR"
    ) is True
    assert len(_itens_caixa(caminho_caixa)) == 1

    servicos: dict[str, Any] = {
        "_normalizar_texto_com_apelidos": normalizar_texto_basico,
        "_texto_tem_comando_explicito": texto_tem_comando_explicito,
        "_target_from_params": (
            lambda params, _texto="": str(
                (params or {}).get("target") or "pc_a"
            )
        ),
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

    # A prioridade usa exatamente as superfícies públicas do ciclo real.
    servicos.update({
        "executar_intencao": ciclo.executar_intencao,
        "resolver_comando_natural": ciclo.resolver_comando_natural,
        "processar_comando_deterministico": ciclo.processar_deterministico,
        "processar_comandos_em_cadeia": ciclo.processar_cadeia,
        "decisao_comando_ja_avaliada": ciclo.decisao_ja_avaliada,
        "_caixa_entrada_pessoal_runtime": caixa,
    })

    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: servicos,
        loop_getter=lambda: None,
    )

    def publicar_turno(
        texto: str,
        *,
        confirmacao_contextual_valida: bool = False,
    ) -> dict[str, Any]:
        turno = classificar_modalidade_turno(
            texto,
            normalizar_texto=normalizar_texto_basico,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao_contextual_valida,
        )
        estado.atualizar_campos("mental", turno_atual=dict(turno))
        return dict(turno)

    def processar_turno(texto: str, *, confirmacao: bool = False):
        turno = publicar_turno(
            texto,
            confirmacao_contextual_valida=confirmacao,
        )
        tratado_prioritario = imediato.processar_prioritarios(texto)
        executou_ciclo = None
        if not tratado_prioritario:
            executou_ciclo = ciclo.executar_texto(texto, origem="terminal")
        return turno, tratado_prioritario, executou_ciclo

    return {
        "area": area,
        "caminho_caixa": caminho_caixa,
        "estado": estado,
        "pendencia": pendencia,
        "lixeira": lixeira,
        "mutacoes": mutacoes,
        "caixa": caixa,
        "ciclo": ciclo,
        "imediato": imediato,
        "falas": falas,
        "publicacoes": publicacoes,
        "processar_turno": processar_turno,
    }


@pytest.mark.parametrize(
    ("fala", "nome_arquivo"),
    [
        ("Apaga o troca ideia.txt.", "troca ideia.txt"),
        ("Apaga o caos seguro.txt.", "caos seguro.txt"),
        ("Apaga o arquivo tarefa.", "tarefa.txt"),
    ],
)
def test_fluxo_producao_exclusao_respeita_dominio_e_confirmacao(
    pilha_producao_exclusao,
    fala: str,
    nome_arquivo: str,
) -> None:
    ambiente = pilha_producao_exclusao
    area: Path = ambiente["area"]
    estado: EstadoCompartilhadoRuntime = ambiente["estado"]
    lixeira: LixeiraLaylay = ambiente["lixeira"]
    processar_turno = ambiente["processar_turno"]

    arquivo = area / nome_arquivo
    conteudo = f"conteudo seguro de {nome_arquivo}\n"
    arquivo.write_text(conteudo, encoding="utf-8")

    caixa_antes = _itens_caixa(ambiente["caminho_caixa"])
    assert len(caixa_antes) == 1
    assert caixa_antes[0]["status"] == "ativo"

    # TURNO 1 — o classificador real precisa autorizar a fala como comando.
    turno_delete, prioridade_delete, executou_delete = processar_turno(fala)

    assert turno_delete.get("autoriza_execucao") is True
    assert str(turno_delete.get("modalidade") or "") in {"comando", "misto"}

    # DELETE_ITEM não é executado pela Caixa prioritária. Ela deve ceder e o
    assert (prioridade_delete, executou_delete) in {
        (True, None),
        (False, True),
    }

    mente_apos_delete = dict(estado.mental)
    assert mente_apos_delete.get("ultima_acao_intent") == "DELETE_ITEM"
    assert mente_apos_delete.get("ultima_acao_status") == "aguardando_confirmacao"
    assert os.path.basename(
        str(mente_apos_delete.get("ultima_acao_alvo") or "")
    ) == nome_arquivo

    assert arquivo.is_file(), "arquivo foi removido antes da confirmação"
    assert lixeira.tem_confirmacao_pendente() is True

    # A nota sentinela prova que a Caixa não transformou o filename em nota.
    caixa_depois_pedido = _itens_caixa(ambiente["caminho_caixa"])
    assert len(caixa_depois_pedido) == 1
    assert caixa_depois_pedido[0]["status"] == "ativo"
    assert (
        caixa_depois_pedido[0]["conteudo"]
        == "SENTINELA DE JURISDICAO NAO APAGAR"
    )

    # TURNO 2 — "sim" ganha autoridade exclusivamente porque existe a
    # PendenciaAcaoRuntime real criada pela lixeira neste mesmo estado.
    turno_sim, prioridade_sim, executou_sim = processar_turno(
        "sim",
        confirmacao=True,
    )

    assert turno_sim.get("autoriza_execucao") is True
    assert prioridade_sim is True or executou_sim is True

    mente_final = dict(estado.mental)
    assert mente_final.get("ultima_acao_intent") == "CONFIRM_DELETE_ITEM"
    assert mente_final.get("ultima_acao_status") == "movido_para_lixeira"
    assert mente_final.get("ultima_acao_confirmada") is True

    assert not arquivo.exists()
    assert lixeira.tem_confirmacao_pendente() is False

    itens_lixeira = list((Path(lixeira.raiz) / "itens").rglob(nome_arquivo))
    assert len(itens_lixeira) == 1
    assert itens_lixeira[0].read_text(encoding="utf-8") == conteudo

    # E mesmo depois da confirmação física, a Caixa continua intacta.
    caixa_final = _itens_caixa(ambiente["caminho_caixa"])
    assert len(caixa_final) == 1
    assert caixa_final[0]["status"] == "ativo"
    assert caixa_final[0]["conteudo"] == "SENTINELA DE JURISDICAO NAO APAGAR"

    diagnostico = ambiente["ciclo"].diagnostico_linguagem_natural()
    assert diagnostico["resolvidas"] >= 1
    assert diagnostico["por_habilidade"].get("arquivos", 0) >= 1
