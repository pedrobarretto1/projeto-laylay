"""Conclusão global não substitui as confirmações parciais da mesma invocação."""
import json
from dataclasses import asdict, replace, FrozenInstanceError

import pytest

from mente_laylay.memoria_mental.resultado_acao import (
    AspectoResultado, ResultadoAcao, identificar_solicitacao_execucao, normalizar_resultado_acao,
)
from mente_laylay.personalidade.planejador_resposta import (
    fala_resultado_por_aspectos, planejar_resposta_acao, fala_factual_resultados_compostos,
)


@pytest.fixture(scope='module')
def respostas_instaladas(tmp_path_factory):
    from scripts.tests.test_leituras_parciais_corpo import parciais_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_RESPOSTA_IMEDIATA', '1')
        return parciais_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('caso', ['parcial', 'zero', 'divergente', 'ultrapassou', 'sem_parada'])
def test_publicacao_declara_aspectos_sem_promover_falha_global(caso, respostas_instaladas):
    c = respostas_instaladas['medidas_ocorrencias'][caso]
    assert all(respostas_instaladas['owners'].values())
    r = c['publicacoes'][0]
    bruto = r['contexto']['receipt_corpo']
    assert r['confirmado'] is False and bruto['aplicacao_pwm_confirmada'] is True
    assert bruto['parada_confirmada'] is (caso != 'sem_parada')
    aspectos = r.get('aspectos', [])
    assert aspectos, 'falta projeção canônica dos aspectos para a fala; receipt bruto foi preservado'
    assert [(a['escopo'], a['confirmado']) for a in aspectos] == [
        ('comando elétrico dos motores', True), ('parada elétrica', caso != 'sem_parada')]


@pytest.mark.parametrize('caso', ['parcial', 'zero', 'divergente', 'ultrapassou', 'sem_parada'])
def test_fala_imediata_conserva_partes_confirmadas_sem_anunciar_sucesso_total(caso, respostas_instaladas):
    c = respostas_instaladas['medidas_ocorrencias'][caso]
    assert len(c['textos_imediatos']) == 1, 'conclusão observável da ação deve chegar ao texto'
    fala = c['textos_imediatos'][0]
    assert 'Não consegui concluir' in fala
    assert 'Confirmação registrada de "comando elétrico dos motores"' in fala
    if caso == 'sem_parada':
        assert 'Sem confirmação de "parada elétrica"' in fala
    else:
        assert 'Confirmação registrada de "parada elétrica"' in fala
    assert c['publicacoes'][0]['confirmado'] is False


def resultado_parcial(*, intent='APP_OPEN', escopo='abertura da aplicação', confirmado=False, aspecto=True):
    a = AspectoResultado('operacao-1', escopo, aspecto, 'receipt_do_owner')
    status = 'resultado_confirmado' if confirmado is True else 'falha_execucao' if confirmado is False else 'resultado_incerto'
    return ResultadoAcao(intent=intent, status=status, alvo='alvo do pedido',
        origem='executor', executou=True, confirmado=confirmado,
        id_solicitacao='operacao-1', aspectos=(a,))


@pytest.mark.parametrize('intent,escopo', [('APP_OPEN', 'abertura da aplicação'),
    ('FILE_WRITE', 'leitura do conteúdo anterior'), ('IOT_CONTROL', 'envio ao dispositivo')])
@pytest.mark.parametrize('confirmado', [True, False, None])
@pytest.mark.parametrize('aspecto', [True, False, None])
def test_contrato_e_realizacao_compartilhados_preservam_as_duas_certezas(intent, escopo, confirmado, aspecto):
    r = resultado_parcial(intent=intent, escopo=escopo, confirmado=confirmado, aspecto=aspecto)
    p = planejar_resposta_acao(r, 'Tudo foi feito e confirmado.')
    assert p.fala == fala_resultado_por_aspectos(r)
    prefixo = 'Confirmação registrada de' if aspecto is True else 'Sem confirmação de' if aspecto is False else 'Confirmação desconhecida de'
    assert f'{prefixo} "{escopo}"' in p.fala
    assert r.confirmado is confirmado and r.aspectos[0].confirmado is aspecto
    assert fala_factual_resultados_compostos([r], informacoes={r.id_solicitacao: 'Tudo feito.'}) == p.fala
    with pytest.raises(FrozenInstanceError):
        r.aspectos[0].confirmado = True


@pytest.mark.parametrize('campo,valor', [('id_solicitacao', ''), ('escopo', ''),
    ('escopo', ' fonte'), ('escopo', 'duas\nlinhas'), ('evidencia', ''),
    ('confirmado', 1), ('confirmado', 'sim')])
def test_aspecto_recusa_dados_malformados(campo, valor):
    dados = asdict(resultado_parcial().aspectos[0]) | {campo: valor}
    with pytest.raises(ValueError):
        AspectoResultado(**dados)


@pytest.mark.parametrize('tipo', ['json', 'lista', 'outra_ocorrencia', 'duplicata', 'outra_origem'])
def test_receipt_recusa_aspectos_sem_captura_da_mesma_ocorrencia(tipo):
    r = resultado_parcial()
    a = r.aspectos[0]
    campos = {'aspectos': (a,)}
    if tipo == 'json': campos['aspectos'] = (asdict(a),)
    elif tipo == 'lista': campos['aspectos'] = [a]
    elif tipo == 'outra_ocorrencia': campos['aspectos'] = (replace(a, id_solicitacao='outra'),)
    elif tipo == 'duplicata': campos['aspectos'] = (a, a)
    else: campos['origem'] = 'llm'
    with pytest.raises(ValueError):
        replace(r, **campos)


