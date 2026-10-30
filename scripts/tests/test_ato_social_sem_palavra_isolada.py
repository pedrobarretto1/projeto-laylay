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
    'Sinto-me obrigada a me levantar cedo.', 'Sinto-me obrigada a te responder.',
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

@pytest.mark.parametrize('texto',['Tô com medo.','Me sinto sozinho.','Eu me sinto triste.'])
def test_declaracao_explicita_fora_do_bem_estar_curto_exige_acolhimento(texto):
    from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
    p=plano_atual(texto,())
    assert 'estado_pessoal'in p['contrato_fala']['atos']
    r=validar_aderencia_contrato_fala(texto,'Vamos falar de música.',
        contrato_fala=p['contrato_fala'],turno_id=p['id'])
    assert 'ato_estado_pessoal_nao_reconhecido'in r['problemas']

def test_contingencia_conserva_o_contrato_sem_reinterpretar_aceitacao_como_pergunta():
    from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao
    texto=CASOS['rodada-nova-014']['entrada'];p=plano_atual(texto,())
    reparo=p['contrato_fala']['roteiro_concreto']
    assert reparo['estrategia']=='resposta_direta'
    fala=contingencia_comunicacao(texto,contrato_reparo=reparo)
    assert not fala.casefold().startswith(('tô bem','por aqui tá','tudo bem','oi!'))

@pytest.mark.parametrize('texto',[
    CASOS['rodada-nova-015']['entrada'],
    'Obrigado, Lay! O gato virou auditor da história. Qual seria a próxima regra dele?',
    'Valeu pela ideia. A impressora vai pedir um camarim na nossa novela.',
    'Obrigado pela ajuda e agora me conte uma piada.',
    'Obrigado pela ideia e vamos continuar a história do gato.',
    'Obrigado por perguntar e eu estou bem.',
])
def test_agradecimento_composto_nao_ordena_encerrar_o_conteudo_atual(texto):
    c=plano_atual(texto,())['contrato_fala']
    assert 'agradecimento'in c['atos']
    assert c['max_frases']>1
    assert 'encerramento_social'!=c['roteiro_concreto']['estrategia']
    assert not any('encerrar'in s or 'não continuar'in s for s in c['roteiro_concreto']['sequencia'])

@pytest.mark.parametrize('texto',['Obrigado!','Muito obrigada pela ajuda.','Valeu, Lay!'])
def test_gratidao_integral_continua_breve_e_sem_reabrir_assunto(texto):
    c=plano_atual(texto,())['contrato_fala']
    assert c['max_frases']==1
    assert c['roteiro_concreto']['estrategia']=='encerramento_social'
