"""Recusar a projeção compacta não dispensa a autoria do envio atual."""
from copy import deepcopy
import json
import pytest

from tests.test_explicacao_capacidades_sem_execucao import preparar
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm


@pytest.mark.parametrize('alvo,campo,valor,autoria_atual',[
    ('turno_atual','id',80,False),
    ('turno_atual','autoriza_execucao',True,True),
    ('turno_atual','modalidade_geral','misto',True),
    ('contrato_fala_atual','turno_id',80,True),
    ('contrato_fala_atual','documentacao_capacidades','',True),
])
@pytest.mark.parametrize('rapido',[False,True])
def test_guarda_didatica_preserva_fluxo_completo_e_protocolo_independente(alvo,campo,valor,autoria_atual,rapido):
    estado,runtime,mensagens=preparar('como eu poderia pausar a música?')
    documento=estado['contrato_fala_atual']['documentacao_capacidades']
    estado[alvo][campo]=valor
    antes=deepcopy(mensagens);estado_antes=deepcopy(estado)
    p=runtime.preparar_envio_modelo(mensagens,turno_id=81)
    assert not p.contexto_fechado
    assert mensagens==antes and estado==estado_antes
    assert [m for m in p.mensagens if m['role']!='system']==[m for m in antes if m['role']!='system']
    assert p.mensagens[0]==antes[0] and p.mensagens[-1]==antes[-1]
    assert documento not in str(p.mensagens)
    assert 'Documentação da habilidade' not in str(p.mensagens)
    if not autoria_atual:
        assert list(p.mensagens)==antes and p.contrato_saida is None
    else:
        assert p.contrato_saida is not None
        schema=p.contrato_saida.response_format['json_schema']['schema']
        assert 'suporte_proposicoes' in schema['required']
        valida={'suporte_proposicoes':[{'texto':'Posso explicar como pedir ajuda.','fontes':[]}],'comandos':[]}
        assert p.contrato_saida.decodificar_json(json.dumps(valida))['fala']=='Posso explicar como pedir ajuda.'
        for invalida in [
            {'fala':'Posso explicar como pedir ajuda.','comandos':[]},
            {'suporte_proposicoes':[{'texto':'Algo novo.','fontes':['fonte_inventada']}],'comandos':[]},
        ]:
            with pytest.raises(ValueError):p.contrato_saida.decodificar_json(json.dumps(invalida))
    transporte=preparar_payload_llm(list(p.mensagens),model='teste',modo_rapido=rapido,contexto_fechado=p.contexto_fechado)
    assert any(m['role']=='assistant' and m['content']==antes[1]['content'] for m in transporte['messages'])
    assert transporte['messages'][-1]==antes[-1]
