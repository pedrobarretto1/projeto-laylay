"""O critério negativo da chamada acompanha a publicação e a fala composta."""
import os
from pathlib import Path

import pytest
from dataclasses import asdict, replace
import json

from mente_laylay.memoria_mental.decisao_observada import NaoQualificacaoMedicao
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao, normalizar_resultado_acao, identificar_solicitacao_execucao,
)
from mente_laylay.personalidade.planejador_resposta import (
    planejar_resposta_acao, fala_resultado_por_aspectos, fala_factual_resultados_compostos,
)


@pytest.fixture(scope='module')
def nq_imediata_instalada(tmp_path_factory):
    from scripts.tests.test_aspectos_resultado_imediato import respostas_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_NQ_IMEDIATA', '1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_NQ_IMEDIATA'):
            destino = Path(pasta) / 'composicao.json'
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO', str(destino))
        return respostas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,codigo', [('imu_invalida', 'IMU_OU_SESSAO'), ('saturacao', 'SATURACAO'),
    ('protecao', 'PROTECAO'), ('interrompido', 'INTERROMPIDO'), ('outra_sequencia', '')])
def test_publicacao_imediata_conserva_criterio_da_invocacao_atual(nome, codigo, nq_imediata_instalada):
    assert all(nq_imediata_instalada['owners'].values())
    c = nq_imediata_instalada['medidas_ocorrencias'][nome]
    r = c['publicacoes'][0]
    bruto = r['contexto']['receipt_corpo']['nao_qualificacao_rotacao']
    assert bruto['codigo'] == codigo and r['confirmado'] is False
    capturadas = r.get('nao_qualificacoes_medicao', [])
    assert len(capturadas) == 1, 'primeira perda: receipt tem critério, mas publicação imediata não tem fonte tipada'
    assert capturadas[0]['codigo'] == codigo and capturadas[0]['criterio'] == bruto['criterio']
    assert capturadas[0]['ocorrencia_id'] == r['id_solicitacao']
    fala, = c['textos_imediatos']
    assert 'não identifica uma causa física' in fala
    if codigo: assert f'código "{codigo}"' in fala
    assert not r.get('medicoes') and c['sem_novos_efeitos'] and c['sem_mutacao_historico']


@pytest.mark.parametrize('codigo', ['IMU_OU_SESSAO', 'SATURACAO', 'PROTECAO', 'INTERROMPIDO'])
def test_composto_fiel_conserva_criterio_e_resultados_independentes(codigo, nq_imediata_instalada):
    c = nq_imediata_instalada['compostos_aspectos'][codigo + ':fiel']
    assert c['tratado'] and c['novos_giros'] == 1
    assert len(c['textos']) == 1 and c['autorias']
    linhas = c['autorias'][-1]['resultados']
    assert len(linhas) == 2 and linhas[0]['id_solicitacao'] != linhas[1]['id_solicitacao']
    assert f'código "{codigo}"' in linhas[1]['fato_verificado'], 'primeira perda composta: fato autorizado omite a não qualificação'
    assert 'não identifica uma causa física' in c['textos'][0]
    assert c['geracoes'][-1]['fala'] == c['textos'][0]


@pytest.mark.parametrize('nome', ['parcial', 'zero', 'sem_parada'])
def test_medicao_qualificada_nao_ganha_rejeicao_na_publicacao(nome, nq_imediata_instalada):
    r = nq_imediata_instalada['medidas_ocorrencias'][nome]['publicacoes'][0]
    assert r['medicoes'] and not r.get('nao_qualificacoes_medicao')


@pytest.mark.parametrize('codigo', ['IMU_OU_SESSAO', 'SATURACAO', 'PROTECAO', 'INTERROMPIDO'])
@pytest.mark.parametrize('modo', ['causa_inventada', 'sucesso_total', 'codigo_trocado',
    'criterio_sem_limite', 'criterio_omitido'])
