"""O pedido literal de esclarecer continua obrigatório em uma fala composta."""
from copy import deepcopy
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada


def preparar(texto, fala='Eu prefiro jazz, mas descrevi isso de um jeito confuso.'):
    registro = registrar_fala_observada(None, ocorrencia_id='publicacao', turno_id='anterior',
        fala=fala, resultados=(), canal='texto_publicado')
    mente = {'registro_semantico': registro, 'ultima_resposta': fala}
    turno = classificar_modalidade_turno(texto)
    mente['turno_atual'] = turno
    plano = planejar_turno(texto, turno=turno, mente=mente)
    return turno, plano, mente, fala


@pytest.mark.parametrize('texto', [
    'como assim? voce nao tem nenhum em especifico?',
    'como assim? você pode ser mais clara?',
    'o que você quis dizer? você está falando da música?',
])
@pytest.mark.parametrize('fala', [
    'Eu prefiro jazz, mas descrevi isso de um jeito confuso.',
    'Eu escolheria o aplicativo de notas, mas expliquei mal o critério.',
    'A luz segue desligada segundo a leitura anterior, não uma medição atual.',
])
def test_esclarecimento_composto_mantem_ancora_e_recusa_repetir_a_fala(texto, fala):
    turno, plano, mente, fala = preparar(texto, fala)
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert 'esclarecimento' in contrato['atos']
    assert contrato['fala_anterior_relevante'] == fala
    assert contrato['roteiro_concreto']['estrategia'] == 'esclarecimento_literal'
    assert contrato['referencia_fala_observada'].conteudo == fala
    parecer = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato, turno_id=plano['id'])
    assert 'esclarecimento_sem_explicacao' in parecer['problemas']
    assert not contrato['autoriza_execucao']


@pytest.mark.parametrize('texto', [
    'a frase "como assim?" é uma pergunta?',
    'o João perguntou como assim? você gosta de jazz?',
    'qual música? você gosta de jazz?',
])
def test_texto_citado_ou_outro_agente_nao_cria_esclarecimento(texto):
    turno, plano, mente, _ = preparar(texto)
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert 'esclarecimento' not in contrato['atos']


def test_segmento_sem_vinculo_literal_nao_cria_pedido_de_esclarecimento():
    texto = 'qual música? você gosta de jazz?'
    turno, plano, mente, _ = preparar(texto)
    turno = deepcopy(turno)
    turno['segmentos'][0]['texto'] = turno['segmentos'][0]['texto_estrutural'] = 'como assim?'
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert 'esclarecimento' not in contrato['atos']


def test_consulta_a_duas_publicacoes_nao_produz_referencia_unica():
    from mente_laylay.memoria_mental.registro_semantico import construir_referencia_fala_consulta
    fala1, fala2 = 'Eu prefiro jazz para esta conversa.', 'Eu escolheria o aplicativo de notas.'
    texto = f'como assim? você disse {fala1} e {fala2}?'
    turno, plano, mente, _ = preparar(texto, fala1)
    mente['registro_semantico'] = registrar_fala_observada(mente['registro_semantico'],
        ocorrencia_id='outra_publicacao', turno_id='outro', fala=fala2, resultados=(), canal='texto_publicado')
    assert construir_referencia_fala_consulta(texto, turno_id=plano['id'], mente=mente, turno=turno) is None


def test_projecao_nao_empresta_turno_estrangeiro():
    from mente_laylay.memoria_mental.registro_semantico import construir_referencia_fala_consulta
    texto = 'o que você quis dizer? você está falando da música?'
    turno, plano, mente, _ = preparar(texto)
    assert construir_referencia_fala_consulta(texto, turno_id='estrangeiro', mente=mente, turno=turno) is None
