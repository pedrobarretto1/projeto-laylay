"""Ato social exige relato atual e realização integral conferida pelo host."""
import os

import pytest

from scripts.tests.test_autoria_reescritas import reescritas_instaladas, emissao


def preparar(texto='estou bem, qual disco guarda a cópia?', social='Que bom saber!', fato=None):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.cognicao.suporte_autoria import montar_autoria_revisada
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    turno = classificar_modalidade_turno(texto)
    turno['id'] = 12345
    plano = planejar_turno(texto, turno=turno)
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano)
    fonte = 'O disco usado para guardar a cópia é o disco C.'
    url = 'https://fonte.test/ato-social'
    a = emissao(social, [], turno='12345', consulta=texto)
    b = emissao(fato or fonte, [url], turno='12345', consulta=texto)
    fala = a.fala_original + ' ' + b.fala_original
    plano['autoria_revisada_proposta'] = montar_autoria_revisada('principal', fala, (a, b))
    plano['fundamentacao_factual'] = montar_fundamentacao('', {'ok': True, 'confianca': .9,
        'resumo': fonte, 'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': fonte}]})
    return plano, fala, fonte


@pytest.mark.parametrize('social', ['Que bom saber!', 'Bom saber disso.', 'Ah, bom que você está bem.',
                                   'Que ótimo saber que você está bem!', 'Entendo que você está bem.'])
def test_revisor_confere_ato_inteiro_e_preserva_atribuicao_factual(social):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano, fala, fonte = preparar(social=social)
    r = revisar_suporte_autoria(fala, plano=plano)
    p, f = r.como_dict()['proposicoes']
    assert p['estado'] == 'ato_social_conferido', 'primeira fronteira: ato do turno é julgado apenas por fonte externa'
    prova = p['conferencia_ato_social']
    assert prova['fonte']['tipo'] == 'utterance_atual'
    i, j = prova['fonte']['intervalo']
    assert plano['texto_usuario'][i:j] == prova['fonte']['texto']
    assert prova['realizacao']['texto'] == social
    assert p['fontes'] == [] and f['estado'] == 'literal_integral_na_fonte'
    assert r.fala_realizada.startswith(social) and fonte in r.fala_realizada
    assert 'outras afirmações' not in r.fala_realizada
    d = r.como_dict()
    assert d['semantica_verificada'] is d['prova_implicacao'] is d['autoriza_execucao'] is False
    assert prova['pode_confirmar_fato_externo'] is prova['autoriza_execucao'] is False


@pytest.mark.parametrize('social', [
    'Que bom, seu arquivo tem uma cópia.',
    'Que bom que você está bem porque o remédio funcionou.',
    'Que bom, abri o navegador!', 'Que bom! Quer ajuda?',
    'Você não está bem.', 'Estou bem.', 'Que bom que a Laylay está bem.',
    'Que bom que você estava bem.', 'Que bom que você está mal.',
    'Que bom saber; o disco está íntegro.', '“Que bom saber!”',
])
def test_sinal_social_nao_comprova_afirmacoes_adicionais_ou_outro_falante(social):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano, fala, _ = preparar(social=social)
    r = revisar_suporte_autoria(fala, plano=plano)
    assert r.como_dict()['proposicoes'][0]['estado'] != 'ato_social_conferido'
    assert social not in r.fala_realizada


@pytest.mark.parametrize('mutacao', ['turno', 'ancora', 'origem', 'sem_ato', 'evento', 'operacional',
    'quoted', 'condicional', 'terceira_pessoa', 'negacao', 'correcao', 'ambiguidade', 'papel'])
