"""Meta original e comparação acompanham somente as fontes da invocação."""
import os
from pathlib import Path

import pytest


@pytest.fixture(scope='module')
def comparacoes_imediatas_instaladas(tmp_path_factory):
    from scripts.tests.test_aspectos_resultado_imediato import respostas_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_EXPECTATIVAS_OCORRENCIA', '1')
        ambiente.setenv('LAYLAY_COLETAR_COMPARACAO_IMEDIATA', '1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_COMPARACAO_IMEDIATA'):
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO', str(Path(pasta) / 'composicao.json'))
        return respostas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,meta,diferenca', [('meta90',90,'-66.25'), ('meta180',180,'-156.25'),
    ('meta_direita',-90,'113.75'), ('sem_leitura',45,None), ('erro_executor',90,None)])
def test_meta_previa_atravessa_publicacao_e_resposta_imediata(nome,meta,diferenca,comparacoes_imediatas_instaladas):
    dados = comparacoes_imediatas_instaladas
    assert all(dados['owners'].values())
    c = dados['medidas_ocorrencias'][nome]
    inicio = c['inicio_ocorrencia']['ocorrencia']
    fonte, = inicio['expectativas']
    assert fonte['valor'] == meta and c['experiencia']['expectativas'] == inicio['expectativas']
    r, = c['publicacoes']
    metas = r.get('expectativas', [])
    assert len(metas) == 1, 'primeira perda: captura prévia existe, mas não atravessa publicação do executor'
    assert metas[0]['valor'] == meta and metas[0]['ocorrencia_id'] == r['id_solicitacao']
    assert metas[0]['registrada_em'] == fonte['registrada_em'] and metas[0]['fonte'] == fonte['fonte']
    fala, = c['textos_imediatos']
    assert f'{meta} "graus"' in fala and 'A meta registrada não comprova' in fala
    assert r['confirmado'] is False and c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    if diferenca is not None:
        assert f'Diferença aritmética (medido menos solicitado): {diferenca} "graus"' in fala
        assert 'Esta diferença não comprova conclusão nem explica a causa do resultado.' in fala
    else:
        assert 'Não há medição qualificada nesta fonte para comparar com o valor solicitado.' in fala
        assert 'Diferença aritmética' not in fala


def test_pulso_imediato_nao_inventa_meta_angular(comparacoes_imediatas_instaladas):
    c = comparacoes_imediatas_instaladas['medidas_ocorrencias']['pulso']
    assert not c['inicio_ocorrencia']['ocorrencia'].get('expectativas')
    assert not c['publicacoes'][0].get('expectativas')
    assert 'Valor solicitado' not in c['textos_imediatos'][0] and 'Diferença aritmética' not in c['textos_imediatos'][0]


def test_composto_fiel_recebe_meta_e_comparacao_antes_da_autoria(comparacoes_imediatas_instaladas):
    c = comparacoes_imediatas_instaladas['compostos_aspectos']['TEMPO_LIMITE:fiel']
    assert c['tratado'] and c['novos_giros'] == 1 and len(c['textos']) == 1
    linhas = c['autorias'][-1]['resultados']
    assert len(linhas) == 2 and linhas[0]['id_solicitacao'] != linhas[1]['id_solicitacao']
    fato = linhas[1]['fato_verificado']
    assert 'Valor solicitado de' in fato, 'fonte entregue à autoria já omite meta e comparação'
    assert '-66.25 "graus"' in fato and 'Esta diferença não comprova conclusão' in fato
    assert linhas[1]['informacao_literal'] in c['textos'][0]
    assert c['geracoes'][-1]['fala'] == c['textos'][0]


@pytest.mark.parametrize('nome,valor,diferenca,confirmado', [('igual',90.0,'0',True),
    ('zero',0.0,'-90.0',False), ('divergente',-17.25,'-107.25',False), ('ultrapassou',110.5,'20.5',False)])
def test_comparacao_instalada_preserva_sinal_zero_e_confirmacao(nome,valor,diferenca,confirmado,comparacoes_imediatas_instaladas):
    c = comparacoes_imediatas_instaladas['medidas_ocorrencias'][nome]
    r, = c['publicacoes']
    assert r['expectativas'][0]['valor'] == 90 and r['medicoes'][0]['valor'] == valor
    assert r['confirmado'] is confirmado
    assert f'medido menos solicitado): {diferenca} "graus"' in c['textos_imediatos'][0]
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']


