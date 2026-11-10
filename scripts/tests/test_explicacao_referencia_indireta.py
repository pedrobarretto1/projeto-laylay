"""Consulta ao dizer não herda uma pergunta sobre execução inexistente."""
from mente_laylay.cognicao.explicacao_fala_historica import (
    avaliar_fala_historica, realizacoes_fala_historica,
)
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, recuperar_evidencia_da_fala


def test_referencia_ao_dizer_sem_receipt_nao_vira_informe_operacional():
    texto = 'Por que você disse que não pode abrir esse arquivo?'
    registro = registrar_fala_observada(None, ocorrencia_id='fonte', turno_id='anterior',
        fala='Eu não posso abrir esse arquivo sem autorização.', resultados=(), canal='texto_publicado')
    evidencia = recuperar_evidencia_da_fala(texto, {'registro_semantico': registro})
    assert evidencia and evidencia['origem_referencia'] == 'conteudo_indireto'
    respostas = realizacoes_fala_historica(evidencia)
    assert respostas
    assert all('motivo' in r.casefold() and 'registrad' in r.casefold() for r in respostas)
    assert all('resultado operacional' not in r.casefold() for r in respostas)
    assert all('porque' not in r.casefold() for r in respostas)


def test_fonte_do_dizer_nao_comprova_justificativa_proposta_pelo_modelo():
    texto = 'Entendi. Por que você disse que não consegue inventar?'
    registro = registrar_fala_observada(None, ocorrencia_id='fonte', turno_id='anterior',
        fala='Eu não consigo inventar de novo o que não existe.', resultados=(), canal='texto_publicado')
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno,
        plano=plano, mente={'registro_semantico': registro})
    fonte = plano['contrato_fala']['explicacoes_historicas_por_ato']
    assert fonte.partes[-1].fala.como_dict()['falas'][0]['id'] == 'fonte'
    falsa = 'Eu disse isso porque o servidor caiu e não posso mais criar histórias.'
    revisao = avaliar_fala_historica(falsa, plano=plano)
    assert revisao['fonte_valida'] and revisao['fala'] != falsa
    assert 'servidor caiu' not in revisao['fala']
    assert revisao['autoriza_execucao'] is revisao['prova_semantica_livre'] is False
