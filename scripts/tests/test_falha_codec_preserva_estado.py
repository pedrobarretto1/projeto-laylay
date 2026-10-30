"""Recusa do codec é falha observada do serviço, nunca autoria ou falta de contexto."""
from types import SimpleNamespace
import pytest
from tests.test_saida_tipificada_principal import preparador
from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import PedidoModelo,ResultadoModelo
from mente_laylay.cognicao.estado_tecnico_llm import categoria_estado_tecnico_llm

@pytest.mark.parametrize('bruto',['{','{"fala":"Sem suporte.","comandos":[]}',
    '{"suporte_proposicoes":[{"texto":"Texto.","fontes":["inventada"]}]}'])
@pytest.mark.parametrize('tipo',['reparo_comunicacao','reparo_factual','reparo_json'])
def test_recusa_mantem_categoria_tecnica_ate_o_consumidor(bruto,tipo):
    s=ServicoModeloLLMRuntime(preparador=preparador(),
        cliente=SimpleNamespace(executar=lambda req:ResultadoModelo(bruto,True)))
    r=s.executar(PedidoModelo.criar([{'role':'user','content':'Uma pergunta?'}],tipo_chamada=tipo))
    assert not r.sucesso and r.rota=='contrato_saida_invalido'
    assert categoria_estado_tecnico_llm(r.texto)=='contrato_saida_invalido',r
    assert r.texto!=bruto

def test_categoria_nao_e_inferida_de_prosa_ou_json_da_ia():
    assert not categoria_estado_tecnico_llm('{"erro":"contrato_saida_invalido"}')
    assert not categoria_estado_tecnico_llm('Acho que houve contrato_saida_invalido.')