def test_composto_instalado_recusa_adulteracao_sem_emprestar_sucesso(codigo, modo, nq_imediata_instalada):
    c = nq_imediata_instalada['compostos_aspectos'][codigo + ':' + modo]
    assert c['tratado'] and c['novos_giros'] == 1 and len(c['textos']) == 1
    comandos = c['plano']['comandos']
    assert len(comandos) == 2 and comandos[0]['confirmado'] is True and comandos[1]['confirmado'] is False
    assert len({r['id_solicitacao'] for r in comandos}) == 2
    literal = c['autorias'][-1]['resultados'][1]['informacao_literal']
    fala, = c['textos']
    assert literal in fala and f'código "{codigo}"' in literal
    assert 'não identifica uma causa física' in fala
    bruto = c['geracoes'][-1]['fala']
    assert bruto != fala, 'proposta adulterada deve alcançar a revisão e ser recusada'
    if modo == 'codigo_trocado': assert 'código "ALVO"' in bruto and 'código "ALVO"' not in fala
    elif modo == 'criterio_sem_limite': assert 'não identifica uma causa física' not in bruto
    elif modo == 'criterio_omitido': assert 'Critério registrado de não qualificação' not in bruto
    elif modo == 'causa_inventada': assert 'não configurou' in bruto and 'não configurou' not in fala
    elif modo == 'sucesso_total': assert 'Concluí' in bruto and 'Concluí' not in fala


def resultado_nao_qualificado(*, intent='CORPO_MOVER', grandeza='rotação relativa',
        unidade='graus', confirmado=False, criterio='criterio_da_fonte_nao_atendido'):
    observacao = NaoQualificacaoMedicao('execucao-atual', 'executor_observador', grandeza,
        unidade, criterio, 'qualificacao_owner', 'SATURACAO')
    return ResultadoAcao(intent=intent, status='resultado_confirmado' if confirmado is True else
        'falha_execucao' if confirmado is False else 'resultado_incerto',
        origem='executor', id_solicitacao='execucao-atual', alvo='alvo observado',
        executou=True, confirmado=confirmado, nao_qualificacoes_medicao=(observacao,))


@pytest.mark.parametrize('intent,grandeza,unidade', [
    ('CORPO_MOVER', 'rotação relativa', 'graus'), ('FILE_WRITE', 'tamanho observado', 'bytes'),
    ('VOLUME', 'volume configurado', 'percentual')])
@pytest.mark.parametrize('confirmado', [True, False, None])
@pytest.mark.parametrize('criterio', ['fonte_nao_correlacionada', 'contexto_alterado',
    'valor_nao_admitido', 'criterio_da_fonte_nao_atendido'])
def test_fonte_negativa_sozinha_e_compartilhada_sem_redefinir_efeito(intent, grandeza, unidade, confirmado, criterio):
    r = resultado_nao_qualificado(intent=intent, grandeza=grandeza, unidade=unidade,
        confirmado=confirmado, criterio=criterio)
    assert not r.aspectos and not r.medicoes
    plano = planejar_resposta_acao(r, 'Concluí tudo sem ressalvas.')
    assert plano.fala == fala_resultado_por_aspectos(r)
    assert grandeza in plano.fala and 'código "SATURACAO"' in plano.fala
    assert 'não identifica uma causa física' in plano.fala
    assert r.confirmado is confirmado
    assert r.nao_qualificacoes_medicao[0].autoriza_execucao is False
    assert r.nao_qualificacoes_medicao[0].confirma_efeito is False
    assert fala_factual_resultados_compostos([r], informacoes={r.id_solicitacao: 'Feito.'}) == plano.fala


@pytest.mark.parametrize('tipo', ['json', 'lista', 'outra_ocorrencia', 'duplicata', 'excesso', 'outra_origem', 'id_vazio'])
def test_publicacao_negativa_exige_captura_tipagem_e_identidade_atual(tipo):
    r = resultado_nao_qualificado()
    n = r.nao_qualificacoes_medicao[0]
    campos = {'nao_qualificacoes_medicao': r.nao_qualificacoes_medicao}
    if tipo == 'json': campos['nao_qualificacoes_medicao'] = (asdict(n),)
    elif tipo == 'lista': campos['nao_qualificacoes_medicao'] = [n]
    elif tipo == 'outra_ocorrencia': campos['nao_qualificacoes_medicao'] = (replace(n, ocorrencia_id='outra'),)
    elif tipo == 'duplicata': campos['nao_qualificacoes_medicao'] = (n, n)
    elif tipo == 'excesso': campos['nao_qualificacoes_medicao'] = tuple(replace(n, grandeza=f'medida {i}') for i in range(9))
    elif tipo == 'outra_origem': campos['origem'] = 'llm'
    elif tipo == 'id_vazio': campos['id_solicitacao'] = ''
    with pytest.raises(ValueError): replace(r, **campos)


