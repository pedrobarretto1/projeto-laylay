"""Ocorrências reais reproduzidas no adaptador instalado com HTTP fixo."""
import json
from pathlib import Path

import pytest

from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


CASOS = json.loads((Path(__file__).parent / 'fixtures/estrela_20261108.json').read_text(encoding='utf8'))


def coletar(monkeypatch, rodada, reparo=None):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    caso = CASOS[rodada]
    respostas = [caso['proposta']]
    if reparo is not None:
        respostas.append(proposta(reparo))
    d = autoria.coletar_autoria({'entrada': caso['entrada'], 'historico': []}, respostas)
    assert not d['operacional'] and not d['execucao_exigida']
    assert d['resposta']['tipo'] == 'resposta' and not d['resposta']['encerrada']
    assert len(d['publicacoes']) == 1
    return d


@pytest.mark.parametrize('rodada', ['3', '7', '12'])
def test_interpretacao_da_estrela_formato_e_convite_publicam_a_autoria(monkeypatch, rodada):
    d = coletar(monkeypatch, rodada)
    assert not d['plano']['atualidade']['depende_atualidade']
    assert d['resposta']['texto'] == CASOS[rodada]['proposta']['suporte_proposicoes'][0]['texto']
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert d['http'] == 1


def test_repeticao_interna_repara_antes_da_publicacao(monkeypatch):
    reparo = 'Escolheria a vermelha. Ver o jardim mudar de estação a cada minuto seria divertido.'
    d = coletar(monkeypatch, '8', reparo)
    assert any('repeticao_interna_de_enunciado' in (t['problemas_bloqueantes'] or [])
               for t in d['trace'])
    assert d['resposta']['texto'] == reparo
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert d['http'] == 2
