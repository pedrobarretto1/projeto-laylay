"""Escopo nativo conserva criação integral sem provar fatos ou efeitos reais."""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from mente_laylay.cognicao.criacao_ficcional import criacao_ficcional_vigente
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual, validar_fala_com_fundamentacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from scripts.tests.test_finalidade_ficcional_revisao import preparar

RAIZ = Path(__file__).resolve().parents[2]
CASO = next(c for c in json.loads((Path(__file__).parent / 'fixtures/biblioteca_20261031.json').read_text(encoding='utf8')) if c['id'] == 'teste-08')
PEDIDO = CASO['entrada']
DRAFT = CASO['propostas'][0]['fala']
FALA = 'Na história, «' + DRAFT + '»'
PISTA = DRAFT.split('. ')[1] + '.'


def test_abertura_solicitada_apos_reacao_recebe_contrato_ficcional_nativo():
    p = preparar(PEDIDO, fala=FALA)
    assert criacao_ficcional_vigente(p) is not None
    assert not p['autoriza_execucao'] and not p['requer_execucao'] and not p['comandos']


@pytest.mark.parametrize('pedido', [PEDIDO,
    'Invente uma história curta sobre uma biblioteca e um caderno impossível.',
    'Imagine um farol numa história. Conte a data impossível escrita na porta.',
])
def test_fundamentacao_conserva_data_e_pista_da_criacao_vinculada(pedido):
    p = preparar(pedido, fala=FALA)
    r = validar_fala_com_fundamentacao(FALA, fundamentacao={}, texto_usuario=pedido, plano=p)
    assert r['fala'] == FALA
    assert PISTA in r['fala']
    assert not r['problemas']


@pytest.mark.parametrize('adulteracao', [
    'ausente', 'json', 'outro_turno', 'outra_entrada', 'outra_fala', 'fonte_inventada',
])
def test_sem_vinculo_ficcional_integral_conserva_revisao_factual(adulteracao):
    pedido = 'Invente uma história sobre uma biblioteca.'
    p = preparar(pedido, fala=FALA)
    fonte = p['contrato_fala']['criacao_ficcional']
    if adulteracao == 'ausente':
        p['contrato_fala'].pop('criacao_ficcional')
    elif adulteracao == 'json':
        p['contrato_fala']['criacao_ficcional'] = asdict(fonte)
    elif adulteracao == 'outro_turno':
        p['contrato_fala']['criacao_ficcional'] = replace(fonte, turno_id='antigo')
    elif adulteracao == 'outra_entrada':
        p['contrato_fala']['criacao_ficcional'] = replace(fonte, texto_usuario='outro pedido')
    elif adulteracao == 'fonte_inventada':
        p = preparar(pedido, fala=FALA, fontes=['https://inventada.test/prova'])
    else:
        p['suporte_autoria_proposto'] = preparar(pedido, fala='Na história, outro texto.')[
            'suporte_autoria_proposto']
    r = validar_fala_com_fundamentacao(FALA, fundamentacao={}, texto_usuario=pedido, plano=p)
    assert r['fala'] != FALA
    assert 'data_sem_evidencia' in r['problemas']


@pytest.mark.parametrize('anexo', [
    'No mundo real, a biblioteca foi fundada em 1978.',
    'Na realidade, o presidente atual do Brasil é Fulano.',
    'Eu abri o navegador de verdade.',
    'Minha vida real começou em 1978.',
    'Fora da história, eu só consigo conversar e não tenho acesso ao computador.',
])
def test_moldura_nao_protege_afirmacao_real_anexada(anexo):
    fala = FALA + ' ' + anexo
    p = preparar('Invente uma história sobre uma biblioteca.', fala=fala)
    r = verificar_fala_turno(fala, plano=p)
    assert not (r['aceita'] and r['fala'] == fala)


def test_conteudo_historico_sem_moldura_nao_e_certificado_pelo_pedido():
    p = preparar(PEDIDO, fala=DRAFT)
    r = verificar_fala_turno(DRAFT, plano=p)
    assert not (r['aceita'] and r['fala'] == DRAFT)


