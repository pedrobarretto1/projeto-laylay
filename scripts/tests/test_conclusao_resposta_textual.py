"""Entrega pertence à ocorrência publicada, não à última geração auxiliar."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

PONTE = Path('C:/Users/pbarr/Documents/Codex/2026-10-28/ch/outputs/ponte_laylay')

def carregar(nome):
    spec=importlib.util.spec_from_file_location('teste_'+nome,PONTE/(nome+'.py'))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def sessao(tmp_path,cenario):
    m=carregar('runtime_laylay')
    s=m.SessaoLaylay.__new__(m.SessaoLaylay)
    s.pasta=tmp_path;s.id_atual=None;s.publicacoes=[];s.modelos=[]
    s.guarda=m.GuardaSemEfeitos(s.registrar)
    mental={'turno_atual':{'id':'turno-x'},'plano_turno_atual':{'id':'turno-x'}}
    s.root=SimpleNamespace(_estado_compartilhado_runtime=SimpleNamespace(mental=mental))
    confirmados=[]
    s.root._orquestrador_fala_runtime=SimpleNamespace(textos_publicados_turno=lambda ident:
        tuple(confirmados) if ident=='turno-x' else ())
    def processar(*a,**k):
        for evento in cenario:
            if evento['tipo']=='publicar':
                if s.publicar_texto(evento['texto'],mensagem_id=evento.get('mensagem_id','turno:turno-x')):
                    confirmados.append(evento['texto'])
            else:s.registrar(evento)
    s.runtime=SimpleNamespace(processar=processar)
    return s

def modelo(sucesso,tipo='principal'):
    return {'tipo':'modelo_retornou','sucesso':sucesso,'tipo_chamada':tipo,
            'rota':'principal' if sucesso else 'orcamento_bloqueado','texto':'diagnóstico'}

@pytest.mark.parametrize('cenario,degradada',[
    ([modelo(True),{'tipo':'publicar','texto':'Uma resposta aprovada.'},modelo(False,'manutencao')],False),
    ([modelo(True),modelo(False,'reparo_comunicacao'),{'tipo':'publicar','texto':'Não concluí esta resposta.'}],True),
])
def test_publicacao_confirmada_nao_e_apagada_por_falha_de_geracao(tmp_path,cenario,degradada):
    s=sessao(tmp_path,cenario)
    r=s.conversar('x','Uma pergunta')
    assert r['publicado'] and not r['modelo_falhou'],r
    assert r['degradada'] is degradada
    assert r['texto']==next(e['texto'] for e in cenario if e['tipo']=='publicar')

def test_publicacao_antiga_nao_e_receipt_do_turno_atual(tmp_path):
    s=sessao(tmp_path,[modelo(True),{'tipo':'publicar','texto':'Antiga.','mensagem_id':'turno:outro'}])
    r=s.conversar('x','Nova pergunta')
    assert not r['publicado'] and not r['texto'],r

def test_falha_recuperavel_concluida_nao_mata_o_processo_da_conversa(tmp_path):
    s=sessao(tmp_path,[modelo(False)])
    r=s.conversar('x','Uma pergunta')
    assert r['modelo_falhou'] and r['turno_concluido']
    m=carregar('ponte_laylay')
    backend=SimpleNamespace(conversar=lambda *_:r,fechar=lambda:pytest.fail('Não há timeout ou corrupção'))
    p=m.PonteConversa(backend)
    erro=p.receber({'tipo':'mensagem','id':'x','texto':'Uma pergunta'})
    assert erro['codigo']=='resposta_indisponivel' and not erro['encerrada']

def test_texto_proposto_sem_publicacao_nao_vira_resposta(tmp_path):
    s=sessao(tmp_path,[modelo(True)])
    r=s.conversar('x','Uma pergunta')
    assert not r['publicado'] and not r['texto']

def test_metadados_de_tipo_chegam_ao_journal_sem_alterar_resultado():
    m=carregar('runtime_laylay')
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo,ResultadoModelo
    resultado=ResultadoModelo('texto',True)
    servico=SimpleNamespace(executar=lambda pedido:resultado)
    eventos=[];m.conectar_identidade(servico,eventos.append)
    assert servico.executar(PedidoModelo.criar([],tipo_chamada='reparo_comunicacao')) is resultado
    assert eventos[0]['tipo_chamada']=='reparo_comunicacao'
