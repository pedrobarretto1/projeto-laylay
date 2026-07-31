"""Direção final de voz: contexto, personalidade e ritmo sem mudar fatos."""

from __future__ import annotations

import re
import time
from typing import Any, Dict


_ABERTURAS_MECANICAS = re.compile(
    r"^(?:a-?ah\.\.\.|aí sim\.\.\.|ai sim\.\.\.|entendi[,.]|tá[,.]|ta[,.])\s*",
    re.IGNORECASE,
)

PERFIL_PERSONALIDADE = {
    "base": "carinhosa_sem_infantilizar",
    "humor": "debochado_leve_quando_houver_intimidade",
    "curiosidade": "seletiva",
    "correcao": "receptiva_sem_se_defender",
    "operacional": "objetiva_com_calor_humano",
}


def _sem_pergunta_opcional(texto: str, *, permite: bool) -> str:
    fala = str(texto or "").strip()
    if permite or "?" not in fala:
        return fala
    # Perguntas que desbloqueiam uma decisão real não são floreio.
    if re.search(
        r"\b(?:confirma|posso prosseguir|quer que eu execute|qual|onde|quando|"
        r"que horas|em quantos minutos|voc[eê] quis|foi isso|qual dispositivo)\b",
        fala,
        flags=re.IGNORECASE,
    ):
        return fala
    partes = [p.strip() for p in re.split(r"(?<=[.!?])\s+", fala) if p.strip()]
    sem_perguntas = [parte for parte in partes if "?" not in parte]
    return " ".join(sem_perguntas).strip() or fala.replace("?", ".")


def _reduzir_abertura_repetida(texto: str, ultima_fala: str) -> str:
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    abertura = _ABERTURAS_MECANICAS.match(fala)
    if not abertura:
        return fala
    ultima = re.sub(r"\s+", " ", str(ultima_fala or "")).strip()
    abertura_anterior = _ABERTURAS_MECANICAS.match(ultima)
    if abertura_anterior or abertura.group(0).casefold().startswith("a-ah"):
        restante = fala[abertura.end():].strip()
        if restante:
            return restante[0].upper() + restante[1:]
    return fala


def _tom_por_contexto(politica: str, emocao: str, operacional: bool) -> str:
    if operacional:
        return "objetiva_calorosa"
    return {
        "encerrar": "serena",
        "reconhecer_sem_pergunta": "calorosa",
        "reparar_sem_se_defender": "receptiva",
        "acolher_antes_de_sugerir": "acolhedora",
        "reconhecer_e_continuar": "interessada",
    }.get(politica, str(emocao or "natural"))


def _substituir_resposta_social_mecanica(
    texto: str,
    *,
    funcao: str,
    mente: Dict[str, Any],
) -> str:
    """Troca apenas respostas genéricas conhecidas; não reescreve fala livre."""
    fala = str(texto or "").strip()
    base = fala.casefold()
    mecanica = any(sinal in base for sinal in (
        "isso foi fofo. vou guardar aqui",
        "vou guardar esse elogio",
        "eu ia responder toda confiante",
    ))
    if not mecanica:
        return fala
    assunto = dict(mente.get("assunto_estruturado_atual") or {})
    alvo = str(mente.get("ultima_acao_alvo") or assunto.get("titulo") or "").strip()
    if funcao == "agradecimento":
        return (
            f"Que nada. Fico feliz que tenha ajudado com {alvo}."
            if alvo else "Que nada. Fico feliz que tenha ajudado."
        )
    if funcao == "elogio":
        return "Obrigada... isso me deixou um pouquinho sem jeito."
    return fala