MODOS_COMPOSTOS = [('TEMPO_LIMITE', modo) for modo in ('meta_trocada', 'diferenca_trocada',
    'sinal_diferenca', 'diferenca_sem_limite', 'comparacao_omitida', 'causa_inventada', 'sucesso_total')]
MODOS_COMPOSTOS += [('IMU_OU_SESSAO', modo) for modo in ('fiel', 'meta_trocada', 'comparacao_inventada',
    'limite_indisponibilidade_omitido', 'causa_inventada', 'sucesso_total')]
MODOS_COMPOSTOS += [('ERRO_EXECUTOR', modo) for modo in ('fiel', 'meta_trocada', 'comparacao_inventada',
    'limite_indisponibilidade_omitido', 'causa_inventada', 'sucesso_total')]


@pytest.mark.parametrize('codigo,modo', MODOS_COMPOSTOS)
def test_composto_instalado_recusa_meta_ou_derivacao_da_proposta(codigo,modo,comparacoes_imediatas_instaladas):
    c = comparacoes_imediatas_instaladas['compostos_aspectos'][codigo + ':' + modo]
    assert c['tratado'] and c['novos_giros'] == (0 if codigo == 'ERRO_EXECUTOR' else 1) and len(c['textos']) == 1
    assert c['falhas_folha'] == (1 if codigo == 'ERRO_EXECUTOR' else 0)
    rs = c['plano']['comandos']
    assert len(rs) == 2 and rs[0]['confirmado'] is True and rs[1]['confirmado'] is False
    assert rs[0]['id_solicitacao'] != rs[1]['id_solicitacao']
    literal = c['autorias'][-1]['resultados'][1]['informacao_literal']
    fala, = c['textos']
    assert literal in fala and '90 "graus"' in fala
    if codigo == 'TEMPO_LIMITE': assert '-66.25 "graus"' in fala and 'Esta diferença não comprova conclusão' in fala
    else:
        assert 'Diferença aritmética' not in fala
        assert 'Não há medição qualificada nesta fonte para comparar com o valor solicitado.' in fala
    bruto = c['geracoes'][-1]['fala']
    assert (bruto == fala) is (modo == 'fiel'), 'adversarial precisa alterar a proposta antes da revisão'
    if modo == 'meta_trocada': assert '180 "graus"' in bruto
    elif modo == 'diferenca_trocada': assert '-156.25' in bruto
    elif modo == 'sinal_diferenca': assert '): 66.25' in bruto
    elif modo == 'diferenca_sem_limite': assert 'Esta diferença não comprova' not in bruto
    elif modo == 'comparacao_omitida': assert 'Diferença aritmética' not in bruto
    elif modo == 'comparacao_inventada': assert 'Diferença aritmética' in bruto
    elif modo == 'limite_indisponibilidade_omitido': assert 'Não há medição qualificada nesta fonte para comparar' not in bruto


from dataclasses import asdict, replace
import json
from mente_laylay.memoria_mental.decisao_observada import FontesComparacaoResultado, avaliar_comparacoes_resultado
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, normalizar_resultado_acao, identificar_solicitacao_execucao
from mente_laylay.personalidade.planejador_resposta import fala_resultado_por_aspectos, planejar_resposta_acao, fala_factual_resultados_compostos


def resultado_comparavel(**campos):
    from scripts.tests.test_comparacao_resultado import episodio_comparavel
    e = episodio_comparavel(**campos)
    return ResultadoAcao(intent='CORPO_MOVER', status='falha_execucao', origem='executor',
        id_solicitacao=e.id, alvo='alvo observado', executou=True, confirmado=e.confirmado,
        expectativas=e.expectativas, medicoes=e.medicoes, inicio_execucao=e.iniciada_em)


