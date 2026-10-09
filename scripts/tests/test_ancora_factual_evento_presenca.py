"""Motivo comunicativo permanece metadado; a âncora usa fatos observados."""

from __future__ import annotations

import json
from typing import Any

import pytest

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
from mente_laylay.percepcao.visao_jogo.coordenador import CoordenadorVisaoJogoRuntime
from mente_laylay.percepcao.visao_jogo.presenca_visual import extrair_presenca_visual
from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local


MOTIVO = "Comentário de companhia sobre a paisagem visualmente marcante."
FATOS = ["mar azul extenso ao fundo", "terreno seco e montanhoso"]
FATO_LONGO = "O caminho continua por " + "vários trechos completos " * 17 + "até a ponte visível."


def _diretor():
    estado: dict[str, Any] = {}
    eventos: list[dict[str, Any]] = []

    def cogitar(evento):
        eventos.append(evento)
        return {
            "natureza_entrada": "evento", "entrada_cognitiva": evento,
            "autoridade_usuario": False, "permissao_execucao": False,
            "autoriza_execucao": False,
            "contrato_fala": construir_contrato_semantico_evento(evento),
        }

    diretor = DiretorPresencaRuntime(
        estado_get=lambda: estado, estado_set=lambda novo: estado.update(novo),
        contexto_getter=lambda: {"modo_jogo_ativo": True, "ultima_entrada_ts": 0.0},
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=cogitar,
        processar_proposta_comunicativa=lambda *_a, **_k: {
            "status": "agendada", "agendada": True, "autoriza_execucao": False,
        },
        clock=lambda: 1000.0, log=lambda _texto: None,
    )
    return diretor, estado, eventos


def _coordenador(diretor: DiretorPresencaRuntime) -> CoordenadorVisaoJogoRuntime:
    return CoordenadorVisaoJogoRuntime(
        memoria_jogos=None, observador_inventario_getter=lambda: None,
        diretor_presenca_getter=lambda: diretor, recomendar_playlist=lambda _clima: "",
        registrar_oportunidade=lambda _dados: {}, decisao_permite_emissao=lambda _dados: False,
        agendar_fala=lambda *_a, **_k: False, registrar_mente_curta=lambda *_a, **_k: None,
        estado_mental_getter=lambda: {}, estado_mental_substituir=lambda _dados: None,
        criar_pendencia=lambda **_dados: {}, registrar_pendencia=lambda *_a, **_k: {},
        pendencia_ativa=lambda *_a, **_k: None, limpar_pendencia=lambda *_a, **_k: {},
        salvar_memoria=lambda: None,
    )


def test_produtor_visual_separa_motivo_dos_fatos_antes_do_diretor() -> None:
    diretor, _estado, eventos = _diretor()
    coordenador = _coordenador(diretor)
    assert coordenador.processar_sugestao_proativa(
        {"relevante": True, "categoria": "companhia", "confianca": 0.90,
         "momento_seguro": True, "fala": "Que vista mais bonita!",
         "motivo": MOTIVO, "evidencias": FATOS},
        {"chave": "exe:justcause3"}, {},
    ) is True

    # Primeira fronteira: o produtor não pode rotular seu motivo como fato.
    assert eventos[0]["evidencia"]["itens"] == FATOS
    assert eventos[0]["evidencia"]["motivo"] == MOTIVO


@pytest.mark.parametrize("dominio,motivo,fatos", [
    ("jogo", MOTIVO, FATOS),
    ("janela", "Oferta de companhia durante a tarefa.",
     ["janela Calculadora em primeiro plano", "expressão 2 + 2 visível"]),
])
def test_contrato_materializa_ancora_factual_separada_do_motivo(
    dominio: str, motivo: str, fatos: list[str],
) -> None:
    diretor, estado, _eventos = _diretor()
    resultado = diretor.considerar({
        "origem": f"observador_{dominio}", "dominio": dominio,
        "categoria": "companhia", "confianca": 0.95, "momento_seguro": True,
        "chave": "fonte-factual", "motivo": motivo, "evidencias": fatos,
    })

    assert resultado["status"] == "proposta_cognitiva"
    roteiro = resultado["contrato_fala"]["roteiro_concreto"]
    assert motivo not in roteiro["ancora_literal"]
    assert roteiro["ancora_literal"] == fatos[0]
    assert resultado["contrato_fala"]["evidencias_factuais"] == fatos
    assert resultado["contrato_fala"]["motivo_evento"] == motivo
    assert resultado["contrato_fala"]["autoriza_execucao"] is False
    assert estado["ultima_emissao"] == {}


def test_motivo_sem_fatos_nao_materializa_fala_generica() -> None:
    contrato = construir_contrato_semantico_evento({
        "natureza": "evento", "tipo": "presenca_companhia", "conteudo": MOTIVO,
        "evidencia": {"itens": [], "motivo": MOTIVO, "categoria": "companhia"},
        "autoridade_usuario": False, "permissao_execucao": False,
    })
    assert contrato["motivo_evento"] == MOTIVO
    assert contrato["roteiro_concreto"]["ancora_literal"] == ""
    assert compor_reacao_evento_local(contrato) == ""


def test_evento_legado_sem_motivo_preserva_descricao_factual() -> None:
    fato = "Uma ponte suspensa liga as duas encostas."
    contrato = construir_contrato_semantico_evento({
        "natureza": "evento", "tipo": "presenca_companhia", "conteudo": fato,
        "evidencia": {"descricao": fato, "categoria": "companhia"},
        "autoridade_usuario": False, "permissao_execucao": False,
    })
    assert contrato["motivo_evento"] == ""
    assert contrato["roteiro_concreto"]["ancora_literal"] == fato
    assert fato in compor_reacao_evento_local(contrato)


def test_transporte_visual_coordenador_diretor_conserva_fato_longo_para_rejeitar() -> None:
    diretor, estado, eventos = _diretor()
    _fala, sugestao = extrair_presenca_visual(
        "PRESENCA_JOGO_JSON: " + json.dumps({
            "relevante": True, "categoria": "companhia", "fala": "Um detalhe observado.",
            "confianca": 0.95, "momento_seguro": True,
            "motivo": MOTIVO, "evidencias": [FATO_LONGO],
        }, ensure_ascii=False)
    )
    assert _coordenador(diretor).processar_sugestao_proativa(
        sugestao, {"chave": "exe:justcause3"}, {},
    ) is True
    assert eventos[0]["evidencia"]["itens"] == [FATO_LONGO]
    contrato = estado["ultima_proposta_cognitiva"]["contrato_fala"]
    assert compor_reacao_evento_local(contrato) == ""


def test_contrato_direto_conserva_fonte_longa_e_compositor_rejeita_sem_cortar() -> None:
    contrato = construir_contrato_semantico_evento({
        "natureza": "evento", "tipo": "presenca_companhia",
        "evidencia": {"itens": [FATO_LONGO], "motivo": MOTIVO, "categoria": "companhia"},
        "autoridade_usuario": False, "permissao_execucao": False,
    })
    assert contrato["evidencias_factuais"] == [FATO_LONGO]
    assert contrato["ancora_factual_completa"] == FATO_LONGO
    assert compor_reacao_evento_local(contrato) == ""
