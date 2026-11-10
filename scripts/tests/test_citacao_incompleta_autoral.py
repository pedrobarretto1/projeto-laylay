"""Uma aspa órfã não pode proteger uma fala livre de sua revisão."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_continuidade_resposta_recente import plano_atual
from tests.test_papo_casual_composicao import proposta


CASO = json.loads((Path(__file__).parent / 'fixtures/despertador_coruja_20261108.json').read_text(encoding='utf8'))
FALA = ' '.join(p['texto'] for p in CASO['propostas'][0]['suporte_proposicoes'])
PROBLEMA = 'citacao_incompleta_na_autoria'


@pytest.mark.parametrize('fala', [
    FALA,
    "A coruja respondeu: 'Voltarei amanhã.",
    'Na placa está escrito: “Vire à esquerda.',
])
def test_fala_com_citacao_incompleta_exige_reparo(fala):
    texto = CASO['entrada']
    plano = plano_atual(texto, ())
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert avaliacao['requer_reparo'] and not avaliacao['aceita']
    assert PROBLEMA in avaliacao['problemas_bloqueantes']
    assert PROBLEMA in verificar_fala_turno(fala, plano=plano)['problemas']


@pytest.mark.parametrize('fala', [
    "A coruja respondeu: 'Voltarei amanhã.'",
    'A placa diz: “Vire à esquerda.”',
    'A placa diz: "317".',
    "A coruja levou um copo d'água.",
    'O refrão dizia: «O sino tocou. O sino tocou.»',
    'A medida anotada é 5\'11".',
])
def test_aspas_validas_apostrofos_e_unidades_nao_pedem_reparo_de_citacao(fala):
    texto = 'Como você continuaria a história?'
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano_atual(texto, ()))
    assert PROBLEMA not in avaliacao['problemas']


def test_reproducao_literal_pedida_preserva_a_aspa_do_objeto():
    fala = "A coruja disse: 'Vire à esquerda."
    texto = 'Repita exatamente esta frase: ' + fala
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano_atual(texto, ()))
    assert PROBLEMA not in avaliacao['problemas']


def test_composicao_repara_aspa_que_ocultava_a_repeticao(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    reparo = ('Se ninguém responder, o relógio continua sussurrando e tenta de novo após um minuto. '
              'Ele só para quando a pessoa confirmar que acordou.')
    d = autoria.coletar_autoria(CASO, [*CASO['propostas'], proposta(reparo)])
    assert not d['operacional'] and not d['execucao_exigida']
    assert any(PROBLEMA in (t['problemas_bloqueantes'] or []) for t in d['trace'])
    assert d['resposta']['texto'] == reparo
    assert len(d['publicacoes']) == 1 and d['http'] == 2
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
