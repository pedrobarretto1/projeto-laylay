"""Uma fonte de contexto não cria finalidade de explicação histórica."""
from copy import deepcopy

import pytest

from scripts.tests.test_explicacao_fala_historica import plano_historico
from scripts.tests.test_explicacao_historica_por_ato import consulta, owner_dois_dominios
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


FICCAO = (
    'Gosto, sim! Às vezes um detalhe pequeno transforma uma história inteira. Imagine que esse robozinho encontra uma carta esquecida debaixo da árvore. O que estaria escrito nela?',
    'Sem problema, vamos só brincar com ideias. Se um robozinho fosse seu mascote numa história fictícia, que nome divertido você daria a ele?',
    'Gostei desse garoto com o caderno. Ele parece perceber o que muita gente ignora. Como ele chamaria você nessa aventura?',
    'Como ele chamaria você?',
    'Como continuaria «Era uma vez um pequeno robô.»?',
    'Use «Era uma vez um pequeno robô.» como começo. O que acontece depois?',
    'Gostei da ideia. Vamos pensar em outra. Como isso funcionaria?',
    'Entendi. Como assim?',
)
CHAVES_HISTORICAS = {'explicacoes_historicas_por_ato', 'explicacao_ocorrencia',
                     'evidencia_fala_historica', 'revisao_alegacao'}


@pytest.mark.parametrize('texto', FICCAO)
@pytest.mark.parametrize('com_receipt', [False, True])
def test_contexto_narrativo_ou_receipt_anterior_nao_criam_obrigacao(texto, com_receipt):
    fala = 'Era uma vez um pequeno robô.'
    resultados = (ResultadoAcao(intent='APP_OPEN', alvo='Calculadora', status='confirmado',
        executou=True, confirmado=True, origem='executor', id_solicitacao='antiga'),) if com_receipt else ()
    registro = registrar_fala_observada(None, ocorrencia_id='publicacao', turno_id='anterior',
        fala=fala, resultados=resultados, canal='texto_publicado')
    mente = {'registro_semantico':registro, 'ultima_resposta':fala}
    antes = deepcopy(mente)
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente=mente)
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert not CHAVES_HISTORICAS.intersection(contrato), 'contexto foi promovido a finalidade histórica'
    assert mente == antes and turno['autoriza_execucao'] is False
    assert not plano['comandos'] and not plano['requer_execucao']


@pytest.mark.parametrize('texto', [
    pytest.param('Quando disse "Registrei o resultado do pedido.", por que aconteceu?',
        marks=pytest.mark.xfail(strict=True, reason='RED anterior ao candidato: segmentação separa atribuição e pergunta causal')),
    'Por que você disse isso?', 'Não entendi por que você disse isso?',
    'Qual o motivo de você dizer "Registrei o resultado do pedido."?',
])
def test_consulta_causal_a_fala_real_mantem_fonte_e_limite(texto):
    original = plano_historico()
    registro = {'falas_observadas':original['contrato_fala']['evidencia_fala_historica']['falas']}
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={'registro_semantico':registro})
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno,
        plano=plano, mente={'registro_semantico':registro})
    assert CHAVES_HISTORICAS.intersection(plano['contrato_fala'])
    falsa = 'Tudo aconteceu porque o servidor caiu e a conexão falhou.'
    r = verificar_fala_turno(falsa, plano=plano)
    assert not (r['aceita'] and r['fala']==falsa), 'a causa inventada atravessou o verificador'


@pytest.mark.parametrize('texto', ['Por que você apagou esse arquivo? Por que você desligou essa tomada?',
    'Gostei da história. Por que você apagou esse arquivo?',
    'Invente uma história. Por que você desligou essa tomada?'])
def test_pedido_historico_em_composto_nao_e_dispensado_por_conteudo_criativo(texto):
    _, plano = consulta(texto, recuperar=owner_dois_dominios)
    assert 'explicacoes_historicas_por_ato' in plano['contrato_fala']
    falsa = 'Apaguei o arquivo e desliguei a tomada porque achei melhor.'
    r = verificar_fala_turno(falsa, plano=plano)
    assert not (r['aceita'] and r['fala']==falsa)


def test_ocorrencia_fornecida_mas_estrangeira_continua_falhando_fechado():
    from mente_laylay.memoria_mental.decisao_observada import ExplicacaoOcorrencia
    texto = 'Gostei da ideia. Como isso funcionaria?'
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    estrangeira = ExplicacaoOcorrencia('outro','outra pergunta',(),'ausente')
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        explicacao_ocorrencia=estrangeira)
    assert 'explicacoes_historicas_por_ato' in contrato
    assert contrato['explicacoes_historicas_por_ato'] is None


def test_segmentacao_adulterada_em_consulta_historica_nao_cai_em_prosa_livre():
    texto = 'Por que você apagou esse arquivo? Por que você desligou essa tomada?'
    turno, plano = consulta(texto)
    # Adulterar a fonte estrutural, não apenas o texto de apresentação.
    turno['segmentos'][0]['texto_estrutural'] = 'outra coisa'
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        recuperar_explicacao_ocorrencia=owner_dois_dominios)
    assert 'explicacoes_historicas_por_ato' in contrato
    assert contrato['explicacoes_historicas_por_ato'] is None


@pytest.mark.parametrize('texto, esperado', [
    ('Quando disse "olá", por que fez isso?', 'fala'),
    ('Quando respondeu "olá", qual foi o motivo?', 'fala'),
    ('Qual a razão de você responder "olá"?', 'fala'),
    ('Qual o motivo de você dizer "olá"?', 'fala'),
    ('Por que você abriu esse aplicativo?', 'ocorrencia'),
    ('Por que ele disse "olá"?', 'outro_agente'),
    ('Como continuaria «Por que você disse isso?»?', ''),
    ('Use «Por que você disse isso?» como começo. O que acontece depois?', ''),
    ('Quando disse «olá», continue a história.', ''),
    ('Se você dissesse «olá», por que faria isso?', ''),
])
def test_finalidade_vem_da_consulta_e_nao_do_conteudo_citado(texto, esperado):
    from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_historica
    assert referencia_explicacao_historica(texto) == esperado
