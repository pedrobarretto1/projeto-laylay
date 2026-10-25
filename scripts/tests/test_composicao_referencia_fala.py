"""Identidade atravessa entrega, mente curta, turno e juiz instalados."""
from pathlib import Path
import os
import subprocess
import sys
import textwrap


def test_fala_longa_observada_chega_inteira_a_revisao_na_instalacao(tmp_path):
    codigo = textwrap.dedent(r'''
        from pathlib import Path
        import json, sys
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(Path(sys.argv[1]))
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta
        from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta, recuperar_evidencia_da_fala
        from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
        from mente_laylay.autonomia import coordenador_intencao
        fala = 'Acho importante terminar os exercícios, porque isso ajuda a praticar.' + ' Conferir cada etapa ajuda a localizar dúvidas.' * 16
        estado = root._estado_compartilhado_runtime
        publicadas, executores = [], []
        root._voz_runtime.falar = lambda *a, **k: False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda fala, *a, **k: publicadas.append(fala) or True)
        coordenador_intencao.executar_intencao = lambda *a, **k: executores.append(a) or False
        RegistroModeloLLM.executar = lambda *a, **k: ResultadoModelo(json.dumps({'fala':fala, 'comandos':[]}), True)
        root._iniciar_planejamento_turno('o que você acha disso?', origem='teste_identidade')
        root.falar_com_lipsync(fala)
        estado.atualizar('mental', lambda mente: registrar_mente_curta(mente,
            resposta_ia=fala, texto_usuario='o que você acha disso?', log=lambda *_: None))
        antes = recuperar_evidencia_da_fala('como assim?', dict(estado.mental))
        assert antes and antes['falas'][0]['fala'] == fala
        origem = antes['falas'][0]['id']
        assert len(estado.mental['ultima_resposta']) <= 180
        root._resposta_ia_runtime.processar('como  assim?', origem='teste_identidade')
        plano = dict(estado.mental['plano_turno_atual'])
        fonte = plano['contrato_fala'].get('referencia_fala_observada')
        assert isinstance(fonte, ReferenciaFalaConsulta)
        assert fonte.ocorrencia_id == origem and fonte.conteudo == fala
        revisao = avaliar_qualidade_comunicacao('como  assim?', fala, plano=plano)
        assert not revisao['aceita']
        assert 'esclarecimento_sem_explicacao' in revisao['problemas_bloqueantes']
        assert executores == [] and len(publicadas) == 2 and publicadas[-1] != fala
    ''')
    p = subprocess.run([sys.executable, '-c', codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert p.returncode == 0, p.stdout[-3500:] + p.stderr[-2500:]
