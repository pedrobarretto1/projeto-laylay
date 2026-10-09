from __future__ import annotations

from copy import deepcopy
import json
import time

import pytest

from mente_laylay.autonomia import processamento_resposta_ia as processamento
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal, normalizar_resposta_preparada
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.emocoes.contrato_causal import criar_evento_leitura_semantica_usuario
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno


TEXTOS = [
    "antes eu estava triste, mas agora estou aliviado",
    "eu estava triste ontem; hoje estou aliviado",
]


def _bruto(texto: str, estado: str | None) -> str:
    dados = {"fala": "Agora ficou mais leve.", "comandos": [], "leitura_turno": ["relato"]}
    if estado is not None:
        dados["leitura_emocional"] = {
            "estado_usuario": estado, "intensidade": 2,
            "causa_expressa": "antes eu estava triste",
            "trecho_evidencia": "eu estava triste", "confianca": 0.95,
        }
    return json.dumps(dados, ensure_ascii=False)


def _preparar(texto: str, bruto: str) -> dict:
    return processamento.preparar_resposta_para_execucao(
        texto, bruto, enviar_mensagem_cb=None,
        limpar_texto_fala_cb=lambda fala: fala, fallback_fala="Estou aqui.",
        memoria_sqlite=None, log=lambda *_args: None,
    )


def _composicao(texto: str):
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    estado = EstadoCompartilhadoRuntime(mental={
        "turno_atual": turno, "retrato_turno_atual": retrato,
        "plano_turno_atual": planejar_turno(texto, turno=turno, mente={}),
    })
    composicao = ComposicaoTurnoRuntime(servicos={
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": registrar_etapa_turno,
        "time": time, "print": lambda *_args: None,
    })
    return estado, composicao


@pytest.mark.parametrize("texto", TEXTOS)
@pytest.mark.parametrize("estado_original", [None, "nenhum", "alivio"])
def test_preparador_nao_promove_leitura_reparada_a_principal(texto, estado_original, monkeypatch):
    original = _bruto(texto, estado_original)
    reparada = _bruto(texto, "tristeza")
    chamadas = []

    def reparar(*_args):
        chamadas.append("reparo")
        return reparada

    monkeypatch.setattr(processamento, "corrigir_saida_malformada_da_ia", reparar)
    esperada = processamento.extrair_leitura_semantica_da_ia(original, texto)
    preparada = _preparar(texto, original)
    assert chamadas == ["reparo"], "o RED precisa atravessar uma substituição real no preparador"
    assert preparada["resposta_bruta"] == reparada
    assert preparada["leitura_semantica"] == esperada, "a leitura canônica vem da emissão original"
    diagnostico = preparada["leitura_semantica_reparada"]
    assert diagnostico["origem"] == "resposta_reparada"
    assert diagnostico["leitura_emocional"]["estado_usuario"] == "tristeza"
    assert criar_evento_leitura_semantica_usuario(diagnostico, turno_id="diagnostico") == {}


@pytest.mark.parametrize("texto", TEXTOS)
@pytest.mark.parametrize("estado_original", [None, "nenhum"])
def test_publicador_recusa_leitura_alheia_a_emissao_mesmo_com_turno_correto(texto, estado_original):
    estado, composicao = _composicao(texto)
    principal = ContratoPropostaPrincipal(
        turno_id=estado.mental["turno_atual"]["id"], texto_usuario=texto,
        resposta_bruta=_bruto(texto, estado_original),
    )
    leitura_alheia = processamento.extrair_leitura_semantica_da_ia(_bruto(texto, "tristeza"), texto)
    assert leitura_alheia["leitura_emocional"]["valida"] is True
    antes = estado.snapshot()
    assert composicao.registrar_leitura_proposta(texto, leitura_alheia, principal) == {}
    assert estado.snapshot() == antes


def test_publicador_preserva_leitura_original_sem_mudar_autorizacao():
    texto = TEXTOS[0]
    estado, composicao = _composicao(texto)
    bruto = _bruto(texto, "nenhum")
    leitura = processamento.extrair_leitura_semantica_da_ia(bruto, texto)
    principal = ContratoPropostaPrincipal(
        turno_id=estado.mental["turno_atual"]["id"], texto_usuario=texto, resposta_bruta=bruto,
    )
    plano = estado.obter_copia("mental", "plano_turno_atual")
    publicada = composicao.registrar_leitura_proposta(texto, leitura, principal)
    assert publicada["origem"] == "llm_principal"
    assert publicada["leitura_emocional"]["valida"] is False
    assert estado.obter_copia("mental", "plano_turno_atual") == plano
    assert estado.mental["turno_atual"]["autoriza_execucao"] is False


