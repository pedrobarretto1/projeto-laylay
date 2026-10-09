"""Coleta finita no root instalado e reinício real com SQLite isolado.

Publicação textual e voz silenciosa são reais. Conteúdo da resposta é entrada
controlada, não autoria da LLM; nenhum executor externo ou áudio é utilizado.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


CODIGO = r'''
import json, os, sys, time, threading
from pathlib import Path
from datetime import datetime
from memoria_sqlite import MemoriaSQLite
from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
from mente_laylay.integracao import instancia_unica
pasta = Path(os.environ['LAYLAY_P20_GRADUAL_TESTE'])
init_sql = MemoriaSQLite.__init__
MemoriaSQLite.__init__ = lambda self, caminho=None: init_sql(self, str(pasta / Path(caminho or 'memoria.sqlite').name))
init_resumo = MemoriaLaylay.__init__
MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: init_resumo(self, pasta_memoria=str(pasta / 'resumo'), **k)
init_pessoas = MemoriaPessoasRuntime.__init__
MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: init_pessoas(self, caminho=pasta / 'pessoas.json', **k)
init_central = CentralNotificacoesRuntime.__init__
CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: init_central(self, str(pasta / 'central.json'), **k)
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident)+'.p20-gradual-'+str(os.getpid()), **k)
import laylay as root
sys.excepthook = sys.__excepthook__
sys.tracebacklimit = 100
import traceback
sys.excepthook = lambda tipo, erro, tb: traceback.print_exception(tipo, erro, tb, limit=100)
from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
from mente_laylay.personalidade.perfil_amizade import selecionar_postura_amizade
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
modelo = []
def proibido(*a, **k):
    modelo.append('modelo')
    raise AssertionError('esta coleta não pode chamar modelo')
RegistroModeloLLM.executar = proibido
estado = root._estado_compartilhado_runtime
motor = root._motor_aprendizado_runtime
diretor = root._diretor_presenca_runtime
orq = root._orquestrador_fala_runtime
root._voz_runtime.definir_modo_silencioso(True, origem='teste_p20_gradual')
textos = []
orq.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto))
threads_iniciais = {id(t) for t in threading.enumerate()}
ctx_resposta = root._resposta_ia_runtime._contexto_getter()
assert ctx_resposta['observar_feedback_presenca'].__self__ is diretor, 'callback de entrada não é Diretor'
assert orq._servicos['_registrar_entrega_comunicativa'].__self__ is diretor, 'callback de entrega não é Diretor'
assert root._ponte_iniciativa_aplicacao_runtime._registrar_feedback_compartilhado.__self__ is root._adaptadores_aplicacao_runtime, 'callback de aprendizado não é Adaptador instalado'
assert root._adaptadores_aplicacao_runtime._ns()['_motor_aprendizado_runtime'] is motor
saida = {'owners': True, 'casos': {}, 'pid': os.getpid(), 'db': motor.memoria.db_path}
def iniciar(contexto, texto=None):
    root._modo_jogo_runtime._ativo = contexto == 'jogo'
    root._iniciar_planejamento_turno(texto or ('abra a calculadora' if contexto == 'comandos' else 'oi'), origem='terminal')
    return dict(estado.mental.get('preferencia_humor_contextual') or {})
def contar(contexto):
    return len(motor.memoria.listar_eventos_aprendizado('personalidade:tolerancia_humor_implicita:'+contexto))
if os.environ['LAYLAY_P20_GRADUAL_MODO'] == 'emitir':
    for contexto in ('jogo','conversa','comandos'):
        estado.substituir('mental', {})
        etapas = []
        for n in range(3):
            iniciar(contexto)
            orq.falar('Essa foi uma brincadeira de teste.')
            emissao = dict(estado.mental['presenca_contextual']['ultima_emissao'])
            assert emissao['contexto_humor'] == contexto
            # Contexto perceptivo mudou antes de receber o feedback.
            root._modo_jogo_runtime._ativo = contexto != 'jogo'
            retorno = ctx_resposta['observar_feedback_presenca']('Essa piada passou do ponto.')
            assert retorno['resultado'] == 'correcao'
            replay = ctx_resposta['observar_feedback_presenca']('Essa piada passou do ponto.')
            etapas.append({'amostras': contar(contexto), 'replay': replay,
                'preferencia': motor.carregar_preferencia_humor_duravel(contexto),
                'entrega': emissao})
        preferencia = iniciar(contexto)
        postura = selecionar_postura_amizade('oi', estado_mental=estado.mental, operacional=contexto=='comandos')
        receipt = ResultadoAcao(intent='IOT_CONTROL',status='brilho_ajustado',alvo='lâmpada',executou=True,confirmado=True)
        plano = planejar_resposta_acao(receipt,'Ajustei o brilho de lâmpada para 27%.',
            contexto=estado.mental if contexto=='comandos' else None, emocao_preferida='debochada')
        saida['casos'][contexto] = {'etapas': etapas, 'preferencia': preferencia,
            'humor': postura.humor, 'fala': plano.fala, 'receipts': estado.mental.get('ultima_acao_contrato')}
    iniciar('jogo', 'pode me zoar mais hoje')
    saida['explicita'] = iniciar('jogo')
    # Feedback factual em uma nova entrega continua genérico.
    iniciar('conversa')
    orq.falar('Essa foi uma resposta factual de teste.')
    antes = contar('conversa')
    ctx_resposta['observar_feedback_presenca']('Não, Lay. O número da dica está errado.')
    saida['negativo_factual'] = (contar('conversa') == antes)
else:
    for contexto in ('jogo','conversa','comandos'):
        preferencia = iniciar(contexto)
        saida['casos'][contexto] = {'amostras': contar(contexto), 'preferencia': preferencia}
    motor.maturidade.agora = lambda: datetime.fromtimestamp(time.time()+15*86400)
    saida['expirada'] = iniciar('comandos')
saida['diagnostico'] = motor.diagnostico_tolerancia_humor()
saida['modelo'] = modelo
saida['audio_enfileirado'] = root._voz_runtime.fila.qsize()
saida['threads_novas'] = [t.name for t in threading.enumerate() if id(t) not in threads_iniciais]
sys.__stdout__.write('P20_GRADUAL '+json.dumps(saida, ensure_ascii=False)+'\n')
sys.__stdout__.flush()
'''


def _executar(pasta, modo):
    processo = subprocess.run([sys.executable, "-c", CODIGO],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, LAYLAY_P20_GRADUAL_TESTE=str(pasta), LAYLAY_P20_GRADUAL_MODO=modo,
            LAYLAY_AUDIO_SILENCIOSO="1", LAYLAY_NEURAL_COLETA_ENTRADAS="0"),
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert processo.returncode == 0, processo.stderr[-6000:] + processo.stdout[-2500:]
    linhas = [l.removeprefix("P20_GRADUAL ") for l in processo.stdout.splitlines() if l.startswith("P20_GRADUAL ")]
    assert len(linhas) == 1, processo.stdout[-2500:] + processo.stderr[-1000:]
    return json.loads(linhas[0])


@pytest.fixture(scope="module")
def coleta(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("p20_gradual_instalada")
    rodadas = _executar(pasta, "emitir"), _executar(pasta, "reiniciar")
    evidencia = os.environ.get("LAYLAY_P20_EVIDENCIA_DIR")
    if evidencia:
        destino = Path(evidencia)
        assert destino.is_absolute() and destino.is_dir()
        (destino / "coleta_instalada.json").write_text(
            json.dumps(rodadas, ensure_ascii=False, indent=2), encoding="utf-8")
    return rodadas


def test_owners_instalados_sem_modelo_audio_efeito_ou_background(coleta):
    for rodada in coleta:
        assert rodada["owners"] is True
        assert rodada["modelo"] == []
        assert rodada["audio_enfileirado"] == 0
        assert rodada["threads_novas"] == []


@pytest.mark.parametrize("contexto", ["jogo", "conversa", "comandos"])
def test_entrega_feedback_memoria_maturidade_e_consumo_no_root(coleta, contexto):
    caso = coleta[0]["casos"][contexto]
    for n, etapa in enumerate(caso["etapas"]):
        assert etapa["amostras"] == n+1
        assert etapa["replay"] == {}
        assert etapa["entrega"]["canal_entrega"] == "texto_publicado"
        assert etapa["entrega"]["contexto_humor"] == contexto
        if n < 2:
            assert etapa["preferencia"] == {}
    assert caso["preferencia"]["direcao"] == "leve"
    assert caso["preferencia"]["contexto"] == contexto
    assert caso["preferencia"]["autoriza_execucao"] is False
    assert caso["humor"] == "bloqueado"
    assert caso["receipts"] is None, "aprender expressão não executa o pedido de controle"
    if contexto == "comandos":
        assert caso["fala"] == "Ajustei o brilho de lâmpada para 27%."


@pytest.mark.parametrize("contexto", ["jogo", "conversa", "comandos"])
def test_segundo_processo_reconstroi_proveniencia_sem_cache(coleta, contexto):
    assert coleta[0]["pid"] != coleta[1]["pid"]
    assert coleta[0]["db"] == coleta[1]["db"]
    caso = coleta[1]["casos"][contexto]
    assert caso["amostras"] == 3
    assert caso["preferencia"]["origem"] == "tolerancia_implicita"
    assert caso["preferencia"]["direcao"] == "leve"


def test_preferencia_explicita_prevalece_factual_nao_calibra_e_expiracao_limpa_cache(coleta):
    assert coleta[0]["explicita"]["origem"] == "usuario_explicito"
    assert coleta[0]["explicita"]["direcao"] == "mais_humor"
    assert coleta[0]["negativo_factual"] is True
    assert coleta[1]["expirada"] == {}


def test_diagnostico_nao_expoe_literais_ou_rotulo_da_pessoa(coleta):
    diagnostico = coleta[0]["diagnostico"]
    assert diagnostico["autoriza_execucao"] is False
    assert diagnostico["minimo_entregas"] == 3
    assert set(diagnostico["contextos"]) == {"jogo", "conversa", "comandos"}
    assert "piada" not in json.dumps(diagnostico)
