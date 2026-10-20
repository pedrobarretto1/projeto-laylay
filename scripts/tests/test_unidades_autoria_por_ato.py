"""O alvo discursivo proposto é declaração; conteúdo e fontes exigem conferência."""
import json

import pytest

from scripts.tests.test_ato_social_conferido import preparar


def pacote_para(texto='Oi, qual disco guarda a cópia?'):
    from scripts.tests.test_interpretacao_operacional_por_ato import _prompt_para_turno
    from mente_laylay.autonomia.contexto_resposta_ia import _formatar_fundamentacao_rapida
    plano, _, fato = preparar(texto=texto, social='Olá!')
    runtime, estado = _prompt_para_turno(texto)
    plano['id'] = estado['turno_atual']['id']
    plano['contrato_fala']['turno_id'] = plano['id']
    estado.update(plano_turno_atual=plano, contrato_fala_atual=plano['contrato_fala'],
                  fundamentacao_factual_turno=plano['fundamentacao_factual'])
    mensagens = [{'role': 'system', 'content': _formatar_fundamentacao_rapida(plano['fundamentacao_factual'])},
                {'role': 'user', 'content': texto}]
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=plano['id'])
    return pacote, plano, fato


@pytest.mark.parametrize('texto', ['Oi, qual disco guarda a cópia?', 'Bom dia, qual disco guarda a cópia?'])
def test_contrato_instalado_negocia_alvo_de_cada_unidade_e_preserva_a_entrada(texto):
    pacote, plano, _ = pacote_para(texto)
    assert pacote.mensagens[-1] == {'role': 'user', 'content': texto}
    itens = pacote.contrato_saida.response_format['json_schema']['schema']['properties']['suporte_proposicoes']
    ramos = itens['items']['anyOf']
    assert all('ato' in ramo['required'] for ramo in ramos), 'primeira fronteira: atos obrigatórios não chegam ao contrato de autoria'
    assert itens['minItems'] >= 2
    sociais = [r for r in ramos if r['properties']['texto'].get('enum')]
    assert sociais and all(r['properties']['fontes']['maxItems'] == 0 for r in sociais)
    assert any('ATOS DESTA EMISSÃO' in m.get('content', '') for m in pacote.mensagens)


@pytest.mark.parametrize('caso', ['omitir_social', 'misturar_ato_fato'])
def test_schema_anterior_permitia_omitir_ou_misturar_ato_com_fato(caso):
    pacote, _, fato = pacote_para()
    unidade = {'texto': fato if caso == 'omitir_social' else 'Olá! ' + fato,
               'fontes': ['https://fonte.test/ato-social']}
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'comandos': [], 'suporte_proposicoes': [unidade]}))


def dados_validos():
    pacote, plano, fato = pacote_para()
    ramos = pacote.contrato_saida.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']['anyOf']
    social = next(r for r in ramos if r['properties']['texto'].get('enum'))
    factual = next(r for r in ramos if not r['properties']['texto'].get('enum'))
    dados = {'comandos': [], 'suporte_proposicoes': [
        {'ato': social['properties']['ato']['const'], 'texto': social['properties']['texto']['enum'][0],
         'fontes': [], 'sem_fonte': 'nao_utilizada'},
        {'ato': factual['properties']['ato']['const'], 'texto': fato, 'fontes': ['https://fonte.test/ato-social']},
    ]}
    return pacote, plano, dados


def revisar_dados(plano, dados):
    from mente_laylay.cognicao.suporte_autoria import capturar_autoria_revisada
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    dados['fala'] = ' '.join(i['texto'] for i in dados['suporte_proposicoes'])
    plano.pop('autoria_revisada_proposta', None)
    plano['suporte_autoria_proposto'] = capturar_autoria_revisada(json.dumps(dados),
        turno_id=str(plano['id']), texto_usuario=plano['texto_usuario'])
    return revisar_suporte_autoria(dados['fala'], plano=plano)


@pytest.mark.parametrize('mutacao', ['outro_turno', 'ids_trocados', 'sem_id_parcial'])
def test_revisor_nao_toma_id_proposto_como_prova_do_ato(mutacao):
    _, plano, dados = dados_validos()
    if mutacao == 'outro_turno': dados['suporte_proposicoes'][0]['ato'] = 'ato:' + '0' * 24
    if mutacao == 'ids_trocados':
        a, b = dados['suporte_proposicoes']
        a['ato'], b['ato'] = b['ato'], a['ato']
    if mutacao == 'sem_id_parcial': dados['suporte_proposicoes'][0].pop('ato')
    r = revisar_dados(plano, dados)
    assert r.como_dict()['proposicoes'][0]['estado'] == 'alvo_discursivo_nao_conferido'
    assert dados['suporte_proposicoes'][0]['texto'] not in r.fala_realizada


