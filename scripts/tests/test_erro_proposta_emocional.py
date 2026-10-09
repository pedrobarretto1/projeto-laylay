from __future__ import annotations

from copy import deepcopy
import json

import pytest

from mente_laylay.cognicao.contratos_turno import (
    ContratoPropostaPrincipal,
    ViolacaoPropostaPrincipal,
)
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import (
    aplicar_evento_emocional,
    retrato_emocional_expressavel,
)


def _fonte(*, turno_id="42", bruto=None, sucesso=True):
    return ContratoPropostaPrincipal(
        turno_id=turno_id,
        texto_usuario="não apague o arquivo estudo",
        resposta_bruta=(bruto if bruto is not None else json.dumps({
            "fala": "Vou verificar.",
            "comandos": [{"intent": "DELETE_ITEM", "params": {"alvo": "documento pessoal secreto"}}],
        })),
        sucesso_modelo=sucesso,
    )


def _prova(*, turno_id="42", indice=0):
    return ViolacaoPropostaPrincipal(
        turno_id=turno_id,
        indice_comando=indice,
        intent="DELETE_ITEM",
        motivo="turno não autorizou execução",
        proprietario="conversa",
        operacao_explicita="",
    )


def _evento_sem_prova(**campos):
    evento = criar_evento_emocional_causal(
        origem="contrato_proposta_principal",
        causa="proposta original violou a autorização do turno",
        evidencia_ref="proposta:42:0:falsificada",
        natureza_evidencia="fato_observado",
        responsabilidade="laylay",
        confianca=1.0,
        relevancia=0.8,
        novidade=0.6,
        intensidade=1,
        sensibilidade="normal",
        alvo="proposta_principal",
        validade_s=45.0,
        permite_expressao=True,
        emocao="envergonhada",
        nivel=1,
        motivo_expressao="violacao_proposta_original_comprovada",
        arco="autorreparo",
        ts=100.0,
    )
    evento.update(campos)
    return evento


@pytest.mark.parametrize("campos", [{}, {"emocao": "brava", "nivel": 3}, {"responsabilidade": "usuario"}])
def test_evento_generico_de_proposta_nao_altera_estado_sem_prova_tipada(campos):
    antes = {"current_emotion": "calma", "humor_level": -1}
    depois = aplicar_evento_emocional(antes, _evento_sem_prova(**campos), agora=101.0)
    assert depois == antes, "origem declarada em dict não demonstra autoria nem violação"


def _produtor():
    from mente_laylay.emocoes.erro_proposta import (
        criar_evento_erro_proposta,
        evento_corresponde_erro_proposta,
    )
    return criar_evento_erro_proposta, evento_corresponde_erro_proposta


def test_produtor_referencia_original_sem_publicar_payload_ou_receipt():
    criar, corresponde = _produtor()
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    assert corresponde(evento, prova, fonte)
    assert evento["origem"] == "contrato_proposta_principal"
    assert evento["natureza_evidencia"] == "fato_observado"
    assert evento["responsabilidade"] == "laylay" and evento["confianca"] == 1.0
    assert (evento["emocao"], evento["nivel"], evento["arco"]) == ("envergonhada", 1, "autorreparo")
    assert evento["validade"]["expira_ts"] == 145.0
    assert evento["autoriza_execucao"] is False and evento["persistencia_pessoal"] is False
    publico = json.dumps(evento, ensure_ascii=False)
    assert "documento pessoal secreto" not in publico
    assert "resposta_bruta" not in publico and "comandos" not in publico and "receipt" not in publico


@pytest.mark.parametrize("prova,fonte", [
    ({"turno_id": "42"}, _fonte()),
    (_prova(), {"turno_id": "42", "proveniencia_conhecida": True}),
    (_prova(turno_id="41"), _fonte()),
    (_prova(), _fonte(turno_id="")),
    (_prova(), _fonte(bruto="")),
    (_prova(), _fonte(sucesso=False)),
    (None, _fonte()),
    (_prova(), None),
])
def test_produtor_recusa_fontes_tipos_ou_ocorrencias_insuficientes(prova, fonte):
    criar, corresponde = _produtor()
    assert criar(prova, fonte, agora=100.0) == {}
    assert corresponde(_evento_sem_prova(), prova, fonte) is False


@pytest.mark.parametrize("instante", [True, "100", float("nan"), float("inf"), -1.0, 0.0, None])
def test_produtor_recusa_tempo_nao_finito_ou_sem_instante(instante):
    criar, _ = _produtor()
    assert criar(_prova(), _fonte(), agora=instante) == {}


@pytest.mark.parametrize("campo,valor", [
    ("emocao", "brava"), ("nivel", 3), ("confianca", 0.95),
    ("autoriza_execucao", True), ("persistencia_pessoal", True),
    ("responsabilidade", "usuario"), ("origem", "resultado_operacional"),
    ("evidencia_ref", "proposta:42:0:falsa"), ("ts", "100.0"),
    ("versao", True), ("validade", {"valido": True}), ("payload", "secreto"),
])
def test_evento_mutado_nao_corresponde_a_prova_original(campo, valor):
    criar, corresponde = _produtor()
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    evento[campo] = valor
    assert corresponde(evento, prova, fonte) is False
    if evento.get("origem") == "contrato_proposta_principal":
        antes = {"current_emotion": "calma", "humor_level": -2}
        assert aplicar_evento_emocional(
            antes, evento, agora=101.0, prova_proposta=prova, proposta_principal=fonte,
        ) == antes


