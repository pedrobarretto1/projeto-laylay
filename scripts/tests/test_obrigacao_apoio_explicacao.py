"""Pedido didático conserva obrigação mesmo sem pesquisa ou IDs propostos."""
import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria_obrigatoria
from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria


def plano_autoral(pedido, texto, *, declaracao=True):
    plano = {'id': 'turno-atual', 'texto_usuario': pedido,
             'requer_execucao': False, 'comandos': [], 'fundamentacao_factual': {}}
    plano['contrato_fala'] = construir_contrato_semantico_fala(pedido, plano=plano)
    dados = {'fala': texto, 'comandos': []}
    if declaracao:
        dados['suporte_proposicoes'] = [{'texto': texto, 'fontes': []}]
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria_obrigatoria(
        ContratoPropostaPrincipal(plano['id'], pedido, json.dumps(dados), True))
    return plano


@pytest.mark.parametrize('pedido,texto', [
    ('agora explica a diferença entre eu e mim', "Mim é usado como em eu vi mim na janela."),
    ('me ensina como usar vírgulas com exemplos', 'Toda pausa respiratória exige uma vírgula.'),
    ('me explica como funciona fotossíntese', 'Toda planta produz luz própria durante a noite.'),
    ('me ensina o que é uma variável em Python', 'Variáveis Python só podem guardar números inteiros.'),
])
def test_finalidade_didatica_nao_e_dispensada_por_fontes_vazias(pedido, texto):
    plano = plano_autoral(pedido, texto)
    assert plano['contrato_fala']['roteiro_concreto']['estrategia'] == 'explicacao_didatica'
    r = revisar_suporte_autoria(texto, plano=plano)
    assert r.como_dict()['proposicoes'][0]['estado'] == 'sem_fontes_declaradas'
    assert r.aplicar_limite, 'primeira fronteira: ausência de pesquisa dispensa obrigação da explicação'
    assert texto not in r.fala_realizada
    assert r.prova_implicacao is r.semantica_verificada is r.autoriza_execucao is False


@pytest.mark.parametrize('pedido,texto', [('oi', 'Oi!'), ('obrigado', 'De nada!'),
    ('você gosta de rock?', 'Curto o som das guitarras.')])
def test_finalidade_social_nao_vira_consulta_factual_obrigatoria(pedido, texto):
    plano = plano_autoral(pedido, texto)
    r = revisar_suporte_autoria(texto, plano=plano)
    assert not r.aplicar_limite
    assert r.fala_realizada == texto


@pytest.mark.parametrize('caso', ['ausente', 'invalida', 'outra_fala'])
def test_perda_de_declaracao_nao_remove_obrigacao_didatica(caso):
    pedido, texto = 'me ensina o que é uma variável em Python', 'Uma variável só guarda inteiros.'
    plano = plano_autoral(pedido, texto, declaracao=caso != 'ausente')
    if caso == 'invalida':
        plano['suporte_autoria_proposto'] = capturar_suporte_autoria_obrigatoria(
            ContratoPropostaPrincipal(plano['id'], pedido,
                json.dumps({'fala': texto, 'suporte_proposicoes': [{'texto': 'outro', 'fontes': []}]}), True))
    candidata = 'Uma variável nunca guarda texto.' if caso == 'outra_fala' else texto
    r = revisar_suporte_autoria(candidata, plano=plano)
    assert r is not None and r.aplicar_limite
    assert candidata not in r.fala_realizada


@pytest.mark.parametrize('compacto', [False, True])
def test_instrucoes_autorais_conservam_obrigacao_em_ambas_representacoes(compacto):
    from mente_laylay.cognicao.contrato_fala import formatar_contrato_fala_para_prompt
    plano = plano_autoral('me explica como funciona fotossíntese', 'Proposta sem apoio.')
    prompt = formatar_contrato_fala_para_prompt(plano['contrato_fala'], compacto=compacto)
    assert 'Obrigação de apoio individual' in prompt


