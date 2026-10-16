"""Visão operacional vazia por veto não perde identidade nem concede efeito."""
from copy import deepcopy
import json

import pytest

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_turno import (
    filtrar_comandos_pelo_turno, motivo_divergencia_ocorrencia_principal,
    motivo_incoerencia_contratos_turno,
)
from mente_laylay.cognicao.modalidade_turno import aplicar_veto_canonico, classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    alinhar_identidade_plano_revisao, registrar_leitura_semantica_principal,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_principal
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


def frame_bloqueado(texto):
    revisao = resolver_revisao_intra_turno(texto)
    assert revisao["detectada"] and (not revisao["resolvida"] or revisao["cancelada"])
    cancelada = revisao["cancelada"]
    turno = classificar_modalidade_turno(texto)
    turno.update(texto=texto, texto_original=texto, texto_operacional_efetivo="", revisao_intra_turno=revisao)
    turno = aplicar_veto_canonico(turno, texto=texto,
        modalidade="recusa" if cancelada else "correcao",
        natureza="cancelamento_revisao" if cancelada else "revisao_ambigua",
        motivo=revisao["motivo"], requer_esclarecimento=not cancelada,
        origem_veto="revisao_cancelada" if cancelada else "revisao_ambigua")
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = alinhar_identidade_plano_revisao(planejar_turno(texto, turno=turno, mente={}),
        texto_original=texto, texto_operacional_efetivo="", revisao_intra_turno=revisao)
    return {"turno_atual": turno, "plano_turno_atual": plano, "retrato_turno_atual": retrato}


def motivo(frame):
    return motivo_incoerencia_contratos_turno(frame["turno_atual"], frame["plano_turno_atual"], frame["retrato_turno_atual"])


@pytest.mark.parametrize("texto", [
    "abre o aplicativo Calculadora; deixa ela à esquerda; não liga a luz",
    "abre o aplicativo Calculadora... não abre",
    "apaga o arquivo notas.txt... não apaga",
    "liga a luz... não liga",
    "pausa a música... não pausa",
    "cria um arquivo teste.txt... na verdade alguma outra coisa",
    "abre\t o aplicativo\nCalculadora... não abre",
    pytest.param("abre " + " " * 520 + "o aplicativo Calculadora... não abre",
        marks=pytest.mark.xfail(strict=True,
            reason="fronteira anterior: projeções de identidade truncam espaços em ordens diferentes")),
])
def test_revisao_bloqueada_tem_frame_coerente_e_proposta_vinculada_sem_permissao(texto):
    frame = frame_bloqueado(texto)
    antes = deepcopy(frame)
    turno, plano, retrato = (frame[k] for k in ("turno_atual", "plano_turno_atual", "retrato_turno_atual"))
    assert turno["texto_operacional_efetivo"] == plano["texto_operacional_efetivo"] == ""
    assert turno["veto_execucao_operacional"] is True
    assert turno["autoriza_execucao"] is plano["decisao_turno"]["permite_acao"] is False
    assert motivo(frame) == "", "primeira fronteira: veto legítimo tratado como perda de identidade"
    proposta = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario=texto,
        resposta_bruta=json.dumps({"fala": "Nenhuma ação executada.", "leitura_turno": ["recusa"], "comandos": []}))
    assert motivo_divergencia_ocorrencia_principal(proposta, turno=turno, plano=plano, retrato=retrato) == ""
    resultado = filtrar_comandos_pelo_turno([{"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}],
        turno=turno, plano=plano, retrato=retrato, proposta_principal=proposta)
    assert resultado["ocorrencia_vinculada"] is True
    assert resultado["proposta_vinculada"] is True
    assert resultado["autoriza_execucao"] is False and resultado["comandos"] == []
    assert frame == antes
    estado = EstadoCompartilhadoRuntime(mental=frame)
    leitura = extrair_leitura_semantica_principal(proposta, texto)
    registrada = registrar_leitura_semantica_principal(
        lambda: {"_estado_compartilhado_runtime": estado, "print": lambda *_: None},
        texto, leitura, proposta_principal=proposta)
    assert registrada
    depois = estado.snapshot()["mental"]
    depois["turno_atual"].pop("leitura_semantica_principal", None)
    assert all(depois[k] == antes[k] for k in antes)


@pytest.mark.parametrize("caminho,valor", [
    (("turno_atual", "autoriza_execucao"), True),
    (("turno_atual", "autoriza_execucao"), "False"),
    (("turno_atual", "veto_execucao_operacional"), False),
    (("turno_atual", "origem_veto_execucao_operacional"), "outro"),
    (("turno_atual", "natureza_acao"), "pedido_direto"),
    (("turno_atual", "modalidade"), "comando"),
    (("plano_turno_atual", "requer_execucao"), True),
    (("plano_turno_atual", "autoriza_execucao"), True),
    (("plano_turno_atual", "veto_execucao_operacional"), False),
    (("plano_turno_atual", "decisao_turno", "permite_acao"), True),
    (("plano_turno_atual", "decisao_turno", "proprietario"), "operacional"),
    (("turno_atual", "texto_operacional_efetivo"), "abre a Calculadora"),
    (("retrato_turno_atual", "texto"), "outra fala"),
    (("plano_turno_atual", "revisao_intra_turno"), {}),
    (("turno_atual", "revisao_intra_turno"), {}),
    (("retrato_turno_atual", "id"), "outro"),
])
def test_vazio_arbitrario_ou_contraditorio_nao_herda_validade_do_bloqueio(caminho, valor):
    frame = frame_bloqueado("abre o aplicativo Calculadora... não abre")
    destino = frame
    for chave in caminho[:-1]:
        destino = destino[chave]
    destino[caminho[-1]] = valor
    assert motivo(frame)


@pytest.mark.parametrize("alterar", [
    {"detectada": "True"}, {"resolvida": False}, {"cancelada": False},
    {"tipo": "substituicao_comando"}, {"texto_original": "outro pedido"},
    {"texto_operacional_efetivo": "abre a Calculadora"},
])
def test_duas_copias_de_revisao_igualmente_invalidas_nao_provam_coerencia(alterar):
    frame = frame_bloqueado("abre o aplicativo Calculadora... não abre")
    for nome in ("turno_atual", "plano_turno_atual"):
        frame[nome]["revisao_intra_turno"] = {**frame[nome]["revisao_intra_turno"], **alterar}
    assert motivo(frame)


def test_frame_bloqueado_coerente_nao_revalida_proposta_de_outra_ocorrencia():
    texto = "abre o aplicativo Calculadora... não abre"
    frame = frame_bloqueado(texto)
    proposta = ContratoPropostaPrincipal(turno_id="outra", texto_usuario=texto, resposta_bruta='{"fala":"Oi"}')
    assert "outra ocorrência" in motivo_divergencia_ocorrencia_principal(proposta,
        turno=frame["turno_atual"], plano=frame["plano_turno_atual"], retrato=frame["retrato_turno_atual"])