def test_serializacao_nao_reidrata_proposta_ou_alegacao_como_aspecto_observado():
    r = resultado_parcial()
    bruto = json.loads(json.dumps(r.como_dict()))
    assert bruto['aspectos'][0]['confirmado'] is True
    assert not normalizar_resultado_acao(bruto).aspectos
    assert not identificar_solicitacao_execucao(bruto, nova_identidade=True).get('aspectos')
    assert normalizar_resultado_acao(r).aspectos == r.aspectos


def test_porta_final_tipado_conserva_aspectos_quando_recebe_outro_texto():
    from scripts.tests.test_vinculo_fala_resultado import runtime_audio
    runtime, _, _ = runtime_audio()
    textos = []
    runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto) or True)
    r = resultado_parcial()
    runtime.falar_resultado_operacional(r, 'Não consegui fazer nada; não confirmei a abertura.')
    assert textos == [fala_resultado_por_aspectos(r)]


def test_composto_recusa_acrescimo_ao_aspecto_mesmo_com_literal_preservado():
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    r = resultado_parcial()
    segura = fala_resultado_por_aspectos(r)
    alterada = segura + ' Isso aconteceu porque você não configurou direito.'
    resposta = personalizar_confirmacao_composta_llm([r], segura,
        informacoes={r.id_solicitacao: segura},
        enviar_mensagem=lambda *_a, **_k: json.dumps({'fala': alterada, 'trechos': [alterada]}))
    assert resposta.fala == segura and not resposta.usada_llm


@pytest.mark.parametrize('modo', ['fiel', 'causa_inventada', 'sucesso_total'])
def test_cadeia_instalada_preserva_aspectos_e_falha_parcial_em_publicacao_unica(modo, respostas_instaladas):
    c = respostas_instaladas['compostos_aspectos'][modo]
    assert c['tratado'] and c['leituras_janela']
    resultados = c['plano']['comandos']
    assert [r['intent'] for r in resultados] == ['APP_OPEN', 'CORPO_MOVER']
    assert [r['confirmado'] for r in resultados] == [True, False]
    assert len({r['id_solicitacao'] for r in resultados}) == 2
    assert resultados[-1]['status'] == 'falha_execucao', 'alcançar o receipt de giro, não uma recusa anterior'
    assert c['novos_giros'] == 1
    # O plano é projeção compacta; a autoria deve receber o receipt tipado inteiro.
    assert c['autorias'][-1]['resultados'][-1]['informacao_literal']
    assert len(c['textos']) == 1
    fala = c['textos'][0]
    assert 'Não consegui concluir' in fala and 'Confirmação registrada de "parada elétrica"' in fala
    assert 'não configurou' not in fala and 'Concluí o giro' not in fala
    assert c['autorias'], 'composição deve alcançar autoria instalada antes de conferir seus trechos'


@pytest.mark.parametrize('canal', ['status', 'direto'])
@pytest.mark.parametrize('publicacao', ['aceita', 'recusada', 'outra_ocorrencia', 'nova_tentativa'])
def test_adaptador_so_verbaliza_aspectos_da_publicacao_atual_aceita(canal, publicacao):
    from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
    textos, chamadas_modelo = [], []
    r = resultado_parcial()
    pedido = {'intent': r.intent, 'id_solicitacao': r.id_solicitacao}
    ctx = {'_registrar_resultado_execucao': lambda *_a, **_k: publicacao != 'recusada',
        'falar_com_lipsync': lambda texto, *_a, **_k: textos.append(texto) or True,
        'enviar_mensagem': lambda *_a, **_k: chamadas_modelo.append(True) or '', 'print': lambda *_a: None}
    a = AdaptadorResultadoOperacional(pedido, {}, 'abre o aplicativo', 'pc_a', ctx)
    a.marcar_resultado(r.status, executou=True, confirmado=False, alvo_resolvido=r.alvo, aspectos=r.aspectos)
    if publicacao == 'outra_ocorrencia': pedido['id_solicitacao'] = 'outra'
    elif publicacao == 'nova_tentativa':
        a.marcar_resultado(r.status, executou=True, confirmado=False, alvo_resolvido=r.alvo)
    if canal == 'status':
        a.falar_por_status(r.status, 'Não consegui confirmar nada.', alvo=r.alvo)
    else:
        a.falar_texto_da_invocacao('Não consegui confirmar nada.')
    assert textos
    if publicacao == 'aceita':
        assert textos == [fala_resultado_por_aspectos(r)] and not chamadas_modelo
    else:
        assert not any('Confirmação registrada de' in t for t in textos)


def test_cancelar_nao_apaga_aspecto_confirmado_anterior():
    r = replace(resultado_parcial(), status='cancelado')
    fala = fala_resultado_por_aspectos(r)
    assert 'foi cancelado' in fala and 'Confirmação registrada de' in fala
    assert 'não mexi' not in fala
