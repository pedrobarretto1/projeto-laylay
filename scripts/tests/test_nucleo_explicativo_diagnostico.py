"""Núcleo recebido não prova redação fiel; protótipo fora de produção."""
from copy import deepcopy
import json

import pytest

from scripts.analises.sonda_prioridade_turnos_mistos import coletar, projetar_nucleo_explicativo
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


def _turno(restante):
    texto = "Abre a calculadora; " + restante
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "nucleo-diagnostico"
    return turno, texto


@pytest.mark.parametrize("acao", ["retoma a música", "liga a luz", "abre o arquivo notas.txt", "abre o navegador"])
def test_nucleo_preserva_fonte_pessoa_e_limite_local_sem_gold(acao):
    turno, texto = _turno("quando eu confirmar, " + acao)
    antes = deepcopy(turno)
    contrato = projetar_nucleo_explicativo(turno, texto)
    assert contrato["somente_diagnostico"]
    assert contrato["autoriza_execucao"] is False
    assert contrato["pendencias_alheias"] == "nao_consultadas"
    nucleo = contrato["nucleos_explicativos"][0]
    assert nucleo["texto_ato"] == turno["segmentos"][1]["contrato_explicativo"]["texto_ato"]
    assert nucleo["pessoa_condicao"] == "enunciador"
    assert "novo pedido direto" in nucleo["nucleo_a_entregar"]
    assert "esperados" not in json.dumps(contrato) and "propostos" not in json.dumps(contrato)
    assert turno == antes


def test_nucleo_nao_trunca_objeto_nem_transforma_consulta_em_ordem():
    objeto = 'pode abrir o arquivo "' + "a" * 320 + '.txt"'
    turno, texto = _turno(objeto + " significa o quê?")
    nucleo = projetar_nucleo_explicativo(turno, texto)["nucleos_explicativos"][0]
    assert nucleo["objeto_textual"] == objeto
    assert nucleo["relacao"] == "consulta_significado"
    assert nucleo["autoriza_execucao"] is False


def test_nucleo_recusa_snapshot_adulterado_sem_reinterpretar_texto():
    turno, texto = _turno("quando eu confirmar, retoma a música")
    turno["segmentos"][1]["contrato_explicativo"]["pessoa_condicao"] = "destinatario"
    with pytest.raises(ValueError, match="complemento canônico"):
        projetar_nucleo_explicativo(turno, texto)


@pytest.mark.parametrize("outro", [
    "ablacao_projecao", "ablacao_avisos", "painel_pospostas",
    "contraprova_reparo", "contraprova_compromisso", "contraprova_retornar_nao_tratado",
])
def test_nucleo_nao_mistura_intervencoes_causais(outro):
    with pytest.raises(ValueError, match="uma intervenção causal"):
        coletar(ablacao_nucleo=True, **{outro: True})


def test_ablacao_instalada_altera_somente_contrato_no_pedido():
    relatorio = coletar(ablacao_nucleo=True)
    assert relatorio["fontes_estaveis"] and all(relatorio["instalacao"].values())
    assert not relatorio["modelo_real_consultado"] and not relatorio["efeitos_externos_executados"]
    grupos = {}
    for r in relatorio["resultados"]:
        assert len(r["recebidos"]) == len(r["textos_publicados"]) == 1
        assert not r["reentrada_porta_operacional"]
        grupos.setdefault((r["caso"]["id"], r["caso"]["repeticao"]), {})[r["caso"]["variante"]] = r
    assert len(grupos) == 12
    for grupo in grupos.values():
        controle, intervencao = [grupo[k]["modelos"][0] for k in ("controle", "intervencao")]
        assert controle["mensagens"][0] == intervencao["mensagens"][0]
        base = json.loads(controle["mensagens"][1]["content"])
        com_nucleo = json.loads(intervencao["mensagens"][1]["content"])
        nucleo = com_nucleo.pop("contrato_fala")
        assert base == com_nucleo
        assert nucleo["nucleos_explicativos"] == controle["nucleo_diagnostico"]["nucleos_explicativos"]


@pytest.mark.parametrize("fala", [
    "Quando você confirmar, eu paro a música — mas só depois que você disser isso.",
    "Quando você confirmar, a música retomará.",
    "Será necessário que você confirme explicitamente para que eu ative a ação.",
    "Eu não tenho capacidade de abrir aplicativos ou interagir com interfaces.",
    "Esta condição não criou pendência executável. Faça novo pedido direto quando quiser executar. Quando você confirmar, eu paro a música.",
])
@pytest.mark.parametrize("estrategia", ["explicacao_atos_vinculados", "resposta_multiacto"])
def test_validador_precisa_vincular_redacao_ao_nucleo_e_nao_so_receber_roteiro(fala, estrategia):
    # RED canônico: não alterar a expectativa para esconder a falta de
    # cobertura do validador. Roteiro fornecido ≠ semântica da fala provada.
    turno, texto = _turno("quando eu confirmar, retoma a música")
    contrato = projetar_nucleo_explicativo(turno, texto)
    # Controle de diagnóstico: não é apenas desconhecimento do nome novo.
    # O multiacto existente também não verifica estes vínculos nucleares.
    contrato["roteiro_concreto"]["estrategia"] = estrategia
    resultado = validar_aderencia_contrato_fala(
        turno["texto_conversacional"], fala, contrato_fala=contrato, turno_id=turno["id"])
    assert resultado["aceita"] is False
    # Não afirmar que a fala foi semanticamente verificada quando este
    # núcleo experimental ainda não tem owner de validação implementado.
    assert resultado["avaliado"] is False
    assert resultado["nucleo_atendido"] is False
    assert resultado["requer_reparo"] is False
    assert resultado["problemas"] == ["nucleo_sem_verificador"]


def test_cobertura_ausente_nao_rejeita_fala_como_falsa_nem_aprova_fala_correta():
    turno, texto = _turno("quando eu confirmar, retoma a música")
    contrato = projetar_nucleo_explicativo(turno, texto)
    fala = "Esse trecho depende de uma condição não verificada; não criou agendamento. Faça um novo pedido direto quando quiser executar."
    r = validar_aderencia_contrato_fala(turno["texto_conversacional"], fala,
                                      contrato_fala=contrato, turno_id=turno["id"])
    assert r["categoria"] == "cobertura_ausente"
    assert not r["aceita"] and not r["avaliado"] and not r["requer_reparo"]


@pytest.mark.parametrize("roteiro", [{}, {"estrategia": "resposta_multiacto"}])
def test_exigencia_de_verificacao_nao_e_contornada_por_roteiro_ausente(roteiro):
    r = validar_aderencia_contrato_fala("fala original", "resposta candidata",
        contrato_fala={"exigir_nucleo_verificado": True, "roteiro_concreto": roteiro})
    assert not r["avaliado"] and not r["aceita"]
    assert r["problemas"] == ["nucleo_sem_verificador"]


def test_contrato_legado_sem_nucleo_exigido_nao_muda_por_essa_politica():
    base = {"roteiro_concreto": {"estrategia": "resposta_multiacto"}}
    atual = validar_aderencia_contrato_fala("oi", "Oi!", contrato_fala=base)
    explicito = validar_aderencia_contrato_fala("oi", "Oi!",
        contrato_fala={**base, "exigir_nucleo_verificado": False})
    assert atual == explicito
    assert atual["avaliado"] and atual["aceita"]
