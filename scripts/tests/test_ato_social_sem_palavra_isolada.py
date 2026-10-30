"""Função afetiva não declara estado nem transforma dever em gratidão."""
import json
from pathlib import Path
import pytest
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.personalidade.leitura_social_conversa import tipo_reconhecimento_afetivo
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social
from scripts.tests.test_continuidade_resposta_recente import plano_atual

CASOS={c['id']:c for c in json.loads((Path(__file__).parent/'fixtures/retoma_improviso.json').read_text(encoding='utf8'))}

@pytest.mark.parametrize('texto',[
    CASOS['rodada-nova-006']['entrada'], 'Sou obrigado a estudar.',
    'Fui obrigada a sair.', 'Estou sendo obrigado a reiniciar o sistema.',
    'Não sou obrigado a responder.', 'Ele foi obrigado a abrir a porta.',
])
def test_participio_de_obrigacao_nao_e_agradecimento(texto):
    assert analisar_funcao_comunicativa(texto)['funcao']!='agradecimento'
    assert tipo_reconhecimento_afetivo(texto)!='agradecimento'

@pytest.mark.parametrize('texto',['Obrigado!', 'Muito obrigada pela ajuda.',
    'Obrigado a todos.', 'Sou obrigado a sair. Mas obrigado pela ajuda!', 'Valeu, Lay!'])
def test_gratidao_enunciada_permanece_gratidao(texto):
    assert analisar_funcao_comunicativa(texto)['funcao']=='agradecimento'
    assert tipo_reconhecimento_afetivo(texto)=='agradecimento'

@pytest.mark.parametrize('texto',[
    CASOS['rodada-nova-013']['entrada'], 'Você errou o cálculo. Pode corrigir?',
    'Já falei de gatos demais. Que assunto você escolheria?',
])
def test_funcao_afetiva_ou_correcao_nao_declara_estado_pessoal(texto):
    assert 'estado_pessoal'not in plano_atual(texto,())['contrato_fala']['atos']

@pytest.mark.parametrize('texto',[
    CASOS['rodada-nova-014']['entrada'],
    'Tudo bem, Lay. Eu gostei da piada.',
    'Tudo bem, não precisa. Eu procuro depois.',
])
def test_aceitacao_dirigida_a_outro_nao_informa_o_estado_do_usuario(texto):
    assert analisar_ato_social(texto).get('tipo')not in {'WELLBEING','WELLBEING_REPLY'}
    assert 'estado_pessoal'not in plano_atual(texto,())['contrato_fala']['atos']

@pytest.mark.parametrize('texto',['Tô bem, Lay. Obrigado por perguntar.',
    'Estou triste. Podemos conversar?', 'Eu estou muito feliz.',
    'Tudo bem comigo. Gostei da conversa.'])
def test_estado_explicitamente_atribuido_ao_usuario_continua_no_composto(texto):
    assert 'estado_pessoal'in plano_atual(texto,())['contrato_fala']['atos']
