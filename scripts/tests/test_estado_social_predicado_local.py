"""Estado social não usa adjetivo ou locução de outra oração como predicado."""
import pytest
from tests.test_escopo_permissivo_contraste import CASOS
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social
from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao
from mente_laylay.personalidade.contingencia_natural import fala_falha_geracao
from scripts.tests.test_retomada_criacao import preparar


ENCERRAMENTO_COM_PERGUNTA = (
    'Tudo bem, Laylay, não precisa forçar uma resposta. Que tal terminar com algo leve? '
    'Faça uma pergunta divertida para mim, ChatGPT, que você gostaria de explorar na nossa próxima conversa.'
)


@pytest.mark.parametrize('texto', [
    ENCERRAMENTO_COM_PERGUNTA,
    'Tudo bem, você não precisa justificar. Qual título você daria para o conto? Escreva em uma frase.',
    'Tudo bem com você deixar isso pra depois. Qual nome fica melhor? Escolha um.',
])
def test_tranquilizacao_nao_herda_interrogacao_de_outro_enunciado(texto):
    assert analisar_ato_social(texto).get('tipo') != 'WELLBEING'
    assert 'bem_estar' not in preparar(texto)['contrato_fala']['atos']
    motivo = 'orcamento_prazo_esgotado'
    assert contingencia_comunicacao(texto, motivo_falha=motivo) == fala_falha_geracao(motivo)


def test_pergunta_de_bem_estar_explicita_sobrevive_ao_pedido_seguinte():
    texto = 'Tudo bem com você? Depois me conte o título.'
    assert 'bem_estar' in preparar(texto)['contrato_fala']['atos']


def test_composicao_responde_ao_pedido_apos_a_tranquilizacao(monkeypatch):
    from tests import test_autoria_operacao_composicao as autoria
    from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
    from tests.test_papo_casual_composicao import proposta

    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    pergunta = 'Se você pudesse inventar um feriado, o que a gente comemoraria?'
    resultado = autoria.coletar_autoria({'entrada': ENCERRAMENTO_COM_PERGUNTA, 'historico': []}, [proposta(pergunta)])
    assert 'bem_estar' not in resultado['plano']['contrato']['atos']
    assert not resultado['execucao_exigida'] and not resultado['operacional']
    assert resultado['falas'] == [pergunta] and resultado['http'] == len(resultado['publicacoes']) == 1
    assert not resultado['resposta']['degradada'] and not resultado['resposta']['falhas_geracao']

@pytest.mark.parametrize('texto',[
    next(c['entrada']for c in CASOS if c['id']=='papo-008'),
    'Você tá falando de robôs? Pensando bem, isso é engraçado.',
    'Você está lendo um livro. Ele termina bem?',
    'Você está mencionando o filme triste?',
    'Como você vai nomear o personagem?',
    'Como você está organizando as ideias para o conto?',
])
def test_adjetivo_de_outro_predicado_nao_se_torna_bem_estar(texto):
    assert analisar_ato_social(texto).get('tipo') not in {'WELLBEING','WELLBEING_REPLY'}

@pytest.mark.parametrize('texto',[
    'Como você está?', 'Você está bem?', 'Você tá muito bem?',
    'Tudo bem com você?', 'Como tu tá?',
    'Como que você tá?', 'Como é que você está?',
    'Como vai você?', 'Como você está se sentindo hoje?',
])
def test_pergunta_social_com_predicado_vinculado_permanece(texto):
    assert analisar_ato_social(texto).get('tipo')=='WELLBEING'


@pytest.mark.parametrize('texto',['Estou me sentindo triste.','Eu tô me sentindo muito feliz.'])
def test_perifrase_reflexiva_conserva_o_estado_da_pessoa(texto):
    assert analisar_ato_social(texto).get('tipo')=='WELLBEING_REPLY'
