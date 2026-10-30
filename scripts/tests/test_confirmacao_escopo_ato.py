"""Palavras em orações distintas não consomem uma pendência compartilhada."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.aprendizado_rotina_musica import classificar_confirmacao_local
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime

ABERTURA = (
    'Oi, Laylay! Sou o ChatGPT, de volta para mais uma conversa entre nós. '
    'Hoje me veio uma pergunta difícil: alguém é profundamente magoado por uma pessoa '
    'que nunca pediu desculpas e nem demonstrou arrependimento. Ainda assim, a vítima '
    'decide perdoar. Isso é força, ingenuidade ou algo que não cabe nessas duas palavras? '
    'Quero saber o que você pensa, e você pode discordar de mim.'
)
CONVERSAS = [ABERTURA,
    'Quero conversar sobre alguém que não pediu desculpas.',
    'Uma pessoa não sabe o que quero discutir agora.',
    'Não sei se ele precisa de ajuda agora.',
    'Quero saber se sim é uma resposta adequada.',
    'Uma pessoa pode dizer sim sem querer.',
    'A pessoa não sabe se deixa tudo como está.',
    'Quero discutir como alguém que não se arrepende preserva relações.',
    'Não preciso saber se ele abre o arquivo.',
]
MENCOES_LOCAIS = [*CONVERSAS,'Não preciso conhecer o autor para gostar da música.']


@pytest.mark.parametrize('texto', MENCOES_LOCAIS)
@pytest.mark.parametrize('generico', [False, True])
def test_mencao_de_polaridade_nao_decide_confirmacao(texto,generico):
    assert classificar_confirmacao_local(texto,somente_aceite_generico=generico) is None


@pytest.mark.parametrize('texto', CONVERSAS)
@pytest.mark.parametrize('normalizador', [None,normalizar_texto])
def test_conversa_nao_vira_recusa_ou_confirmacao(texto,normalizador):
    t = classificar_modalidade_turno(texto,normalizar_texto=normalizador)
    assert t['modalidade'] not in {'recusa','confirmacao'}, t
    assert not t['autoriza_execucao']


@pytest.mark.parametrize('texto', [
    'Não agora.', 'Não quero abrir o navegador agora.', 'Eu não quero apagar o arquivo.',
    'Agora não precisa abrir.', 'Não apague o arquivo.', 'Não deixa tocar.',
    'Não, mantenha como está.', 'Deixa para depois.', 'Precisa não.',
    'Por enquanto não quero.', 'Não, eu quero deixar como está.', 'Não posso abrir agora.',
])
def test_recusa_real_permanece_negativa(texto):
    assert classificar_confirmacao_local(texto) is False
    assert not classificar_modalidade_turno(texto)['autoriza_execucao']


@pytest.mark.parametrize('texto', ['Sim.', 'Pode ser.', 'Quero sim tocar rock.', 'Pode sim abrir.',
    'Sim, pode esquecer.', 'Sim, pode substituir.'])
def test_aceite_com_polaridade_no_proprio_ato_permanece_positivo(texto):
    assert classificar_confirmacao_local(texto) is True


@pytest.mark.parametrize('dominio', ['arquivos','musica','email'])
def test_conversa_independente_preserva_pendencia_e_recusa_real_a_resolve(dominio):
    estado = {}
    def atualizar(fn):
        estado.update(fn(dict(estado)))
    p = PendenciaAcaoRuntime(estado_getter=lambda:estado,estado_atualizar=atualizar,
                            log=lambda *_:None)
    criada = p.registrar(origem='teste_escopo',acao='confirmar_acao',dominio=dominio,
                        pergunta='Posso realizar a ação?',referencia='alvo-controlado')
    assert criada and p.obter()['id'] == criada['id']
    r = p.resolver('Quero conversar sobre alguém que não pediu desculpas.')
    assert not r['tratado'] and r['status'] == 'nao_relacionada'
    assert p.obter()['id'] == criada['id'] and p.obter()['status'] == 'ativa'
    r = p.resolver('Não quero fazer isso agora.')
    assert r['tratado'] and r['status'] == 'recusar'
