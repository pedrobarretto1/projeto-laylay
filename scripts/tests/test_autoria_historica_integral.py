"""Realizações do owner conservam texto e suporte sem aumentar limites."""
from copy import deepcopy
import json

import pytest

from mente_laylay.cognicao.suporte_autoria import (
    conferir_suporte_proposicoes, exigir_suporte_no_pacote_autoral, capturar_autoria_revisada,
)
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, PedidoModelo
from mente_laylay.integracao.llm_http import compactar_payload_llm_local
from scripts.tests.test_negociacao_historica import cenario, projetar
from scripts.tests.test_saida_tipificada_principal import preparador


def partes_de_referencia(fala):
    """Oráculo de transporte literal; não interpreta proposições ou fontes."""
    partes, restante = [], fala
    while len(restante) > 500:
        candidatos = [i for i in range(1, 501) if restante[i] == ' '
            and not restante[i-1].isspace() and not restante[i+1].isspace()]
        assert candidatos, 'controle exige ponto de junção literal'
        i = max(candidatos)
        partes.append(restante[:i])
        restante = restante[i+1:]
    return [*partes, restante]


def envelope(fala):
    return {'comandos': [], 'suporte_proposicoes': [
        {'texto': parte, 'fontes': []} for parte in partes_de_referencia(fala)]}


def pacote_restrito(opcoes):
    def validar(dados):
        if set(dados) != {'fala', 'comandos'} or dados['fala'] not in opcoes or dados['comandos'] != []:
            raise ValueError('realizacao_recusada_pelo_owner')
    codec = ContratoSaidaEstruturada('owner_teste', '[OWNER]', {
        'type': 'object', 'additionalProperties': False, 'required': ['fala', 'comandos'],
        'properties': {'fala': {'type': 'string', 'enum': opcoes},
            'comandos': {'type': 'array', 'maxItems': 0, 'items': {'type': 'object'}}}}, validar)
    return exigir_suporte_no_pacote_autoral(PacotePrompt((
        {'role': 'system', 'content': 'Realização conferível pelo owner.'},
        {'role': 'user', 'content': 'Explique as etapas.'}), contrato_saida=codec))


@pytest.mark.parametrize('quantidade', [2, 4, 8])
def test_enum_do_owner_pode_ocupar_varias_unidades_sem_aumentar_limite(quantidade):
    fala = ' '.join(f'Etapa {i}: ' + chr(97+i) * 280 + '.' for i in range(quantidade))
    entrada = envelope(fala)
    assert 500 < len(fala) <= 4000 and 1 < len(entrada['suporte_proposicoes']) <= 8
    # Falsifica incapacidade da captura: a declaração integral já é válida.
    assert conferir_suporte_proposicoes({**entrada, 'fala': fala})[0] == fala
    pacote = pacote_restrito([fala])
    schema = pacote.contrato_saida.response_format['json_schema']['schema']
    unidades = schema['properties']['suporte_proposicoes']
    assert unidades['maxItems'] > 1, 'primeira fronteira: enum completo é forçado a uma unidade'
    assert unidades['items']['properties']['texto']['enum'] == partes_de_referencia(fala)
    saida = pacote.contrato_saida.decodificar_json(json.dumps(entrada))
    assert saida['fala'] == fala and saida['comandos'] == []
    captura = capturar_autoria_revisada(json.dumps(saida), turno_id='consulta', texto_usuario='Explique as etapas.')
    assert captura.declaracao.como_dict()['cobertura_textual'] is True
    assert captura.prova_implicacao is captura.autoriza_execucao is False


@pytest.mark.parametrize('intent', ['MEDIA_CONTROL', 'CREATE_FILE', 'EMAIL_READ', 'IOT_CONTROL', 'CORPO_MOVER'])
@pytest.mark.parametrize('rapido', [False, True])
def test_historico_composto_negocia_todas_as_premissas_do_owner(intent, rapido):
    runtime, estado, plano = cenario(intent, quantidade=8)
    antes = deepcopy(estado)
    avaliacao = avaliar_fala_historica('', plano=plano)
    fala = avaliacao['fala']
    assert avaliacao['fonte_valida'] and 500 < len(fala) < 4000
    pacote = projetar(runtime, plano, rapido)
    assert pacote.contexto_fechado, 'owner válido fica em prosa livre só porque excede uma unidade'
    saida = pacote.contrato_saida.decodificar_json(json.dumps(envelope(fala)))
    assert saida['fala'] == fala and fala.count('etapa ') == 9  # oito resultados e o limite sobre processamento
    assert not avaliar_fala_historica(saida['fala'], plano=plano)['problemas']
    assert estado == antes


@pytest.mark.parametrize('ataque', ['omissao', 'ordem', 'duplicata', 'causa', 'fonte', 'comando', 'corte', 'limite'])
def test_multiplas_unidades_nao_perdem_cobertura_ou_criam_autoridade(ataque):
    runtime, _, plano = cenario(quantidade=8)
    fala = avaliar_fala_historica('', plano=plano)['fala']
    pacote = projetar(runtime, plano)
    assert pacote.contexto_fechado
    dados = envelope(fala)
    itens = dados['suporte_proposicoes']
    if ataque == 'omissao': itens.pop()
    elif ataque == 'ordem': itens.reverse()
    elif ataque == 'duplicata': itens[1] = dict(itens[0])
    elif ataque == 'causa': itens[-1]['texto'] += ' A causa foi uma rotina.'
    elif ataque == 'fonte': itens[0]['fontes'] = ['receipt_inventado']
    elif ataque == 'comando': dados['comandos'] = [{'intent': 'CORPO_MOVER'}]
    elif ataque == 'corte': itens[-1]['texto'] = itens[-1]['texto'][:-10]
    else: dados['suporte_proposicoes'] = [{'texto': fala, 'fontes': []}]
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps(dados))


