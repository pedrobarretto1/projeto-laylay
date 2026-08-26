"""Configuração persistente e sanitizada da aplicação Laylay.

As escolhas de backend ficam no ``configuracao.env``. A credencial do
OpenRouter é protegida pelo DPAPI do usuário atual do Windows e nunca faz
parte de snapshots, diagnósticos ou memória semântica.
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Mapping
from urllib.parse import quote

import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1"
OLLAMA_URL = "http://localhost:11434/v1"
PROVEDORES = frozenset({"ollama", "portatil", "openrouter"})
CHAVES_GERENCIADAS = frozenset({
    "LAYLAY_LLM_BACKEND",
    "LAYLAY_LLM_BASE_URL",
    "LAYLAY_LLM_MODEL",
    "LAYLAY_LLM_MODEL_OLLAMA",
    "LAYLAY_LLM_MODEL_PORTATIL",
    "LAYLAY_LLM_MODEL_OPENROUTER",
    "LAYLAY_MASCOT_ENABLED",
})
CHAVES_MODELO_PROVEDOR = {
    "ollama": "LAYLAY_LLM_MODEL_OLLAMA",
    "portatil": "LAYLAY_LLM_MODEL_PORTATIL",
    "openrouter": "LAYLAY_LLM_MODEL_OPENROUTER",
}
MODELOS_PADRAO = {
    "ollama": "Qwen3:4b-instruct",
    "portatil": "Qwen3:4b-instruct",
    "openrouter": "",
}


class ErroConfiguracaoAplicacao(ValueError):
    """Erro seguro para exibição na interface, sem material confidencial."""


def _win32crypt_padrao() -> Any:
    try:
        import win32crypt  # type: ignore[import-not-found]
    except ImportError as erro:
        raise ErroConfiguracaoAplicacao(
            "A proteção de credenciais do Windows não está disponível. "
            "Instale pywin32 ou configure a chave manualmente fora da interface."
        ) from erro
    return win32crypt


def caminho_segredo_padrao() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    return base / "Laylay" / "credencial_openrouter.dpapi"


def _proteger(segredo: str, win32crypt_mod: Any) -> bytes:
    try:
        resultado = win32crypt_mod.CryptProtectData(
            segredo.encode("utf-8"), "Laylay OpenRouter", None, None, None, 0,
        )
        return bytes(resultado[1] if isinstance(resultado, tuple) else resultado)
    except Exception as erro:
        raise ErroConfiguracaoAplicacao(
            "O Windows não conseguiu proteger a credencial. Nada foi salvo."
        ) from erro


def _desproteger(blob: bytes, win32crypt_mod: Any) -> str:
    try:
        resultado = win32crypt_mod.CryptUnprotectData(blob, None, None, None, 0)
        dados = resultado[1] if isinstance(resultado, tuple) else resultado
        return bytes(dados).decode("utf-8").strip()
    except Exception as erro:
        raise ErroConfiguracaoAplicacao(
            "A credencial protegida pertence a outro usuário ou está inválida."
        ) from erro


def carregar_segredo_no_ambiente(
    *,
    caminho: str | os.PathLike[str] | None = None,
    win32crypt_mod: Any | None = None,
) -> bool:
    """Carrega a chave protegida sem sobrescrever variáveis externas."""
    if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LAYLAY_LLM_API_KEY"):
        return True
    arquivo = Path(caminho) if caminho else caminho_segredo_padrao()
    if not arquivo.is_file():
        return False
    segredo = _desproteger(arquivo.read_bytes(), win32crypt_mod or _win32crypt_padrao())
    if not segredo:
        return False
    os.environ.setdefault("OPENROUTER_API_KEY", segredo)
    os.environ.setdefault("LAYLAY_LLM_API_KEY", segredo)
    return True


class ConfiguracaoAplicacaoRuntime:
    def __init__(
        self,
        *,
        raiz: str | os.PathLike[str],
        caminho_segredo: str | os.PathLike[str] | None = None,
        win32crypt_mod: Any | None = None,
        requests_get: Callable[..., Any] | None = None,
    ) -> None:
        self.raiz = Path(raiz).resolve()
        self.arquivo_env = self.raiz / "configuracao.env"
        self.arquivo_segredo = Path(caminho_segredo) if caminho_segredo else caminho_segredo_padrao()
        self._win32crypt_mod = win32crypt_mod
        self._requests_get = requests_get or requests.get
        self._reinicio_pendente = False

    def _ler_env(self) -> tuple[list[str], dict[str, str]]:
        try:
            linhas = self.arquivo_env.read_text(encoding="utf-8-sig").splitlines()
        except FileNotFoundError:
            linhas = []
        except OSError as erro:
            raise ErroConfiguracaoAplicacao("Não consegui ler configuracao.env.") from erro
        valores: dict[str, str] = {}
        for linha in linhas:
            texto = linha.strip()
            if not texto or texto.startswith("#") or "=" not in texto:
                continue
            chave, valor = texto.split("=", 1)
            valores[chave.strip()] = valor.strip().strip('"').strip("'")
        return linhas, valores

    @staticmethod
    def _provedor(valores: Mapping[str, str]) -> str:
        backend = str(valores.get("LAYLAY_LLM_BACKEND") or os.environ.get("LAYLAY_LLM_BACKEND") or "ollama").casefold()
        url = str(valores.get("LAYLAY_LLM_BASE_URL") or os.environ.get("LAYLAY_LLM_BASE_URL") or "")
        if backend in {"remoto", "remote"} and url.rstrip("/") == OPENROUTER_URL:
            return "openrouter"
        if backend in {"portatil", "portable", "llama.cpp", "llamacpp"}:
            return "portatil"
        return "ollama"

    def _tem_chave(self) -> bool:
        if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LAYLAY_LLM_API_KEY"):
            return True
        return self.arquivo_segredo.is_file() and self.arquivo_segredo.stat().st_size > 0

    def _modelos_por_provedor(
        self,
        valores: Mapping[str, str],
        provedor_ativo: str,
    ) -> dict[str, str]:
        """Migra o modelo legado apenas para o backend ao qual ele pertencia."""
        legado = str(
            valores.get("LAYLAY_LLM_MODEL")
            or os.environ.get("LAYLAY_LLM_MODEL")
            or ""
        ).strip()[:160]
        modelos: dict[str, str] = {}
        for provedor, chave in CHAVES_MODELO_PROVEDOR.items():
            especifico = str(valores.get(chave) or os.environ.get(chave) or "").strip()
            if not especifico and provedor == provedor_ativo:
                especifico = legado
            modelos[provedor] = (especifico or MODELOS_PADRAO[provedor])[:160]
        return modelos

    def _validar_modelo_openrouter(self, modelo: str) -> dict[str, Any]:
        """Consulta o catálogo público sem transmitir a chave privada."""
        partes = modelo.split("/", 1)
        if len(partes) != 2 or not all(partes):
            raise ErroConfiguracaoAplicacao(
                "O modelo OpenRouter deve usar o formato autor/modelo."
            )
        autor, nome = partes
        url = (
            f"{OPENROUTER_URL}/models/{quote(autor, safe='')}/"
            f"{quote(nome, safe='._:-')}/endpoints"
        )
        try:
            resposta = self._requests_get(url, timeout=8)
        except requests.exceptions.RequestException:
            return {"checked": False, "available": None}
        status = int(getattr(resposta, "status_code", 0) or 0)
        if status == 404:
            raise ErroConfiguracaoAplicacao(
                f"O modelo {modelo} não foi encontrado na OpenRouter."
            )
        if status < 200 or status >= 300:
            return {"checked": False, "available": None}
        try:
            dados = resposta.json()
            endpoints = list(((dados or {}).get("data") or {}).get("endpoints") or [])
        except (TypeError, ValueError, AttributeError):
            return {"checked": False, "available": None}
        if not endpoints:
            raise ErroConfiguracaoAplicacao(
                f"O modelo {modelo} está sem provedor ativo na OpenRouter. "
                "Escolha outro modelo antes de salvar."
            )
        return {"checked": True, "available": True, "endpoint_count": len(endpoints)}

    def estado(self) -> dict[str, Any]:
        _linhas, valores = self._ler_env()
        provedor = self._provedor(valores)
        modelos = self._modelos_por_provedor(valores, provedor)
        modelo = modelos[provedor]
        url = {
            "openrouter": OPENROUTER_URL,
            "ollama": OLLAMA_URL,
            "portatil": "Gerenciada pelo runtime portátil",
        }[provedor]
        return {
            "provider": provedor,
            "model": modelo,
            "models_by_provider": modelos,
            "base_url": url,
            "api_key_configured": self._tem_chave(),
            "restart_required": self._reinicio_pendente,
            "mascot_enabled": str(
                valores.get("LAYLAY_MASCOT_ENABLED")
                or os.environ.get("LAYLAY_MASCOT_ENABLED")
                or "0"
            ).strip().casefold() in {"1", "true", "sim", "yes", "on", "ligado"},
        }

    def _escrever_env(self, atualizacoes: Mapping[str, str]) -> None:
        linhas, _valores = self._ler_env()
        saida: list[str] = []
        vistas: set[str] = set()
        for linha in linhas:
            texto = linha.strip()
            if "=" not in texto or texto.startswith("#"):
                saida.append(linha)
                continue
            chave = texto.split("=", 1)[0].strip()
            if chave in CHAVES_GERENCIADAS:
                if chave in atualizacoes and chave not in vistas:
                    saida.append(f"{chave}={atualizacoes[chave]}")
                    vistas.add(chave)
                continue
            saida.append(linha)
        ordem = (
            "LAYLAY_LLM_BACKEND", "LAYLAY_LLM_BASE_URL", "LAYLAY_LLM_MODEL",
            "LAYLAY_LLM_MODEL_OLLAMA", "LAYLAY_LLM_MODEL_PORTATIL",
            "LAYLAY_LLM_MODEL_OPENROUTER",
            "LAYLAY_MASCOT_ENABLED",
        )
        for chave in ordem:
            if chave in atualizacoes and chave not in vistas:
                saida.append(f"{chave}={atualizacoes[chave]}")
        conteudo = "\n".join(saida).rstrip() + "\n"
        self.arquivo_env.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", newline="\n", delete=False,
                dir=self.arquivo_env.parent, prefix=".configuracao-", suffix=".tmp",
            ) as temporario:
                temporario.write(conteudo)
                temporario.flush()
                os.fsync(temporario.fileno())
                temporario_path = Path(temporario.name)
            os.replace(temporario_path, self.arquivo_env)
        except OSError as erro:
            raise ErroConfiguracaoAplicacao("Não consegui salvar configuracao.env.") from erro

    def _salvar_segredo(self, segredo: str) -> None:
        modulo = self._win32crypt_mod or _win32crypt_padrao()
        protegido = _proteger(segredo, modulo)
        self.arquivo_segredo.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                "wb", delete=False, dir=self.arquivo_segredo.parent,
                prefix=".credencial-", suffix=".tmp",
            ) as temporario:
                temporario.write(protegido)
                temporario.flush()
                os.fsync(temporario.fileno())
                temporario_path = Path(temporario.name)
            os.replace(temporario_path, self.arquivo_segredo)
        except OSError as erro:
            raise ErroConfiguracaoAplicacao("Não consegui salvar a credencial protegida.") from erro

    def atualizar(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        permitidos = {
            "provider", "model", "api_key_action", "api_key", "mascot_enabled",
        }
        extras = set(payload) - permitidos
        if extras:
            raise ErroConfiguracaoAplicacao("A configuração contém campos não reconhecidos.")
        provedor = str(payload.get("provider") or "").casefold().strip()
        if provedor not in PROVEDORES:
            raise ErroConfiguracaoAplicacao("Provedor de modelo inválido.")
        modelo = str(payload.get("model") or "").strip()
        if not modelo or len(modelo) > 160 or any(ord(c) < 32 for c in modelo):
            raise ErroConfiguracaoAplicacao("Informe um modelo válido de até 160 caracteres.")
        acao = str(payload.get("api_key_action") or "preserve").casefold().strip()
        if acao not in {"preserve", "replace", "remove"}:
            raise ErroConfiguracaoAplicacao("Ação de credencial inválida.")
        segredo = str(payload.get("api_key") or "")
        mascote_bruto = payload.get("mascot_enabled", self.estado()["mascot_enabled"])
        if not isinstance(mascote_bruto, bool):
            raise ErroConfiguracaoAplicacao("A preferência do mascote deve ser booleana.")
        if provedor == "openrouter" and acao == "remove":
            raise ErroConfiguracaoAplicacao(
                "Escolha outro provedor antes de remover a chave OpenRouter."
            )
        validacao_modelo = (
            self._validar_modelo_openrouter(modelo)
            if provedor == "openrouter"
            else {"checked": True, "available": True}
        )
        if acao == "replace":
            if not segredo.strip() or len(segredo) > 8_192 or any(ord(c) < 32 for c in segredo):
                raise ErroConfiguracaoAplicacao("Informe uma chave OpenRouter válida.")
            self._salvar_segredo(segredo.strip())
        elif acao == "remove":
            try:
                self.arquivo_segredo.unlink(missing_ok=True)
            except OSError as erro:
                raise ErroConfiguracaoAplicacao("Não consegui remover a credencial protegida.") from erro
        if provedor == "openrouter" and acao != "replace" and not self._tem_chave():
            raise ErroConfiguracaoAplicacao("Configure uma chave OpenRouter antes de salvar.")
        _linhas, valores_atuais = self._ler_env()
        provedor_anterior = self._provedor(valores_atuais)
        modelos = self._modelos_por_provedor(valores_atuais, provedor_anterior)
        modelos[provedor] = modelo
        atualizacoes = {
            "LAYLAY_LLM_BACKEND": {
                "ollama": "ollama", "portatil": "portatil", "openrouter": "remoto",
            }[provedor],
            "LAYLAY_LLM_BASE_URL": {
                "ollama": OLLAMA_URL, "portatil": "", "openrouter": OPENROUTER_URL,
            }[provedor],
            "LAYLAY_LLM_MODEL": modelo,
            **{
                chave: modelos[nome_provedor]
                for nome_provedor, chave in CHAVES_MODELO_PROVEDOR.items()
            },
            "LAYLAY_MASCOT_ENABLED": "1" if mascote_bruto else "0",
        }
        self._escrever_env(atualizacoes)
        self._reinicio_pendente = True
        estado = self.estado()
        return {
            "saved": True,
            "restart_required": True,
            "message": (
                "Configuração salva e modelo disponível. Ela será aplicada após reiniciar a Laylay."
                if validacao_modelo.get("checked")
                else "Configuração salva, mas a OpenRouter não respondeu à validação. "
                "Ela será aplicada após reiniciar a Laylay."
            ),
            "settings": estado,
        }

    def diagnostico(self) -> dict[str, Any]:
        estado = self.estado()
        return {
            "provider": estado["provider"],
            "model_configured": bool(estado["model"]),
            "api_key_configured": estado["api_key_configured"],
            "restart_required": estado["restart_required"],
            "secret_storage": "windows_dpapi",
        }


def criar_configuracao_aplicacao_runtime(**kwargs: Any) -> ConfiguracaoAplicacaoRuntime:
    return ConfiguracaoAplicacaoRuntime(**kwargs)
