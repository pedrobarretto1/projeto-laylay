from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from mente_laylay.integracao.configuracao_aplicacao import (
    ConfiguracaoAplicacaoRuntime,
    ErroConfiguracaoAplicacao,
    OPENROUTER_URL,
    carregar_segredo_no_ambiente,
)


class DPAPIFalso:
    def CryptProtectData(self, dados, *_args):
        return ("descrição", b"dpapi:" + bytes(dados)[::-1])

    def CryptUnprotectData(self, dados, *_args):
        bruto = bytes(dados)
        assert bruto.startswith(b"dpapi:")
        return ("descrição", bruto[6:][::-1])


class DPAPIIndisponivel:
    def CryptProtectData(self, _dados, *_args):
        raise OSError("não disponível")


class RespostaCatalogo:
    def __init__(self, endpoints=None, status_code: int = 200):
        self.status_code = status_code
        self._endpoints = [{"provider_name": "teste"}] if endpoints is None else endpoints

    def json(self):
        return {"data": {"endpoints": self._endpoints}}


def catalogo_ativo(*_args, **_kwargs):
    return RespostaCatalogo()


@pytest.fixture
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_LLM_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_MASCOT_ENABLED", raising=False)
    return ConfiguracaoAplicacaoRuntime(
        raiz=tmp_path,
        caminho_segredo=tmp_path / "privado" / "openrouter.dpapi",
        win32crypt_mod=DPAPIFalso(),
        requests_get=catalogo_ativo,
    )


def test_salva_env_atomicamente_preservando_comentarios_e_chaves(runtime) -> None:
    runtime.arquivo_env.write_text(
        "# arquivo privado\nOUTRA_CHAVE=preservar\nLAYLAY_LLM_MODEL=antigo\n",
        encoding="utf-8",
    )
    resultado = runtime.atualizar({
        "provider": "ollama", "model": "qwen3:4b",
        "api_key_action": "preserve", "api_key": "",
    })
    texto = runtime.arquivo_env.read_text(encoding="utf-8")
    assert "# arquivo privado" in texto
    assert "OUTRA_CHAVE=preservar" in texto
    assert "LAYLAY_LLM_BACKEND=ollama" in texto
    assert "LAYLAY_LLM_BASE_URL=http://localhost:11434/v1" in texto
    assert "LAYLAY_LLM_MODEL=qwen3:4b" in texto
    assert resultado["saved"] is True
    assert resultado["restart_required"] is True


def test_mascote_e_desligado_por_padrao_e_persistido_com_tipo(runtime) -> None:
    assert runtime.estado()["mascot_enabled"] is False

    resultado = runtime.atualizar({
        "provider": "ollama", "model": "qwen3:4b",
        "api_key_action": "preserve", "api_key": "",
        "mascot_enabled": True,
    })
    assert "LAYLAY_MASCOT_ENABLED=1" in runtime.arquivo_env.read_text(encoding="utf-8")
    assert resultado["settings"]["mascot_enabled"] is True
    assert resultado["restart_required"] is True

    runtime.atualizar({
        "provider": "ollama", "model": "qwen3:4b",
        "api_key_action": "preserve", "api_key": "",
        "mascot_enabled": False,
    })
    assert runtime.estado()["mascot_enabled"] is False
    assert "LAYLAY_MASCOT_ENABLED=0" in runtime.arquivo_env.read_text(encoding="utf-8")

    with pytest.raises(ErroConfiguracaoAplicacao, match="booleana"):
        runtime.atualizar({
            "provider": "ollama", "model": "qwen3:4b",
            "api_key_action": "preserve", "api_key": "",
            "mascot_enabled": "sim",
        })


def test_openrouter_fixa_url_e_protege_chave_sem_vazar(runtime) -> None:
    segredo = "sk-or-v1-super-secreto"
    resultado = runtime.atualizar({
        "provider": "openrouter", "model": "openai/gpt-4.1-mini",
        "api_key_action": "replace", "api_key": segredo,
    })
    env = runtime.arquivo_env.read_text(encoding="utf-8")
    assert f"LAYLAY_LLM_BASE_URL={OPENROUTER_URL}" in env
    assert "LAYLAY_LLM_BACKEND=remoto" in env
    assert segredo not in env
    assert segredo.encode() not in runtime.arquivo_segredo.read_bytes()
    assert segredo not in json.dumps(resultado)
    assert resultado["settings"]["api_key_configured"] is True


def test_chave_vazia_preserva_e_remocao_e_explicita(runtime) -> None:
    runtime.atualizar({
        "provider": "openrouter", "model": "qwen/model",
        "api_key_action": "replace", "api_key": "segredo-real",
    })
    antes = runtime.arquivo_segredo.read_bytes()
    runtime.atualizar({
        "provider": "openrouter", "model": "outro/modelo",
        "api_key_action": "preserve", "api_key": "",
    })
    assert runtime.arquivo_segredo.read_bytes() == antes
    runtime.atualizar({
        "provider": "ollama", "model": "qwen",
        "api_key_action": "remove", "api_key": "",
    })
    assert not runtime.arquivo_segredo.exists()


