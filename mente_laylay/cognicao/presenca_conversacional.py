"""Fonte e realizações do ato de responder nesta conversa.

Presença discursiva não é observação do corpo, exclusividade de atividade,
confirmação de entrega ou prova de um efeito externo.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Mapping, TYPE_CHECKING
from mente_laylay.cognicao.normalizacao_linguagem import (
    SAUDACOES_CONVERSACIONAIS, SAUDACOES_TEMPORAIS, separar_saudacao_inicial,
)

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


_PRESENCAS = ("Estou aqui conversando com você.", "Agora estou respondendo à sua mensagem.",
              "Estou acompanhando nossa conversa.")
_SAUDACOES = SAUDACOES_CONVERSACIONAIS
_RECIPROCIDADES = ("Tudo bem por aqui. E com você?",
                  "Estou por aqui, pronta para conversar. Como você está?",
                  "Por aqui, tudo tranquilo. E por aí?")
_ABERTURAS = ("Como você está?", "Bom ter você por aqui.", "Vamos conversar?")
_DESPEDIDAS = ("Até mais!", "Tudo bem. Até a próxima!", "Combinado, até mais! Se cuida.")
_SENTIDO = ("Minha frase se refere à participação nesta conversa. "
            "Ela não informa outras atividades no computador nem o estado do corpo físico.")
_SENTIDO_CORTESIA = "Eu estava retribuindo sua gentileza e dizendo que estou por aqui para conversar."
_SENTIDO_DESPEDIDA = "Quis respeitar seu encerramento da conversa e me despedir."


def _presenca_integral(fala: Any) -> bool:
    return type(fala) is str and fala in {
        f for ato in ('saudacao', 'cortesia_temporal', 'cortesia', 'bem_estar', 'atividade_atual', 'encerramento')
        for saudacao in ('', *_SAUDACOES) for f in _realizacoes_do_ato(ato, saudacao)}


def _realizacoes_do_ato(ato: str, saudacao: str) -> tuple[str, ...]:
    if ato == 'encerramento':
        return _DESPEDIDAS
    prefixo = _SAUDACOES.get(saudacao, '')
    if ato == 'cortesia_temporal':
        # Reciprocidade compatível com chegada ou saída, sem impor pergunta
        # nem declarar um encerramento que o usuário não explicitou.
        return (prefixo.rstrip(), prefixo + 'Estou por aqui.') if prefixo else ()
    if ato == 'saudacao':
        return tuple(prefixo + p for p in _ABERTURAS) if prefixo else ()
    presencas = tuple(prefixo + p for p in _PRESENCAS)
    if ato == 'atividade_atual':
        return presencas
    # A saudação integra a primeira frase da reciprocidade, em vez de
    # acrescentar uma terceira frase ao limite contratual de duas.
    cortesia = tuple((prefixo.replace('! ', ', ') + p[:1].lower() + p[1:]) if prefixo else p
                     for p in _RECIPROCIDADES) + (prefixo + 'Tudo bem comigo.',)
    return cortesia + presencas if ato == 'bem_estar' else cortesia


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
    saudacao, corpo = separar_saudacao_inicial(normal)
    if not saudacao:
        corpo = re.sub(r'^(?:laylay|lay)[, ]+', '', corpo)
    if saudacao and not corpo:
        return ('cortesia_temporal' if saudacao in SAUDACOES_TEMPORAIS else 'saudacao'), saudacao
    corpo = re.sub(r'^e\s+', '', corpo)
    if re.fullmatch(r'como (?:voce|tu) (?:esta|ta|vai)[?!.]*', corpo):
        return 'bem_estar', saudacao
    if re.fullmatch(r'o que (?:voce|tu) (?:esta|ta) fazendo(?: agora)?[?!.]*', corpo):
        return 'atividade_atual', saudacao
    # Cortesia integral, não consulta sobre o dia literal, retrospectiva,
    # corpo, programa ou disponibilidade. Complementos ficam fora deste ato.
    if (re.fullmatch(r'tudo (?:bem|certo)(?: com (?:voce|tu)| por ai)?[?!.]*', corpo)
        or re.fullmatch(r'como (?:esta|ta|vai) (?:o )?(?:seu|teu) dia[?!.]*', corpo)):
        return 'cortesia', saudacao
    return None


def _ler_ato_atual(texto: str, encerramento: Any) -> tuple[str, str] | None:
    # Consome a decisão da sessão, confirmada pelo MESMO leitor canônico.
    # Não mantém uma lista privada nem extrai despedida de um pedido composto.
    if encerramento == 'sessao':
        from mente_laylay.memoria_mental.sessao_conversa import texto_encerra_conversa
        if texto_encerra_conversa(texto):
            return 'encerramento', ''
        return None
    return _ler_pergunta(texto)


def construir_fonte_presenca(texto: str, *, turno: Mapping[str, Any],
                            plano: Mapping[str, Any], mente: Mapping[str, Any]) -> dict[str, Any] | None:
    """O host atesta a autoria em curso; a proposta da IA não fornece esta fonte."""
    leitura = _ler_ato_atual(texto, turno.get('encerramento_assunto'))
    if (leitura is None or not turno.get("id")
        or str(plano.get("id")) != str(turno["id"])
        or (turno.get("texto_original") or turno.get("texto")) != texto
        or plano.get("texto_usuario") != texto
        or turno.get("autoriza_execucao") is not False
        or plano.get("requer_execucao") or plano.get("comandos")
        or turno.get("natureza_entrada") == "evento" or plano.get("natureza_entrada") == "evento"
        or (leitura[0] == 'encerramento' and (plano.get('autoriza_execucao') is not False
            or not isinstance(plano.get('decisao_turno'), Mapping)
            or plano['decisao_turno'].get('permite_acao') is not False))
        or (dict(mente.get("modelo_corporal") or {}).get("companhia_ativa") is True
            and leitura[0] != 'encerramento')):
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
    fonte = contrato.get("fonte_presenca_conversacional")
    encerrando = (contrato.get('encerramento_assunto') == 'sessao'
        and isinstance(fonte, Mapping) and fonte.get('ato') == 'encerramento')
    if (isinstance(modelo_corporal, Mapping) and turno_id
        and str(modelo_corporal.get("turno_id")) == str(turno_id)
        and modelo_corporal.get("companhia_ativa") is True and not encerrando):
        return ()
    leitura = _ler_ato_atual(texto, contrato.get('encerramento_assunto'))
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
            original = fonte['fala_observada']
            presencas = {prefixo + p for prefixo in ('', *_SAUDACOES.values()) for p in _PRESENCAS}
            return (_SENTIDO if original in presencas else
                    _SENTIDO_DESPEDIDA if original in _DESPEDIDAS else _SENTIDO_CORTESIA,)
        return ()
    if (leitura is None or fonte.get("tipo") != "autoria_conversacional_em_curso_v1"
        or fonte.get("ato") != leitura[0]
        or dict(contrato.get("roteiro_concreto") or {}).get("ancora_literal") != texto):
        return ()
    return _realizacoes_do_ato(*leitura)


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
        {"role": "system", "content": "Você é Laylay. Retribua a cortesia ou responda sobre sua presença "
         "nesta conversa com uma realização permitida, natural e curta. Prefira reciprocidade acolhedora "
         "nas perguntas de bem-estar; nas perguntas de atividade, responda o que faz nesta conversa. "
         "Quando o ato é encerramento, respeite a despedida: não reabra pergunta, convite, oferta ou assunto. "
         "Não apresente diagnóstico técnico nem invente um dia de experiências. "
         "A fonte é a autoria atual, não um diagnóstico do corpo, observação externa, exclusividade de atividade "
         "ou confirmação de entrega. Preserve o ato e não acrescente outros fatos."},
        {"role": "user", "content": texto}), contexto_fechado=True, reserva_saida_tokens=192, contrato_saida=codec)
