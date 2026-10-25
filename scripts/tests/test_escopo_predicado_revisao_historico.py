"""O foco de uma clivagem não atribui propriedades a todo tema mencionado."""
import pytest

from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao


@pytest.mark.parametrize('tema,frase', [
    ('Azul', 'De acordo com o histórico, a Bia é quem vai levar o livro azul.'),
    ('Duna', 'A Bia é quem vai levar o livro Duna.'),
    ('Projetor', 'Segundo o que você contou, Dora é quem vai trazer o projetor.'),
    ('Amarelo', 'É o Leo quem vai usar o caderno amarelo.'),
    ('Rascunho', 'É a Julia quem vai revisar o arquivo Rascunho.'),
    ('Atlas', 'O Rui é quem vai usar o aplicativo Atlas.'),
    ('Azul', 'É a Bia que vai levar o livro azul.'),
    ('Rascunho', 'A Julia é que vai revisar o arquivo Rascunho.'),
    ('Atlas', 'Quem vai usar o aplicativo Atlas é o Rui.'),
])
def test_foco_de_plano_futuro_nao_confirma_fato_externo_sobre_objeto_mencionado(tema, frase):
    r=validar_fala_com_fundamentacao(frase, fundamentacao={
        'tema':tema,'titulo':tema,'confiavel':False,'resumo':''})
    assert r['fala']==frase, 'cópula de sujeito foi aplicada ao objeto mencionado em outra oração'
    assert 'alegacao_especifica_sem_fonte' not in r['problemas']
    # Classificar alcance do predicado não declara suporte ou verdade.
    assert not r.get('relatos_usuario_conferidos')


@pytest.mark.parametrize('frase', [
    'A Bia vai levar o livro azul.',
    'Segundo o histórico, Dora trouxe o projetor.',
])
def test_controle_sem_copula_ja_preserva_mesmo_relato(frase):
    r=validar_fala_com_fundamentacao(frase,fundamentacao={
        'tema':'Azul' if 'azul' in frase else 'Projetor','confiavel':False})
    assert r['fala']==frase


@pytest.mark.parametrize('tema,frase', [
    ('Azul', 'O livro Azul é um clássico.'),
    ('Azul', 'A Bia é quem publicou o livro Azul.'),
    ('Azul', 'Foi a Bia quem publicou o livro Azul.'),
    ('Azul', 'A Bia é quem vai levar o livro Azul, que foi publicado em 1997.'),
    ('Azul', 'É a Bia quem vai levar o livro Azul, que é um clássico.'),
    ('Azul', 'O livro Azul é quem tem os melhores personagens.'),
    ('Azul', 'A Bia é quem ganhou o prêmio pelo livro Azul.'),
    ('Azul', 'A Bia é quem escreveu o livro Azul.'),
    ('Azul', 'A Bia é quem desenhou o livro Azul.'),
    ('Azul', 'É Bia quem dirige o filme Azul.'),
    ('Projetor', 'Segundo o que você contou, Dora foi quem trouxe o projetor.'),
    ('Azul', 'Foi a Bia que escreveu o livro Azul.'),
    ('Atlas', 'Quem publicou o jogo Atlas foi o Rui.'),
])
def test_foco_nao_isenta_outros_predicados_e_fatos_externos(tema,frase):
    r=validar_fala_com_fundamentacao(frase,fundamentacao={
        'tema':tema,'titulo':tema,'confiavel':False,'resumo':''})
    assert r['fala']!=frase
    assert r['problemas']


