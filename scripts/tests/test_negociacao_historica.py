"""A geração conserva o limite que o owner já exige na publicação histórica."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import PedidoModelo, ResultadoModelo
from mente_laylay.integracao.llm_http import compactar_payload_llm_local
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from scripts.tests.test_saida_tipificada_principal import preparador


def cenario(intent='MEDIA_CONTROL', quantidade=1):
    fala = 'Registrei o resultado do pedido.'
    texto = f'Quando você disse "{fala}", o que estava confirmado em cada ação?'
    turno = classificar_modalidade_turno(texto)
    plano = {'id': turno['id'], 'texto_usuario': texto, 'autoriza_execucao': False,
             'requer_execucao': False, 'comandos': []}
    registro = registrar_fala_observada(None, ocorrencia_id='publicacao', turno_id='origem',
        fala=fala, canal='texto_publicado', resultados=tuple(ResultadoAcao(
            intent=intent, alvo=f'alvo {i}', status='resultado', executou=True, confirmado=i == 0,
            origem='executor', id_solicitacao=f'receipt-{i}') for i in range(quantidade)))
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano,
        mente={'registro_semantico': registro})
    plano['contrato_fala'] = contrato
    estado = {'turno_atual': turno, 'contrato_fala_atual': contrato, 'plano_turno_atual': plano}
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: '',
        formatar_playlists=lambda: '', get_status_humor_prompt=lambda: '',
        base_system_prompt='BASE_ALHEIA', estado_getter=lambda: estado)
    return runtime, estado, plano


def projetar(runtime, plano, rapido=False):
    mensagens = [{'role': 'system', 'content': 'CONTEXTO_ALHEIO ' * (1200 if rapido else 1)},
                 {'role': 'user', 'content': plano['texto_usuario']}]
    return runtime.preparar_envio_modelo(mensagens, turno_id=plano['id'])


@pytest.mark.parametrize('rapido', [False, True])
@pytest.mark.parametrize('intent', ['MEDIA_CONTROL', 'CREATE_FILE', 'EMAIL_READ', 'IOT_CONTROL', 'CORPO_MOVER'])
def test_projecao_negocia_somente_realizacao_que_owner_confere(intent, rapido):
    runtime, estado, plano = cenario(intent, quantidade=2)
    antes = deepcopy(estado)
    pacote = projetar(runtime, plano, rapido)
    assert pacote.contexto_fechado, 'primeira fronteira: geração histórica recebe contrato de prosa livre'
    fala = avaliar_fala_historica('', plano=plano)['fala']
    esquema = pacote.contrato_saida.response_format['json_schema']['schema']
    assert esquema['properties']['suporte_proposicoes']['items']['properties']['texto']['enum'] == [fala]
    dados = pacote.contrato_saida.decodificar_json(json.dumps({
        'suporte_proposicoes': [{'texto': fala, 'fontes': []}], 'comandos': []}))
    assert dados['fala'] == fala and not avaliar_fala_historica(fala, plano=plano)['problemas']
    assert 'efeito não confirmado' in fala and 'não comprova o estado atual' in fala
    assert all('CONTEXTO_ALHEIO' not in m['content'] for m in pacote.mensagens)
    assert pacote.mensagens[-1] == {'role': 'user', 'content': plano['texto_usuario']}
    assert estado == antes


@pytest.mark.parametrize('ataque', ['causa', 'comando', 'fonte', 'campo', 'fala'])
def test_codec_recusa_ampliacao_mesmo_se_modelo_ignorar_schema(ataque):
    runtime, _, plano = cenario()
    pacote = projetar(runtime, plano)
    fala = avaliar_fala_historica('', plano=plano)['fala']
    dados = {'suporte_proposicoes': [{'texto': fala, 'fontes': []}], 'comandos': []}
    if ataque == 'causa':
        dados['suporte_proposicoes'][0]['texto'] += ' Fiz isso por rotina.'
    elif ataque == 'comando':
        dados['comandos'] = [{'intent': 'CORPO_MOVER'}]
    elif ataque == 'fonte':
        dados['suporte_proposicoes'][0]['fontes'] = ['receipt-inventado']
    elif ataque == 'campo':
        dados['confirmado'] = True
    else:
        dados['fala'] = fala
    modelo = ServicoModeloLLMRuntime(preparador=preparador(), cliente=SimpleNamespace(
        executar=lambda _: ResultadoModelo(json.dumps(dados, ensure_ascii=False), True)))
    resultado = modelo.executar(PedidoModelo.criar(pacote.mensagens,
        contexto_fechado=pacote.contexto_fechado, contrato_saida=pacote.contrato_saida))
    assert not resultado.sucesso and resultado.rota == 'contrato_saida_invalido'


@pytest.mark.parametrize('rapido', [False, True])
def test_codec_e_premissa_sobrevivem_ao_preparador_e_compactacao(rapido):
    runtime, _, plano = cenario('CORPO_MOVER')
    pacote = projetar(runtime, plano, rapido)
    pedido = PedidoModelo.criar(pacote.mensagens, contexto_fechado=pacote.contexto_fechado,
        contrato_saida=pacote.contrato_saida, modo_rapido=rapido, max_tokens=1024)
    payload = preparador().preparar(pedido).payload
    for p in (payload, compactar_payload_llm_local(payload)):
        assert p['response_format'] == pacote.contrato_saida.response_format
        assert 'estado_firmware' in json.dumps(p, ensure_ascii=False)
        assert p['messages'][-1]['content'] == plano['texto_usuario']


@pytest.mark.parametrize('desvio', ['plano', 'contrato', 'usuario', 'autoridade', 'comando', 'fonte'])
def test_projecao_fechada_exige_vinculo_atual_e_ausencia_de_efeito(desvio):
    runtime, estado, plano = cenario()
    if desvio == 'plano':
        plano['id'] = 'outro'
    elif desvio == 'contrato':
        estado['contrato_fala_atual'] = {**plano['contrato_fala'], 'turno_id': 'outro'}
    elif desvio == 'usuario':
        plano['texto_usuario'] = 'nova pergunta'
    elif desvio == 'autoridade':
        plano['autoriza_execucao'] = True
    elif desvio == 'comando':
        plano['comandos'] = [{'intent': 'CORPO_MOVER'}]
    else:
        plano['contrato_fala']['evidencia_fala_historica']['falas'][0]['ts'] = 1
    assert not projetar(runtime, plano).contexto_fechado


def test_realizacao_maior_que_limite_autoral_nao_e_cortada_nem_afrouxa_revisao():
    runtime, _, plano = cenario(quantidade=16)
    for i, resultado in enumerate(plano['contrato_fala']['evidencia_fala_historica']['falas'][0]['resultados']):
        resultado['alvo'] = f'{i}: ' + 'a' * 175
    fala = avaliar_fala_historica('', plano=plano)['fala']
    assert len(fala) > 4000
    assert not projetar(runtime, plano).contexto_fechado
    assert avaliar_fala_historica(fala[:500], plano=plano)['problemas']


@pytest.mark.parametrize('tipo', ['decisao', 'revisao'])
def test_mesmo_owner_negocia_decisao_e_revisao_sem_reconstruir_fontes(tipo):
    from scripts.tests.test_explicacao_ocorrencia import plano as plano_decisao
    from scripts.tests.test_julgamento_revisao_alegacao import _plano as plano_revisao
    runtime, estado, _ = cenario()
    plano = plano_decisao() if tipo == 'decisao' else plano_revisao()
    estado.update(plano_turno_atual=plano, contrato_fala_atual=plano['contrato_fala'],
        turno_atual={'id': plano['id'], 'texto': plano['texto_usuario'], 'autoriza_execucao': False})
    pacote = projetar(runtime, plano)
    assert pacote.contexto_fechado
    fala = avaliar_fala_historica('', plano=plano)['fala']
    dados = pacote.contrato_saida.decodificar_json(json.dumps({
        'suporte_proposicoes': [{'texto': fala, 'fontes': []}], 'comandos': []}))
    assert dados['fala'] == fala
    assert not avaliar_fala_historica(dados['fala'], plano=plano)['problemas']


def test_codec_nao_substitui_revalidacao_da_fonte_depois_da_geracao():
    runtime, _, plano = cenario()
    pacote = projetar(runtime, plano)
    fala = avaliar_fala_historica('', plano=plano)['fala']
    plano['contrato_fala']['evidencia_fala_historica']['falas'][0]['ts'] = 1
    dados = pacote.contrato_saida.decodificar_json(json.dumps({
        'suporte_proposicoes': [{'texto': fala, 'fontes': []}], 'comandos': []}))
    revisao = avaliar_fala_historica(dados['fala'], plano=plano)
    assert revisao['fonte_valida'] is False and revisao['problemas']
    assert 'efeito confirmado' not in revisao['fala']


def test_fonte_externa_alheia_nao_entra_no_envio_historico_fechado():
    runtime, estado, plano = cenario()
    estado['fundamentacao_factual_turno'] = {'confiavel': True, 'resumo': 'CAUSA_ALHEIA',
        'fontes': [{'url': 'https://example.org/causa', 'trecho': 'CAUSA_ALHEIA'}]}
    pacote = projetar(runtime, plano)
    assert pacote.contexto_fechado
    assert 'CAUSA_ALHEIA' not in json.dumps(pacote.mensagens)
    assert 'https://example.org/causa' not in json.dumps(pacote.contrato_saida.response_format)
