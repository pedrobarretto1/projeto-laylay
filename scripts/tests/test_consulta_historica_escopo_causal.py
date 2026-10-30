"""Relato passado e explicação de outro assunto não formam consulta histórica."""
import json
from pathlib import Path
import pytest
from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_historica
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala

CASOS=json.loads((Path(__file__).parent/'fixtures/papo_casual.json').read_text(encoding='utf8'))
CONVERSA=[c['entrada']for c in CASOS if c['id']in {'papo-005','papo-009'}]
CONVERSA += ['Você apertou um botão imaginário. As pessoas dão nome às coisas porque gostam de companhia. Você acha engraçado?',
    'Você perguntou o que quero fazer agora? Só conversar. A gente levou dez minutos para criar uma história.',
    'Você disse olá. A causa do arco-íris é outra. Gostou da história?',
    'Você abriu o editor porque eu pedi. Vamos conversar?',
    'Você falou de música. Por que as pessoas gostam de dar nome aos objetos?']

@pytest.mark.parametrize('texto',CONVERSA)
def test_causa_declarada_ou_predicado_de_outra_oracao_nao_impoem_passado(texto):
    assert referencia_explicacao_historica(texto)=='',texto
    t=classificar_modalidade_turno(texto);p=planejar_turno(texto,turno=t)
    c=construir_contrato_semantico_fala(texto,turno=t,plano=p)
    assert not {'explicacao_ocorrencia','evidencia_fala_historica',
        'explicacoes_historicas_por_ato'}.intersection(c)

@pytest.mark.parametrize('texto,esperado',[
    ('Você abriu o navegador. Por que você fez isso?','ocorrencia'),
    ('Não entendi por que você disse isso?','fala'),
    ('Qual o motivo da sua decisão?','ocorrencia'),
    ('Qual foi o motivo da sua decisão?','ocorrencia'),
    ('Quando você abriu o arquivo, qual foi a causa?','ocorrencia'),
    ('Você abriu o navegador. Qual foi o motivo?','ocorrencia'),
    ('Você disse isso. Explique por quê.','fala'),
    ('Você disse isso. Qual foi a razão?','fala'),
    ('Você abriu o arquivo. E por quê?','ocorrencia'),
    ('Você abriu o arquivo. Por qual motivo?','ocorrencia'),
    ('O que motivou sua decisão?','ocorrencia'),
    ('Que motivo levou você a apagar o arquivo?','ocorrencia'),
    ('O que te levou a apagar esse arquivo?','ocorrencia'),
    ('Qual o motivo de você dizer isso?','fala'),
    ('Explique sua reação.','ocorrencia'),
    ('Quando você disse "oi", o que estava confirmado?','fala'),
    ('Por que ela apagou o arquivo?','outro_agente'),
])
def test_consulta_retrospectiva_real_conserva_owner_e_limite(texto,esperado):
    assert referencia_explicacao_historica(texto)==esperado
