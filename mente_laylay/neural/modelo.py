"""Modelo local pequeno e versionado para interpretação geral de comandos."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
import unicodedata
from typing import Any, Callable, Iterable, Mapping

import joblib
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline

from .encoder_semantico import EncoderSemanticoHibrido, EncoderSemanticoONNX


ESTRATEGIAS_PERMITIDAS = frozenset(
    {"logistic", "sgd_log_loss", "complement_nb"}
)
ARQUITETURAS_ACAO_PERMITIDAS = frozenset({"global", "hierarchical"})
ARQUITETURAS_COMANDO_PERMITIDAS = frozenset({
    "independent",
    "intent_gated",
})
REPRESENTACOES_PERMITIDAS = frozenset(
    {"tfidf", "tfidf_indicadores", "onnx_semantico", "onnx_semantico_hibrido"}
)
REPRESENTACOES_SEMANTICAS = frozenset(
    {"onnx_semantico", "onnx_semantico_hibrido"}
)
FEATURES_COMANDO_PERMITIDAS = frozenset({
    "legado",
    "modalidade_v1",
    "modalidade_por_intent_v1",
    "modalidade_v2",
    "modalidade_por_intent_v2",
    "modalidade_v3",
    "modalidade_por_intent_v3",
    "modalidade_v4_sparse",
    "modalidade_por_intent_v4_sparse",
})
FEATURES_INTENT_GATE_PERMITIDAS = frozenset({"legado", "volume_numeros_v1"})
FEATURES_NEGACAO_PERMITIDAS = frozenset({"legado", "escopo_operacional_v1"})
OVERLAYS_INTENT_PERMITIDOS = frozenset({"volume_numeros_v1"})
OVERLAYS_COMANDO_MODALIDADE_PERMITIDOS = frozenset({
    "modalidade_v4_sparse_v1",
    "pragmatica_v5_sparse_v1",
    "pragmatica_estado_v6_sparse_v1",
    "pragmatica_contexto_v7_sparse_v1",
})
ATIVADORES_EXTENSAO_INTENT_PERMITIDOS = frozenset({
    "",
    "estado_pragmatico_v1",
    "gate_intent_match",
    "base_intent_match",
    "base_intent_off_verb_v1",
    "app_open_signal_v1",
})
REPRESENTACOES_EXTENSAO_PERMITIDAS = frozenset({
    "tfidf",
    "estrutura_bordas",
    "estrutura_pontuacao",
    "integral_v1",
    "semantico_hibrido_base",
    "fatorada",
})


def _validar_limiar_comando(valor: float) -> float:
    limiar = float(valor)
    if not 0.5 <= limiar <= 1.0:
        raise ValueError("limiar de comando precisa estar em [0.5, 1.0]")
    return limiar


def veto_intent_comando(
    arquitetura_comando: str,
    *,
    intent: str,
    intent_gate: str,
    confianca_intent: float = 0.0,
    limiares_fallback_intent_semantica: Mapping[str, float] | None = None,
) -> bool:
    """Aplica o contrato canônico de veto por intenção, sem autorizar efeito."""
    arquitetura = str(arquitetura_comando or "").strip().casefold()
    if arquitetura not in ARQUITETURAS_COMANDO_PERMITIDAS:
        raise ValueError(f"arquitetura de comando desconhecida: {arquitetura}")
    intent_semantica = str(intent or "").strip().upper()
    intent_lexical = str(intent_gate or intent_semantica).strip().upper()
    if arquitetura == "independent":
        return False
    if intent_semantica == "NONE":
        return True
    if intent_lexical != "NONE":
        return False
    limiares = {
        str(chave or "").strip().upper(): _validar_limiar_comando(valor)
        for chave, valor in dict(
            limiares_fallback_intent_semantica or {}
        ).items()
    }
    limiar_fallback = limiares.get(intent_semantica)
    return not (
        limiar_fallback is not None
        and float(confianca_intent) >= limiar_fallback
    )


def _enriquecer_texto_features(texto: str, *, extensoes_negacao: bool) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"\s+", " ", base).strip()
    indicadores: list[str] = []
    if (
        re.search(r"\b(?:nao|nem|nunca|jamais)\b", base)
        or (
            extensoes_negacao
            and re.search(r"\bde\s+jeito\s+nenhum\b", base)
        )
    ):
        indicadores.append("marcador_negacao_explicita")
    if (
        re.search(r"\b(?:evita|evite|evitar|evitando)\b", base)
        or re.search(r"\b(?:deixa|deixe|manter|mantenha).{0,80}\bfora\b", base)
        or re.search(r"\b(?:menos|exceto)\b", base)
        or re.search(r"\bsem\s+(?!querer\b)\w+(?:ar|er|ir)\b", base)
        or re.search(r"\bpassa(?:r)?\s+longe\b", base)
        or (
            extensoes_negacao
            and re.search(r"\b(?:fica|fique)\s+longe\b", base)
        )
        or re.search(r"\btira(?:r)?\b.{0,80}\b(?:opcoes|fila|lista|selecao)\b", base)
        or re.search(r"\btroca(?:r)?\b.{0,80}\bpor\s+(?:outra|outro)\b", base)
        or re.search(r"\b(?:conservar|conserve)\b", base)
        or (
            extensoes_negacao
            and re.search(r"\bcontinue\s+com\b.{0,80}\babert[oa]s?\b", base)
        )
        or re.search(
            r"\bescolh(?:e|a|er)\s+outr[oa]\s+no\s+lugar\s+d",
            base,
        )
    ):
        indicadores.append("marcador_negacao_exclusao")
    return " ".join((base, *indicadores)).strip()


def enriquecer_texto_features(texto: str) -> str:
    """Anexa pistas gerais de negação; não classifica nem autoriza."""
    return _enriquecer_texto_features(texto, extensoes_negacao=True)


def enriquecer_texto_features_comando(texto: str) -> str:
    """Preserva apenas as pistas já úteis à detecção de comandos."""
    return _enriquecer_texto_features(texto, extensoes_negacao=False)


def _slug_feature(valor: Any) -> str:
    base = unicodedata.normalize("NFKD", str(valor or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return base or "nenhuma"


def normalizar_texto_intent_gate_volume_numeros_v1(texto: str) -> str:
    """Neutraliza valores numéricos apenas em frases claramente de volume.

    O texto fora do domínio de áudio permanece idêntico. Esta função não
    decide intent, comando ou autorização; só estabiliza a entrada semântica
    do intent_gate contra números arbitrários.
    """
    bruto = " ".join(str(texto or "").strip().split())
    base = unicodedata.normalize("NFKD", bruto.casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    alvo = re.search(
        r"\b(?:volume|som|audio)\b.{0,24}?"
        r"(?P<valor>(?<![\w])\d+(?:[.,]\d+)?(?:\s*%)?)",
        base,
    )
    if alvo is None:
        return bruto
    inicio, fim = alvo.span("valor")
    normalizado = f"{bruto[:inicio]}valor{bruto[fim:]}"
    return re.sub(r"\s+", " ", normalizado).strip()


def normalizar_texto_negacao_escopo_operacional_v1(texto: str) -> str:
    """Recorta a cláusula operacional quando a negação pertence ao contexto.

    Só atua quando há duas cláusulas explícitas: a primeira expressa
    preferência/estado negativo e a segunda contém um pedido operacional.
    A função não decide se há comando nem concede autoridade.
    """
    bruto = " ".join(str(texto or "").strip().split())
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(
        ch for ch in normalizado if not unicodedata.combining(ch)
    )
    partes_brutas = re.split(r"\s*[,;]\s*", bruto, maxsplit=1)
    partes_norm = re.split(r"\s*[,;]\s*", normalizado, maxsplit=1)
    if len(partes_brutas) != 2 or len(partes_norm) != 2:
        return bruto
    contexto, operacao = partes_norm
    contexto_negativo = bool(re.search(
        r"\b(?:nao\s+(?:quero|gostei|vou|preciso|curti|pretendo)|"
        r"(?:eu\s+)?nao\s+quero|essa\s+eu\s+nao\s+quero)\b",
        contexto,
    ))
    comando_posterior = bool(re.search(
        r"\b(?:pula|pule|passa|passe|proxima|proximo|fecha|feche|"
        r"pode\s+fechar|abre|abra|pode\s+abrir|toca|toque|"
        r"coloca|coloque|aumenta|aumente|abaixa|abaixe|diminui|diminua)\b",
        operacao,
    ))
    operacao_negada = bool(re.search(r"\b(?:nao|nem|nunca|jamais)\b", operacao))
    if contexto_negativo and comando_posterior and not operacao_negada:
        return partes_brutas[1].strip()
    return bruto


def enriquecer_texto_features_comando_modalidade(texto: str) -> str:
    """Acrescenta estrutura discursiva ao command head sem impor um veto.

    Os marcadores vêm da leitura canônica de modalidade, mas omitem de
    propósito ``autoriza_execucao``. Assim a rede observa pergunta, comando,
    natureza do ato e ação explícita sem receber a decisão final como rótulo.
    """
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando(bruto)
    marcadores: list[str] = []
    try:
        from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

        leitura = classificar_modalidade_turno(
            bruto,
            texto_tem_comando_explicito=texto_tem_comando_explicito,
        )
    except Exception:
        leitura = {}
    for chave in ("modalidade", "modalidade_geral", "natureza_acao"):
        valor = _slug_feature(leitura.get(chave))
        marcadores.append(f"marcador_{chave}_{valor}")
    marcadores.append(
        "marcador_acao_explicita"
        if bool(leitura.get("acao_explicita"))
        else "marcador_sem_acao_explicita"
    )
    pares = (("\"", "\""), ("“", "”"), ("'", "'"), ("‘", "’"))
    tem_citacao = any(
        bruto.count(abertura) >= 2 if abertura == fechamento
        else abertura in bruto and fechamento in bruto
        for abertura, fechamento in pares
    )
    marcadores.append(
        "marcador_citacao_presente"
        if tem_citacao
        else "marcador_sem_citacao_presente"
    )
    return " ".join((base, *marcadores)).strip()


def enriquecer_texto_features_comando_modalidade_v2(texto: str) -> str:
    """Extende a modalidade v1 com sinais de relato e metalinguagem."""
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando_modalidade(bruto)
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(
        ch for ch in normalizado if not unicodedata.combining(ch)
    )
    marcadores: list[str] = []
    marcadores.append(
        "marcador_sujeito_terceira_pessoa"
        if re.match(r"^(?:ele|ela|eles|elas)\b", normalizado)
        else "marcador_sem_sujeito_terceira_pessoa"
    )
    tem_meta = bool(re.search(
        r"\b(?:dizer|diz|disse|falar|fala|falou|frase|exemplo|"
        r"traduz|traduza|traduzir)\b",
        normalizado,
    ))
    tem_citacao = "marcador_citacao_presente" in base
    marcadores.append(
        "marcador_metalinguagem_citada"
        if tem_meta and tem_citacao
        else "marcador_sem_metalinguagem_citada"
    )
    return " ".join((base, *marcadores)).strip()


def enriquecer_texto_features_comando_modalidade_v3(texto: str) -> str:
    """Features discursivas autocontidas e estáveis para o command head.

    Diferente das versões v1/v2, não chama o classificador canônico em tempo
    de inferência. Os marcadores descrevem apenas a forma da fala e nunca
    incluem autorização, veto ou decisão operacional.
    """
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando(bruto)
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(
        ch for ch in normalizado if not unicodedata.combining(ch)
    )
    normalizado = re.sub(r"\s+", " ", normalizado).strip()
    marcadores: list[str] = []

    def marcar(condicao: bool, nome: str) -> None:
        marcadores.append(
            f"marcador_{nome}" if condicao else f"marcador_sem_{nome}"
        )

    marcar(bruto.endswith("?"), "interrogacao_final")
    marcar(bool(re.match(
        r"^(?:como|por que|porque|qual|onde|quando|quem|quanto|o que)\b",
        normalizado,
    )), "inicio_interrogativo")
    marcar(bool(re.match(
        r"^(?:voce|tu)\s+(?:pode|poderia|consegue|conseguiria|sabe)\b|"
        r"^(?:tem como|e possivel)\b",
        normalizado,
    )), "moldura_capacidade")
    marcar(bool(re.search(
        r"\b(?:explica|explique|explicar|ensina|ensine|ensinar|mostra|"
        r"mostre|mostrar)\b.{0,90}\bcomo\b",
        normalizado,
    )), "moldura_explicacao")
    marcar(bool(re.search(
        r"\b(?:dizer|diz|disse|falar|fala|falou|frase|exemplo|"
        r"traduz|traduza|traduzir)\b",
        normalizado,
    )), "metalinguagem")
    pares = (("\"", "\""), ("“", "”"), ("'", "'"), ("‘", "’"))
    tem_citacao = any(
        bruto.count(abertura) >= 2 if abertura == fechamento
        else abertura in bruto and fechamento in bruto
        for abertura, fechamento in pares
    )
    marcar(tem_citacao, "citacao_presente")
    marcar(bool(re.match(r"^(?:ele|ela|eles|elas)\b", normalizado)),
           "sujeito_terceira_pessoa")
    marcar(bool(re.search(r"\bontem\b", normalizado)), "referencia_passado")
    marcar(bool(re.search(
        r"\b(?:prefiro|preferia|gosto|costumo|costumava)\b",
        normalizado,
    )), "preferencia_ou_habito")
    return " ".join((base, *marcadores)).strip()


def enriquecer_texto_features_comando_modalidade_v4_sparse(texto: str) -> str:
    """Versao autocontida esparsa: so anexa sinais estruturais presentes.

    Mantem o texto legado intacto quando nenhuma moldura e detectada. Isso
    evita que combinacoes de ``marcador_sem_*`` virem uma assinatura artificial
    e continuem influenciando o command head em frases comuns.
    """
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando(bruto)
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(
        ch for ch in normalizado if not unicodedata.combining(ch)
    )
    normalizado = re.sub(r"\s+", " ", normalizado).strip()
    marcadores: list[str] = []

    def marcar_se(condicao: bool, nome: str) -> None:
        if condicao:
            marcadores.append(f"marcador_{nome}")

    marcar_se(bruto.endswith("?"), "interrogacao_final")
    marcar_se(bool(re.match(
        r"^(?:como|por que|porque|qual|onde|quando|quem|quanto|o que)\b",
        normalizado,
    )), "inicio_interrogativo")
    marcar_se(bool(re.match(
        r"^(?:voce|tu)\s+(?:pode|poderia|consegue|conseguiria|sabe)\b|"
        r"^(?:tem como|e possivel)\b",
        normalizado,
    )), "moldura_capacidade")
    marcar_se(bool(re.search(
        r"\b(?:explica|explique|explicar|ensina|ensine|ensinar|mostra|"
        r"mostre|mostrar)\b.{0,90}\bcomo\b",
        normalizado,
    )), "moldura_explicacao")
    marcar_se(bool(re.search(
        r"\b(?:dizer|diz|disse|falar|fala|falou|frase|exemplo|"
        r"traduz|traduza|traduzir)\b",
        normalizado,
    )), "metalinguagem")
    pares = (("\"", "\""), ("“", "”"), ("'", "'"), ("‘", "’"))
    tem_citacao = any(
        bruto.count(abertura) >= 2 if abertura == fechamento
        else abertura in bruto and fechamento in bruto
        for abertura, fechamento in pares
    )
    marcar_se(tem_citacao, "citacao_presente")
    marcar_se(bool(re.match(r"^(?:ele|ela|eles|elas)\b", normalizado)),
              "sujeito_terceira_pessoa")
    marcar_se(bool(re.search(r"\bontem\b", normalizado)),
              "referencia_passado")
    marcar_se(bool(re.search(
        r"\b(?:prefiro|preferia|gosto|costumo|costumava)\b",
        normalizado,
    )), "preferencia_ou_habito")
    return " ".join((base, *marcadores)).strip()


def enriquecer_texto_features_comando_pragmatica_v5_sparse(texto: str) -> str:
    """Extende v4 com sinais esparsos de pedido indireto.

    Os sinais descrevem somente a forma linguística. Não codificam intent,
    ação, autorização ou o rótulo de comando.
    """
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando_modalidade_v4_sparse(bruto)
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(
        ch for ch in normalizado if not unicodedata.combining(ch)
    )
    normalizado = re.sub(r"\s+", " ", normalizado).strip()
    marcadores: list[str] = []

    def marcar_se(condicao: bool, nome: str) -> None:
        if condicao:
            marcadores.append(f"marcador_{nome}")

    marcar_se(bool(re.match(
        r"^(?:seria|ia ser)\s+(?:legal|bom|boa|otimo|otima|melhor|interessante)\b\s+\S",
        normalizado,
    )), "pedido_indireto_avaliativo")
    marcar_se(bool(re.match(
        r"^(?:eu\s+)?(?:queria|gostaria)(?:\s+de)?\b\s+\S",
        normalizado,
    )), "pedido_indireto_desejo")
    marcar_se(bool(re.match(
        r"^bem\s+que\s+(?:voce\s+)?(?:podia|poderia)\b\s+\S",
        normalizado,
    )), "pedido_indireto_modal")
    marcar_se(bool(re.match(
        r"^(?:eu\s+)?(?:to|estou|estava)\s+(?:a\s+fim|com\s+vontade)\s+de\b\s+\S",
        normalizado,
    )), "pedido_indireto_vontade")
    marcar_se(bool(re.search(
        r"\b(?:saber|entender|aprender)\s+(?:melhor\s+)?como\b",
        normalizado,
    )), "consulta_instrucional_como")
    return " ".join((base, *marcadores)).strip()


def enriquecer_texto_features_comando_pragmatica_estado_v6_sparse(texto: str) -> str:
    """Extende v5 com sinais descritivos de estado, sem codificar ação."""
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando_pragmatica_v5_sparse(bruto)
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(ch for ch in normalizado if not unicodedata.combining(ch))
    normalizado = re.sub(r"\s+", " ", normalizado).strip()
    marcadores: list[str] = []

    def marcar_se(condicao: bool, nome: str) -> None:
        if condicao:
            marcadores.append(f"marcador_{nome}")

    tem_audio = bool(re.search(r"\b(?:volume|som|audio)\b", normalizado))
    marcar_se(tem_audio and bool(re.search(
        r"\b(?:alto|alta|forte|estourando|estourado|barulhento)\b", normalizado
    )), "estado_excesso_audio")
    marcar_se(tem_audio and bool(re.search(
        r"\b(?:baixo|baixa|baixinho|baixinha|fraco|fraca)\b", normalizado
    )), "estado_audio_insuficiente")
    marcar_se(bool(re.search(
        r"\b(?:quarto|ambiente|aqui|luz|iluminacao)\b", normalizado
    )) and bool(re.search(
        r"\b(?:escuro|escura|escuridao|sem luz)\b", normalizado
    )), "estado_baixa_iluminacao")
    return " ".join((base, *marcadores)).strip()


def enriquecer_texto_features_comando_contexto_v7_sparse(texto: str) -> str:
    """Extende v6 com a estrutura contexto + cláusula operacional posterior."""
    bruto = " ".join(str(texto or "").strip().split())
    base = enriquecer_texto_features_comando_pragmatica_estado_v6_sparse(bruto)
    normalizado = unicodedata.normalize("NFKD", bruto.casefold())
    normalizado = "".join(ch for ch in normalizado if not unicodedata.combining(ch))
    partes = re.split(r"\s*[,;]\s*", normalizado, maxsplit=1)
    marcadores: list[str] = []
    if len(partes) == 2:
        contexto, operacao = partes
        tem_contexto = bool(re.search(
            r"\b(?:eu|estou|to|preciso|quero|queria|tenho|aqui|agora)\b",
            contexto,
        ))
        tem_operacao = bool(re.search(
            r"\b(?:abre|abra|abrir|entra|entre|entrar|liga|ligue|ligar|"
            r"desliga|desligue|desligar|fecha|feche|fechar|pula|pule|"
            r"passa|passe|coloca|coloque|aumenta|aumente|abaixa|abaixe)\b",
            operacao,
        ))
        operacao_negada = bool(re.search(
            r"\b(?:nao|nem|nunca|jamais)\b", operacao
        ))
        if tem_contexto and tem_operacao and not operacao_negada:
            marcadores.append("marcador_contexto_clausula_operacional")
    tem_objetivo = bool(re.search(
        r"\b(?:preciso|quero|queria|tenho\s+que|necessito)\b", normalizado
    ))
    tem_navegacao = bool(re.search(
        r"\b(?:pesquisar|consultar|procurar|buscar|ver|olhar|conferir)\b",
        normalizado,
    ))
    eh_pergunta = "?" in bruto or bool(re.match(
        r"^(?:como|por\s+que|porque|qual|onde|quando)\b", normalizado
    ))
    if tem_objetivo and tem_navegacao and not eh_pergunta:
        marcadores.append("marcador_objetivo_navegacao_indireto")
    return " ".join((base, *marcadores)).strip()


def extrair_clausula_operacional_contexto_v1(texto: str) -> str:
    """Retorna a cláusula operacional posterior apenas quando v7 a reconhece."""
    bruto = " ".join(str(texto or "").strip().split())
    enriquecido = enriquecer_texto_features_comando_contexto_v7_sparse(bruto)
    if "marcador_contexto_clausula_operacional" not in enriquecido:
        return bruto
    partes = re.split(r"\s*[,;]\s*", bruto, maxsplit=1)
    if len(partes) != 2 or not partes[1].strip():
        return bruto
    return partes[1].strip()


def detectar_estado_pragmatico_v1(texto: str) -> bool:
    """Detecta apenas a presença de uma moldura linguística de estado."""
    return (
        enriquecer_texto_features_comando_pragmatica_estado_v6_sparse(texto)
        != enriquecer_texto_features_comando_pragmatica_v5_sparse(texto)
    )


def _preprocessador_overlay_comando(versao: str):
    nome = str(versao or "").strip().casefold()
    if nome == "modalidade_v4_sparse_v1":
        return enriquecer_texto_features_comando_modalidade_v4_sparse
    if nome == "pragmatica_v5_sparse_v1":
        return enriquecer_texto_features_comando_pragmatica_v5_sparse
    if nome == "pragmatica_estado_v6_sparse_v1":
        return enriquecer_texto_features_comando_pragmatica_estado_v6_sparse
    if nome == "pragmatica_contexto_v7_sparse_v1":
        return enriquecer_texto_features_comando_contexto_v7_sparse
    raise ValueError(f"overlay de comando desconhecido: {nome}")


def enriquecer_texto_estrutura_bordas(texto: str) -> str:
    """Representa forma e bordas sem conhecer intent, entidade ou rótulo."""
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    tokens = re.sub(r"[^a-z0-9]+", " ", base).strip().split()
    marcadores = [f"tamanho_{min(len(tokens), 8)}"]
    for tamanho in range(1, min(5, len(tokens)) + 1):
        marcadores.extend((
            f"prefixo_{tamanho}_{'_'.join(tokens[:tamanho])}",
            f"sufixo_{tamanho}_{'_'.join(tokens[-tamanho:])}",
        ))
    return " ".join(marcadores)


def enriquecer_texto_estrutura_pontuacao(texto: str) -> str:
    """Acrescenta forma comunicativa sem conhecer domínio, intent ou rótulo."""
    bruto = str(texto or "").strip()
    marcadores = [enriquecer_texto_estrutura_bordas(bruto)]
    marcadores.append(
        "marcador_interrogacao_final"
        if bruto.endswith("?")
        else "marcador_sem_interrogacao_final"
    )
    pares_citacao = (("\"", "\""), ("“", "”"), ("'", "'"), ("‘", "’"))
    citacao_total = bool(
        len(bruto) >= 2
        and any(
            bruto.startswith(abertura) and bruto.endswith(fechamento)
            for abertura, fechamento in pares_citacao
        )
    )
    marcadores.append(
        "marcador_citacao_total"
        if citacao_total
        else "marcador_sem_citacao_total"
    )
    return " ".join(item for item in marcadores if item).strip()


def _pipeline(
    rotulos: list[Any],
    *,
    estrategia: str = "logistic",
    representacao: str = "tfidf",
    preprocessador_indicadores: Callable[[str], str] = enriquecer_texto_features,
    ngramas_caracteres: tuple[int, int] = (3, 5),
) -> Pipeline:
    estrategia_normalizada = str(estrategia or "").strip().casefold()
    if estrategia_normalizada not in ESTRATEGIAS_PERMITIDAS:
        raise ValueError(f"estratégia neural desconhecida: {estrategia_normalizada}")
    representacao_normalizada = str(representacao or "").strip().casefold()
    if representacao_normalizada not in REPRESENTACOES_PERMITIDAS:
        raise ValueError(
            f"representação neural desconhecida: {representacao_normalizada}"
        )
    parametros_preprocessamento = (
        {"preprocessor": preprocessador_indicadores, "lowercase": False}
        if representacao_normalizada == "tfidf_indicadores"
        else {"strip_accents": "unicode"}
    )
    features = FeatureUnion(
        [
            (
                "palavras",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    **parametros_preprocessamento,
                ),
            ),
            (
                "caracteres",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=ngramas_caracteres,
                    min_df=1,
                    **parametros_preprocessamento,
                ),
            ),
        ]
    )
    classificador = _classificador(rotulos, estrategia_normalizada)
    return Pipeline([("features", features), ("classifier", classificador)])


def _classificador(rotulos: list[Any], estrategia: str) -> Any:
    if len(set(rotulos)) < 2:
        return DummyClassifier(strategy="most_frequent")
    if estrategia == "logistic":
        return LogisticRegression(
            max_iter=800,
            class_weight="balanced",
            random_state=42,
        )
    if estrategia == "sgd_log_loss":
        return SGDClassifier(
            loss="log_loss",
            class_weight="balanced",
            max_iter=2000,
            tol=1e-4,
            random_state=42,
        )
    return ComplementNB(alpha=0.5)


def _entrada_modelo(entrada: Any) -> Any:
    return [entrada] if isinstance(entrada, str) else entrada


def _confianca(modelo: Any, entrada: Any, rotulo: Any) -> float:
    probabilidades = modelo.predict_proba(_entrada_modelo(entrada))[0]
    classes = list(modelo.classes_)
    try:
        return float(probabilidades[classes.index(rotulo)])
    except (ValueError, IndexError):
        return 0.0


def _validar_limiar_extensao_intent(valor: float) -> float:
    limiar = float(valor)
    if not 0.5 <= limiar <= 1.0:
        raise ValueError("limiar de extensão de intent precisa estar em [0.5, 1.0]")
    return limiar


def _pipeline_extensao(rotulos: list[bool], representacao: str) -> Pipeline:
    """Cria o detector experimental sem alterar os pipelines legados."""
    representacao_normalizada = str(representacao or "").strip().casefold()
    if representacao_normalizada == "integral_v1":
        # Import local evita ciclo: representacao_integral reutiliza a estrutura
        # canônica deste módulo, mas só é necessária quando o ensaio a solicita.
        from .representacao_integral import criar_extrator_texto_integral_v1

        return Pipeline([
            ("features", criar_extrator_texto_integral_v1()),
            ("classifier", _classificador(rotulos, "sgd_log_loss")),
        ])

    preprocessador = (
        enriquecer_texto_estrutura_pontuacao
        if representacao_normalizada == "estrutura_pontuacao"
        else enriquecer_texto_estrutura_bordas
    )
    return _pipeline(
        rotulos,
        estrategia="sgd_log_loss",
        representacao=(
            "tfidf_indicadores"
            if representacao_normalizada in {
                "estrutura_bordas",
                "estrutura_pontuacao",
            }
            else "tfidf"
        ),
        preprocessador_indicadores=preprocessador,
    )


@dataclass
class DetectorExtensaoEncoderBase:
    """Head experimental sobre o encoder já versionado pelo modelo-base."""

    encoder: Any
    classificador: Any

    @property
    def classes_(self) -> Any:
        return self.classificador.classes_

    def predict_proba(self, entradas: Any) -> Any:
        textos = [entradas] if isinstance(entradas, str) else list(entradas)
        codificar = getattr(self.encoder, "codificar", None)
        if not callable(codificar):
            raise ValueError("encoder semântico do modelo-base não implementa codificar")
        return self.classificador.predict_proba(codificar(textos))


def _treinar_detector_extensao(
    modelo_base: "ModeloNeuralComandos",
    textos: list[str],
    rotulos: list[bool],
    representacao: str,
) -> Any:
    representacao_normalizada = str(representacao or "").strip().casefold()
    if representacao_normalizada == "semantico_hibrido_base":
        encoder = getattr(modelo_base, "encoder_semantico", None)
        codificar = getattr(encoder, "codificar", None)
        if encoder is None or not callable(codificar):
            raise ValueError(
                "representação semântico-híbrida exige encoder semântico no modelo-base"
            )
        vetores = codificar(textos)
        classificador = _classificador(
            rotulos, "sgd_log_loss"
        ).fit(vetores, rotulos)
        return DetectorExtensaoEncoderBase(
            encoder=encoder,
            classificador=classificador,
        )
    return _pipeline_extensao(
        rotulos,
        representacao_normalizada,
    ).fit(textos, rotulos)


@dataclass
class ExtensaoIntentNeural:
    """Detector lexical aditivo que propõe intent sem decidir comando."""

    intent: str
    action: str
    detector: Any
    limiar: float = 0.925
    versao: str = ""
    escopo: str = ""
    representacao: str = "tfidf"
    ativacao: str = ""
    detectores_fatores: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.intent = str(self.intent or "").strip().upper()
        self.action = str(self.action or "").strip().casefold()
        self.versao = str(self.versao or "").strip()
        self.escopo = str(self.escopo or "").strip().casefold()
        self.representacao = str(
            self.representacao or "tfidf"
        ).strip().casefold()
        self.ativacao = str(getattr(self, "ativacao", "") or "").strip().casefold()
        if self.ativacao not in ATIVADORES_EXTENSAO_INTENT_PERMITIDOS:
            raise ValueError("ativador de extensão desconhecido")
        self.limiar = _validar_limiar_extensao_intent(self.limiar)
        if not self.intent or self.intent == "NONE":
            raise ValueError("extensão exige intent operacional")
        if not self.action or self.action == "none":
            raise ValueError("extensão exige action operacional")
        nomes_fatores = [
            str(nome or "").strip().casefold()
            for nome in dict(self.detectores_fatores or {})
        ]
        if any(not nome for nome in nomes_fatores) or len(nomes_fatores) != len(set(nomes_fatores)):
            raise ValueError("fatores exigem nomes únicos e não vazios")
        self.detectores_fatores = {
            str(nome or "").strip().casefold(): detector
            for nome, detector in dict(self.detectores_fatores or {}).items()
        }
        if self.representacao == "fatorada" and not self.detectores_fatores:
            raise ValueError("representação fatorada exige detectores de fatores")
        if self.detectores_fatores:
            if any(
                not callable(getattr(detector, "predict_proba", None))
                for detector in self.detectores_fatores.values()
            ):
                raise TypeError(
                    "todo detector de fator precisa implementar predict_proba"
                )
        elif not callable(getattr(self.detector, "predict_proba", None)):
            raise TypeError("detector de extensão precisa implementar predict_proba")
        if self.representacao not in REPRESENTACOES_EXTENSAO_PERMITIDAS:
            raise ValueError("representação de extensão desconhecida")

    def probabilidade(self, texto: str) -> float:
        probabilidade, _fatores = self.avaliar(texto)
        return probabilidade

    def avaliar(self, texto: str) -> tuple[float, dict[str, float]]:
        detectores = dict(getattr(self, "detectores_fatores", {}) or {})
        if not detectores:
            return _confianca(self.detector, texto, True), {}
        probabilidades = {
            nome: _confianca(detector, texto, True)
            for nome, detector in sorted(detectores.items())
        }
        if any(not math.isfinite(p) or not 0.0 <= p <= 1.0 for p in probabilidades.values()):
            raise ValueError("probabilidade inválida em fator de extensão")
        # O mínimo implementa a conjunção dos limiares; não estima uma
        # probabilidade conjunta calibrada.
        return min(probabilidades.values()), probabilidades


def _chave_nova_extensao_intent(
    extensoes: Mapping[str, "ExtensaoIntentNeural"],
    intent: str,
    action: str,
) -> str:
    par = (intent, action)
    for existente in extensoes.values():
        if isinstance(existente, ExtensaoIntentNeural) and (
            existente.intent,
            existente.action,
        ) == par:
            raise ValueError(
                f"extensão de intent/action já existe: {intent}/{action}"
            )
    if intent not in extensoes:
        return intent
    chave = f"{intent}::{action}"
    if chave in extensoes:
        raise ValueError(
            f"chave de extensão já existe: {chave}"
        )
    return chave


@dataclass
class ModeloNeuralComandos:
    versao: str
    cabeca_intent: Any
    cabeca_comando: Any
    cabeca_negacao: Any
    cabeca_acao: Any
    cabeca_intent_gate: Any = None
    cabecas_intent_overlay: dict[str, Any] = field(default_factory=dict)
    estrategia: str = "logistic"
    arquitetura_comando: str = "independent"
    arquitetura_acao: str = "global"
    cabecas_acao_por_intent: dict[str, Any] = field(default_factory=dict)
    cabecas_comando_por_intent: dict[str, Any] = field(default_factory=dict)
    cabecas_comando_extensao_por_intent: dict[str, Any] = field(default_factory=dict)
    cabecas_comando_overlay_por_intent: dict[str, Any] = field(default_factory=dict)
    versoes_overlay_comando_por_intent: dict[str, str] = field(default_factory=dict)
    limiar_comando: float = 0.5
    limiares_comando_por_intent: dict[str, float] = field(default_factory=dict)
    limiares_fallback_intent_semantica: dict[str, float] = field(
        default_factory=dict
    )
    features_comando: str = "legado"
    features_comando_intents: tuple[str, ...] = ()
    features_intent_gate: str = "legado"
    features_negacao: str = "legado"
    representacao: str = "tfidf"
    encoder_semantico: Any = None
    extensoes_intent: dict[str, ExtensaoIntentNeural] = field(default_factory=dict)
    reavaliar_comando_apos_extensao: bool = False
    # Calibrado no frozen_v0: com 14 classes, comandos corretos começam em
    # 0.137. OOD não concede autoridade; comando, negação e risco são gates
    # independentes.
    limiar_ood: float = 0.13

    def prever(self, texto: str) -> dict[str, Any]:
        fala = " ".join(str(texto or "").strip().split())
        fala_volume_numeros = normalizar_texto_intent_gate_volume_numeros_v1(fala)
        tem_volume_numerico = fala_volume_numeros != fala
        encoder = getattr(self, "encoder_semantico", None)
        entrada_intent_gate = None
        if (
            self.representacao == "onnx_semantico_hibrido"
            and encoder is not None
        ):
            entrada_intent_gate, entrada_semantica = (
                encoder.codificar_componentes([fala])
            )
            features_intent_gate = str(
                getattr(self, "features_intent_gate", "legado") or "legado"
            ).strip().casefold()
            if features_intent_gate == "volume_numeros_v1" and tem_volume_numerico:
                entrada_intent_gate = encoder.codificar_base([fala_volume_numeros])
        else:
            entrada_semantica = (
                encoder.codificar([fala])
                if self.representacao in REPRESENTACOES_SEMANTICAS
                and encoder is not None
                else None
            )
        entrada_intent = entrada_semantica if entrada_semantica is not None else fala
        cabeca_intent = self.cabeca_intent
        variante_cabeca_intent = "legado"
        overlays_intent = dict(
            getattr(self, "cabecas_intent_overlay", {}) or {}
        )
        if tem_volume_numerico and "volume_numeros_v1" in overlays_intent:
            cabeca_intent = overlays_intent["volume_numeros_v1"]
            variante_cabeca_intent = "volume_numeros_v1"
        intent = str(
            cabeca_intent.predict(_entrada_modelo(entrada_intent))[0]
        ).upper()
        confianca_intent = _confianca(
            cabeca_intent,
            entrada_intent,
            intent,
        )
        cabeca_intent_gate = getattr(self, "cabeca_intent_gate", None)
        intent_gate = (
            str(
                cabeca_intent_gate.predict(
                    _entrada_modelo(entrada_intent_gate)
                )[0]
            ).upper()
            if cabeca_intent_gate is not None and entrada_intent_gate is not None
            else intent
        )
        confianca_intent_gate = (
            _confianca(
                cabeca_intent_gate,
                entrada_intent_gate,
                intent_gate,
            )
            if cabeca_intent_gate is not None and entrada_intent_gate is not None
            else confianca_intent
        )
        cabecas_comando_por_intent = (
            getattr(self, "cabecas_comando_por_intent", {}) or {}
        )
        escopo_comando = (
            intent
            if intent != "NONE"
            and intent in cabecas_comando_por_intent
            else "GLOBAL"
        )
        cabeca_comando = (
            cabecas_comando_por_intent[escopo_comando]
            if escopo_comando != "GLOBAL"
            else self.cabeca_comando
        )
        variante_cabeca_comando = "legado"
        overlays_comando = dict(
            getattr(self, "cabecas_comando_overlay_por_intent", {}) or {}
        )
        versoes_overlay = {
            str(intent_overlay or "").strip().upper(): str(versao_overlay or "").strip().casefold()
            for intent_overlay, versao_overlay in dict(
                getattr(self, "versoes_overlay_comando_por_intent", {}) or {}
            ).items()
        }
        escopo_overlay = (
            intent
            if intent in overlays_comando
            else intent_gate
            if intent_gate in overlays_comando
            else ""
        )
        if escopo_overlay:
            versao_overlay = versoes_overlay.get(escopo_overlay, "")
            if versao_overlay in OVERLAYS_COMANDO_MODALIDADE_PERMITIDOS:
                preprocessador_overlay = _preprocessador_overlay_comando(
                    versao_overlay
                )
                fala_overlay = preprocessador_overlay(fala)
                fala_base_overlay = (
                    enriquecer_texto_features_comando_modalidade_v4_sparse(fala)
                    if versao_overlay == "pragmatica_v5_sparse_v1"
                    else enriquecer_texto_features_comando(fala)
                )
                if fala_overlay != fala_base_overlay:
                    cabeca_comando = overlays_comando[escopo_overlay]
                    escopo_comando = escopo_overlay
                    variante_cabeca_comando = versao_overlay
        comando_bruto = bool(cabeca_comando.predict([fala])[0])
        confianca_comando = _confianca(
            cabeca_comando,
            fala,
            comando_bruto,
        )
        probabilidade_comando = (
            confianca_comando if comando_bruto else 1.0 - confianca_comando
        )
        limiar_comando_global = _validar_limiar_comando(
            getattr(self, "limiar_comando", 0.5)
        )
        limiares_por_intent = {
            str(chave or "").strip().upper(): _validar_limiar_comando(valor)
            for chave, valor in dict(
                getattr(self, "limiares_comando_por_intent", {}) or {}
            ).items()
        }
        alvo_limiar_comando = (
            escopo_comando
            if escopo_comando != "GLOBAL"
            else intent
            if intent == intent_gate and intent != "NONE"
            else ""
        )
        limiar_comando = (
            limiares_por_intent.get(alvo_limiar_comando, limiar_comando_global)
            if alvo_limiar_comando
            else limiar_comando_global
        )
        veto_limiar = bool(
            comando_bruto and probabilidade_comando < limiar_comando
        )
        arquitetura_comando = str(
            getattr(self, "arquitetura_comando", "independent") or "independent"
        ).casefold()
        limiares_fallback_semantico = dict(
            getattr(self, "limiares_fallback_intent_semantica", {}) or {}
        )
        veto_intent = veto_intent_comando(
            arquitetura_comando,
            intent=intent,
            intent_gate=intent_gate,
            confianca_intent=confianca_intent,
            limiares_fallback_intent_semantica=limiares_fallback_semantico,
        )
        veto_comando = bool(
            comando_bruto
            and (
                veto_limiar
                or veto_intent
            )
        )
        comando = bool(comando_bruto and not veto_comando)
        arquitetura_acao = str(
            getattr(self, "arquitetura_acao", "global") or "global"
        ).casefold()
        cabecas_por_intent = getattr(self, "cabecas_acao_por_intent", {}) or {}
        if arquitetura_acao == "hierarchical":
            cabeca_acao = cabecas_por_intent.get(intent)
            if cabeca_acao is None:
                acao = "none"
                confianca_acao = 1.0 if intent == "NONE" else 0.0
            else:
                entrada_acao = (
                    entrada_semantica if entrada_semantica is not None else fala
                )
                acao = str(
                    cabeca_acao.predict(_entrada_modelo(entrada_acao))[0]
                ).casefold()
                confianca_acao = _confianca(cabeca_acao, entrada_acao, acao)
        else:
            entrada_acao = entrada_semantica if entrada_semantica is not None else fala
            acao = str(
                self.cabeca_acao.predict(_entrada_modelo(entrada_acao))[0]
            ).casefold()
            confianca_acao = _confianca(self.cabeca_acao, entrada_acao, acao)
        acao_bruta = acao
        features_negacao = str(
            getattr(self, "features_negacao", "legado") or "legado"
        ).strip().casefold()
        fala_negacao = (
            normalizar_texto_negacao_escopo_operacional_v1(fala)
            if features_negacao == "escopo_operacional_v1"
            else fala
        )
        negada = bool(self.cabeca_negacao.predict([fala_negacao])[0])
        confianca_negacao = _confianca(self.cabeca_negacao, fala_negacao, negada)
        params = {} if veto_comando or acao == "none" else {"acao": acao}
        resultado = {
            "intent": intent,
            "intent_head_variant": variante_cabeca_intent,
            "gate_intent": intent_gate,
            "params": params,
            "raw_action": acao_bruta,
            "is_command": comando,
            "raw_is_command": comando_bruto,
            "command_veto_reason": (
                "confianca_comando_abaixo_limiar"
                if veto_limiar
                else "intent_desconhecida"
                if veto_comando
                else ""
            ),
            "command_probability": probabilidade_comando,
            "command_threshold": limiar_comando,
            "command_head_scope": escopo_comando,
            "command_head_variant": variante_cabeca_comando,
            "intent_gate_fallback_applied": bool(
                arquitetura_comando == "intent_gated"
                and intent != "NONE"
                and intent_gate == "NONE"
                and not veto_intent
            ),
            "negated": negada,
            "negation_input_variant": features_negacao,
            "negation_scope_applied": fala_negacao != fala,
            "ood": confianca_intent < self.limiar_ood,
            # O limiar 0.13 foi calibrado para a representação lexical. A
            # representação semântica permanece observável, mas não pode
            # apresentar esse mesmo limiar como se já estivesse calibrado.
            "ood_calibrated": self.representacao not in REPRESENTACOES_SEMANTICAS,
            "confidence": {
                "intent": confianca_intent,
                "intent_gate": confianca_intent_gate,
                "command": confianca_comando,
                "negation": confianca_negacao,
                "action": confianca_acao,
            },
        }
        return self._aplicar_extensoes_intent(fala, resultado)

    def _aplicar_extensoes_intent(
        self,
        fala: str,
        previsao_base: dict[str, Any],
    ) -> dict[str, Any]:
        extensoes = dict(getattr(self, "extensoes_intent", {}) or {})
        if not extensoes:
            return previsao_base
        ativadas: list[tuple[ExtensaoIntentNeural, float, dict[str, float]]] = []
        for extensao in extensoes.values():
            if not isinstance(extensao, ExtensaoIntentNeural):
                continue
            ativacao = str(getattr(extensao, "ativacao", "") or "").strip().casefold()
            if ativacao == "estado_pragmatico_v1" and not detectar_estado_pragmatico_v1(fala):
                continue
            if (
                ativacao == "gate_intent_match"
                and str(previsao_base.get("gate_intent") or "").upper() != extensao.intent
            ):
                continue
            if (
                ativacao == "base_intent_match"
                and str(previsao_base.get("intent") or "").upper() != extensao.intent
            ):
                continue
            if ativacao == "base_intent_off_verb_v1":
                if str(previsao_base.get("intent") or "").upper() != extensao.intent:
                    continue
                fala_norm = unicodedata.normalize("NFKD", str(fala or "").casefold())
                fala_norm = "".join(
                    ch for ch in fala_norm if not unicodedata.combining(ch)
                )
                if not re.search(
                    r"\b(?:desliga|desligue|desligar|apaga|apague|apagar|"
                    r"desativa|desative|desativar)\b",
                    fala_norm,
                ):
                    continue
            if ativacao == "app_open_signal_v1":
                fala_norm = unicodedata.normalize("NFKD", str(fala or "").casefold())
                fala_norm = "".join(
                    ch for ch in fala_norm if not unicodedata.combining(ch)
                )
                if re.search(
                    r"\b(?:fecha|feche|fechar|encerra|encerre|encerrar|"
                    r"finaliza|finalize|finalizar|sai|saia|sair)\b",
                    fala_norm,
                ):
                    continue
                if re.search(
                    r"\bnao\s+quero(?:\s+mais)?\s+(?:usar|abrir|jogar)\b",
                    fala_norm,
                ):
                    continue
                if not re.search(
                    r"\b(?:abre|abra|abri|abrir|inicia|inicie|iniciar|liga|ligue|"
                    r"ligar|usa|usar|joga|jogar|roda|rodar|executa|executar|"
                    r"coloca|coloque)\b",
                    fala_norm,
                ):
                    continue
            try:
                probabilidade, fatores = extensao.avaliar(fala)
            except Exception:
                continue
            if probabilidade >= extensao.limiar:
                ativadas.append((extensao, probabilidade, fatores))
        # Ausência ou concorrência entre propostas preserva bit a bit a
        # interpretação base. Uma extensão nunca desempata outra extensão.
        if len(ativadas) != 1:
            return previsao_base
        extensao, probabilidade, fatores = ativadas[0]
        resultado = dict(previsao_base)
        resultado["intent"] = extensao.intent
        resultado["gate_intent"] = extensao.intent
        resultado["raw_action"] = extensao.action
        resultado["params"] = {"acao": extensao.action}
        if bool(getattr(self, "reavaliar_comando_apos_extensao", False)):
            intent_extensao = extensao.intent
            cabecas_dedicadas = dict(
                getattr(self, "cabecas_comando_por_intent", {}) or {}
            )
            cabecas_extensao = dict(
                getattr(self, "cabecas_comando_extensao_por_intent", {}) or {}
            )
            if intent_extensao in cabecas_extensao:
                escopo_comando = intent_extensao
                cabeca_comando = cabecas_extensao[intent_extensao]
                variante_comando = "extensao_dedicada_v1"
            else:
                escopo_comando = (
                    intent_extensao
                    if intent_extensao in cabecas_dedicadas
                    else "GLOBAL"
                )
                cabeca_comando = (
                    cabecas_dedicadas[intent_extensao]
                    if escopo_comando != "GLOBAL"
                    else self.cabeca_comando
                )
                variante_comando = "legado"
            overlays = dict(
                getattr(self, "cabecas_comando_overlay_por_intent", {}) or {}
            )
            versoes = {
                str(chave or "").strip().upper(): str(valor or "").strip().casefold()
                for chave, valor in dict(
                    getattr(self, "versoes_overlay_comando_por_intent", {}) or {}
                ).items()
            }
            fala_comando = fala
            entrada_comando_variant = "fala_completa"
            if intent_extensao in overlays:
                versao_overlay = versoes.get(intent_extensao, "")
                if versao_overlay in OVERLAYS_COMANDO_MODALIDADE_PERMITIDOS:
                    preprocessador = _preprocessador_overlay_comando(versao_overlay)
                    fala_overlay = preprocessador(fala)
                    fala_base_overlay = (
                        enriquecer_texto_features_comando_modalidade_v4_sparse(fala)
                        if versao_overlay == "pragmatica_v5_sparse_v1"
                        else enriquecer_texto_features_comando(fala)
                    )
                    if fala_overlay != fala_base_overlay:
                        clausula = (
                            extrair_clausula_operacional_contexto_v1(fala)
                            if versao_overlay == "pragmatica_contexto_v7_sparse_v1"
                            else fala
                        )
                        if clausula != fala:
                            fala_comando = clausula
                            cabeca_comando = (
                                cabecas_dedicadas[intent_extensao]
                                if intent_extensao in cabecas_dedicadas
                                else self.cabeca_comando
                            )
                            escopo_comando = (
                                intent_extensao
                                if intent_extensao in cabecas_dedicadas
                                else "GLOBAL"
                            )
                            variante_comando = "clausula_operacional_v1"
                            entrada_comando_variant = "clausula_operacional_v1"
                        else:
                            cabeca_comando = overlays[intent_extensao]
                            escopo_comando = intent_extensao
                            variante_comando = versao_overlay
            comando_bruto = bool(cabeca_comando.predict([fala_comando])[0])
            confianca_comando = _confianca(
                cabeca_comando, fala_comando, comando_bruto
            )
            probabilidade_comando = (
                confianca_comando
                if comando_bruto
                else 1.0 - confianca_comando
            )
            limiar_global = _validar_limiar_comando(
                getattr(self, "limiar_comando", 0.5)
            )
            limiares_intent = {
                str(chave or "").strip().upper(): _validar_limiar_comando(valor)
                for chave, valor in dict(
                    getattr(self, "limiares_comando_por_intent", {}) or {}
                ).items()
            }
            limiar_comando = limiares_intent.get(
                intent_extensao, limiar_global
            )
            veto_limiar = bool(
                comando_bruto and probabilidade_comando < limiar_comando
            )
            resultado["raw_is_command"] = comando_bruto
            resultado["is_command"] = bool(comando_bruto and not veto_limiar)
            resultado["command_probability"] = probabilidade_comando
            resultado["command_threshold"] = limiar_comando
            resultado["command_head_scope"] = escopo_comando
            resultado["command_head_variant"] = variante_comando
            resultado["command_input_variant"] = entrada_comando_variant
            resultado["command_veto_reason"] = (
                "confianca_comando_abaixo_limiar" if veto_limiar else ""
            )
            resultado["command_gate_recomputed_after_extension"] = True
            confiancas_comando = dict(resultado.get("confidence") or {})
            confiancas_comando["command"] = confianca_comando
            resultado["confidence"] = confiancas_comando
        elif (
            resultado.get("command_veto_reason") == "intent_desconhecida"
            and resultado.get("raw_is_command") is True
        ):
            try:
                probabilidade_comando = float(
                    resultado.get("command_probability")
                )
                limiar_comando = float(resultado.get("command_threshold"))
            except (TypeError, ValueError):
                probabilidade_comando = math.nan
                limiar_comando = math.nan
            if (
                math.isfinite(probabilidade_comando)
                and math.isfinite(limiar_comando)
                and probabilidade_comando >= limiar_comando
            ):
                resultado["is_command"] = True
                resultado["command_veto_reason"] = ""
                resultado["command_gate_recomputed_after_extension"] = True
        resultado["ood"] = False
        confiancas = dict(resultado.get("confidence") or {})
        confiancas["intent"] = probabilidade
        confiancas["intent_gate"] = probabilidade
        confiancas["action"] = probabilidade
        resultado["confidence"] = confiancas
        resultado["intent_extension_applied"] = extensao.intent
        resultado["intent_extension_version"] = extensao.versao
        resultado["intent_extension_scope"] = extensao.escopo
        resultado["intent_extension_representation"] = extensao.representacao
        resultado["intent_extension_probability"] = probabilidade
        resultado["intent_extension_threshold"] = extensao.limiar
        if fatores:
            resultado["intent_extension_factor_probabilities"] = fatores
        return resultado

    def precarregar(self) -> bool:
        encoder = getattr(self, "encoder_semantico", None)
        if encoder is None:
            return True
        return bool(encoder.precarregar())


def treinar_modelo(
    exemplos: Iterable[Mapping[str, Any]],
    *,
    caminho: str | Path,
    versao: str,
    estrategia: str = "logistic",
    arquitetura_comando: str = "independent",
    arquitetura_acao: str = "global",
    limiar_comando: float = 0.5,
    limiares_comando_por_intent: Mapping[str, float] | None = None,
    limiares_fallback_intent_semantica: Mapping[str, float] | None = None,
    features_comando: str = "legado",
    features_comando_intents: Iterable[str] = (),
    features_intent_gate: str = "legado",
    representacao: str = "tfidf",
    encoder_semantico: Any = None,
    pasta_encoder_semantico: str | Path | None = None,
    sha256_encoder_semantico: str = "",
) -> ModeloNeuralComandos:
    itens = [dict(item) for item in exemplos]
    if not itens:
        raise ValueError("não é possível treinar com dataset vazio")
    textos = [str(item.get("text") or "").strip() for item in itens]
    if any(not texto for texto in textos):
        raise ValueError("todo exemplo precisa de text")

    rotulos_intent = [str(item.get("intent") or "NONE").upper() for item in itens]
    rotulos_comando = [bool(item.get("is_command")) for item in itens]
    rotulos_negacao = [bool(item.get("negated")) for item in itens]
    rotulos_acao = [str(item.get("action") or "none").casefold() for item in itens]

    def _indices_head(head: str) -> list[int]:
        return [
            indice
            for indice, item in enumerate(itens)
            if item.get("training_heads") is None
            or head in {
                str(valor or "").strip().casefold()
                for valor in item.get("training_heads", ())
            }
        ]

    indices_head_intent = _indices_head("intent")
    indices_head_intent_gate = _indices_head("intent_gate")
    indices_head_action = _indices_head("action")
    indices_head_command = _indices_head("command")
    indices_head_negation = _indices_head("negation")
    if not all((
        indices_head_intent,
        indices_head_intent_gate,
        indices_head_action,
        indices_head_command,
        indices_head_negation,
    )):
        raise ValueError("cada head neural precisa de ao menos um exemplo aplicável")
    indices_head_command_global = [
        indice
        for indice in indices_head_command
        if not str(itens[indice].get("command_head_intent") or "").strip()
    ]
    if not indices_head_command_global:
        raise ValueError("head command global precisa de ao menos um exemplo")
    estrategia_normalizada = str(estrategia or "").strip().casefold()
    representacao_normalizada = str(representacao or "").strip().casefold()
    if representacao_normalizada not in REPRESENTACOES_PERMITIDAS:
        raise ValueError(
            f"representação neural desconhecida: {representacao_normalizada}"
        )
    usa_semantica = representacao_normalizada in REPRESENTACOES_SEMANTICAS
    if usa_semantica and estrategia_normalizada != "sgd_log_loss":
        raise ValueError("encoder semântico experimental exige sgd_log_loss")
    if usa_semantica and encoder_semantico is None:
        if pasta_encoder_semantico is None:
            raise ValueError("representação ONNX exige encoder semântico")
        encoder_semantico = EncoderSemanticoONNX(
            pasta_encoder_semantico,
            sha256_modelo=sha256_encoder_semantico,
        )
    if (
        representacao_normalizada == "onnx_semantico_hibrido"
        and not isinstance(encoder_semantico, EncoderSemanticoHibrido)
    ):
        encoder_semantico = EncoderSemanticoHibrido(encoder_semantico)
    if usa_semantica:
        validar_encoder = getattr(encoder_semantico, "validar_artefatos", None)
        if not callable(validar_encoder):
            raise TypeError("encoder semântico não implementa validar_artefatos")
        validar_encoder()
        if representacao_normalizada == "onnx_semantico_hibrido":
            vetores_semanticos_base, vetores_semanticos = (
                encoder_semantico.codificar_componentes(textos)
            )
        else:
            vetores_semanticos_base = None
            vetores_semanticos = encoder_semantico.codificar(textos)
    else:
        encoder_semantico = None
        vetores_semanticos_base = None
        vetores_semanticos = None
    arquitetura_normalizada = str(arquitetura_acao or "").strip().casefold()
    if arquitetura_normalizada not in ARQUITETURAS_ACAO_PERMITIDAS:
        raise ValueError(
            f"arquitetura de ação desconhecida: {arquitetura_normalizada}"
        )
    arquitetura_comando_normalizada = str(
        arquitetura_comando or ""
    ).strip().casefold()
    if arquitetura_comando_normalizada not in ARQUITETURAS_COMANDO_PERMITIDAS:
        raise ValueError(
            "arquitetura de comando desconhecida: "
            f"{arquitetura_comando_normalizada}"
        )
    limiar_comando_validado = _validar_limiar_comando(limiar_comando)
    limiares_intent_validados = {
        str(intent or "").strip().upper(): _validar_limiar_comando(valor)
        for intent, valor in dict(limiares_comando_por_intent or {}).items()
    }
    if any(not intent or intent == "NONE" for intent in limiares_intent_validados):
        raise ValueError("limiar por intent exige intent operacional")
    limiares_fallback_validados = {
        str(intent or "").strip().upper(): _validar_limiar_comando(valor)
        for intent, valor in dict(
            limiares_fallback_intent_semantica or {}
        ).items()
    }
    if any(
        not intent or intent == "NONE"
        for intent in limiares_fallback_validados
    ):
        raise ValueError("fallback semântico exige intent operacional")
    representacao_geral = (
        "tfidf"
        if representacao_normalizada in {"tfidf_indicadores", *REPRESENTACOES_SEMANTICAS}
        else representacao_normalizada
    )
    representacao_gates = (
        "tfidf_indicadores" if usa_semantica else representacao_normalizada
    )
    ngramas_caracteres_gates = (
        (4, 6)
        if representacao_normalizada in {"tfidf_indicadores", *REPRESENTACOES_SEMANTICAS}
        else (3, 5)
    )
    features_comando_normalizadas = str(
        features_comando or "legado"
    ).strip().casefold()
    if features_comando_normalizadas not in FEATURES_COMANDO_PERMITIDAS:
        raise ValueError(
            f"features de comando desconhecidas: {features_comando_normalizadas}"
        )
    features_comando_intents_normalizadas = tuple(sorted({
        str(intent or "").strip().upper()
        for intent in features_comando_intents
        if str(intent or "").strip()
    }))
    if features_comando_normalizadas in {
        "modalidade_por_intent_v1",
        "modalidade_por_intent_v2",
        "modalidade_por_intent_v3",
        "modalidade_por_intent_v4_sparse",
    }:
        if not features_comando_intents_normalizadas:
            raise ValueError("modalidade por intent exige ao menos uma intent")
        if "NONE" in features_comando_intents_normalizadas:
            raise ValueError("features por intent exigem intents operacionais")
    elif features_comando_intents_normalizadas:
        raise ValueError(
            "features_comando_intents exige modo modalidade_por_intent"
        )
    def _preprocessador_comando(intent_alvo: str | None = None) -> Callable[[str], str]:
        usar_v4_sparse = (
            features_comando_normalizadas == "modalidade_v4_sparse"
            or (
                features_comando_normalizadas == "modalidade_por_intent_v4_sparse"
                and intent_alvo in features_comando_intents_normalizadas
            )
        )
        if usar_v4_sparse:
            return enriquecer_texto_features_comando_modalidade_v4_sparse
        usar_v3 = (
            features_comando_normalizadas == "modalidade_v3"
            or (
                features_comando_normalizadas == "modalidade_por_intent_v3"
                and intent_alvo in features_comando_intents_normalizadas
            )
        )
        if usar_v3:
            return enriquecer_texto_features_comando_modalidade_v3
        usar_v2 = (
            features_comando_normalizadas == "modalidade_v2"
            or (
                features_comando_normalizadas == "modalidade_por_intent_v2"
                and intent_alvo in features_comando_intents_normalizadas
            )
        )
        if usar_v2:
            return enriquecer_texto_features_comando_modalidade_v2
        usar_v1 = (
            features_comando_normalizadas == "modalidade_v1"
            or (
                features_comando_normalizadas == "modalidade_por_intent_v1"
                and intent_alvo in features_comando_intents_normalizadas
            )
        )
        return (
            enriquecer_texto_features_comando_modalidade
            if usar_v1
            else enriquecer_texto_features_comando
        )

    preprocessador_comando_global = _preprocessador_comando()
    cabeca_intent = (
        _classificador(
            [rotulos_intent[indice] for indice in indices_head_intent],
            estrategia_normalizada,
        ).fit(
            vetores_semanticos[indices_head_intent],
            [rotulos_intent[indice] for indice in indices_head_intent],
        )
        if usa_semantica
        else _pipeline(
            [rotulos_intent[indice] for indice in indices_head_intent],
            estrategia=estrategia_normalizada,
            representacao=representacao_geral,
        ).fit(
            [textos[indice] for indice in indices_head_intent],
            [rotulos_intent[indice] for indice in indices_head_intent],
        )
    )
    cabeca_intent_gate = (
        _classificador(
            [rotulos_intent[indice] for indice in indices_head_intent_gate],
            estrategia_normalizada,
        ).fit(
            vetores_semanticos_base[indices_head_intent_gate],
            [rotulos_intent[indice] for indice in indices_head_intent_gate],
        )
        if vetores_semanticos_base is not None
        else None
    )
    cabeca_comando = _pipeline(
        [rotulos_comando[indice] for indice in indices_head_command_global],
        estrategia=estrategia_normalizada,
        representacao=representacao_gates,
        preprocessador_indicadores=preprocessador_comando_global,
        ngramas_caracteres=ngramas_caracteres_gates,
    ).fit(
        [textos[indice] for indice in indices_head_command_global],
        [rotulos_comando[indice] for indice in indices_head_command_global],
    )
    alvos_head_comando = sorted({
        str(itens[indice].get("command_head_intent") or "").strip().upper()
        for indice in indices_head_command
        if str(itens[indice].get("command_head_intent") or "").strip()
    })
    cabecas_comando_por_intent: dict[str, Any] = {}
    for intent_alvo in alvos_head_comando:
        dominios_intent = {
            str(itens[indice].get("domain") or "").strip().casefold()
            for indice in indices_head_command
            if (
                str(itens[indice].get("command_head_intent") or "")
                .strip()
                .upper()
                == intent_alvo
                or (
                    not str(
                        itens[indice].get("command_head_intent") or ""
                    ).strip()
                    and str(itens[indice].get("intent") or "").strip().upper()
                    == intent_alvo
                )
            )
            and str(itens[indice].get("domain") or "").strip()
        }
        indices_intent = [
            indice
            for indice in indices_head_command
            if (
                str(itens[indice].get("command_head_intent") or "")
                .strip()
                .upper()
                == intent_alvo
            )
            or (
                not str(itens[indice].get("command_head_intent") or "").strip()
                and str(itens[indice].get("intent") or "").strip().upper()
                == intent_alvo
            )
            or (
                not str(itens[indice].get("command_head_intent") or "").strip()
                and not rotulos_comando[indice]
                and str(itens[indice].get("domain") or "").strip().casefold()
                in dominios_intent
            )
        ]
        rotulos_intent_comando = [
            rotulos_comando[indice] for indice in indices_intent
        ]
        if len(set(rotulos_intent_comando)) < 2:
            raise ValueError(
                f"head command direcionado {intent_alvo} exige exemplos positivos e negativos"
            )
        preprocessador_comando_intent = _preprocessador_comando(intent_alvo)
        cabecas_comando_por_intent[intent_alvo] = _pipeline(
            rotulos_intent_comando,
            estrategia=estrategia_normalizada,
            representacao=representacao_gates,
            preprocessador_indicadores=preprocessador_comando_intent,
            ngramas_caracteres=ngramas_caracteres_gates,
        ).fit(
            [textos[indice] for indice in indices_intent],
            rotulos_intent_comando,
        )
    cabeca_negacao = _pipeline(
        [rotulos_negacao[indice] for indice in indices_head_negation],
        estrategia=estrategia_normalizada,
        representacao=representacao_gates,
        ngramas_caracteres=ngramas_caracteres_gates,
    ).fit(
        [textos[indice] for indice in indices_head_negation],
        [rotulos_negacao[indice] for indice in indices_head_negation],
    )
    cabeca_acao = (
        _classificador(
            [rotulos_acao[indice] for indice in indices_head_action],
            estrategia_normalizada,
        ).fit(
            vetores_semanticos[indices_head_action],
            [rotulos_acao[indice] for indice in indices_head_action],
        )
        if usa_semantica
        else _pipeline(
            [rotulos_acao[indice] for indice in indices_head_action],
            estrategia=estrategia_normalizada,
            representacao=representacao_geral,
        ).fit(
            [textos[indice] for indice in indices_head_action],
            [rotulos_acao[indice] for indice in indices_head_action],
        )
    )
    cabecas_acao_por_intent: dict[str, Any] = {}
    if arquitetura_normalizada == "hierarchical":
        intents_comando = sorted({
            str(item.get("intent") or "").strip().upper()
            for indice in indices_head_action
            for item in [itens[indice]]
            if bool(item.get("is_command"))
            and str(item.get("intent") or "").strip().upper() != "NONE"
        })
        for intent in intents_comando:
            indices_intent = [
                indice
                for indice in indices_head_action
                for item in [itens[indice]]
                if bool(item.get("is_command"))
                and str(item.get("intent") or "").strip().upper() == intent
            ]
            itens_intent = [itens[indice] for indice in indices_intent]
            textos_intent = [str(item.get("text") or "").strip() for item in itens_intent]
            acoes_intent = [
                str(item.get("action") or "none").strip().casefold()
                for item in itens_intent
            ]
            cabecas_acao_por_intent[intent] = (
                _classificador(acoes_intent, estrategia_normalizada).fit(
                    vetores_semanticos[indices_intent],
                    acoes_intent,
                )
                if usa_semantica
                else _pipeline(
                    acoes_intent,
                    estrategia=estrategia_normalizada,
                    representacao=representacao_geral,
                ).fit(textos_intent, acoes_intent)
            )
    modelo = ModeloNeuralComandos(
        versao=str(versao or "sem-versao"),
        cabeca_intent=cabeca_intent,
        cabeca_comando=cabeca_comando,
        cabeca_negacao=cabeca_negacao,
        cabeca_acao=cabeca_acao,
        cabeca_intent_gate=cabeca_intent_gate,
        estrategia=estrategia_normalizada,
        arquitetura_comando=arquitetura_comando_normalizada,
        arquitetura_acao=arquitetura_normalizada,
        cabecas_acao_por_intent=cabecas_acao_por_intent,
        cabecas_comando_por_intent=cabecas_comando_por_intent,
        limiar_comando=limiar_comando_validado,
        limiares_comando_por_intent=limiares_intent_validados,
        limiares_fallback_intent_semantica=limiares_fallback_validados,
        features_comando=features_comando_normalizadas,
        features_comando_intents=features_comando_intents_normalizadas,
        representacao=representacao_normalizada,
        encoder_semantico=encoder_semantico,
    )
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    joblib.dump(modelo, temporario)
    temporario.replace(destino)
    return modelo


def adicionar_extensao_intent(
    modelo_base: ModeloNeuralComandos,
    exemplos: Iterable[Mapping[str, Any]],
    *,
    intent: str,
    action: str,
    limiar: float = 0.925,
    escopo: str = "",
    representacao: str = "tfidf",
    ativacao: str = "",
    versao: str = "",
    caminho: str | Path | None = None,
) -> ModeloNeuralComandos:
    """Cria candidato aditivo sem retreinar ou mutar as cabeças existentes."""
    if not isinstance(modelo_base, ModeloNeuralComandos):
        raise TypeError("modelo_base precisa ser ModeloNeuralComandos")
    intent_alvo = str(intent or "").strip().upper()
    action_alvo = str(action or "").strip().casefold()
    escopo_alvo = str(escopo or "").strip().casefold()
    representacao_normalizada = str(
        representacao or "tfidf"
    ).strip().casefold()
    if not intent_alvo or intent_alvo == "NONE":
        raise ValueError("extensão exige intent operacional")
    if not action_alvo or action_alvo == "none":
        raise ValueError("extensão exige action operacional")
    if representacao_normalizada not in REPRESENTACOES_EXTENSAO_PERMITIDAS - {"fatorada"}:
        raise ValueError("representação de extensão desconhecida")
    extensoes_atuais = dict(getattr(modelo_base, "extensoes_intent", {}) or {})
    chave_extensao = _chave_nova_extensao_intent(
        extensoes_atuais,
        intent_alvo,
        action_alvo,
    )

    itens = [dict(item) for item in exemplos]
    if not itens:
        raise ValueError("não é possível treinar extensão com dataset vazio")
    textos = [str(item.get("text") or "").strip() for item in itens]
    if any(not texto for texto in textos):
        raise ValueError("todo exemplo da extensão precisa de text")
    rotulos = []
    for item in itens:
        intent_item = str(item.get("intent") or "NONE").strip().upper()
        action_item = str(item.get("action") or "none").strip().casefold()
        escopo_item = str(item.get("extension_scope") or "").strip().casefold()
        if intent_item == intent_alvo and action_item == "none":
            raise ValueError(
                "exemplo da intent alvo exige action explícita"
            )
        rotulos.append(
            intent_item == intent_alvo
            and action_item == action_alvo
            and (not escopo_alvo or escopo_item == escopo_alvo)
        )
    if len(set(rotulos)) < 2:
        raise ValueError("extensão exige exemplos positivos e negativos")
    detector = _treinar_detector_extensao(
        modelo_base,
        textos,
        rotulos,
        representacao_normalizada,
    )
    extensao = ExtensaoIntentNeural(
        intent=intent_alvo,
        action=action_alvo,
        detector=detector,
        limiar=limiar,
        versao=str(versao or "").strip(),
        escopo=escopo_alvo,
        representacao=representacao_normalizada,
        ativacao=str(ativacao or "").strip().casefold(),
    )
    candidato = copy.copy(modelo_base)
    candidato.extensoes_intent = {
        **extensoes_atuais,
        chave_extensao: extensao,
    }
    if str(versao or "").strip():
        candidato.versao = str(versao).strip()
    if caminho is not None:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(destino.suffix + ".tmp")
        joblib.dump(candidato, temporario)
        temporario.replace(destino)
    return candidato


def adicionar_extensao_intent_fatorada(
    modelo_base: ModeloNeuralComandos,
    exemplos: Iterable[Mapping[str, Any]],
    *,
    intent: str,
    action: str,
    limiar: float = 0.925,
    representacoes_fatores: Mapping[str, str],
    ativacao: str = "",
    versao: str = "",
    caminho: str | Path | None = None,
) -> ModeloNeuralComandos:
    """Treina evidências independentes cuja conjunção propõe uma intent."""
    if not isinstance(modelo_base, ModeloNeuralComandos):
        raise TypeError("modelo_base precisa ser ModeloNeuralComandos")
    intent_alvo = str(intent or "").strip().upper()
    action_alvo = str(action or "").strip().casefold()
    if not intent_alvo or intent_alvo == "NONE":
        raise ValueError("extensão exige intent operacional")
    if not action_alvo or action_alvo == "none":
        raise ValueError("extensão exige action operacional")
    extensoes_atuais = dict(getattr(modelo_base, "extensoes_intent", {}) or {})
    chave_extensao = _chave_nova_extensao_intent(
        extensoes_atuais,
        intent_alvo,
        action_alvo,
    )
    _validar_limiar_extensao_intent(limiar)
    nomes_fatores = [
        str(nome or "").strip().casefold()
        for nome in dict(representacoes_fatores or {})
    ]
    if any(not nome for nome in nomes_fatores) or len(nomes_fatores) != len(set(nomes_fatores)):
        raise ValueError("fatores exigem nomes únicos e não vazios")
    representacoes = {
        str(nome or "").strip().casefold(): str(representacao or "").strip().casefold()
        for nome, representacao in dict(representacoes_fatores or {}).items()
        if str(nome or "").strip()
    }
    if not representacoes:
        raise ValueError("extensão fatorada exige fatores")
    permitidas_fatores = REPRESENTACOES_EXTENSAO_PERMITIDAS - {"fatorada"}
    if any(valor not in permitidas_fatores for valor in representacoes.values()):
        raise ValueError("representação de fator desconhecida")

    itens = [dict(item) for item in exemplos]
    textos = [str(item.get("text") or "").strip() for item in itens]
    if not itens or any(not texto for texto in textos):
        raise ValueError("extensão fatorada exige exemplos com text")
    detectores: dict[str, Any] = {}
    for nome, representacao in sorted(representacoes.items()):
        rotulos: list[bool] = []
        for item in itens:
            fatores = item.get("extension_factors")
            if not isinstance(fatores, Mapping) or not isinstance(
                fatores.get(nome), bool
            ):
                raise ValueError(
                    f"exemplo sem rótulo booleano para o fator {nome}"
                )
            rotulos.append(bool(fatores[nome]))
        if len(set(rotulos)) < 2:
            raise ValueError(f"fator {nome} exige exemplos positivos e negativos")
        detectores[nome] = _treinar_detector_extensao(
            modelo_base,
            textos,
            rotulos,
            representacao,
        )

    extensao = ExtensaoIntentNeural(
        intent=intent_alvo,
        action=action_alvo,
        detector=None,
        limiar=limiar,
        versao=str(versao or "").strip(),
        escopo="fatores:" + "+".join(sorted(detectores)),
        representacao="fatorada",
        ativacao=str(ativacao or "").strip().casefold(),
        detectores_fatores=detectores,
    )
    candidato = copy.copy(modelo_base)
    candidato.extensoes_intent = {
        **extensoes_atuais,
        chave_extensao: extensao,
    }
    if str(versao or "").strip():
        candidato.versao = str(versao).strip()
    if caminho is not None:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(destino.suffix + ".tmp")
        joblib.dump(candidato, temporario)
        temporario.replace(destino)
    return candidato



def adicionar_overlay_comando_modalidade(
    modelo_base: ModeloNeuralComandos,
    exemplos: Iterable[Mapping[str, Any]],
    *,
    intent: str,
    caminho: str | Path | None = None,
    versao: str = "",
    overlay: str = "modalidade_v4_sparse_v1",
) -> ModeloNeuralComandos:
    """Acopla um head estrutural sem retreinar nem substituir o head legado."""
    intent_alvo = str(intent or "").strip().upper()
    if not intent_alvo or intent_alvo == "NONE":
        raise ValueError("overlay de comando exige intent operacional")
    overlay_normalizado = str(overlay or "").strip().casefold()
    if overlay_normalizado not in OVERLAYS_COMANDO_MODALIDADE_PERMITIDOS:
        raise ValueError("overlay de comando desconhecido")
    cabecas_legadas = dict(
        getattr(modelo_base, "cabecas_comando_por_intent", {}) or {}
    )
    if intent_alvo not in cabecas_legadas:
        raise ValueError(
            f"overlay exige head de comando direcionado existente: {intent_alvo}"
        )

    itens = [dict(item) for item in exemplos]
    if not itens:
        raise ValueError("overlay exige dataset não vazio")

    def aplica_command_head(item: Mapping[str, Any]) -> bool:
        heads = item.get("training_heads")
        if heads is None:
            return True
        return "command" in {
            str(valor or "").strip().casefold() for valor in heads
        }

    indices_command = [
        indice for indice, item in enumerate(itens) if aplica_command_head(item)
    ]
    dominios_intent = {
        str(itens[indice].get("domain") or "").strip().casefold()
        for indice in indices_command
        if (
            str(itens[indice].get("command_head_intent") or "")
            .strip()
            .upper()
            == intent_alvo
            or (
                not str(
                    itens[indice].get("command_head_intent") or ""
                ).strip()
                and str(itens[indice].get("intent") or "").strip().upper()
                == intent_alvo
            )
        )
        and str(itens[indice].get("domain") or "").strip()
    }
    indices_intent = [
        indice
        for indice in indices_command
        if (
            str(itens[indice].get("command_head_intent") or "")
            .strip()
            .upper()
            == intent_alvo
        )
        or (
            not str(itens[indice].get("command_head_intent") or "").strip()
            and str(itens[indice].get("intent") or "").strip().upper()
            == intent_alvo
        )
        or (
            not str(itens[indice].get("command_head_intent") or "").strip()
            and not bool(itens[indice].get("is_command"))
            and str(itens[indice].get("domain") or "").strip().casefold()
            in dominios_intent
        )
    ]
    if not indices_intent:
        raise ValueError("overlay sem exemplos aplicáveis")
    textos = [str(itens[indice].get("text") or "").strip() for indice in indices_intent]
    rotulos = [bool(itens[indice].get("is_command")) for indice in indices_intent]
    if any(not texto for texto in textos):
        raise ValueError("overlay recebeu exemplo sem texto")
    if len(set(rotulos)) < 2:
        raise ValueError("overlay exige exemplos positivos e negativos")

    representacao_base = str(
        getattr(modelo_base, "representacao", "tfidf") or "tfidf"
    ).strip().casefold()
    representacao_gate = (
        "tfidf_indicadores"
        if representacao_base in REPRESENTACOES_SEMANTICAS
        else representacao_base
    )
    ngramas_caracteres = (
        (4, 6)
        if representacao_base in {
            "tfidf_indicadores",
            *REPRESENTACOES_SEMANTICAS,
        }
        else (3, 5)
    )
    estrategia = str(
        getattr(modelo_base, "estrategia", "logistic") or "logistic"
    ).strip().casefold()
    preprocessador_overlay = _preprocessador_overlay_comando(
        overlay_normalizado
    )
    cabeca_overlay = _pipeline(
        rotulos,
        estrategia=estrategia,
        representacao=representacao_gate,
        preprocessador_indicadores=preprocessador_overlay,
        ngramas_caracteres=ngramas_caracteres,
    ).fit(textos, rotulos)

    candidato = copy.copy(modelo_base)
    candidato.cabecas_comando_overlay_por_intent = dict(
        getattr(modelo_base, "cabecas_comando_overlay_por_intent", {}) or {}
    )
    candidato.versoes_overlay_comando_por_intent = dict(
        getattr(modelo_base, "versoes_overlay_comando_por_intent", {}) or {}
    )
    candidato.cabecas_comando_overlay_por_intent[intent_alvo] = cabeca_overlay
    candidato.versoes_overlay_comando_por_intent[intent_alvo] = overlay_normalizado
    if str(versao or "").strip():
        candidato.versao = str(versao).strip()

    if caminho is not None:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(destino.suffix + ".tmp")
        joblib.dump(candidato, temporario)
        temporario.replace(destino)
    return candidato


def carregar_modelo(caminho: str | Path) -> ModeloNeuralComandos:
    modelo = joblib.load(Path(caminho))
    if not isinstance(modelo, ModeloNeuralComandos):
        raise TypeError("artefato não contém ModeloNeuralComandos")
    if not getattr(modelo, "estrategia", ""):
        modelo.estrategia = "logistic"
    if not getattr(modelo, "arquitetura_acao", ""):
        modelo.arquitetura_acao = "global"
    if not getattr(modelo, "arquitetura_comando", ""):
        modelo.arquitetura_comando = "independent"
    if not hasattr(modelo, "cabecas_acao_por_intent"):
        modelo.cabecas_acao_por_intent = {}
    if not hasattr(modelo, "cabecas_intent_overlay"):
        modelo.cabecas_intent_overlay = {}
    modelo.cabecas_intent_overlay = dict(modelo.cabecas_intent_overlay or {})
    if any(
        str(chave or "").strip().casefold() not in OVERLAYS_INTENT_PERMITIDOS
        for chave in modelo.cabecas_intent_overlay
    ):
        raise ValueError("artefato contém overlay de intent desconhecido")
    modelo.cabecas_intent_overlay = {
        str(chave or "").strip().casefold(): valor
        for chave, valor in modelo.cabecas_intent_overlay.items()
    }
    if not hasattr(modelo, "cabecas_comando_por_intent"):
        modelo.cabecas_comando_por_intent = {}
    if not hasattr(modelo, "cabecas_comando_extensao_por_intent"):
        modelo.cabecas_comando_extensao_por_intent = {}
    modelo.cabecas_comando_extensao_por_intent = dict(
        modelo.cabecas_comando_extensao_por_intent or {}
    )
    if any(
        str(intent or "").strip().upper() == "NONE"
        for intent in modelo.cabecas_comando_extensao_por_intent
    ):
        raise ValueError("head de comando de extensão não pode usar NONE")
    modelo.cabecas_comando_extensao_por_intent = {
        str(intent or "").strip().upper(): head
        for intent, head in modelo.cabecas_comando_extensao_por_intent.items()
    }
    if not hasattr(modelo, "cabecas_comando_overlay_por_intent"):
        modelo.cabecas_comando_overlay_por_intent = {}
    if not hasattr(modelo, "versoes_overlay_comando_por_intent"):
        modelo.versoes_overlay_comando_por_intent = {}
    modelo.versoes_overlay_comando_por_intent = {
        str(intent or "").strip().upper(): str(versao or "").strip().casefold()
        for intent, versao in dict(
            modelo.versoes_overlay_comando_por_intent or {}
        ).items()
    }
    overlays = dict(modelo.cabecas_comando_overlay_por_intent or {})
    if set(overlays) != set(modelo.versoes_overlay_comando_por_intent):
        raise ValueError("artefato contém overlay de comando inconsistente")
    if any(
        versao not in OVERLAYS_COMANDO_MODALIDADE_PERMITIDOS
        for versao in modelo.versoes_overlay_comando_por_intent.values()
    ):
        raise ValueError("artefato contém versão de overlay desconhecida")
    if any(intent not in modelo.cabecas_comando_por_intent for intent in overlays):
        raise ValueError("overlay de comando sem head direcionado correspondente")
    modelo.cabecas_comando_overlay_por_intent = overlays
    if not hasattr(modelo, "cabeca_intent_gate"):
        modelo.cabeca_intent_gate = None
    if not hasattr(modelo, "limiar_comando"):
        modelo.limiar_comando = 0.5
    modelo.limiar_comando = _validar_limiar_comando(modelo.limiar_comando)
    if not hasattr(modelo, "limiares_comando_por_intent"):
        modelo.limiares_comando_por_intent = {}
    modelo.limiares_comando_por_intent = {
        str(intent or "").strip().upper(): _validar_limiar_comando(valor)
        for intent, valor in dict(modelo.limiares_comando_por_intent or {}).items()
    }
    if not hasattr(modelo, "limiares_fallback_intent_semantica"):
        modelo.limiares_fallback_intent_semantica = {}
    modelo.limiares_fallback_intent_semantica = {
        str(intent or "").strip().upper(): _validar_limiar_comando(valor)
        for intent, valor in dict(
            modelo.limiares_fallback_intent_semantica or {}
        ).items()
    }
    modelo.features_comando = str(
        getattr(modelo, "features_comando", "legado") or "legado"
    ).strip().casefold()
    if modelo.features_comando not in FEATURES_COMANDO_PERMITIDAS:
        raise ValueError("artefato contém features de comando desconhecidas")
    modelo.features_comando_intents = tuple(sorted({
        str(intent or "").strip().upper()
        for intent in getattr(modelo, "features_comando_intents", ()) or ()
        if str(intent or "").strip()
    }))
    if modelo.features_comando.startswith("modalidade_por_intent_"):
        if not modelo.features_comando_intents:
            raise ValueError("artefato de modalidade por intent sem escopo")
    elif modelo.features_comando_intents:
        raise ValueError("artefato contém escopo de features incompatível")
    modelo.features_intent_gate = str(
        getattr(modelo, "features_intent_gate", "legado") or "legado"
    ).strip().casefold()
    if modelo.features_intent_gate not in FEATURES_INTENT_GATE_PERMITIDAS:
        raise ValueError("artefato contém features de intent_gate desconhecidas")
    modelo.features_negacao = str(
        getattr(modelo, "features_negacao", "legado") or "legado"
    ).strip().casefold()
    if modelo.features_negacao not in FEATURES_NEGACAO_PERMITIDAS:
        raise ValueError("artefato contém features de negação desconhecidas")
    if not hasattr(modelo, "representacao"):
        modelo.representacao = "tfidf"
    if not hasattr(modelo, "encoder_semantico"):
        modelo.encoder_semantico = None
    if not hasattr(modelo, "extensoes_intent"):
        modelo.extensoes_intent = {}
    modelo.reavaliar_comando_apos_extensao = bool(
        getattr(modelo, "reavaliar_comando_apos_extensao", False)
    )
    extensoes = dict(modelo.extensoes_intent or {})
    pares: set[tuple[str, str]] = set()
    for chave, extensao in extensoes.items():
        if not isinstance(extensao, ExtensaoIntentNeural):
            raise TypeError("artefato contém extensão de intent inválida")
        if not hasattr(extensao, "escopo"):
            extensao.escopo = ""
        if not hasattr(extensao, "representacao"):
            extensao.representacao = "tfidf"
        if not hasattr(extensao, "ativacao"):
            extensao.ativacao = ""
        if not hasattr(extensao, "detectores_fatores"):
            extensao.detectores_fatores = {}
        extensao.__post_init__()
        chave_texto = str(chave or "").strip()
        chave_legada = extensao.intent
        chave_composta = f"{extensao.intent}::{extensao.action}"
        if chave_texto not in {chave_legada, chave_composta}:
            raise ValueError(
                "chave de extensão diverge da intent/action declarada"
            )
        par = (extensao.intent, extensao.action)
        if par in pares:
            raise ValueError(
                "artefato contém extensão intent/action duplicada"
            )
        pares.add(par)
    modelo.extensoes_intent = extensoes
    if modelo.representacao not in REPRESENTACOES_PERMITIDAS:
        raise ValueError("artefato contém representação neural desconhecida")
    if modelo.representacao in REPRESENTACOES_SEMANTICAS:
        encoder = getattr(modelo, "encoder_semantico", None)
        if encoder is None:
            raise ValueError("artefato sem encoder semântico")
        encoder.validar_artefatos()
    return modelo
