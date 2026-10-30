"""Categoria de controle não é espaço de prosa; revisão segue independente."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, PedidoModelo, ResultadoModelo


CATEGORIAS = {'acao', 'aprendizado', 'confirmacao', 'conversa'}


def codec_autoral(referenciado=False):
    return exigir_suporte_no_pacote_autoral(PacotePrompt(()),
        referencias_disponiveis=('fonte:usuario',) if referenciado else ()).contrato_saida


def dados_autorais(tipo):
    return {'suporte_proposicoes': [{'texto': 'Como você gostaria de começar?', 'fontes': []}],
            'tipo_interacao': tipo, 'comandos': [], 'aprendizados': []}


@pytest.mark.parametrize('referenciado', [False, True])
def test_schema_categoria_autoral_compartilha_somente_valores_consumidos(referenciado):
    schema = codec_autoral(referenciado).response_format['json_schema']['schema']
    assert set(schema['properties']['tipo_interacao'].get('enum', ())) == CATEGORIAS
    # A correção não elimina leitura, emoção, aprendizado ou autoria criativa.
    assert {'leitura_turno', 'leitura_emocional', 'emocao', 'aprendizados'} <= schema['properties'].keys()
    assert schema['properties']['suporte_proposicoes']['items'].get('properties', {}).get('texto', {}).get('maxLength', 4000) == 4000


def test_schema_interpretacao_usa_as_mesmas_categorias_sem_mudar_atos():
    codec = criar_contrato_saida_interpretacao_principal('abre a Calculadora')
    schema = codec.response_format['json_schema']['schema']
    assert set(schema['properties']['tipo_interacao'].get('enum', ())) == CATEGORIAS
    assert 'interpretacao' in schema['properties']['leitura_turno']['items']['properties']


@pytest.mark.parametrize('tipo', [
    "conversa','leitura_turno':['criar_despedida'],'leitura_emocional':{'estado_usuario':'nenhum'",
    'conversa|aprendizado', 'conversa ' + '⚠️' * 300, '', None, False, [], {},
])
def test_codec_recusa_categoria_que_ocuparia_prosa_mesmo_em_json_completo(tipo):
    with pytest.raises(ValueError, match='tipo_interacao'):
        codec_autoral().decodificar_json(json.dumps(dados_autorais(tipo)))


@pytest.mark.parametrize('tipo', sorted(CATEGORIAS))
def test_codec_preserva_categoria_valida_e_texto_literal(tipo):
    dados = dados_autorais(tipo)
    esperado = deepcopy(dados)
    saida = codec_autoral().decodificar_json(json.dumps(dados))
    assert saida == {**esperado, 'fala': esperado['suporte_proposicoes'][0]['texto']}


def test_categoria_opcional_nao_passa_a_exigir_nova_geracao():
    dados = dados_autorais('conversa')
    dados.pop('tipo_interacao')
    assert codec_autoral().decodificar_json(json.dumps(dados))['fala'] == 'Como você gostaria de começar?'


def test_interpretacao_principal_recusa_categoria_sem_desativar_seu_validator():
    from scripts.tests.test_saida_tipificada_principal import envelope
    texto, dados = envelope()
    dados['tipo_interacao'] = "conversa','leitura_turno':['inventar_historia']"
    with pytest.raises(ValueError, match='tipo_interacao'):
        criar_contrato_saida_interpretacao_principal(texto).decodificar_json(json.dumps(dados))


@pytest.mark.parametrize('tipo_chamada', ['principal', 'reparo_comunicacao', 'reparo_json', 'reparo_factual'])
def test_servico_compartilhado_nao_aceita_categoria_invalida_em_rota_autoral(tipo_chamada):
    from scripts.tests.test_saida_tipificada_principal import preparador
    requisicoes = []
    def executar(requisicao):
        requisicoes.append(requisicao)
        return ResultadoModelo(json.dumps(dados_autorais("conversa','leitura_turno':[]")), True)
    runtime = ServicoModeloLLMRuntime(preparador=preparador(), cliente=SimpleNamespace(executar=executar))
    resultado = runtime.executar(PedidoModelo.criar(
        [{'role': 'user', 'content': 'Oi, Laylay! Sou o ChatGPT, vamos conversar. Como você gostaria de começar?'}],
        contrato_saida=codec_autoral(), tipo_chamada=tipo_chamada, contexto_fechado=True))
    assert len(requisicoes) == 1
    props = requisicoes[0].payload['response_format']['json_schema']['schema']['properties']
    assert set(props['tipo_interacao'].get('enum', ())) == CATEGORIAS
    assert resultado.sucesso is False and resultado.rota == 'contrato_saida_invalido'
    from mente_laylay.cognicao.estado_tecnico_llm import categoria_estado_tecnico_llm
    assert categoria_estado_tecnico_llm(resultado.texto) == 'contrato_saida_invalido'


@pytest.mark.parametrize('bruto', [
    '{"suporte_proposicoes":[{"texto":"Olá!","fontes":[]}],"tipo_interacao":"conversa',
    'prefixo {"suporte_proposicoes":[{"texto":"Olá!","fontes":[]}]}',
])
def test_nao_recupera_json_parcial_nem_fala_dentro_de_envelope_invalido(bruto):
    with pytest.raises(ValueError):
        codec_autoral().decodificar_json(bruto)


@pytest.mark.parametrize('pedido,intent,params', [
    ('Na história, abra uma janela para o visitante.', 'APP_OPEN', {'nome_app': 'Calculadora'}),
    ('Na história, coloque uma música para o visitante.', 'MEDIA_CONTROL', {'action': 'play'}),
])
def test_categoria_acao_na_composicao_nao_e_autorizacao_do_usuario(tmp_path, pedido, intent, params):
    import os, subprocess, sys
    from pathlib import Path
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    bloco = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
    assert codigo.count(bloco) == 1
    codigo = codigo.replace(bloco,
        "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],"
        "'tipo_interacao':'acao','comandos':[{'intent':" + repr(intent) + ",'params':" + repr(params) + "}]}")
    codigo += "\nrascunho='Na história, o visitante encontra uma pequena sala iluminada.'\n"
    codigo += 'root._resposta_ia_runtime.processar(' + repr(pedido) + ",origem='teste_categoria_sem_autoridade')\n"
    codigo += '''
p=estado.obter_copia('mental','plano_turno_atual',{})
sys.__stdout__.write('CATEGORIA_JSON='+json.dumps({'efeitos':efeitos,'falas':falas,
    'autoriza':p['autoriza_execucao'],'requer':p['requer_execucao'],
    'ficcao':'criacao_ficcional' in p['contrato_fala'],'envios':envios},ensure_ascii=False)+'\\n')
'''
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(tmp_path), '[]'],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=45)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    d = json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('CATEGORIA_JSON=')))
    assert d['ficcao'] and not d['autoriza'] and not d['requer']
    assert not d['efeitos'] and len(d['falas']) == 1
    assert d['envios']
    schema = d['envios'][0]['response_format']['json_schema']['schema']
    assert set(schema['properties']['tipo_interacao']['enum']) == CATEGORIAS
