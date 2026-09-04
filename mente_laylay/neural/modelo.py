"""Modelo local pequeno e versionado para interpretação geral de comandos."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
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


@dataclass
class ExtensaoIntentNeural:
    """Detector lexical aditivo que propõe intent sem decidir comando."""

    intent: str
    action: str
    detector: Any
    limiar: float = 0.925
    versao: str = ""

    def __post_init__(self) -> None:
        self.intent = str(self.intent or "").strip().upper()
        self.action = str(self.action or "").strip().casefold()
        self.versao = str(self.versao or "").strip()
        self.limiar = _validar_limiar_extensao_intent(self.limiar)
        if not self.intent or self.intent == "NONE":
            raise ValueError("extensão exige intent operacional")
        if not self.action or self.action == "none":
            raise ValueError("extensão exige action operacional")
        if not callable(getattr(self.detector, "predict_proba", None)):
            raise TypeError("detector de extensão precisa implementar predict_proba")

    def probabilidade(self, texto: str) -> float:
        return _confianca(self.detector, texto, True)


@dataclass
class ModeloNeuralComandos:
    versao: str
    cabeca_intent: Any
    cabeca_comando: Any
    cabeca_negacao: Any
    cabeca_acao: Any
    cabeca_intent_gate: Any = None
    estrategia: str = "logistic"
    arquitetura_comando: str = "independent"
    arquitetura_acao: str = "global"
    cabecas_acao_por_intent: dict[str, Any] = field(default_factory=dict)
    cabecas_comando_por_intent: dict[str, Any] = field(default_factory=dict)
    limiar_comando: float = 0.5
    limiares_comando_por_intent: dict[str, float] = field(default_factory=dict)
    limiares_fallback_intent_semantica: dict[str, float] = field(
        default_factory=dict
    )
    representacao: str = "tfidf"
    encoder_semantico: Any = None
    extensoes_intent: dict[str, ExtensaoIntentNeural] = field(default_factory=dict)
    # Calibrado no frozen_v0: com 14 classes, comandos corretos começam em
    # 0.137. OOD não concede autoridade; comando, negação e risco são gates
    # independentes.
    limiar_ood: float = 0.13

    def prever(self, texto: str) -> dict[str, Any]:
        fala = " ".join(str(texto or "").strip().split())
        encoder = getattr(self, "encoder_semantico", None)
        entrada_intent_gate = None
        if (
            self.representacao == "onnx_semantico_hibrido"
            and encoder is not None
        ):
            entrada_intent_gate, entrada_semantica = (
                encoder.codificar_componentes([fala])
            )
        else:
            entrada_semantica = (
                encoder.codificar([fala])
                if self.representacao in REPRESENTACOES_SEMANTICAS
                and encoder is not None
                else None
            )
        entrada_intent = entrada_semantica if entrada_semantica is not None else fala
        intent = str(
            self.cabeca_intent.predict(_entrada_modelo(entrada_intent))[0]
        ).upper()
        confianca_intent = _confianca(
            self.cabeca_intent,
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
        limiar_comando = (
            limiares_por_intent.get(intent, limiar_comando_global)
            if (
                escopo_comando != "GLOBAL"
                or (intent == intent_gate and intent != "NONE")
            )
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
        negada = bool(self.cabeca_negacao.predict([fala])[0])
        confianca_negacao = _confianca(self.cabeca_negacao, fala, negada)
        params = {} if veto_comando or acao == "none" else {"acao": acao}
        resultado = {
            "intent": intent,
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
            "intent_gate_fallback_applied": bool(
                arquitetura_comando == "intent_gated"
                and intent != "NONE"
                and intent_gate == "NONE"
                and not veto_intent
            ),
            "negated": negada,
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
        ativadas: list[tuple[ExtensaoIntentNeural, float]] = []
        for extensao in extensoes.values():
            if not isinstance(extensao, ExtensaoIntentNeural):
                continue
            try:
                probabilidade = extensao.probabilidade(fala)
            except Exception:
                continue
            if probabilidade >= extensao.limiar:
                ativadas.append((extensao, probabilidade))
        # Ausência ou concorrência entre propostas preserva bit a bit a
        # interpretação base. Uma extensão nunca desempata outra extensão.
        if len(ativadas) != 1:
            return previsao_base
        extensao, probabilidade = ativadas[0]
        resultado = dict(previsao_base)
        resultado["intent"] = extensao.intent
        resultado["gate_intent"] = extensao.intent
        resultado["raw_action"] = extensao.action
        resultado["params"] = {"acao": extensao.action}
        resultado["ood"] = False
        confiancas = dict(resultado.get("confidence") or {})
        confiancas["intent"] = probabilidade
        confiancas["intent_gate"] = probabilidade
        confiancas["action"] = probabilidade
        resultado["confidence"] = confiancas
        resultado["intent_extension_applied"] = extensao.intent
        resultado["intent_extension_version"] = extensao.versao
        resultado["intent_extension_probability"] = probabilidade
        resultado["intent_extension_threshold"] = extensao.limiar
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
        preprocessador_indicadores=enriquecer_texto_features_comando,
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
        cabecas_comando_por_intent[intent_alvo] = _pipeline(
            rotulos_intent_comando,
            estrategia=estrategia_normalizada,
            representacao=representacao_gates,
            preprocessador_indicadores=enriquecer_texto_features_comando,
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
    versao: str = "",
    caminho: str | Path | None = None,
) -> ModeloNeuralComandos:
    """Cria candidato aditivo sem retreinar ou mutar as cabeças existentes."""
    if not isinstance(modelo_base, ModeloNeuralComandos):
        raise TypeError("modelo_base precisa ser ModeloNeuralComandos")
    intent_alvo = str(intent or "").strip().upper()
    action_alvo = str(action or "").strip().casefold()
    if not intent_alvo or intent_alvo == "NONE":
        raise ValueError("extensão exige intent operacional")
    if not action_alvo or action_alvo == "none":
        raise ValueError("extensão exige action operacional")
    extensoes_atuais = dict(getattr(modelo_base, "extensoes_intent", {}) or {})
    if intent_alvo in extensoes_atuais:
        raise ValueError(f"extensão de intent já existe: {intent_alvo}")

    itens = [dict(item) for item in exemplos]
    if not itens:
        raise ValueError("não é possível treinar extensão com dataset vazio")
    textos = [str(item.get("text") or "").strip() for item in itens]
    if any(not texto for texto in textos):
        raise ValueError("todo exemplo da extensão precisa de text")
    rotulos = [
        str(item.get("intent") or "NONE").strip().upper() == intent_alvo
        for item in itens
    ]
    if len(set(rotulos)) < 2:
        raise ValueError("extensão exige exemplos positivos e negativos")
    detector = _pipeline(
        rotulos,
        estrategia="sgd_log_loss",
        representacao="tfidf",
    ).fit(textos, rotulos)
    extensao = ExtensaoIntentNeural(
        intent=intent_alvo,
        action=action_alvo,
        detector=detector,
        limiar=limiar,
        versao=str(versao or "").strip(),
    )
    candidato = copy.copy(modelo_base)
    candidato.extensoes_intent = {**extensoes_atuais, intent_alvo: extensao}
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
    if not hasattr(modelo, "cabecas_comando_por_intent"):
        modelo.cabecas_comando_por_intent = {}
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
    if not hasattr(modelo, "representacao"):
        modelo.representacao = "tfidf"
    if not hasattr(modelo, "encoder_semantico"):
        modelo.encoder_semantico = None
    if not hasattr(modelo, "extensoes_intent"):
        modelo.extensoes_intent = {}
    extensoes = dict(modelo.extensoes_intent or {})
    for chave, extensao in extensoes.items():
        intent = str(chave or "").strip().upper()
        if not isinstance(extensao, ExtensaoIntentNeural):
            raise TypeError("artefato contém extensão de intent inválida")
        if intent != extensao.intent:
            raise ValueError("chave de extensão diverge da intent declarada")
    modelo.extensoes_intent = extensoes
    if modelo.representacao not in REPRESENTACOES_PERMITIDAS:
        raise ValueError("artefato contém representação neural desconhecida")
    if modelo.representacao in REPRESENTACOES_SEMANTICAS:
        encoder = getattr(modelo, "encoder_semantico", None)
        if encoder is None:
            raise ValueError("artefato sem encoder semântico")
        encoder.validar_artefatos()
    return modelo