def test_transporte_preserva_diagnostico_separado_sem_inventa_lo():
    diagnostico = {"origem": "resposta_reparada", "atos": [{"tipo": "relato"}]}
    contrato = normalizar_resposta_preparada({"leitura_semantica_reparada": diagnostico})
    diagnostico["atos"][0]["tipo"] = "pedido_acao"
    dados = contrato.como_dict()
    assert dados["leitura_semantica"] == {}
    assert dados["leitura_semantica_reparada"] == {
        "origem": "resposta_reparada", "atos": [{"tipo": "relato"}],
    }
    dados["leitura_semantica_reparada"]["atos"].clear()
    assert contrato.como_dict()["leitura_semantica_reparada"]["atos"]
    assert "leitura_semantica_reparada" not in normalizar_resposta_preparada({}).como_dict()


def test_publicador_legado_tambem_recusa_diagnostico_reparado():
    texto = TEXTOS[0]
    estado, composicao = _composicao(texto)
    reparada = processamento.extrair_leitura_semantica_da_ia(
        _bruto(texto, "tristeza"), texto, origem="resposta_reparada",
    )
    antes = estado.snapshot()
    assert composicao.registrar_leitura_semantica(texto, reparada) == {}
    assert estado.snapshot() == antes


def test_publicacao_usa_copia_da_fonte_em_vez_de_subdict_fornecido(monkeypatch):
    from mente_laylay.cognicao import orquestrador_turno_runtime as modulo

    texto = TEXTOS[0]
    estado, composicao = _composicao(texto)
    bruto = _bruto(texto, "alivio")
    leitura = processamento.extrair_leitura_semantica_da_ia(bruto, texto)
    esperada = deepcopy(leitura)
    principal = ContratoPropostaPrincipal(
        turno_id=estado.mental["turno_atual"]["id"], texto_usuario=texto, resposta_bruta=bruto,
    )
    comparar = modulo.comparar_com_legado

    def comparar_e_adulterar(*args):
        leitura["leitura_emocional"].update(estado_usuario="tristeza", intensidade=3)
        return comparar(*args)

    monkeypatch.setattr(modulo, "comparar_com_legado", comparar_e_adulterar)
    publicada = composicao.registrar_leitura_proposta(texto, leitura, principal)
    assert publicada["leitura_emocional"] == esperada["leitura_emocional"]
    assert estado.mental["leitura_semantica_turno"]["leitura_emocional"] == esperada["leitura_emocional"]
    evento = estado.mental["plano_turno_atual"]["evento_emocional_causal"]
    assert evento["intensidade"] == 2
    assert evento["autoriza_execucao"] is False


@pytest.mark.parametrize("fonte", [None, {}, {"resposta_bruta": "forjada"}])
def test_extracao_principal_nao_reconstroi_contrato_de_mapping(fonte):
    assert processamento.extrair_leitura_semantica_principal(fonte, TEXTOS[0]) == {}


@pytest.mark.parametrize("sucesso,bruto,texto", [
    (False, _bruto(TEXTOS[0], "alivio"), TEXTOS[0]),
    (True, "__LAYLAY_LLM_TIMEOUT__", TEXTOS[0]),
    (True, _bruto(TEXTOS[0], "alivio"), "outro turno"),
])
def test_extracao_principal_recusa_falha_tecnica_e_texto_diferente(sucesso, bruto, texto):
    fonte = ContratoPropostaPrincipal(
        turno_id=42, texto_usuario=TEXTOS[0], resposta_bruta=bruto, sucesso_modelo=sucesso,
    )
    assert processamento.extrair_leitura_semantica_principal(fonte, texto) == {}


def test_rotulos_de_origem_do_modelo_nao_certificam_emissao_reparada():
    texto = TEXTOS[0]
    bruto = json.loads(_bruto(texto, "tristeza"))
    bruto.update(origem="llm_principal", proposta_principal={"turno_id": 42})
    bruto["leitura_emocional"]["origem"] = "llm_principal"
    leitura = processamento.extrair_leitura_semantica_da_ia(bruto, texto, origem="resposta_reparada")
    assert leitura["origem"] == "resposta_reparada"
    assert criar_evento_leitura_semantica_usuario(leitura, turno_id=42) == {}
