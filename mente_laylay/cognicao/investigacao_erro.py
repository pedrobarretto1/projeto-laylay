"""Pesquisa erros copiados sem abrir uma página no navegador do usuário."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any, Callable

from mente_laylay.integracao.registro_conversa_llm import resolver_enviador_modelo

import requests

from mente_laylay.integracao.llm_http import eh_estado_tecnico_llm


def extrair_consulta_erro(conteudo: str) -> str:
    texto = re.sub(r"\s+", " ", str(conteudo or "")).strip()
    if not texto:
        return ""
    candidatos = re.findall(
        r"(?:HTTP[_ -]?\d{3}[_A-Z-]*|[A-Za-z][A-Za-z0-9_.]*(?:Error|Exception)\s*:[^\n]{0,180}|"
        r"(?:erro|error|falha)\s*\d{3}[^.!?\n]{0,180})",
        texto,
        flags=re.IGNORECASE,
    )
    consulta = candidatos[0] if candidatos else texto[:220]
    consulta = re.sub(r"(?:[A-Za-z]:\\|/)(?:[^\s:]+[/\\]){2,}[^\s:]*", " ", consulta)
    return re.sub(r"\s+", " ", consulta).strip(" -:;,.\t")[:240]


class _ParserResultados(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.resultados: list[dict[str, str]] = []
        self._campo = ""
        self._href = ""
        self._partes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        atributos = dict(attrs)
        classes = str(atributos.get("class") or "")
        if tag == "a" and "result__a" in classes:
            self._campo, self._href, self._partes = "titulo", str(atributos.get("href") or ""), []
        elif tag in {"a", "div"} and "result__snippet" in classes:
            self._campo, self._partes = "snippet", []

    def handle_data(self, data: str) -> None:
        if self._campo:
            self._partes.append(str(data or ""))

    def handle_endtag(self, tag: str) -> None:
        if self._campo == "titulo" and tag == "a":
            titulo = re.sub(r"\s+", " ", html.unescape(" ".join(self._partes))).strip()
            if titulo:
                self.resultados.append({"titulo": titulo, "url": self._href, "resumo": ""})
            self._campo, self._partes = "", []
        elif self._campo == "snippet" and tag in {"a", "div"}:
            resumo = re.sub(r"\s+", " ", html.unescape(" ".join(self._partes))).strip()
            if resumo and self.resultados:
                self.resultados[-1]["resumo"] = resumo
            self._campo, self._partes = "", []


class InvestigadorErroRuntime:
    def __init__(
        self,
        *,
        enviar_mensagem: Callable[..., Any] | None = None,
        modelo_llm: Any = None,
        limpar_resposta: Callable[[str], str] | None = None,
        requests_get: Callable[..., Any] = requests.get,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.enviar_mensagem = resolver_enviador_modelo(
            modelo_llm=modelo_llm,
            enviar_mensagem=enviar_mensagem,
        )
        self.limpar_resposta = limpar_resposta or (lambda valor: str(valor or "").strip())
        self.requests_get = requests_get
        self.log = log

    def _buscar(self, consulta: str) -> list[dict[str, str]]:
        try:
            resposta = self.requests_get(
                "https://html.duckduckgo.com/html/",
                params={"q": consulta, "kl": "br-pt"},
                headers={"User-Agent": "Mozilla/5.0 LaylayAssistant/2.5"},
                timeout=6,
            )
            resposta.raise_for_status()
            parser = _ParserResultados()
            parser.feed(str(resposta.text or ""))
            return [item for item in parser.resultados if item.get("resumo")][:4]
        except Exception as erro:
            self.log(f"⚠️ [CLIPBOARD:INVESTIGAÇÃO] pesquisa interna falhou: {type(erro).__name__}")
            return []

    def investigar(self, conteudo: str) -> dict[str, Any]:
        erro = str(conteudo or "").strip()[:4000]
        consulta = extrair_consulta_erro(erro)
        if not consulta:
            return {"ok": False, "fala": "Não consegui identificar o erro copiado."}
        self.log(f"🔎 [CLIPBOARD:INVESTIGAÇÃO] consulta interna={consulta!r}")
        resultados = self._buscar(consulta)
        evidencias = "\n".join(
            f"- {item['titulo']}: {item['resumo']}" for item in resultados
        ) or "Nenhum resultado web confiável ficou disponível; deixe essa limitação explícita."
        mensagens = [
            {
                "role": "system",
                "content": (
                    "Analise uma mensagem de erro para o usuário. Responda em português, de forma direta e útil. "
                    "Explique o significado, a causa mais provável, como confirmar e os próximos passos. "
                    "Separe hipótese de fato, não invente detalhes, não peça novamente qual é o erro e use no máximo 180 palavras."
                ),
            },
            {"role": "user", "content": f"ERRO COPIADO:\n{erro}\n\nRESULTADOS DA PESQUISA:\n{evidencias}"},
        ]
        fala = ""
        sintese_llm = False
        try:
            try:
                # Esta chamada acontece depois de uma confirmação direta da
                # pessoa usuária. Portanto, ela é parte do turno interativo,
                # não uma tarefa autônoma de baixa prioridade.
                bruto = self.enviar_mensagem(
                    mensagens,
                    _com_tools=False,
                    max_tokens=320,
                    modo_rapido=True,
                    timeout=20,
                    _permitir_conversa_modo_jogo=True,
                    _prioridade_interativa=True,
                )
            except TypeError:
                bruto = self.enviar_mensagem(mensagens)
            if eh_estado_tecnico_llm(bruto):
                self.log("⚠️ [CLIPBOARD:INVESTIGAÇÃO] síntese local indisponível; usando evidência direta")
            else:
                fala = str(self.limpar_resposta(str(bruto or "")) or "").strip()
                # O limpador pode retirar os sublinhados da sentinela. A
                # segunda verificação impede esse estado interno de virar voz.
                if eh_estado_tecnico_llm(fala):
                    fala = ""
                else:
                    sintese_llm = bool(fala)
        except Exception as erro_llm:
            self.log(f"⚠️ [CLIPBOARD:INVESTIGAÇÃO] síntese falhou: {type(erro_llm).__name__}")
            fala = ""
        if not fala:
            primeira_evidencia = next(
                (str(item.get("resumo") or "").strip() for item in resultados if item.get("resumo")),
                "",
            )
            if primeira_evidencia:
                fala = (
                    f"O erro copiado é {consulta}. A pesquisa encontrou esta pista: "
                    f"{primeira_evidencia} Isso ainda é uma hipótese; o contexto e os logs do sistema "
                    "é que confirmam a causa."
                )
            else:
                fala = (
                    f"Reconheci o erro como {consulta}, mas a pesquisa e a síntese não responderam agora. "
                    "Prefiro não inventar a causa."
                )
        return {
            "ok": True,
            "fala": fala,
            "consulta": consulta,
            "fontes": [item.get("url", "") for item in resultados if item.get("url")],
            "pesquisa_web": bool(resultados),
            "sintese_llm": sintese_llm,
        }
