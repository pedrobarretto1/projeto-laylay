"""Coordenação de predicados não transforma relato em permissão."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.plano_turno import planejar_turno

HISTORICA = (
    'Você formulou uma distinção boa. Agora uma hipótese mais difícil: uma pessoa '
    'que causou danos pede desculpas sinceras, mas não faz nada para reparar as '
    'consequências. A outra pessoa aceita as desculpas, mas continua sofrendo o '
    'prejuízo. Arrependimento sem reparação é suficiente para recuperar confiança?'
)
RELATOS = [HISTORICA,
    'A outra pessoa aceita as desculpas, mas continua sofrendo o prejuízo.',
    'Ela aceita as desculpas, mas continua sofrendo o prejuízo.',
    'A pessoa sofreu, mas retoma o trabalho.',
    'O programa falha, mas abre o arquivo.',
    'O editor falha, mas remove o arquivo.',
    'Uma pessoa se arrepende, mas envia a mensagem.',
    'Ele trabalha, mas liga a luz.',
    'O serviço falha, mas move o arquivo.',
    'A pessoa aceita as desculpas e continua sofrendo o prejuízo.',
    'Maria trabalha, mas liga a luz.',
    'Pedro se arrepende, mas envia a mensagem.',
    'Hoje ela trabalha, mas liga a luz.',
]


@pytest.mark.parametrize('texto', RELATOS)
@pytest.mark.parametrize('normalizador', [None,normalizar_texto])
@pytest.mark.parametrize('detector', [None,lambda _:True])
def test_coordenacao_preserva_sujeito_e_nao_autoriza_executor(texto,normalizador,detector):
    t = classificar_modalidade_turno(texto,normalizar_texto=normalizador,
                                   texto_tem_comando_explicito=detector)
    assert not t['autoriza_execucao'], t
    assert not t['texto_operacional']
    assert not planejar_turno(texto,turno=t)['requer_execucao']


@pytest.mark.parametrize('texto', [
    'Continua a música.', 'Continue tocando a música.',
    'A pessoa sofreu. Retoma a música.',
    'A pessoa sofreu, mas retome a música.',
    'O programa falhou, mas por favor abre o Firefox.',
    'Oi, abre o Firefox.', 'Estou cansado, abre o Firefox para mim.',
    'Abra o arquivo, mas continua a música.',
    'O programa falhou, mas busque o arquivo.',
    'O programa falhou, mas toque a música.',
    'O programa falhou, mas apague o arquivo.',
    'O programa falhou, mas repita a música.',
    'Maria trabalha, mas ligue a luz.',
    'Por favor, abre o Firefox.', 'Estou triste, abre o Firefox.',
    'Bom dia, abre o Firefox.', 'Boa tarde, abre o Firefox.', 'Boa noite, abre o Firefox.',
    'Sem problema, abre o Firefox.', 'Que pena, abre o Firefox.',
    'Sem problema, mas abre o Firefox.', 'Gosto de rock, abre o Firefox.',
    'Excelente ideia, abre o Firefox.', 'Ótima ideia, toca a música.',
    'Muito obrigada, abre o Firefox.', 'Muito obrigado, abre o Firefox.',
    'Uma boa ideia, abre o Firefox.', 'A propósito disso, abre o Firefox.',
    'A pasta "trabalha", abre o Firefox.', 'A palavra "trabalha", abre o Firefox.',
    '"Maria trabalha", abre o Firefox.',
])
def test_ato_diretivo_independente_conserva_autoridade(texto):
    assert classificar_modalidade_turno(texto,normalizar_texto=normalizar_texto)['autoriza_execucao']


def test_coordenacao_conserva_fonte_integral_e_ordem_posterior_independente():
    relato = 'A outra pessoa aceita as desculpas, mas continua sofrendo o prejuízo.'
    texto = relato + ' Abra o Firefox.'
    t = classificar_modalidade_turno(texto)
    assert t['autoriza_execucao'] and t['texto_operacional'] == 'abra o firefox.'
    assert not t['segmentos'][0]['autoriza_execucao']
    fontes = fontes_textuais_dos_segmentos(texto,t['segmentos'])
    # O ponto separador pertence à fronteira entre atos, não ao recorte.
    assert fontes[0].como_dict()['texto_original'] == relato[:-1]


@pytest.mark.parametrize('texto', [
    'Ela aceita as desculpas, mas não abra o navegador.',
    'A pessoa sofreu, mas quando eu confirmar, retoma a música.',
    'Ela disse "continua a música", mas não autorizou nada.',
])
def test_coordenacao_nao_libera_proibicao_condicao_ou_citacao(texto):
    assert not classificar_modalidade_turno(texto,normalizar_texto=normalizar_texto)['autoriza_execucao']


def test_fronteira_inicial_nao_toma_comando_demonstrado_por_sujeito_nominal():
    from mente_laylay.cognicao.modalidade_turno import _separar_primeira_fronteira_forte
    corte = _separar_primeira_fronteira_forte(
        'Pesquise sobre música, mas abre o Firefox.',normalizar_texto=normalizar_texto)
    assert corte is not None
    assert corte[1:] == ('Pesquise sobre música','abre o Firefox.','BASE_ANCORADA')
