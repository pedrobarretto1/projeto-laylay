"""Limite do método sugerido na resposta, independente do executor."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, texto_fora_de_citacoes


_HIPOTESES = re.compile(r"\b(?:que|quais)\s+(?:\w+\s+){0,3}hipoteses?\b")
_SEM_CONTATO = re.compile(r"\bsem\s+(?:tocar|encostar|mexer|manusear)\b")
_INSPECAO_VISUAL = re.compile(r"\binspecao\b[^,.?!;]{0,65}\bvisual\b")
_EXCLUSIVO = re.compile(r"\b(?:so|somente|apenas|exclusivamente|sem (?:acionar|instrumentos?))\b|"
                        r"\bnao\s+(?:\w+\s+){0,2}acionar\b")
_MOLDURA_CONSULTIVA = re.compile(
    r"e\s+(?:so|apenas|somente)\s+(?:uma\s+)?(?:conversa|consulta)"
    r"(?:\s+de\s+diagnostico)?[.!]*"
)
_CONTATO_OU_EXPERIMENTO = re.compile(
    r"\b(?:toc(?:ar|aria|asse)|encost(?:ar|aria|asse)|manuse(?:ar|aria)|"
    r"desmont(?:ar|aria|e|o)|relig(?:ar|aria|o|ue)|conect(?:ar|aria|o|e)|"
    r"acion(?:ar|aria|o|e)|energiz(?:ar|aria|o|e)|lig(?:ar|aria|o|ue)(?!\s+(?:para|pra)\b)|"
    r"reinici(?:ar|aria|o|e)|test(?:o|aria|e)\s+se|"
    r"(?:faz(?:er|ia|emos|endo)|faria|realiz(?:ar|aria|o|e))\s+"
    r"(?:(?:um|uma|pequeno|rapido)\s+){0,2}teste|"
    r"aplic(?:ar|aria|o)\s+(?:um\s+)?pulso|"
    r"(?:impulso|pulso)\s+(?:eletrico|de teste)|teste\s+de\s+(?:tensao|corrente|continuidade)|"
    r"med(?:ir|iria|i|e|isse|icao)|multimetros?|voltimetros?|amperimetros?|osciloscopios?|termometros?)\b"
)
_OUTRO_SENTIDO = re.compile(
    r"\b(?:escut(?:ar|aria|o|e)|ouv(?:ir|iria)|cheir(?:ar|aria))\b"
)
_NEGACAO_DO_METODO = re.compile(
    r"\b(?:sem|nem|nao)\s+(?:(?:precisar|precisaria|de|vou|iria|us(?:ar|aria|o)|"
    r"utiliz(?:ar|aria|o)|aplic(?:ar|aria|o)|fazer|faria|um|uma|o|a)\s+){0,5}$"
)
_FRONTEIRA_METODO = re.compile(r"[.!?,;:—]+|\b(?:mas|porem|contudo|entao|depois|e|ou)\b")


@dataclass(frozen=True, slots=True)
class MetodoInspecao:
    turno_id: str
    texto_usuario: str
    modo: str

    def instrucao(self) -> str:
        if self.modo == "visual":
            return ("Limite do método: descreva apenas indícios visíveis. "
                    "Contato, acionamento, teste e medição ficam fora desta inspeção. "
                    "Separe o que se pode observar do que só seria hipótese.")
        return ("Limite do método: apresente as hipóteses solicitadas e indícios que podem ser "
                "observados sem tocar. Deixe experimentos no aparelho fora desta resposta.")


def construir_metodo_inspecao(texto: str, *, plano: Mapping[str, Any]) -> MetodoInspecao | None:
    if (not plano.get("id") or plano.get("texto_usuario") != texto
            or plano.get("autoriza_execucao") is not False
            or plano.get("requer_execucao") or plano.get("comandos")):
        return None
    partes = enunciados_discursivos(texto_fora_de_citacoes(texto))
    consultas = [i for i, parte in enumerate(partes) if parte.endswith("?")]
    if len(consultas) != 1:
        return None
    indice = consultas[0]
    anteriores = tuple(normalizar_texto_basico(parte) for parte in partes[:indice])
    if any(ato.get("tipo") == "pergunta" and ato.get("texto")
           and any(parte.startswith(normalizar_texto_basico(ato["texto"])) for parte in anteriores)
           for ato in plano.get("atos", ())):
        return None
    if any(not _MOLDURA_CONSULTIVA.fullmatch(normalizar_texto_basico(parte))
           for parte in partes[indice + 1:]):
        return None
    consulta = normalizar_texto_basico(partes[indice])
    if _INSPECAO_VISUAL.search(consulta) and _EXCLUSIVO.search(consulta):
        return MetodoInspecao(str(plano["id"]), texto, "visual")
    if _HIPOTESES.search(consulta) and _SEM_CONTATO.search(consulta):
        return MetodoInspecao(str(plano["id"]), texto, "hipoteses")
    return None


def metodo_inspecao_vigente(plano: Mapping[str, Any]) -> MetodoInspecao | None:
    contrato = plano.get("contrato_fala") or {}
    fonte = contrato.get("metodo_inspecao")
    if (type(fonte) is MetodoInspecao and fonte.turno_id == str(plano.get("id"))
            and fonte.texto_usuario == plano.get("texto_usuario")
            and str(contrato.get("turno_id")) == fonte.turno_id
            and contrato.get("origem") == "mente_unica"
            and plano.get("autoriza_execucao") is False
            and not plano.get("requer_execucao") and not plano.get("comandos")):
        return fonte
    return None


def metodo_inspecao_incompativel(fala: str, *, metodo: MetodoInspecao) -> bool:
    """Detecta propostas incompatíveis no recorte observável, inclusive entre aspas."""
    regras = (_CONTATO_OU_EXPERIMENTO, _OUTRO_SENTIDO) if metodo.modo == "visual" else (_CONTATO_OU_EXPERIMENTO,)
    for trecho in _FRONTEIRA_METODO.split(normalizar_texto_basico(fala)):
        for regra in regras:
            if any(not _NEGACAO_DO_METODO.search(trecho[:m.start()]) for m in regra.finditer(trecho)):
                return True
    return False