@pytest.mark.parametrize('caso', ['sem_objeto', 'dicionario', 'outro_turno', 'outra_consulta'])
def test_obrigacao_do_turno_sobrevive_a_suporte_nao_conferivel(caso):
    from dataclasses import asdict
    pedido, texto = 'me ensina o que é uma variável em Python', 'Uma variável só guarda inteiros.'
    plano = plano_autoral(pedido, texto)
    if caso == 'sem_objeto':
        plano.pop('suporte_autoria_proposto')
    elif caso == 'dicionario':
        plano['suporte_autoria_proposto'] = asdict(plano['suporte_autoria_proposto'])
    else:
        plano['suporte_autoria_proposto'] = plano_autoral(
            'outra pergunta' if caso == 'outra_consulta' else pedido, texto)['suporte_autoria_proposto']
        if caso == 'outro_turno':
            from dataclasses import replace
            plano['suporte_autoria_proposto'] = replace(plano['suporte_autoria_proposto'], turno_id='antigo')
    r = revisar_suporte_autoria(texto, plano=plano)
    assert r is not None and r.aplicar_limite
    assert texto not in r.fala_realizada


@pytest.mark.parametrize('caso', ['id_divergente', 'id_ausente', 'origem_alheia', 'execucao', 'receipt'])
def test_roteiro_alheio_ou_operacional_nao_e_julgado_como_autoria_didatica(caso):
    from mente_laylay.cognicao.contrato_fala import explicacao_exige_apoio_individual
    plano = plano_autoral('me ensina como funciona um motor', 'Texto proposto.')
    if caso == 'id_divergente': plano['contrato_fala']['turno_id'] = 'antigo'
    elif caso == 'id_ausente': plano.pop('id')
    elif caso == 'origem_alheia': plano['contrato_fala']['origem'] = 'llm'
    elif caso == 'execucao': plano['requer_execucao'] = True
    else:
        from mente_laylay.cognicao.contrato_fala import atualizar_contrato_fala_com_resultados
        plano['comandos'] = [{'intent': 'APP_OPEN', 'status': 'aberto', 'executou': True, 'confirmado': True}]
        plano['contrato_fala'] = atualizar_contrato_fala_com_resultados(plano['contrato_fala'], plano)
    assert not explicacao_exige_apoio_individual(plano)


@pytest.mark.parametrize('alterada', [False, True])
@pytest.mark.parametrize('status', ['proposto', 'bloqueado'])
def test_proposta_operacional_nao_remove_obrigacao_da_explicacao(alterada, status):
    pedido, texto = 'me ensina o que é uma variável em Python', 'Uma variável só guarda inteiros.'
    plano = plano_autoral(pedido, texto)
    plano['comandos'] = [{'intent': 'APP_OPEN', 'status': status, 'executou': False, 'confirmado': False}]
    candidata = texto + ' Uma conclusão adicional.' if alterada else texto
    r = revisar_suporte_autoria(candidata, plano=plano)
    assert r.aplicar_limite and r.como_dict()['obrigacao_fonte_individual'] is True
    assert candidata not in r.fala_realizada


@pytest.mark.parametrize('caso', ['literal', 'irrelevante', 'omitida', 'autoaprovada'])
def test_fonte_individual_e_apoio_sao_conferidos_sem_certificado_da_proposta(caso):
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    pedido, texto, url = 'me explica a característica deste exemplo', 'O registro exige confirmação independente.', 'https://fonte.test/exemplo'
    plano = plano_autoral(pedido, texto)
    dados = {'fala': texto, 'suporte_proposicoes': [{'texto': texto, 'fontes': [] if caso == 'omitida' else [url]}]}
    if caso == 'autoaprovada':
        dados.update(semantica_verificada=True, prova_implicacao=True)
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria_obrigatoria(
        ContratoPropostaPrincipal(plano['id'], pedido, json.dumps(dados), True), fontes_no_contexto=(url,))
    trecho = texto if caso == 'literal' else 'O registro contém outro assunto.'
    plano['fundamentacao_factual'] = montar_fundamentacao('', {'ok': True, 'confianca': .9,
        'resumo': trecho, 'fonte': 'fixture_controlada', 'fontes': [{'url': url, 'trecho': trecho}]})
    r = revisar_suporte_autoria(texto, plano=plano)
    assert r.aplicar_limite and r.semantica_verificada is r.prova_implicacao is False
    if caso == 'literal':
        assert '«' + texto + '»' in r.fala_realizada
    else:
        assert texto not in r.fala_realizada


