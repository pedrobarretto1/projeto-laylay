"""Critério observado de qualificação não é um diagnóstico físico."""
import os
from copy import deepcopy
from dataclasses import asdict, replace, FrozenInstanceError
from pathlib import Path

import pytest

from scripts.tests.test_leituras_parciais_corpo import EspLeituraParcial, parciais_instaladas
from scripts.tests.test_companhia_corporal import montar
from mente_laylay.memoria_mental.decisao_observada import NaoQualificacaoMedicao, ExplicacaoOcorrencia, comparacoes_resultado
from mente_laylay.memoria_mental.experiencia_corporal_runtime import nao_qualificacoes_rotacao_observadas
from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia, avaliar_fala_historica


@pytest.fixture(scope='module')
def qualificacoes_instaladas(tmp_path_factory):
    with pytest.MonkeyPatch.context() as ambiente:
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_EXPECTATIVAS'):
            destino = Path(pasta) / 'qualificacao'
            destino.mkdir(parents=True, exist_ok=True)
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO', str(destino / 'composicao.json'))
        return parciais_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('codigo', ['IMU_OU_SESSAO', 'SATURACAO', 'PROTECAO', 'INTERROMPIDO'])
def test_transporte_publica_criterio_de_nao_qualificacao_sem_reinterpretar_codigo(codigo):
    _, _, rosto, _, _, _ = montar(esp=EspLeituraParcial(resultado=codigo))
    try:
        r = rosto.girar_corpo(90)
        assert r['rotacao_medida_graus'] == 23.75 and r['leitura_rotacao_valida'] is False
        observado = r.get('nao_qualificacao_rotacao')
        assert observado, 'primeira perda: owner decide validade, mas não publica o critério observado'
        assert observado['criterio'] == 'criterio_da_fonte_nao_atendido' and observado['codigo'] == codigo
        assert observado['fonte'] == 'qualificacao_turnend_owner_usb_v1'
    finally:
        rosto.encerrar()


@pytest.mark.parametrize('nome,codigo', [('imu_invalida', 'IMU_OU_SESSAO'), ('saturacao', 'SATURACAO'),
    ('protecao', 'PROTECAO'), ('interrompido', 'INTERROMPIDO'), ('outra_sequencia', '')])
def test_criterio_atual_atravessa_receipt_historico_aprendizado_fonte_e_entrega(nome, codigo, qualificacoes_instaladas):
    assert all(qualificacoes_instaladas['owners'].values())
    c = qualificacoes_instaladas['medidas_ocorrencias'][nome]
    r = c['publicacoes'][0]['contexto']['receipt_corpo']
    assert r['leitura_rotacao_valida'] is False
    fonte_receipt = r.get('nao_qualificacao_rotacao')
    assert fonte_receipt, 'primeira perda na composição: receipt não publica a decisão de qualificação'
    assert fonte_receipt['codigo'] == codigo
    capturadas = c['experiencia'].get('nao_qualificacoes_medicao', [])
    assert len(capturadas) == 1
    assert capturadas[0]['ocorrencia_id'] == c['experiencia']['id']
    assert capturadas[0]['criterio'] == fonte_receipt['criterio'] and capturadas[0]['codigo'] == codigo
    e = c['fonte']['episodios'][0]
    assert e['nao_qualificacoes_medicao'] == capturadas and not e['medicoes']
    aprendidos = [evento['contexto']['experiencia'] for evento in c['eventos_aprendizado']
        if evento.get('contexto', {}).get('experiencia', {}).get('id') == e['id']]
    assert aprendidos and all(item['nao_qualificacoes_medicao'] == capturadas for item in aprendidos)
    assert 'não identifica uma causa física' in c['fala_owner']
    if codigo: assert f'código "{codigo}"' in c['fala_owner']
    else: assert 'Não há encerramento correlacionado admitido' in c['fala_owner']
    assert e['confirmado'] is False and c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    for t in c['turnos']:
        assert t['codec_integral'] and t['contexto_fechado'] and t['textos'] == [c['fala_owner']] and not t['executores']


