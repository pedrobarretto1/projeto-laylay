"""Autoria segura da fala conversacional pela própria Laylay.

O Python fornece contexto e limites, mas não redige a resposta cotidiana. A
fala local recebida por esta camada é apenas um piso semântico para a LLM não
perder o sentido quando estiver recuperando um turno problemático.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
)
from mente_laylay.integracao.llm_http import eh_estado_tecnico_llm
from mente_laylay.personalidade.prompt_voz_unica import IDENTIDADE_VOZ_LAYLAY


@dataclass(frozen=True)
class FalaAutoral:
    fala: str
    usada_llm: bool
    motivo_fallback: str = ""


def _extrair_json(valor: Any) -> dict[str, Any]:
    texto = str(valor or "").strip()
    if not texto or eh_estado_tecnico_llm(texto):
        return {}
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.I)
    try:
        dados = json.loads(texto)
    except (TypeError, ValueError, json.JSONDecodeError):
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio < 0 or fim <= inicio:
            return {}
        try:
            dados = json.loads(texto[inicio : fim + 1])
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return dados if isinstance(dados, dict) else {}


def _falas_assistente(
    mensagens: Iterable[Mapping[str, Any]] | None,
    *,
    limite: int = 5,
) -> list[str]:
    falas = [
        re.sub(r"\s+", " ", str(item.get("content") or "")).strip()[:320]
        for item in list(mensagens or [])
        if isinstance(item, Mapping)
        and str(item.get("role") or "").casefold() == "assistant"
        and str(item.get("content") or "").strip()
    ]
    return falas[-max(1, int(limite or 5)):]


def criar_fala_autoral(
    texto_usuario: str,
    fala_segura: str,
    *,
    enviar_mensagem: Callable[..., Any] | None,
    mensagens: Iterable[Mapping[str, Any]] | None = None,
    foco: Mapping[str, Any] | None = None,
    contrato_reparo: Mapping[str, Any] | None = None,
) -> FalaAutoral:
    """Pede à LLM uma fala nova sem conceder autoridade operacional.

    Esta função é usada somente depois de uma resposta conversacional ser
    rejeitada. Ela nunca gera ou aceita comandos e nunca transforma o fallback
    local na voz oficial quando o modelo está saudável.
    """
    fallback = re.sub(r"\s+", " ", str(fala_segura or "")).strip()
    if not callable(enviar_mensagem):
        return FalaAutoral(fallback, False, "modelo_sem_callback")

    recentes = _falas_assistente(mensagens)
    payload = {
        "mensagem_atual": str(texto_usuario or "").strip()[:1000],
        "sentido_minimo_a_preservar": fallback[:700],
        "foco_confirmado": dict(foco or {}),
        "contrato_de_reparo": dict(contrato_reparo or {}),
        "falas_recentes_que_nao_devem_ser_repetidas": recentes,
    }
    sistema = (
        f"{IDENTIDADE_VOZ_LAYLAY} "
        "Escreva a fala final da Laylay para a mensagem atual. O Python forneceu apenas "
        "o sentido mínimo e os limites; não copie o texto mínimo como um molde e não fale "
        "sobre sistema, verificador, rascunho, resposta, erro interno ou tentativa de reparo. "
        "Responda como amiga presente, natural, clara e com deboche leve quando combinar. "
        "Não seja poética sem necessidade. Preserve fatos, foco, relações e negações; não "
        "invente memória, corpo, ambiente ou experiência pessoal. Não execute, prometa ou "
        "sugira comandos. Não reutilize frases, aberturas ou tiradas da lista recente. Uma "
        "ou duas frases bastam e no máximo uma pergunta é permitida. Retorne somente JSON "
        'válido no formato {"fala":"...","comandos":[]}.'
    )
    try:
        bruto = enviar_mensagem(
            [
                {"role": "system", "content": sistema},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=220,
            modo_rapido=True,
            timeout=12,
            _prioridade_interativa=True,
            _permitir_durante_interacao=True,
            _tipo_chamada="reparo_comunicacao",
            _classe_timeout="rapida",
        )
    except Exception as erro:
        return FalaAutoral(
            fallback,
            False,
            f"erro_chamada_{type(erro).__name__.casefold()}",
        )

    dados = _extrair_json(bruto)
    fala = re.sub(r"\s+", " ", str(dados.get("fala") or "")).strip()
    comandos = dados.get("comandos")
    if not fala or not 2 <= len(fala.split()) <= 80:
        return FalaAutoral(fallback, False, "fala_invalida")
    if comandos not in (None, [], ()):
        return FalaAutoral(fallback, False, "comando_na_fala_conversacional")
    if detectar_experiencia_pessoal_inventada(fala):
        return FalaAutoral(fallback, False, "realidade_pessoal_inventada")
    if re.search(
        r"\b(?:verificador|rascunho|resposta saiu|resposta não fechou|"
        r"resposta nao fechou|erro interno|falha técnica|falha tecnica)\b",
        fala,
        flags=re.I,
    ):
        return FalaAutoral(fallback, False, "bastidor_exposto")
    normalizada = fala.casefold()
    if any(normalizada == item.casefold() for item in recentes):
        return FalaAutoral(fallback, False, "fala_recente_repetida")
    return FalaAutoral(fala, True)
