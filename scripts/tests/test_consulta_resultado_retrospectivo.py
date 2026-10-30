"""Consulta retrospectiva à própria fala não depende de perguntar por uma causa."""
import pytest
from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_historica
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


@pytest.mark.parametrize('verbo', ['disse','falou','respondeu','afirmou','explicou'])
@pytest.mark.parametrize('pergunta', ['o que estava confirmado em cada ação?', 'quais resultados havia?', 'como ficou o pedido?'])
def test_pergunta_temporal_resolve_fala_observada_sem_inventar_causa(verbo, pergunta):
    texto = f'Quando você {verbo} "Registrei os resultados.", {pergunta}'
    assert referencia_explicacao_historica(texto) == 'fala'
    t = classificar_modalidade_turno(texto)
    p = planejar_turno(texto, turno=t)
    registro = registrar_fala_observada(None, ocorrencia_id='publicacao', turno_id='anterior',
        fala='Registrei os resultados.',canal='texto_publicado',resultados=(ResultadoAcao(
            intent='APP_OPEN',alvo='Calculadora',status='falha',executou=False,confirmado=False,
            origem='executor',id_solicitacao='receipt'),))
    p['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=t,plano=p,mente={'registro_semantico':registro})
    assert 'evidencia_fala_historica' in p['contrato_fala']
    falsa = 'Abri tudo porque achei melhor.'
    r = verificar_fala_turno(falsa,plano=p)
    assert not (r['aceita'] and r['fala'] == falsa)
    assert not p['comandos'] and not p['autoriza_execucao']


@pytest.mark.parametrize('texto', [
    'Quando você disser "oi", quais resultados haverá?',
    'Se você dissesse "oi", quais resultados haveria?',
    'Quando ele disse "oi", quais resultados havia?',
    'Imagine uma história: «Quando você disse oi, quais resultados havia?»',
    'Traduza «Quando você disse oi, quais resultados havia?»',
    'Quando você disse "Podemos inventar uma história.", como ele continuaria essa história?',
    'Quando você disse "Vamos conversar.", o que você vai fazer agora?',
])
def test_condicao_futura_outro_agente_ou_citacao_nao_escolhem_fonte_propria(texto):
    assert referencia_explicacao_historica(texto) != 'fala'
