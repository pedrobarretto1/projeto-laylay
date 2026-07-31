from __future__ import annotations

from types import SimpleNamespace

import requests

from mente_laylay.integracao.runtime_llm_portatil import RuntimeLLMPortatil


class ProcessoFake:
    def __init__(self) -> None:
        self.terminado = False
        self.morto = False

    def poll(self):
        return 0 if self.terminado else None

    def terminate(self) -> None:
        self.terminado = True

    def wait(self, timeout=None) -> int:
        return 0

    def kill(self) -> None:
        self.morto = True
        self.terminado = True


def _arquivos_portateis(tmp_path):
    servidor = tmp_path / "runtime_llm" / "cpu" / "llama-server.exe"
    servidor.parent.mkdir(parents=True)
    servidor.write_bytes(b"exe")
    modelo = tmp_path / "modelos" / "laylay-qwen3-4b-q4_k_m.gguf"
    modelo.parent.mkdir(parents=True)
    modelo.write_bytes(b"GGUFmodelo")
    return servidor, modelo


def test_auto_em_codigo_fonte_preserva_ollama(tmp_path) -> None:
    runtime = RuntimeLLMPortatil(raiz=tmp_path, ambiente={})

    assert runtime.backend == "ollama"
    assert runtime.base_url == "http://localhost:11434/v1"


def test_backend_portatil_inicia_sob_demanda_e_repassa_post(tmp_path) -> None:
    servidor, modelo = _arquivos_portateis(tmp_path)
    processos: list[ProcessoFake] = []
    comandos: list[tuple] = []
    posts: list[tuple] = []

    def popen(comando, **kwargs):
        comandos.append((comando, kwargs))
        processo = ProcessoFake()
        processos.append(processo)
        return processo

    def get(*_args, **_kwargs):
        return SimpleNamespace(status_code=200 if processos else 503)

    runtime = RuntimeLLMPortatil(
        raiz=tmp_path,
        ambiente={"LAYLAY_LLM_BACKEND": "portatil"},
        requests_get=get,
        requests_post=lambda url, **kwargs: posts.append((url, kwargs)) or "ok",
        popen=popen,
        sleep=lambda _s: None,
    )

    retorno = runtime.post("http://127.0.0.1:11435/v1/chat/completions", json={})

    assert retorno == "ok"
    assert comandos
    assert comandos[0][0][0] == str(servidor)
    assert str(modelo) in comandos[0][0]
    assert "-ngl" in comandos[0][0]
    assert posts[0][0].endswith("/v1/chat/completions")

    runtime.encerrar()
    assert processos[0].terminado is True


def test_runtime_portatil_sem_modelo_falha_sem_criar_processo(tmp_path) -> None:
    servidor = tmp_path / "runtime_llm" / "cpu" / "llama-server.exe"
    servidor.parent.mkdir(parents=True)
    servidor.write_bytes(b"exe")
    chamadas: list[bool] = []
    runtime = RuntimeLLMPortatil(
        raiz=tmp_path,
        ambiente={"LAYLAY_LLM_BACKEND": "portatil"},
        requests_get=lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError()),
        popen=lambda *_args, **_kwargs: chamadas.append(True),
    )

    assert runtime.garantir_servidor() is False
    assert chamadas == []

    try:
        runtime.post("http://127.0.0.1:11435/v1/chat/completions")
    except requests.exceptions.ConnectionError:
        pass
    else:
        raise AssertionError("post deveria informar motor portátil indisponível")


def test_configuracao_explicita_de_modelo_e_endpoint_tem_prioridade(tmp_path) -> None:
    modelo = tmp_path / "meu.gguf"
    runtime = RuntimeLLMPortatil(
        raiz=tmp_path,
        ambiente={
            "LAYLAY_LLM_BACKEND": "remote",
            "LAYLAY_LLM_BASE_URL": "http://maquina:9000/v1/",
            "LAYLAY_LLM_MODEL_PATH": str(modelo),
            "LAYLAY_LLM_MODEL": "laylay-teste",
        },
    )

    assert runtime.backend == "remoto"
    assert runtime.base_url == "http://maquina:9000/v1"
    assert runtime.caminho_modelo == modelo
    assert runtime.modelo == "laylay-teste"