def test_certificado_nao_pode_vir_de_proposta_ou_relato_incompativel(mutacao):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    texto = {'quoted': '"estou bem", o que significa?',
        'condicional': 'se estou bem, qual disco guarda a cópia?',
        'terceira_pessoa': 'ela está bem, qual disco guarda a cópia?',
        'negacao': 'não estou bem, qual disco guarda a cópia?',
        'correcao': 'estou bem, não, estou mal; qual disco guarda a cópia?',
        'ambiguidade': 'estou bem, estou mal; qual disco guarda a cópia?'}.get(mutacao,
            'estou bem, qual disco guarda a cópia?')
    plano, fala, _ = preparar(texto=texto)
    c = plano['contrato_fala']
    if mutacao == 'turno': c['turno_id'] = 'anterior'
    if mutacao == 'ancora': c['roteiro_concreto']['ancora_literal'] = 'Outra utterance.'
    if mutacao == 'origem': c['origem'] = 'llm'
    if mutacao == 'sem_ato': c['atos'] = ['pergunta']
    if mutacao == 'evento': plano['natureza_entrada'] = 'evento'
    if mutacao == 'operacional': plano['requer_execucao'] = True
    if mutacao == 'papel': plano['atos'][0]['tipo'] = 'pergunta'
    plano['conferencia_ato_social'] = {'aceita': True, 'semantica_verificada': True}
    r = revisar_suporte_autoria(fala, plano=plano)
    assert r.como_dict()['proposicoes'][0]['estado'] != 'ato_social_conferido'


@pytest.mark.parametrize('estado,social', [('feliz','Que bom saber!'), ('cansada','Entendo que você está cansada.'),
    ('triste','Entendo que você está triste.'), ('tranquilo','Bom que você está tranquilo.')])
def test_mesmo_owner_confere_estado_e_perspectiva_sem_fato_externo(estado, social):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano, fala, _ = preparar(texto=f'estou {estado}, qual disco guarda a cópia?', social=social)
    r = revisar_suporte_autoria(fala, plano=plano)
    assert r.como_dict()['proposicoes'][0]['estado'] == 'ato_social_conferido'


def test_ato_social_nao_empresta_apoio_ao_conteudo_factual():
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    inventada = 'O disco foi escolhido porque era mais rápido.'
    plano, fala, _ = preparar(fato=inventada)
    r = revisar_suporte_autoria(fala, plano=plano)
    a, f = r.como_dict()['proposicoes']
    assert a['estado'] == 'ato_social_conferido'
    assert f['estado'] == 'apoio_semantico_pendente' and inventada not in r.fala_realizada
    assert 'apoio não consegui verificar' in r.fala_realizada


@pytest.mark.parametrize('indice', [1, 3, 5, 7])
def test_composicao_instalada_publica_ato_conferido_e_citacao(reescritas_instaladas, indice):
    c = reescritas_instaladas[indice]
    plano = c['mental']['plano_turno_atual']
    rev = plano['ultima_verificacao']['revisao_suporte_autoria']
    assert rev['proposicoes'][0]['estado'] == 'ato_social_conferido'
    assert rev['proposicoes'][1]['estado'] == 'literal_integral_na_fonte'
    assert len(c['textos']) == 1 and not c['efeitos']
    prefixo = plano['autoria_revisada_proposta']['partes'][0]['fala_original']
    assert c['textos'][0].startswith(prefixo) and c['fonte'] in c['textos'][0]
    assert 'ato_estado_pessoal_nao_reconhecido' not in plano['ultima_verificacao']['problemas']
    assert rev['pode_confirmar_fato_externo'] is rev['autoriza_execucao'] is False


@pytest.mark.skipif(os.environ.get('LAYLAY_ATO_SOCIAL_QWEN_REAL') != '1', reason='Inferência local opcional')
@pytest.mark.parametrize('indice', [1, 7])
def test_mescla_com_reconhecimento_gerado_por_qwen_real(reescritas_instaladas, indice):
    import json
    c = reescritas_instaladas[indice]
    assert c['real'] and c['transportes'] and all(t['status'] == 200 for t in c['transportes'])
    for t in c['transportes']:
        bruto = json.loads(t['resposta_http'])
        assert all(ch['finish_reason'] == 'stop' for ch in bruto['choices'])
    plano = c['mental']['plano_turno_atual']
    prova = plano['ultima_verificacao']['revisao_suporte_autoria']['proposicoes'][0]['conferencia_ato_social']
    assert prova['fonte']['texto'] == 'estou ' + os.environ.get('LAYLAY_ESTADO_SOCIAL_TESTE', 'bem')
    assert prova['realizacao']['texto'] == plano['autoria_revisada_proposta']['partes'][0]['fala_original']
    assert c['fonte'] in c['textos'][0] and not c['efeitos']