def test_partes_de_opcoes_distintas_nao_formam_nova_realizacao():
    opcoes = [' '.join(f'Etapa {i}: ' + chr(ord(c)+i) * 280 + '.' for i in range(3)) for c in ('a', 'x')]
    pacote = pacote_restrito(opcoes)
    dados = envelope(opcoes[0])
    dados['suporte_proposicoes'][-1] = envelope(opcoes[1])['suporte_proposicoes'][-1]
    with pytest.raises(ValueError): pacote.contrato_saida.decodificar_json(json.dumps(dados))


@pytest.mark.parametrize('rapido', [False, True])
def test_projecao_longa_chega_ao_payload_sem_corte(rapido):
    runtime, _, plano = cenario('CORPO_MOVER', quantidade=8)
    fala = avaliar_fala_historica('', plano=plano)['fala']
    pacote = projetar(runtime, plano, rapido)
    pedido = PedidoModelo.criar(pacote.mensagens, contrato_saida=pacote.contrato_saida,
        contexto_fechado=pacote.contexto_fechado, modo_rapido=rapido, max_tokens=1024)
    payload = preparador().preparar(pedido).payload
    for p in (payload, compactar_payload_llm_local(payload)):
        esquema = p['response_format']['json_schema']['schema']
        partes = esquema['properties']['suporte_proposicoes']['items']['properties']['texto']['enum']
        assert ' '.join(partes) == fala
        assert all(len(s) <= 500 for s in partes)


def test_explicacoes_por_ato_conservam_dois_owners_e_limites():
    from scripts.tests.test_explicacao_historica_por_ato import consulta, owner_dois_dominios
    runtime, estado, _ = cenario()
    turno, plano = consulta(recuperar=owner_dois_dominios)
    estado.update(turno_atual=turno, plano_turno_atual=plano, contrato_fala_atual=plano['contrato_fala'])
    fala = avaliar_fala_historica('', plano=plano)['fala']
    pacote = projetar(runtime, plano)
    assert pacote.contexto_fechado and len(fala) > 500
    dados = pacote.contrato_saida.decodificar_json(json.dumps(envelope(fala)))
    assert dados['fala'] == fala and fala.count('Sobre ') == 2
    assert 'pedido explicito de copia' in fala and 'regra autorizada do usuario' in fala


def test_prosa_livre_continua_limitada_a_500_por_unidade():
    pacote = exigir_suporte_no_pacote_autoral(PacotePrompt(({'role': 'user', 'content': 'Converse.'},)))
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({
            'suporte_proposicoes': [{'texto': 'a' * 501, 'fontes': []}]}))


@pytest.mark.parametrize('fala', ['', ' a', 'a ', 'a' * 501, 'a' * 4001,
    ' '.join('a' * 280 for _ in range(3)), 42, None])
def test_realizacao_sem_ancoras_integrais_nao_afrouxa_guardas(fala):
    from mente_laylay.cognicao.suporte_autoria import segmentar_realizacao_autoral
    assert segmentar_realizacao_autoral(fala) == ()


@pytest.mark.parametrize('texto', [
    'Etapa á: ' + 'ç' * 280 + '. Etapa β: ' + 'ω' * 280 + '.',
    'Relato: "dois  espaços";\nressalva preservada. ' + 'a' * 280 + ' Fim: ' + 'b' * 280,
    'a' * 500,
    'a' * 499 + ' b',
])
def test_particionamento_preserva_literal_inclusive_espacos_aspas_e_unicode(texto):
    from mente_laylay.cognicao.suporte_autoria import segmentar_realizacao_autoral
    partes = segmentar_realizacao_autoral(texto)
    assert partes and ' '.join(partes) == texto
    assert all(0 < len(p) <= 500 for p in partes) and len(partes) <= 8
    dados = pacote_restrito([texto]).contrato_saida.decodificar_json(json.dumps(envelope(texto)))
    assert dados['fala'].encode('utf-8') == texto.encode('utf-8')


def test_realizacao_longa_nao_empresta_apoio_da_escolha_ou_do_schema():
    runtime, _, plano = cenario(quantidade=8)
    pacote = projetar(runtime, plano)
    fala = avaliar_fala_historica('', plano=plano)['fala']
    dados = pacote.contrato_saida.decodificar_json(json.dumps(envelope(fala)))
    # O owner continua responsável por validade da fonte depois da geração.
    plano['contrato_fala']['evidencia_fala_historica']['falas'][0]['ts'] = 1
    revisao = avaliar_fala_historica(dados['fala'], plano=plano)
    assert revisao['fonte_valida'] is False and revisao['problemas']
    assert revisao['prova_semantica_livre'] is revisao['autoriza_execucao'] is False
