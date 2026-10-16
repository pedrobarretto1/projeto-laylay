"""Atividade real no transporte deve alcançar a política de recursos instalada."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import threading
from types import SimpleNamespace

import pytest

from mente_laylay.integracao.runtime_llm_portatil import RuntimeLLMPortatil
from mente_laylay.integracao.llm_http import LLMHttpRuntime


@pytest.fixture(scope="module")
def atividade_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("atividade_llm_instalada")
    codigo = textwrap.dedent(r'''
        import json,sys,threading
        from pathlib import Path
        from types import SimpleNamespace
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        entrou,liberar = threading.Event(),threading.Event()
        posts=[]
        def folha(sessao,method,url,*a,**k):
            posts.append({"method":method,"url":url})
            entrou.set()
            if not liberar.wait(5): raise RuntimeError("fixture não liberou transporte")
            return SimpleNamespace(status_code=200)
        root=preparar_instalacao_isolada(Path(sys.argv[1]),requisicao_http=folha)
        saida={}
        def medir(nome,target):
            entrou.clear();liberar.clear()
            resultados=[]
            t=threading.Thread(target=lambda:resultados.append(target()),daemon=True)
            t.start()
            try:
                assert entrou.wait(5),"fixture não alcançou a folha HTTP"
                caso={"atividade":root._llm_http_runtime.requisicao_local_em_andamento,
                    "atividade_consumer":root._modo_jogo_runtime.llm_em_andamento()}
                # O consumer é o instalado; só a liberação externa é isolada.
                # Cena de jogo é evidência sintética, não detecção física.
                pedido_liberacao=[]
                root._modo_jogo_runtime.descarregar_modelo=lambda:pedido_liberacao.append(True) or False
                root._modo_jogo_runtime.definir_bloqueio_llm=lambda ativo:None
                observada=root._modo_jogo_runtime.observar({"exe":"cs2.exe","title":"Counter-Strike 2"},True)
                caso.update(observada=observada,pedidos_liberacao=pedido_liberacao)
            finally:
                liberar.set();t.join(5)
            caso.update(thread_terminou=not t.is_alive(),atividade_depois=root._llm_http_runtime.requisicao_local_em_andamento)
            saida[nome]=caso
        medir("aquecimento",root._runtime_llm_portatil.preaquecer)
        # Controle interno: o mesmo consumer reconhece uma conversa HTTP.
        # Instância de política nova evita herdar o jogo sintético anterior;
        # não é a prova de ligação instalada já exercitada acima.
        from mente_laylay.percepcao.modo_jogo import ModoJogoRuntime
        root._modo_jogo_runtime=ModoJogoRuntime(definir_bloqueio_llm=lambda ativo:None,
            descarregar_modelo=lambda:False,llm_em_andamento=lambda:root._llm_http_runtime.requisicao_local_em_andamento,
            log=lambda *_:None)
        medir("conversa",lambda:root._llm_http_runtime.post({}, {"model":"fixture","messages":[],
            "_laylay_prioridade_interativa":True},timeout=3))
        ocioso=ModoJogoRuntime(definir_bloqueio_llm=lambda ativo:None,descarregar_modelo=lambda:False,
            llm_em_andamento=root._modo_jogo_runtime.llm_em_andamento,clock=lambda:10.,log=lambda *_:None)
        saida["ocioso"]=ocioso.observar({"exe":"cs2.exe","title":"Counter-Strike 2"},True)
        saida["posts"]=posts
        sys.__stdout__.write("ATIVIDADE_JSON="+json.dumps(saida)+"\n")
    ''')
    env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
        LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
        LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
        LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
        LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
    processo = subprocess.run([sys.executable,"-c",codigo,str(pasta)],
        cwd=Path(__file__).resolve().parents[2],env=env,capture_output=True,text=True,encoding="utf-8",timeout=25)
    assert processo.returncode == 0, processo.stderr
    linhas = [l for l in processo.stdout.splitlines() if l.startswith("ATIVIDADE_JSON=")]
    assert len(linhas) == 1
    return json.loads(linhas[0].split("=",1)[1])


def test_aquecimento_em_transporte_alcanca_indicador_canonico_instalado(atividade_instalada):
    caso = atividade_instalada["aquecimento"]
    assert caso["atividade"] is True, "primeira perda: infraestrutura local não chega ao indicador"
    assert caso["atividade_consumer"] is True
    assert caso["thread_terminou"] and not caso["atividade_depois"]


def test_politica_instalada_reconhece_urgencia_durante_aquecimento(atividade_instalada):
    caso = atividade_instalada["aquecimento"]
    assert caso["observada"]["jogo_confirmado"] is True, "classificação do jogo é controle"
    assert caso["observada"]["ativo"] is True, "atividade real não deve aguardar estabilidade de janela"
    assert caso["pedidos_liberacao"] == [True], "pedido de liberação não equivale a VRAM liberada"


def test_conversa_e_ociosidade_preservam_politica_de_recursos(atividade_instalada):
    caso = atividade_instalada["conversa"]
    assert caso["atividade"] and caso["atividade_consumer"]
    assert caso["observada"]["ativo"] and caso["pedidos_liberacao"] == [True]
    assert not caso["atividade_depois"] and caso["thread_terminou"]
    assert atividade_instalada["ocioso"]["jogo_confirmado"] and not atividade_instalada["ocioso"]["ativo"]


def test_atividade_nao_serializa_conversa_atras_do_aquecedor(tmp_path):
    entrou = [threading.Event(), threading.Event()]
    liberar = [threading.Event(), threading.Event()]
    resultados = []
    def folha(_url, **kwargs):
        indice = 0 if kwargs["json"]["max_tokens"] == 1 else 1
        entrou[indice].set()
        if not liberar[indice].wait(3): raise RuntimeError("fixture não liberou transporte")
        return SimpleNamespace(status_code=200)
    portatil = RuntimeLLMPortatil(raiz=tmp_path, ambiente={"LAYLAY_LLM_BACKEND":"ollama"},
        requests_post=folha,log=lambda *_:None)
    http = LLMHttpRuntime(base_url=portatil.base_url,local_timeout=3,remote_timeout=3,
        requests_post=portatil.post,atividade_local_getter=lambda:portatil.requisicao_local_em_andamento,
        print_fn=lambda *_:None)
    warm = threading.Thread(target=lambda:resultados.append(portatil.preaquecer()))
    conversa = threading.Thread(target=lambda:resultados.append(http.post({},
        {"max_tokens":8,"messages":[],"_laylay_prioridade_interativa":True},timeout=3)))
    warm.start()
    try:
        assert entrou[0].wait(1)
        assert http.requisicao_local_em_andamento
        conversa.start()
        assert entrou[1].wait(1), "nova contagem não pode criar espera de transporte"
        liberar[1].set();conversa.join(1)
        assert not conversa.is_alive()
        assert http.requisicao_local_em_andamento, "fim da conversa não encerra aquecimento ainda pendente"
    finally:
        liberar[0].set();liberar[1].set()
        warm.join(3)
        if conversa.ident is not None: conversa.join(3)
    assert not http.requisicao_local_em_andamento
    assert not portatil.requisicao_local_em_andamento and len(resultados) == 2


@pytest.mark.parametrize("resultado", [200, 503, "erro"])
def test_fim_ou_falha_do_post_limpa_atividade_sem_confirmar_prontidao(tmp_path, resultado):
    observadas = []
    def folha(_url, **_k):
        observadas.append(runtime.requisicao_local_em_andamento)
        if resultado == "erro": raise OSError("fixture")
        return SimpleNamespace(status_code=resultado)
    runtime = RuntimeLLMPortatil(raiz=tmp_path,ambiente={"LAYLAY_LLM_BACKEND":"ollama"},
        requests_post=folha,log=lambda *_:None)
    assert runtime.preaquecer() is (resultado == 200)
    assert observadas == [True]
    assert not runtime.requisicao_local_em_andamento


@pytest.mark.parametrize("backend,url", [
    ("ollama","https://localhost.evil.example/v1/chat/completions"),
    ("ollama","https://api.exemplo.invalid/v1/chat/completions"),
    ("remoto","http://localhost:11434/v1/chat/completions"),
])
def test_transporte_fora_do_recurso_local_nao_cria_ocupacao(tmp_path, backend, url):
    observadas = []
    runtime = RuntimeLLMPortatil(raiz=tmp_path,ambiente={"LAYLAY_LLM_BACKEND":backend},
        requests_post=lambda *_a,**_k:observadas.append(runtime.requisicao_local_em_andamento) or "retorno",
        log=lambda *_:None)
    assert runtime.post(url) == "retorno"
    assert observadas == [False] and not runtime.requisicao_local_em_andamento


def test_carregamento_portatil_e_observavel_sem_lock_de_lifecycle(tmp_path, monkeypatch):
    runtime = RuntimeLLMPortatil(raiz=tmp_path,ambiente={"LAYLAY_LLM_BACKEND":"portatil"},log=lambda *_:None)
    entrou,liberar = threading.Event(),threading.Event()
    erros = []
    def carregar():
        with runtime._lock:
            entrou.set()
            liberar.wait(3)
            return False
    monkeypatch.setattr(runtime,"garantir_servidor",carregar)
    def postar():
        try: runtime.post(runtime.base_url+"/chat/completions")
        except Exception as erro: erros.append(type(erro).__name__)
    thread = threading.Thread(target=postar)
    thread.start()
    try:
        assert entrou.wait(1)
        assert runtime.requisicao_local_em_andamento
    finally:
        liberar.set();thread.join(3)
    assert erros == ["ConnectionError"] and not runtime.requisicao_local_em_andamento


@pytest.mark.parametrize("estado", ["ativo","desconhecido"])
def test_idle_nao_descarrega_enquanto_infraestrutura_ativa_ou_incerta(estado):
    ativos = {"valor":True}
    timers,descargas = [],[]
    class Timer:
        def __init__(self,_delay,callback): self.callback=callback;timers.append(self)
        def start(self): pass
        def cancel(self): pass
    def atividade():
        if ativos["valor"] and estado == "desconhecido": raise OSError("fixture")
        return ativos["valor"]
    runtime = LLMHttpRuntime(base_url="http://localhost:11434/v1",local_timeout=3,remote_timeout=3,
        requests_post=lambda *_a,**_k:None,atividade_local_getter=atividade,
        ao_finalizar_conversa_modo_jogo=lambda:descargas.append(True),timer_factory=Timer,print_fn=lambda *_:None)
    runtime.definir_modo_jogo(True)
    runtime._agendar_descarregamento_jogo()
    timers[-1].callback()
    assert descargas == [] and len(timers) == 2
    ativos["valor"] = False
    timers[-1].callback()
    assert descargas == [True]


def test_getter_externo_nao_promove_endpoint_remoto_a_atividade_local():
    runtime = LLMHttpRuntime(base_url="https://api.exemplo.invalid/v1",local_timeout=3,remote_timeout=3,
        requests_post=lambda *_a,**_k:None,atividade_local_getter=lambda:True)
    assert not runtime.requisicao_local_em_andamento