def test_openrouter_sem_chave_e_recusado(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_LLM_API_KEY", raising=False)
    runtime = ConfiguracaoAplicacaoRuntime(
        raiz=tmp_path, caminho_segredo=tmp_path / "sem-chave.dpapi",
        win32crypt_mod=DPAPIFalso(),
        requests_get=catalogo_ativo,
    )
    with pytest.raises(ErroConfiguracaoAplicacao, match="Configure uma chave"):
        runtime.atualizar({
            "provider": "openrouter", "model": "qwen/model",
            "api_key_action": "preserve", "api_key": "",
        })


def test_falha_dpapi_recusa_salvamento_sem_gravar_segredo(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_LLM_API_KEY", raising=False)
    arquivo = tmp_path / "privado" / "segredo.dpapi"
    runtime = ConfiguracaoAplicacaoRuntime(
        raiz=tmp_path, caminho_segredo=arquivo,
        win32crypt_mod=DPAPIIndisponivel(),
        requests_get=catalogo_ativo,
    )
    with pytest.raises(ErroConfiguracaoAplicacao, match="Nada foi salvo"):
        runtime.atualizar({
            "provider": "openrouter", "model": "qwen/model",
            "api_key_action": "replace", "api_key": "nao-vazar",
        })
    assert not arquivo.exists()
    assert not runtime.arquivo_env.exists()


def test_carrega_dpapi_no_ambiente_sem_sobrescrever_externo(tmp_path, monkeypatch) -> None:
    arquivo = tmp_path / "chave.dpapi"
    arquivo.write_bytes(DPAPIFalso().CryptProtectData(b"salva")[1])
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_LLM_API_KEY", raising=False)
    assert carregar_segredo_no_ambiente(caminho=arquivo, win32crypt_mod=DPAPIFalso())
    assert os.environ["OPENROUTER_API_KEY"] == "salva"
    monkeypatch.setenv("OPENROUTER_API_KEY", "externa")
    monkeypatch.setenv("LAYLAY_LLM_API_KEY", "externa")
    assert carregar_segredo_no_ambiente(caminho=arquivo, win32crypt_mod=DPAPIFalso())
    assert os.environ["OPENROUTER_API_KEY"] == "externa"


def test_diagnostico_e_estado_nao_expoem_credencial(runtime) -> None:
    runtime.atualizar({
        "provider": "openrouter", "model": "qwen/model",
        "api_key_action": "replace", "api_key": "segredo-invisivel",
    })
    saida = json.dumps({"estado": runtime.estado(), "diagnostico": runtime.diagnostico()})
    assert "segredo-invisivel" not in saida
    assert "api_key" not in runtime.estado()


def test_modelos_ficam_separados_por_provedor(runtime) -> None:
    runtime.arquivo_env.write_text(
        "LAYLAY_LLM_BACKEND=ollama\n"
        "LAYLAY_LLM_BASE_URL=http://localhost:11434/v1\n"
        "LAYLAY_LLM_MODEL=qwen-local:4b\n",
        encoding="utf-8",
    )
    runtime.atualizar({
        "provider": "openrouter", "model": "qwen/qwen3-32b",
        "api_key_action": "replace", "api_key": "segredo",
    })
    estado_remoto = runtime.estado()
    assert estado_remoto["model"] == "qwen/qwen3-32b"
    assert estado_remoto["models_by_provider"]["ollama"] == "qwen-local:4b"

    runtime.atualizar({
        "provider": "ollama", "model": "qwen-local:4b",
        "api_key_action": "preserve", "api_key": "",
    })
    estado_local = runtime.estado()
    assert estado_local["model"] == "qwen-local:4b"
    assert estado_local["models_by_provider"]["openrouter"] == "qwen/qwen3-32b"


def test_openrouter_recusa_modelo_sem_endpoint_antes_de_salvar(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LAYLAY_LLM_API_KEY", raising=False)
    runtime = ConfiguracaoAplicacaoRuntime(
        raiz=tmp_path,
        caminho_segredo=tmp_path / "segredo.dpapi",
        win32crypt_mod=DPAPIFalso(),
        requests_get=lambda *_args, **_kwargs: RespostaCatalogo(endpoints=[]),
    )
    with pytest.raises(ErroConfiguracaoAplicacao, match="sem provedor ativo"):
        runtime.atualizar({
            "provider": "openrouter", "model": "qwen/modelo-antigo",
            "api_key_action": "replace", "api_key": "nao-salvar",
        })
    assert not runtime.arquivo_env.exists()
    assert not runtime.arquivo_segredo.exists()
