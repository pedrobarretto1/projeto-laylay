"""Valida a extensão LIST_WINDOWS v27 na composição, sem executar ações."""

from __future__ import annotations

import hashlib
import json
import tempfile
from copy import deepcopy
from pathlib import Path

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    finalizar_especialista_neural_turno,
    observar_especialista_neural_turno,
)
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.carregador import (
    ModeloNeuralPreguicoso,
    resolver_caminho_modelo_neural,
)
from mente_laylay.neural.experiencias import BufferExperienciasNeurais
from mente_laylay.neural.modelo import carregar_modelo
from mente_laylay.neural.runtime import EspecialistaNeuralComandosRuntime


RAIZ = Path(__file__).resolve().parent
CAMINHO_ATIVO = RAIZ / "memoria" / "neural" / "modelo_ativo.joblib"
CAMINHO_BASE = (
    RAIZ / "memoria" / "neural" / "experimentos"
    / "hibrido_v3_iot_v4_negacao_v5_cmd_v6_exp_v7_telegraphic_final_v8_v26"
    / "modelo_candidato.joblib"
)
CAMINHO_CANDIDATO = (
    RAIZ / "memoria" / "neural" / "experimentos"
    / "v27_list_windows_onda_v1"
    / "modelo_candidato_extensao_estado_estrutura_v4.joblib"
)
HASH_CANDIDATO_ESPERADO = (
    "CAAA93027EB96451CBBF1C61136389AC8402533226C666225DA3A2DEF356E0CF"
)
VERSAO_ESPERADA = "hibrido_v26_ext_list_windows_estado_estrutura_v4_v27"

SONDAS_ALVO = (
    "O Opera está aberto?",
    "A microsoft store está aberta?",
    "A ferramenta de recortes continua aberta?",
    "O editor Krita ainda está aberto?",
    "O aplicativo Fotos está rodando?",
)

SONDAS_CONTRASTE = (
    "mantenha o Opera aberto",
    "abre o Spotify",
    "lista as abas abertas",
    "fecha as janelas abertas",
    "o navegador está com duas abas abertas",
    "eu costumo deixar vários programas abertos",
)

GATES_PRESERVADOS = (
    "is_command",
    "raw_is_command",
    "negated",
    "command_probability",
    "command_threshold",
)


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest().upper()


def _turno_canonico(texto: str) -> dict:
    return classificar_modalidade_turno(
        texto,
        normalizar_texto=lambda valor: str(valor or "").casefold().strip(),
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )


def _configuracao_neural() -> dict[str, str]:
    resultado: dict[str, str] = {}
    for linha in (RAIZ / "configuracao.env").read_text(
        encoding="utf-8-sig"
    ).splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, valor = texto.split("=", 1)
        if chave.strip() in {"LAYLAY_NEURAL_MODE", "LAYLAY_NEURAL_MODEL_PATH"}:
            resultado[chave.strip()] = valor.strip().strip('"').strip("'")
    return resultado