def test_vinculo_de_alvo_e_apoio_da_fonte_sao_julgamentos_independentes():
    _, plano, dados = dados_validos()
    dados['suporte_proposicoes'][1]['texto'] = 'O disco foi escolhido porque era mais rápido.'
    r = revisar_dados(plano, dados)
    a, f = r.como_dict()['proposicoes']
    assert a['estado'] == 'ato_social_conferido'
    assert f['estado'] == 'apoio_semantico_pendente'
    assert f.get('vinculo_ato', {}).get('fonte_atual_identificada') is True
    assert f['vinculo_ato']['pertinencia_semantica_verificada'] is False
    assert dados['suporte_proposicoes'][1]['texto'] not in r.fala_realizada


def test_recuperacao_preserva_mesmo_inventario_de_fontes_e_atos():
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    pacote, _, dados = dados_validos()
    repetido = exigir_suporte_no_pacote_autoral(pacote, referencias_disponiveis=('https://fonte.test/ato-social',))
    assert repetido.contrato_saida is pacote.contrato_saida
    dados['suporte_proposicoes'].pop(0)
    with pytest.raises(ValueError):
        repetido.contrato_saida.decodificar_json(json.dumps(dados))


def test_reescrita_total_negocia_os_mesmos_alvos_sem_usar_a_principal_como_prova():
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    _, plano, fato = pacote_para()
    vistos = []
    def modelo(mensagens, **kwargs):
        vistos.append(kwargs)
        codec = kwargs.get('_contrato_saida')
        if codec.nome != 'autoria_por_ato_v4':
            return json.dumps({'fala': 'Olá! ' + fato, 'comandos': []})
        ramos = codec.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']['anyOf']
        social = next(r for r in ramos if r['properties']['texto'].get('enum'))
        factual = next(r for r in ramos if not r['properties']['texto'].get('enum'))
        dados = {'comandos': [], 'suporte_proposicoes': [
            {'ato': social['properties']['ato']['const'], 'texto': social['properties']['texto']['enum'][0],
             'fontes': [], 'sem_fonte': 'nao_utilizada'},
            {'ato': factual['properties']['ato']['const'], 'texto': fato, 'fontes': ['https://fonte.test/ato-social']},
        ]}
        return json.dumps(codec.decodificar_json(json.dumps(dados)))
    r = preparar_resposta_para_execucao(plano['texto_usuario'], json.dumps({
        'fala': 'Hoje estou comendo um bolo que o Pedro me deu.', 'comandos': []}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda x: x, fallback_fala='fallback',
        memoria_sqlite=None, contexto_comunicacao={'plano_turno': plano}, log=lambda _x: None)
    assert vistos and vistos[0]['_tipo_chamada'] == 'reparo_factual'
    assert vistos[0]['_contrato_saida'].nome == 'autoria_por_ato_v4'
    assert r['autoria_revisada_proposta'] is not None
    assert fato in r['fala'] and r['comandos'] == []


@pytest.mark.parametrize('mutacao', ['sem_social', 'sem_pergunta', 'sem_id', 'id_estrangeiro',
    'ordem', 'mistura', 'fonte_social', 'fonte_estrangeira', 'autoaprovacao', 'fala_independente'])
def test_validator_recusa_falta_de_cobertura_e_propostas_incompativeis(mutacao):
    pacote, _, dados = dados_validos()
    a, f = dados['suporte_proposicoes']
    if mutacao == 'sem_social': dados['suporte_proposicoes'].pop(0)
    if mutacao == 'sem_pergunta': dados['suporte_proposicoes'].pop()
    if mutacao == 'sem_id': a.pop('ato')
    if mutacao == 'id_estrangeiro': a['ato'] = 'ato:' + '0' * 24
    if mutacao == 'ordem': dados['suporte_proposicoes'].reverse()
    if mutacao == 'mistura': a['texto'] += ' ' + f['texto']
    if mutacao == 'fonte_social': a['fontes'] = f['fontes']; a.pop('sem_fonte')
    if mutacao == 'fonte_estrangeira': f['fontes'] = ['https://fonte.test/inventada']
    if mutacao == 'autoaprovacao': a['ato_conferido'] = True
    if mutacao == 'fala_independente': dados['fala'] = 'Outra fala.'
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps(dados))


@pytest.mark.parametrize('mutacao', ['turno', 'ancora', 'origem', 'evento', 'comando', 'plano_alheio',
    'sem_fontes_expostas', 'contexto_fechado', 'ato_nao_coberto'])