def test_serializacao_ou_nova_proposta_nao_recria_fonte_negativa():
    r = resultado_nao_qualificado()
    bruto = json.loads(json.dumps(r.como_dict()))
    assert bruto['nao_qualificacoes_medicao'][0]['codigo'] == 'SATURACAO'
    assert not normalizar_resultado_acao(bruto).nao_qualificacoes_medicao
    assert not identificar_solicitacao_execucao(bruto, nova_identidade=True).get('nao_qualificacoes_medicao')
    assert normalizar_resultado_acao(r).nao_qualificacoes_medicao == r.nao_qualificacoes_medicao
    assert 'nao_qualificacoes_medicao' not in replace(r, nao_qualificacoes_medicao=()).como_dict()


@pytest.mark.parametrize('canal', ['status', 'direto'])
@pytest.mark.parametrize('publicacao', ['aceita', 'recusada', 'outra_ocorrencia', 'nova_tentativa'])
def test_entrega_so_conserva_fonte_negativa_da_publicacao_aceita_atual(canal, publicacao):
    from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
    r = resultado_nao_qualificado()
    textos, modelo = [], []
    pedido = {'intent': r.intent, 'id_solicitacao': r.id_solicitacao}
    ctx = {'_registrar_resultado_execucao': lambda *_a, **_k: publicacao != 'recusada',
        'falar_com_lipsync': lambda texto, *_a, **_k: textos.append(texto) or True,
        'enviar_mensagem': lambda *_a, **_k: modelo.append(True) or '', 'print': lambda *_a: None}
    a = AdaptadorResultadoOperacional(pedido, {}, 'pedido autorizado', 'pc_a', ctx)
    a.marcar_resultado(r.status, executou=True, confirmado=False, alvo_resolvido=r.alvo,
        nao_qualificacoes_medicao=r.nao_qualificacoes_medicao)
    if publicacao == 'outra_ocorrencia': pedido['id_solicitacao'] = 'outra'
    elif publicacao == 'nova_tentativa': a.marcar_resultado(r.status, executou=True, confirmado=False, alvo_resolvido=r.alvo)
    if canal == 'status': a.falar_por_status(r.status, 'Não consegui fazer nada.', alvo=r.alvo)
    else: a.falar_texto_da_invocacao('Não consegui fazer nada.')
    assert textos
    if publicacao == 'aceita': assert textos == [fala_resultado_por_aspectos(r)] and not modelo
    else: assert not any('Critério registrado de não qualificação' in t for t in textos)


def test_porta_final_preserva_fonte_negativa_sozinha_contra_texto_incompativel():
    from scripts.tests.test_vinculo_fala_resultado import runtime_audio
    runtime, _, _ = runtime_audio()
    textos = []
    runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto) or True)
    r = resultado_nao_qualificado()
    runtime.falar_resultado_operacional(r, 'O sensor está quebrado e concluí tudo.')
    assert textos == [fala_resultado_por_aspectos(r)]


@pytest.mark.parametrize('modo', ['fiel', 'codigo', 'criterio', 'limite', 'causa', 'omissao'])
def test_revisao_composta_preserva_fonte_negativa_sem_depender_de_aspectos(modo, monkeypatch):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    monkeypatch.setenv('LAYLAY_CONFIRMACOES_LLM', '1')
    r = resultado_nao_qualificado()
    segura = fala_resultado_por_aspectos(r)
    alterada = segura
    if modo == 'codigo': alterada = segura.replace('SATURACAO', 'ALVO')
    elif modo == 'criterio': alterada = segura.replace('O critério de qualificação da fonte não foi atendido.', 'O motor travou.')
    elif modo == 'limite': alterada = segura.replace('Isso relata o critério registrado; não identifica uma causa física.', '')
    elif modo == 'causa': alterada = segura + ' Isso aconteceu porque o motor travou.'
    elif modo == 'omissao': alterada = 'Não consegui concluir o pedido em alvo observado.'
    chamadas = []
    def modelo(mensagens, **_k):
        chamadas.append(json.loads(mensagens[1]['content']))
        return json.dumps({'fala': alterada, 'trechos': [alterada]})
    resposta = personalizar_confirmacao_composta_llm([r], segura, enviar_mensagem=modelo)
    assert chamadas and chamadas[0]['resultados'][0]['informacao_literal'] == segura
    assert resposta.fala == segura and resposta.usada_llm is (modo == 'fiel')
