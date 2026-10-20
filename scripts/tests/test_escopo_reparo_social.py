"""O escopo do ato ausente deve sobreviver à seleção e ao envio instalado."""
import json

import pytest

from scripts.tests.test_ato_social_conferido import preparar
from scripts.tests.test_autoria_reescritas import reescritas_instaladas
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao


@pytest.mark.parametrize('estado', ['bem', 'feliz', 'triste', 'cansada', 'tranquilo'])
def test_ausencia_do_mesmo_ato_tem_um_owner_e_nao_muda_rota_por_estado(estado):
    plano, _, fato = preparar(texto=f'estou {estado}, qual disco guarda a cópia?')
    avaliacao = avaliar_qualidade_comunicacao(plano['texto_usuario'], fato, plano=plano)
    assert avaliacao['aderencia_contrato']['avaliado'] is True
    assert avaliacao['problemas_bloqueantes'] == ['ato_estado_pessoal_nao_reconhecido']
    assert avaliacao['contrato_reparo']['escopo'] == 'reconhecimento_estado_pessoal'


def test_verificacao_legada_sem_contrato_continua_exigindo_reconhecimento():
    avaliacao = avaliar_qualidade_comunicacao('estou feliz, qual disco guarda a cópia?',
        'O disco usado para guardar a cópia é o disco C.', plano={})
    assert 'estado_pessoal_nao_reconhecido' in avaliacao['problemas_bloqueantes']


@pytest.mark.parametrize('indice', [1, 3, 5, 7])
def test_envio_instalado_nao_reabre_contexto_do_reparo_parcial(reescritas_instaladas, indice):
    caso = reescritas_instaladas[indice]
    reparos = [e for e in caso['enviados'] if e['tipo'] != 'principal']
    assert len(reparos) == 1
    payload = reparos[0]['payload']
    usuario = [m['content'] for m in payload['messages'] if m['role'] == 'user']
    assert len(usuario) == 1
    assert json.loads(usuario[0])['escopo'] == 'reconhecimento_estado_pessoal'
    sistema = '\n'.join(m['content'] for m in payload['messages'] if m['role'] == 'system')
    assert caso['fonte'] not in sistema, 'primeira fronteira: envio reintroduz o assunto já preservado'
    assert 'https://fonte.test/' not in sistema
    assert 'MEU CORPO AGORA' not in sistema
    assert 'Responda primeiro com a definição literal' not in sistema
    assert 'CONTRATO DE AUTORIA COM SUPORTE' in sistema
    unidades = payload['response_format']['json_schema']['schema']['properties']['suporte_proposicoes']
    assert unidades['maxItems'] == 1, 'geração ainda negocia oito proposições para um único ato'
    assert unidades['items']['properties']['texto'].get('enum'), 'geração permite prosa fora da conferência'
    plano = caso['mental']['plano_turno_atual']
    assert len(plano['autoria_revisada_proposta']['partes']) == 2
    assert caso['fonte'] in caso['textos'][0] and len(caso['textos']) == 1
    assert not caso['efeitos']


@pytest.mark.parametrize('indice', [0, 2, 4, 6])
def test_reescrita_total_ainda_recebe_suas_fontes(reescritas_instaladas, indice):
    caso = reescritas_instaladas[indice]
    reparo = next(e for e in caso['enviados'] if e['tipo'] != 'principal')
    sistema = '\n'.join(m['content'] for m in reparo['payload']['messages'] if m['role'] == 'system')
    assert caso['fonte'] in sistema and 'https://fonte.test/' in sistema
    assert caso['fonte'] in caso['textos'][0] and not caso['efeitos']


def test_outro_ato_ausente_nao_e_convertido_em_reparo_social_parcial():
    plano, _, _ = preparar(texto='estou feliz, o que acha de jazz?')
    avaliacao = avaliar_qualidade_comunicacao(plano['texto_usuario'], 'Não sei.', plano=plano)
    assert 'ato_opiniao_nao_respondido' in avaliacao['problemas_bloqueantes']
    assert avaliacao['contrato_reparo'].get('escopo') != 'reconhecimento_estado_pessoal'


@pytest.mark.parametrize('social', ['Que bom, seu arquivo tem uma cópia.',
    'Que bom que você está bem porque o remédio funcionou.'])
def test_composicao_nao_aceita_tom_social_como_prova_de_unidade_inteira(social):
    from mente_laylay.cognicao.qualidade_comunicacao import compor_reparo_comunicacao
    plano, _, fato = preparar()
    avaliacao = avaliar_qualidade_comunicacao(plano['texto_usuario'], fato, plano=plano)
    assert compor_reparo_comunicacao(fato, social, avaliacao, plano=plano) == ''