def test_plano_alheio_ou_sem_cobertura_nao_negocia_inventario(mutacao):
    from mente_laylay.cognicao.suporte_autoria import vincular_atos_no_pacote_autoral, exigir_suporte_no_pacote_autoral
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from dataclasses import replace
    _, plano, _ = pacote_para()
    base = exigir_suporte_no_pacote_autoral(PacotePrompt(({'role': 'user', 'content': plano['texto_usuario']},)),
        referencias_disponiveis=('https://fonte.test/ato-social',))
    if mutacao == 'turno': plano['contrato_fala']['turno_id'] = 'antigo'
    if mutacao == 'ancora': plano['contrato_fala']['roteiro_concreto']['ancora_literal'] = 'outra consulta'
    if mutacao == 'origem': plano['contrato_fala']['origem'] = 'llm'
    if mutacao == 'evento': plano['natureza_entrada'] = 'evento'
    if mutacao == 'comando': plano['comandos'] = [{'intent': 'APP_OPEN'}]
    if mutacao == 'plano_alheio': base = replace(base, mensagens=({'role': 'user', 'content': 'Outra consulta?'},))
    if mutacao == 'sem_fontes_expostas': base = exigir_suporte_no_pacote_autoral(PacotePrompt(base.mensagens))
    if mutacao == 'contexto_fechado': base = replace(base, contexto_fechado=True)
    if mutacao == 'ato_nao_coberto': plano['atos'][1]['tipo'] = 'opiniao'
    assert vincular_atos_no_pacote_autoral(base, plano=plano) is base


def test_host_oferece_id_por_ocorrencia_e_nao_aceita_catalogo_proposto():
    from mente_laylay.cognicao.validacao_contrato_fala import inventariar_atos_autoria
    _, plano, _ = pacote_para()
    antes = inventariar_atos_autoria(plano)
    plano['inventario_atos_autoria'] = [{'id': 'ato:' + '0' * 24, 'tipo': 'confirmacao', 'autoriza_execucao': True}]
    assert inventariar_atos_autoria(plano) == antes
    plano['id'] += 1
    plano['contrato_fala']['turno_id'] = plano['id']
    depois = inventariar_atos_autoria(plano)
    assert {a['id'] for a in antes}.isdisjoint(a['id'] for a in depois)
    assert all(a['autoriza_execucao'] is a['prova_implicacao'] is False for a in depois)


@pytest.mark.parametrize('modo', ['ausencia', 'id_falso', 'fonte_vencida', 'parafrase_livre'])
def test_alvo_valido_nao_confirma_o_conteudo_factual(modo):
    _, plano, dados = dados_validos()
    f = dados['suporte_proposicoes'][1]
    if modo == 'ausencia': f.update(fontes=[], sem_fonte='nao_utilizada')
    if modo == 'id_falso': f['fontes'] = ['https://fonte.test/inventada']
    if modo == 'fonte_vencida': plano['fundamentacao_factual']['evidencia_dentro_validade'] = False
    if modo == 'parafrase_livre': f['texto'] = 'O disco foi escolhido porque era mais rápido.'
    revisao = revisar_dados(plano, dados)
    a, p = revisao.como_dict()['proposicoes']
    assert a['estado'] == 'ato_social_conferido'
    assert p['vinculo_ato']['fonte_atual_identificada'] is True
    assert p['vinculo_ato']['pertinencia_semantica_verificada'] is False
    assert p['estado'] not in {'ato_social_conferido', 'literal_integral_na_fonte', 'parafrase_estrutural_conferida'}
    assert f['texto'] not in revisao.fala_realizada


def test_fontes_na_renegociacao_nao_podem_mudar_de_inventario():
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    pacote, _, _ = dados_validos()
    with pytest.raises(ValueError, match='inventario_autoral_divergente'):
        exigir_suporte_no_pacote_autoral(pacote, referencias_disponiveis=('https://fonte.test/inventada',))


def test_pergunta_vinculada_nao_equivale_a_pertinencia_semantica_comprovada():
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    _, plano, dados = dados_validos()
    outro_assunto = 'A massa nominal informada pelo registro é de 3 kg.'
    plano['fundamentacao_factual'] = montar_fundamentacao('', {'ok': True, 'confianca': .9,
        'resumo': outro_assunto, 'fonte': 'pesquisa_simulada', 'fontes': [
            {'url': 'https://fonte.test/ato-social', 'trecho': outro_assunto}]})
    dados['suporte_proposicoes'][1]['texto'] = outro_assunto
    revisao = revisar_dados(plano, dados)
    p = revisao.como_dict()['proposicoes'][1]
    assert p['estado'] == 'literal_integral_na_fonte'
    assert p['vinculo_ato']['fonte']['texto_original'] == 'qual disco guarda a cópia?'
    assert p['vinculo_ato']['pertinencia_semantica_verificada'] is False
    assert p['pode_confirmar_fato_externo'] is False