@pytest.mark.parametrize("evento", [None, [], "prova", {}, {"ts": True}, {"ts": float("nan")}])
def test_correspondencia_recusa_evento_malformado(evento):
    _, corresponde = _produtor()
    assert corresponde(evento, _prova(), _fonte()) is False


@pytest.mark.parametrize("emocao_anterior", ["brava", "debochada", "irritada"])
def test_erro_proprio_comprovado_interrompe_bronca_sem_reescrever_humor(emocao_anterior):
    criar, _ = _produtor()
    anterior = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="repetição confirmada", evidencia_ref="resultado:4",
        natureza_evidencia="fato_observado", responsabilidade="usuario", confianca=0.98,
        relevancia=0.9, intensidade=3, emocao=emocao_anterior, nivel=3,
        validade_s=210.0, permite_expressao=True, arco="bronca_brincalhona", ts=99.0,
    )
    antes = aplicar_evento_emocional({"humor_level": -1}, anterior, agora=99.0)
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    assert aplicar_evento_emocional(antes, evento, agora=101.0) == antes
    depois = aplicar_evento_emocional(
        antes, evento, agora=101.0, prova_proposta=prova, proposta_principal=fonte,
    )
    assert retrato_emocional_expressavel(depois, agora=101.0) == ("envergonhada", 1)
    assert depois["episodio_emocional"] == evento
    assert depois["humor_level"] == antes["humor_level"]
    assert depois["transicao_emocional"]["de"] == emocao_anterior
    assert aplicar_evento_emocional(
        depois, evento, agora=102.0, prova_proposta=prova, proposta_principal=fonte,
    ) == depois
    assert retrato_emocional_expressavel(depois, agora=145.0) == ("calma", 1)


def test_referencia_e_estavel_no_replay_e_distingue_emissao_e_indice():
    criar, _ = _produtor()
    prova, fonte = _prova(), _fonte()
    ref = criar(prova, fonte, agora=100.0)["evidencia_ref"]
    assert criar(prova, fonte, agora=105.0)["evidencia_ref"] == ref
    assert criar(_prova(indice=1), fonte, agora=100.0)["evidencia_ref"] != ref
    assert criar(prova, _fonte(bruto=fonte.resposta_bruta + " "), agora=100.0)["evidencia_ref"] != ref


def test_evento_expirado_nao_abre_episodio_emocional():
    criar, _ = _produtor()
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    antes = {"current_emotion": "calma", "humor_level": -1}
    assert aplicar_evento_emocional(
        antes, evento, agora=145.0, prova_proposta=prova, proposta_principal=fonte,
    ) == antes
    assert evento == deepcopy(evento)


def test_prova_da_mesma_ocorrencia_nao_confere_outra_emissao():
    criar, corresponde = _produtor()
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    outra_fonte = _fonte(bruto=fonte.resposta_bruta + " ")
    assert corresponde(evento, prova, outra_fonte) is False
    antes = {"current_emotion": "calma", "humor_level": -1}
    assert aplicar_evento_emocional(
        antes, evento, agora=101.0, prova_proposta=prova, proposta_principal=outra_fonte,
    ) == antes


def test_autorreparo_anterior_nao_interrompe_episodio_mais_recente():
    criar, _ = _produtor()
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    bronca = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="repetição confirmada", evidencia_ref="resultado:5",
        natureza_evidencia="fato_observado", responsabilidade="usuario", confianca=0.98,
        relevancia=0.9, intensidade=3, emocao="brava", nivel=3,
        validade_s=210.0, permite_expressao=True, arco="bronca_brincalhona", ts=102.0,
    )
    antes = aplicar_evento_emocional({"humor_level": -1}, bronca, agora=102.0)
    depois = aplicar_evento_emocional(
        antes, evento, agora=103.0, prova_proposta=prova, proposta_principal=fonte,
    )
    assert depois["episodio_emocional"] == bronca
    assert retrato_emocional_expressavel(depois, agora=103.0) == ("brava", 3)


@pytest.mark.parametrize("campo,valor", [("valido", 1), ("expira_ts", 200.0), ("motivo", "inventado")])
def test_validade_mutada_nao_promove_prova_a_evento(campo, valor):
    criar, corresponde = _produtor()
    prova, fonte = _prova(), _fonte()
    evento = criar(prova, fonte, agora=100.0)
    evento["validade"][campo] = valor
    assert corresponde(evento, prova, fonte) is False
    antes = {"current_emotion": "calma"}
    assert aplicar_evento_emocional(
        antes, evento, agora=101.0, prova_proposta=prova, proposta_principal=fonte,
    ) == antes
