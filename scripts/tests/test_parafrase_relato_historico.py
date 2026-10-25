"""Paráfrase pessoal depende da declaração histórica, não da fonte do assunto."""
import hashlib
import pytest

from mente_laylay.cognicao.fundamentacao_factual import (
    conferir_relato_preferencia_usuario, validar_fala_com_fundamentacao,
)


def _fonte(texto, *, autor='usuario', status='relatado_pelo_usuario'):
    return {'id':'dialogo:usuario:0:'+hashlib.sha256(texto.encode('utf8')).hexdigest(),
        'origem':'historico_conversa','autor':autor,'status':status,'texto':texto}


@pytest.mark.parametrize('origem,destino',[
    ('eu gosto de rock','Você disse gostar de rock.'),
    ('eu prefiro chá','Você contou preferir chá.'),
    ('eu curto jogos de estratégia','Você mencionou curtir jogos de estratégia.'),
    ('eu adoro desenhos','Você relatou adorar desenhos.'),
    ('eu não gosto de rock','Você disse não gostar de rock.'),
    ('eu não prefiro café','Você contou que não prefere café.'),
])
def test_transformacao_sintatica_preserva_predicado_polaridade_e_argumentos(origem,destino):
    r=conferir_relato_preferencia_usuario(destino,[_fonte(origem)])
    assert r is not None, 'declaração disponível, mas forma equivalente não tem conferência'
    assert r['pode_confirmar_fato_externo'] is r['autoriza_execucao'] is False


@pytest.mark.parametrize('confiavel',[False,True])
@pytest.mark.parametrize('destino',[
    'Você disse que gostava de rock.',
    'Você disse gostar de rock.',
])
def test_fonte_externa_sobre_o_assunto_nao_prova_que_usuario_declarou_preferencia(confiavel,destino):
    r=validar_fala_com_fundamentacao(destino,relatos_usuario=[_fonte('eu gosto de jazz')],
        fundamentacao={'tema':'rock','confiavel':confiavel,
            'resumo':'Rock e jazz são gêneros musicais.','fonte':'https://fonte.test/musica'})
    assert r['fala']!=destino, 'pesquisa externa foi usada para admitir um relato pessoal sem fonte'


def test_inversao_dos_valores_do_turno_historico_nao_e_equivalencia():
    origem='pra descansar eu gosto de rock, principalmente Nirvana'
    destino='Lá no começo, você falou que gostava de Nirvana, especialmente o rock deles.'
    assert conferir_relato_preferencia_usuario(destino,[_fonte(origem)]) is None


@pytest.mark.parametrize('autor,status',[('laylay','relatado_pelo_usuario'),
    ('usuario','corrigido'),('usuario','contestado')])
def test_forma_equivalente_nao_reabilita_proposta_ou_declaracao_revisada(autor,status):
    fonte=_fonte('eu gosto de rock',autor=autor,status=status)
    assert conferir_relato_preferencia_usuario('Você disse gostar de rock.',[fonte]) is None


@pytest.mark.parametrize('valor',['meu teclado','seu violão','esse aplicativo','rock deles','café hoje'])
def test_identidade_lexical_nao_resolve_deixis_entre_enunciadores_ou_momentos(valor):
    assert conferir_relato_preferencia_usuario(f'Você disse que prefere {valor}.',
        [_fonte(f'eu prefiro {valor}')]) is None


def _plano(fonte):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno
    texto='qual era a minha preferência?'
    return planejar_turno(texto,turno=classificar_modalidade_turno(texto),
        mente={'messages':[{'role':'user','content':fonte}]})


def test_plano_sem_pesquisa_tambem_confere_parafrase_pessoal():
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    plano=_plano('eu prefiro Obsidian')
    fala='Você disse preferir Obsidian.'
    r=verificar_fala_turno(fala,plano=plano)
    assert r['fala']==fala
    assert r['aceita'] is True
    assert r.get('revisao_relatos_usuario'), 'a ausência de tema externo pulou a conferência histórica'
    assert r['revisao_relatos_usuario'][0]['estado']=='conferido'


