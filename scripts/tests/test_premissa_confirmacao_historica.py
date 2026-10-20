"""Uma confirmação histórica conserva a premissa de escopo do executor."""
from copy import deepcopy

import pytest

from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, recuperar_evidencia_da_fala,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_fala_historica


def receipt(escopo='estado_firmware', *, executou=True, confirmado=True, **kwargs):
    return ResultadoAcao(intent='CORPO_MOVER', alvo='corpo', status='resultado',
        executou=executou, confirmado=confirmado, origem='executor', id_solicitacao='pedido-1',
        confirmacao_oferecida=escopo, evidencia_confirmacao='Critério declarado; não inferir seu significado.', **kwargs)


def registrar(resultado):
    return registrar_fala_observada(None, ocorrencia_id='fala-1', turno_id='turno-1',
        fala='Registrei a resposta do pedido.', resultados=(resultado,), canal='texto_publicado', agora=1000)


def evidencia_para(resultado):
    registro = registrar(resultado)
    return recuperar_evidencia_da_fala('Quando você disse "Registrei a resposta do pedido.", o que estava confirmado?',
        {'registro_semantico': registro}, agora=1001)


@pytest.mark.parametrize('intent,escopo', [('CORPO_MOVER','estado_firmware'), ('CREATE_FILE','estado_observado'),
    ('EMAIL_READ','retorno_dados'), ('IOT_CONTROL','estado_observado')])
def test_publicacao_conserva_escopo_canonico_de_cada_receipt(intent, escopo):
    r = ResultadoAcao(intent=intent, alvo='alvo do pedido', status='resultado', executou=True,
        confirmado=True, origem='executor', id_solicitacao='pedido-1')
    assert r.como_dict()['confirmacao_oferecida'] == escopo, 'controle: premissa precisa nascer no receipt'
    fonte = registrar(r)['falas_observadas'][0]['resultados'][0]
    assert fonte.get('confirmacao_oferecida') == escopo, 'primeira fronteira: snapshot da fala descarta o escopo tipado'


def test_duas_confirmacoes_de_mesmo_valor_nao_colapsam_escopos_distintos():
    a, b = registrar(receipt('estado_firmware')), registrar(receipt('estado_observado'))
    assert a['falas_observadas'][0]['resultados'] != b['falas_observadas'][0]['resultados']


def test_mesma_ocorrencia_nao_pode_reescrever_o_escopo_historico():
    fonte = registrar(receipt('estado_firmware'))
    with pytest.raises(ValueError, match='Outra publicação'):
        registrar_fala_observada(fonte, ocorrencia_id='fala-1', turno_id='turno-1',
            fala='Registrei a resposta do pedido.', resultados=(receipt('estado_observado'),),
            canal='audio_reproducao_confirmada', agora=1001)


@pytest.mark.parametrize('escopo', ['estado_firmware','estado_owner','retorno_dados','persistencia_local'])
def test_realizacao_se_limita_ao_escopo_capturado_sem_interpretar_descricao(escopo):
    evidencia = evidencia_para(receipt(escopo))
    # Injeta somente a premissa já presente no receipt para isolar projeção de captura.
    evidencia['falas'][0]['resultados'][0]['confirmacao_oferecida'] = escopo
    for fala in realizacoes_fala_historica(evidencia, agora=1001):
        assert f'no escopo registrado "{escopo}"' in fala, 'projeção não pode ampliar confirmação pelo booleano'
        assert 'Critério declarado' not in fala


def test_historico_legado_sem_escopo_nao_consulta_catalogo_atual(monkeypatch):
    evidencia = evidencia_para(receipt())
    evidencia['falas'][0]['resultados'][0].pop('confirmacao_oferecida', None)
    import mente_laylay.especialistas.capacidades as capacidades
    monkeypatch.setattr(capacidades, 'consultar_capacidade', lambda *_: pytest.fail('catálogo atual não prova escopo antigo'))
    for fala in realizacoes_fala_historica(evidencia, agora=1001):
        assert 'escopo não registrado' in fala
        assert 'efeito confirmado' not in fala
        assert 'não comprova o estado atual' in fala


@pytest.mark.parametrize('valor', [True, 42, {}, [], '', 'x' * 81, 'estado\nfirmware', ' estado_firmware'])
def test_premissa_de_escopo_malformada_nao_e_convertida_em_confirmacao(valor):
    evidencia = evidencia_para(receipt())
    evidencia['falas'][0]['resultados'][0]['confirmacao_oferecida'] = valor
    assert realizacoes_fala_historica(evidencia, agora=1001) == ()


def test_recuperacao_conserva_premissa_sem_criar_autoridade_ou_efeito():
    evidencia = evidencia_para(receipt())
    assert evidencia['falas'][0]['resultados'][0].get('confirmacao_oferecida') == 'estado_firmware'
    assert evidencia['autoriza_execucao'] is False
    assert evidencia['falas'][0]['autoriza_execucao'] is False


def test_atualizacao_de_outra_acao_nao_muda_premissa_da_fala_original():
    fonte = registrar(receipt())
    original = deepcopy(fonte['falas_observadas'][0])
    registrar_fala_observada(fonte, ocorrencia_id='fala-2', turno_id='turno-2',
        fala='Outra resposta.', resultados=(receipt('estado_observado'),), canal='texto_publicado', agora=1001)
    assert fonte['falas_observadas'][0] == original


@pytest.mark.parametrize('executou', [True, False, None])
@pytest.mark.parametrize('confirmado', [True, False, None])
def test_premissa_de_escopo_nao_modifica_os_tres_valores_do_resultado(executou, confirmado):
    evidencia = evidencia_para(receipt(executou=executou, confirmado=confirmado))
    original = deepcopy(evidencia)
    falas = realizacoes_fala_historica(evidencia, agora=1001)
    assert falas and evidencia == original
    for fala in falas:
        assert 'no escopo registrado "estado_firmware"' in fala
        assert ('sem nova execução registrada' in fala) is (executou is False and confirmado is True)
        assert ('confirmação desconhecida' in fala) is (confirmado is None)
        assert ('efeito não confirmado' in fala) is (confirmado is False)
        assert ('efeito confirmado' in fala) is (confirmado is True)


def test_dicionario_da_ia_com_campos_de_receipt_nao_cria_premissa():
    with pytest.raises(ValueError, match='receipt tipado'):
        registrar_fala_observada(None, ocorrencia_id='fala-1', turno_id='turno-1',
            fala='Registrei a resposta do pedido.', resultados=(receipt().como_dict(),),
            canal='texto_publicado', agora=1000)


def test_escopo_indisponivel_nao_vira_comprovacao_de_efeito_por_booleano():
    evidencia = evidencia_para(receipt())
    r = evidencia['falas'][0]['resultados'][0]
    r['confirmacao_oferecida'] = 'indisponivel'
    antes = deepcopy(evidencia)
    for fala in realizacoes_fala_historica(evidencia, agora=1001):
        assert 'confirmação registrada no escopo registrado "indisponivel"' in fala
        assert 'efeito confirmado' not in fala
    assert evidencia == antes and r['confirmado'] is True
