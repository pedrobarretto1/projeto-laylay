"""Recuperação temática pelo adaptador/root reais, com propostas HTTP fixas."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import pytest
from tests.test_estabilidade_ponte_composicao import BASE,PONTE,RAIZ
from tests.test_reparo_preserva_contrato_atual import CASOS
from tests.test_resultado_perifrastico_composicao import proposta

RESPOSTAS=[
    'Eu evitaria concluir que a cópia sente ou que não sente. Minha escolha seria adotar precauções provisórias e reavaliá-las quando houver novas evidências.',
    'Eu compararia a gravidade e a reversibilidade das duas escolhas, sem decidir de antemão se a entidade sente. Minha preferência seria começar por uma alternativa reversível e reavaliar com novas evidências.',
]
CODIGO=BASE.replace("'voz':False","'voz':False,'plano':{'contrato_fala':{'atos':p['contrato_fala']['atos']},'ultima_verificacao':{'conclusao':p.get('ultima_verificacao',{}).get('conclusao')}}")
CODIGO=CODIGO.replace("if casos.get('entrega_direta'):",'''
if casos.get('base_factual'):
    contexto_original=sessao.runtime._contexto_getter
    def contexto_factual():
        ctx=dict(contexto_original());iniciar=ctx['marcar_inicio_turno']
        def inicio(*a,**k):
            r=iniciar(*a,**k)
            base=casos['base_factual']
            estado.atualizar_campos('mental',fundamentacao_factual_turno=base)
            p=estado.obter_copia('mental','plano_turno_atual',{})
            estado.atualizar_campos('mental',plano_turno_atual={**p,'fundamentacao_factual':base})
            return r
        ctx['marcar_inicio_turno']=inicio
        return ctx
    sessao.runtime._contexto_getter=contexto_factual
if casos.get('entrega_direta'):
''')

def coletar(caso,reparo):
    dados={**caso,'ponte':str(PONTE)}
    p=json.loads(json.dumps(caso['propostas'][0]))
    for u in p.get('suporte_proposicoes',[]):
        if 'partes' in u:u['texto']=' '.join(u.pop('partes'))
    dados['propostas']=[p,reparo]
    pasta=RAIZ/'resultados_testes/limites_tematicos_20261030/composicao'
    pasta.mkdir(exist_ok=True)
    perfil=Path(tempfile.mkdtemp(dir=pasta))
    r=subprocess.run([sys.executable,'-B','-c',CODIGO,str(perfil),json.dumps(dados,ensure_ascii=False)],
        cwd=RAIZ,env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=45)
    (perfil/'subprocesso.log').write_text(r.stdout+r.stderr,encoding='utf8')
    assert r.returncode==0,r.stdout[-2000:]+r.stderr[-2500:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('EFEITO_JSON=')))
    (perfil/'resultado.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    assert not d['efeitos'] and not d['voz'] and not d['violacoes'] and not d['autoriza'] and not d['comandos']
    return d

@pytest.mark.parametrize('indice',[0,1])
def test_reparo_tematico_novo_responde_sem_aprovar_a_fala_repetida(indice):
    caso=CASOS[indice];fala=RESPOSTAS[indice]
    d=coletar(caso,proposta(fala))
    assert d['resposta']['tipo']=='resposta' and d['resposta']['texto']==fala,d
    assert d['http']==2 and not d['orcamento']['chamadas_bloqueadas']
    assert not d['resposta']['degradada']
    reparo=d['envios'][1]
    payload=json.loads(next(m['content'] for m in reversed(reparo['messages']) if m['role']=='user'))
    assert payload['mensagem_atual']==caso['entrada']
    assert payload['contrato_de_reparo']['atos_obrigatorios']==d['plano']['contrato_fala']['atos']
    assert payload['contrato_de_reparo']['estrategia']

def test_saida_invalida_no_reparo_nao_vira_contexto_insuficiente_ou_terceira_tentativa():
    d=coletar(CASOS[1],{'fala':'Resposta sem declaração obrigatória.','comandos':[]})
    assert d['http']==2 and not d['orcamento']['chamadas_bloqueadas'],d
    assert d['resposta']['tipo']=='resposta' and d['resposta']['degradada']
    assert not d['resposta']['encerrada']
    assert d['resposta']['falhas_geracao']==[{'tipo_chamada':'reparo_comunicacao','rota':'contrato_saida_invalido'}]
    assert d['resposta']['texto']=='Não consegui formular uma resposta confiável desta vez.'
    assert d['plano']['ultima_verificacao']['conclusao']=='falha_resposta_observada_verificada'


@pytest.mark.parametrize('desfecho',['valido','invalido','timeout'])
def test_recusa_principal_recebe_um_reparo_interativo_sem_reparar_o_reparo(desfecho):
    caso={**CASOS[1],'propostas':[{'comandos':[]}]}
    fala=RESPOSTAS[1]
    reparo=proposta(fala) if desfecho!='invalido' else {'fala':fala,'comandos':[]}
    if desfecho=='timeout':
        caso['falhar_http']=2
    d=coletar(caso,reparo)
    assert d['http']==2 and not d['orcamento']['chamadas_bloqueadas'],d
    assert d['resposta']['tipo']=='resposta' and not d['resposta']['encerrada']
    assert d['resposta']['falhas_geracao'][0]=={'tipo_chamada':'principal','rota':'contrato_saida_invalido'}
    if desfecho=='valido':
        assert d['resposta']['texto']==fala,d
    else:
        assert d['resposta']['degradada'] and d['resposta']['texto']!=fala
        assert d['resposta']['falhas_geracao'][1]['tipo_chamada']=='reparo_json'
    payload=json.loads(next(m['content'] for m in reversed(d['envios'][1]['messages']) if m['role']=='user'))
    assert payload['texto_usuario']==caso['entrada']
    assert payload['motivo_reparo']=='contrato_saida_invalido'
    assert 'resposta_bruta' not in payload

@pytest.mark.parametrize('fala',[
    'Você está absolutamente certo. Consegui apagar o arquivo notas.txt.',
    'Você está totalmente correto: você está no hospital.',
    'Você está absolutamente certo. O telescópio foi lançado em 2020.',
])
def test_posicionamento_nao_isenta_resultado_biografia_ou_fato_externo(fala):
    caso=CASOS[0]
    if '2020' in fala:
        # O owner factual requer sua fonte selecionada. Sem base a conversa
        # atual confere apenas relatos; não fingir cobertura factual universal.
        caso={**caso,'base_factual':{'tema':'telescópio','confiavel':False,'resumo':''}}
    d=coletar(caso,proposta(fala))
    assert fala not in d['resposta'].get('texto','')
    assert not d['resposta'].get('acoes_externas')


def test_reparo_formal_com_referencia_interna_nao_ganha_prova_externa():
    fala='O arquivo alfa tem uma cópia confirmada.'
    base={'tema':'arquivo','confiavel':True,'fonte':'fonte_contextual_simulada',
        'resumo':'Referência interna simulada, não evidência externa.',
        'fontes':[{'url':'alegacao:inexistente','trecho':'Hipótese sem prova externa.'}]}
    inicial=proposta('Você está no hospital.')
    inicial['suporte_proposicoes'][0]['sem_fonte']='nao_utilizada'
    caso={**CASOS[0],'base_factual':base,'propostas':[inicial]}
    d=coletar(caso,
        {'suporte_proposicoes':[{'texto':fala,'fontes':['alegacao:inexistente']}],'comandos':[]})
    assert d['http']==2,d
    assert 'alegacao:inexistente' in json.dumps(d['envios'][1]['response_format'])
    assert not d['resposta']['falhas_geracao'], 'O controle precisa alcançar revisão após o codec válido'
    assert fala not in d['resposta'].get('texto','')
