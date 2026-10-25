"""Fonte e realizações do ato de responder nesta conversa.

Presença discursiva não é observação do corpo, exclusividade de atividade,
confirmação de entrega ou prova de um efeito externo.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


_PRESENCAS = ("Estou aqui conversando com você.", "Agora estou respondendo à sua mensagem.",
              "Estou acompanhando nossa conversa.")
_SAUDACOES = {"oi": "Oi! ", "ola": "Olá! ", "bom dia": "Bom dia! ",
             "boa tarde": "Boa tarde! ", "boa noite": "Boa noite! "}
_SENTIDO = ("Minha frase se refere à participação nesta conversa. "
            "Ela não informa outras atividades no computador nem o estado do corpo físico.")


def _presenca_integral(fala: Any) -> bool:
    return type(fala) is str and fala in {
        prefixo + p for prefixo in ("", *_SAUDACOES.values()) for p in _PRESENCAS}


def construir_fonte_sentido_presenca(texto: str, *, contrato: Mapping[str, Any],
                                     evidencia: Mapping[str, Any]) -> dict[str, Any] | None:
    """A entrega identifica a frase; sua gramática limita o significado.

    Isso não certifica como verdade as proposições livres do histórico.
    """
    falas = evidencia.get("falas")
    anterior = contrato.get("fala_anterior_relevante")
    if (dict(contrato.get("roteiro_concreto") or {}).get("estrategia") != "esclarecimento_literal"
        or contrato.get("origem") != "mente_unica" or contrato.get("autoriza_execucao") is not False
        or not contrato.get("turno_id") or not _presenca_integral(anterior)
        or evidencia.get("autoriza_execucao") is not False
        or evidencia.get("referencia_ambigua") is not False
        or not isinstance(falas, list) or len(falas) != 1 or not isinstance(falas[0], Mapping)
        or falas[0].get("fala") != anterior or not falas[0].get("id") or not falas[0].get("turno_id")
        or str(falas[0]["turno_id"]) == str(contrato["turno_id"])):
        return None
    return {"tipo": "sentido_presenca_observada_v1", "turno_id": str(contrato["turno_id"]),
            "texto_sha256": hashlib.sha256(texto.encode("utf8")).hexdigest(),
            "fala_observada_id": falas[0]["id"], "turno_fala": str(falas[0]["turno_id"]),
            "fala_observada": anterior, "autoriza_execucao": False,
            "estado_externo_verificado": False, "escopo": "sentido_da_frase_integral"}

def _ler_pergunta(texto: str) -> tuple[str, str] | None:
    normal = unicodedata.normalize("NFKD", texto.casefold())
    normal = "".join(c for c in normal if not unicodedata.combining(c))
    normal = re.sub(r"\s+", " ", normal).strip()
    # Leitura integral: aspas, complementos, passado, terceiros e atos adicionais
    # não cabem neste ato. Saudação é um prefixo opcional, nunca prova do restante.
    prefixo = r"(?:(?P<saudacao>oi|ola|bom dia|boa tarde|boa noite)(?: laylay)?[,! ]+|laylay, )?"
    pergunta = (r"(?:e )?(?:(?P<bem_estar>como (?:voce|tu) (?:esta|ta|vai))|"
                r"(?P<atividade>o que (?:voce|tu) (?:esta|ta) fazendo(?: agora)?))\??")
    leitura = re.fullmatch(prefixo + pergunta, normal)
    if leitura is None:
        return None
    return ("bem_estar" if leitura.group("bem_estar") else "atividade_atual",
            leitura.group("saudacao") or "")


def construir_fonte_presenca(texto: str, *, turno: Mapping[str, Any],
                            plano: Mapping[str, Any], mente: Mapping[str, Any]) -> dict[str, Any] | None:
    """O host atesta a autoria em curso; a proposta da IA não fornece esta fonte."""
    leitura = _ler_pergunta(texto)
    if (leitura is None or not turno.get("id")
        or str(plano.get("id")) != str(turno["id"])
        or (turno.get("texto_original") or turno.get("texto")) != texto
        or plano.get("texto_usuario") != texto
        or turno.get("autoriza_execucao") is not False
        or plano.get("requer_execucao") or plano.get("comandos")
        or turno.get("natureza_entrada") == "evento" or plano.get("natureza_entrada") == "evento"
        or dict(mente.get("modelo_corporal") or {}).get("companhia_ativa") is True):
        return None
    return {"tipo": "autoria_conversacional_em_curso_v1", "turno_id": str(turno["id"]),
            "texto_sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            "ato": leitura[0], "escopo": "resposta_a_utterance_atual",
            "estado_externo_verificado": False, "entrega_confirmada": False,
            "autoriza_execucao": False}


def realizacoes_presenca(texto: str, *, contrato: Mapping[str, Any], turno_id: Any,
                        modelo_corporal: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    # O retrato vivo é publicado pelo owner corporal também no plano. A fonte
    # de presença não deve suprimir o caminho corporal após uma transição.
    if (isinstance(modelo_corporal, Mapping) and turno_id
        and str(modelo_corporal.get("turno_id")) == str(turno_id)
        and modelo_corporal.get("companhia_ativa") is True):
        return ()
    fonte = contrato.get("fonte_presenca_conversacional")
    leitura = _ler_pergunta(texto)
    if (not isinstance(fonte, Mapping) or not turno_id
        or contrato.get("origem") != "mente_unica" or contrato.get("autoriza_execucao") is not False
        or str(contrato.get("turno_id")) != str(turno_id)
        or fonte.get("turno_id") != str(turno_id)
        or fonte.get("texto_sha256") != hashlib.sha256(texto.encode("utf-8")).hexdigest()
        or fonte.get("autoriza_execucao") is not False):
        return ()
    if fonte.get("tipo") == "sentido_presenca_observada_v1":
        if (dict(contrato.get("roteiro_concreto") or {}).get("estrategia") == "esclarecimento_literal"
            and _presenca_integral(fonte.get("fala_observada"))
            and contrato.get("fala_anterior_relevante") == fonte.get("fala_observada")
            and dict(contrato.get("roteiro_concreto") or {}).get("ancora_literal") == fonte.get("fala_observada")
            and fonte.get("fala_observada_id") and fonte.get("turno_fala")
            and fonte.get("turno_fala") != str(turno_id)):
            return (_SENTIDO,)
        return ()
    if (leitura is None or fonte.get("tipo") != "autoria_conversacional_em_curso_v1"
        or fonte.get("ato") != leitura[0]
        or dict(contrato.get("roteiro_concreto") or {}).get("ancora_literal") != texto):
        return ()
    prefixo = _SAUDACOES.get(leitura[1], "")
    return tuple(prefixo + p for p in _PRESENCAS)


def montar_pacote_presenca(texto: str, *, contrato: Mapping[str, Any], turno_id: Any,
                          modelo_corporal: Mapping[str, Any] | None = None) -> PacotePrompt | None:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    opcoes = realizacoes_presenca(texto, contrato=contrato, turno_id=turno_id, modelo_corporal=modelo_corporal)
    if not opcoes:
        return None

    def validar(dados: dict[str, Any]) -> None:
        if set(dados) != {"fala", "comandos"} or dados.get("fala") not in opcoes or dados.get("comandos") != []:
            raise ValueError("presenca_conversacional_extrapolada")

    codec = ContratoSaidaEstruturada(nome="presenca_conversacional_v1", marcador="PRESENCA_CONVERSACIONAL_V1",
        esquema={"type": "object", "additionalProperties": False, "required": ["fala", "comandos"],
                 "properties": {"fala": {"type": "string", "enum": list(opcoes)},
                                "comandos": {"type": "array", "maxItems": 0, "items": {"type": "object"}}}},
        validar=validar)
    return PacotePrompt((
        {"role": "system", "content": "Responda sobre sua presença nesta conversa com uma realização permitida. "
         "A fonte é a autoria atual, não um diagnóstico do corpo, observação externa, exclusividade de atividade "
         "ou confirmação de entrega. Preserve o ato e não acrescente outros fatos."},
        {"role": "user", "content": texto}), contexto_fechado=True, reserva_saida_tokens=192, contrato_saida=codec)
