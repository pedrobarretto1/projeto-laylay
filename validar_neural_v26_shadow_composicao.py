"""Valida a candidata neural v26 no caminho de composição sem executar ações."""

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
from mente_laylay.neural.runtime import EspecialistaNeuralComandosRuntime


RAIZ = Path(__file__).resolve().parent
CAMINHO_ATIVO = RAIZ / "memoria" / "neural" / "modelo_ativo.joblib"
CAMINHO_CANDIDATO = (
    RAIZ
    / "memoria"
    / "neural"
    / "experimentos"
    / "hibrido_v3_iot_v4_negacao_v5_cmd_v6_exp_v7_telegraphic_final_v8_v26"
    / "modelo_candidato.joblib"
)
HASH_CANDIDATO_ESPERADO = (
    "B711BB036F3DE4F64AA977A83C324EE3903FDDB771BA94FC3BC4E07D43C02626"
)
VERSAO_ESPERADA = (
    "hibrido_v3_iot_v4_negacao_v5_cmd_v6_exp_v7_telegraphic_final_v8_v26"
)

SONDAS = (
    ("deixa a lâmpada acesa", "IOT_CONTROL", "on", True),
    ("vai para github", "OPEN_URL", "open", True),
    ("acha canção amor", "MUSIC_SEARCH", "search", True),
    ("qual a previsão hoje", "WEATHER", "query", True),
    ("acho canção de amor bonita", "MUSIC_SEARCH", "search", False),
    ("ela acha canção de amor bonita", "", "", False),
    ("você consegue colocar música em apresentações", "", "", False),
)

