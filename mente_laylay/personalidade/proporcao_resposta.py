"""Ajusta tamanho de respostas sem decidir intenção ou conteúdo."""

from __future__ import annotations

import re
from typing import Dict


def parece_problema_matematico(texto: str) -> bool:
    """Reconhece fórmulas compactas que não podem ser tratadas como fala curta."""
    bruto = str(texto or "").strip()
    base = bruto.casefold()
    tem_numero_ou_variavel = bool(re.search(r"\d|\b[xyz]\b|\d[xyz]\b", base))
    tem_notacao_forte = bool(re.search(r"[=<>≤≥√∑∫^]|\\(?:frac|sqrt|times|div)\b", bruto))
    operadores = len(re.findall(r"(?<!\w)[+*/÷×](?!\w)|(?<=\d)[+*/-]|[+*/-](?=\d)", bruto))
    pedido_explicito = bool(re.search(
        r"\b(?:resolv[ae]|calcule|equação|equacao|sistema|integral|derivada|"
        r"raiz|fração|fracao|problema matemático|problema matematico)\b",
        base,
    ))
    return bool(
        (tem_numero_ou_variavel and tem_notacao_forte)
        or (tem_numero_ou_variavel and operadores >= 2)
        or (pedido_explicito and (tem_numero_ou_variavel or tem_notacao_forte))
    )


def parece_pedido_reexplicacao(texto: str) -> bool:
    """Reconhece correções curtas que pedem uma nova explicação completa."""
    base = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
    if not base:
        return False
    return bool(re.search(
        r"\b(?:n[aã]o\s+entendi|n[aã]o\s+compreendi|n[aã]o\s+ficou\s+claro|"
        r"fiquei\s+(?:perdido|perdida|confuso|confusa)|explica\s+(?:de\s+novo|melhor|"
        r"mais\s+devagar|(?:isso\s+)?(?:de\s+um\s+jeito|de\s+forma)\s+simples)|"
        r"refaz(?:\s+(?:a\s+explica[cç][aã]o|os\s+passos?))?|"
        r"repete\s+(?:a\s+explica[cç][aã]o|os\s+passos?))\b",
        base,
    ))


def classificar_proporcao(texto_usuario: str, tipo_interacao: str = "") -> str:
    texto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    base = texto.casefold()
    palavras = base.split()
    tipo = str(tipo_interacao or "").strip().lower()

    if tipo in {"acao", "aprendizado"}:
        return "tecnica"
    # ``3(2x-5)-4(x+1)=...`` possui uma única palavra para o contador comum,
    # mas exige desenvolvimento e conclusão. Precisa ser reconhecida antes
    # da regra genérica de mensagens com até quatro palavras.
    if parece_problema_matematico(texto):
        return "matematica"
    if parece_pedido_reexplicacao(texto):
        return "explicativa"
    if any(sinal in base for sinal in (
        "explica detalhadamente", "explica melhor", "me explica direito",
        "quero entender", "passo a passo", "com detalhes", "aprofund",
        "por que isso acontece", "como isso funciona", "como funciona",
    )):
        return "explicativa"
    if any(sinal in base for sinal in (
        "estou triste", "to triste", "tô triste", "estou cansado",
        "estou cansada", "to mal", "tô mal", "desabafar", "me sinto",
        "estou preocupado", "estou preocupada", "não aguento", "nao aguento",
    )):
        return "emocional"
    if tipo == "confirmacao" or len(palavras) <= 8 and "?" not in texto:
        return "curta"
    if "?" in texto and len(palavras) <= 12:
        return "objetiva"
    if "?" not in texto and len(palavras) <= 16:
        return "objetiva"
    return "normal"


LIMITES: Dict[str, tuple[int, int]] = {
    "curta": (2, 220),
    "objetiva": (3, 360),
    "emocional": (5, 700),
    "explicativa": (7, 1000),
    "normal": (5, 600),
    "tecnica": (3, 460),
    "matematica": (14, 1800),
}


def _perfil_exigido_pela_propria_resposta(texto: str) -> str:
    """Impede que uma explicação real seja mutilada por uma entrada elíptica."""
    fala = str(texto or "")
    passos = len(re.findall(r"(?:^|\s)\d{1,2}[.)]\s+", fala))
    equacoes = len(re.findall(
        r"(?:\d|[xyz])\s*=\s*(?:-?\d|[xyz(])",
        fala,
        re.IGNORECASE,
    ))
    operadores = len(re.findall(
        r"(?<=\d)\s*[+*/-]\s*(?=\d|[xyz])|(?<=[xyz])\s*[+*/-]\s*(?=\d)",
        fala,
        re.IGNORECASE,
    ))
    conectores = len(re.findall(
        r"\b(?:primeiro|depois|em\s+seguida|agora|por\s+fim|portanto|logo|"
        r"isso\s+significa|em\s+outras\s+palavras)\b",
        fala,
        re.IGNORECASE,
    ))
    if equacoes >= 2 or (equacoes >= 1 and operadores >= 3):
        return "matematica"
    if passos >= 2 or (len(fala) > 240 and conectores >= 3):
        return "explicativa"
    return ""


def _dividir_frases(texto: str) -> list[str]:
    """Separa frases sem transformar marcadores ``1.`` em frases isoladas."""
    protegido = re.sub(r"(?<!\w)(\d{1,2})\.\s+", r"\1§ ", str(texto or ""))
    partes = [
        f.replace("§", ".").strip()
        for f in re.split(r"(?<=[.!?…])\s+", protegido)
        if f.strip()
    ]
    return partes


def ajustar_proporcao_resposta(
    fala: str,
    texto_usuario: str,
    tipo_interacao: str = "",
    *,
    possui_comandos: bool = False,
) -> str:
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    if not texto or possui_comandos:
        return texto

    perfil = classificar_proporcao(texto_usuario, tipo_interacao)
    perfil_resposta = _perfil_exigido_pela_propria_resposta(texto)
    if perfil in {"curta", "objetiva"} and perfil_resposta:
        perfil = perfil_resposta
    max_frases, max_chars = LIMITES[perfil]
    frases = _dividir_frases(texto)
    if len(texto) <= max_chars and len(frases) <= max_frases:
        return texto
    if len(frases) <= 1:
        # Não corta uma ideia no meio quando o modelo produziu uma frase longa.
        return texto

    escolhidas = []
    total = 0
    for frase in frases:
        novo_total = total + len(frase) + (1 if escolhidas else 0)
        if escolhidas and (len(escolhidas) >= max_frases or novo_total > max_chars):
            break
        escolhidas.append(frase)
        total = novo_total

    return " ".join(escolhidas).strip() or texto


def limite_tokens_resposta(
    texto_usuario: str,
    *,
    modo_rapido: bool = False,
    depende_contexto: bool = False,
) -> int:
    perfil = classificar_proporcao(texto_usuario, "")
    limites = {
        "curta": 128,
        "objetiva": 224,
        "emocional": 320,
        "explicativa": 512,
        "normal": 384,
        "tecnica": 320,
        "matematica": 800,
    }
    limite = limites.get(perfil, 520)
    if depende_contexto and perfil in {"curta", "objetiva"}:
        limite = max(limite, limites["explicativa"])
    if modo_rapido:
        return min(limite, 128)
    return limite
