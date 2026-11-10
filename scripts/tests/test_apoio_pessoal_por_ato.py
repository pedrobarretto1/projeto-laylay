"""Uma pergunta vizinha não apaga a declaração literal do interlocutor."""
import pytest

from mente_laylay.cognicao.afirmacoes_interlocutor import conferir_afirmacoes_interlocutor
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.referencias_linguagem import PerspectivaEnunciador


def plano(texto):
    turno = classificar_modalidade_turno(texto)
    resultado = planejar_turno(texto, turno=turno)
    resultado['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=resultado)
    assert type(resultado['contrato_fala'].get('perspectiva_enunciador')) is PerspectivaEnunciador
    return resultado


@pytest.mark.parametrize('texto,fala', [
    ('Estou cansado, pode me recomendar um filme?', 'Entendo, você está cansado.'),
    ('Estou cansado. Pode sugerir uma conversa?', 'Você está cansado.'),
    ('Eu uso Linux. Que jogo você sugeriria?', 'Você usa Linux.'),
    ('Eu moro em Salvador, qual assunto quer discutir?', 'Você mora em Salvador.'),
    ('Eu trabalho de noite; podemos conversar?', 'Você trabalha de noite.'),
])
def test_declaracao_atual_por_ato_sustenta_somente_a_atribuicao_literal(texto, fala):
    assert conferir_afirmacoes_interlocutor(fala, plano=plano(texto)) is None


@pytest.mark.parametrize('fala', [
    'Quando converso com você e com o Pedro, quero mostrar meu humor.',
    'Pensei em um assunto para você e para sua equipe.',
])
def test_coordenacao_de_complementos_nao_e_predicado_pessoal(fala):
    assert conferir_afirmacoes_interlocutor(fala, plano=plano('Como você quer conversar?')) is None


@pytest.mark.parametrize('fala', [
    'Quando converso com você e com o Pedro, você está cansado.',
    'Para você e para sua equipe, você é de Recife.',
    'Você é de Recife.',
    'Voce e de Recife.',
])
def test_coordenacao_nao_dispensa_predicado_pessoal_independente(fala):
    resultado = conferir_afirmacoes_interlocutor(fala, plano=plano('Como você quer conversar?'))
    assert resultado and resultado['problemas_bloqueantes']


@pytest.mark.parametrize('texto', [
    'Estou cansado? Pode sugerir uma conversa?',
    'Se estou cansado, você não sabe. Pode me indicar um filme?',
    'Ela está cansada, pode me indicar um filme?',
    'Não estou cansado, pode me indicar um filme?',
    'Eu disse "estou cansado" como exemplo. Qual filme você sugere?',
    'Talvez eu esteja cansado, qual assunto você quer?',
    'Estou cansado, não é?', 'Estou cansado, será?',
    'Estou cansado, certo?', 'Estou cansado, você acha?',
    'Estou cansado, confere?',
    'Estou cansado, ou não? Qual filme você sugere?',
    'Estou cansado, não estou? Qual filme você sugere?',
    'Estou cansado, será mesmo? Qual filme você sugere?',
    'Estou cansado, se é que estou. Qual filme você sugere?',
    'Estou cansado, se é que estou, pode me recomendar um filme?',
    'Estou cansado, embora não pareça, pode me recomendar um filme?',
])
def test_pergunta_hipotese_citacao_e_terceiro_nao_fornecem_declaracao(texto):
    resultado = conferir_afirmacoes_interlocutor('Você está cansado.', plano=plano(texto))
    assert resultado and 'afirmacao_interlocutor_sem_apoio' in resultado['problemas']


@pytest.mark.parametrize('fala', [
    'Você está cansado e triste.', 'Você está na cama.',
    'Você está cansado por causa do trabalho.',
])
def test_declaracao_nao_sustenta_qualificacao_causa_ou_cena_nova(fala):
    resultado = conferir_afirmacoes_interlocutor(fala, plano=plano('Estou cansado, que assunto leve podemos conversar?'))
    assert resultado and resultado['problemas_bloqueantes']


def test_proposta_de_ato_no_plano_nao_substitui_a_mensagem_fonte():
    p = plano('Estou cansado? Qual assunto você escolheria?')
    p['atos'] = [{'tipo': 'conversa', 'texto': 'Estou cansado.'}]
    resultado = conferir_afirmacoes_interlocutor('Você está cansado.', plano=p)
    assert resultado and resultado['problemas_bloqueantes']


def test_relato_historico_misto_preserva_autoria_sem_emprestar_a_pergunta():
    p = plano('Qual assunto você escolheria?')
    p['relatos_usuario'] = [{'autor': 'usuario', 'origem': 'historico_conversa',
        'status': 'relatado_pelo_usuario', 'texto': 'Eu uso Linux. Podemos falar de jogos?'}]
    assert conferir_afirmacoes_interlocutor('Você usa Linux.', plano=p) is None
    assert conferir_afirmacoes_interlocutor('Você usa Linux e trabalha de noite.', plano=p)


def test_composicao_atribuicao_atual_e_pergunta_publicam_uma_resposta():
    from scripts.tests.test_papo_casual_composicao import coletar, proposta
    entrada = 'Estou cansado, que assunto leve podemos conversar?'
    fala = 'Você está cansado. Podemos inventar uma história curta, se quiser.'
    resultado = coletar({'entrada': entrada, 'historico': []}, [proposta(fala)])
    assert resultado['resposta']['texto'] == fala, resultado
    assert resultado['http'] == 1 and not resultado['resposta']['degradada']


def test_composicao_recomendacao_preserva_estado_sem_inventar_candidato():
    from scripts.tests.test_papo_casual_composicao import coletar, proposta
    resultado = coletar({'entrada': 'Estou cansado, pode me recomendar um filme?',
                        'historico': []}, [proposta('Recomendo o Filme Inventado.')])
    assert resultado['resposta']['texto'].startswith('Entendo, você está cansado.'), resultado
    assert 'Filme Inventado' not in resultado['resposta']['texto']
    assert 'opção verificada' in resultado['resposta']['texto']
    assert resultado['http'] == 1 and not resultado['resposta']['degradada']
