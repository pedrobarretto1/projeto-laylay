"""Adjunto e pergunta matriz conservam uma única fonte textual por ato."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos
from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_historica
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada


@pytest.mark.parametrize('atribuicao', ['disse', 'você respondeu', 'tu explicou'])
@pytest.mark.parametrize('matriz', ['por que aconteceu?', 'qual foi o motivo?', 'o que aconteceu?'])
def test_adjunto_temporal_e_matriz_tem_uma_fonte_integral(atribuicao, matriz):
    texto = f'Quando {atribuicao} "A janela estava fechada.", {matriz}'
    turno = classificar_modalidade_turno(texto)
    assert referencia_explicacao_historica(texto) == 'fala'
    assert len(turno['segmentos']) == 1
    fontes = fontes_textuais_dos_segmentos(texto, turno['segmentos'])
    assert len(fontes) == 1 and fontes[0].como_dict()['texto_original'] == texto
    assert not turno['autoriza_execucao']


@pytest.mark.parametrize('texto', [
    'Quando você abriu esse arquivo, por que fez isso?',
    'Quando você ligou essa tomada, qual foi o motivo?',
    'Quando você tocou essa playlist, por que aconteceu?',
])
def test_dependencia_temporal_de_acao_nao_concede_execucao(texto):
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 1 and not turno['autoriza_execucao']
    plano = planejar_turno(texto, turno=turno, mente={})
    assert not plano['comandos'] and not plano['requer_execucao']


@pytest.mark.parametrize('texto', [
    'Quando disse "olá"? Por que você apagou esse arquivo?',
    'Quando disse "olá"; por que você apagou esse arquivo?',
    'Quando disse "olá", por que aconteceu? Por que você apagou esse arquivo?',
    'Quando disse "olá", por que aconteceu? Abre a Calculadora.',
])
def test_fronteira_forte_mantem_os_atos_independentes(texto):
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 2


@pytest.mark.parametrize('texto', [
    'Como continuaria «Quando disse olá, por que aconteceu?»?',
    'Se você dissesse "olá", por que faria isso?',
    'Quando disse "olá", continue a história.',
])
def test_ficcao_e_futuro_nao_ganham_fonte_historica(texto):
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    c = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    assert not {'evidencia_fala_historica','explicacoes_historicas_por_ato','explicacao_ocorrencia'}.intersection(c)


@pytest.mark.parametrize('fala', ['A janela estava fechada.', 'Registrei o resultado do pedido.'])
def test_binding_da_fala_publicada_nao_permite_causa_proposta(fala):
    texto = f'Quando disse "{fala}", por que aconteceu?'
    registro = registrar_fala_observada(None, ocorrencia_id='publicacao', turno_id='anterior',
        fala=fala, resultados=(), canal='texto_publicado')
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={'registro_semantico': registro})
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        mente={'registro_semantico': registro})
    assert 'evidencia_fala_historica' in plano['contrato_fala']
    assert plano['contrato_fala']['evidencia_fala_historica']['falas'][0]['fala'] == fala
    falsa = 'Tudo aconteceu porque o servidor caiu e a conexão falhou.'
    r = verificar_fala_turno(falsa, plano=plano)
    assert not (r['aceita'] and r['fala'] == falsa)