@pytest.mark.parametrize('intent,owner,grandeza,unidade', [('CORPO_MOVER','executor_corpo','rotação relativa','graus'),
    ('FILE_WRITE','executor_arquivos','tamanho solicitado','bytes'), ('VOLUME','executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('confirmado', [True,False,None])
def test_meta_e_diferenca_compartilhadas_nao_redefinem_conclusao(intent,owner,grandeza,unidade,confirmado):
    r = replace(resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade,confirmado=confirmado), intent=intent)
    fala = fala_resultado_por_aspectos(r)
    assert '90' in fala and '-66.25' in fala and grandeza in fala and unidade in fala
    assert 'Esta diferença não comprova conclusão nem explica a causa do resultado.' in fala
    assert planejar_resposta_acao(r,'Concluí tudo.').fala == fala
    assert fala_factual_resultados_compostos([r],informacoes={r.id_solicitacao:'Feito.'}) == fala
    assert r.confirmado is confirmado and r.expectativas[0].autoriza_execucao is False


@pytest.mark.parametrize('owner,grandeza,unidade', [('executor_corpo','rotação relativa','graus'),
    ('executor_arquivos','tamanho solicitado','bytes'), ('executor_volume','volume configurado','percentual')])
@pytest.mark.parametrize('nome', ['sem_meta','sem_medicao','grandeza_distinta','unidade_distinta',
    'sem_referencial','referencial_medicao','referencial_distinto','ambigua','outro_owner'])
def test_imediata_declara_premissa_ausente_sem_calculo_da_ia(nome,owner,grandeza,unidade):
    from scripts.tests.test_limites_comparacao import cenario, FALAS
    e = cenario(nome,owner=owner,grandeza=grandeza,unidade=unidade)
    if nome == 'outro_owner': e = replace(e, medicoes=())  # O episódio histórico exige owner único.
    r = replace(resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade),
        expectativas=e.expectativas, medicoes=e.medicoes)
    if nome == 'outro_owner':
        original = resultado_comparavel(owner=owner,grandeza=grandeza,unidade=unidade)
        r = replace(r, medicoes=(replace(original.medicoes[0],owner='outro_owner'),))
    a, = avaliar_comparacoes_resultado(FontesComparacaoResultado(r.id_solicitacao,r.expectativas,r.medicoes,r.inicio_execucao))
    fala = fala_resultado_por_aspectos(r)
    assert a.comparacao is None and 'Diferença aritmética' not in fala
    assert (FALAS[nome] if nome != 'outro_owner' else 'Não há medição do mesmo owner da meta para comparação.') in fala
    assert r.confirmado is False and not a.autoriza_execucao and not a.confirma_efeito


@pytest.mark.parametrize('tipo', ['json','lista','outra_ocorrencia','posterior','duplicada','excesso',
    'outra_origem','sem_inicio','inicio_invalido','id_vazio'])
def test_resultado_exige_meta_tipificada_da_execucao_anterior_ao_efeito(tipo):
    r = resultado_comparavel(); e = r.expectativas[0]; campos = {}
    if tipo == 'json': campos['expectativas'] = (asdict(e),)
    elif tipo == 'lista': campos['expectativas'] = [e]
    elif tipo == 'outra_ocorrencia': campos['expectativas'] = (replace(e,ocorrencia_id='outra'),)
    elif tipo == 'posterior': campos['expectativas'] = (replace(e,registrada_em=r.inicio_execucao+1),)
    elif tipo == 'duplicada': campos['expectativas'] = (e,e)
    elif tipo == 'excesso': campos['expectativas'] = tuple(replace(e,grandeza=f'meta{i}') for i in range(9))
    elif tipo == 'outra_origem': campos['origem'] = 'llm'
    elif tipo == 'sem_inicio': campos['inicio_execucao'] = None
    elif tipo == 'inicio_invalido': campos['inicio_execucao'] = float('nan')
    elif tipo == 'id_vazio': campos['id_solicitacao'] = ''
    with pytest.raises(ValueError): replace(r,**campos)


def test_json_e_nova_proposta_nao_recriam_meta_nem_comparacao():
    r = resultado_comparavel(); bruto = json.loads(json.dumps(r.como_dict()))
    assert bruto['expectativas'][0]['valor'] == 90
    assert 'comparacao' not in bruto and 'diferenca' not in bruto
    assert not normalizar_resultado_acao(bruto).expectativas
    novo = identificar_solicitacao_execucao(bruto,nova_identidade=True)
    assert 'expectativas' not in novo and 'inicio_execucao' not in novo
    assert normalizar_resultado_acao(r).expectativas == r.expectativas
    assert not avaliar_comparacoes_resultado(asdict(FontesComparacaoResultado(r.id_solicitacao,r.expectativas,r.medicoes,r.inicio_execucao)))


@pytest.mark.parametrize('canal', ['status','direto'])
@pytest.mark.parametrize('publicacao', ['aceita','recusada','outra_ocorrencia','nova_tentativa'])
def test_adaptador_nao_empresta_meta_ou_derivacao_de_publicacao_anterior(canal,publicacao):
    from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
    r = replace(resultado_comparavel(),medicoes=())
    textos = []; pedido = {'intent':r.intent,'id_solicitacao':r.id_solicitacao}
    ctx = {'_registrar_resultado_execucao':lambda *_a,**_k:publicacao!='recusada',
        'falar_com_lipsync':lambda t,*_a,**_k:textos.append(t) or True, 'print':lambda *_a:None}
    a = AdaptadorResultadoOperacional(pedido,{},'pedido autorizado','pc_a',ctx)
    a.marcar_resultado(r.status,executou=True,confirmado=False,alvo_resolvido=r.alvo,
        expectativas=r.expectativas,inicio_execucao=r.inicio_execucao)
    if publicacao == 'outra_ocorrencia': pedido['id_solicitacao'] = 'outra'
    elif publicacao == 'nova_tentativa': a.marcar_resultado(r.status,executou=True,confirmado=False,alvo_resolvido=r.alvo)
    if canal == 'status': a.falar_por_status(r.status,'Concluí tudo.',alvo=r.alvo)
    else: a.falar_texto_da_invocacao('Concluí tudo.')
    assert textos
    if publicacao == 'aceita': assert textos == [fala_resultado_por_aspectos(r)]
    else: assert not any('Valor solicitado de' in t for t in textos)


def test_porta_final_conserva_meta_sozinha_sem_inferir_efeito():
    from scripts.tests.test_vinculo_fala_resultado import runtime_audio
    runtime,_,_ = runtime_audio(); textos = []
    runtime.registrar_observador_texto_final(lambda t,*_a,**_k:textos.append(t) or True)
    r = replace(resultado_comparavel(),medicoes=())
    runtime.falar_resultado_operacional(r,'Concluí os 90 graus porque o motor funciona bem.')
    assert textos == [fala_resultado_por_aspectos(r)]


@pytest.mark.parametrize('modo', ['fiel','meta','diferenca','sinal','limite','causa','omissao'])
def test_revisao_composta_usa_derivacao_compartilhada_em_vez_de_calculo_proposto(modo,monkeypatch):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    monkeypatch.setenv('LAYLAY_CONFIRMACOES_LLM','1')
    r = resultado_comparavel(); segura = fala_resultado_por_aspectos(r); alterada = segura
    if modo == 'meta': alterada = segura.replace('90 "graus"','180 "graus"')
    elif modo == 'diferenca': alterada = segura.replace('-66.25','-156.25')
    elif modo == 'sinal': alterada = segura.replace('-66.25','66.25')
    elif modo == 'limite': alterada = segura.replace('Esta diferença não comprova conclusão nem explica a causa do resultado.','')
    elif modo == 'causa': alterada = segura + ' Isso aconteceu porque o motor travou.'
    elif modo == 'omissao': alterada = 'Não consegui concluir o pedido.'
    chamadas = []
    def modelo(mensagens,**_k):
        chamadas.append(json.loads(mensagens[1]['content']))
        return json.dumps({'fala':alterada,'trechos':[alterada]})
    resposta = personalizar_confirmacao_composta_llm([r],segura,enviar_mensagem=modelo)
    assert chamadas[0]['resultados'][0]['informacao_literal'] == segura
    assert resposta.fala == segura and resposta.usada_llm is (modo == 'fiel')


@pytest.mark.parametrize('modo', ['retorno_trocado','captura_alterada_depois','envelope_transportado'])
def test_retorno_de_execucao_conserva_captura_previa_em_vez_de_reconstruir_meta(modo):
    from types import SimpleNamespace
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    corpo = CorpoMotorRuntime(transporte=SimpleNamespace(diagnostico=lambda:{}))
    ocorrencia = corpo.experiencias.iniciar(nome='giro',origem_intencao='pedido_usuario',perfil='bancada',angulo_solicitado_graus=90)
    def efeito():
        if modo == 'captura_alterada_depois': ocorrencia['expectativas'][0]['valor'] = 999
        return {'ok':False,'angulo_solicitado_graus':180,'_fontes_resultado':{'expectativas':[{'valor':999}]}}
    r = corpo._executar_manual_observado(ocorrencia,'CORPO_MOVER',efeito)
    fontes = r['_fontes_resultado']
    assert type(fontes) is FontesComparacaoResultado and fontes.expectativas[0].valor == 90
    assert fontes.expectativas[0].registrada_em <= fontes.iniciada_em


@pytest.mark.parametrize('fonte', ['ausente','json','excecao'])
def test_executor_nao_reconstroi_meta_pelo_pedido_receipt_ou_json(fonte):
    from types import SimpleNamespace
    from mente_laylay.autonomia.executor_corpo import executar_intencao_corpo, DependenciasExecutorCorpo
    from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    r = resultado_comparavel(); publicados, tentativas = [], []
    bruto = {'ok':False,'angulo_solicitado_graus':180,'rotacao_medida_graus':23.75,
        'leitura_rotacao_valida':True,'evidencia_leitura_rotacao':'turnend_correlacionado_imu_valida'}
    if fonte == 'json': bruto['_fontes_resultado'] = asdict(FontesComparacaoResultado(r.id_solicitacao,r.expectativas,r.medicoes,r.inicio_execucao))
    def executar(*_a):
        tentativas.append(True)
        if fonte == 'excecao': raise OSError('falha controlada')
        return bruto
    texto = 'gire 90 graus para a esquerda'; pedido = detectar_intencao_corpo(texto)
    executar_intencao_corpo(pedido['intent'],pedido['params'],texto,
        {'turno_atual':classificar_modalidade_turno(texto),'_corpo_motor_runtime':SimpleNamespace(executar=executar)},
        DependenciasExecutorCorpo(lambda s,**k:publicados.append(k),lambda *_a,**_k:None,'pedido-atual'))
    assert len(tentativas) == len(publicados) == 1
    assert not publicados[0]['expectativas'] and publicados[0]['inicio_execucao'] is None
    assert '_fontes_resultado' not in publicados[0]['contexto_resultado']['receipt_corpo']


@pytest.mark.parametrize('tipo', ['excecao_original','fonte_de_outra_execucao'])
def test_falha_preserva_fonte_local_e_causa_original_sem_receipt_falso(tipo):
    from types import SimpleNamespace
    from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
    from mente_laylay.memoria_mental.decisao_observada import FalhaExecucaoComFontes
    corpo = CorpoMotorRuntime(transporte=SimpleNamespace(diagnostico=lambda:{}))
    ocorrencia = corpo.experiencias.iniciar(nome='giro',origem_intencao='pedido_usuario',perfil='bancada',angulo_solicitado_graus=90)
    if tipo == 'excecao_original': original = OSError('folha controlada')
    else:
        r = resultado_comparavel()
        original = FalhaExecucaoComFontes(FontesComparacaoResultado(r.id_solicitacao,
            (replace(r.expectativas[0],valor=999),),iniciada_em=r.inicio_execucao))
    def efeito(): raise original
    with pytest.raises(FalhaExecucaoComFontes) as captura:
        corpo._executar_manual_observado(ocorrencia,'CORPO_MOVER',efeito)
    erro = captura.value
    assert erro.__cause__ is original
    assert erro.fontes.id == ocorrencia['id'] and erro.fontes.expectativas[0].valor == 90
    assert not erro.fontes.medicoes and not erro.fontes.confirma_efeito and not erro.fontes.autoriza_execucao
    with pytest.raises(ValueError): FalhaExecucaoComFontes(asdict(erro.fontes))
