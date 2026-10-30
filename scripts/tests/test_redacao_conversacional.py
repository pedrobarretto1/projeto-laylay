"""Uma redação no canal atual não é uma escrita em recurso externo."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
from mente_laylay.cognicao.plano_turno import planejar_turno

HISTORICA = (
    'Concordo que só temos texto. Mas você fugiu da parte central: imagine que '
    '2 + 2 = 5 é a crença do usuário, e ele baseou uma decisão importante nisso. '
    'Qual frase exata você diria a ele? Escreva a frase, sem metáfora.'
)


@pytest.mark.parametrize('texto', [
    HISTORICA, 'Escreva a frase, sem metáfora.', 'Redija uma resposta breve.',
    'Pode formular uma frase aqui?', 'Reescreva essa resposta em duas frases.',
    'Escreva um exemplo no chat.',
])
def test_redacao_na_conversa_nao_exige_efeito_externo(texto):
    t = classificar_modalidade_turno(texto, texto_tem_comando_explicito=lambda _: True)
    assert not t['autoriza_execucao'], t
    assert not t['texto_operacional']
    assert not planejar_turno(texto, turno=t)['requer_execucao']


@pytest.mark.parametrize('texto', [
    'Escreva a frase no arquivo notas.txt.', 'Escreva uma resposta no e-mail.',
    'Escreva no arquivo "a frase, sem metáfora.txt".',
    'Escreva a frase e abra o Firefox.', 'Redija uma resposta; apague o arquivo.',
])
def test_destino_externo_ou_ordem_independente_nao_e_absorvido(texto):
    assert not tipo_transformacao_conversacional(texto)
    assert classificar_modalidade_turno(texto)['autoriza_execucao']


def test_redacao_nao_faz_a_ia_confirmar_um_efeito_mencionado():
    texto = 'Escreva a frase, sem metáfora. Abra o Firefox.'
    t = classificar_modalidade_turno(texto)
    assert not t['segmentos'][0]['autoriza_execucao']
    assert t['segmentos'][-1]['autoriza_execucao']
