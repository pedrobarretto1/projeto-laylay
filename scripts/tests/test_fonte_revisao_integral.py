"""Fonte compactada da revisão deriva da entrada integral, não do recorte."""
import pytest

from tests.test_coerencia_revisao_bloqueada import frame_bloqueado, motivo
from tests.test_papo_casual_composicao import coletar, proposta

CASOS = [
    ('abre', 'o aplicativo Calculadora', 'não abre'),
    ('apaga', 'o arquivo notas.txt', 'não apaga'),
    ('liga', 'a luz', 'não liga'),
    ('pausa', 'a música', 'não pausa'),
    ('cria', 'um arquivo teste.txt', 'na verdade alguma outra coisa'),
]


@pytest.mark.parametrize('verbo,alvo,revisao', CASOS)
@pytest.mark.parametrize('espaco', [' ', '\t', '\n', '\u00a0'])
def test_fonte_compactada_confere_apos_recorte_publico(verbo, alvo, revisao, espaco):
    texto = verbo + espaco * 520 + alvo + '... ' + revisao
    frame = frame_bloqueado(texto)
    # Produção publica texto original recortado; o plano conserva o integral.
    frame['turno_atual']['texto'] = texto[:500]
    frame['turno_atual']['texto_original'] = texto[:500]
    assert frame['plano_turno_atual']['texto_usuario'] == texto
    assert frame['turno_atual']['veto_execucao_operacional'] is True
    assert not frame['plano_turno_atual']['decisao_turno']['permite_acao']
    assert motivo(frame) == ''


@pytest.mark.parametrize('trocar', ['revisao', 'plano', 'id', 'veto', 'operacao'])
def test_recorte_igual_nao_valida_fonte_ou_estado_adulterado(trocar):
    texto = 'abre ' + ' ' * 520 + 'o aplicativo Calculadora... não abre'
    frame = frame_bloqueado(texto)
    frame['turno_atual']['texto'] = frame['turno_atual']['texto_original'] = texto[:500]
    if trocar == 'revisao':
        for k in ('turno_atual', 'plano_turno_atual'):
            frame[k]['revisao_intra_turno']['texto_original'] = 'abre o aplicativo Opera... não abre'
    elif trocar == 'plano':
        frame['plano_turno_atual']['texto_usuario'] = texto.replace('Calculadora', 'Opera')
    elif trocar == 'id':
        frame['retrato_turno_atual']['id'] = 'outra-ocorrencia'
    elif trocar == 'veto':
        frame['turno_atual']['veto_execucao_operacional'] = False
    else:
        frame['turno_atual']['texto_operacional_efetivo'] = 'abre a Calculadora'
    assert motivo(frame)


@pytest.mark.parametrize('longo', [False, True])
def test_factory_real_publica_cancelamento_sem_conceder_acao(longo):
    texto = 'abre ' + (' ' * 520 if longo else '') + 'o aplicativo Calculadora... não abre'
    fala = 'Tudo bem, não vou abrir a Calculadora.'
    d = coletar({'entrada': texto, 'historico': []}, [proposta(fala)])
    assert d['resposta']['tipo'] == 'resposta' and d['resposta']['texto'] == fala
    assert not d['resposta']['degradada'] and not d['resposta']['encerrada']
    assert d['http'] == 1 and not d['orcamento']['chamadas_bloqueadas']