@pytest.mark.parametrize('nome', ['parcial', 'zero', 'sem_parada'])
def test_leitura_qualificada_nao_herda_rejeicao_do_objetivo_ou_da_parada(nome, qualificacoes_instaladas):
    c = qualificacoes_instaladas['medidas_ocorrencias'][nome]
    e = c['fonte']['episodios'][0]
    assert e['medicoes'] and e['confirmado'] is False
    assert not e.get('nao_qualificacoes_medicao')
    assert 'Critério registrado de não qualificação' not in c['fala_owner']


@pytest.mark.parametrize('resultado,correlacao', [('AUSENTE', 'atual'), ('SATURACAO', 'outra_sessao'), ('PROTECAO', 'outra_sequencia')])
def test_sem_encerramento_admitido_nao_empresta_codigo_de_outro_pacote(resultado, correlacao):
    _, _, rosto, _, _, _ = montar(esp=EspLeituraParcial(resultado=resultado, correlacao=correlacao))
    try:
        r = rosto.girar_corpo(90)
        assert r['rotacao_medida_graus'] is None and r['leitura_rotacao_valida'] is False
        assert r['nao_qualificacao_rotacao']['criterio'] == 'fonte_nao_correlacionada'
        assert r['nao_qualificacao_rotacao']['codigo'] == ''
    finally:
        rosto.encerrar()


def observacao(e, **alteracoes):
    campos = dict(ocorrencia_id=e.id, owner=e.owner, grandeza='rotação relativa', unidade='graus',
        criterio='criterio_da_fonte_nao_atendido', fonte='fonte_qualificada_do_owner', codigo='SATURACAO')
    return NaoQualificacaoMedicao(**(campos | alteracoes))


def realizar(e):
    return realizacoes_explicacao_ocorrencia(ExplicacaoOcorrencia('c', 'Por que fez essa ação?', (e,), 'unica'))[0]


@pytest.mark.parametrize('owner,grandeza,unidade,codigo', [('executor_corpo', 'rotação relativa', 'graus', 'IMU_OU_SESSAO'),
    ('executor_arquivos', 'tamanho verificado', 'bytes', 'CHECKSUM_DIVERGENTE'), ('executor_volume', 'volume lido', 'percentual', 'SEM_RETORNO')])
@pytest.mark.parametrize('criterio', ['fonte_nao_correlacionada', 'contexto_alterado', 'valor_nao_admitido', 'criterio_da_fonte_nao_atendido'])
def test_tipo_e_realizador_compartilhados_relatam_criterio_sem_conceder_efeito(owner, grandeza, unidade, codigo, criterio):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e = episodio(owner=owner, confirmado=False)
    n = observacao(e, grandeza=grandeza, unidade=unidade, criterio=criterio,
        codigo=codigo if criterio == 'criterio_da_fonte_nao_atendido' else '')
    e = replace(e, nao_qualificacoes_medicao=(n,))
    antes = deepcopy(e)
    fala = realizar(e)
    assert grandeza in fala and 'não identifica uma causa física' in fala
    if n.codigo: assert f'código "{codigo}"' in fala
    assert not e.medicoes and not comparacoes_resultado(e) and e.confirmado is False
    assert not n.autoriza_execucao and not n.confirma_efeito and e == antes
    with pytest.raises(FrozenInstanceError): n.codigo = 'ALVO'


@pytest.mark.parametrize('alteracao', [{'ocorrencia_id': ''}, {'owner': ''}, {'grandeza': ''}, {'unidade': ''},
    {'fonte': ''}, {'criterio': 'causa_inventada'}, {'criterio': []}, {'codigo': []}, {'codigo': ' x'}, {'codigo': 'x' * 81}])
def test_nao_qualificacao_recusa_estrutura_sem_fonte_explicita(alteracao):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    with pytest.raises(ValueError): observacao(episodio(), **alteracao)


@pytest.mark.parametrize('tipo', ['json', 'lista', 'outro_id', 'outro_owner', 'duplicada', 'excesso'])
def test_episodio_nao_admite_observacao_de_outra_fonte_ou_duplicada(tipo):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e = episodio(); n = observacao(e); fontes = (n,)
    if tipo == 'json': fontes = (asdict(n),)
    if tipo == 'lista': fontes = [n]
    if tipo == 'outro_id': fontes = (replace(n, ocorrencia_id='outra'),)
    if tipo == 'outro_owner': fontes = (replace(n, owner='outro'),)
    if tipo == 'duplicada': fontes = (n, n)
    if tipo == 'excesso': fontes = tuple(replace(n, grandeza=f'g{i}') for i in range(9))
    with pytest.raises(ValueError): replace(e, nao_qualificacoes_medicao=fontes)


