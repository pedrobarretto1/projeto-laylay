"""A negociação de alvos não desloca a evidência do par atual system/user."""
import json
import pytest

from scripts.tests.test_unidades_autoria_por_ato import pacote_para
from scripts.tests.test_saida_tipificada_principal import preparador
from mente_laylay.autonomia.contexto_resposta_ia import (
    _formatar_fundamentacao_rapida, negociar_autoria_com_fontes,
)
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, PedidoModelo
from mente_laylay.integracao.llm_http import compactar_payload_llm_local
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT


@pytest.mark.parametrize('rapido', [False, True])
@pytest.mark.parametrize('reescrita', [False, True])
def test_alvos_fontes_e_contrato_atual_sobrevivem_juntos_ao_preparador(rapido, reescrita):
    _, plano, fato = pacote_para()
    evidencia = _formatar_fundamentacao_rapida(plano['fundamentacao_factual'])
    mensagens = (
        {'role': 'system', 'content': BASE_SYSTEM_PROMPT},
        {'role': 'system', 'content': 'INSTRUCAO_ANTIGA_NAO_REUTILIZAR'},
        {'role': 'user', 'content': 'Pergunta antiga?'},
        {'role': 'assistant', 'content': 'Resposta antiga.'},
        {'role': 'system', 'content': 'CONTRATO_ATUAL_COMPLETO\n' + evidencia},
        {'role': 'user', 'content': plano['texto_usuario']},
    )
    pacote = negociar_autoria_com_fontes(PacotePrompt(mensagens), plano['fundamentacao_factual'], plano_autoria=plano)
    assert pacote.contrato_saida.nome == 'autoria_por_ato_v5'
    assert any(fato in m['content'] for m in pacote.mensagens)
    pedido = PedidoModelo.criar(pacote.mensagens, contrato_saida=pacote.contrato_saida,
        tipo_chamada='reparo_factual' if reescrita else 'principal', modo_rapido=rapido, max_tokens=1024)
    payload = preparador().preparar(pedido).payload
    for atual in (payload, compactar_payload_llm_local(payload)):
        sistema_atual = atual['messages'][-2]['content']
        assert 'CONTRATO_ATUAL_COMPLETO' in sistema_atual, 'primeira fronteira: alvos em outro system deslocam contrato e evidência atuais'
        assert evidencia in sistema_atual and fato in sistema_atual
        assert 'CONTRATO DE AUTORIA COM SUPORTE' in sistema_atual
        assert 'REFERÊNCIAS DISPONÍVEIS' in sistema_atual and 'ATOS DESTA EMISSÃO' in sistema_atual
        assert not any('INSTRUCAO_ANTIGA_NAO_REUTILIZAR' in m['content'] for m in atual['messages'])
        assert atual['messages'][-1]['content'] == plano['texto_usuario']
        assert atual['response_format'] == pacote.contrato_saida.response_format


def test_inventario_exposto_preserva_alvos_sem_repetir_metadados_de_conferencia():
    from mente_laylay.cognicao.validacao_contrato_fala import inventariar_atos_autoria
    pacote, plano, _ = pacote_para()
    mensagem = next(m['content'] for m in pacote.mensagens if 'ATOS DESTA EMISSÃO' in m['content'])
    bruto = mensagem.split('ATOS DESTA EMISSÃO (IDs do host, não prova): ', 1)[1]
    exposto, _ = json.JSONDecoder().raw_decode(bruto)
    inventario = inventariar_atos_autoria(plano)
    assert exposto == [{k: a[k] for k in ('id', 'tipo', 'texto_original')} for a in inventario]
    assert all(a['turno_id'] and a['intervalo'] for a in inventario)
    assert all(a['autoriza_execucao'] is a['prova_implicacao'] is False for a in inventario)