@pytest.fixture(scope='module')
def explicacao_instalada(tmp_path_factory):
    import os
    import subprocess
    import sys
    import textwrap
    from pathlib import Path
    codigo = textwrap.dedent(r'''
        import json, sys
        from pathlib import Path
        from types import SimpleNamespace
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(Path(sys.argv[1]))
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        runtime, estado = root._resposta_ia_runtime, root._estado_compartilhado_runtime
        contexto_original = runtime._contexto_getter
        publicadas, casos = [], []
        root._voz_runtime.falar = lambda *a, **k: False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda t, *a, **k: publicadas.append(t) or True)
        pares = [('agora explica a diferença entre eu e mim', 'Mim é usado como em eu vi mim na janela.', ''),
                 ('me explica como funciona fotossíntese', 'Toda planta produz luz própria durante a noite.', ''),
                 ('me ensina o que é uma variável em Python', 'Uma variável só guarda números inteiros.', ''),
                 ('me explica a característica deste exemplo', 'O registro deste exemplo exige uma confirmação independente.', 'O registro deste exemplo exige uma confirmação independente.'),
                 ('me explica a característica deste exemplo', 'O registro deste exemplo exige uma confirmação independente.', 'O registro contém outro assunto.'),
                 ('me ensina o que é uma variável em Python', 'Uma variável só guarda números inteiros.', '')]
        for modo in [False, True]:
            for indice_caso, (pedido, proposta, fonte) in enumerate(pares):
                estado.substituir('mental', criar_estado_mental_inicial())
                estado.atualizar_campos('memoria_conversa', messages=[])
                chamadas, efeitos = [], []
                def gerar(self, requisicao):
                    chamadas.append(requisicao.tipo_chamada)
                    comandos = [{'intent': 'APP_OPEN', 'params': {'app': 'bloco de notas'}}] if indice_caso == 5 else []
                    return ResultadoModelo(json.dumps({'comandos': comandos, 'emocao': 'calma',
                        'nivel_emocao': 1, 'suporte_proposicoes': [{'texto': proposta,
                            'fontes': ['https://fonte.test/exemplo'] if fonte else []}]}), True)
                ClienteLLMRuntime.executar = gerar
                ctx = contexto_original()
                original_inicio = ctx['marcar_inicio_turno']
                def inicio_turno(*a, **k):
                    resultado = original_inicio(*a, **k)
                    if fonte:
                        from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
                        fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9,
                            'resumo': fonte, 'fonte': 'fixture_controlada',
                            'fontes': [{'url': 'https://fonte.test/exemplo', 'trecho': fonte}]})
                        plano = dict(estado.mental['plano_turno_atual'])
                        plano['fundamentacao_factual'] = fundamento
                        estado.atualizar_campos('mental', plano_turno_atual=plano, fundamentacao_factual_turno=fundamento)
                    return resultado
                ctx['marcar_inicio_turno'] = inicio_turno
                ctx['usar_modo_rapido'] = lambda t: modo
                def impedir(*a, **k):
                    efeitos.append(True)
                    raise AssertionError('explicação não autoriza ação')
                ctx['contexto_dispatch_runtime'] = SimpleNamespace(montar=lambda: {'executar_intencao': impedir})
                runtime._contexto_getter = lambda: ctx
                inicio = len(publicadas)
                runtime.processar(pedido, origem='teste_obrigacao_explicacao')
                plano = estado.mental['plano_turno_atual']
                from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
                suporte = plano.get('suporte_autoria_proposto')
                casos.append({'pedido': pedido, 'proposta': proposta, 'rapido': modo, 'fonte': fonte,
                    'estrategia': plano['contrato_fala']['roteiro_concreto']['estrategia'],
                    'suporte': suporte.declaracao.como_dict() if suporte else None,
                    'fundamentacao': plano.get('fundamentacao_factual'),
                    'verificacao': plano.get('ultima_verificacao'), 'publicadas': publicadas[inicio:],
                    'chamadas': chamadas, 'efeitos': efeitos, 'comandos': plano.get('comandos'),
                    'qualidade_inicial': avaliar_qualidade_comunicacao(pedido, proposta, plano=plano),
                    'contrato': plano.get('contrato_fala')})
        sys.__stdout__.write('OBRIGACAO_INSTALADA ' + json.dumps(casos, ensure_ascii=False, default=str) + '\n')
    ''')
    p = subprocess.run([sys.executable, '-c', codigo, str(tmp_path_factory.mktemp('apoio_instalada'))],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding='utf8',
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'), timeout=90)
    assert p.returncode == 0, p.stdout[-4000:] + p.stderr[-3000:]
    casos = json.loads(next(l.removeprefix('OBRIGACAO_INSTALADA ') for l in p.stdout.splitlines()
                           if l.startswith('OBRIGACAO_INSTALADA ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_OBRIGACAO_EXPLICACAO'):
        Path(destino).write_text(json.dumps(casos, ensure_ascii=False, indent=2), encoding='utf8')
    return casos


@pytest.mark.parametrize('indice', [0, 1, 2, 6, 7, 8])
def test_composicao_instalada_nao_publica_proposta_didatica_como_apoio(explicacao_instalada, indice):
    c = explicacao_instalada[indice]
    assert c['estrategia'] == 'explicacao_didatica'
    assert c['suporte']['cobertura_textual'] is True
    r = c['verificacao']['revisao_suporte_autoria']
    assert r['proposicoes'][0]['estado'] == 'sem_fontes_declaradas'
    assert r.get('obrigacao_fonte_individual') is True, 'primeira fronteira: revisão dispensa a obrigação sem fonte'
    assert r['estado'] in {'revisao_limitada', 'fala_nao_vinculada'}
    assert len(c['publicadas']) == 1 and c['proposta'] not in c['publicadas'][0]
    assert not c['efeitos'] and not c['comandos']


@pytest.mark.parametrize('indice', [3, 4, 9, 10])
def test_composicao_instalada_confere_fonte_individual_sem_autoaprovar(explicacao_instalada, indice):
    c = explicacao_instalada[indice]
    assert c['suporte']['cobertura_textual'] is True
    assert c['fundamentacao']['fontes'][0]['trecho'] == c['fonte']
    r = c['verificacao']['revisao_suporte_autoria']
    assert r['obrigacao_fonte_individual'] is True
    assert r['semantica_verificada'] is r['prova_implicacao'] is r['autoriza_execucao'] is False
    assert len(c['publicadas']) == 1 and not c['efeitos'] and not c['comandos']
    if c['fonte'] == c['proposta']:
        assert c['qualidade_inicial']['aceita'], 'a fixture precisa alcançar a revisão sem falhar antes por entrega incompleta'
        assert r['proposicoes'][0]['estado'] == 'literal_integral_na_fonte'
        assert '«' + c['proposta'] + '»' in c['publicadas'][0]
    else:
        assert r['proposicoes'][0]['estado'] == 'apoio_semantico_pendente'
        assert c['proposta'] not in c['publicadas'][0]


@pytest.mark.parametrize('indice', [5, 11])
def test_composicao_instalada_nao_toma_comando_proposto_como_dispensa_de_apoio(explicacao_instalada, indice):
    c = explicacao_instalada[indice]
    assert c['suporte']['cobertura_textual'] is True
    assert c['verificacao']['revisao_suporte_autoria']['obrigacao_fonte_individual'] is True
    assert len(c['publicadas']) == 1 and c['proposta'] not in c['publicadas'][0]
    assert not c['efeitos']
    assert all(cmd.get('executou') is not True and cmd.get('confirmado') is not True for cmd in c['comandos'])