def retorno_nao_qualificado(codigo='IMU_OU_SESSAO'):
    return {'ok': False, 'angulo_solicitado_graus': 90, 'rotacao_medida_graus': 23.75,
        'leitura_rotacao_valida': False, 'prova_rotacao': False,
        'nao_qualificacao_rotacao': {'fonte': 'qualificacao_turnend_owner_usb_v1',
            'criterio': 'criterio_da_fonte_nao_atendido', 'codigo': codigo,
            'autoriza_execucao': False, 'confirma_efeito': False}}


@pytest.mark.parametrize('campo,valor', [('fonte', 'proposta_ia'), ('criterio', 'causa_inventada'), ('criterio', []),
    ('codigo', []), ('codigo', 'ALVO'), ('codigo', 'TRAVOU'), ('autoriza_execucao', True), ('confirma_efeito', True)])
def test_adaptador_do_owner_nao_reinterpreta_metadados_invalidados(campo, valor):
    r = retorno_nao_qualificado()
    r['nao_qualificacao_rotacao'][campo] = valor
    assert not nao_qualificacoes_rotacao_observadas(r, ocorrencia_id='atual')


@pytest.mark.parametrize('campo,valor', [('ocorrencia_id', 'outra'), ('owner', 'outro'),
    ('grandeza', 'outra grandeza'), ('unidade', 'outra unidade')])
def test_adaptador_nao_reatribui_identidade_explicita_de_outra_observacao(campo, valor):
    r = retorno_nao_qualificado()
    r['nao_qualificacao_rotacao'][campo] = valor
    assert not nao_qualificacoes_rotacao_observadas(r, ocorrencia_id='atual')


@pytest.mark.parametrize('criterio', ['fonte_nao_correlacionada', 'contexto_alterado', 'valor_nao_admitido'])
def test_criterio_sem_correlacao_ou_contexto_nao_ganha_codigo_de_outro_retorno(criterio):
    r = retorno_nao_qualificado()
    r['nao_qualificacao_rotacao'].update(criterio=criterio, codigo='')
    n, = nao_qualificacoes_rotacao_observadas(r, ocorrencia_id='atual')
    assert n.criterio == criterio and n.codigo == ''
    r['nao_qualificacao_rotacao']['codigo'] = 'SATURACAO'
    assert not nao_qualificacoes_rotacao_observadas(r, ocorrencia_id='atual')


@pytest.mark.parametrize('mudanca', ['validade', 'prova', 'medicao', 'legado'])
def test_retorno_valido_ou_legado_nao_inventa_criterio_pelo_codigo_solto(mudanca):
    r = retorno_nao_qualificado()
    if mudanca == 'validade': r['leitura_rotacao_valida'] = True
    if mudanca == 'prova': r['prova_rotacao'] = True
    if mudanca == 'medicao': r.update(ok=True, prova_rotacao=True, evidencia='imu_relativa_turnend_e_sack')
    if mudanca == 'legado':
        r.pop('nao_qualificacao_rotacao')
        r.update(resultado_giro='IMU_OU_SESSAO', motivo='sensor falhou', status='falha_execucao')
    assert not nao_qualificacoes_rotacao_observadas(r, ocorrencia_id='atual')


def experiencia_com_criterio():
    from scripts.tests.test_decisao_observada import experiencia
    estado, runtime = experiencia()
    inicio = runtime.iniciar(nome='giro', origem_intencao='pedido_usuario', perfil='bancada', angulo_solicitado_graus=90)
    registro = runtime.registrar(inicio, retorno_nao_qualificado(), [{'ok': False, 'parada_confirmada': True, 'aplicacao_pwm_confirmada': True}])
    return estado, runtime, registro


@pytest.mark.parametrize('campo,valor', [('ocorrencia_id', 'outra'), ('owner', 'outro'), ('grandeza', 'posição'),
    ('unidade', 'metros'), ('fonte', 'proposta_ia'), ('codigo', 'ALVO'), ('criterio', []),
    ('autoriza_execucao', True), ('confirma_efeito', True)])