def validar() -> dict:
    for caminho in (CAMINHO_ATIVO, CAMINHO_BASE, CAMINHO_CANDIDATO):
        if not caminho.is_file():
            raise FileNotFoundError(f"artefato ausente: {caminho}")
    hash_ativo_antes = _sha256(CAMINHO_ATIVO)
    hash_candidato = _sha256(CAMINHO_CANDIDATO)
    if hash_candidato != HASH_CANDIDATO_ESPERADO:
        raise RuntimeError(
            "hash da candidata v27 divergiu: "
            f"esperado={HASH_CANDIDATO_ESPERADO} obtido={hash_candidato}"
        )

    configuracao = _configuracao_neural()
    modo_configurado = configuracao.get("LAYLAY_NEURAL_MODE", "shadow")
    caminho_resolvido = resolver_caminho_modelo_neural(
        raiz=RAIZ,
        pasta_memoria=RAIZ / "memoria",
        configurado=configuracao.get("LAYLAY_NEURAL_MODEL_PATH", ""),
        modo=modo_configurado,
    ).resolve()
    if modo_configurado.casefold() != "shadow":
        raise AssertionError("configuração neural não está em modo shadow")
    if caminho_resolvido != CAMINHO_CANDIDATO.resolve():
        raise AssertionError(
            f"configuração resolveu outro artefato neural: {caminho_resolvido}"
        )

    modelo_base = carregar_modelo(CAMINHO_BASE)
    resultados_alvo: list[dict] = []
    resultados_contraste: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="laylay-neural-v27-shadow-") as pasta:
        pasta_estado = Path(pasta)
        modelo = ModeloNeuralPreguicoso(CAMINHO_CANDIDATO)
        runtime = EspecialistaNeuralComandosRuntime(
            modelo=modelo,
            buffer=BufferExperienciasNeurais(pasta_estado / "experiencias.jsonl"),
            publicar=None,
            modo="shadow",
            intents_permitidas=intents_registradas(),
            log=lambda *_args: None,
        )
        if not runtime.preaquecer():
            raise RuntimeError("a candidata v27 não pôde ser pré-carregada")
        if modelo.versao != VERSAO_ESPERADA:
            raise RuntimeError(f"versão inesperada: {modelo.versao}")

        for texto in SONDAS_ALVO:
            turno = _turno_canonico(texto)
            turno_antes = deepcopy(turno)
            base = modelo_base.prever(texto)
            observado = observar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime}, texto, turno,
            )
            finalizado = finalizar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime},
                texto,
                observado,
            )
            previsao = dict(finalizado.get("previsao_neural") or {})
            if turno != turno_antes:
                raise AssertionError(f"shadow mutou o turno: {texto}")
            if previsao.get("route") != "SHADOW":
                raise AssertionError(f"rota não-shadow: {texto}")
            if previsao.get("autoriza_execucao") is not False:
                raise AssertionError(f"extensão criou autoridade: {texto}")
            if previsao.get("intent") != "LIST_WINDOWS":
                raise AssertionError(f"intent inesperada: {texto}")
            if dict(previsao.get("params") or {}).get("acao") != "list":
                raise AssertionError(f"ação inesperada: {texto}")
            extensao = dict(previsao.get("intent_extension") or {})
            if extensao.get("intent") != "LIST_WINDOWS":
                raise AssertionError(f"extensão não foi observável: {texto}")
            bruto = modelo.prever(texto)
            if any(bruto[chave] != base[chave] for chave in GATES_PRESERVADOS):
                raise AssertionError(f"extensão alterou gate base: {texto}")
            resultados_alvo.append({
                "texto": texto,
                "intent": previsao.get("intent"),
                "acao": dict(previsao.get("params") or {}).get("acao"),
                "is_command": previsao.get("is_command"),
                "negated": previsao.get("negated"),
                "autoriza_execucao": previsao.get("autoriza_execucao"),
            })

        for texto in SONDAS_CONTRASTE:
            turno = _turno_canonico(texto)
            turno_antes = deepcopy(turno)
            base = modelo_base.prever(texto)
            bruto = modelo.prever(texto)
            if bruto != base:
                raise AssertionError(f"contraste divergiu da v26: {texto}")
            finalizado = finalizar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime},
                texto,
                observar_especialista_neural_turno(
                    {"_especialista_neural_comandos_runtime": runtime},
                    texto,
                    turno,
                ),
            )
            previsao = dict(finalizado.get("previsao_neural") or {})
            if turno != turno_antes:
                raise AssertionError(f"shadow mutou contraste: {texto}")
            if previsao.get("autoriza_execucao") is not False:
                raise AssertionError(f"contraste criou autoridade: {texto}")
            resultados_contraste.append({
                "texto": texto,
                "intent": previsao.get("intent"),
                "is_command": previsao.get("is_command"),
                "autoriza_execucao": previsao.get("autoriza_execucao"),
            })

        eventos = [
            json.loads(linha)
            for linha in (pasta_estado / "shadow_eventos.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            if linha.strip()
        ]
        if len(eventos) != len(SONDAS_ALVO) + len(SONDAS_CONTRASTE):
            raise AssertionError("quantidade de eventos shadow divergiu")
        if not all(
            evento.get("somente_observacao") is True
            and evento.get("autoriza_execucao") is False
            and evento.get("apto_treino") is False
            and evento.get("predicao_propria_vira_label") is False
            for evento in eventos
        ):
            raise AssertionError("evento shadow violou contrato fail-closed")

    hash_ativo_depois = _sha256(CAMINHO_ATIVO)
    if hash_ativo_depois != hash_ativo_antes:
        raise AssertionError("ensaio alterou o modelo ativo")
    return {
        "status": "green_composicao_shadow",
        "modelo": VERSAO_ESPERADA,
        "hash_candidato": hash_candidato,
        "hash_ativo_antes": hash_ativo_antes,
        "hash_ativo_depois": hash_ativo_depois,
        "modelo_ativo_preservado": True,
        "configuracao_shadow": {
            "modo": modo_configurado,
            "caminho_resolvido": str(caminho_resolvido.relative_to(RAIZ)),
        },
        "acoes_executadas": 0,
        "sondas_alvo": resultados_alvo,
        "sondas_contraste": resultados_contraste,
        "eventos_shadow": len(SONDAS_ALVO) + len(SONDAS_CONTRASTE),
    }


if __name__ == "__main__":
    print(json.dumps(validar(), ensure_ascii=False, indent=2, sort_keys=True))
