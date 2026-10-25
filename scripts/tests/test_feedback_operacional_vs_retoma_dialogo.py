"""Um sinal de resultado não vincula uma pergunta nova à última tentativa."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time

import pytest

from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.memoria_mental.continuidade_conversa import detectar_comentario_resultado_operacional
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


PERGUNTA_HISTORICA = "então, como ficou o nosso plano depois das mudanças?"


def _estado(intent: str = "APP_OPEN", confirmado: bool = False) -> dict:
    alvos = {"APP_OPEN": "aplicativo bloco de notas", "IOT_CONTROL": "lâmpada do quarto",
             "CREATE_FILE": "resumo.txt", "PLAYLIST_PLAY": "playlist de estudo"}
    resultado = ResultadoAcao(intent=intent, params={"alvo": alvos[intent]},
        alvo=alvos[intent], status="executado" if confirmado else "falha_execucao",
        executou=confirmado, confirmado=confirmado, origem="diagnostico_sem_efeitos")
    return registrar_resultado_execucao({}, resultado)


@pytest.mark.parametrize("intent", ["APP_OPEN", "IOT_CONTROL", "CREATE_FILE", "PLAYLIST_PLAY"])
@pytest.mark.parametrize("confirmado", [False, True])
def test_pergunta_nova_nao_herda_alvo_da_ultima_tentativa(intent, confirmado):
    estado = _estado(intent, confirmado)
    turno = classificar_modalidade_turno(PERGUNTA_HISTORICA)
    assert turno["ato_principal"] == "pergunta"
    assert turno["autoriza_execucao"] is False
    assert detectar_comentario_resultado_operacional(PERGUNTA_HISTORICA, estado) is None


@pytest.mark.parametrize("texto", [
    "Como ficou a divisão de tarefas?",
    "Qual foi o resultado do nosso planejamento?",
    "Por que meu desenho ficou estranho?",
    "O que parece melhor para o nosso jogo?",
    "Como ficou isso?",
    "Me explica por que esse resultado ficou errado.",
    "ficou melhor, mas como ficou nosso plano?",
    "não funcionou, tenta de novo",
    "meu plano ficou melhor",
    "O programa abriu?",
])
def test_pergunta_ou_instrucao_nova_nao_e_feedback_so_por_sinal_lexical(texto):
    assert detectar_comentario_resultado_operacional(texto, _estado()) is None


@pytest.mark.parametrize("texto", ["ficou melhor", "não funcionou", "isso aí ficou estranho"])
@pytest.mark.parametrize("confirmado", [False, True])
def test_feedback_curto_permanece_ligado_a_tentativa_sem_fabricar_confirmacao(texto, confirmado):
    estado = _estado(confirmado=confirmado)
    antes = dict(estado["ultima_acao_contrato"])
    comentario = detectar_comentario_resultado_operacional(texto, estado)
    assert comentario is not None
    assert comentario["alvo"] == "aplicativo bloco de notas"
    assert estado["ultima_acao_contrato"] == antes
    assert estado["ultima_acao_confirmada"] is confirmado


@pytest.mark.parametrize("confirmado", [False, True])
def test_pergunta_sobre_autoria_preserva_status_real_da_tentativa(confirmado):
    comentario = detectar_comentario_resultado_operacional("por que você abriu o programa?", _estado(confirmado=confirmado))
    assert comentario["tipo"] == "questiona_autoria"
    assert comentario["confirmado"] is confirmado
    assert comentario["executou"] is confirmado


def test_feedback_sem_tentativa_ou_expirado_nao_consumido():
    assert detectar_comentario_resultado_operacional("ficou melhor", {}) is None
    estado = _estado()
    estado["ultima_acao_ts"] = time.time() - 300
    assert detectar_comentario_resultado_operacional("ficou melhor", estado) is None


@pytest.mark.parametrize("referencia", [{}, {"nome": "nosso plano"}])
def test_pronome_sem_binding_canonico_nao_herda_alvo_operacional(referencia):
    estado = _estado()
    estado["turno_atual"] = {**classificar_modalidade_turno("ele ficou estranho"),
                             "texto": "ele ficou estranho", "referencia_resolvida": referencia}
    assert detectar_comentario_resultado_operacional("ele ficou estranho", estado) is None


def test_pronome_vinculado_ao_alvo_do_resultado_e_comentario():
    estado = _estado(confirmado=True)
    estado["turno_atual"] = {**classificar_modalidade_turno("ele ficou estranho"),
        "texto": "ele ficou estranho", "referencia_resolvida": {"nome": "aplicativo bloco de notas"}}
    assert detectar_comentario_resultado_operacional("ele ficou estranho", estado) is not None


def test_sujeito_literal_do_resultado_pode_receber_feedback():
    assert detectar_comentario_resultado_operacional(
        "o aplicativo bloco de notas ficou estranho", _estado(confirmado=True)) is not None


def test_foco_antigo_nao_pode_mentir_sobre_o_ato_da_pergunta_atual():
    estado = _estado()
    estado["turno_atual"] = {"texto": "ficou melhor", "atos": ["conversa"], "modalidade": "conversa"}
    assert detectar_comentario_resultado_operacional(PERGUNTA_HISTORICA, estado) is None


def test_pre_fluxo_deixa_pergunta_nova_seguir_sem_fala_nem_suspensao():
    falas, suspensoes = [], []
    estado = _estado()
    estado["turno_atual"] = classificar_modalidade_turno(PERGUNTA_HISTORICA)
    contexto = {"mente_integrada_estado": estado,
        "_emitir_resposta_curta": lambda texto, fala, **kw: falas.append(fala) or True,
        "_suspender_topico_conversacional": suspensoes.append}
    assert processar_inicio_fluxo_resposta_ia(contexto, PERGUNTA_HISTORICA) is False
    assert not suspensoes
    assert not falas


@pytest.fixture(scope="module")
def retoma_instalada(tmp_path_factory):
    codigo = textwrap.dedent(r'''
        import json,sys
        from pathlib import Path
        from types import ModuleType,SimpleNamespace
        import requests
        apps=ModuleType('AppOpener')
        apps.open=apps.close=lambda *a,**k:False
        apps.give_appnames=lambda *a,**k:{}
        sys.modules['AppOpener']=apps
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
        from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
        from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
        enviados=[]
        def http(self,method,url,**kw):
            payload=kw.get('json') or {};enviados.append(payload)
            conteudo=json.dumps({'suporte_proposicoes':[{'texto':
                'O plano ficou assim: você faz a música e o Leo faz os desenhos.','fontes':[]}],
                'emocao':'calma','nivel_emocao':1,'comandos':[]})
            r=requests.Response();r.status_code=200
            r._content=json.dumps({'choices':[{'message':{'content':conteudo}}]}).encode('utf8')
            return r
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=http)
        # A entrega textual deve ser observável: recusar toda publicação
        # faria o pré-fluxo devolver False por falha do sink, mascarando o RED.
        falas=[]
        fala_owner=root._orquestrador_fala_runtime
        fala_owner._servicos['_voz_runtime']=SimpleNamespace(falar=lambda *a,**k:True)
        fala_owner._observadores_texto_final=[lambda fala,*a,**k:falas.append(fala) or True]
        fala_owner._observadores_fala_final=[]
        estado,runtime=root._estado_compartilhado_runtime,root._resposta_ia_runtime
        original=runtime._contexto_getter
        efeitos=[]
        from mente_laylay.autonomia import coordenador_intencao
        coordenador_intencao.executar_intencao=lambda *a,**k:efeitos.append(str(a)) or False
        casos=[]
        for confirmado in [False,True]:
            receipt=ResultadoAcao(intent='APP_OPEN',params={'nome_app':'aplicativo bloco de notas'},
                alvo='aplicativo bloco de notas',status='app_iniciado_focado' if confirmado else 'falha_execucao',
                executou=confirmado,confirmado=confirmado,origem='diagnostico_sem_efeitos')
            from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
            estado.substituir('mental',estado_mental_inicial())
            root._registrar_resultado_execucao_base(receipt,'abre o aplicativo Bloco de Notas')
            estado.atualizar_campos('memoria_conversa',messages=[{'role':'system','content':BASE_SYSTEM_PROMPT},
                {'role':'user','content':'Eu e Leo estamos planejando um jogo. Minha parte é o desenho.'},
                {'role':'assistant','content':'Vocês dividiram desenho e música.'},
                {'role':'user','content':'Mudamos: a música agora será minha e o Leo desenha.'}])
            ctx=original();ctx['usar_modo_rapido']=lambda t:False
            fronteiras=[]
            pre_fluxo_original=ctx['processar_inicio_fluxo']
            def medir_pre_fluxo(contexto,texto):
                antes=dict(contexto.get('mente_integrada_estado') or {})
                retorno=pre_fluxo_original(contexto,texto)
                fronteiras.append({'intent_antes':antes.get('ultima_acao_intent'),
                    'ts_antes':antes.get('ultima_acao_ts'),
                    'intent_depois':(contexto.get('mente_integrada_estado') or {}).get('ultima_acao_intent'),
                    'tratado':retorno})
                return retorno
            ctx['processar_inicio_fluxo']=medir_pre_fluxo
            ctx['contexto_dispatch_runtime']=SimpleNamespace(montar=lambda:{'executar_intencao':lambda *a,**k:efeitos.append(str(a)) or False})
            runtime._contexto_getter=lambda:ctx
            pergunta='então, como ficou o nosso plano depois das mudanças?'
            inicio=len(enviados)
            inicio_falas=len(falas)
            runtime.processar(pergunta,origem='teste_retoma_instalada')
            casos.append({'confirmado':confirmado,'pergunta':pergunta,'envios':enviados[inicio:],
                'turno':dict(estado.mental.get('turno_atual') or {}),'efeitos':list(efeitos),
                'fronteiras':fronteiras,'falas':falas[inicio_falas:]})
        sys.__stdout__.write('RETOMA_INSTALADA '+json.dumps(casos,ensure_ascii=False,default=str)+'\n')
    ''')
    r = subprocess.run([sys.executable, "-B", "-c", codigo, str(tmp_path_factory.mktemp("retoma_instalada"))],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding="utf8",
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off"), timeout=100)
    assert r.returncode == 0, r.stdout[-3500:] + r.stderr[-2500:]
    casos = json.loads(next(l.removeprefix("RETOMA_INSTALADA ") for l in r.stdout.splitlines()
        if l.startswith("RETOMA_INSTALADA ")))
    if destino := os.environ.get("LAYLAY_EVIDENCIA_RETOMA"):
        Path(destino).write_text(json.dumps(casos, ensure_ascii=False, indent=2), encoding="utf8")
    return casos


@pytest.mark.parametrize("indice", [0, 1])
def test_factory_leva_pergunta_nova_a_autoria_sem_emprestar_alvo_operacional(retoma_instalada, indice):
    caso = retoma_instalada[indice]
    assert caso["turno"]["autoriza_execucao"] is False
    assert not caso["efeitos"]
    principais = [p for p in caso["envios"] if (p.get("messages") or [{}])[-1].get("content") == caso["pergunta"]]
    assert principais, "a pergunta nova foi consumida antes da porta de autoria instalada"
    assert len(caso["falas"]) == 1, "a pergunta precisa de uma conclusão observável única"
    assert caso["falas"][0] == "O plano ficou assim: você faz a música e o Leo faz os desenhos."