def test_plano_sem_pesquisa_nao_aprova_preferencia_nao_declarada():
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    fala='Você disse preferir Atlas.'
    r=verificar_fala_turno(fala,plano=_plano('eu prefiro Obsidian'))
    assert r['fala']!=fala
    assert 'relato_usuario_sem_apoio' in r['problemas']


def test_declaracao_atual_tipada_tambem_pode_sustentar_relato_sem_virar_memoria_duravel():
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno,verificar_fala_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    texto='eu adoro desenhos'
    turno=classificar_modalidade_turno(texto)
    plano=planejar_turno(texto,turno=turno)
    plano['contrato_fala']=construir_contrato_semantico_fala(texto,turno=turno,plano=plano)
    fala='Você disse adorar desenhos.'
    r=verificar_fala_turno(fala,plano=plano)
    assert r['fala']==fala
    fonte=r['revisao_relatos_usuario'][0]['conferencia']
    assert fonte['fonte_id'].startswith('entrada:usuario:')
    assert not plano['relatos_usuario'], 'a revisão não deve persistir nem duplicar a entrada atual'


def test_derivacao_expoe_campos_intervalos_e_hashes_sem_parecer_semantico_da_ia():
    fonte=_fonte('eu não gosto de rock, especialmente Nirvana')
    fala='Você disse não gostar de rock, principalmente Nirvana.'
    r=conferir_relato_preferencia_usuario(fala,[fonte])
    assert r is not None
    d=r['derivacao']
    assert d['regra']=='preservacao_preferencia_atribuida_v1'
    assert d['fonte_sha256']==hashlib.sha256(fonte['texto'].encode('utf8')).hexdigest()
    assert d['destino_sha256']==hashlib.sha256(fala.encode('utf8')).hexdigest()
    for lado in ['fonte','destino']:
        leitura=d[lado]
        assert leitura['papeis']=={'predicado':'gostar','negada':True,'valor':'rock','foco':'nirvana'}
        for campo in ['valor','foco']:
            a,b=leitura['intervalos'][campo]
            assert leitura['texto_normalizado'][a:b].strip().casefold()==leitura['papeis'][campo]
    assert d['alinhamento_estrutural_conferido'] is True
    assert d['prova_semantica_livre'] is False


def test_fonte_do_dialogo_com_texto_alterado_nao_mantem_identidade_anterior():
    fonte=_fonte('eu gosto de rock')
    fonte['texto']='eu gosto de jazz'
    assert conferir_relato_preferencia_usuario('Você disse gostar de jazz.',[fonte]) is None


def test_duas_frases_consultam_mesmo_snapshot_mesmo_quando_fontes_sao_iterador():
    fala='Você disse que gosta de rock. Você contou gostar de rock.'
    r=validar_fala_com_fundamentacao(fala, fundamentacao={'tema':'rock','confiavel':False},
        relatos_usuario=iter([_fonte('eu gosto de rock')]))
    assert r['fala']==fala
    assert len(r['relatos_usuario_conferidos'])==2


def test_relato_curto_conferido_nao_e_apagado_quando_fato_adicional_e_rejeitado():
    fala='Você disse adorar chá. O chá foi lançado em 1997.'
    r=validar_fala_com_fundamentacao(fala,fundamentacao={'tema':'chá','confiavel':False},
        relatos_usuario=[_fonte('eu adoro chá')])
    assert r['fala']=='Você disse adorar chá.'
    assert 'data_sem_evidencia' in r['problemas']


def test_pergunta_de_confirmacao_nao_e_julgada_como_declaracao_do_historico():
    fala='Você disse gostar de rock?'
    r=validar_fala_com_fundamentacao(fala,fundamentacao=None,apenas_relatos_usuario=True)
    assert r['fala']==fala
    assert not r['relatos_usuario_conferidos'] and not r['revisao_relatos_usuario']


@pytest.mark.parametrize('fala',['Você não disse preferir chá.',
    'Você nunca disse que prefere chá.','Você apenas disse preferir chá.'])
def test_operador_sobre_atribuicao_nao_e_polaridade_da_preferencia(fala):
    r=validar_fala_com_fundamentacao(fala,fundamentacao={'tema':'chá','confiavel':True,
        'resumo':'Chá é uma bebida.'},relatos_usuario=[_fonte('eu prefiro chá')])
    assert r['fala']!=fala
    assert not r.get('relatos_usuario_conferidos')


