"""Orçamento de fonte é admissibilidade de perfil, nunca nova interpretação."""
from copy import deepcopy

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.integracao.registro_conversa_llm import RegistroPreparacaoConversa
from mente_laylay.integracao.preparacao_llm import historico_recuperavel_exige_contexto_amplo
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT


def historico(quantidade):
    return [{'role':'system','content':BASE_SYSTEM_PROMPT},
        {'role':'user','content':'Meu telescópio é Azul.'},
        {'role':'assistant','content':'Entendi.'},
        {'role':'user','content':'Corrigindo: ele é Âmbar.'},
        *[{'role':'user','content':f'Observei a nuvem número {i} perto da janela da sala.'}for i in range(quantidade)]]


def preparar_runtime(estado, otimizar=True):
    return ContextoPromptRuntime(memoria_sqlite=None,resumo_mente_integrada=lambda _: '',
        formatar_playlists=lambda:'',get_status_humor_prompt=lambda:'',
        base_system_prompt=BASE_SYSTEM_PROMPT,estado_getter=lambda:estado,
        otimizacao_prompt_ativa=otimizar)


@pytest.mark.parametrize('quantidade,esperado',[(0,False),(3,False),(18,True),(45,False)])
def test_mesmo_orcamento_decide_apenas_quando_contexto_normal_recupera(quantidade,esperado):
    mensagens=historico(quantidade);antes=deepcopy(mensagens)
    assert historico_recuperavel_exige_contexto_amplo(mensagens,'Qual é o telescópio?') is esperado
    assert mensagens==antes


def test_arquivo_longo_sem_vinculo_nao_exige_perfil_normal():
    assert not historico_recuperavel_exige_contexto_amplo(historico(14),'Como está o jardim?')


def test_consulta_de_admissibilidade_nao_prepara_fala_nem_muda_estado():
    estado={'messages':historico(18),'turno_atual':{'autoriza_execucao':False}}
    antes=deepcopy(estado);runtime=preparar_runtime(estado)
    registro=RegistroPreparacaoConversa.criar(runtime)
    diagnostico=runtime.diagnostico()
    for _ in range(2):
        assert registro.exige_contexto_amplo('Qual é o telescópio?') is True
    assert estado==antes
    assert runtime.diagnostico()==diagnostico


def test_otimizacao_desativada_nao_impoe_orcamento_que_nao_sera_usado():
    runtime=preparar_runtime({'messages':historico(18)},otimizar=False)
    assert not runtime.exige_contexto_amplo('Qual é o telescópio?')


def test_preparador_antigo_permanece_compativel_sem_receber_memoria():
    class Antigo:
        def preparar_pacote(self,texto):raise AssertionError('não preparar em consulta de perfil')
        def diagnostico(self):return {}
    registro=RegistroPreparacaoConversa.criar(Antigo())
    assert not registro.exige_contexto_amplo('Qual é o telescópio?')


def test_orcamento_nao_antecipa_llm_a_resposta_social_local_de_jogo():
    from types import SimpleNamespace
    from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
    from mente_laylay.autonomia.fluxos_conversa import usar_modo_rapido_conversa
    from mente_laylay.integracao.registro_conversa_llm import EstadoConversaRuntime, ResultadoModelo

    mensagens=[{'role':'system','content':BASE_SYSTEM_PROMPT},
        {'role':'user','content':'Boa tarde.'},
        *[{'role':'user','content':f'Hoje observei a nuvem número {i}, perto da janela da sala.'}for i in range(18)]]
    fala,pedidos=[],[]
    estado=EstadoConversaRuntime(getter=lambda:mensagens,
        setter=lambda novas:mensagens.__setitem__(slice(None),novas))
    prompt=preparar_runtime({'messages':mensagens})
    assert prompt.exige_contexto_amplo('boa tarde') is True
    inicio={'mente_integrada_estado':{'turno_atual':{'modalidade':'conversa'}},
        '_texto_social_curto':lambda _:True,'_texto_conversa_casual_sem_acao':lambda _:True,
        '_texto_tem_comando_explicito':lambda _:False,
        '_resposta_conversa_rapida_local':lambda _:'Boa tarde!',
        '_emitir_resposta_curta':lambda entrada,texto,**kw:fala.append(texto)}
    def gerar(pedido):
        pedidos.append(pedido)
        return ResultadoModelo('{"fala":"Entendi.","comandos":[]}',True)
    ctx={'contexto_inicio':lambda:inicio,'processar_inicio_fluxo':lambda *a:False,
        'usar_modo_rapido':usar_modo_rapido_conversa,'texto_depende_de_contexto':lambda _:False,
        'modo_jogo_ativo':lambda:True,'contexto_prompt_runtime':prompt,
        'estado_conversa':estado,'modelo_llm':SimpleNamespace(executar=gerar),
        'preparar_resposta':lambda *a:{'resposta_bruta':'{}','fala':'Entendi.','comandos':[],
            'tipo_interacao':'conversa','leitura_semantica':{}},
        'contexto_dispatch_runtime':SimpleNamespace(montar=lambda:{}),
        'executar_comandos_json':lambda *a:{'erros':[]},
        'contexto_finalizacao_runtime':SimpleNamespace(montar=lambda:{}),
        'finalizar_execucao':lambda *a:None}
    RespostaIARuntime(contexto_getter=lambda:ctx,log=lambda *a:None).processar('boa tarde')
    assert fala==['Boa tarde!'],'saudação local foi desviada por histórico lexical antigo'
    assert not pedidos