def test_historico_invalido_perde_somente_o_criterio_sem_apagar_tentativa_ou_meta(campo, valor):
    estado, runtime, registro = experiencia_com_criterio()
    historico = estado.obter_copia('mental', 'historico_corporal', [])
    historico[0]['nao_qualificacoes_medicao'][0][campo] = valor
    estado.atualizar_campos('mental', historico_corporal=historico)
    antes = estado.retrato_dominio('mental')
    f = runtime.recuperar_explicacao(f"Por que fez esse gesto {registro['id']}?", turno={'id': 'consulta'})
    assert f.episodios and not f.episodios[0].nao_qualificacoes_medicao
    assert f.episodios[0].expectativas[0].valor == 90 and f.episodios[0].confirmado is False
    assert estado.retrato_dominio('mental') == antes


@pytest.mark.parametrize('alteracao', ['duplicada', 'outra_decisao', 'nao_lista', 'legado', 'contradicao'])
def test_fonte_ambigua_ou_ausente_nao_e_completada_pelo_estado_vivo(alteracao):
    estado, runtime, registro = experiencia_com_criterio()
    historico = estado.obter_copia('mental', 'historico_corporal', [])
    fontes = historico[0]['nao_qualificacoes_medicao']
    if alteracao == 'duplicada': fontes.append(deepcopy(fontes[0]))
    if alteracao == 'outra_decisao': fontes.append(fontes[0] | {'codigo': 'SATURACAO'})
    if alteracao == 'nao_lista': historico[0]['nao_qualificacoes_medicao'] = {}
    if alteracao == 'legado': historico[0].pop('nao_qualificacoes_medicao')
    if alteracao == 'contradicao': historico[0]['leitura_rotacao_valida'] = True
    estado.atualizar_campos('mental', historico_corporal=historico,
        corpo_motor={'resultado_giro': 'SATURACAO'}, turno_atual={'id': 'agora', 'texto': 'o sensor falhou'})
    f = runtime.recuperar_explicacao(f"Por que fez esse gesto {registro['id']}?", turno={'id': 'consulta'})
    assert f.episodios and not f.episodios[0].nao_qualificacoes_medicao
    assert f.episodios[0].confirmado is False


def test_decisao_anterior_na_ocorrencia_nao_substitui_observacao_da_chamada_atual():
    from scripts.tests.test_decisao_observada import experiencia
    _, runtime = experiencia()
    inicio = runtime.iniciar(nome='giro', origem_intencao='pedido_usuario', perfil='bancada')
    inicio['nao_qualificacoes_medicao'] = [{'codigo': 'SATURACAO'}]
    registro = runtime.registrar(inicio, {'ok': False, 'resultado_giro': 'SATURACAO'}, [])
    assert not registro.get('nao_qualificacoes_medicao')


@pytest.mark.parametrize('codigo', ['IMU_OU_SESSAO', 'SATURACAO', 'PROTECAO', 'INTERROMPIDO'])
@pytest.mark.parametrize('alteracao', ['codigo', 'causa', 'remocao_ressalva', 'sucesso'])
def test_revisao_recusa_reinterpretacao_do_criterio_registrado(codigo, alteracao):
    from scripts.tests.test_explicacao_ocorrencia import episodio, plano
    e = episodio(confirmado=False)
    e = replace(e, nao_qualificacoes_medicao=(observacao(e, codigo=codigo),))
    f = ExplicacaoOcorrencia('consulta', 'Por que você fez esse gesto?', (e,), 'unica')
    p = plano(f); antes = deepcopy(p)
    fiel = realizacoes_explicacao_ocorrencia(f)[0]
    proposta = {'codigo': fiel.replace(f'código "{codigo}"', 'código "ALVO"'),
        'causa': fiel + ' O sensor está quebrado e travou o motor.',
        'remocao_ressalva': fiel.replace('Isso relata o critério registrado; não identifica uma causa física.', ''),
        'sucesso': fiel + ' Portanto, concluí a operação.'}[alteracao]
    assert proposta != fiel
    revisao = avaliar_fala_historica(proposta, plano=p)
    assert revisao['fala'] == fiel and revisao['problemas'] and not revisao['autoriza_execucao']
    assert p == antes
