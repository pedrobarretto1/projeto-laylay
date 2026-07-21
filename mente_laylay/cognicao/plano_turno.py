"""Planejamento e verificacao deterministica de um turno da mente unica."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Iterable

from mente_laylay.cognicao.coerencia_temporal import ajustar_fala_ao_periodo
from mente_laylay.personalidade.ritmo_natural import ajustar_encerramento_organico
from mente_laylay.especialistas.coordenador import registrar_resultado_operacional
from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.decisao_turno import criar_contrato_decisao


_REFERENCIAS_CURTAS = re.compile(
    r"\b(?:ele|ela|isso|aquilo|esse|essa|dele|dela|o mesmo|a mesma|de novo|tem certeza|entao voce|então você)\b",
    re.IGNORECASE,
)
_MARCADORES_MUSICA = re.compile(
    r"\b(?:musica|música|som|playlist|faixa|artista|cantor|banda|toca|ouvir)\b",
    re.IGNORECASE,
)
_MARCADORES_IDENTIDADE = re.compile(
    r"\b(?:meu nome|me chamo|pode me chamar|não sou|nao sou|me chama de)\b",
    re.IGNORECASE,
)
_MARCADORES_TEMPO = re.compile(
    r"\b(?:hora|horário|horario|manhã|manha|tarde|noite|madrugada|hoje|agora)\b",
    re.IGNORECASE,
)
_FALAS_VAGAS = (
    "estou aqui, me fala o proximo passo",
    "estou aqui, me fala o próximo passo",
    "tem uma ideia boa ai",
    "tem uma ideia boa aí",
    "lado mais humano disso",
    "deixar a ideia respirar",
    "lado mais vivo da coisa",
)
_VAZAMENTO_INTERNO = re.compile(
    r"^\s*[\[{].*(?:comandos?|aprendizados?|humor|intent|params)\s*[\"']?\s*:",
    re.IGNORECASE | re.DOTALL,
)
_ALEGACAO_EXECUCAO = re.compile(
    r"\b(?:pronto|feito|executei|abri|fechei|liguei|desliguei|toquei|coloquei|criei|apaguei|agendei)\b",
    re.IGNORECASE,
)
_ADMITE_NAO_EXECUCAO = re.compile(
    r"\b(?:não consegui|nao consegui|não executei|nao executei|preciso que|qual|confirma|não entendi|nao entendi)\b",
    re.IGNORECASE,
)


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip().casefold()


def _objetivo_ato(tipo: str) -> str:
    return {
        "comando": "executar a ação pedida e responder com o resultado real",
        "pergunta": "responder diretamente à pergunta atual",
        "correcao": "reconhecer a correção e atualizar o entendimento",
        "confirmacao": "resolver a pendência que foi realmente apresentada",
        "recusa": "encerrar ou reverter a pendência compatível",
        "deliberacao": "conversar sobre a possibilidade sem executar automaticamente",
        "reacao": "acolher a reação sem puxar assunto antigo",
        "conversa": "continuar o assunto da fala atual",
    }.get(str(tipo or "").strip().lower(), "responder à fala atual")


def _dominio_turno(texto: str, mente: Dict[str, Any]) -> str:
    t = _normalizar(texto)
    if _MARCADORES_MUSICA.search(t):
        return "musica"
    if re.search(r"\b(?:arquivo|pasta|renomeia|apaga|cria)\b", t):
        return "arquivo"
    if re.search(r"\b(?:ventilador|lâmpada|lampada|tomada|liga|desliga)\b", t):
        return "iot"
    if re.search(r"\b(?:abre|fecha|maximiza|janela|programa|app)\b", t):
        return "sistema"
    pendencia = mente.get("pendencia_atual") if isinstance(mente, dict) else {}
    if isinstance(pendencia, dict) and pendencia.get("status") == "ativa":
        return str(pendencia.get("dominio") or "conversa")
    return "conversa"


def planejar_turno(
    texto: str,
    *,
    turno: Dict[str, Any] | None = None,
    mente: Dict[str, Any] | None = None,
    periodo: str = "",
) -> Dict[str, Any]:
    """Transforma a leitura do turno em um compromisso explícito da mente."""
    leitura = dict(turno or {})
    estado = dict(mente or {})
    funcao_comunicativa = dict(leitura.get("funcao_comunicativa") or {})
    identidade = dict(leitura.get("identidade") or {})
    segmentos = leitura.get("segmentos") if isinstance(leitura.get("segmentos"), list) else []
    atos = []
    for indice, segmento in enumerate(segmentos):
        if not isinstance(segmento, dict):
            continue
        tipo = str(segmento.get("modalidade") or "conversa").strip().lower()
        atos.append({
            "ordem": indice,
            "tipo": tipo,
            "texto": str(segmento.get("texto") or "").strip()[:300],
            "objetivo": _objetivo_ato(tipo),
            "requer_execucao": tipo == "comando",
        })
    if not atos:
        tipo = str(leitura.get("ato_principal") or leitura.get("modalidade") or "conversa")
        atos.append({
            "ordem": 0,
            "tipo": tipo,
            "texto": str(texto or "").strip()[:300],
            "objetivo": _objetivo_ato(tipo),
            "requer_execucao": tipo == "comando",
        })

    contexto_necessario = ["fala_atual"]
    t = str(texto or "")
    tipos = {ato["tipo"] for ato in atos}
    if _REFERENCIAS_CURTAS.search(t):
        contexto_necessario.extend(["foco_recente", "ultima_acao"])
    if tipos & {"confirmacao", "recusa"}:
        contexto_necessario.append("pendencia_ativa")
    if _MARCADORES_MUSICA.search(t):
        contexto_necessario.append("preferencias_musicais")
    if _MARCADORES_IDENTIDADE.search(t):
        contexto_necessario.append("identidade_usuario")
    if identidade.get("referencia_laylay") or identidade.get("referencia_pedro"):
        contexto_necessario.append("identidade_interlocutores")
    if _MARCADORES_TEMPO.search(t):
        contexto_necessario.append("relogio_atual")
    contexto_necessario = list(dict.fromkeys(contexto_necessario))

    requer_execucao = any(bool(ato.get("requer_execucao")) for ato in atos)
    misto = requer_execucao and any(ato.get("tipo") != "comando" for ato in atos)
    if misto:
        resposta_esperada = "reconhecer a parte humana e informar o resultado real da ação em uma única fala"
    elif len(atos) > 1 and any(ato.get("tipo") == "pergunta" for ato in atos):
        resposta_esperada = (
            "reconhecer brevemente a parte social e responder diretamente à pergunta temática "
            "na mesma fala, sem ignorar nenhum dos atos"
        )
    elif requer_execucao:
        resposta_esperada = "informar uma única vez o resultado real da ação"
    else:
        resposta_esperada = _objetivo_ato(str(leitura.get("ato_principal") or atos[0]["tipo"]))
    if funcao_comunicativa.get("objetivo"):
        resposta_esperada = str(funcao_comunicativa.get("objetivo"))

    plano = {
        "id": int(leitura.get("id") or time.time_ns()),
        "texto_usuario": str(texto or "").strip()[:500],
        "modalidade": str(leitura.get("modalidade_geral") or leitura.get("modalidade") or "conversa"),
        "ato_principal": str(leitura.get("ato_principal") or leitura.get("modalidade") or atos[0]["tipo"]),
        "atos": atos,
        "dominio": _dominio_turno(t, estado),
        "contexto_necessario": contexto_necessario,
        "requer_execucao": requer_execucao,
        "misto": misto,
        "texto_operacional": str(leitura.get("texto_operacional") or "").strip()[:500],
        "texto_conversacional": str(leitura.get("texto_conversacional") or "").strip()[:500],
        "resposta_esperada": resposta_esperada,
        "funcao_comunicativa": str(funcao_comunicativa.get("funcao") or "informacao"),
        "emocao_implicita": str(funcao_comunicativa.get("emocao_implicita") or "neutra"),
        "postura_esperada": str(funcao_comunicativa.get("postura_esperada") or "natural"),
        "permite_pergunta": bool(funcao_comunicativa.get("permite_pergunta", True)),
        "identidade": identidade,
        "retrato_id": leitura.get("retrato_id"),
        "entidades": dict(leitura.get("entidades") or {}),
        "referencia_resolvida": dict(leitura.get("referencia_resolvida") or {}),
        "operacao_explicita": str(leitura.get("operacao_explicita") or ""),
        "especialistas": dict(leitura.get("especialistas") or {}),
        "atualidade_factual": dict(leitura.get("atualidade_factual") or {}),
        "modo_coordenacao": str(
            ((leitura.get("especialistas") or {}).get("coordenacao") or {}).get("modo") or "social"
        ),
        "confianca": round(float(leitura.get("confianca") or 0.0), 3),
        "periodo": str(periodo or "indefinido"),
        "fase": "planejado",
        "comandos": [],
        "problemas": [],
        "ts": time.time(),
    }
    plano["decisao_turno"] = criar_contrato_decisao(leitura, plano)
    return plano


def atualizar_plano_turno(
    plano: Dict[str, Any] | None,
    *,
    fase: str,
    comandos: Iterable[Dict[str, Any]] = (),
    erros: Iterable[str] = (),
    fala: str = "",
) -> Dict[str, Any]:
    novo = dict(plano or {})
    comandos_resumo = []
    for comando in comandos or ():
        if isinstance(comando, dict):
            comandos_resumo.append({
                "intent": str(comando.get("intent") or comando.get("acao") or "").strip(),
                "alvo": str(comando.get("alvo") or (comando.get("params") or {}).get("alvo") or "").strip(),
                "status": str(comando.get("status") or "").strip(),
                "executou": comando.get("executou"),
                "confirmado": comando.get("confirmado"),
                "confirmacao_oferecida": comando.get("confirmacao_oferecida"),
                "evidencia_confirmacao": comando.get("evidencia_confirmacao"),
            })
    novo.update({
        "fase": str(fase or novo.get("fase") or "planejado"),
        "comandos": comandos_resumo,
        "erros": [str(erro)[:300] for erro in (erros or ()) if str(erro).strip()],
        "fala_planejada": str(fala or "").strip()[:500],
        "atualizado_ts": time.time(),
    })
    novo["especialistas"] = registrar_resultado_operacional(
        dict(novo.get("especialistas") or {}),
        comandos_resumo,
    )
    return novo


def verificar_fala_turno(
    fala: str,
    *,
    plano: Dict[str, Any] | None,
    periodo: str = "",
    ultima_resposta: str = "",
    origem: str = "conversa",
) -> Dict[str, Any]:
    """Valida coerência básica sem inventar conteúdo ou executar ações."""
    contrato = dict(plano or {})
    texto_usuario = str(contrato.get("texto_usuario") or "")
    original = re.sub(r"\s+", " ", str(fala or "")).strip()
    ajustada = ajustar_encerramento_organico(original, texto_usuario)
    problemas: list[str] = []
    if ajustada != original:
        problemas.append("pergunta_opcional_removida")

    if not ajustada:
        return {
            "aceita": False, "fala": "", "acao": "bloqueada",
            "problemas": ["fala_vazia"], "pontuacao": 0.0,
        }

    fundamentacao = contrato.get("fundamentacao_factual")
    if not (isinstance(fundamentacao, dict) and fundamentacao.get("tema")) and contrato.get("dominio") == "musica":
        referencia = dict(contrato.get("referencia_resolvida") or {})
        fundamentacao = {
            "tema": str(referencia.get("nome") or "música").strip(),
            "titulo": str(referencia.get("nome") or "música").strip(),
            "resumo": "",
            "confiavel": False,
        }
    if isinstance(fundamentacao, dict) and fundamentacao.get("tema"):
        validacao_factual = validar_fala_com_fundamentacao(
            ajustada,
            fundamentacao=fundamentacao,
            texto_usuario=texto_usuario,
        )
        problemas_fatuais = list(validacao_factual.get("problemas") or [])
        if problemas_fatuais:
            problemas.extend(problemas_fatuais)
            ajustada = str(validacao_factual.get("fala") or ajustada).strip()

    validacao_alegacoes = validar_alegacoes_da_fala(
        ajustada,
        plano=contrato,
        origem=origem,
    )
    problemas_alegacoes = list(validacao_alegacoes.get("problemas") or [])
    if problemas_alegacoes:
        problemas.extend(problemas_alegacoes)
        ajustada = str(validacao_alegacoes.get("fala") or ajustada).strip()

    if _VAZAMENTO_INTERNO.search(ajustada):
        problemas.append("vazamento_formato_interno")
        ajustada = "Minha resposta saiu em formato interno e não ficou boa. Me fala de novo que eu respondo direito."

    base = _normalizar(ajustada)
    if any(marcador in base for marcador in _FALAS_VAGAS):
        problemas.append("resposta_vaga")
        if contrato.get("ato_principal") == "pergunta":
            ajustada = "Não consegui formular uma resposta concreta para essa pergunta. Pode repetir de outro jeito?"
        elif contrato.get("requer_execucao"):
            ajustada = "Entendi que você pediu uma ação, mas não consegui executá-la nem confirmar o resultado."
        else:
            ajustada = "Minha resposta ficou vaga. Vou me prender ao que você acabou de dizer."

    usuario_norm = _normalizar(texto_usuario)
    funcao_comunicativa = str(contrato.get("funcao_comunicativa") or "").strip().lower()
    if funcao_comunicativa == "conquista" and not re.search(
        r"\b(?:parab[eé]ns|a[ií] sim|mandou bem|boa|merecid|orgulho|nota m[aá]xima)\b",
        ajustada,
        flags=re.IGNORECASE,
    ):
        problemas.append("conquista_sem_reconhecimento")
        ajustada = f"Aí sim, parabéns por isso. {ajustada}"
    if funcao_comunicativa == "correcao" and not re.search(
        r"\b(?:entendi|corrigi|corre[cç][aã]o|voc[eê] tem raz[aã]o|ajustei)\b",
        ajustada,
        flags=re.IGNORECASE,
    ):
        problemas.append("correcao_sem_reconhecimento")
        ajustada = f"Entendi a correção. {ajustada}"
    if not bool(contrato.get("permite_pergunta", True)) and "?" in ajustada:
        problemas.append("pergunta_inadequada_a_funcao_emocional")
        frases_sem_pergunta = [
            trecho for trecho in re.split(r"(?<=[.!?])\s+", ajustada)
            if trecho and "?" not in trecho
        ]
        fallbacks = {
            "encerramento": "Até mais.",
            "correcao": "Entendi a correção e vou considerar isso daqui para frente.",
            "agradecimento": "Que nada. Fico feliz que tenha ajudado.",
            "elogio": "Obrigada. Gostei de ouvir isso.",
            "frustracao": "Entendi. Vou corrigir isso sem insistir no erro.",
            "decepcao": "Entendi a decepção. Vou tratar isso com mais cuidado.",
        }
        ajustada = " ".join(frases_sem_pergunta).strip() or fallbacks.get(
            funcao_comunicativa, "Entendi o que você quis dizer."
        )
    pede_referencia = any(x in usuario_norm for x in ("como assim", "o que quis dizer", "explica", "tipo o que"))
    if not pede_referencia and any(x in _normalizar(ajustada) for x in ("eu tava falando de", "o ponto sobre", "o fio era")):
        problemas.append("contexto_antigo_sem_referencia")
        ajustada = "Eu puxei um contexto que você não pediu. Vou responder somente ao que você disse agora."

    comandos = contrato.get("comandos") if isinstance(contrato.get("comandos"), list) else []
    if contrato.get("requer_execucao") and not comandos and str(origem) in {"ia_final", "resposta_ia"}:
        if _ALEGACAO_EXECUCAO.search(ajustada) or not _ADMITE_NAO_EXECUCAO.search(ajustada):
            problemas.append("comando_sem_execucao_confirmada")
            ajustada = "Entendi a ação que você pediu, mas não executei nem confirmei o resultado."

    if periodo:
        temporal = ajustar_fala_ao_periodo(ajustada, periodo)
        if temporal != ajustada:
            problemas.append("incoerencia_temporal_corrigida")
            ajustada = temporal

    if ultima_resposta and _normalizar(ultima_resposta) == _normalizar(ajustada):
        problemas.append("repeticao_exata")
        # A repetição continua registrada para diagnóstico, mas não deve vazar
        # como uma fala metalinguística. Repetir uma resposta útil é mais
        # natural do que comentar o funcionamento interno da própria resposta.

    acao = "ajustada" if problemas else "aceita"
    pontuacao = max(0.0, 1.0 - (0.18 * len(problemas)))
    return {
        "aceita": True,
        "fala": ajustada,
        "acao": acao,
        "problemas": problemas,
        "pontuacao": round(pontuacao, 2),
    }