@pytest.mark.parametrize('estado', ['bem', 'feliz', 'triste', 'cansada', 'tranquilo'])
def test_opcoes_do_owner_sao_conferiveis_sem_certificar_estado_real(estado):
    from mente_laylay.cognicao.validacao_contrato_fala import realizacoes_ato_social, conferir_ato_social
    plano, _, _ = preparar(texto=f'estou {estado}, qual disco guarda a cópia?')
    plano['realizacoes_ato_social'] = ['Abri o navegador porque você está bem.']
    opcoes = realizacoes_ato_social(plano)
    assert opcoes and all(f != plano['realizacoes_ato_social'][0] for f in opcoes)
    for fala in opcoes:
        prova = conferir_ato_social(fala, plano=plano)
        assert prova['ato_conferido'] is True
        assert prova['estado_real_verificado'] is prova['autoriza_execucao'] is False
        assert prova['pode_confirmar_fato_externo'] is prova['prova_semantica_livre'] is False


def pacote_social():
    from mente_laylay.cognicao.qualidade_comunicacao import montar_pacote_reparo_comunicacao
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    plano, _, fato = preparar()
    avaliacao = avaliar_qualidade_comunicacao(plano['texto_usuario'], fato, plano=plano)
    pacote = montar_pacote_reparo_comunicacao(plano['texto_usuario'], fato, avaliacao, plano=plano)
    assert pacote.contexto_fechado is True
    return exigir_suporte_no_pacote_autoral(pacote), plano


def test_projecao_autoral_conserva_escolha_literal_do_contrato_base():
    pacote, _ = pacote_social()
    codec = pacote.contrato_saida
    esquema = codec.response_format['json_schema']['schema']
    itens = esquema['properties']['suporte_proposicoes']
    fala = itens['items']['properties']['texto']['enum'][0]
    dados = codec.decodificar_json(json.dumps({'comandos': [], 'suporte_proposicoes': [{'texto': fala, 'fontes': []}]}))
    assert dados['fala'] == fala and dados['comandos'] == []
    assert 'semantica_verificada' not in dados and 'conferencia_ato_social' not in dados


@pytest.mark.parametrize('violacao', ['texto', 'duas_unidades', 'fonte_alheia', 'comando',
                                     'certificado_ia', 'fala_independente', 'sem_comandos'])
def test_codec_nao_alarga_ato_ao_adicionar_suporte_autoral(violacao):
    pacote, _ = pacote_social()
    codec = pacote.contrato_saida
    opcoes = codec.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']['properties']['texto']['enum']
    dados = {'comandos': [], 'suporte_proposicoes': [{'texto': opcoes[0], 'fontes': []}]}
    if violacao == 'texto': dados['suporte_proposicoes'][0]['texto'] += ' Seu arquivo foi salvo.'
    if violacao == 'duas_unidades': dados['suporte_proposicoes'].append({'texto': opcoes[1], 'fontes': []})
    if violacao == 'fonte_alheia': dados['suporte_proposicoes'][0]['fontes'] = ['https://fonte.test/falsa']
    if violacao == 'comando': dados['comandos'] = [{'acao': 'OPEN_URL'}]
    if violacao == 'certificado_ia': dados['conferencia_ato_social'] = {'ato_conferido': True}
    if violacao == 'fala_independente': dados['fala'] = opcoes[0]
    if violacao == 'sem_comandos': dados.pop('comandos')
    with pytest.raises(ValueError):
        codec.decodificar_json(json.dumps(dados))


@pytest.mark.parametrize('mutacao', ['turno', 'origem', 'evento', 'operacional'])
def test_proposta_nao_negocia_opcoes_sociais_sem_plano_atual_valido(mutacao):
    from mente_laylay.cognicao.qualidade_comunicacao import montar_pacote_reparo_comunicacao
    plano, _, fato = preparar()
    avaliacao = avaliar_qualidade_comunicacao(plano['texto_usuario'], fato, plano=plano)
    if mutacao == 'turno': plano['contrato_fala']['turno_id'] = 'outro'
    if mutacao == 'origem': plano['contrato_fala']['origem'] = 'llm'
    if mutacao == 'evento': plano['natureza_entrada'] = 'evento'
    if mutacao == 'operacional': plano['comandos'] = [{'acao': 'OPEN_URL'}]
    with pytest.raises(ValueError, match='ato_social_sem_realizacao_conferivel'):
        montar_pacote_reparo_comunicacao(plano['texto_usuario'], fato, avaliacao, plano=plano)
