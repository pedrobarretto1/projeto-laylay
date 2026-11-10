"""Interpretação de atos sociais pela perspectiva da conversa.

Não executa comandos nem produz respostas. A decisão combina forma da frase,
papéis dos interlocutores e contexto recente, evitando que uma expressão
isolada determine sozinha se Pedro perguntou ou respondeu alguma coisa.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict

from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, texto_fora_de_citacoes


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9?!,;:.\s]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def _pergunta_anterior_sobre_pedro(mente: Dict[str, Any]) -> bool:
    anterior = _normalizar(str(mente.get("ultima_resposta") or ""))
    if not anterior or "?" not in anterior:
        return False
    return bool(re.search(
        r"\b(?:e voce|do teu lado|como voce|como foi seu dia|voce esta|voce ta)\b",
        anterior,
    ))


def analisar_ato_social(
    texto: str,
    *,
    mente: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Distingue pergunta de bem-estar, resposta pessoal e ambiguidade."""
    bruto = str(texto or "").strip()
    base = _normalizar(bruto)
    estado = dict(mente or {})
    if not base:
        return {}
    if texto_e_metalinguistico(bruto):
        return {
            "tipo": "METALINGUAGEM",
            "confianca": 0.99,
            "motivo": "a fala discute uma formulação ou citação",
            "evidencias": ["moldura_metalinguistica"],
        }

    externo = texto_fora_de_citacoes(bruto)
    partes = enunciados_discursivos(externo)
    if len(partes) > 1:
        # A pergunta e o destinatário precisam pertencer ao mesmo enunciado
        # que descreve o estado. A pontuação do pedido vizinho não conta.
        atos = [analisar_ato_social(parte, mente=estado) for parte in partes]
        for tipo in ("WELLBEING", "WELLBEING_REPLY"):
            for ato in atos:
                if ato.get("tipo") == tipo:
                    return ato
        return {}
    bruto = externo
    base = re.sub(r"^(?:oi|ola|opa|bom dia|boa tarde|boa noite)(?:[, ]+(?:lay|laylay))?[, ]+",
                  "", _normalizar(externo), count=1)
    if re.search(r"[,;].+\?\s*$", base):
        return {
            "tipo": "COMPOSTO", "confianca": 0.98,
            "motivo": "afirmacao social seguida de pergunta nova",
            "evidencias": ["mais_de_um_ato"],
        }

    # O estado precisa estar explicitamente atribuído à interlocutora. Tornar
    # esse referente opcional fazia perguntas metalinguísticas como "Como eu
    # perguntaria se o Opera está aberto?" virarem WELLBEING apenas porque
    # continham ``como`` e ``está`` em pontos diferentes da frase.
    pessoa = r"(?:voce|tu|a laylay|lay|laylay)"
    pergunta_estado_como = bool(re.fullmatch(
        rf"como\s+(?:(?:e\s+)?que\s+)?(?:{pessoa}\s+(?:esta|ta|vai)|vai\s+{pessoa})"
        r"(?:\s+(?:se sentindo|por ai|hoje|agora)){0,2}[?!.]*",
        base,
    ))
    vocabulario_estado = bool(re.search(
        r"\b(?:bem|mal|tranquil[oa]|de boa|suave|feliz|triste|cansad[oa]|"
        r"tudo certo|na paz|mais ou menos)\b",
        base,
    ))
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
    predicados = re.finditer(
        r"\b(?:(?:estou|to)\s+(?:me\s+sentindo\s+)?|(?:esta|ta)\s+(?:se\s+sentindo\s+)?)"
        r"(?P<modificadores>(?:[a-z]+\s+){0,2})"
        r"(?:bem|mal|tranquil[oa]|feliz|triste|cansad[oa])\b", base)
    # Estar + gerúndio/objeto não recebe o adjetivo de outro predicado.
    # Somente modificadores lexicais pertencem ao intervalo do estado.
    estado_vinculado = any(all((consultar_morfologia(p) or 0)&64
        for p in m['modificadores'].split()) for m in predicados)
    bem = re.search(r"\btudo\s+bem\b", base)
    if bem and re.match(r"\s+(?:com\s+)?(?:voce|tu|lay|laylay)\s+\w", base[bem.end():]) and not re.fullmatch(
            r"\s+(?:com\s+)?(?:voce|tu)\s+(?:lay|laylay)[?!.]*", base[bem.end():]):
        # O complemento pode ser uma ação consentida ("com você deixar").
        # Essa forma não é a pergunta curta sobre o estado da interlocutora.
        bem = None
    estrutura_estado = bool(estado_vinculado or bem)
    if not ((vocabulario_estado and estrutura_estado) or pergunta_estado_como):
        return {}

    pergunta_grafica = "?" in bruto
    inicio_interrogativo = bool(re.match(r"^(?:como|e voce|e tu)\b", base))
    referencia_laylay = bool(re.search(
        rf"\b(?:{pessoa}|com voce|do seu lado)\b",
        base,
    ))
    recortes_estado = [r for r in re.split(r'[.!?;]+', base)
        if re.search(r'\b(?:bem|mal|tranquil[oa]|feliz|triste|cansad[oa])\b', r)]
    primeira_pessoa = any(re.search(
        r"\b(?:eu|comigo|meu lado|por aqui|aqui comigo)\b|^(?:estou|to)\b",
        r.strip(),
    ) for r in recortes_estado)
    afirmacao_explicita = any(re.search(
        r"\b(?:sim|por aqui|do meu lado|comigo|estou|eu to|eu estou)\b",
        r,
    ) for r in recortes_estado)
    contexto_resposta = _pergunta_anterior_sobre_pedro(estado)

    pontos_pergunta = 0.0
    pontos_resposta = 0.0
    evidencias: list[str] = []
    if pergunta_grafica:
        pontos_pergunta += 0.48
        evidencias.append("pontuacao_interrogativa")
        if not primeira_pessoa:
            pontos_pergunta += 0.16
    if inicio_interrogativo:
        pontos_pergunta += 0.34
        evidencias.append("forma_interrogativa")
    if referencia_laylay:
        pontos_pergunta += 0.34
        evidencias.append("estado_dirigido_a_laylay")
    if primeira_pessoa:
        pontos_resposta += 0.48
        evidencias.append("perspectiva_de_pedro")
    if afirmacao_explicita:
        pontos_resposta += 0.34
        evidencias.append("forma_afirmativa")
    if not pergunta_grafica:
        pontos_resposta += 0.14
    if contexto_resposta and not referencia_laylay and not pergunta_grafica:
        pontos_resposta += 0.34
        evidencias.append("responde_pergunta_anterior")

    diferenca = pontos_pergunta - pontos_resposta
    if pontos_pergunta >= 0.58 and diferenca >= 0.20:
        return {
            "tipo": "WELLBEING", "confianca": round(min(0.98, 0.66 + diferenca / 3), 2),
            "motivo": "pergunta dirigida ao estado da Laylay",
            "evidencias": evidencias,
        }
    if pontos_resposta >= 0.48 and diferenca <= -0.20:
        return {
            "tipo": "WELLBEING_REPLY", "confianca": round(min(0.98, 0.66 + abs(diferenca) / 3), 2),
            "motivo": "O usuário informa o proprio estado ou responde a pergunta anterior",
            "evidencias": evidencias,
        }
    return {
        "tipo": "AMBIGUO", "confianca": 0.42,
        "motivo": "perspectiva social insuficiente ou conflitante",
        "evidencias": evidencias,
    }