def _lapidar_presenca_social(
    texto: str,
    *,
    funcao: str,
    mente: Dict[str, Any],
    operacional: bool,
) -> str:
    """Dá presença a respostas sociais vazias sem enfeitar conteúdo útil."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    if operacional or not fala:
        return fala
    base = fala.casefold().strip(" .!…")
    generica = base in {
        "entendi", "certo", "ok", "tá bom", "ta bom", "beleza",
        "que bom", "legal", "parabéns", "parabens", "de nada",
        "por nada", "tudo bem", "sem problema",
    }
    if not generica:
        return fala

    alvo = str(
        mente.get("ultima_acao_alvo")
        or mente.get("ultimo_alvo")
        or dict(mente.get("assunto_estruturado_atual") or {}).get("titulo")
        or ""
    ).strip()
    respostas = {
        "agradecimento": (
            f"Que nada. Fico feliz que tenha ajudado com {alvo}."
            if alvo else "Que nada. Fico feliz que tenha ajudado de verdade."
        ),
        "elogio": "Obrigada... você tem um talento meio perigoso pra desmontar minha pose.",
        "conquista": "Aí sim. Essa é daquelas vitórias que merecem um segundo de orgulho.",
        "desabafo": "Eu ouvi. Não vou te apressar nem transformar isso em tarefa.",
        "inseguranca": "Eu entendo a dúvida. Vamos sem promessa vazia e sem te diminuir.",
        "frustracao": "Eu entendi o incômodo. Ajusto o rumo sem tentar me defender.",
        "correcao": "Você fez bem em corrigir. Ajustei o rumo e sigo daqui.",
        "decepcao": "Eu entendi. Não vou cobrir essa decepção com uma explicação bonita.",
        "brincadeira": "Tá, essa me pegou. Minha dignidade digital sobrevive, mas por pouco.",
        "encerramento": "Fechado. Vai no teu ritmo; eu fico por aqui.",
        "reacao_positiva": "Aí sim. Bom quando as coisas encaixam sem precisar de novela.",
    }
    return respostas.get(str(funcao or "").casefold(), fala)


def dirigir_fala(
    texto: str,
    *,
    texto_usuario: str = "",
    estado_mental: Dict[str, Any] | None = None,
    emocao: str = "calma",
    nivel: int | None = 1,
    proativa: bool = False,
    preservar_texto: bool = False,
    agora: float | None = None,
) -> Dict[str, Any]:
    """Escolhe a expressão final sem reescrever resultados ou conteúdo factual."""
    mente = dict(estado_mental or {})
    instante = float(agora if agora is not None else time.time())
    especialistas = {} if proativa else dict(mente.get("especialistas_turno_atual") or {})
    social = dict(especialistas.get("social") or {})
    operacional = dict(especialistas.get("operacional") or {})
    politica = str(social.get("politica_resposta") or "responder_diretamente")
    tem_operacao = bool(operacional.get("ativo"))
    permite_pergunta = bool(social.get("permite_pergunta", True)) and not tem_operacao
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    funcao = str(social.get("funcao") or "")
    if not preservar_texto:
        fala = _substituir_resposta_social_mecanica(fala, funcao=funcao, mente=mente)
        fala = _lapidar_presenca_social(
            fala,
            funcao=funcao,
            mente=mente,
            operacional=tem_operacao,
        )
        fala = _sem_pergunta_opcional(fala, permite=permite_pergunta)
        fala = _reduzir_abertura_repetida(fala, str(mente.get("ultima_resposta") or ""))

    emocao_final = str(emocao or "calma").strip().lower()
    nivel_final = max(1, min(3, int(nivel or 1)))
    if not proativa:
        if funcao == "elogio":
            emocao_final, nivel_final = "envergonhada", max(1, min(2, nivel_final))
        elif funcao == "conquista":
            emocao_final, nivel_final = "alegre", max(2, nivel_final)
        elif funcao in {"frustracao", "correcao", "decepcao"}:
            emocao_final, nivel_final = "calma", 1
        elif funcao in {"desabafo", "inseguranca"}:
            emocao_final, nivel_final = "triste", 1
        elif tem_operacao and emocao_final in {"brava", "irritada"}:
            # Falha técnica não fabrica raiva; o resultado continua claro.
            emocao_final, nivel_final = "calma", 1

        # Uma emoção social pode deixar um rastro leve no turno seguinte,
        # mas nunca domina comando, correção ou assunto sensível.
        anterior = dict(mente.get("direcao_fala_atual") or {})
        idade_anterior = instante - float(anterior.get("ts") or 0.0)
        if (
            funcao in {"", "informacao"}
            and not tem_operacao
            and 0.0 <= idade_anterior <= 90.0
            and str(anterior.get("emocao") or "") in {"alegre", "envergonhada", "surpresa"}
        ):
            emocao_final = str(anterior.get("emocao"))
            nivel_final = 1

    palavras = len(re.findall(r"\b\w+\b", fala, flags=re.UNICODE))
    comprimento = "curto" if palavras <= 18 else "medio" if palavras <= 55 else "longo"
    humor = "leve" if funcao in {"brincadeira", "elogio"} and not tem_operacao else "nenhum"
    return {
        "fala": fala,
        "tom": _tom_por_contexto(politica, emocao_final, tem_operacao),
        "emocao": emocao_final,
        "nivel": nivel_final,
        "comprimento": comprimento,
        "permite_pergunta": permite_pergunta,
        "humor": humor,
        "politica": politica,
        "memoria": "sutil",
        "formato": "fala",
        "preservar_resultado_operacional": tem_operacao,
        "perfil_personalidade": dict(PERFIL_PERSONALIDADE),
        "texto_usuario": str(texto_usuario or "")[:300],
        "ts": instante,
    }
