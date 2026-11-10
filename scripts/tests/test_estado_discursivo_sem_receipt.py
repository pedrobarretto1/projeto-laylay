"""Um estado de assunto não declara o efeito de um executor."""
import pytest

from mente_laylay.cognicao.guardiao_alegacoes import detectar_resultados_operacionais_sem_evidencia
from mente_laylay.cognicao.plano_turno import verificar_fala_turno


@pytest.mark.parametrize('sujeito', ['o assunto', 'o tema', 'a conversa', 'o debate', 'a discussão'])
@pytest.mark.parametrize('predicado', ['continua aberto', 'está fechado'])
def test_estado_de_objeto_discursivo_nao_confirma_estado_de_recurso(sujeito, predicado):
    if sujeito.startswith('a '):
        predicado = predicado.replace('aberto', 'aberta').replace('fechado', 'fechada')
    fala = f'Entendi, {sujeito} {predicado}.'
    assert not detectar_resultados_operacionais_sem_evidencia(fala, plano={
        'texto_usuario': f'{sujeito} {predicado}.',
    })


@pytest.mark.parametrize('fala', [
    'O arquivo assunto.txt continua aberto.',
    'O arquivo chamado "assunto" continua aberto.',
    'O assunto do Opera continua aberto.',
    'Consegui abrir o arquivo.', 'O Opera continua aberto.',
    'O assunto continua aberto e o arquivo está fechado.',
    'O tema do dispositivo está fechado.',
    'O debate continua aberto, mas o Opera está fechado.',
    'O assunto continua aberto e o Opera também.',
    'O tema está fechado e o arquivo também.',
    'O assunto continua aberto, assim como o arquivo.',
])
def test_nome_de_recurso_e_outro_estado_nao_herdam_dispensa_discursiva(fala):
    assert detectar_resultados_operacionais_sem_evidencia(fala, plano={'texto_usuario': 'Podemos conversar?'})


def test_estado_discursivo_nao_dispensa_efeito_em_outra_oracao():
    fala = 'O assunto continua aberto. Consegui apagar o arquivo.'
    r = verificar_fala_turno(fala, plano={'texto_usuario': 'O assunto continua aberto.', 'comandos': []})
    assert 'Consegui apagar' not in r['fala']
    assert r['problemas']


def test_composicao_mantem_estado_discursivo_sem_exigir_executor():
    from scripts.tests.test_papo_casual_composicao import coletar, proposta
    texto, fala = 'O assunto continua aberto.', 'Entendi, o assunto continua aberto.'
    d = coletar({'entrada': texto, 'historico': []}, [proposta(fala)])
    assert d['resposta']['texto'] == fala, d
    assert d['http'] == 1 and not d['resposta']['degradada']