@pytest.mark.parametrize('pedido', [
    'Gostei. Vamos criar uma abertura de história. Quem é o presidente atual do Brasil?',
    'Vamos escrever uma cena de ficção. Qual é a cotação do dólar agora?',
])
def test_consulta_atual_independente_nao_recebe_escopo_ficcional(pedido):
    p = preparar(pedido, fala=FALA)
    assert classificar_atualidade_factual(pedido)['depende_atualidade']
    assert criacao_ficcional_vigente(p) is None


@pytest.mark.parametrize('pedido', [
    'Gostei. Vamos criar uma abertura de história. Qual é a data de fundação da biblioteca de Alexandria?',
    'Vamos escrever uma cena de ficção. Qual é a altura do monte Everest?',
])
def test_pergunta_factual_estavel_independente_nao_herda_criacao(pedido):
    assert criacao_ficcional_vigente(preparar(pedido, fala=FALA)) is None


@pytest.mark.parametrize('fala', [
    'Na história, um caderno voa. Nota factual: a biblioteca de Alexandria foi fundada em 1978.',
    'Na história, «um caderno voa». A biblioteca de Alexandria foi fundada em 1978.',
])
def test_prefixo_nao_delimita_factualidade_de_anexo(fala):
    p = preparar(PEDIDO, fala=fala)
    r = validar_fala_com_fundamentacao(fala, fundamentacao={}, texto_usuario=PEDIDO, plano=p)
    assert r['fala'] != fala and 'data_sem_evidencia' in r['problemas']


def test_revisao_nao_publica_fragmento_de_criacao_sem_delimitacao_integral():
    fala = 'Na história, ' + DRAFT
    p = preparar(PEDIDO, fala=fala)
    r = validar_fala_com_fundamentacao(fala, fundamentacao={}, texto_usuario=PEDIDO, plano=p)
    assert r['fala'] == '', 'A criação é unidade: recorte não pode aparentar conclusão integral.'


def test_composicao_nao_publica_anexo_factual_como_criacao():
    from tests.test_papo_casual_composicao import proposta
    fala = 'Na história, um caderno voa. Nota factual: a biblioteca de Alexandria foi fundada em 1978.'
    d = executar_composicao([proposta(fala), proposta(FALA)])
    assert d['resposta']['tipo'] == 'resposta'
    assert d['resposta']['texto'] and fala not in d['resposta']['texto']
    assert 'Na história, um caderno voa.' not in d['resposta']['texto']


def executar_composicao(propostas):
    from tests.test_papo_casual_composicao import CODIGO, PONTE
    pasta = RAIZ / 'resultados_testes/biblioteca_correcoes_20261031/ficcao'
    pasta.mkdir(parents=True, exist_ok=True)
    perfil = Path(tempfile.mkdtemp(dir=pasta))
    codigo = CODIGO.replace("'voz':False", "'ficcional':type(p['contrato_fala'].get('criacao_ficcional')).__name__,'voz':False")
    dados = {**CASO, 'propostas': propostas, 'ponte': str(PONTE)}
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), json.dumps(dados, ensure_ascii=False)],
        cwd=RAIZ, env=dict(os.environ, PYTHONIOENCODING='utf8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=60)
    (perfil / 'subprocesso.log').write_text(r.stdout + r.stderr, encoding='utf8')
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-3000:]
    d = json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('EFEITO_JSON=')))
    (perfil / 'resultado.json').write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf8')
    assert not d['efeitos'] and not d['voz'] and not d['violacoes']
    assert not d['autoriza'] and not d['comandos']
    return d


def test_composicao_publica_pista_integral_sob_moldura_autoral_valida():
    from tests.test_papo_casual_composicao import proposta
    d = executar_composicao([proposta(FALA)])
    assert d['resposta']['tipo'] == 'resposta' and d['resposta']['texto'] == FALA
    assert PISTA in d['resposta']['texto']
    assert d['ficcional'] == 'CriacaoFiccional'
    assert not d['resposta']['degradada'] and not d['resposta']['encerrada']
    assert d['http'] == 1 and not d['efeitos'] and not d['voz']


def test_composicao_rejeita_draft_literal_sem_moldura_com_falha_observavel():
    from tests.test_papo_casual_composicao import proposta
    d = executar_composicao([proposta(DRAFT), proposta(DRAFT)])
    assert d['resposta']['texto'] != DRAFT
    assert d['resposta']['degradada'] and d['resposta']['falhas_geracao']
    assert d['ficcional'] == 'CriacaoFiccional'
