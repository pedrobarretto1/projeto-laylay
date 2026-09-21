"""A contingência realiza o ato canônico sem inventar domínio ou efeito."""

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


@pytest.mark.parametrize("texto", (
    "preciso que você não pause a música",
    "não abra a calculadora",
    "não apague o arquivo notas.txt",
    "não ligue a lâmpada",
    "não feche o Opera",
    "não liste os programas abertos",
))
def test_recusa_generica_nao_e_rebatizada_como_consulta(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False
    plano = planejar_turno(texto, turno=turno, mente={})
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "negacao_operacional_sem_efeito"
    fala = contingencia_comunicacao(texto, contrato_reparo=roteiro)
    assert "consulta" not in fala.casefold(), fala
    assert "não vou" in fala.casefold(), fala
    assert validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato)["aceita"]
    assert not plano.get("comandos")


def test_correcao_de_pergunta_mantem_reconhecimento_especifico():
    assert contingencia_comunicacao(
        "Eu não perguntei se o Discord está aberto.",
        contrato_reparo={"estrategia": "negacao_operacional_sem_efeito"},
    ) == "Tem razão, você não perguntou isso."


@pytest.mark.parametrize("resposta_reparo", ("{}", '{"fala":"A música já está pausada.","comandos":[]}'))
def test_pipeline_de_reparo_falho_preserva_recusa_sem_inventar_consulta(resposta_reparo):
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao

    texto = "preciso que você não pause a música"
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, mente={},
    )
    chamadas = []

    def responder(*args, **kwargs):
        chamadas.append(True)
        return resposta_reparo

    resultado = preparar_resposta_para_execucao(
        texto, '{"fala":"A música já está pausada.","comandos":[]}',
        enviar_mensagem_cb=responder,
        limpar_texto_fala_cb=lambda t: t, fallback_fala="Contingência",
        memoria_sqlite=None, contexto_comunicacao={"plano_turno": plano},
        log=lambda t: None,
    )
    assert chamadas, "o teste precisa chegar ao reparo, não parar antes dele"
    assert resultado["comandos"] == []
    assert resultado["fala"] == "Entendi, não vou executar essa ação."
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    final = verificar_fala_turno(resultado["fala"], plano=plano, origem="ia_final")
    assert final["aceita"], final
    assert final["fala"] == resultado["fala"]


@pytest.mark.parametrize("fala", (
    "Entendi, não vou executar essa ação.",
    "Não vou abrir a calculadora.",
    "Eu não vou ligar a lâmpada.",
    "Nunca vou acionar esse dispositivo.",
    "Não vou fechar o Opera nem vou iniciar outro aplicativo.",
))
def test_negacao_local_de_promessa_nao_e_promessa_positiva(fala):
    from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
    r = validar_alegacoes_da_fala(fala, plano={"comandos": []}, origem="ia_final")
    assert "promessa_operacional_sem_comando" not in r["problemas"], r
    assert r["fala"] == fala


@pytest.mark.parametrize("fala", (
    "Vou executar essa ação.",
    "Não, vou abrir a calculadora.",
    "Não vou fechar o Opera, mas vou abrir a calculadora.",
    "Eu não vou desligar a lâmpada; vou ligar o ventilador.",
    "Vou abrir a calculadora, mas não vou fechar o Opera.",
))
def test_negacao_em_outra_oracao_nao_libera_promessa_sem_comando(fala):
    from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
    r = validar_alegacoes_da_fala(fala, plano={"comandos": []}, origem="ia_final")
    assert "promessa_operacional_sem_comando" in r["problemas"], r
