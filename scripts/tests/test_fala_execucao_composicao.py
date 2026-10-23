"""Composição instalada e disco reais; entrada determinística e voz silenciosa."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_objetivo_com_duas_habilidades_preserva_receipts_e_conclusoes(tmp_path):
    codigo = textwrap.dedent(r'''
        import json, sys
        from pathlib import Path
        from scripts.validar_fala_execucao_real import carregar_composicao
        pasta = Path(sys.argv[1])
        root = carregar_composicao(pasta)
        root._voz_runtime.definir_modo_silencioso(True, origem='teste_explicito')
        fonte = {'texto': 'Conteúdo de estudo controlado para o objetivo cooperativo.'}
        # Só a porta de leitura do SO é controlada; a habilidade de clipboard,
        # o quadro, a governança, a voz, o ciclo e o executor de arquivo são reais.
        root._area_transferencia_runtime.leitor = lambda: fonte['texto']
        falas, entregas = [], []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda texto, *_a, **_k: falas.append(texto) or True)
        root._orquestrador_fala_runtime.registrar_observador_entrega_resultados(
            lambda **dados: entregas.extend(dados['resultados']))
        def executar(nome, destino=pasta):
            pedido=f'salva o que eu copiei em um arquivo chamado {nome} dentro da pasta {destino}'
            root._coordenador_exec_runtime.processar_sync(pedido, origem='terminal')
            return root._quadro_cooperacao_runtime.snapshot()['planos_recentes'][-1]
        sucesso = executar('estudo')
        assert (pasta/'estudo.txt').read_text(encoding='utf-8') == fonte['texto']
        assert sucesso['estado']=='confirmado'
        assert len(falas)==2 and falas[0].startswith('Vou ')
        assert len(entregas)==1 and entregas[0].origem=='executor' and entregas[0].id_solicitacao
        assert entregas[0].params['plano_cooperativo_id']==sucesso['id']
        idempotente = executar('estudo')
        assert idempotente['estado']=='confirmado' and len(entregas)==1
        barreira=pasta/'pai.txt'
        barreira.write_text('pai é arquivo',encoding='utf-8')
        falha = executar('falha',barreira)
        assert falha['estado']=='falhou'
        assert [e['estado'] for e in falha['etapas']]==['confirmado','falhou']
        assert not falha['resultado']['confirmado']
        assert 'Não consegui' in falas[-1]
        assert entregas[-1].confirmado is False
        original=root._orquestrador_cooperativo_runtime.anunciar_etapa
        def cancelar(plano,etapa,**_):
            root._quadro_cooperacao_runtime.solicitar_cancelamento(plano['id'])
        root._orquestrador_cooperativo_runtime.anunciar_etapa=cancelar
        cancelado=executar('cancelado')
        assert cancelado['estado']=='cancelado' and not (pasta/'cancelado.txt').exists()
        assert 'cancelado' in falas[-1]
        root._orquestrador_cooperativo_runtime.anunciar_etapa=original
        negativos=[]
        for pedido in ('não salva o que copiei em um arquivo chamado negado',
                       'você consegue salvar o que copiei em um arquivo chamado negado?'):
            negativos.append(root._orquestrador_cooperativo_runtime.processar(pedido))
        assert negativos==[False,False] and not (pasta/'negado.txt').exists()
        registro=root._estado_compartilhado_runtime.mental.get('registro_semantico') or {}
        assert any(f.get('resultados') for f in registro.get('falas_observadas',[]))
        print('FALA_EXECUCAO_JSON='+json.dumps({'sucesso':sucesso['estado'], 'falha':falha['estado'],
            'cancelamento':cancelado['estado'], 'idempotente':idempotente['estado'],
            'receipts_entregues':len(entregas), 'conteudo_temporario':fonte['texto'] not in str(sucesso)}))
    ''')
    ambiente = dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off',
                    LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS=str(tmp_path))
    processo = subprocess.run([sys.executable, '-c', codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2], env=ambiente, capture_output=True,
        text=True, encoding='utf-8', timeout=90)
    assert processo.returncode == 0, processo.stdout[-3500:] + processo.stderr[-2000:]
    linha = next(l for l in processo.stdout.splitlines() if l.startswith('FALA_EXECUCAO_JSON='))
    dados = json.loads(linha.split('=', 1)[1])
    assert dados['conteudo_temporario'] is True