def test_factory_instalada_confere_apoio_sem_pesquisa_em_dominios_distintos(tmp_path):
    import os
    import subprocess
    import sys
    import textwrap
    from pathlib import Path
    codigo=textwrap.dedent('''
        import importlib.abc, importlib.machinery, importlib.util
        import json, sys
        from pathlib import Path
        from types import ModuleType
        import requests
        raiz=Path.cwd(); perfil=Path(sys.argv[1])
        apps=ModuleType('AppOpener')
        apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{}
        sys.modules['AppOpener']=apps
        codigo=(raiz/'laylay.py').read_bytes()
        bloco=b'PASTA_MEMORIA = os.path.join(_base_dir, "memoria")'
        assert codigo.count(bloco)==1
        codigo=codigo.replace(bloco,('PASTA_MEMORIA = '+repr(str(perfil/'raiz'))).encode())
        class Loader(importlib.machinery.SourceFileLoader):
            def get_code(self,nome):return compile(codigo,self.path,'exec')
        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self,nome,path=None,target=None):
                if nome=='laylay':
                    return importlib.util.spec_from_loader(nome,Loader(nome,str(raiz/'laylay.py')))
        sys.meta_path.insert(0,Finder())
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.autonomia import coordenador_intencao,roteador_intencao
        fala=''; efeitos=[];publicadas=[];enviados=[]
        def http(self,method,url,**kwargs):
            if not (str(method).upper()=='POST' and url=='http://localhost:11434/v1/chat/completions'):
                raise PermissionError('rede externa bloqueada')
            enviados.append(kwargs['json'])
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':json.dumps({
                'comandos':[],'suporte_proposicoes':[{'texto':fala,'fontes':[]}]})}}]}).encode()
            return r
        root=preparar_instalacao_isolada(perfil/'simulada',requisicao_http=http)
        for porta in ('_coleta_entradas_neurais','_especialista_neural_comandos_runtime',
                      '_interpretador_semantico_runtime','_pesquisa_contextual_runtime'):
            root._composicao_turno_runtime._servicos[porta]=getattr(root,porta)
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f,*a,**k:publicadas.append(f)or True)
        coordenador_intencao.executar_intencao=roteador_intencao.executar_intencao=lambda *a,**k:efeitos.append(a)or False
        estado=root._estado_compartilhado_runtime
        for fonte,proposta,apoiada in [
            ('eu gosto de rock','Você disse gostar de rock.',True),
            ('eu prefiro Obsidian','Você contou preferir Obsidian.',True),
            ('eu não gosto de café','Você disse não gostar de café.',True),
            ('eu gosto de jazz','Você disse gostar de rock.',False),
            ('eu prefiro Obsidian','Você contou preferir Atlas.',False)]:
            estado.substituir('mental',criar_estado_mental_inicial())
            estado.atualizar_campos('memoria_conversa',messages=[
                {'role':'system','content':BASE_SYSTEM_PROMPT},{'role':'user','content':fonte}])
            fala=proposta; inicio=len(publicadas)
            root._resposta_ia_runtime.processar('qual era a minha preferência?',origem='teste_parafrase')
            assert len(publicadas)==inicio+1
            plano=estado.mental['plano_turno_atual']
            assert not plano['autoriza_execucao'] and not plano['comandos']
            revisao=plano['ultima_verificacao']['revisao_relatos_usuario'][0]
            assert (revisao['estado']=='conferido') is apoiada
            assert (publicadas[-1]==proposta) is apoiada
            assert not any(revisao[k] for k in ('semantica_verificada','prova_implicacao',
                'pode_confirmar_fato_externo','autoriza_execucao'))
            if apoiada:
                assert revisao['conferencia']['texto_fonte']==fonte
        assert enviados and not efeitos
        sys.__stdout__.write('PARAFRASE_HISTORICO_INSTALADA_OK')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path)],capture_output=True,
        text=True,encoding='utf8',cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-2000:]
    assert 'PARAFRASE_HISTORICO_INSTALADA_OK' in r.stdout