def test_factory_preserva_plano_do_historico_sem_aceitar_data_ou_autoridade_propostas(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    import textwrap
    codigo=textwrap.dedent(r'''
        import json,sys
        import importlib.abc,importlib.machinery,importlib.util
        from pathlib import Path
        from types import ModuleType
        import requests
        apps=ModuleType('AppOpener');apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{};sys.modules['AppOpener']=apps
        raiz=Path.cwd();fonte_root=(raiz/'laylay.py').read_bytes()
        bloco=b'PASTA_MEMORIA = os.path.join(_base_dir, "memoria")'
        assert fonte_root.count(bloco)==1
        fonte_root=fonte_root.replace(bloco,('PASTA_MEMORIA = '+repr(str(Path(sys.argv[1])/'memoria_root'))).encode('utf8'))
        class LoaderRoot(importlib.machinery.SourceFileLoader):
            def get_code(self,nome):return compile(fonte_root,self.path,'exec')
        class FinderRoot(importlib.abc.MetaPathFinder):
            def find_spec(self,nome,path=None,target=None):
                if nome=='laylay':return importlib.util.spec_from_loader(nome,LoaderRoot(nome,str(raiz/'laylay.py')))
        sys.meta_path.insert(0,FinderRoot())
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        textos=[];efeitos=[];envios=[]
        fala=''
        forjar=False
        def http(self,method,url,**k):
            if not (str(method).upper()=='POST' and url=='http://localhost:11434/v1/chat/completions'):
                raise PermissionError('Rede externa bloqueada na simulação.')
            envios.append(k['json'])
            # Flags e comandos da proposta não podem criar prova/autoridade.
            bruto={'suporte_proposicoes':[{'texto':fala,'fontes':[]}],'comandos':[]}
            if forjar:
                bruto.update(semantica_verificada=True,prova_implicacao=True,autoriza_execucao=True,
                    comandos=[{'intent':'APP_OPEN','params':{'nome_app':'Calculadora'}}])
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':json.dumps(bruto)}}]}).encode('utf8')
            return r
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=http)
        for porta in ('_coleta_entradas_neurais','_especialista_neural_comandos_runtime',
                      '_interpretador_semantico_runtime','_pesquisa_contextual_runtime'):
            root._composicao_turno_runtime._servicos[porta]=getattr(root,porta)
        root._voz_runtime.falar=lambda *a,**k:False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f,*a,**k:textos.append(f)or True)
        from mente_laylay.autonomia import coordenador_intencao,roteador_intencao
        coordenador_intencao.executar_intencao=roteador_intencao.executar_intencao=lambda *a,**k:efeitos.append(a)or False
        estado=root._estado_compartilhado_runtime
        for fonte,pergunta,candidata in [
            ('A Bia vai levar um livro azul.','quem vai levar o livro azul?',
             'De acordo com o histórico, a Bia é quem vai levar o livro azul.'),
            ('A Dora vai levar o jogo Espiral.','quem vai levar o jogo Espiral?',
             'A Dora é quem vai levar o jogo Espiral.')]:
            for acrescimo in ('',' O livro Azul foi publicado em 1997.'):
                estado.substituir('mental',criar_estado_mental_inicial())
                estado.atualizar_campos('memoria_conversa',messages=[
                    {'role':'system','content':BASE_SYSTEM_PROMPT},{'role':'user','content':fonte}])
                fala=candidata+acrescimo;inicio=len(textos)
                root._resposta_ia_runtime.processar(pergunta,origem='teste_escopo_revisao')
                assert textos[inicio:]==[candidata],textos[inicio:]
                plano=estado.mental['plano_turno_atual']
                assert not plano['autoriza_execucao'] and not plano['comandos']
                revisao=plano['ultima_verificacao']['revisao_suporte_autoria']
                assert revisao['semantica_verificada'] is revisao['prova_implicacao'] is False
                assert revisao['pode_confirmar_fato_externo'] is revisao['autoriza_execucao'] is False
                if acrescimo:
                    assert 'data_sem_evidencia' in plano['ultima_verificacao']['problemas']
        # A proposta que viola o envelope deve ser recusada antes da revisão;
        # não usá-la como fixture positiva da fronteira factual.
        forjar=True
        estado.substituir('mental',criar_estado_mental_inicial())
        estado.atualizar_campos('memoria_conversa',messages=[
            {'role':'system','content':BASE_SYSTEM_PROMPT},
            {'role':'user','content':'A Bia vai levar um livro azul.'}])
        root._resposta_ia_runtime.processar('quem vai levar o livro azul?',origem='teste_proposta_sem_autoridade')
        plano=estado.mental['plano_turno_atual']
        assert not plano['autoriza_execucao'] and not plano['comandos']
        assert plano.get('semantica_verificada') is not True
        assert plano.get('prova_implicacao') is not True
        assert envios and not efeitos
        sys.__stdout__.write('ESCOPO_FUTURO_OK\n')
    ''')
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path)],capture_output=True,
        text=True,encoding='utf8',cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),timeout=90)
    assert r.returncode==0,r.stdout[-3500:]+r.stderr[-2000:]
