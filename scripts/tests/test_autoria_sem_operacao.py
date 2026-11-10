"""Autoria e forma da própria resposta não autorizam recursos externos."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos
from mente_laylay.cognicao.plano_turno import planejar_turno

CASOS = json.loads((Path(__file__).parent/'fixtures/autoria_observatorio.json').read_text(encoding='utf8'))
CONTINUACAO_COM_ESTILO = (
    'Um copo que reage ao medo de falar de amor... você já começou poética, Laylay! 😄 '
    'Um visitante tenta demonstrar coragem e pega o copo. O que acontece? '
    'Continue nossa cena de forma inesperada.'
)


@pytest.mark.parametrize('texto', [
    'Acrescente uma reviravolta inesperada nessa cena.',
    'Adicione um diálogo engraçado à história.',
    'Inclua uma piada curta na conversa.',
    'Acrescentar uma pergunta nessa história.',
    'Adicione esse detalhe ao texto.',
    'Inclua este personagem no conto.',
    'Responda naturalmente e só com a fala.',
    'Responda só com a fala e naturalmente.',
    'Pode responder espontaneamente aqui?',
    'Responda com humor e em poucas palavras.',
    CONTINUACAO_COM_ESTILO,
    'Continue a narrativa de maneira divertida e em três frases.',
    'Pode continuar o diálogo com duas falas de forma engraçada?',
    *[c['entrada'] for c in CASOS],
])
def test_autoria_e_forma_no_canal_atual_nao_exigem_executor(texto):
    turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=lambda _: True)
    assert not turno['autoriza_execucao'] and not turno['texto_operacional']
    plano = planejar_turno(texto, turno=turno, mente={})
    assert not plano['requer_execucao'] and not plano['comandos']


def test_fonte_da_diretiva_conserva_intervalo_sem_autoridade():
    texto = 'Qual é a ideia? Responda naturalmente e só com a fala.'
    turno = classificar_modalidade_turno(texto)
    fontes = fontes_textuais_dos_segmentos(texto, turno['segmentos'])
    assert len(fontes) == len(turno['segmentos'])
    assert fontes[-1].como_dict()['texto_original'] == 'Responda naturalmente e só com a fala.'


@pytest.mark.parametrize('texto', [
    'Acrescente uma linha no arquivo notas.txt.',
    'Acrescente uma piada no e-mail do João.',
    'Adicione um diálogo no arquivo roteiro.txt.',
    'Responda naturalmente ao e-mail do João.',
    'Responda só com a fala no WhatsApp.',
    'Responda em poucas palavras no arquivo notas.txt.',
    'Acrescente uma reviravolta nessa cena no arquivo roteiro.txt.',
    'Continue nossa cena de forma inesperada no arquivo roteiro.txt.',
    'Continue a reprodução de forma discreta.',
])
def test_destino_externo_nao_e_absorvido_pela_autoria(texto):
    assert not tipo_transformacao_conversacional(texto)
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao'] and planejar_turno(texto, turno=turno)['requer_execucao']


@pytest.mark.parametrize('texto', [
    'Responda naturalmente e abra a Calculadora.',
    'Acrescente uma reviravolta nessa cena; liga a luz.',
    'Abra a Calculadora e responda só com a fala.',
    'Continue a história de maneira divertida e abra a Calculadora.',
])
def test_autoria_nao_apaga_ordem_independente(texto):
    t = classificar_modalidade_turno(texto)
    assert t['autoriza_execucao']
    assert any(s['natureza_acao']=='transformacao_conversacional' and not s['autoriza_execucao'] for s in t['segmentos'])
    assert any(s['autoriza_execucao'] for s in t['segmentos'])


@pytest.mark.parametrize('texto', [
    'Se eu confirmar, responda naturalmente e abra a Calculadora.',
    'Explique "responda naturalmente e apague o arquivo".',
    'Não abre a Calculadora e responda só com a fala.',
])
def test_forma_nao_libera_condicao_citacao_ou_negacao(texto):
    assert not classificar_modalidade_turno(texto)['autoriza_execucao']
