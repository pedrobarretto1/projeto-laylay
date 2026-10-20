"""Fonte de receipt pela raiz instalada: frame parcial, canônico e troca de turno.

Só serial, modelo externo, som e persistência pessoal são isolados. Os owners
de turno, executor, publicação, aprendizado e cadeia vêm de laylay.py.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


CASOS = ('parcial_movimento', 'frame_movimento', 'pipeline_movimento',
         'frame_falha', 'parcial_cadeia', 'frame_cadeia', 'pipeline_cadeia',
         'parcial_companhia', 'frame_companhia', 'pipeline_companhia',
         'tardio_mesmo_texto', 'frame_companhia_expirada', 'frame_companhia_renovada')


@pytest.fixture(scope='module', params=CASOS)
def vinculo_instalado(request, tmp_path_factory):
    pasta = tmp_path_factory.mktemp('vinculo_receipt_' + request.param)
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ['LAYLAY_VINCULO_MEMORIA_TESTE'])
        caso = os.environ['LAYLAY_VINCULO_CASO']
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or 'laylay.sqlite').name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / 'resumo'), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / 'pessoas.json', **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / 'central.json'), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + '.vinculo-' + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        from mente_laylay.cognicao.decisao_turno import motivo_divergencia_ocorrencia_turno
        from scripts.tests.test_corpo_transporte_oled import EspCorpo
        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo('', False)
        for nome in ('_coleta_entradas_neurais', '_especialista_neural_comandos_runtime', '_interpretador_semantico_runtime', '_pesquisa_contextual_runtime'):
            root._composicao_turno_runtime._servicos[nome] = None
        estado, corpo, rosto = root._estado_compartilhado_runtime, root._corpo_motor_runtime, root._rosto_oled_runtime
        esp = EspCorpo()
        rosto._config_wifi_path = rosto._config_wifi = rosto._wifi_alternativo_path = None
        rosto.identidade_usb_getter = lambda: {}
        rosto.listar_portas = lambda: ()
        rosto.porta = 'SERIAL_SIMULADO'
        rosto.autodetectar = False
        rosto.abrir_serial = lambda _: esp
        rosto.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError('TCP externo proibido'))
        corpo.companhia.perfil_corporal = 'bancada'
        corpo.companhia._automatica_ao_iniciar = corpo.companhia._ativacao_pendente = False
        root._voz_runtime.falar = lambda *_a, **_k: False
        publicacoes, textos = [], []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        adaptador = root._adaptadores_aplicacao_runtime
        publicar_original = adaptador.registrar_resultado_execucao
        def publicar(receipt, *args, **kwargs):
            mental = estado.retrato_dominio('mental')
            fonte = kwargs.get('_ocorrencia')
            motivo = motivo_divergencia_ocorrencia_turno(fonte,
                turno=mental.get('turno_atual'), plano=mental.get('plano_turno_atual'), retrato=mental.get('retrato_turno_atual'))
            retorno = publicar_original(receipt, *args, **kwargs)
            publicacoes.append({'receipt': receipt.como_dict() if hasattr(receipt, 'como_dict') else receipt,
                'origem': dataclasses.asdict(fonte) if fonte is not None else None,
                'turno': mental.get('turno_atual'), 'plano': mental.get('plano_turno_atual'),
                'retrato': mental.get('retrato_turno_atual'), 'motivo': motivo, 'aceita': retorno is not False})
            return retorno
        adaptador.registrar_resultado_execucao = publicar
        texto = ('ande para frente e pare os motores' if caso.endswith('cadeia') else
                 'ative modo companhia na bancada' if 'companhia' in caso else 'ande para frente')
        try:
            assert rosto.sincronizar()
            ciclo = root._composicao_ciclo_comandos_runtime.ciclo
            if caso.startswith('parcial'):
                estado.atualizar_campos('mental', turno_atual=classificar_modalidade_turno(texto))
            elif not caso.startswith('pipeline'):
                root._iniciar_planejamento_turno(texto, origem='teste_vinculo_receipt')
            antes = estado.retrato_dominio('mental')
            diagnostico_inicial = rosto.diagnostico()
            if caso in ('frame_companhia_expirada', 'frame_companhia_renovada'):
                # Tempo host avança sem fabricar ACK. O recebimento de outro
                # frame pelo protocolo real é a única renovação no controle.
                monotonic = rosto.monotonic
                rosto.monotonic = lambda: monotonic() + 3
            diagnostico_apos_prazo = rosto.diagnostico()
            if caso == 'frame_companhia_renovada':
                assert rosto.sincronizar()
            diagnostico_execucao = rosto.diagnostico()
            if caso.endswith('cadeia'):
                parar = rosto.parar_corpo
                def parada_falha():
                    esp.stopped = False
                    try:
                        return parar()
                    finally:
                        esp.stopped = True
                rosto.parar_corpo = parada_falha
            if caso == 'frame_falha':
                esp.mack = False
            if caso == 'tardio_mesmo_texto':
                mover = rosto.mover_corpo
                def trocar_turno(*args, **kwargs):
                    retorno = mover(*args, **kwargs)
                    root._iniciar_planejamento_turno(texto, origem='novo_turno_mesma_fala')
                    return retorno
                rosto.mover_corpo = trocar_turno
            observada = None
            if caso.startswith('pipeline'):
                root._resposta_ia_runtime.processar(texto, origem='teste_pipeline_vinculo_receipt')
                retorno = None
            elif caso.endswith('cadeia'):
                retorno = ciclo.processar_cadeia(texto, 'teste_vinculo_cadeia')
            else:
                pedido, rota = ciclo.resolver_comando_natural(texto, 'teste_vinculo')
                assert pedido, rota
                observada = ciclo.executar_intencao_observando(pedido, texto)
                retorno = observada.retorno_legado
            depois = estado.retrato_dominio('mental')
            memoria = root._motor_aprendizado_runtime.memoria
            chave = ('confiabilidade:CORPO_COMPANHIA:ativar:corpo' if 'companhia' in caso
                     else 'confiabilidade:CORPO_MOVER::corpo')
            saida = {'caso': caso, 'texto': texto, 'antes': antes, 'depois': depois,
                'retorno': retorno, 'publicacoes': publicacoes, 'textos': textos,
                'diagnostico_inicial': diagnostico_inicial, 'diagnostico_apos_prazo': diagnostico_apos_prazo,
                'diagnostico_execucao': diagnostico_execucao,
                'observada': dataclasses.asdict(observada) if observada is not None else None,
                'protocolo': esp.enviados, 'aprendizado': memoria.obter_hipotese_aprendizado(chave),
                'eventos': memoria.listar_eventos_aprendizado(chave),
                'owners': {'transporte': corpo.transporte is rosto,
                    'estado': corpo.estado is estado and corpo.experiencias.estado is estado,
                    'aprendizado': corpo.experiencias.aprendizado is root._motor_aprendizado_runtime}}
        finally:
            rosto.encerrar()
        sys.__stdout__.write('VINCULO_INSTALADO ' + json.dumps(saida, ensure_ascii=False,
            default=lambda v: dict(v) if hasattr(v, 'keys') else dataclasses.asdict(v)) + '\n')
    ''')
    processo = subprocess.run([sys.executable, '-c', codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_VINCULO_MEMORIA_TESTE=str(pasta),
                 LAYLAY_VINCULO_CASO=request.param),
        capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert processo.returncode == 0, processo.stdout[-2500:] + processo.stderr[-4500:]
    dados = json.loads(next(l.removeprefix('VINCULO_INSTALADO ')
        for l in processo.stdout.splitlines() if l.startswith('VINCULO_INSTALADO ')))
    destino = os.environ.get('LAYLAY_EVIDENCIA_VINCULO')
    if destino:
        with (Path(destino) / (request.param + '.json')).open('x', encoding='utf-8') as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return dados


def test_vinculo_e_receipt_na_composicao_instalada(vinculo_instalado):
    c = vinculo_instalado
    assert all(c['owners'].values())
    assert c['publicacoes'], 'executor deve alcançar a porta de publicação'
    if c['caso'].startswith('parcial') or c['caso'] == 'tardio_mesmo_texto':
        assert all(not p['aceita'] and p['motivo'] for p in c['publicacoes'])
        assert not c['aprendizado'] and not c['eventos']
        assert not c['depois'].get('ultima_acao_contrato')
        assert c['depois']['resultados_execucao_tardios']
        if c['caso'] == 'tardio_mesmo_texto':
            assert c['antes']['turno_atual']['id'] != c['depois']['turno_atual']['id']
            assert c['antes']['turno_atual']['texto'] == c['depois']['turno_atual']['texto']
        return
    assert all(p['aceita'] and not p['motivo'] for p in c['publicacoes'])
    assert c['aprendizado'] and c['eventos']
    r = c['depois']['ultima_acao_contrato']
    if c['caso'].endswith('cadeia'):
        assert [p['receipt']['intent'] for p in c['publicacoes']] == ['CORPO_MOVER', 'CORPO_PARAR']
        assert r['intent'] == 'CORPO_PARAR' and r['confirmado'] is False
        assert len({p['receipt']['id_solicitacao'] for p in c['publicacoes']}) == 2
        assert len(c['textos']) == 1
    else:
        assert r['intent'] == ('CORPO_COMPANHIA' if 'companhia' in c['caso'] else 'CORPO_MOVER')
        assert r['confirmado'] is (c['caso'] not in ('frame_falha', 'frame_companhia_expirada'))
    if c['caso'] in ('frame_companhia_expirada', 'frame_companhia_renovada'):
        assert c['diagnostico_inicial']['aplicacao_confirmada'] is True
        assert c['diagnostico_apos_prazo']['aplicacao_confirmada'] is False
        assert c['diagnostico_execucao']['aplicacao_confirmada'] is (c['caso'] == 'frame_companhia_renovada')
