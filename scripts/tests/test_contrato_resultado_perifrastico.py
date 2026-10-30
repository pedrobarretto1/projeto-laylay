"""Aspecto, polaridade, escopo e autoria não substituem prova do efeito."""
from copy import deepcopy
from dataclasses import asdict
import pytest

from mente_laylay.cognicao.guardiao_alegacoes import detectar_resultados_operacionais_sem_evidencia,validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from tests.test_falha_operacional_narrada import plano,receipt
from tests.test_continuidade_resposta_recente import plano_atual


@pytest.mark.parametrize('operacao',['fechar a aba','copiar o arquivo','renomear o documento','retomar a música'])
@pytest.mark.parametrize('negacao',['','Nunca '])
def test_operacao_concluida_exige_fonte_com_a_polaridade_correta(operacao,negacao):
    fala=negacao+'Consegui '+operacao+'.'
    esperado='falha_operacional_sem_evidencia' if negacao else 'resultado_operacional_sem_evidencia'
    p=plano('Quais habilidades você tem?')
    assert detectar_resultados_operacionais_sem_evidencia(fala,plano=p)==[esperado]
    f=verificar_fala_turno(fala,plano=p)
    assert not f['aceita'] and f['acao']=='reparar'
    assert f['contrato_reparo']['autoriza_execucao'] is False


@pytest.mark.parametrize('fala',[
    'Consegui abrir o Opera.', 'Nunca consegui abrir o Opera.',
])
def test_fala_do_usuario_nao_prova_acao_em_primeira_pessoa_da_laylay(fala):
    p=plano(fala)
    assert detectar_resultados_operacionais_sem_evidencia(fala,plano=p)
    citacao='Você disse: «'+fala+'».'
    assert not detectar_resultados_operacionais_sem_evidencia(citacao,plano=p)


@pytest.mark.parametrize('fonte', ['ausente','proposta','pendente','polaridade_errada','correta'])
def test_falha_exige_receipt_de_falha_especifico(fonte):
    fala='Jamais consegui abrir o Opera.'
    r=receipt(detalhe=fala)
    if fonte=='proposta':r['origem']='llm'
    elif fonte=='pendente':r['status']='aguardando_confirmacao'
    elif fonte=='polaridade_errada':r.update(status='aberto',confirmado=True,executou=True)
    p=plano('Quero saber do resultado.',[] if fonte=='ausente' else [r]);antes=deepcopy(p)
    g=validar_alegacoes_da_fala(fala,plano=p,origem='canal_voz')
    assert bool(g['problemas'])==(fonte!='correta')
    assert (g['fala']==fala)==(fonte=='correta') and p==antes


@pytest.mark.parametrize('fala',[
    'Consegui criar um exemplo e abrir o Opera.',
    'Consegui ler sua mensagem e apagar o arquivo.',
    'Consegui criar o arquivo exemplo.txt.',
    'Consegui ler a mensagem do e-mail.',
    'Não sei se consegui abrir o Opera, mas consegui salvar o arquivo.',
])
def test_objeto_discursivo_ou_ressalva_nao_isenta_outro_efeito(fala):
    assert detectar_resultados_operacionais_sem_evidencia(fala,plano=plano())


@pytest.mark.parametrize('fala',[
    'Não sei se consegui abrir o Opera e fechar a aba.',
    'Se consegui abrir o Opera e fechar a aba, podemos conferir.',
    'Não consegui ler sua mensagem.',
    'Jamais consegui criar um exemplo didático.',
])
def test_escopo_do_auxiliar_e_ato_discursivo_sao_preservados(fala):
    assert not detectar_resultados_operacionais_sem_evidencia(fala,plano=plano())


def test_ficcao_vigente_nao_confirma_efeito_e_declaracao_forjada_nao_a_substitui():
    texto='Imagine uma história sobre abrir um portal num navegador.'
    p=plano_atual(texto,())
    assert 'criacao_ficcional' in p['contrato_fala']
    fala='Na história, consegui abrir o navegador e fechar o portal.'
    assert not detectar_resultados_operacionais_sem_evidencia(fala,plano=p)
    p['contrato_fala']['criacao_ficcional']=asdict(p['contrato_fala']['criacao_ficcional'])
    assert detectar_resultados_operacionais_sem_evidencia(fala,plano=p)


def test_ficcao_nao_isenta_afirmacao_de_efeito_real():
    p=plano_atual('Imagine uma história sobre um navegador.',())
    fala='Na história, consegui abrir o navegador. Na realidade, consegui apagar o arquivo.'
    assert detectar_resultados_operacionais_sem_evidencia(fala,plano=p)