SONDAS_SEGMENTADAS = (
    "abre o opera e abaixa o volume",
    "não abra o opera, mas abaixa o volume",
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
    if not CAMINHO_ATIVO.is_file():
        raise FileNotFoundError(f"modelo ativo ausente: {CAMINHO_ATIVO}")
    if not CAMINHO_CANDIDATO.is_file():
        raise FileNotFoundError(f"candidata v26 ausente: {CAMINHO_CANDIDATO}")

    hash_ativo_antes = _sha256(CAMINHO_ATIVO)
    hash_candidato = _sha256(CAMINHO_CANDIDATO)
    if hash_candidato != HASH_CANDIDATO_ESPERADO:
        raise RuntimeError(
            "hash da candidata v26 divergiu: "
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

    with tempfile.TemporaryDirectory(prefix="laylay-neural-v26-shadow-") as pasta:
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
            raise RuntimeError("a candidata v26 não pôde ser pré-carregada")
        if modelo.versao != VERSAO_ESPERADA:
            raise RuntimeError(
                f"versão inesperada: esperado={VERSAO_ESPERADA} obtido={modelo.versao}"
            )

        resultados = []
        for texto, intent, acao, comando in SONDAS:
            turno = _turno_canonico(texto)
            turno_antes = deepcopy(turno)
            observado = observar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime},
                texto,
                turno,
            )
            finalizado = finalizar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime},
                texto,
                observado,
            )
            previsao = dict(finalizado.get("previsao_neural") or {})

            if turno != turno_antes:
                raise AssertionError(f"o shadow mutou o turno canônico: {texto}")
            if observado.get("autoriza_execucao") != turno_antes.get("autoriza_execucao"):
                raise AssertionError(f"o shadow alterou a autoridade canônica: {texto}")
            if previsao.get("route") != "SHADOW":
                raise AssertionError(f"rota não-shadow: {texto}")
            if previsao.get("autoriza_execucao") is not False:
                raise AssertionError(f"a previsão neural criou autoridade: {texto}")
            if bool(previsao.get("is_command")) is not comando:
                raise AssertionError(f"classificação de comando inesperada: {texto}")
            if str(previsao.get("intent") or "") != intent:
                raise AssertionError(f"intent inesperada: {texto}")
            if str(dict(previsao.get("params") or {}).get("acao") or "") != acao:
                raise AssertionError(f"ação inesperada: {texto}")

            resultados.append(
                {
                    "texto": texto,
                    "neural": {
                        "is_command": previsao.get("is_command"),
                        "intent": previsao.get("intent"),
                        "acao": dict(previsao.get("params") or {}).get("acao", ""),
                        "autoriza_execucao": previsao.get("autoriza_execucao"),
                    },
                    "canonico": {
                        "modalidade": turno_antes.get("modalidade_geral"),
                        "autoriza_execucao": turno_antes.get("autoriza_execucao"),
                    },
                    "comparacao": dict(previsao.get("comparacao_canonica") or {}),
                }
            )

        resultados_segmentados = []
        for texto in SONDAS_SEGMENTADAS:
            turno = _turno_canonico(texto)
            turno_antes = deepcopy(turno)
            segmentos_canonicos = list(turno.get("segmentos") or [])
            if len(segmentos_canonicos) < 2:
                raise AssertionError(
                    f"o owner canônico não segmentou a sonda: {texto}"
                )
            observado = observar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime},
                texto,
                turno,
            )
            finalizado = finalizar_especialista_neural_turno(
                {"_especialista_neural_comandos_runtime": runtime},
                texto,
                observado,
            )
            previsao = dict(finalizado.get("previsao_neural") or {})
            previsoes_segmentos = list(
                previsao.get("previsoes_segmentos") or []
            )
            if turno != turno_antes:
                raise AssertionError(
                    f"o shadow segmentado mutou o turno canônico: {texto}"
                )
            if len(previsoes_segmentos) != len(segmentos_canonicos):
                raise AssertionError(
                    f"a neural não observou todos os segmentos: {texto}"
                )
            if previsao.get("segmentos_origem") != "turno_canonico":
                raise AssertionError(
                    f"a neural criou segmentação privada: {texto}"
                )
            if previsao.get("autoriza_execucao") is not False or any(
                item.get("autoriza_execucao") is not False
                for item in previsoes_segmentos
            ):
                raise AssertionError(
                    f"a observação segmentada criou autoridade: {texto}"
                )
            resultados_segmentados.append({
                "texto": texto,
                "segmentos_canonicos": len(segmentos_canonicos),
                "intents_neurais": [
                    str(item.get("intent") or "")
                    for item in previsoes_segmentos
                ],
                "comparacao": dict(
                    previsao.get("comparacao_canonica") or {}
                ),
            })

        caminho_eventos = pasta_estado / "shadow_eventos.jsonl"
        caminho_relatorio = pasta_estado / "shadow_relatorio.json"
        eventos = [
            json.loads(linha)
            for linha in caminho_eventos.read_text(encoding="utf-8").splitlines()
            if linha.strip()
        ]
        relatorio = json.loads(caminho_relatorio.read_text(encoding="utf-8"))
        if len(eventos) != len(SONDAS) + len(SONDAS_SEGMENTADAS):
            raise AssertionError("a composição não persistiu todas as comparações")
        if not all(
            evento.get("somente_observacao") is True
            and evento.get("autoriza_execucao") is False
            and evento.get("apto_treino") is False
            and evento.get("predicao_propria_vira_label") is False
            for evento in eventos
        ):
            raise AssertionError("um evento shadow violou o contrato fail-closed")

        totais = dict(relatorio.get("totais") or {})
        if totais.get("turnos") != len(SONDAS) + len(SONDAS_SEGMENTADAS):
            raise AssertionError("total de turnos do relatório shadow divergiu")
        eventos_simples = eventos[:len(SONDAS)]
        falsos_simples = sum(
            bool(item.get("comparacao", {}).get("falso_comando_neural"))
            for item in eventos_simples
        )
        perdidos_simples = sum(
            bool(item.get("comparacao", {}).get("comando_perdido_neural"))
            for item in eventos_simples
        )
        if falsos_simples != 2:
            raise AssertionError("as duas divergências canônicas esperadas não apareceram")
        if perdidos_simples != 0:
            raise AssertionError("a v26 perdeu um comando canônico nas sondas")
        if totais.get("segmentos_comparaveis") != 4:
            raise AssertionError("os quatro segmentos não foram comparados")

    hash_ativo_depois = _sha256(CAMINHO_ATIVO)
    if hash_ativo_depois != hash_ativo_antes:
        raise AssertionError("o ensaio alterou o modelo ativo")

    return {
        "status": "green_composicao_shadow",
        "modelo": VERSAO_ESPERADA,
        "hash_candidato": hash_candidato,
        "hash_ativo_antes": hash_ativo_antes,
        "hash_ativo_depois": hash_ativo_depois,
        "modelo_ativo_preservado": True,
        "configuracao_proxima_sessao": {
            "modo": modo_configurado,
            "caminho_resolvido": str(caminho_resolvido.relative_to(RAIZ)),
        },
        "acoes_executadas": 0,
        "sondas": resultados,
        "sondas_segmentadas": resultados_segmentados,
        "totais_shadow": totais,
    }


if __name__ == "__main__":
    print(json.dumps(validar(), ensure_ascii=False, indent=2, sort_keys=True))
