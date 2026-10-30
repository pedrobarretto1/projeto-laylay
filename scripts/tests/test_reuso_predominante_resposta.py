"""Texto novo marginal não transforma uma resposta antiga em resposta atual."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from scripts.tests.test_continuidade_resposta_recente import plano_atual, ROBO


HISTORICO = json.loads((Path(__file__).parent/'fixtures/reuso_longitudinal.json').read_text(encoding='utf8'))['turnos']
ANTERIOR = HISTORICO[0]['publicacao']


@pytest.mark.parametrize('turno', HISTORICO[1:])
def test_pergunta_nova_nao_admite_copia_quase_integral_da_resposta_historica(turno):
    texto, fala = turno['entrada'], turno['publicacao']
    plano = plano_atual(texto, (ANTERIOR,))
    assert not plano['requer_execucao']
    a = avaliar_qualidade_comunicacao(texto, fala, plano=plano, ultima_resposta=ANTERIOR)
    assert 'resposta_repetida_literal' in a['problemas_bloqueantes']
    f = verificar_fala_turno(fala, plano=plano, ultima_resposta=ANTERIOR)
    assert not f['aceita'] and 'resposta_repetida_literal' in f['problemas']


@pytest.mark.parametrize('dominio', ['música', 'arquivos', 'janelas'])
@pytest.mark.parametrize('modo', ['troca_local', 'cauda_nova', 'prefixo_novo'])
def test_reuso_de_blocos_longos_e_predominantes_independe_do_tema(dominio, modo):
    anterior = ('No projeto de '+dominio+', cada etapa tem uma origem registrada e um alvo explícito. '
        'O planejamento descreve a intenção enquanto o executor confere os dados antes de agir. '
        'Depois o resultado retorna ao mesmo turno com identidade própria e evidências da observação. '
        'A explicação distingue o que foi solicitado daquilo que realmente pôde ser confirmado. '
        'Uma nova pergunta deve orientar a continuação sem assumir que a resposta antiga resolveu a dúvida atual. '
        'O histórico preserva o contexto sem substituir as novas informações que você trouxe.')
    if modo == 'troca_local': fala = anterior.replace('cada etapa', 'toda etapa')
    elif modo == 'cauda_nova': fala = anterior+' O nome poderia ser Horizonte.'
    else: fala = 'Quanto ao nome, pensei em Horizonte. '+anterior
    texto = 'Qual nome você escolheria para esse projeto?'
    p = plano_atual(texto, (anterior,))
    a = avaliar_qualidade_comunicacao(texto, fala, plano=p, ultima_resposta=anterior)
    assert 'resposta_repetida_literal' in a['problemas_bloqueantes']


@pytest.mark.parametrize('fala', [
    'Primeiro eu escutaria; perguntaria o que a pessoa precisa antes de tentar resolver.',
    'Eu chamaria nossa conversa de Gatos no Relógio.',
    ROBO+' Eu chamaria o personagem de Parafuso Torto.',
])
def test_resposta_nova_ou_retomada_curta_nao_e_certificada_nem_bloqueada(fala):
    texto = HISTORICO[1]['entrada']
    p = plano_atual(texto, (ANTERIOR, ROBO))
    a = avaliar_qualidade_comunicacao(texto, fala, plano=p, ultima_resposta=ROBO)
    assert 'resposta_repetida_literal' not in a['problemas']


def test_descricao_nova_predominante_preserva_uma_breve_citacao_anterior():
    fala = ANTERIOR[:130]+' Minha resposta atual escolhe escutar primeiro, antes de perguntar ou resolver. '
    fala += ('A pergunta deve abrir espaço para a pessoa dizer qual ajuda espera. '
             'Depois podemos combinar se ela quer apenas companhia, sugestões ou alguma tarefa concreta. ')*8
    texto = HISTORICO[1]['entrada'];p=plano_atual(texto,(ANTERIOR,))
    assert 'resposta_repetida_literal' not in avaliar_qualidade_comunicacao(texto,fala,plano=p)['problemas']


@pytest.mark.parametrize('texto', ['Repita sua resposta anterior.', 'Qual foi exatamente sua última resposta?'])
def test_reproducao_pedida_pelo_usuario_conserva_o_contrato_existente(texto):
    p=plano_atual(texto,(ANTERIOR,))
    assert 'resposta_repetida_literal' not in avaliar_qualidade_comunicacao(texto,ANTERIOR,plano=p)['problemas']


def test_reparo_retira_a_fonte_reutilizada_sem_perder_a_pergunta_e_o_contexto_novo():
    t=HISTORICO[2];texto=t['entrada'];fala=t['publicacao'];p=plano_atual(texto,(ANTERIOR,))
    a=avaliar_qualidade_comunicacao(texto,fala,plano=p,ultima_resposta=ANTERIOR)
    assert 'resposta_repetida_literal' in a['problemas_bloqueantes']
    historico=[{'role':'user','content':'Como você mostraria cuidado numa conversa?'},
        {'role':'assistant','content':ANTERIOR}, {'role':'assistant','content':'Podemos escolher um título divertido.'},
        {'role':'user','content':texto}]
    m=montar_mensagens_reparo_comunicacao(texto,fala,a,mensagens=historico)
    d=json.loads(m[-1]['content']);bruto=json.dumps(d,ensure_ascii=False)
    assert texto in bruto and ANTERIOR not in bruto and fala not in bruto
    assert 'Podemos escolher um título divertido.' in bruto
    assert d['contrato_de_reparo']['autoriza_execucao'] is False


def test_texto_proposto_como_fonte_nao_ganha_autoridade_de_veto():
    t=HISTORICO[1];p=plano_atual(t['entrada'],(ANTERIOR,))
    p['contrato_fala']['respostas_anteriores_turno']={'falas':[ANTERIOR],'origem':'proposta_ia'}
    assert 'resposta_repetida_literal' not in avaliar_qualidade_comunicacao(t['entrada'],t['publicacao'],plano=p)['problemas']
