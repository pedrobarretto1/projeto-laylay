"""Uma projeção de prompt não substitui a identidade integral do pedido."""
import json
import pytest
from tests.test_escopo_permissivo_contraste import CASOS
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria

ENTRADA=next(c['entrada']for c in CASOS if c['id']=='papo-004')

@pytest.mark.parametrize('texto',[ENTRADA, 'Um detalhe da nossa conversa. '*22+'O que você acha?'])
def test_plano_preserva_texto_atual_inteiro_para_vincular_autoria(texto):
    assert len(texto)>500
    p=planejar_turno(texto,turno=classificar_modalidade_turno(texto))
    assert p['texto_usuario']==texto
    fala='Acho engraçado.'
    bruto=json.dumps({'fala':fala,'comandos':[],'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})
    p['suporte_autoria_proposto']=capturar_suporte_autoria(ContratoPropostaPrincipal(str(p['id']),texto,bruto,True))
    r=revisar_suporte_autoria(fala,plano=p)
    assert r is None or r.como_dict()['estado']!='autoria_de_outra_ocorrencia'


def test_mesmo_prefixo_nao_confere_suporte_ao_pedido_com_outro_final():
    p=planejar_turno(ENTRADA,turno=classificar_modalidade_turno(ENTRADA))
    fala='Acho engraçado.';outra=ENTRADA[:500]+' outro pedido'
    bruto=json.dumps({'fala':fala,'comandos':[],'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})
    p['suporte_autoria_proposto']=capturar_suporte_autoria(ContratoPropostaPrincipal(str(p['id']),outra,bruto,True))
    r=revisar_suporte_autoria(fala,plano=p)
    assert r.aplicar_limite and r.como_dict()['estado']=='autoria_de_outra_ocorrencia'


def test_alinhador_na_composicao_nao_reintroduz_truncamento_da_identidade():
    from mente_laylay.cognicao.orquestrador_turno_runtime import alinhar_identidade_plano_revisao
    p=alinhar_identidade_plano_revisao({},texto_original=ENTRADA)
    assert p['texto_usuario']==ENTRADA
