from __future__ import annotations

import hashlib
import json

import joblib
import numpy as np
import pytest
from sklearn.pipeline import Pipeline

import mente_laylay.neural.modelo as modelo_neural
from mente_laylay.neural.contratos import normalizar_previsao_neural
from mente_laylay.neural.dataset import separar_dataset_por_familia, validar_exemplo
from mente_laylay.neural.dataset import carregar_jsonl, experiencias_para_dataset
from mente_laylay.neural.avaliacao import avaliar_previsoes
from mente_laylay.neural.cobertura import (
    analisar_cobertura_dataset,
    carregar_manifesto_variantes,
    validar_catalogo_variantes,
    validar_manifesto_variantes,
)
from mente_laylay.neural.experiencias import (
    BufferExperienciasNeurais,
    RegistroRevisoesCorrecoesNeurais,
)
from mente_laylay.neural.governanca import avaliar_roteamento_neural
from mente_laylay.neural.carregador import (
    ModeloNeuralPreguicoso,
    resolver_caminho_modelo_neural,
)
from mente_laylay.neural.calibracao_ood import (
    avaliar_detector_ood_prototipos,
    avaliar_detector_ood_semantico,
    calibrar_detector_ood,
    calibrar_limiar_ood,
    carregar_dataset_ood,
)
from mente_laylay.neural.encoder_semantico import EncoderSemanticoONNX
from mente_laylay.neural.modelo import (
    carregar_modelo,
    enriquecer_texto_features,
    enriquecer_texto_features_comando,
    treinar_modelo,
)
from mente_laylay.neural.promocao import avaliar_promocao
from mente_laylay.neural.qualidade import auditar_leakage_dataset
from mente_laylay.neural.runtime import EspecialistaNeuralComandosRuntime
from mente_laylay.neural.shadow import RelatorioShadowNeural
from mente_laylay.neural.treino import executar_ciclo_treino
from mente_laylay.neural.validacao_cruzada import (
    atribuir_fold_estavel,
    diagnosticar_erros_por_familia,
    validar_por_familias,
    varrer_limiares_comando,
    varrer_limiares_comando_por_intent,
)


from mente_laylay.neural.datasets.gerar_musica_search_onda_v3 import (
    gerar_exemplos as gerar_exemplos_musica_search_v3,
    validar_lote as validar_lote_musica_search_v3,
)
from mente_laylay.neural.datasets.gerar_musica_search_onda_v4 import (
    gerar_exemplos as gerar_exemplos_musica_search_v4,
    validar_lote as validar_lote_musica_search_v4,
)
from mente_laylay.neural.datasets.gerar_volume_onda_v2 import (
    gerar_exemplos as gerar_exemplos_volume_v2,
    validar_lote as validar_lote_volume_v2,
)
from mente_laylay.neural.datasets.gerar_navegador_onda_v1 import (
    gerar_exemplos as gerar_exemplos_navegador_v1,
    validar_lote as validar_lote_navegador_v1,
)
from mente_laylay.neural.datasets.gerar_apps_arquivos_onda_v1 import (
    gerar_exemplos as gerar_exemplos_apps_arquivos_v1,
    validar_lote as validar_lote_apps_arquivos_v1,
)
from mente_laylay.neural.datasets.gerar_list_windows_onda_v1 import (
    FRASES_VALIDACAO_RESERVADAS_V2,
    FRASES_VALIDACAO_RESERVADAS_V3,
    gerar_exemplos as gerar_exemplos_list_windows_v1,
    validar_lote as validar_lote_list_windows_v1,
)
from mente_laylay.neural.datasets.gerar_list_windows_onda_v2 import (
    FRASES_CAOS_RESERVADAS,
    gerar_exemplos as gerar_exemplos_list_windows_v2,
    validar_lote as validar_lote_list_windows_v2,
)
from mente_laylay.neural.datasets.gerar_iot_midia_clima_onda_v1 import (
    gerar_exemplos as gerar_exemplos_iot_midia_clima_v1,
    validar_lote as validar_lote_iot_midia_clima_v1,
)
from mente_laylay.neural.datasets.gerar_shadow_contrastivo_v2 import (
    gerar_exemplos as gerar_exemplos_shadow_contrastivo_v2,
    validar_lote as validar_lote_shadow_contrastivo_v2,
)
from mente_laylay.neural.datasets.gerar_shadow_mecanismos_v3 import (
    gerar_exemplos as gerar_exemplos_shadow_mecanismos_v3,
    validar_lote as validar_lote_shadow_mecanismos_v3,
)
from mente_laylay.neural.datasets.gerar_iot_fronteira_comando_v4 import (
    gerar_exemplos as gerar_exemplos_iot_fronteira_v4,
    validar_lote as validar_lote_iot_fronteira_v4,
)
from mente_laylay.neural.datasets.gerar_negacao_contrastiva_v5 import (
    gerar_exemplos as gerar_exemplos_negacao_v5,
    validar_lote as validar_lote_negacao_v5,
)
from mente_laylay.neural.datasets.gerar_ood_calibracao_v0 import (
    gerar_exemplos as gerar_exemplos_ood_v0,
    validar_lote as validar_lote_ood_v0,
)
from mente_laylay.neural.datasets.gerar_ood_detector_v1 import (
    gerar_exemplos as gerar_exemplos_ood_detector_v1,
    validar_lote as validar_lote_ood_detector_v1,
)
from mente_laylay.neural.datasets.gerar_ood_detector_v2 import (
    gerar_exemplos as gerar_exemplos_ood_detector_v2,
    validar_lote as validar_lote_ood_detector_v2,
)
from mente_laylay.cognicao.composicao_turno import DEPENDENCIAS_ORQUESTRACAO_TURNO
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    finalizar_especialista_neural_turno,
    observar_especialista_neural_turno,
)
from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    AdaptadoresAplicacaoRuntime,
)
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_consulta_sistema_local,
)
from mente_laylay.memoria_mental.correcoes_interpretacao import (
    concluir_correcao_interpretacao,
)


class _EncoderSemanticoFalso:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, ...]] = []
        self.precarregamentos = 0

    def validar_artefatos(self) -> bool:
        return True

    def precarregar(self) -> bool:
        self.precarregamentos += 1
        return True

    def codificar(self, textos) -> np.ndarray:
        lote = tuple(str(texto) for texto in textos)
        self.chamadas.append(lote)
        return np.asarray([
            [
                float(len(texto)),
                float("volume" in texto.casefold()),
                float("navegador" in texto.casefold()),
                float("não" in texto.casefold()),
            ]
            for texto in lote
        ], dtype=np.float32)


class _ModeloFalso:
    versao = "teste-v0"

    @staticmethod
    def prever(_texto: str) -> dict:
        return {
            "intent": "VOLUME",
            "params": {"acao": "down"},
            "is_command": True,
            "negated": False,
            "ood": False,
            "confidence": {
                "intent": 0.96,
                "command": 0.98,
                "negation": 0.99,
            },
        }


class _DetectorExtensaoFalso:
    classes_ = np.asarray([False, True], dtype=object)

    def __init__(self, termos: tuple[str, ...]) -> None:
        self.termos = tuple(item.casefold() for item in termos)

    def predict_proba(self, entradas) -> np.ndarray:
        probabilidades = []
        for entrada in entradas:
            texto = str(entrada or "").casefold()
            positiva = 0.99 if any(item in texto for item in self.termos) else 0.01
            probabilidades.append([1.0 - positiva, positiva])
        return np.asarray(probabilidades, dtype=float)


def test_varredura_limiar_reaplica_gate_sem_retreinar() -> None:
    esperados = [
        {"intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    previstos = [
        {"intent": "VOLUME", "raw_is_command": True, "command_probability": 0.90, "is_command": True, "negated": False, "params": {"acao": "up"}},
        {"intent": "VOLUME", "raw_is_command": True, "command_probability": 0.70, "is_command": True, "negated": False, "params": {"acao": "up"}},
        {"intent": "VOLUME", "raw_is_command": True, "command_probability": 0.64, "is_command": True, "negated": False, "params": {"acao": "up"}},
        {"intent": "NONE", "raw_is_command": True, "command_probability": 0.95, "is_command": False, "negated": False, "params": {}},
        {"intent": "VOLUME", "gate_intent": "NONE", "raw_is_command": True, "command_probability": 0.95, "is_command": False, "negated": False, "params": {"acao": "up"}},
    ]

    resultados = varrer_limiares_comando(
        esperados,
        previstos,
        arquitetura_comando="intent_gated",
        limiares=(0.5, 0.65, 0.75),
    )

    assert resultados[0]["false_command_count"] == 1
    assert resultados[1]["false_command_count"] == 0
    assert resultados[1]["command_recall"] == 1.0
    assert resultados[2]["command_recall"] == 0.5


def test_varredura_por_intent_preserva_limiar_dos_demais() -> None:
    esperados = [
        {"intent": "IOT_CONTROL", "is_command": True, "negated": False, "action": "off"},
        {"intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    previstos = [
        {"intent": "IOT_CONTROL", "gate_intent": "IOT_CONTROL", "raw_is_command": True, "command_probability": 0.61, "is_command": False, "negated": False, "params": {"acao": "off"}},
        {"intent": "VOLUME", "gate_intent": "VOLUME", "raw_is_command": True, "command_probability": 0.61, "is_command": False, "negated": False, "params": {"acao": "up"}},
        {"intent": "IOT_CONTROL", "gate_intent": "IOT_CONTROL", "raw_is_command": True, "command_probability": 0.55, "is_command": False, "negated": False, "params": {"acao": "on"}},
    ]

    resultados = varrer_limiares_comando_por_intent(
        esperados,
        previstos,
        intent_alvo="IOT_CONTROL",
        limiar_padrao=0.65,
        arquitetura_comando="intent_gated",
        limiares=(0.60, 0.65),
    )

    assert resultados[0]["command_recall"] == 0.5
    assert resultados[0]["false_command_count"] == 0
    assert resultados[0]["mudancas_total"] == 1
    assert resultados[0]["mudancas"][0]["text"] == ""
    assert resultados[1]["command_recall"] == 0.0


def test_particao_hash_mantem_grupos_antigos_quando_novos_entram() -> None:
    antigos = [f"grupo_{numero}" for numero in range(30)]
    atribuicoes_antigas = {
        grupo: atribuir_fold_estavel(grupo, n_splits=5) for grupo in antigos
    }
    ampliados = [*antigos, *(f"novo_{numero}" for numero in range(20))]
    atribuicoes_ampliadas = {
        grupo: atribuir_fold_estavel(grupo, n_splits=5) for grupo in ampliados
    }

    assert all(
        atribuicoes_ampliadas[grupo] == fold
        for grupo, fold in atribuicoes_antigas.items()
    )
    assert set(atribuicoes_ampliadas.values()) == set(range(5))


def test_validacao_separa_metricas_da_base_comparavel() -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down", "family": "a"},
        {"text": "aumenta o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up", "family": "b"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none", "family": "c"},
        {"text": "ontem ajustei o som", "intent": "NONE", "is_command": False, "negated": False, "action": "none", "family": "d"},
    ]

    relatorio = validar_por_familias(
        exemplos,
        n_splits=2,
        quantidade_base_comparavel=2,
    )

    assert relatorio["totais"]["exemplos_base_comparavel"] == 2
    assert relatorio["metricas_base_comparavel"]["total"] == 2
    assert relatorio["metricas"]["total"] == 4
    assert "VOLUME" not in relatorio["varredura_limiar_por_intent_base_comparavel"]


def test_dataset_preserva_escopo_explicito_de_heads() -> None:
    exemplo = validar_exemplo(
        {
            "text": "despausa aí",
            "intent": "MEDIA_CONTROL",
            "is_command": True,
            "negated": False,
            "action": "play",
            "family": "despausa_curto",
            "source": "MANUAL_PARAPHRASE",
            "domain": "music",
            "training_heads": ["action", "intent", "intent"],
        },
        intents_permitidas={"MEDIA_CONTROL"},
    )

    assert exemplo["training_heads"] == ["action", "intent"]
    with pytest.raises(ValueError, match="head vazio ou desconhecido"):
        validar_exemplo(
            {**exemplo, "training_heads": ["executor"]},
            intents_permitidas={"MEDIA_CONTROL"},
        )


def test_dataset_preserva_alvo_de_head_comando_sem_mudar_label() -> None:
    exemplo = validar_exemplo(
        {
            "text": "costumo deixar o ventilador desligado",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "family": "iot_habito",
            "source": "HARD_NEGATIVE",
            "domain": "iot",
            "training_heads": ["command"],
            "command_head_intent": "iot_control",
        },
        intents_permitidas={"IOT_CONTROL"},
    )

    assert exemplo["intent"] == "NONE"
    assert exemplo["command_head_intent"] == "IOT_CONTROL"

    multihead = validar_exemplo(
        {**exemplo, "training_heads": ["command", "negation"]},
        intents_permitidas={"IOT_CONTROL"},
    )
    assert multihead["training_heads"] == ["command", "negation"]

    with pytest.raises(ValueError, match="exige o head command"):
        validar_exemplo(
            {**exemplo, "training_heads": ["intent"]},
            intents_permitidas={"IOT_CONTROL"},
        )

    with pytest.raises(ValueError, match="intent operacional"):
        validar_exemplo(
            {**exemplo, "command_head_intent": "NONE"},
            intents_permitidas={"IOT_CONTROL"},
        )


def test_lote_musica_search_v3_atende_cotas_sem_criar_autoridade() -> None:
    exemplos = gerar_exemplos_musica_search_v3()
    resumo = validar_lote_musica_search_v3(exemplos)

    assert resumo == {
        "total": 240,
        "comandos": 160,
        "comandos_negados": 40,
        "nao_comandos": 80,
        "familias_comando": 30,
        "familias_nao_comando": 20,
    }
    assert all(item["domain"] == "music" for item in exemplos)
    assert all(item["intent"] in {"MUSIC_SEARCH", "NONE"} for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_musica_search_v4_distribui_mecanismos_sem_criar_autoridade() -> None:
    exemplos = gerar_exemplos_musica_search_v4()
    resumo = validar_lote_musica_search_v4(exemplos)

    assert resumo == {
        "total": 240,
        "comandos": 160,
        "comandos_negados": 40,
        "nao_comandos": 80,
        "familias_comando": 60,
        "familias_nao_comando": 40,
        "max_exemplos_por_familia": 3,
        "mecanismos_afirmativos": 20,
        "mecanismos_negados": 10,
        "mecanismos_nao_comando": 20,
    }
    assert all(item["domain"] == "music" for item in exemplos)
    assert all(item["intent"] in {"MUSIC_SEARCH", "NONE"} for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_volume_v2_completa_acoes_sem_criar_autoridade() -> None:
    exemplos = gerar_exemplos_volume_v2()
    resumo = validar_lote_volume_v2(exemplos)

    assert resumo == {
        "total": 324,
        "volume_down": 132,
        "volume_up": 132,
        "nao_comandos": 60,
        "familias_down": 44,
        "familias_up": 44,
        "familias_nao_comando": 30,
        "max_exemplos_por_familia": 3,
    }
    assert all(item["domain"] == "audio" for item in exemplos)
    assert all(item["intent"] in {"VOLUME", "NONE"} for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_navegador_v1_equilibra_quatro_variantes_sem_criar_autoridade() -> None:
    exemplos = gerar_exemplos_navegador_v1()
    resumo = validar_lote_navegador_v1(exemplos)

    assert resumo["total"] == 656
    assert resumo["nao_comandos"] == 80
    for intent in ("close_tab", "open_url", "list_tabs", "search"):
        assert resumo[intent] == 144
        assert resumo[f"{intent}_negados"] == 24
        assert resumo[f"{intent}_familias"] == 52
    assert resumo["max_exemplos_por_familia"] == 3
    assert all(item["domain"] == "browser" for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_apps_arquivos_v1_equilibra_variantes_sem_criar_autoridade() -> None:
    exemplos = gerar_exemplos_apps_arquivos_v1()
    resumo = validar_lote_apps_arquivos_v1(exemplos)

    assert resumo["total"] == 668
    assert resumo["hard_negatives_app"] == 40
    assert resumo["hard_negatives_files"] == 40
    for intent in ("file_read", "file_search"):
        assert resumo[intent] == 144
        assert resumo[f"{intent}_negados"] == 24
        assert resumo[f"{intent}_familias"] == 52
    assert resumo["app_open"] == 148
    assert resumo["app_open_negados"] == 20
    assert resumo["app_open_familias"] == 54
    assert resumo["close_app"] == 152
    assert resumo["close_app_negados"] == 16
    assert resumo["close_app_familias"] == 54
    assert resumo["max_exemplos_por_familia"] == 3
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_list_windows_v1_separa_consulta_de_abrir_e_fechar_apps() -> None:
    exemplos = gerar_exemplos_list_windows_v1()
    resumo = validar_lote_list_windows_v1(exemplos)

    assert resumo == {
        "total": 198,
        "list_windows": 150,
        "list_windows_afirmativos": 120,
        "list_windows_negados": 30,
        "list_windows_familias": 50,
        "hard_negatives_app": 48,
        "command_positivos": 0,
        "command_negativos": 0,
        "negation_afirmativos": 30,
        "negation_negados": 30,
        "grupos_validacao": 46,
        "grupos_entidade": 30,
        "max_exemplos_por_familia": 3,
    }
    assert any(
        item["text"] == "que aplicativos estão abertos"
        and item["intent"] == "LIST_WINDOWS"
        and item["action"] == "list"
        for item in exemplos
    )
    assert all(item["domain"] == "app" for item in exemplos)
    assert all(item["intent"] in {"LIST_WINDOWS", "NONE"} for item in exemplos)
    assert not any("command_head_intent" in item for item in exemplos)
    assert all(item["validation_entity_group"] for item in exemplos)
    assert sum(
        item["extension_scope"] == "estado_alvo" for item in exemplos
    ) == 48
    assert all(
        str(item["text"]).endswith("?")
        for item in exemplos
        if item["extension_scope"] == "estado_alvo"
    )
    assert all(
        item["validation_group"].endswith(item["family"].rsplit("_", 1)[-1])
        for item in exemplos
        if "_nao_comando_" in item["family"]
    )
    assert not any("command" in item["training_heads"] for item in exemplos)
    assert all(
        item["training_heads"] == ["intent", "intent_gate"]
        for item in exemplos if item["intent"] == "NONE"
    )
    contexto = {
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Opera"],
            "processos_segundo_plano": [],
        },
        "_resolver_alvo_ambiente": lambda _nome: {
            "programa_aberto": True,
            "programa_em_foco": False,
        },
        "_emitir_resposta_curta": lambda *_args, **_kwargs: None,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
    }
    for item in exemplos:
        if item["intent"] == "LIST_WINDOWS" and not item["negated"]:
            tratado, _rota = processar_consulta_sistema_local(
                contexto, item["text"]
            )
            assert tratado is True, item["text"]
    for texto in (
        *FRASES_VALIDACAO_RESERVADAS_V2,
        *FRASES_VALIDACAO_RESERVADAS_V3,
    ):
        tratado, rota = processar_consulta_sistema_local(contexto, texto)
        assert tratado is True, texto
        assert rota == "consulta_estado_programa"
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_list_windows_v2_separa_ato_entidade_e_holdout_do_caos() -> None:
    exemplos = gerar_exemplos_list_windows_v2()
    resumo = validar_lote_list_windows_v2(exemplos)

    assert resumo == {
        "total": 705,
        "positivos": 298,
        "negativos": 407,
        "familias": 336,
        "grupos_validacao": 100,
        "grupos_entidade": 85,
        "colisoes_caos": 0,
        "treina_command": 0,
        "ato_consulta_positivo": 451,
        "dominio_app_positivo": 552,
    }
    assert len(FRASES_CAOS_RESERVADAS) == 70
    assert all(
        item["extension_scope"] == "consulta_ativa"
        for item in exemplos
        if item["intent"] == "LIST_WINDOWS"
    )
    assert any(
        item["text"] == '"o GIMP está aberto?"'
        and item["intent"] == "NONE"
        for item in exemplos
    )
    assert any(
        item["text"] == "o GIMP está aberto."
        and item["intent"] == "NONE"
        for item in exemplos
    )
    assert not any("command" in item["training_heads"] for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)
    assert all(
        set(item["extension_factors"]) == {"ato_consulta", "dominio_app"}
        for item in exemplos
    )


def test_lote_iot_midia_clima_v1_completa_catalogo_sem_criar_autoridade() -> None:
    exemplos = gerar_exemplos_iot_midia_clima_v1()
    resumo = validar_lote_iot_midia_clima_v1(exemplos)

    assert resumo["total"] == 1032
    for domain in ("iot", "music", "weather"):
        assert resumo[f"hard_negatives_{domain}"] == 40
    for variante in (
        "media_control_next", "weather_query",
    ):
        assert resumo[variante] == 144
        assert resumo[f"{variante}_negados"] == 24
        assert resumo[f"{variante}_familias"] == 52
    assert resumo["iot_control_on"] == 148
    assert resumo["iot_control_on_negados"] == 20
    assert resumo["iot_control_on_familias"] == 54
    assert resumo["iot_control_off"] == 164
    assert resumo["iot_control_off_negados"] == 16
    assert resumo["iot_control_off_familias"] == 58
    assert resumo["media_control_play"] == 148
    assert resumo["media_control_play_negados"] == 20
    assert resumo["media_control_play_familias"] == 54
    assert resumo["media_control_pause"] == 164
    assert resumo["media_control_pause_negados"] == 16
    assert resumo["media_control_pause_familias"] == 58
    assert resumo["max_exemplos_por_familia"] == 3
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_iot_estado_imperativo_e_acao_afirmativa_nao_negacao() -> None:
    exemplos = gerar_exemplos_iot_midia_clima_v1()
    comandos_estado = [
        item
        for item in exemplos
        if item["intent"] == "IOT_CONTROL"
        and "_estado_" in item["family"]
    ]

    assert len(comandos_estado) == 12
    assert all(
        item["negated"] is False and "training_heads" not in item
        for item in comandos_estado
    )
    assert all(
        item["action"] == "off"
        for item in comandos_estado
        if "_estado_manter_desligado_" in item["family"]
    )
    assert all(
        item["action"] == "on"
        for item in comandos_estado
        if (
            "_estado_manter_ligado_" in item["family"]
            or "_estado_continuar_funcionando_" in item["family"]
        )
    )
    explicitos = [
        item
        for item in exemplos
        if item["intent"] == "IOT_CONTROL"
        and "_negada_nao_" in item["family"]
    ]
    assert explicitos
    assert all("training_heads" not in item for item in explicitos)


def test_estado_oposto_com_capacidade_propria_vira_acao_afirmativa() -> None:
    apps = [
        item for item in gerar_exemplos_apps_arquivos_v1()
        if item["intent"] in {"APP_OPEN", "CLOSE_APP"}
        and "_estado_" in item["family"]
    ]
    midia = [
        item for item in gerar_exemplos_iot_midia_clima_v1()
        if item["intent"] == "MEDIA_CONTROL"
        and "_estado_" in item["family"]
    ]

    assert len(apps) == 12
    assert len(midia) == 12
    assert all(item["negated"] is False for item in [*apps, *midia])
    assert all(
        item["action"] == "close"
        for item in apps if "_estado_manter_fechado_" in item["family"]
    )
    assert all(
        item["action"] == "open"
        for item in apps
        if (
            "_estado_manter_aberto_" in item["family"]
            or "_estado_continuar_funcionando_" in item["family"]
        )
    )
    assert all(
        item["action"] == "pause"
        for item in midia if "_estado_manter_pausado_" in item["family"]
    )
    assert all(
        item["action"] == "play"
        for item in midia
        if (
            "_estado_continuar_sem_pausar_" in item["family"]
            or "_estado_deixar_continuar_" in item["family"]
        )
    )


def test_lote_negacao_v5_e_contrastivo_isolado_e_sem_leakage() -> None:
    exemplos = gerar_exemplos_negacao_v5()
    resumo = validar_lote_negacao_v5(exemplos)

    assert resumo == {
        "total": 108,
        "afirmativos": 54,
        "negados": 54,
        "grupos_validacao": 36,
        "max_exemplos_por_familia": 3,
        "training_heads": ["negation"],
    }
    assert all(item["training_heads"] == ["negation"] for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_shadow_contrastivo_v2_ensina_fronteiras_sem_copiar_receipts() -> None:
    exemplos = gerar_exemplos_shadow_contrastivo_v2()
    resumo = validar_lote_shadow_contrastivo_v2(exemplos)

    assert resumo["total"] >= 180
    assert resumo["comandos"] >= 120
    assert resumo["nao_comandos"] >= 60
    assert resumo["max_exemplos_por_familia"] <= 3
    assert resumo["grupos_validacao"] >= 20
    for variante in (
        "APP_OPEN:open",
        "CLOSE_APP:close",
        "CLOSE_TAB:close",
        "IOT_CONTROL:off",
        "IOT_CONTROL:on",
        "MEDIA_CONTROL:pause",
        "MEDIA_CONTROL:play",
        "MUSIC_SEARCH:search",
        "OPEN_URL:open",
    ):
        assert resumo["por_variante"][variante] >= 6

    textos = {item["text"].casefold() for item in exemplos}
    assert "pausa" not in textos
    assert "despausa" not in textos
    assert "liga a luz" not in textos
    assert "desliga a luz" not in textos
    assert "abre a microsoft store" not in textos
    assert all(item["source"] != "CURATED_RECEIPT" for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_shadow_mecanismos_v3_nao_desloca_heads_de_seguranca() -> None:
    exemplos = gerar_exemplos_shadow_mecanismos_v3()
    resumo = validar_lote_shadow_mecanismos_v3(exemplos)

    assert resumo["total"] == 84
    assert resumo["comandos"] == 84
    assert resumo["nao_comandos"] == 0
    assert resumo["training_heads"] == ["action", "intent"]
    assert all(
        item["training_heads"] == ["action", "intent"] for item in exemplos
    )
    assert not any(item["source"] == "CURATED_RECEIPT" for item in exemplos)


def test_lote_iot_fronteira_v4_positivos_tambem_ensinam_nao_negacao() -> None:
    exemplos = gerar_exemplos_iot_fronteira_v4()
    resumo = validar_lote_iot_fronteira_v4(exemplos)

    assert resumo == {
        "total": 168,
        "comandos": 66,
        "nao_comandos": 102,
        "grupos_validacao": 56,
        "positivos_training_heads": ["command", "negation"],
        "negativos_training_heads": ["command"],
        "command_head_intent": "IOT_CONTROL",
    }
    assert all(
        item["training_heads"] == ["command", "negation"]
        for item in exemplos if item["is_command"]
    )
    assert all(
        item["training_heads"] == ["command"]
        for item in exemplos if not item["is_command"]
    )
    assert all(
        item["command_head_intent"] == "IOT_CONTROL" for item in exemplos
    )
    assert not any("autoriza_execucao" in item for item in exemplos)


def test_lote_fronteiras_comando_v6_tem_owner_por_intent_sem_autoridade() -> None:
    from mente_laylay.neural.datasets.gerar_fronteiras_comando_v6 import (
        gerar_exemplos,
        validar_lote,
    )

    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 252,
        "comandos": 108,
        "nao_comandos": 144,
        "grupos_validacao": 82,
        "max_exemplos_por_familia": 3,
        "training_heads": ["command"],
        "por_intent": {
            "IOT_CONTROL": {"comandos": 24, "nao_comandos": 36},
            "MUSIC_SEARCH": {"comandos": 30, "nao_comandos": 36},
            "OPEN_URL": {"comandos": 24, "nao_comandos": 36},
            "WEATHER": {"comandos": 30, "nao_comandos": 36},
        },
    }
    assert all(item["training_heads"] == ["command"] for item in exemplos)
    assert all(
        item["command_head_intent"]
        in {"IOT_CONTROL", "MUSIC_SEARCH", "OPEN_URL", "WEATHER"}
        for item in exemplos
    )
    assert not any("autoriza_execucao" in item for item in exemplos)
    assert any(
        "music_search_positivo_achar_" in item["family"]
        for item in exemplos
    )
    assert any(
        "weather_positivo_qual_previsao_" in item["family"]
        for item in exemplos
    )
    grupos_achar = {
        item["validation_group"]
        for item in exemplos
        if "music_search_positivo_achar_" in item["family"]
    }
    grupos_qual_previsao = {
        item["validation_group"]
        for item in exemplos
        if "weather_positivo_qual_previsao_" in item["family"]
    }
    assert len(grupos_achar) == 1
    assert len(grupos_qual_previsao) == 1

    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    catalogo = __import__(
        "mente_laylay.especialistas.capacidades",
        fromlist=["intents_registradas"],
    ).intents_registradas()
    dev = carregar_jsonl(base / "dev_v0.jsonl", intents_permitidas=catalogo)
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=catalogo)
    receipts = [
        json.loads(linha)
        for linha in (base / "candidatos" / "shadow_real_curado_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if linha.strip()
    ]
    for reservados in (frozen, receipts):
        auditoria = auditar_leakage_dataset(
            [*dev, *exemplos],
            reservados,
            limiar_similaridade=0.9,
        )
        assert auditoria["aprovado"] is True, auditoria


def test_lote_expansao_mecanismos_v7_amplia_fronteiras_sem_copiar_reservados() -> None:
    from mente_laylay.neural.datasets.gerar_expansao_mecanismos_v7 import (
        gerar_exemplos,
        validar_lote,
    )

    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 126,
        "comandos": 78,
        "nao_comandos": 48,
        "grupos_validacao": 39,
        "max_exemplos_por_familia": 3,
        "positivos_training_heads_por_intent": {
            "MUSIC_SEARCH": {
                "achar_eliptico": ["command"],
                "demais": ["action", "command", "intent"],
            },
            "OPEN_URL": ["command"],
            "WEATHER": ["action", "command", "intent"],
        },
        "negativos_training_heads": ["command"],
        "por_intent": {
            "IOT_CONTROL": {"comandos": 0, "nao_comandos": 24},
            "MUSIC_SEARCH": {"comandos": 39, "nao_comandos": 0},
            "OPEN_URL": {"comandos": 3, "nao_comandos": 24},
            "WEATHER": {"comandos": 36, "nao_comandos": 0},
        },
    }
    assert all(
        item["training_heads"] == ["action", "command", "intent"]
        for item in exemplos
        if (
            item["is_command"]
            and item["command_head_intent"] != "OPEN_URL"
            and not item["family"].endswith("_achar_eliptico")
        )
    )
    assert all(
        item["training_heads"] == ["command"]
        for item in exemplos
        if item["command_head_intent"] == "OPEN_URL"
    )
    assert all(
        item["training_heads"] == ["command"]
        for item in exemplos
        if item["family"].endswith("_achar_eliptico")
    )
    assert all(
        item["training_heads"] == ["command"]
        for item in exemplos
        if not item["is_command"]
    )
    assert not any("autoriza_execucao" in item for item in exemplos)

    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    catalogo = __import__(
        "mente_laylay.especialistas.capacidades",
        fromlist=["intents_registradas"],
    ).intents_registradas()
    caminhos_anteriores = [
        base / "dev_v0.jsonl",
        base / "candidatos" / "onda_balanceada_v1.jsonl",
        base / "candidatos" / "musica_natural_modal_v2.jsonl",
        base / "candidatos" / "musica_search_onda_v4.jsonl",
        base / "candidatos" / "volume_piloto_v1.jsonl",
        base / "candidatos" / "volume_onda_v2.jsonl",
        base / "candidatos" / "navegador_onda_v1.jsonl",
        base / "candidatos" / "apps_arquivos_onda_v1.jsonl",
        base / "candidatos" / "iot_midia_clima_onda_v1.jsonl",
        base / "candidatos" / "shadow_mecanismos_v3.jsonl",
        base / "candidatos" / "iot_fronteira_comando_v4.jsonl",
        base / "candidatos" / "negacao_contrastiva_v5.jsonl",
        base / "candidatos" / "fronteiras_comando_v6.jsonl",
    ]
    anteriores = [
        item
        for caminho in caminhos_anteriores
        for item in carregar_jsonl(caminho, intents_permitidas=catalogo)
    ]
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=catalogo)
    receipts = [
        json.loads(linha)
        for linha in (base / "candidatos" / "shadow_real_curado_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if linha.strip()
    ]
    for reservados in (anteriores, frozen, receipts):
        auditoria = auditar_leakage_dataset(
            exemplos,
            reservados,
            limiar_similaridade=0.9,
        )
        assert auditoria["aprovado"] is True, auditoria


def test_lote_contraste_telegraphico_v8_separa_pedido_de_mencao_sem_leakage() -> None:
    from mente_laylay.neural.datasets.gerar_contraste_telegraphico_v8 import (
        gerar_exemplos,
        validar_lote,
    )

    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)

    assert resumo == {
        "total": 18,
        "comandos": 9,
        "nao_comandos": 9,
        "grupos_validacao": 6,
        "max_exemplos_por_familia": 3,
        "positivos_training_heads": ["command"],
        "intent_gate_training_family": "pedido_achar_eliptico",
        "negativos_training_heads": ["command"],
        "command_head_intent": "MUSIC_SEARCH",
    }
    assert all(
        item["training_heads"] == ["command", "intent_gate"]
        for item in exemplos
        if item["text"].startswith("acha ")
    )
    assert all(
        item["training_heads"] == ["command"]
        for item in exemplos
        if not item["text"].startswith("acha ")
    )
    assert all(
        item["command_head_intent"] == "MUSIC_SEARCH" for item in exemplos
    )
    assert all(item["intent"] == ("MUSIC_SEARCH" if item["is_command"] else "NONE") for item in exemplos)
    assert not any("autoriza_execucao" in item for item in exemplos)

    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    catalogo = __import__(
        "mente_laylay.especialistas.capacidades",
        fromlist=["intents_registradas"],
    ).intents_registradas()
    caminhos_anteriores = [
        base / "dev_v0.jsonl",
        base / "candidatos" / "onda_balanceada_v1.jsonl",
        base / "candidatos" / "musica_natural_modal_v2.jsonl",
        base / "candidatos" / "musica_search_onda_v4.jsonl",
        base / "candidatos" / "volume_piloto_v1.jsonl",
        base / "candidatos" / "volume_onda_v2.jsonl",
        base / "candidatos" / "navegador_onda_v1.jsonl",
        base / "candidatos" / "apps_arquivos_onda_v1.jsonl",
        base / "candidatos" / "iot_midia_clima_onda_v1.jsonl",
        base / "candidatos" / "shadow_mecanismos_v3.jsonl",
        base / "candidatos" / "iot_fronteira_comando_v4.jsonl",
        base / "candidatos" / "negacao_contrastiva_v5.jsonl",
        base / "candidatos" / "fronteiras_comando_v6.jsonl",
        base / "candidatos" / "expansao_mecanismos_v7.jsonl",
    ]
    anteriores = [
        item
        for caminho in caminhos_anteriores
        for item in carregar_jsonl(caminho, intents_permitidas=catalogo)
    ]
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=catalogo)
    receipts = [
        json.loads(linha)
        for linha in (base / "candidatos" / "shadow_real_curado_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if linha.strip()
    ]
    for reservados in (anteriores, frozen, receipts):
        auditoria = auditar_leakage_dataset(
            exemplos,
            reservados,
            limiar_similaridade=0.9,
        )
        assert auditoria["aprovado"] is True, auditoria


def test_volume_v2_atende_meta_combinada_sem_vazar_frozen() -> None:
    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS", "LIST_WINDOWS",
    }
    caminhos = [
        base / "dev_v0.jsonl",
        base / "candidatos" / "onda_balanceada_v1.jsonl",
        base / "candidatos" / "musica_natural_modal_v2.jsonl",
        base / "candidatos" / "musica_search_onda_v4.jsonl",
        base / "candidatos" / "volume_piloto_v1.jsonl",
        base / "candidatos" / "volume_onda_v2.jsonl",
    ]
    combinado = [
        item
        for caminho in caminhos
        for item in carregar_jsonl(caminho, intents_permitidas=intents)
    ]
    frozen = carregar_jsonl(
        base / "frozen_v0.jsonl",
        intents_permitidas=intents,
    )
    manifesto = carregar_manifesto_variantes(
        base / "catalogo_variantes_v0.json",
        intents_catalogadas=intents,
    )
    cobertura = analisar_cobertura_dataset(
        combinado,
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
    )

    assert cobertura["por_comando"]["VOLUME:down"]["dev"] == 151
    assert cobertura["por_comando"]["VOLUME:up"]["dev"] == 152
    assert cobertura["por_comando"]["VOLUME:down"]["cotas_coleta_atendidas"] is True
    assert cobertura["por_comando"]["VOLUME:up"]["cotas_coleta_atendidas"] is True
    assert len(cobertura["comandos_abaixo_meta_dev"]) == 15
    assert auditar_leakage_dataset(combinado, frozen)["aprovado"] is True


def test_navegador_v1_atende_quatro_metas_combinadas_sem_vazar_frozen() -> None:
    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS", "LIST_WINDOWS",
    }
    nomes_lotes = (
        "onda_balanceada_v1.jsonl",
        "musica_natural_modal_v2.jsonl",
        "musica_search_onda_v4.jsonl",
        "volume_piloto_v1.jsonl",
        "volume_onda_v2.jsonl",
        "navegador_onda_v1.jsonl",
    )
    combinado = carregar_jsonl(
        base / "dev_v0.jsonl",
        intents_permitidas=intents,
    )
    for nome in nomes_lotes:
        combinado.extend(carregar_jsonl(
            base / "candidatos" / nome,
            intents_permitidas=intents,
        ))
    frozen = carregar_jsonl(
        base / "frozen_v0.jsonl",
        intents_permitidas=intents,
    )
    manifesto = carregar_manifesto_variantes(
        base / "catalogo_variantes_v0.json",
        intents_catalogadas=intents,
    )
    cobertura = analisar_cobertura_dataset(
        combinado,
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
    )

    esperados = {
        "CLOSE_TAB:close": 150,
        "OPEN_URL:open": 150,
        "LIST_TABS:list": 150,
        "SEARCH:search": 151,
    }
    for variante, total in esperados.items():
        assert cobertura["por_comando"][variante]["dev"] == total
        assert cobertura["por_comando"][variante]["cotas_coleta_atendidas"] is True
    assert len(cobertura["comandos_abaixo_meta_dev"]) == 11
    assert auditar_leakage_dataset(combinado, frozen)["aprovado"] is True


def test_catalogo_completo_atende_18_variantes_sem_vazar_frozen() -> None:
    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS", "LIST_WINDOWS",
    }
    nomes_lotes = (
        "onda_balanceada_v1.jsonl",
        "musica_natural_modal_v2.jsonl",
        "musica_search_onda_v4.jsonl",
        "volume_piloto_v1.jsonl",
        "volume_onda_v2.jsonl",
        "navegador_onda_v1.jsonl",
        "apps_arquivos_onda_v1.jsonl",
        "iot_midia_clima_onda_v1.jsonl",
        "list_windows_onda_v1.jsonl",
    )
    combinado = carregar_jsonl(
        base / "dev_v0.jsonl",
        intents_permitidas=intents,
    )
    for nome in nomes_lotes:
        combinado.extend(carregar_jsonl(
            base / "candidatos" / nome,
            intents_permitidas=intents,
        ))
    frozen = carregar_jsonl(
        base / "frozen_v0.jsonl",
        intents_permitidas=intents,
    )
    manifesto = carregar_manifesto_variantes(
        base / "catalogo_variantes_v0.json",
        intents_catalogadas=intents,
    )
    cobertura = analisar_cobertura_dataset(
        combinado,
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
    )

    assert cobertura["totais"]["variantes_comando_declaradas"] == 18
    assert cobertura["comandos_abaixo_meta_dev"] == []
    assert cobertura["todos_comandos_observados_na_meta_dev"] is True
    assert cobertura["todos_comandos_com_cotas_minimas_dev"] is True
    assert cobertura["todos_dominios_com_hard_negatives_minimos_dev"] is True
    assert all(
        150 <= dados["dev"] <= 200
        for dados in cobertura["por_comando"].values()
        if dados["declarada"]
    )
    assert auditar_leakage_dataset(combinado, frozen)["aprovado"] is True


def test_diagnostico_cv_localiza_familia_sem_promover_previsao_a_rotulo() -> None:
    esperados = [
        {
            "text": "ontem eu ouvi lua de neon",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "family": "musica_relato",
            "domain": "music",
        },
        {
            "text": "não toca lua de neon",
            "intent": "MUSIC_SEARCH",
            "is_command": True,
            "negated": True,
            "action": "search",
            "family": "musica_negada",
            "domain": "music",
        },
    ]
    previstos = [
        {
            "intent": "MUSIC_SEARCH",
            "is_command": True,
            "negated": False,
            "params": {"acao": "search"},
        },
        {
            "intent": "MUSIC_SEARCH",
            "is_command": True,
            "negated": False,
            "params": {"acao": "search"},
        },
    ]

    diagnostico = diagnosticar_erros_por_familia(esperados, previstos)

    assert diagnostico["totais_por_tipo"] == {
        "falso_comando": 1,
        "intent_divergente": 1,
        "negacao_perdida": 1,
    }
    assert [item["family"] for item in diagnostico["por_familia"]] == [
        "musica_negada",
        "musica_relato",
    ]
    assert diagnostico["contrato"]["autoriza_execucao"] is False
    assert diagnostico["contrato"]["predicao_vira_label"] is False


def test_diagnostico_cv_ignora_erros_fora_dos_training_heads() -> None:
    esperado = {
        "text": "consulta a previsão amanhã",
        "intent": "WEATHER",
        "is_command": True,
        "negated": False,
        "action": "query",
        "family": "weather_command_only",
        "domain": "weather",
        "training_heads": ["command"],
    }
    previsto = {
        "intent": "NONE",
        "is_command": True,
        "negated": True,
        "params": {"acao": "none"},
    }

    diagnostico = diagnosticar_erros_por_familia([esperado], [previsto])

    assert diagnostico["familias_com_erro"] == 0
    assert diagnostico["totais_por_tipo"] == {}


def test_diagnostico_cv_expoe_primeira_fronteira_do_veto_de_comando() -> None:
    esperado = {
        "text": "arranja um samba para eu ouvir",
        "intent": "MUSIC_SEARCH",
        "is_command": True,
        "negated": False,
        "action": "search",
        "family": "musica_arranjar",
        "domain": "music",
        "training_heads": ["command"],
    }
    previsto = {
        "intent": "MUSIC_SEARCH",
        "gate_intent": "NONE",
        "is_command": False,
        "raw_is_command": True,
        "command_veto_reason": "intent_desconhecida",
        "command_probability": 0.82,
        "command_threshold": 0.75,
        "command_head_scope": "MUSIC_SEARCH",
        "negated": False,
        "params": {},
        "confidence": {"intent_gate": 0.91},
    }

    diagnostico = diagnosticar_erros_por_familia([esperado], [previsto])
    observado = diagnostico["por_familia"][0]["amostras"][0]["previsto"]

    assert observado["gate_intent"] == "NONE"
    assert observado["raw_is_command"] is True
    assert observado["command_veto_reason"] == "intent_desconhecida"
    assert observado["command_probability"] == 0.82
    assert observado["command_threshold"] == 0.75
    assert observado["command_head_scope"] == "MUSIC_SEARCH"
    assert observado["intent_gate_confidence"] == 0.91


def test_diagnostico_intent_gate_compara_vetos_corretos_e_comandos_perdidos() -> None:
    from mente_laylay.neural.validacao_cruzada import (
        diagnosticar_fronteira_intent_gate,
    )

    esperados = [
        {"text": "me informa o tempo", "is_command": True},
        {"text": "a previsão mudou", "is_command": False},
    ]
    previstos = [
        {
            "intent": "WEATHER",
            "gate_intent": "NONE",
            "raw_is_command": True,
            "command_probability": 0.93,
            "command_threshold": 0.725,
            "confidence": {"intent": 0.82, "intent_gate": 0.54},
        },
        {
            "intent": "WEATHER",
            "gate_intent": "NONE",
            "raw_is_command": True,
            "command_probability": 0.98,
            "command_threshold": 0.725,
            "confidence": {"intent": 0.61, "intent_gate": 0.88},
        },
    ]

    diagnostico = diagnosticar_fronteira_intent_gate(esperados, previstos)

    assert diagnostico["totais"] == {
        "candidatos": 2,
        "comandos_esperados": 1,
        "nao_comandos_esperados": 1,
    }
    assert diagnostico["candidatos"][0]["intent_gate_confidence"] == 0.54
    assert diagnostico["candidatos"][0]["intent_confidence"] == 0.82
    assert diagnostico["contrato"]["autoriza_execucao"] is False


def test_previsao_neural_e_observacao_sem_autoridade() -> None:
    previsao = normalizar_previsao_neural(
        _ModeloFalso.prever("dá uma diminuída no volume"),
        texto="dá uma diminuída no volume",
        modelo="teste-v0",
        intents_permitidas={"VOLUME", "APP_OPEN"},
    )

    assert previsao["intent"] == "VOLUME"
    assert previsao["params"] == {"acao": "down"}
    assert previsao["is_command"] is True
    assert previsao["negated"] is False
    assert previsao["somente_observacao"] is True
    assert previsao["autoriza_execucao"] is False


def test_ood_semantico_nao_calibrado_permanece_visivel_e_fail_closed() -> None:
    bruto = {
        **_ModeloFalso.prever("dá uma diminuída no volume"),
        "ood": True,
        "ood_calibrated": False,
    }
    previsao = normalizar_previsao_neural(
        bruto,
        texto="dá uma diminuída no volume",
        modelo="semantico-experimental",
        intents_permitidas={"VOLUME"},
    )

    assert previsao["ood"] is True
    assert previsao["ood_calibrated"] is False
    decisao = avaliar_roteamento_neural(
        previsao=previsao,
        turno_legado={"veto_execucao_operacional": False},
        execucao_habilitada=True,
        intents_habilitadas={"VOLUME"},
        riscos_habilitados={"LOW_RISK"},
        risco_intent={"VOLUME": "LOW_RISK"},
        thresholds={"VOLUME": 0.5},
    )
    assert decisao["permitido"] is False
    assert decisao["motivo"] == "ood_nao_calibrado"


def test_calibracao_ood_exige_separacao_no_holdout_sem_forcar_limiar() -> None:
    exemplos_id = [
        {"intent": "VOLUME", "action": "down", "is_command": True, "negated": False},
        {"intent": "APP_OPEN", "action": "open", "is_command": True, "negated": False},
    ]

    def previsao(intent: str, acao: str, confianca: float) -> dict:
        return {
            "intent": intent,
            "params": {"acao": acao},
            "is_command": True,
            "negated": False,
            "confidence": {"intent": confianca},
        }

    aprovado = calibrar_limiar_ood(
        exemplos_id,
        [previsao("VOLUME", "down", 0.9), previsao("APP_OPEN", "open", 0.8)],
        [previsao("VOLUME", "down", 0.2), previsao("APP_OPEN", "open", 0.3)],
        [previsao("VOLUME", "down", 0.25), previsao("APP_OPEN", "open", 0.35)],
        alvo_falso_aceite_ood=0.0,
        recall_id_minimo=1.0,
    )
    impossivel = calibrar_limiar_ood(
        exemplos_id,
        [previsao("VOLUME", "down", 0.9), previsao("APP_OPEN", "open", 0.8)],
        [previsao("VOLUME", "down", 0.95)],
        [previsao("VOLUME", "down", 0.96)],
        alvo_falso_aceite_ood=0.0,
        recall_id_minimo=0.5,
    )

    assert aprovado["aprovado"] is True
    assert aprovado["limiar_recomendado"] == 0.8
    assert aprovado["avaliacao_holdout"]["ood_aceitos"] == 0
    assert impossivel["aprovado"] is False
    assert impossivel["limiar_recomendado"] is None
    assert impossivel["motivo"] == "limiar_unico_nao_separa_id_de_ood"
    assert impossivel["melhor_sob_alvo_ood_calibracao"][
        "ood_false_accept_rate"
    ] == 0.0
    assert impossivel["melhor_sob_recall_id_calibracao"][
        "id_recall_operacional"
    ] >= 0.5


def test_detector_ood_calibra_probabilidade_e_confirma_holdout() -> None:
    exemplos_id = [
        {"is_command": True, "negated": False},
        {"is_command": True, "negated": False},
        {"is_command": False, "negated": False},
    ]
    relatorio = calibrar_detector_ood(
        exemplos_id,
        [0.1, 0.2, 0.15],
        [0.8, 0.9],
        [0.85, 0.95],
        alvo_falso_aceite_ood=0.0,
        retencao_comandos_id_minima=1.0,
    )

    assert relatorio["aprovado"] is True
    assert relatorio["limiar_recomendado"] == 0.8
    assert relatorio["avaliacao_holdout"]["ood_false_accept_rate"] == 0.0
    assert relatorio["melhor_sob_alvo_ood_calibracao"][
        "id_command_retention_rate"
    ] == 1.0


def test_detector_ood_semantico_mantem_grupos_id_fora_do_fold() -> None:
    exemplos_id = [
        {"is_command": True, "negated": False},
        {"is_command": False, "negated": False},
        {"is_command": True, "negated": False},
        {"is_command": False, "negated": False},
    ]
    vetores_id = np.asarray(
        [[0.0, 0.0], [0.1, 0.0], [0.0, 0.1], [0.1, 0.1]],
        dtype=np.float32,
    )
    exemplos_ood = [
        {"partition": "training", "family": "ood_treino"},
        {"partition": "calibration", "family": "ood_calibracao"},
        {"partition": "evaluation", "family": "ood_avaliacao"},
    ]
    vetores_ood = np.asarray(
        [[4.0, 4.0], [4.2, 4.0], [4.0, 4.2]],
        dtype=np.float32,
    )
    relatorio = avaliar_detector_ood_semantico(
        exemplos_id,
        vetores_id,
        ["grupo_a", "grupo_a", "grupo_b", "grupo_b"],
        exemplos_ood,
        vetores_ood,
        n_splits=2,
        alvo_falso_aceite_ood=0.0,
        retencao_comandos_id_minima=0.5,
    )

    assert relatorio["totais"]["folds"] == 2
    assert all(not fold["grupos_compartilhados"] for fold in relatorio["folds"])
    assert relatorio["contrato"]["ood_treina_intent_ou_acao"] is False


def test_detector_ood_rejeita_familia_compartilhada_entre_particoes() -> None:
    with pytest.raises(ValueError, match="famílias OOD não podem"):
        avaliar_detector_ood_semantico(
            [
                {"is_command": True, "negated": False},
                {"is_command": True, "negated": False},
            ],
            np.asarray([[0.0], [0.1]], dtype=np.float32),
            ["id_a", "id_b"],
            [
                {"partition": "training", "family": "ood_mesma"},
                {"partition": "calibration", "family": "ood_mesma"},
                {"partition": "evaluation", "family": "ood_outra"},
            ],
            np.asarray([[1.0], [1.1], [1.2]], dtype=np.float32),
            n_splits=2,
        )


def test_detector_ood_por_prototipos_nao_treina_com_ood() -> None:
    exemplos_id = [
        {"intent": "VOLUME", "action": "down", "is_command": True, "negated": False},
        {"intent": "APP_OPEN", "action": "open", "is_command": True, "negated": False},
        {"intent": "VOLUME", "action": "down", "is_command": True, "negated": False},
        {"intent": "APP_OPEN", "action": "open", "is_command": True, "negated": False},
    ]
    vetores_id = np.asarray(
        [[1.0, 0.0], [0.0, 1.0], [0.9, 0.1], [0.1, 0.9]],
        dtype=np.float32,
    )
    exemplos_ood = [
        {"partition": "calibration", "family": "ood_calibracao"},
        {"partition": "evaluation", "family": "ood_avaliacao"},
    ]
    vetores_ood = np.asarray([[-1.0, -1.0], [-0.9, -1.0]], dtype=np.float32)
    relatorio = avaliar_detector_ood_prototipos(
        exemplos_id,
        vetores_id,
        ["grupo_a", "grupo_a", "grupo_b", "grupo_b"],
        exemplos_ood,
        vetores_ood,
        n_splits=2,
        alvo_falso_aceite_ood=0.0,
        retencao_comandos_id_minima=0.5,
    )

    assert relatorio["contrato"]["ood_treina_detector"] is False
    assert all(not fold["grupos_compartilhados"] for fold in relatorio["folds"])


def test_dataset_ood_e_isolado_do_treino_e_tem_holdout(tmp_path) -> None:
    exemplos = gerar_exemplos_ood_v0()
    resumo = validar_lote_ood_v0(exemplos)
    caminho = tmp_path / "ood.jsonl"
    caminho.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in exemplos),
        encoding="utf-8",
    )
    carregados = carregar_dataset_ood(caminho)

    assert resumo == {
        "total": 200,
        "familias": 20,
        "calibration": 100,
        "evaluation": 100,
        "max_exemplos_por_familia": 10,
    }
    assert len(carregados) == 200
    assert {item["partition"] for item in carregados} == {
        "calibration",
        "evaluation",
    }
    assert all(item["expected_ood"] is True for item in carregados)


def test_dataset_detector_ood_v1_preserva_particoes_mas_nao_familias(
    tmp_path,
) -> None:
    exemplos = gerar_exemplos_ood_detector_v1()
    resumo = validar_lote_ood_detector_v1(exemplos)
    caminho = tmp_path / "ood_detector.jsonl"
    caminho.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in exemplos),
        encoding="utf-8",
    )

    carregados = carregar_dataset_ood(caminho)

    assert resumo == {
        "total": 300,
        "familias": 20,
        "training": 100,
        "calibration": 100,
        "evaluation": 100,
        "max_exemplos_por_familia": 15,
    }
    assert len(carregados) == 300
    assert {item["partition"] for item in carregados} == {
        "training",
        "calibration",
        "evaluation",
    }
    familias = {
        particao: {
            item["family"] for item in carregados if item["partition"] == particao
        }
        for particao in ("training", "calibration", "evaluation")
    }
    assert familias["training"] & familias["calibration"]


def test_dataset_detector_ood_v2_isola_familias_entre_particoes(tmp_path) -> None:
    exemplos = gerar_exemplos_ood_detector_v2()
    resumo = validar_lote_ood_detector_v2(exemplos)
    caminho = tmp_path / "ood_detector_v2.jsonl"
    caminho.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in exemplos),
        encoding="utf-8",
    )
    carregados = carregar_dataset_ood(caminho)
    familias = {
        particao: {
            item["family"] for item in carregados if item["partition"] == particao
        }
        for particao in ("training", "calibration", "evaluation")
    }

    assert resumo["total"] == 300
    assert resumo["familias"] == 30
    assert not (familias["training"] & familias["calibration"])
    assert not (familias["training"] & familias["evaluation"])
    assert not (familias["calibration"] & familias["evaluation"])


def test_shadow_nao_transforma_ood_nao_calibrado_em_comando_perdido(
    tmp_path,
) -> None:
    relatorio = RelatorioShadowNeural(tmp_path)
    comparacao = relatorio.registrar_turno(
        texto="abaixa o volume",
        previsao={
            "modelo": "semantico-experimental",
            "intent": "VOLUME",
            "params": {"acao": "down"},
            "is_command": True,
            "negated": False,
            "ood": True,
            "ood_calibrated": False,
            "confidence": {"intent": 0.8},
        },
        turno={
            "autoriza_execucao": True,
            "veto_execucao_operacional": False,
        },
    )

    evento = json.loads(
        (tmp_path / "shadow_eventos.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert comparacao["status"] == "concordancia_comando"
    assert evento["neural"]["ood"] is True
    assert evento["neural"]["ood_calibrated"] is False


def test_receipt_confirmado_e_evidencia_util_mas_nao_ground_truth_isolado(tmp_path) -> None:
    buffer = BufferExperienciasNeurais(tmp_path / "experiencias.jsonl")
    experiencia = buffer.registrar_resultado(
        texto="dá uma diminuída no volume",
        previsao=_ModeloFalso.prever("dá uma diminuída no volume"),
        resultado={
            "intent": "VOLUME",
            "params": {"acao": "down"},
            "status": "volume_ajustado",
            "executou": True,
            "confirmado": True,
        },
        executou=True,
        confirmado=True,
        origem="executor",
    )

    assert experiencia["evidencia"] == "EXPECTED_RECEIPT_VERIFIED"
    assert experiencia["label_confidence"] < 0.7
    assert experiencia["apto_treino"] is False
    assert experiencia["predicao_propria_vira_label"] is False


def test_correcao_confirmada_vira_exemplo_forte_sem_apagar_o_erro(tmp_path) -> None:
    caminho = tmp_path / "experiencias.jsonl"
    buffer = BufferExperienciasNeurais(caminho)
    experiencia = buffer.registrar_correcao(
        texto_original="fecha o chrome",
        intent_errada="CLOSE_TAB",
        intent_correta="CLOSE_APP",
        params_corretos={"nome_app": "chrome"},
        texto_correcao="não, eu pedi para fechar o programa",
        confirmada_por_execucao=True,
    )

    assert experiencia["evidencia"] == "EXPLICIT_CORRECTION"
    assert experiencia["label_confidence"] == 1.0
    assert experiencia["apto_treino"] is True
    assert experiencia["intent_errada"] == "CLOSE_TAB"
    assert experiencia["intent_correta"] == "CLOSE_APP"
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert json.loads(linhas[-1])["intent_correta"] == "CLOSE_APP"


def test_shadow_publica_previsao_sem_mutar_turno_legado(tmp_path) -> None:
    publicadas: list[dict] = []
    turno = {
        "modalidade": "conversa",
        "modalidade_geral": "conversa",
        "autoriza_execucao": False,
        "veto_execucao_operacional": False,
    }
    antes = dict(turno)
    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloFalso(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=publicadas.append,
        modo="shadow",
        intents_permitidas={"VOLUME"},
        log=lambda *_args: None,
    )

    previsao = runtime.observar("dá uma diminuída no volume", turno_legado=turno)

    assert turno == antes
    assert previsao["route"] == "SHADOW"
    assert previsao["latency_ms"] >= 0.0
    assert previsao["comparacao_legado"]["divergiu_comando"] is True
    assert publicadas == [previsao]


def test_composicao_real_anexa_sombra_sem_mudar_autorizacao(tmp_path) -> None:
    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloFalso(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"VOLUME"},
        log=lambda *_args: None,
    )
    turno = {
        "modalidade": "conversa",
        "autoriza_execucao": False,
        "veto_execucao_operacional": False,
    }

    observado = observar_especialista_neural_turno(
        {"_especialista_neural_comandos_runtime": runtime},
        "isso tá alto, dá uma baixada",
        turno,
    )
    finalizado = finalizar_especialista_neural_turno(
        {"_especialista_neural_comandos_runtime": runtime},
        "isso tá alto, dá uma baixada",
        observado,
    )

    assert "_especialista_neural_comandos_runtime" in DEPENDENCIAS_ORQUESTRACAO_TURNO
    assert turno == {
        "modalidade": "conversa",
        "autoriza_execucao": False,
        "veto_execucao_operacional": False,
    }
    assert observado["autoriza_execucao"] is False
    assert observado["previsao_neural"]["intent"] == "VOLUME"
    assert observado["previsao_neural"]["autoriza_execucao"] is False
    assert finalizado["previsao_neural"]["comparacao_canonica"]["status"] == (
        "falso_comando_neural"
    )
    assert (tmp_path / "shadow_relatorio.json").exists()


def test_shadow_multiacao_reusa_segmentos_canonicos_sem_criar_outro_roteador(
    tmp_path,
) -> None:
    class _ModeloPorSegmento:
        versao = "teste-segmentos-v27"

        def __init__(self) -> None:
            self.chamadas: list[str] = []

        def prever(self, texto: str) -> dict:
            self.chamadas.append(texto)
            if texto == "abre o opera":
                return {
                    "intent": "APP_OPEN",
                    "params": {"acao": "open"},
                    "is_command": True,
                    "negated": False,
                    "confidence": {"intent": 0.9, "command": 0.9},
                }
            return {
                "intent": "VOLUME",
                "params": {"acao": "down"},
                "is_command": True,
                "negated": False,
                "confidence": {"intent": 0.9, "command": 0.9},
            }

    modelo = _ModeloPorSegmento()
    runtime = EspecialistaNeuralComandosRuntime(
        modelo=modelo,
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"APP_OPEN", "VOLUME"},
        log=lambda *_args: None,
    )
    turno = {
        "modalidade": "comando",
        "modalidade_geral": "comando",
        "autoriza_execucao": True,
        "veto_execucao_operacional": False,
        "segmentos": [
            {
                "indice": 0,
                "texto": "abre o opera",
                "modalidade": "comando",
                "autoriza_execucao": True,
                "veto_execucao_operacional": False,
            },
            {
                "indice": 1,
                "texto": "abaixa o volume",
                "modalidade": "comando",
                "autoriza_execucao": True,
                "veto_execucao_operacional": False,
            },
        ],
    }
    turno_antes = json.loads(json.dumps(turno))

    previsao = runtime.observar(
        "abre o opera e abaixa o volume",
        turno_legado=turno,
    )

    assert modelo.chamadas == ["abre o opera", "abaixa o volume"]
    assert [
        item["intent"] for item in previsao["previsoes_segmentos"]
    ] == ["APP_OPEN", "VOLUME"]
    assert previsao["multi_segmento"] is True
    assert previsao["is_command"] is True
    assert previsao["intent"] == "APP_OPEN"
    assert previsao["autoriza_execucao"] is False
    assert all(
        item["autoriza_execucao"] is False
        for item in previsao["previsoes_segmentos"]
    )
    assert turno == turno_antes


def test_shadow_expoe_erro_por_segmento_escondido_pelo_acerto_do_turno(
    tmp_path,
) -> None:
    class _ModeloComPerdaNoSegundoSegmento:
        versao = "teste-segmentos-v27"

        @staticmethod
        def prever(texto: str) -> dict:
            comando = texto == "abre o opera"
            return {
                "intent": "APP_OPEN" if comando else "VOLUME",
                "params": {"acao": "open" if comando else "down"},
                "is_command": comando,
                "negated": False,
                "confidence": {"intent": 0.9, "command": 0.9},
            }

    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloComPerdaNoSegundoSegmento(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"APP_OPEN", "VOLUME"},
        log=lambda *_args: None,
    )
    texto = "abre o opera e abaixa o volume"
    turno = {
        "modalidade": "comando",
        "modalidade_geral": "comando",
        "autoriza_execucao": True,
        "veto_execucao_operacional": False,
        "segmentos": [
            {
                "indice": 0,
                "texto": "abre o opera",
                "modalidade": "comando",
                "autoriza_execucao": True,
                "veto_execucao_operacional": False,
            },
            {
                "indice": 1,
                "texto": "abaixa o volume",
                "modalidade": "comando",
                "autoriza_execucao": True,
                "veto_execucao_operacional": False,
            },
        ],
    }

    runtime.observar(texto, turno_legado=turno)
    runtime.finalizar_observacao_turno(texto, turno)

    evento = json.loads(
        (tmp_path / "shadow_eventos.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()[-1]
    )
    relatorio = json.loads(
        (tmp_path / "shadow_relatorio.json").read_text(encoding="utf-8")
    )
    assert evento["comparacao"]["status"] == "concordancia_comando"
    assert evento["comparacao"]["segmentos_total"] == 2
    assert evento["comparacao"]["segmentos_comparaveis"] == 2
    assert evento["comparacao"]["divergencias_comando_segmento"] == 1
    assert evento["comparacao"]["comandos_perdidos_neurais_segmento"] == 1
    assert evento["texto"] == texto
    assert len(evento["neural"]["segmentos"]) == 2
    assert all(
        "texto" not in item for item in evento["neural"]["segmentos"]
    )
    assert relatorio["totais"]["segmentos_comparaveis"] == 2
    assert relatorio["totais"]["concordancias_comando_segmento"] == 1
    assert relatorio["totais"]["divergencias_comando_segmento"] == 1


def test_receipt_multiacao_sem_correlacao_de_segmento_nao_inventa_divergencia(
    tmp_path,
) -> None:
    class _ModeloPorSegmento:
        versao = "teste-segmentos-v27"

        @staticmethod
        def prever(texto: str) -> dict:
            abre = texto == "abre o opera"
            return {
                "intent": "APP_OPEN" if abre else "VOLUME",
                "params": {"acao": "open" if abre else "down"},
                "is_command": True,
                "negated": False,
                "confidence": {"intent": 0.9, "command": 0.9},
            }

    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloPorSegmento(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"APP_OPEN", "VOLUME"},
        log=lambda *_args: None,
    )
    texto = "abre o opera e abaixa o volume"
    turno = {
        "autoriza_execucao": True,
        "segmentos": [
            {
                "indice": 0,
                "texto": "abre o opera",
                "modalidade": "comando",
                "autoriza_execucao": True,
            },
            {
                "indice": 1,
                "texto": "abaixa o volume",
                "modalidade": "comando",
                "autoriza_execucao": True,
            },
        ],
    }
    runtime.observar(texto, turno_legado=turno)
    runtime.finalizar_observacao_turno(texto, turno)

    runtime.observar_resultado(
        {
            "intent": "VOLUME",
            "params": {"acao": "down"},
            "status": "volume_ajustado",
            "confirmado": True,
        },
        texto,
        True,
        origem="executor",
    )

    evento = json.loads(
        (tmp_path / "shadow_eventos.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()[-1]
    )
    relatorio = json.loads(
        (tmp_path / "shadow_relatorio.json").read_text(encoding="utf-8")
    )
    assert evento["comparacao"]["status"] == (
        "receipt_multi_segmento_nao_correlacionado"
    )
    assert evento["comparacao"]["receipt_confirmado"] is True
    assert evento["comparacao"]["intent_comparavel"] is False
    assert evento["comparacao"]["divergiu_receipt"] is False
    assert relatorio["totais"]["receipts_confirmados"] == 1
    assert relatorio["totais"]["concordancias_intent"] == 0
    assert relatorio["totais"]["divergencias_intent"] == 0


def test_shadow_final_registra_falso_comando_sem_criar_autoridade(tmp_path) -> None:
    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloFalso(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"VOLUME"},
        log=lambda *_args: None,
    )
    texto = "isso tá alto, mas não mexe no volume"
    runtime.observar(texto, turno_legado={"autoriza_execucao": False})

    previsao = runtime.finalizar_observacao_turno(
        texto,
        {
            "modalidade": "recusa",
            "modalidade_geral": "recusa",
            "autoriza_execucao": False,
            "veto_execucao_operacional": True,
            "origem_veto_execucao_operacional": "negacao_explicita",
        },
    )

    eventos = [
        json.loads(linha)
        for linha in (tmp_path / "shadow_eventos.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    relatorio = json.loads(
        (tmp_path / "shadow_relatorio.json").read_text(encoding="utf-8")
    )
    assert previsao["autoriza_execucao"] is False
    assert previsao["comparacao_canonica"]["status"] == "falso_comando_neural"
    assert eventos[0]["tipo"] == "comparacao_turno"
    assert eventos[0]["texto"] == texto
    assert eventos[0]["apto_treino"] is False
    assert eventos[0]["predicao_propria_vira_label"] is False
    assert eventos[0]["comparacao"]["falso_comando_neural"] is True
    assert relatorio["totais"]["turnos"] == 1
    assert relatorio["totais"]["divergencias_comando"] == 1
    assert relatorio["totais"]["falsos_comandos_neurais"] == 1
    assert relatorio["taxas"]["divergencia_comando"] == 1.0


def test_shadow_receipt_compara_intent_e_acao_sem_reter_texto_quando_concorda(
    tmp_path,
) -> None:
    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloFalso(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"VOLUME"},
        log=lambda *_args: None,
    )
    texto = "dá uma diminuída no volume"
    runtime.observar(texto, turno_legado={"autoriza_execucao": True})
    runtime.finalizar_observacao_turno(
        texto,
        {
            "modalidade": "comando",
            "modalidade_geral": "comando",
            "autoriza_execucao": True,
            "veto_execucao_operacional": False,
        },
    )

    experiencia = runtime.observar_resultado(
        {
            "intent": "VOLUME",
            "params": {"acao": "down"},
            "status": "volume_ajustado",
            "confirmado": True,
        },
        texto,
        True,
        origem="executor",
    )

    eventos = [
        json.loads(linha)
        for linha in (tmp_path / "shadow_eventos.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    relatorio = json.loads(
        (tmp_path / "shadow_relatorio.json").read_text(encoding="utf-8")
    )
    assert experiencia["apto_treino"] is False
    assert [item["tipo"] for item in eventos] == [
        "comparacao_turno",
        "comparacao_receipt",
    ]
    assert all("texto" not in item for item in eventos)
    assert eventos[1]["comparacao"]["intent_igual"] is True
    assert eventos[1]["comparacao"]["acao_igual"] is True
    assert relatorio["totais"]["concordancias_comando"] == 1
    assert relatorio["totais"]["receipts_confirmados"] == 1
    assert relatorio["totais"]["concordancias_intent"] == 1
    assert relatorio["totais"]["concordancias_acao"] == 1
    assert relatorio["taxas"]["concordancia_intent_confirmado"] == 1.0


def test_shadow_receipt_sem_acao_canonica_nao_inventa_divergencia_de_acao(
    tmp_path,
) -> None:
    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloFalso(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"VOLUME"},
        log=lambda *_args: None,
    )
    texto = "dá uma diminuída no volume"
    runtime.observar(texto, turno_legado={"autoriza_execucao": True})
    runtime.finalizar_observacao_turno(
        texto,
        {
            "modalidade": "comando",
            "autoriza_execucao": True,
            "veto_execucao_operacional": False,
        },
    )

    runtime.observar_resultado(
        {
            "intent": "VOLUME",
            "params": {},
            "status": "volume_ajustado",
            "confirmado": True,
        },
        texto,
        True,
        origem="executor",
    )

    eventos = [
        json.loads(linha)
        for linha in (tmp_path / "shadow_eventos.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    comparacao = eventos[-1]["comparacao"]
    relatorio = json.loads(
        (tmp_path / "shadow_relatorio.json").read_text(encoding="utf-8")
    )
    assert comparacao["receipt_confirmado"] is True
    assert comparacao["intent_igual"] is True
    assert comparacao["acao_comparavel"] is False
    assert comparacao["acao_igual"] is False
    assert comparacao["divergiu_receipt"] is False
    assert comparacao["status"] == "concordancia_receipt"
    assert relatorio["totais"]["concordancias_intent"] == 1
    assert relatorio["totais"]["concordancias_acao"] == 0
    assert relatorio["totais"]["divergencias_acao"] == 0


def test_shadow_distingue_comando_perdido_e_receipt_divergente(tmp_path) -> None:
    class _ModeloNaoComando:
        versao = "teste-nao-comando"

        @staticmethod
        def prever(_texto: str) -> dict:
            return {
                "intent": "VOLUME",
                "params": {"acao": "down"},
                "is_command": False,
                "negated": False,
                "ood": False,
                "confidence": {
                    "intent": 0.7,
                    "command": 0.8,
                    "negation": 0.9,
                    "action": 0.7,
                },
            }

    runtime = EspecialistaNeuralComandosRuntime(
        modelo=_ModeloNaoComando(),
        buffer=BufferExperienciasNeurais(tmp_path / "experiencias.jsonl"),
        publicar=None,
        modo="shadow",
        intents_permitidas={"VOLUME", "CLOSE_APP"},
        log=lambda *_args: None,
    )
    texto = "fecha o chrome"
    runtime.observar(texto, turno_legado={"autoriza_execucao": True})
    previsao = runtime.finalizar_observacao_turno(
        texto,
        {
            "modalidade": "comando",
            "autoriza_execucao": True,
            "veto_execucao_operacional": False,
        },
    )
    runtime.observar_resultado(
        {
            "intent": "CLOSE_APP",
            "params": {"acao": "close"},
            "status": "aplicativo_fechado",
            "confirmado": True,
        },
        texto,
        True,
        origem="executor",
    )

    relatorio = json.loads(
        (tmp_path / "shadow_relatorio.json").read_text(encoding="utf-8")
    )
    assert previsao["comparacao_canonica"]["status"] == "comando_perdido_neural"
    assert relatorio["totais"]["comandos_perdidos_neurais"] == 1
    assert relatorio["totais"]["divergencias_intent"] == 1
    assert relatorio["totais"]["divergencias_acao"] == 1
    assert len(relatorio["divergencias_recentes"]) == 2
    assert all(
        item["texto"] == texto for item in relatorio["divergencias_recentes"]
    )


def test_receipt_e_correcao_confirmada_chegam_ao_especialista_sem_tomar_executor() -> None:
    class _Estado:
        def __init__(self) -> None:
            self.mental = {
                "ultima_entrada": "fecha o chrome",
                "plano_turno_atual": {
                    "fase": "executado",
                    "texto_usuario": "fecha o chrome",
                    "comandos": [],
                    "erros": [],
                },
                "correcao_interpretacao_pendente": {
                    "status": "aguardando_interpretacao_correta",
                },
            }

        def atualizar_campos(self, dominio: str, **campos) -> None:
            assert dominio == "mental"
            self.mental.update(campos)

    class _Neural:
        def __init__(self) -> None:
            self.resultados: list[tuple] = []
            self.correcoes: list[dict] = []

        def observar_resultado(self, *args, **kwargs) -> None:
            self.resultados.append((args, kwargs))

        def observar_correcao(self, correcao) -> None:
            self.correcoes.append(dict(correcao))

    estado = _Estado()
    neural = _Neural()

    def atualizar_plano(plano, *, fase, comandos, erros=(), fala=""):
        novo = dict(plano)
        novo.update(fase=fase, comandos=list(comandos), erros=list(erros), fala_planejada=fala)
        return novo

    ns = {
        "_especialista_neural_comandos_runtime": neural,
        "_estado_compartilhado_runtime": estado,
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_atualizar_plano_turno_mente": atualizar_plano,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {
            "status": "confirmada_por_execucao",
            "texto_original": "fecha o chrome",
            "intent_errada": "CLOSE_TAB",
            "intent_correta": "CLOSE_APP",
        },
        "print": lambda *_args: None,
    }
    adaptador = AdaptadoresAplicacaoRuntime(lambda: ns)

    adaptador.registrar_resultado_execucao(
        {
            "intent": "CLOSE_APP",
            "params": {"nome_app": "chrome", "acao": "close"},
            "status": "aplicativo_fechado",
            "executou": True,
            "confirmado": True,
            "origem": "executor",
        },
        "fecha o chrome",
        True,
        origem="executor",
    )

    assert len(neural.resultados) == 1
    assert neural.resultados[0][0][0]["intent"] == "CLOSE_APP"
    assert len(neural.correcoes) == 1
    assert neural.correcoes[0]["intent_errada"] == "CLOSE_TAB"
    assert neural.correcoes[0]["params_corretos"] == {
        "nome_app": "chrome",
        "acao": "close",
    }


def test_execucao_posterior_descarta_correcao_sem_criar_label_neural() -> None:
    class _Estado:
        def __init__(self) -> None:
            self.mental = {
                "ultima_entrada": "Nanda é minha amiga.",
                "plano_turno_atual": {
                    "fase": "executado",
                    "texto_usuario": "Nanda é minha amiga.",
                    "comandos": [],
                    "erros": [],
                },
                "correcao_interpretacao_pendente": {
                    "status": "aguardando_interpretacao_correta",
                    "texto_original": "Do que eu gosto?",
                    "texto_correcao": (
                        "Na verdade, não considere jazz como algo que eu gosto."
                    ),
                    "intent_errada": "LEARNING_QUERY",
                },
            }

        def atualizar_campos(self, dominio: str, **campos) -> None:
            assert dominio == "mental"
            self.mental.update(campos)

    class _Neural:
        def __init__(self) -> None:
            self.resultados: list[tuple] = []
            self.correcoes: list[dict] = []

        def observar_resultado(self, *args, **kwargs) -> None:
            self.resultados.append((args, kwargs))

        def observar_correcao(self, correcao) -> None:
            self.correcoes.append(dict(correcao))

    estado = _Estado()
    neural = _Neural()

    def atualizar_plano(plano, *, fase, comandos, erros=(), fala=""):
        novo = dict(plano)
        novo.update(
            fase=fase,
            comandos=list(comandos),
            erros=list(erros),
            fala_planejada=fala,
        )
        return novo

    ns = {
        "_especialista_neural_comandos_runtime": neural,
        "_estado_compartilhado_runtime": estado,
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_atualizar_plano_turno_mente": atualizar_plano,
        "_concluir_correcao_interpretacao_mente": concluir_correcao_interpretacao,
        "print": lambda *_args: None,
    }
    adaptador = AdaptadoresAplicacaoRuntime(lambda: ns)

    adaptador.registrar_resultado_execucao(
        {
            "intent": "PEOPLE_REMEMBER",
            "params": {"alvo": "Nanda"},
            "status": "pessoa_registrada",
            "executou": True,
            "confirmado": True,
            "origem": "executor",
        },
        "Nanda é minha amiga.",
        True,
        origem="executor",
    )

    assert len(neural.resultados) == 1
    assert neural.correcoes == []
    assert estado.mental["correcao_interpretacao_pendente"] == {}


def test_gate_generico_exige_evidencia_risco_e_flag_sem_conceder_por_confianca() -> None:
    previsao = normalizar_previsao_neural(
        _ModeloFalso.prever("dá uma diminuída no volume"),
        texto="dá uma diminuída no volume",
        modelo="teste-v0",
        intents_permitidas={"VOLUME"},
    )
    base = {
        "previsao": previsao,
        "turno_legado": {"veto_execucao_operacional": False},
        "intents_habilitadas": {"VOLUME"},
        "riscos_habilitados": {"LOW_RISK"},
        "risco_intent": {"VOLUME": "LOW_RISK"},
        "thresholds": {"VOLUME": 0.9},
    }

    assert avaliar_roteamento_neural(**base, execucao_habilitada=False)["permitido"] is False
    permitido = avaliar_roteamento_neural(**base, execucao_habilitada=True)
    assert permitido["permitido"] is True
    assert permitido["intent"] == "VOLUME"

    negada = dict(previsao, negated=True)
    assert avaliar_roteamento_neural(
        **{**base, "previsao": negada}, execucao_habilitada=True,
    )["permitido"] is False

    destrutiva = dict(previsao, intent="DELETE_ITEM")
    assert avaliar_roteamento_neural(
        **{
            **base,
            "previsao": destrutiva,
            "intents_habilitadas": {"DELETE_ITEM"},
            "risco_intent": {"DELETE_ITEM": "DESTRUCTIVE"},
        },
        execucao_habilitada=True,
    )["permitido"] is False


def test_dataset_valida_catalogo_e_separa_familias_sem_leakage() -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True,
         "negated": False, "action": "down", "family": "volume_direto", "source": "NORMAL_COMMAND", "domain": "audio"},
        {"text": "reduz um pouco o som", "intent": "VOLUME", "is_command": True,
         "negated": False, "action": "down", "family": "volume_indireto", "source": "MANUAL_PARAPHRASE", "domain": "audio"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False,
         "negated": False, "action": "none", "family": "volume_comentario", "source": "HARD_NEGATIVE", "domain": "audio"},
        {"text": "abre o chrome", "intent": "APP_OPEN", "is_command": True,
         "negated": False, "action": "open", "family": "app_direto", "source": "NORMAL_COMMAND", "domain": "app"},
    ]
    validados = [validar_exemplo(item, intents_permitidas={"VOLUME", "APP_OPEN"}) for item in exemplos]
    dev, frozen = separar_dataset_por_familia(
        validados,
        familias_frozen={"volume_indireto", "volume_comentario"},
    )

    assert {item["family"] for item in dev} == {"volume_direto", "app_direto"}
    assert {item["family"] for item in frozen} == {"volume_indireto", "volume_comentario"}


def test_dataset_preserva_grupo_semantico_apenas_quando_declarado() -> None:
    base = {
        "text": "pode diminuir o volume",
        "intent": "VOLUME",
        "is_command": True,
        "negated": False,
        "action": "down",
        "family": "volume_modal_a",
        "source": "MANUAL_PARAPHRASE",
        "domain": "audio",
    }

    sem_grupo = validar_exemplo(base, intents_permitidas={"VOLUME"})
    com_grupo = validar_exemplo(
        {**base, "validation_group": "Volume Modal"},
        intents_permitidas={"VOLUME"},
    )

    assert "validation_group" not in sem_grupo
    assert com_grupo["validation_group"] == "volume modal"


def test_dataset_preserva_e_valida_eixo_de_entidade_separado() -> None:
    base = {
        "text": "o editor está aberto",
        "intent": "LIST_WINDOWS",
        "is_command": True,
        "negated": False,
        "action": "list",
        "family": "consulta_estado",
        "validation_group": "mecanismo_esta_aberto",
        "source": "MANUAL_PARAPHRASE",
        "domain": "app",
    }

    validado = validar_exemplo(
        {**base, "validation_entity_group": "Aplicativo Editor"},
        intents_permitidas={"LIST_WINDOWS"},
    )

    assert validado["validation_group"] == "mecanismo_esta_aberto"
    assert validado["validation_entity_group"] == "aplicativo editor"
    with pytest.raises(ValueError, match="validation_entity_group"):
        validar_exemplo(
            {**base, "validation_entity_group": "   "},
            intents_permitidas={"LIST_WINDOWS"},
        )


def test_dataset_preserva_escopo_explicito_da_extensao() -> None:
    base = {
        "text": "o editor está aberto",
        "intent": "LIST_WINDOWS",
        "is_command": True,
        "negated": False,
        "action": "list",
        "family": "consulta_estado",
        "source": "MANUAL_PARAPHRASE",
        "domain": "app",
    }

    validado = validar_exemplo(
        {**base, "extension_scope": "Estado Alvo"},
        intents_permitidas={"LIST_WINDOWS"},
    )

    assert validado["extension_scope"] == "estado alvo"
    with pytest.raises(ValueError, match="extension_scope"):
        validar_exemplo(
            {**base, "extension_scope": "  "},
            intents_permitidas={"LIST_WINDOWS"},
        )


def test_dataset_preserva_fatores_booleanos_da_extensao() -> None:
    base = {
        "text": "o editor está aberto?",
        "intent": "LIST_WINDOWS",
        "is_command": True,
        "negated": False,
        "action": "list",
        "family": "consulta_estado",
        "source": "MANUAL_PARAPHRASE",
        "domain": "app",
        "extension_factors": {
            "ato_consulta": True,
            "dominio_app": True,
        },
    }

    validado = validar_exemplo(base, intents_permitidas={"LIST_WINDOWS"})

    assert validado["extension_factors"] == {
        "ato_consulta": True,
        "dominio_app": True,
    }
    with pytest.raises(ValueError, match="extension_factors"):
        validar_exemplo(
            {**base, "extension_factors": {"ato_consulta": "sim"}},
            intents_permitidas={"LIST_WINDOWS"},
        )


@pytest.mark.parametrize("fonte", ["REAL_FAILURE", "COUNTERFACTUAL"])
def test_dataset_aceita_fontes_prioritarias_do_plano_neural(fonte: str) -> None:
    exemplo = validar_exemplo(
        {
            "text": "dá uma diminuída nisso",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "down",
            "family": f"volume_{fonte.casefold()}",
            "source": fonte,
            "domain": "audio",
        },
        intents_permitidas={"VOLUME"},
    )

    assert exemplo["source"] == fonte


def test_modelo_treina_tres_cabecas_e_recarrega_artefato(tmp_path) -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "diminui o som", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "aumenta o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"text": "não abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": True, "action": "down"},
        {"text": "abre o chrome", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "inicia o navegador", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "eu gosto do chrome", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "ontem eu abaixei o volume", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "não precisa abrir nada", "intent": "NONE", "is_command": False, "negated": True, "action": "none"},
    ]
    caminho = tmp_path / "modelo.joblib"
    modelo = treinar_modelo(exemplos, caminho=caminho, versao="teste-1")
    recarregado = carregar_modelo(caminho)

    esperado = modelo.prever("abaixa o volume")
    observado = recarregado.prever("abaixa o volume")
    assert caminho.exists()
    assert recarregado.versao == "teste-1"
    assert observado["intent"] == esperado["intent"] == "VOLUME"
    assert observado["is_command"] is True
    assert observado["negated"] is False
    assert observado["params"]["acao"] == "down"
    assert observado["ood"] is False


def _treinar_modelo_base_para_extensao(tmp_path):
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "diminui o som", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "aumenta o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"text": "não abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": True, "action": "down"},
        {"text": "abre o chrome", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "eu gosto do chrome", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "não precisa abrir nada", "intent": "NONE", "is_command": False, "negated": True, "action": "none"},
    ]
    return treinar_modelo(
        exemplos,
        caminho=tmp_path / "modelo-base-extensao.joblib",
        versao="base-extensao",
        estrategia="sgd_log_loss",
    )


def test_extensao_intent_unica_preserva_gates_e_saida_fora_do_escopo(
    tmp_path,
) -> None:
    modelo = _treinar_modelo_base_para_extensao(tmp_path)
    fala_fora = "abaixa o volume"
    fala_alvo = "quais janelas estão abertas"
    previsao_fora_base = modelo.prever(fala_fora)
    previsao_alvo_base = modelo.prever(fala_alvo)
    modelo.extensoes_intent = {
        "LIST_WINDOWS": modelo_neural.ExtensaoIntentNeural(
            intent="LIST_WINDOWS",
            action="list",
            detector=_DetectorExtensaoFalso(("janelas",)),
            limiar=0.925,
            versao="list-windows-teste",
        )
    }

    assert modelo.prever(fala_fora) == previsao_fora_base
    observado = modelo.prever(fala_alvo)
    assert observado["intent"] == "LIST_WINDOWS"
    assert observado["gate_intent"] == "LIST_WINDOWS"
    assert observado["raw_action"] == "list"
    assert observado["params"] == {"acao": "list"}
    assert observado["is_command"] is previsao_alvo_base["is_command"]
    assert observado["raw_is_command"] is previsao_alvo_base["raw_is_command"]
    assert observado["negated"] is previsao_alvo_base["negated"]
    assert observado["command_probability"] == previsao_alvo_base["command_probability"]
    assert observado["command_threshold"] == previsao_alvo_base["command_threshold"]
    assert observado["intent_extension_applied"] == "LIST_WINDOWS"
    assert "autoriza_execucao" not in observado
    normalizado = normalizar_previsao_neural(
        observado,
        texto=fala_alvo,
        modelo=modelo.versao,
        intents_permitidas={"VOLUME", "APP_OPEN", "LIST_WINDOWS"},
    )
    assert normalizado["autoriza_execucao"] is False
    assert normalizado["somente_observacao"] is True
    assert normalizado["intent_extension"] == {
        "intent": "LIST_WINDOWS",
        "version": "list-windows-teste",
        "scope": "",
        "representation": "tfidf",
        "probability": 0.99,
        "threshold": 0.925,
    }


def test_extensoes_intent_ambiguas_falham_fechadas_sem_alterar_base(tmp_path) -> None:
    modelo = _treinar_modelo_base_para_extensao(tmp_path)
    fala = "mostra as janelas abertas"
    previsao_base = modelo.prever(fala)
    detector = _DetectorExtensaoFalso(("janelas",))
    modelo.extensoes_intent = {
        "LIST_WINDOWS": modelo_neural.ExtensaoIntentNeural(
            intent="LIST_WINDOWS",
            action="list",
            detector=detector,
            limiar=0.925,
        ),
        "OUTRA_INTENT": modelo_neural.ExtensaoIntentNeural(
            intent="OUTRA_INTENT",
            action="inspect",
            detector=detector,
            limiar=0.925,
        ),
    }

    assert modelo.prever(fala) == previsao_base


def test_extensao_fatorada_exige_todos_os_fatores_para_propor_intent(
    tmp_path,
) -> None:
    modelo = _treinar_modelo_base_para_extensao(tmp_path)
    modelo.extensoes_intent = {
        "LIST_WINDOWS": modelo_neural.ExtensaoIntentNeural(
            intent="LIST_WINDOWS",
            action="list",
            detector=None,
            limiar=0.925,
            versao="list-windows-fatorada",
            detectores_fatores={
                "ato_consulta": _DetectorExtensaoFalso(("consulta",)),
                "dominio_app": _DetectorExtensaoFalso(("aplicativo",)),
            },
        )
    }

    assert modelo.prever("consulta o aplicativo")["intent"] == "LIST_WINDOWS"
    assert modelo.prever("consulta a porta")["intent"] != "LIST_WINDOWS"
    assert modelo.prever("o aplicativo permanece aberto")["intent"] != "LIST_WINDOWS"
    observado = modelo.prever("consulta o aplicativo")
    assert observado["intent_extension_factor_probabilities"] == {
        "ato_consulta": 0.99,
        "dominio_app": 0.99,
    }


@pytest.mark.parametrize("valor_invalido", [float("nan"), float("inf"), -0.1, 1.1])
def test_fator_com_score_invalido_preserva_previsao_base(tmp_path, valor_invalido):
    class DetectorInvalido:
        classes_ = [False, True]

        def predict_proba(self, entradas):
            return [[0.0, valor_invalido] for _ in entradas]

    modelo = _treinar_modelo_base_para_extensao(tmp_path)
    texto = "consulta aplicativo"
    esperado = modelo.prever(texto)
    modelo.extensoes_intent = {
        "LIST_WINDOWS": modelo_neural.ExtensaoIntentNeural(
            intent="LIST_WINDOWS", action="list", detector=None,
            detectores_fatores={
                "a_valido": _DetectorExtensaoFalso(("consulta",)),
                "z_invalido": DetectorInvalido(),
            },
        ),
    }
    assert modelo.prever(texto) == esperado


def test_extensao_recusa_fator_sem_nome_em_vez_de_remover_condicao():
    with pytest.raises(ValueError, match="nome"):
        modelo_neural.ExtensaoIntentNeural(
            intent="LIST_WINDOWS", action="list", detector=None,
            detectores_fatores={
                "ato": _DetectorExtensaoFalso(("consulta",)),
                " ": _DetectorExtensaoFalso(("impossivel",)),
            },
        )


def test_adicionar_extensao_intent_nao_muta_base_e_persiste_candidato(
    tmp_path,
) -> None:
    modelo_base = _treinar_modelo_base_para_extensao(tmp_path)
    destino = tmp_path / "modelo-com-extensao.joblib"
    exemplos = [
        {"text": "o editor está aberto", "intent": "LIST_WINDOWS", "extension_scope": "estado_alvo"},
        {"text": "a calculadora continua aberta", "intent": "LIST_WINDOWS", "extension_scope": "estado_alvo"},
        {"text": "mostra as janelas abertas", "intent": "LIST_WINDOWS", "extension_scope": "inventario"},
        {"text": "abaixa o volume", "intent": "VOLUME"},
        {"text": "abre o navegador", "intent": "APP_OPEN"},
        {"text": "como está o clima", "intent": "NONE"},
    ]

    candidato = modelo_neural.adicionar_extensao_intent(
        modelo_base,
        exemplos,
        intent="LIST_WINDOWS",
        action="list",
        limiar=0.925,
        escopo="estado_alvo",
        representacao="estrutura_bordas",
        versao="candidato-extensao-v1",
        caminho=destino,
    )
    recarregado = carregar_modelo(destino)

    assert getattr(modelo_base, "extensoes_intent", {}) == {}
    assert candidato is not modelo_base
    assert candidato.versao == "candidato-extensao-v1"
    assert set(candidato.extensoes_intent) == {"LIST_WINDOWS"}
    assert set(recarregado.extensoes_intent) == {"LIST_WINDOWS"}
    assert recarregado.extensoes_intent["LIST_WINDOWS"].limiar == 0.925
    assert recarregado.extensoes_intent["LIST_WINDOWS"].escopo == "estado_alvo"
    assert (
        recarregado.extensoes_intent["LIST_WINDOWS"].representacao
        == "estrutura_bordas"
    )


def test_adicionar_extensao_intent_fatorada_treina_e_persiste_detectores(
    tmp_path,
) -> None:
    modelo_base = _treinar_modelo_base_para_extensao(tmp_path)
    destino = tmp_path / "modelo-fatorado.joblib"
    exemplos = [
        {"text": "o editor está aberto?", "extension_factors": {"ato_consulta": True, "dominio_app": True}},
        {"text": "consulta o aplicativo", "extension_factors": {"ato_consulta": True, "dominio_app": True}},
        {"text": "a porta está aberta?", "extension_factors": {"ato_consulta": True, "dominio_app": False}},
        {"text": "confere a matrícula", "extension_factors": {"ato_consulta": True, "dominio_app": False}},
        {"text": "o editor está aberto.", "extension_factors": {"ato_consulta": False, "dominio_app": True}},
        {"text": '"o aplicativo está aberto?"', "extension_factors": {"ato_consulta": False, "dominio_app": True}},
        {"text": "a porta ficou aberta.", "extension_factors": {"ato_consulta": False, "dominio_app": False}},
        {"text": "a inscrição segue aberta.", "extension_factors": {"ato_consulta": False, "dominio_app": False}},
    ]

    candidato = modelo_neural.adicionar_extensao_intent_fatorada(
        modelo_base,
        exemplos,
        intent="LIST_WINDOWS",
        action="list",
        limiar=0.7,
        representacoes_fatores={
            "ato_consulta": "estrutura_pontuacao",
            "dominio_app": "tfidf",
        },
        versao="candidato-fatorado-v1",
        caminho=destino,
    )
    recarregado = carregar_modelo(destino)

    assert getattr(modelo_base, "extensoes_intent", {}) == {}
    assert set(candidato.extensoes_intent["LIST_WINDOWS"].detectores_fatores) == {
        "ato_consulta", "dominio_app",
    }
    assert set(recarregado.extensoes_intent["LIST_WINDOWS"].detectores_fatores) == {
        "ato_consulta", "dominio_app",
    }
    assert recarregado.extensoes_intent["LIST_WINDOWS"].detector is None


def test_representacao_estrutura_bordas_e_generica_e_independe_de_rotulo() -> None:
    observado = modelo_neural.enriquecer_texto_estrutura_bordas(
        "A ferramenta de desenho continua aberta?"
    )

    assert "LIST_WINDOWS" not in observado
    assert "prefixo_1_a" in observado
    assert "sufixo_2_continua_aberta" in observado
    assert "tamanho_6" in observado


def test_representacao_estrutura_pontuacao_distingue_pergunta_afirmacao_e_citacao() -> None:
    pergunta = modelo_neural.enriquecer_texto_estrutura_pontuacao(
        "O editor está aberto?"
    )
    afirmacao = modelo_neural.enriquecer_texto_estrutura_pontuacao(
        "O editor está aberto."
    )
    citacao = modelo_neural.enriquecer_texto_estrutura_pontuacao(
        '"O editor está aberto?"'
    )

    assert "marcador_interrogacao_final" in pergunta
    assert "marcador_sem_interrogacao_final" in afirmacao
    assert "marcador_citacao_total" in citacao
    assert "marcador_sem_citacao_total" in pergunta
    assert pergunta != afirmacao != citacao
    assert "LIST_WINDOWS" not in pergunta


def test_representacao_semantica_codifica_uma_vez_e_preserva_gates(tmp_path) -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "aumenta o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"text": "não abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": True, "action": "down"},
        {"text": "abre o navegador", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "ontem abri o navegador", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    encoder = _EncoderSemanticoFalso()
    caminho = tmp_path / "modelo-semantico.joblib"
    modelo = treinar_modelo(
        exemplos,
        caminho=caminho,
        versao="teste-semantico",
        estrategia="sgd_log_loss",
        arquitetura_comando="intent_gated",
        arquitetura_acao="hierarchical",
        representacao="onnx_semantico",
        encoder_semantico=encoder,
    )

    assert encoder.chamadas == [tuple(item["text"] for item in exemplos)]
    previsao = modelo.prever("pode abaixar o volume")
    assert len(encoder.chamadas) == 2
    assert encoder.chamadas[-1] == ("pode abaixar o volume",)
    assert modelo.representacao == "onnx_semantico"
    assert isinstance(modelo.cabeca_comando, Pipeline)
    assert isinstance(modelo.cabeca_negacao, Pipeline)
    assert not isinstance(modelo.cabeca_intent, Pipeline)
    assert isinstance(previsao["is_command"], bool)
    assert isinstance(previsao["negated"], bool)
    assert previsao["ood_calibrated"] is False
    assert modelo.precarregar() is True

    recarregado = carregar_modelo(caminho)
    observado = recarregado.prever("pode abaixar o volume")
    assert recarregado.representacao == "onnx_semantico"
    assert observado["intent"] == previsao["intent"]
    assert observado["params"] == previsao["params"]


def test_representacao_semantica_hibrida_preserva_sinal_lexical_curto(tmp_path) -> None:
    exemplos = [
        {"text": "pausa aí", "intent": "MEDIA_CONTROL", "is_command": True, "negated": False, "action": "pause"},
        {"text": "pausa a música", "intent": "MEDIA_CONTROL", "is_command": True, "negated": False, "action": "pause"},
        {"text": "despausa aí", "intent": "MEDIA_CONTROL", "is_command": True, "negated": False, "action": "play"},
        {"text": "despausa o som", "intent": "MEDIA_CONTROL", "is_command": True, "negated": False, "action": "play"},
        {"text": "fecha a aba", "intent": "CLOSE_TAB", "is_command": True, "negated": False, "action": "close"},
        {"text": "ontem eu pausei", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    encoder = _EncoderSemanticoFalso()
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "modelo-semantico-hibrido.joblib",
        versao="teste-semantico-hibrido",
        estrategia="sgd_log_loss",
        arquitetura_comando="intent_gated",
        arquitetura_acao="hierarchical",
        representacao="onnx_semantico_hibrido",
        encoder_semantico=encoder,
        limiares_comando_por_intent={"media_control": 0.605},
    )

    vetores = modelo.encoder_semantico.codificar(["pausa", "despausa"])

    assert modelo.representacao == "onnx_semantico_hibrido"
    assert modelo.limiares_comando_por_intent == {"MEDIA_CONTROL": 0.605}
    assert getattr(modelo, "cabeca_intent_gate", None) is not None
    assert vetores.shape[0] == 2
    assert vetores.shape[1] > 4
    assert not np.array_equal(vetores[0], vetores[1])
    recarregado = carregar_modelo(tmp_path / "modelo-semantico-hibrido.joblib")
    vetores_recarregados = recarregado.encoder_semantico.codificar(
        ["pausa", "despausa"]
    )
    assert recarregado.representacao == "onnx_semantico_hibrido"
    assert np.array_equal(vetores, vetores_recarregados)
    assert recarregado.limiares_comando_por_intent == {"MEDIA_CONTROL": 0.605}

    with pytest.raises(ValueError, match="intent operacional"):
        treinar_modelo(
            exemplos,
            caminho=tmp_path / "limiar-none.joblib",
            versao="limiar-none",
            estrategia="sgd_log_loss",
            representacao="onnx_semantico_hibrido",
            encoder_semantico=_EncoderSemanticoFalso(),
            limiares_comando_por_intent={"NONE": 0.6},
        )


def test_heads_especializados_nao_treinam_gate_de_intent_implicitamente(tmp_path) -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "aumenta o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "ontem ajustei o som", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {
            "text": "costumo deixar o ventilador desligado",
            "intent": "IOT_CONTROL",
            "is_command": False,
            "negated": False,
            "action": "none",
            "training_heads": ["command"],
        },
        {
            "text": "inicia o aplicativo de desenho",
            "intent": "APP_OPEN",
            "is_command": True,
            "negated": False,
            "action": "open",
            "training_heads": ["intent"],
        },
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "gate-intent-escopado.joblib",
        versao="gate-intent-escopado",
        estrategia="sgd_log_loss",
        representacao="onnx_semantico_hibrido",
        encoder_semantico=_EncoderSemanticoFalso(),
    )

    assert "APP_OPEN" in set(modelo.cabeca_intent.classes_)
    assert {"IOT_CONTROL", "APP_OPEN"}.isdisjoint(
        set(modelo.cabeca_intent_gate.classes_)
    )


def test_head_comando_direcionado_isola_fronteira_da_intent(tmp_path) -> None:
    class _CabecaConstante:
        def __init__(self, valor) -> None:
            self.valor = valor
            self.classes_ = [valor]

        def predict(self, _entradas):
            return [self.valor]

        def predict_proba(self, _entradas):
            return [[1.0]]

    exemplos = [
        {"text": "liga a luz", "intent": "IOT_CONTROL", "is_command": True, "negated": False, "action": "on"},
        {"text": "desliga a luz", "intent": "IOT_CONTROL", "is_command": True, "negated": False, "action": "off"},
        {"text": "toca uma música", "intent": "MUSIC_SEARCH", "is_command": True, "negated": False, "action": "search"},
        {"text": "procura outra faixa", "intent": "MUSIC_SEARCH", "is_command": True, "negated": False, "action": "search"},
        {"text": "essa música é boa", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "ontem ouvi música", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {
            "text": "costumo deixar a luz apagada",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "training_heads": ["command"],
            "command_head_intent": "IOT_CONTROL",
        },
        {
            "text": "prefiro o ventilador ligado durante o dia",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "training_heads": ["command"],
            "command_head_intent": "IOT_CONTROL",
        },
    ]
    caminho = tmp_path / "command-head-direcionado.joblib"
    modelo = treinar_modelo(
        exemplos,
        caminho=caminho,
        versao="command-head-direcionado",
        arquitetura_comando="intent_gated",
        estrategia="sgd_log_loss",
        representacao="onnx_semantico_hibrido",
        encoder_semantico=_EncoderSemanticoFalso(),
    )

    assert set(modelo.cabecas_comando_por_intent) == {"IOT_CONTROL"}
    modelo.cabeca_comando = _CabecaConstante(True)
    modelo.cabecas_comando_por_intent["IOT_CONTROL"] = _CabecaConstante(False)
    modelo.cabeca_intent = _CabecaConstante("IOT_CONTROL")
    modelo.cabeca_intent_gate = _CabecaConstante("MUSIC_SEARCH")
    previsao_iot = modelo.prever("frase ambígua")
    modelo.cabeca_intent = _CabecaConstante("MUSIC_SEARCH")
    modelo.cabeca_intent_gate = _CabecaConstante("MUSIC_SEARCH")
    previsao_musica = modelo.prever("frase ambígua")

    assert previsao_iot["command_head_scope"] == "IOT_CONTROL"
    assert previsao_iot["raw_is_command"] is False
    assert previsao_musica["command_head_scope"] == "GLOBAL"
    assert previsao_musica["raw_is_command"] is True
    recarregado = carregar_modelo(caminho)
    assert set(recarregado.cabecas_comando_por_intent) == {"IOT_CONTROL"}


def test_head_comando_direcionado_reusa_nao_comandos_do_mesmo_dominio(
    tmp_path,
) -> None:
    exemplos = [
        {
            "text": "acende a luminária",
            "intent": "IOT_CONTROL",
            "is_command": True,
            "negated": False,
            "action": "on",
            "domain": "iot",
        },
        {
            "text": "toca uma faixa",
            "intent": "MUSIC_SEARCH",
            "is_command": True,
            "negated": False,
            "action": "search",
            "domain": "music",
        },
        {
            "text": "telemetriaiot descreve o estado da luminária",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "iot",
        },
        {
            "text": "musicadominio descreve uma faixa antiga",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "music",
        },
        {
            "text": "costumo deixar a luz apagada",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "domain": "iot",
            "training_heads": ["command"],
            "command_head_intent": "IOT_CONTROL",
        },
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "command-head-negativos-dominio.joblib",
        versao="command-head-negativos-dominio",
        arquitetura_comando="intent_gated",
        estrategia="sgd_log_loss",
        representacao="onnx_semantico_hibrido",
        encoder_semantico=_EncoderSemanticoFalso(),
    )

    features = modelo.cabecas_comando_por_intent["IOT_CONTROL"].named_steps[
        "features"
    ]
    vocabulario = features.transformer_list[0][1].vocabulary_
    assert "telemetriaiot" in vocabulario
    assert "musicadominio" not in vocabulario


def test_representacao_semantica_exige_encoder_e_nao_pode_promover(tmp_path) -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    with pytest.raises(ValueError, match="encoder semântico"):
        treinar_modelo(
            exemplos,
            caminho=tmp_path / "sem-encoder.joblib",
            versao="teste-sem-encoder",
            estrategia="sgd_log_loss",
            representacao="onnx_semantico",
        )

    with pytest.raises(ValueError, match="configuração experimental"):
        executar_ciclo_treino(
            pasta_estado=tmp_path,
            promover_se_aprovado=True,
            versao="teste-semantico-nao-promove",
            estrategia="sgd_log_loss",
            representacao="onnx_semantico",
        )

    assert not (tmp_path / "modelo_candidato.joblib").exists()


def test_encoder_semantico_falha_fechado_quando_artefato_esta_ausente(
    tmp_path,
) -> None:
    encoder = EncoderSemanticoONNX(tmp_path / "modelo-ausente")

    with pytest.raises(FileNotFoundError):
        encoder.validar_artefatos()


def test_encoder_semantico_revalida_hash_depois_de_recarregar(tmp_path) -> None:
    pasta = tmp_path / "encoder"
    modelo_path = pasta / "onnx" / "model_quint8_avx2.onnx"
    tokenizer_path = pasta / "tokenizer.json"
    modelo_path.parent.mkdir(parents=True)
    modelo_path.write_bytes(b"modelo-original")
    tokenizer_path.write_text("{}", encoding="utf-8")
    hash_original = hashlib.sha256(b"modelo-original").hexdigest()
    encoder = EncoderSemanticoONNX(pasta, sha256_modelo=hash_original)
    artefato = tmp_path / "encoder.joblib"

    assert encoder.validar_artefatos() is True
    joblib.dump(encoder, artefato)
    modelo_path.write_bytes(b"modelo-adulterado")
    recarregado = joblib.load(artefato)

    with pytest.raises(ValueError, match="SHA-256"):
        recarregado.validar_artefatos()


def test_modelo_preguicoso_precarrega_dependencias_do_modelo(tmp_path) -> None:
    class ModeloFalso:
        chamadas = 0

        def precarregar(self) -> bool:
            self.chamadas += 1
            return True

    carregador = ModeloNeuralPreguicoso(tmp_path / "nao-sera-lido.joblib")
    modelo = ModeloFalso()
    carregador._modelo = modelo

    assert carregador.precarregar() is True
    assert modelo.chamadas == 1


def test_caminho_modelo_neural_explicito_nao_substitui_ativo(tmp_path) -> None:
    pasta_memoria = tmp_path / "memoria"
    padrao = resolver_caminho_modelo_neural(
        raiz=tmp_path,
        pasta_memoria=pasta_memoria,
        configurado="",
    )
    sombra = resolver_caminho_modelo_neural(
        raiz=tmp_path,
        pasta_memoria=pasta_memoria,
        configurado="memoria/neural/modelo_semantico_shadow.joblib",
    )

    assert padrao == pasta_memoria / "neural" / "modelo_ativo.joblib"
    assert sombra == tmp_path / "memoria" / "neural" / "modelo_semantico_shadow.joblib"
    assert sombra != padrao


def test_candidato_semantico_so_e_padrao_quando_modo_e_shadow(tmp_path) -> None:
    pasta_memoria = tmp_path / "memoria"
    candidato = pasta_memoria / "neural" / "modelo_semantico_shadow.joblib"
    candidato.parent.mkdir(parents=True)
    candidato.write_bytes(b"artefato")

    em_shadow = resolver_caminho_modelo_neural(
        raiz=tmp_path,
        pasta_memoria=pasta_memoria,
        configurado="",
        modo="shadow",
        candidato_shadow=candidato,
    )
    fora_shadow = resolver_caminho_modelo_neural(
        raiz=tmp_path,
        pasta_memoria=pasta_memoria,
        configurado="",
        modo="candidate",
        candidato_shadow=candidato,
    )

    assert em_shadow == candidato
    assert fora_shadow == pasta_memoria / "neural" / "modelo_ativo.joblib"


def test_validacao_cruzada_semantica_recebe_encoder_sem_promover() -> None:
    exemplos = []
    for familia in ("grupo_a", "grupo_b", "grupo_c"):
        exemplos.extend(
            [
                {"text": f"abaixa o volume {familia}", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down", "family": familia},
                {"text": f"aumenta o volume {familia}", "intent": "VOLUME", "is_command": True, "negated": False, "action": "up", "family": familia},
                {"text": f"abre o navegador {familia}", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open", "family": familia},
                {"text": f"não abaixa o volume {familia}", "intent": "VOLUME", "is_command": True, "negated": True, "action": "down", "family": familia},
                {"text": f"o volume está alto {familia}", "intent": "NONE", "is_command": False, "negated": False, "action": "none", "family": familia},
                {"text": f"ontem abri o navegador {familia}", "intent": "NONE", "is_command": False, "negated": False, "action": "none", "family": familia},
            ]
        )

    relatorio = validar_por_familias(
        exemplos,
        n_splits=3,
        estrategia="sgd_log_loss",
        representacao="onnx_semantico",
        encoder_semantico=_EncoderSemanticoFalso(),
        exemplos_ood=[
            {"text": "manda um email", "partition": "calibration"},
            {"text": "cria um alarme", "partition": "calibration"},
            {"text": "por favor manda um email", "partition": "evaluation"},
            {"text": "por favor cria um alarme", "partition": "evaluation"},
        ],
    )

    assert relatorio["representacao"] == "onnx_semantico"
    assert relatorio["encoder_semantico_configurado"] is True
    assert relatorio["contrato"]["autoriza_promocao"] is False
    assert relatorio["contrato"]["ood_usado_como_treino"] is False
    assert relatorio["calibracao_ood"]["contrato"]["autoriza_execucao"] is False


@pytest.mark.parametrize("estrategia", ["logistic", "sgd_log_loss", "complement_nb"])
def test_modelo_experimental_preserva_contrato_de_previsao(
    tmp_path,
    estrategia: str,
) -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "não abaixa o som", "intent": "VOLUME", "is_command": True, "negated": True, "action": "down"},
        {"text": "o áudio está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "ontem mexi no volume", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]

    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / f"{estrategia}.joblib",
        versao=f"teste-{estrategia}",
        estrategia=estrategia,
    )
    previsao = modelo.prever("pode abaixar o volume")

    assert modelo.estrategia == estrategia
    assert isinstance(previsao["is_command"], bool)
    assert isinstance(previsao["negated"], bool)
    assert set(previsao["confidence"]) == {
        "intent", "intent_gate", "command", "negation", "action",
    }


def test_acao_hierarquica_pertence_ao_owner_da_intent_prevista(tmp_path) -> None:
    exemplos = [
        {"text": "procura o relatório", "intent": "FILE_SEARCH", "is_command": True, "negated": False, "action": "search"},
        {"text": "localiza a planilha", "intent": "FILE_SEARCH", "is_command": True, "negated": False, "action": "search"},
        {"text": "lê o documento", "intent": "FILE_READ", "is_command": True, "negated": False, "action": "read"},
        {"text": "conta o arquivo", "intent": "FILE_READ", "is_command": True, "negated": False, "action": "read"},
        {"text": "eu li um documento", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "meu arquivo sumiu", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "hierarquico.joblib",
        versao="teste-hierarquico",
        arquitetura_acao="hierarchical",
    )
    permitidas = {
        "FILE_SEARCH": {"search"},
        "FILE_READ": {"read"},
        "NONE": {"none"},
    }

    for texto in ("acha e conta esse arquivo", "procura o documento", "lê a planilha"):
        previsao = modelo.prever(texto)
        acao = previsao["params"].get("acao", "none")
        assert acao in permitidas[previsao["intent"]]

    assert modelo.arquitetura_acao == "hierarchical"


def test_comando_intent_gated_veta_true_quando_intent_e_none(tmp_path) -> None:
    class _CabecaConstante:
        def __init__(self, valor) -> None:
            self.valor = valor
            self.classes_ = [valor]

        def predict(self, _textos):
            return [self.valor]

        def predict_proba(self, _textos):
            return [[1.0]]

    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "intent-gated.joblib",
        versao="teste-intent-gated",
        arquitetura_comando="intent_gated",
    )
    modelo.cabeca_intent = _CabecaConstante("NONE")
    modelo.cabeca_comando = _CabecaConstante(True)
    modelo.cabeca_negacao = _CabecaConstante(False)
    modelo.cabeca_acao = _CabecaConstante("down")

    previsao = modelo.prever("frase ambígua")

    assert previsao["intent"] == "NONE"
    assert previsao["raw_is_command"] is True
    assert previsao["is_command"] is False
    assert previsao["command_veto_reason"] == "intent_desconhecida"
    assert previsao["raw_action"] == "down"
    assert previsao["params"] == {}


def test_intent_gated_aceita_fallback_semantico_calibrado_por_intent() -> None:
    from mente_laylay.neural.modelo import veto_intent_comando

    configuracao = {"WEATHER": 0.6}
    assert veto_intent_comando(
        "intent_gated",
        intent="WEATHER",
        intent_gate="NONE",
        confianca_intent=0.66,
        limiares_fallback_intent_semantica=configuracao,
    ) is False
    assert veto_intent_comando(
        "intent_gated",
        intent="WEATHER",
        intent_gate="NONE",
        confianca_intent=0.54,
        limiares_fallback_intent_semantica=configuracao,
    ) is True
    assert veto_intent_comando(
        "intent_gated",
        intent="MUSIC_SEARCH",
        intent_gate="NONE",
        confianca_intent=0.9,
        limiares_fallback_intent_semantica=configuracao,
    ) is True


def test_limiar_conservador_veta_comando_sem_transformar_previsao_em_autoridade(
    tmp_path,
) -> None:
    class _CabecaProbabilistica:
        classes_ = [False, True]

        @staticmethod
        def predict(_textos):
            return [True]

        @staticmethod
        def predict_proba(_textos):
            return [[0.4, 0.6]]

    exemplos = [
        {"text": "toca uma música", "intent": "MUSIC_SEARCH", "is_command": True, "negated": False, "action": "search"},
        {"text": "essa música é boa", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "limiar-conservador.joblib",
        versao="teste-limiar-conservador",
        limiar_comando=0.65,
    )
    modelo.cabeca_comando = _CabecaProbabilistica()

    previsao = modelo.prever("frase ambígua")

    assert previsao["raw_is_command"] is True
    assert previsao["command_probability"] == pytest.approx(0.6)
    assert previsao["command_threshold"] == 0.65
    assert previsao["is_command"] is False
    assert previsao["command_veto_reason"] == "confianca_comando_abaixo_limiar"


def test_limiar_por_intent_tambem_se_aplica_ao_head_global(tmp_path) -> None:
    class _CabecaConstante:
        def __init__(self, valor) -> None:
            self.valor = valor
            self.classes_ = [valor]

        def predict(self, _entradas):
            return [self.valor]

        def predict_proba(self, _entradas):
            return [[1.0]]

    class _CabecaComando:
        classes_ = [False, True]

        @staticmethod
        def predict(_entradas):
            return [True]

        @staticmethod
        def predict_proba(_entradas):
            return [[0.4, 0.6]]

    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "limiar-intent-global.joblib",
        versao="limiar-intent-global",
        arquitetura_comando="intent_gated",
        limiar_comando=0.65,
        limiares_comando_por_intent={"VOLUME": 0.55},
    )
    modelo.cabeca_intent = _CabecaConstante("VOLUME")
    modelo.cabeca_comando = _CabecaComando()

    previsao = modelo.prever("frase ambígua")

    assert previsao["command_head_scope"] == "GLOBAL"
    assert previsao["command_threshold"] == pytest.approx(0.55)
    assert previsao["is_command"] is True


def test_limiar_conservador_experimental_nao_pode_promover(tmp_path) -> None:
    with pytest.raises(ValueError, match="configuração experimental"):
        executar_ciclo_treino(
            pasta_estado=tmp_path,
            promover_se_aprovado=True,
            versao="teste-limiar-nao-promove",
            limiar_comando=0.65,
        )

    assert not (tmp_path / "modelo_candidato.joblib").exists()


@pytest.mark.parametrize(
    "texto",
    [
        "nunca toque essa música",
        "evita abrir esse aplicativo",
        "deixa esse arquivo fora da lista",
        "qualquer opção menos essa",
        "troca essa faixa por outra",
        "escolhe outra no lugar dessa",
        "deixa o áudio nesse nível sem aumentar",
        "quero conservar esta aba",
        "continue com esta aba aberta",
        "fique longe desse site",
        "de jeito nenhum aumente o volume",
    ],
)
def test_representacao_experimental_marca_exclusao_sem_decidir(texto: str) -> None:
    enriquecido = enriquecer_texto_features(texto)

    assert "marcador_negacao_" in enriquecido
    assert "marcador_negacao_" not in enriquecer_texto_features(
        "troca para a próxima faixa"
    )
    assert enriquecer_texto_features("ontem fechei sem querer").endswith(
        "sem querer"
    )
    assert enriquecer_texto_features("terminei sem problema").endswith(
        "sem problema"
    )


def test_representacao_experimental_nao_pode_promover(tmp_path) -> None:
    with pytest.raises(ValueError, match="configuração experimental"):
        executar_ciclo_treino(
            pasta_estado=tmp_path,
            promover_se_aprovado=True,
            versao="teste-representacao-nao-promove",
            representacao="tfidf_indicadores",
        )

    assert not (tmp_path / "modelo_candidato.joblib").exists()


def test_indicadores_de_negacao_ficam_na_cabeca_dona_da_decisao(tmp_path) -> None:
    exemplos = [
        {"text": "abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": False, "action": "down"},
        {"text": "não abaixa o volume", "intent": "VOLUME", "is_command": True, "negated": True, "action": "down"},
        {"text": "abre o navegador", "intent": "APP_OPEN", "is_command": True, "negated": False, "action": "open"},
        {"text": "não abre o navegador", "intent": "APP_OPEN", "is_command": True, "negated": True, "action": "open"},
        {"text": "o volume está alto", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
        {"text": "ontem abri o navegador", "intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    modelo = treinar_modelo(
        exemplos,
        caminho=tmp_path / "indicadores-isolados.joblib",
        versao="teste-indicadores-isolados",
        representacao="tfidf_indicadores",
    )

    def preprocessador(cabeca):
        features = cabeca.named_steps["features"]
        palavras = dict(features.transformer_list)["palavras"]
        return palavras.preprocessor

    def ngramas_caracteres(cabeca):
        features = cabeca.named_steps["features"]
        caracteres = dict(features.transformer_list)["caracteres"]
        return caracteres.ngram_range

    assert preprocessador(modelo.cabeca_negacao) is enriquecer_texto_features
    assert preprocessador(modelo.cabeca_intent) is None
    assert (
        preprocessador(modelo.cabeca_comando)
        is enriquecer_texto_features_comando
    )
    assert preprocessador(modelo.cabeca_acao) is None
    assert ngramas_caracteres(modelo.cabeca_intent) == (3, 5)
    assert ngramas_caracteres(modelo.cabeca_acao) == (3, 5)
    assert ngramas_caracteres(modelo.cabeca_comando) == (4, 6)
    assert ngramas_caracteres(modelo.cabeca_negacao) == (4, 6)

    estavel = treinar_modelo(
        exemplos,
        caminho=tmp_path / "representacao-estavel.joblib",
        versao="teste-representacao-estavel",
        representacao="tfidf",
    )
    assert ngramas_caracteres(estavel.cabeca_intent) == (3, 5)
    assert ngramas_caracteres(estavel.cabeca_comando) == (3, 5)
    assert ngramas_caracteres(estavel.cabeca_negacao) == (3, 5)
    assert ngramas_caracteres(estavel.cabeca_acao) == (3, 5)


def test_avaliacao_prioriza_false_command_rate_e_separa_negacao() -> None:
    esperados = [
        {"intent": "VOLUME", "is_command": True, "negated": False},
        {"intent": "NONE", "is_command": False, "negated": False},
        {"intent": "VOLUME", "is_command": True, "negated": True},
        {"intent": "NONE", "is_command": False, "negated": False},
    ]
    previstos = [
        {"intent": "VOLUME", "is_command": True, "negated": False},
        {"intent": "VOLUME", "is_command": True, "negated": False},
        {"intent": "VOLUME", "is_command": True, "negated": True},
        {"intent": "NONE", "is_command": False, "negated": False},
    ]

    metricas = avaliar_previsoes(esperados, previstos)

    assert metricas["false_command_count"] == 1
    assert metricas["false_command_rate"] == 0.5
    assert metricas["command_precision"] == 2 / 3
    assert metricas["negation_accuracy"] == 1.0


def test_avaliacao_cv_respeita_training_heads_por_metrica() -> None:
    esperados = [
        {
            "intent": "WEATHER",
            "is_command": True,
            "negated": False,
            "action": "query",
            "training_heads": ["command"],
        },
        {
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "up",
        },
    ]
    previstos = [
        {
            "intent": "NONE",
            "is_command": True,
            "negated": True,
            "params": {"acao": "none"},
        },
        {
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "params": {"acao": "up"},
        },
    ]

    metricas = avaliar_previsoes(esperados, previstos)

    assert metricas["command_precision"] == 1.0
    assert metricas["command_recall"] == 1.0
    assert metricas["intent_accuracy"] == 1.0
    assert metricas["negation_accuracy"] == 1.0
    assert metricas["action_accuracy_command"] == 1.0
    assert metricas["joint_intent_action_accuracy_command"] == 1.0
    assert metricas["head_evaluation_counts"] == {
        "command": 2,
        "intent": 1,
        "negation": 1,
        "action_command": 1,
        "joint_intent_action_command": 1,
    }


def test_avaliacao_de_head_acao_usa_saida_bruta_quando_comando_foi_vetado() -> None:
    esperado = {
        "intent": "WEATHER",
        "is_command": True,
        "negated": False,
        "action": "query",
        "training_heads": ["action", "command", "intent"],
    }
    previsto = {
        "intent": "WEATHER",
        "is_command": False,
        "raw_is_command": True,
        "raw_action": "query",
        "negated": False,
        "params": {},
    }

    metricas = avaliar_previsoes([esperado], [previsto])

    assert metricas["command_recall"] == 0.0
    assert metricas["intent_accuracy"] == 1.0
    assert metricas["action_accuracy_command"] == 1.0
    assert metricas["joint_intent_action_accuracy_command"] == 1.0


def test_avaliacao_revela_acao_incompativel_com_intent_prevista() -> None:
    esperados = [
        {"intent": "FILE_SEARCH", "is_command": True, "negated": False, "action": "search"},
        {"intent": "FILE_READ", "is_command": True, "negated": False, "action": "read"},
        {"intent": "NONE", "is_command": False, "negated": False, "action": "none"},
    ]
    previstos = [
        {"intent": "FILE_SEARCH", "is_command": True, "negated": False, "params": {"acao": "read"}},
        {"intent": "FILE_READ", "is_command": True, "negated": False, "params": {"acao": "read"}},
        {"intent": "NONE", "is_command": False, "negated": False, "params": {}},
    ]

    metricas = avaliar_previsoes(
        esperados,
        previstos,
        acoes_por_intent={
            "FILE_SEARCH": {"search"},
            "FILE_READ": {"read"},
        },
    )

    assert metricas["invalid_intent_action_count"] == 1
    assert metricas["invalid_intent_action_rate"] == 0.5
    assert metricas["unknown_command_intent_count"] == 0
    assert metricas["incompatible_action_for_known_intent_count"] == 1
    assert metricas["action_accuracy_command"] == 0.5
    assert metricas["joint_intent_action_accuracy_command"] == 0.5


def test_experiencia_so_entra_no_treino_com_correcao_forte() -> None:
    registros = [
        {
            "tipo": "resultado_comando",
            "text": "abaixa o som",
            "intent_observada": "VOLUME",
            "apto_treino": False,
        },
        {
            "tipo": "correcao_interpretacao",
            "text": "fecha o chrome",
            "intent_correta": "CLOSE_APP",
            "params_corretos": {"acao": "close"},
            "apto_treino": True,
            "label_confidence": 1.0,
        },
    ]

    exemplos = experiencias_para_dataset(
        registros,
        intents_permitidas={"VOLUME", "CLOSE_APP"},
        dominio_por_intent={"CLOSE_APP": "app"},
    )

    assert len(exemplos) == 1
    assert exemplos[0]["intent"] == "CLOSE_APP"
    assert exemplos[0]["source"] == "EXPLICIT_CORRECTION"


def test_dataset_real_dev_e_frozen_nao_compartilham_familias() -> None:
    base = __import__("pathlib").Path(__file__).parents[1] / "mente_laylay" / "neural" / "datasets"
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS", "LIST_WINDOWS",
    }
    dev = carregar_jsonl(base / "dev_v0.jsonl", intents_permitidas=intents)
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=intents)

    assert len(dev) >= 50
    assert len(frozen) >= 20
    assert {item["family"] for item in dev}.isdisjoint(
        {item["family"] for item in frozen}
    )
    assert any(item["source"] == "HARD_NEGATIVE" for item in frozen)


def test_validacao_cruzada_mantem_familias_inteiras_fora_do_treino() -> None:
    exemplos = []
    for numero in range(6):
        comando = numero % 2 == 0
        exemplos.append(
            {
                "text": (
                    f"abaixa o volume exemplo {numero}"
                    if comando
                    else f"comentário sobre áudio exemplo {numero}"
                ),
                "intent": "VOLUME" if comando else "NONE",
                "is_command": comando,
                "negated": False,
                "action": "down" if comando else "none",
                "family": f"familia_{numero}",
                "source": "MANUAL_PARAPHRASE" if comando else "HARD_NEGATIVE",
                "domain": "audio",
            }
        )

    relatorio = validar_por_familias(
        exemplos,
        n_splits=3,
        estrategia="sgd_log_loss",
        arquitetura_comando="intent_gated",
    )

    assert relatorio["totais"]["exemplos"] == 6
    assert relatorio["totais"]["exemplos_avaliados"] == 6
    assert len(relatorio["folds"]) == 3
    assert relatorio["estrategia"] == "sgd_log_loss"
    assert relatorio["arquitetura_comando"] == "intent_gated"
    assert all(not fold["familias_compartilhadas"] for fold in relatorio["folds"])
    assert "invalid_intent_action_rate" in relatorio["metricas"]
    assert relatorio["contrato"]["challenge_usado"] is False
    assert relatorio["contrato"]["autoriza_execucao"] is False


def test_validacao_cruzada_estrita_mantem_mecanismos_inteiros_no_fold() -> None:
    exemplos = []
    for numero in range(6):
        comando = numero % 2 == 0
        exemplos.append({
            "text": f"frase semanticamente agrupada {numero}",
            "intent": "VOLUME" if comando else "NONE",
            "is_command": comando,
            "negated": False,
            "action": "down" if comando else "none",
            "family": f"familia_superficie_{numero}",
            "validation_group": f"mecanismo_{numero // 2}",
            "source": "MANUAL_PARAPHRASE" if comando else "HARD_NEGATIVE",
            "domain": "audio",
        })

    relatorio = validar_por_familias(
        exemplos,
        n_splits=3,
        estrategia="sgd_log_loss",
        arquitetura_comando="intent_gated",
        agrupamento="validation_group",
    )

    assert relatorio["agrupamento"] == "validation_group"
    assert relatorio["totais"]["familias"] == 6
    assert relatorio["totais"]["grupos_validacao"] == 3
    assert all(not fold["familias_compartilhadas"] for fold in relatorio["folds"])
    assert all(not fold["grupos_compartilhados"] for fold in relatorio["folds"])
    assert relatorio["contrato"]["grupos_semanticos_inteiros_por_fold"] is True


def test_validacao_cruzada_pode_isolar_entidades_sem_misturar_folds() -> None:
    exemplos = []
    for numero in range(6):
        comando = numero % 2 == 0
        exemplos.append({
            "text": f"consulta entidade {numero}",
            "intent": "VOLUME" if comando else "NONE",
            "is_command": comando,
            "negated": False,
            "action": "down" if comando else "none",
            "family": f"familia_{numero}",
            "validation_group": f"molde_{numero // 2}",
            "validation_entity_group": f"entidade_{numero // 2}",
            "source": "MANUAL_PARAPHRASE" if comando else "HARD_NEGATIVE",
            "domain": "audio",
        })

    relatorio = validar_por_familias(
        exemplos,
        n_splits=3,
        estrategia="sgd_log_loss",
        agrupamento="validation_entity_group",
    )

    assert relatorio["agrupamento"] == "validation_entity_group"
    assert relatorio["totais"]["grupos_validacao"] == 3
    assert all(not fold["grupos_compartilhados"] for fold in relatorio["folds"])
    assert relatorio["contrato"]["entidades_inteiras_por_fold"] is True


def test_validacao_semantica_usa_familia_quando_grupo_nao_foi_declarado() -> None:
    exemplos = []
    for numero in range(6):
        comando = numero % 2 == 0
        exemplos.append({
            "text": f"frase legada sem grupo {numero}",
            "intent": "VOLUME" if comando else "NONE",
            "is_command": comando,
            "negated": False,
            "action": "down" if comando else "none",
            "family": f"familia_legada_{numero}",
            "source": "MANUAL_PARAPHRASE" if comando else "HARD_NEGATIVE",
            "domain": "audio",
        })

    relatorio = validar_por_familias(
        exemplos,
        n_splits=3,
        estrategia="sgd_log_loss",
        arquitetura_comando="intent_gated",
        agrupamento="validation_group",
    )

    assert relatorio["totais"]["familias"] == 6
    assert relatorio["totais"]["grupos_validacao"] == 6
    assert len(relatorio["folds"]) == 3


def test_lote_piloto_volume_staged_cumpre_seguranca_sem_contaminar_dev() -> None:
    base = __import__("pathlib").Path(__file__).parents[1] / "mente_laylay" / "neural" / "datasets"
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS", "LIST_WINDOWS",
    }
    dev = carregar_jsonl(base / "dev_v0.jsonl", intents_permitidas=intents)
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=intents)
    lote = carregar_jsonl(
        base / "candidatos" / "volume_piloto_v1.jsonl",
        intents_permitidas=intents,
    )
    manifesto = carregar_manifesto_variantes(
        base / "catalogo_variantes_v0.json",
        intents_catalogadas=intents,
    )
    relatorio_canonico = analisar_cobertura_dataset(
        dev,
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
    )
    relatorio = analisar_cobertura_dataset(
        [*dev, *lote],
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
        meta_minima_dev=150,
        meta_maxima_dev=200,
        meta_minima_familias_dev=12,
        meta_minima_negados_dev=15,
        meta_minima_hard_negatives_dev_por_dominio=30,
    )

    for variante in ("VOLUME:down", "VOLUME:up"):
        assert relatorio_canonico["por_comando"][variante]["negados_dev"] < 15
        assert relatorio["por_comando"][variante]["familias_dev"] >= 12
        assert relatorio["por_comando"][variante]["negados_dev"] >= 15
        assert relatorio["por_comando"][variante]["status_meta_dev"] == "abaixo_da_meta"
    assert relatorio["por_dominio"]["audio"]["hard_negatives_dev"] >= 30
    assert relatorio["pronto_para_ampliar_influencia"] is False


def test_onda_balanceada_staged_limita_desvio_sem_contaminar_dev() -> None:
    base = __import__("pathlib").Path(__file__).parents[1] / "mente_laylay" / "neural" / "datasets"
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS", "LIST_WINDOWS",
    }
    dev = carregar_jsonl(base / "dev_v0.jsonl", intents_permitidas=intents)
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=intents)
    lote = carregar_jsonl(
        base / "candidatos" / "onda_balanceada_v1.jsonl",
        intents_permitidas=intents,
    )
    manifesto = carregar_manifesto_variantes(
        base / "catalogo_variantes_v0.json",
        intents_catalogadas=intents,
    )

    canonico = analisar_cobertura_dataset(
        dev,
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
    )
    staged = analisar_cobertura_dataset(
        [*dev, *lote],
        frozen,
        intents_catalogadas=intents,
        comandos_planejados=manifesto["variants"],
    )

    assert {dados["dev"] for dados in canonico["por_comando"].values()} != {6}
    contagens = [
        dados["dev"]
        for dados in staged["por_comando"].values()
        if dados["dev"]
    ]
    assert min(contagens) == 6
    assert max(contagens) - min(contagens) <= 1
    assert all(
        dados["familias_dev"] >= 3 and dados["negados_dev"] >= 2
        for dados in staged["por_comando"].values()
        if dados["dev"]
    )
    assert all(
        not dados["cota_aplicavel"] or dados["hard_negatives_dev"] >= 6
        for dados in staged["por_dominio"].values()
    )
    assert auditar_leakage_dataset([*dev, *lote], frozen)["aprovado"] is True
    assert staged["pronto_para_ampliar_influencia"] is False


def test_falha_real_musical_entra_em_staging_com_contrastes_e_sem_leakage() -> None:
    base = __import__("pathlib").Path(__file__).parents[1] / "mente_laylay" / "neural" / "datasets"
    intents = {
        "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH", "OPEN_URL",
        "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL", "FILE_SEARCH", "FILE_READ",
        "WEATHER", "LIST_TABS",
    }
    dev = carregar_jsonl(base / "dev_v0.jsonl", intents_permitidas=intents)
    frozen = carregar_jsonl(base / "frozen_v0.jsonl", intents_permitidas=intents)
    onda = carregar_jsonl(
        base / "candidatos" / "onda_balanceada_v1.jsonl",
        intents_permitidas=intents,
    )
    lote = carregar_jsonl(
        base / "candidatos" / "musica_natural_modal_v2.jsonl",
        intents_permitidas=intents,
    )

    falhas_reais = [item for item in lote if item["source"] == "REAL_FAILURE"]
    comandos = [item for item in lote if item["is_command"]]
    hard_negatives = [item for item in lote if item["source"] == "HARD_NEGATIVE"]

    assert falhas_reais == [{
        "text": "pode colocar glimpse of us",
        "intent": "MUSIC_SEARCH",
        "is_command": True,
        "negated": False,
        "action": "search",
        "family": "musica_modal_colocar_real_v2",
        "source": "REAL_FAILURE",
        "domain": "music",
    }]
    assert len(lote) == 29
    assert len(comandos) == 19
    assert sum(item["negated"] for item in comandos) == 5
    assert len(hard_negatives) == 10
    assert all(item["intent"] == "NONE" for item in hard_negatives)
    assert all(item["text"] != falhas_reais[0]["text"] for item in dev)
    assert auditar_leakage_dataset([*dev, *onda, *lote], frozen)["aprovado"] is True


def test_promocao_rejeita_melhora_de_accuracy_que_piora_falso_comando() -> None:
    estavel = {
        "intent_accuracy": 0.80,
        "false_command_rate": 0.02,
        "command_precision": 0.94,
        "negation_accuracy": 0.96,
    }
    arriscado = {
        "intent_accuracy": 0.90,
        "false_command_rate": 0.05,
        "command_precision": 0.94,
        "negation_accuracy": 0.97,
    }
    seguro = {
        "intent_accuracy": 0.84,
        "false_command_rate": 0.01,
        "command_precision": 0.95,
        "negation_accuracy": 0.97,
    }

    assert avaliar_promocao(estavel, arriscado)["promover"] is False
    assert avaliar_promocao(estavel, seguro)["promover"] is True


def test_promocao_rejeita_candidato_identico_sem_aprendizado_novo() -> None:
    metricas = {
        "intent_accuracy": 0.95,
        "false_command_rate": 0.0,
        "command_precision": 1.0,
        "command_recall": 1.0,
        "negation_accuracy": 0.95,
        "missed_negation_rate": 0.0,
    }

    decisao = avaliar_promocao(metricas, dict(metricas))

    assert decisao["promover"] is False
    assert decisao["motivos"] == ["sem_aprendizado_novo"]


def test_promocao_reconhece_troca_de_estrategia_como_experimento_novo() -> None:
    metricas = {
        "intent_accuracy": 0.9,
        "false_command_rate": 0.0,
        "command_precision": 1.0,
        "command_recall": 0.9,
        "negation_accuracy": 0.95,
        "missed_negation_rate": 0.0,
    }

    decisao = avaliar_promocao(
        metricas,
        dict(metricas),
        evidencia_aprendizado={"estrategia_alterada": True},
    )

    assert decisao["aprendizado_novo"] is True
    assert "sem_aprendizado_novo" not in decisao["motivos"]


def test_promocao_reconhece_troca_da_arquitetura_de_comando() -> None:
    metricas = {
        "intent_accuracy": 0.9,
        "false_command_rate": 0.0,
        "command_precision": 1.0,
        "command_recall": 0.9,
        "negation_accuracy": 0.95,
        "missed_negation_rate": 0.0,
    }

    decisao = avaliar_promocao(
        metricas,
        dict(metricas),
        evidencia_aprendizado={"arquitetura_comando_alterada": True},
    )

    assert decisao["aprendizado_novo"] is True
    assert "sem_aprendizado_novo" not in decisao["motivos"]


def test_ciclo_sem_dados_novos_nao_substitui_modelo_ativo(tmp_path) -> None:
    primeiro = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=True,
        versao="teste-primeiro",
    )
    segundo = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=True,
        versao="teste-vazio",
    )

    assert primeiro["promovido"] is True
    assert segundo["decisao"]["motivos"] == ["sem_aprendizado_novo"]
    assert segundo["promovido"] is False
    assert carregar_modelo(tmp_path / "modelo_ativo.joblib").versao == "teste-primeiro"


def test_lote_candidato_e_avaliado_sem_contaminar_dev_ou_promover(tmp_path) -> None:
    dev_path = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
        / "dev_v0.jsonl"
    )
    dev_antes = dev_path.read_bytes()
    lote = tmp_path / "volume_piloto.jsonl"
    lote.write_text(
        json.dumps(
            {
                "text": "pode diminuir um pouco o áudio",
                "intent": "VOLUME",
                "is_command": True,
                "negated": False,
                "action": "down",
                "family": "volume_piloto_staged",
                "source": "MANUAL_PARAPHRASE",
                "domain": "audio",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    relatorio = executar_ciclo_treino(
        pasta_estado=tmp_path / "estado",
        promover_se_aprovado=False,
        versao="teste-lote-staged",
        lotes_candidatos=[lote],
        estrategia="sgd_log_loss",
        arquitetura_comando="intent_gated",
        limiares_comando_por_intent={"volume": 0.6},
    )

    assert relatorio["dataset"]["exemplos_candidatos"] == 1
    assert relatorio["dataset"]["lotes_candidatos_sha256"]
    assert relatorio["lote_candidato_apenas_avaliacao"] is True
    assert relatorio["estrategia"] == "sgd_log_loss"
    assert relatorio["arquitetura_comando"] == "intent_gated"
    assert relatorio["limiares_comando_por_intent"] == {"VOLUME": 0.6}
    assert relatorio["configuracao_experimental"] is True
    assert relatorio["promovido"] is False
    assert dev_path.read_bytes() == dev_antes

    with pytest.raises(ValueError, match="não pode promover"):
        executar_ciclo_treino(
            pasta_estado=tmp_path / "estado-promocao",
            promover_se_aprovado=True,
            versao="teste-lote-promocao-bloqueada",
            lotes_candidatos=[lote],
        )


def test_lote_candidato_com_leakage_falha_antes_de_criar_modelo(tmp_path) -> None:
    lote = tmp_path / "lote_com_leakage.jsonl"
    lote.write_text(
        json.dumps(
            {
                "text": "dá uma diminuída nisso",
                "intent": "VOLUME",
                "is_command": True,
                "negated": False,
                "action": "down",
                "family": "familia_nova_mas_texto_vazado",
                "source": "MANUAL_PARAPHRASE",
                "domain": "audio",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    estado = tmp_path / "estado"

    with pytest.raises(ValueError, match="reprovado por leakage"):
        executar_ciclo_treino(
            pasta_estado=estado,
            versao="teste-leakage",
            lotes_candidatos=[lote],
        )

    assert not (estado / "modelo_candidato.joblib").exists()


def test_arquitetura_de_comando_experimental_nao_pode_promover(tmp_path) -> None:
    with pytest.raises(ValueError, match="configuração experimental"):
        executar_ciclo_treino(
            pasta_estado=tmp_path,
            promover_se_aprovado=True,
            versao="teste-intent-gated-nao-promove",
            arquitetura_comando="intent_gated",
        )

    assert not (tmp_path / "modelo_candidato.joblib").exists()

    with pytest.raises(ValueError, match="configuração experimental"):
        executar_ciclo_treino(
            pasta_estado=tmp_path / "limiar-intent",
            promover_se_aprovado=True,
            versao="teste-limiar-intent-nao-promove",
            limiares_comando_por_intent={"IOT_CONTROL": 0.605},
        )


def test_dado_novo_so_autoriza_uma_promocao_sem_regressao(tmp_path) -> None:
    executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=True,
        versao="teste-base",
    )
    experiencia = BufferExperienciasNeurais(
        tmp_path / "experiencias.jsonl",
    ).registrar_correcao(
        texto_original="abaixa o volume agora por favor",
        intent_errada="NONE",
        intent_correta="VOLUME",
        params_corretos={"acao": "down"},
        texto_correcao="eu pedi para abaixar o volume",
        confirmada_por_execucao=True,
    )
    RegistroRevisoesCorrecoesNeurais(
        tmp_path / "revisoes_correcoes.jsonl"
    ).registrar_decisao(
        correcao_id=experiencia["id"],
        decisao="aprovada",
        origem="teste",
    )

    com_dado_novo = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=True,
        versao="teste-aprendeu",
    )
    repetido = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=True,
        versao="teste-repetido",
    )

    assert com_dado_novo["evidencia_aprendizado"]["dados_aprendidos_novos"] is True
    assert com_dado_novo["promovido"] is True
    assert repetido["evidencia_aprendizado"]["dados_aprendidos_novos"] is False
    assert repetido["decisao"]["motivos"] == ["sem_aprendizado_novo"]
    assert repetido["promovido"] is False
    assert carregar_modelo(tmp_path / "modelo_ativo.joblib").versao == "teste-aprendeu"


def test_correcao_apta_sem_revisao_nao_entra_no_treino(tmp_path) -> None:
    BufferExperienciasNeurais(
        tmp_path / "experiencias.jsonl",
    ).registrar_correcao(
        texto_original="abaixa o volume agora por favor",
        intent_errada="NONE",
        intent_correta="VOLUME",
        params_corretos={"acao": "down"},
        texto_correcao="eu pedi para abaixar o volume",
        confirmada_por_execucao=True,
    )

    relatorio = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=False,
        versao="teste-revisao-pendente",
    )

    assert relatorio["dataset"]["correcoes_fortes"] == 0
    assert relatorio["dataset"]["correcoes_pendentes_revisao"] == 1
    assert relatorio["dataset"]["correcoes_aprovadas"] == 0


def test_somente_correcao_aprovada_manualmente_entra_no_treino(tmp_path) -> None:
    experiencia = BufferExperienciasNeurais(
        tmp_path / "experiencias.jsonl",
    ).registrar_correcao(
        texto_original="abaixa o volume agora por favor",
        intent_errada="NONE",
        intent_correta="VOLUME",
        params_corretos={"acao": "down"},
        texto_correcao="eu pedi para abaixar o volume",
        confirmada_por_execucao=True,
    )
    (tmp_path / "revisoes_correcoes.jsonl").write_text(
        json.dumps(
            {
                "correcao_id": experiencia["id"],
                "decisao": "aprovada",
                "origem": "teste_manual",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    relatorio = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=False,
        versao="teste-revisao-aprovada",
    )

    assert relatorio["dataset"]["correcoes_fortes"] == 1
    assert relatorio["dataset"]["correcoes_pendentes_revisao"] == 0
    assert relatorio["dataset"]["correcoes_aprovadas"] == 1


def test_correcao_rejeitada_permanece_no_historico_mas_nao_entra_no_treino(
    tmp_path,
) -> None:
    experiencia = BufferExperienciasNeurais(
        tmp_path / "experiencias.jsonl",
    ).registrar_correcao(
        texto_original="fecha o navegador",
        intent_errada="CLOSE_TAB",
        intent_correta="CLOSE_APP",
        params_corretos={"acao": "close"},
        texto_correcao="eu pedi para fechar o aplicativo",
        confirmada_por_execucao=True,
    )
    (tmp_path / "revisoes_correcoes.jsonl").write_text(
        json.dumps(
            {
                "correcao_id": experiencia["id"],
                "decisao": "rejeitada",
                "motivo": "execucao posterior nao correlacionada",
                "origem": "teste_manual",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    relatorio = executar_ciclo_treino(
        pasta_estado=tmp_path,
        promover_se_aprovado=False,
        versao="teste-revisao-rejeitada",
    )

    assert relatorio["dataset"]["correcoes_fortes"] == 0
    assert relatorio["dataset"]["correcoes_rejeitadas"] == 1
    assert experiencia["id"] in (
        tmp_path / "experiencias.jsonl"
    ).read_text(encoding="utf-8")


def test_cobertura_mede_meta_por_intent_acao_sem_contar_challenge_como_treino() -> None:
    dev = [
        {
            "text": "abaixa o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "down",
            "family": "volume_down_a",
            "source": "NORMAL_COMMAND",
            "domain": "audio",
        },
        {
            "text": "não abaixa o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": True,
            "action": "down",
            "family": "volume_down_negado_a",
            "source": "HARD_NEGATIVE",
            "domain": "audio",
        },
        {
            "text": "o volume está alto",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "family": "volume_comentario_a",
            "source": "HARD_NEGATIVE",
            "domain": "audio",
        },
    ]
    frozen = [
        {
            "text": "dá uma diminuída nisso",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "down",
            "family": "volume_down_b",
            "source": "MANUAL_PARAPHRASE",
            "domain": "audio",
        }
    ]

    relatorio = analisar_cobertura_dataset(
        dev,
        frozen,
        intents_catalogadas={"VOLUME", "APP_OPEN"},
        meta_minima_dev=3,
        meta_maxima_dev=4,
    )

    comando = relatorio["por_comando"]["VOLUME:down"]
    assert comando["dev"] == 2
    assert comando["frozen"] == 1
    assert comando["total"] == 3
    assert comando["negados_dev"] == 1
    assert comando["familias_dev"] == 2
    assert comando["faltam_para_meta_dev"] == 1
    assert comando["status_meta_dev"] == "abaixo_da_meta"
    assert relatorio["intents_sem_exemplos"] == ["APP_OPEN"]
    assert relatorio["nao_comandos"]["dev"] == 1
    assert relatorio["pronto_para_ampliar_influencia"] is False


def test_cobertura_sinaliza_faixa_ideal_e_excesso_sem_autorizar_execucao() -> None:
    def exemplo(numero: int, *, intent: str, action: str) -> dict:
        return {
            "text": f"exemplo {intent} {action} {numero}",
            "intent": intent,
            "is_command": True,
            "negated": False,
            "action": action,
            "family": f"familia_{numero}",
            "source": "MANUAL_PARAPHRASE",
            "domain": "teste",
        }

    dev = [
        *(exemplo(i, intent="VOLUME", action="down") for i in range(3)),
        *(exemplo(i, intent="VOLUME", action="up") for i in range(5)),
    ]
    relatorio = analisar_cobertura_dataset(
        dev,
        [],
        intents_catalogadas={"VOLUME"},
        meta_minima_dev=3,
        meta_maxima_dev=4,
    )

    assert relatorio["por_comando"]["VOLUME:down"]["status_meta_dev"] == (
        "faixa_planejada"
    )
    assert relatorio["por_comando"]["VOLUME:up"]["status_meta_dev"] == (
        "acima_da_faixa_planejada"
    )
    assert relatorio["contrato"]["autoriza_execucao"] is False
    assert relatorio["contrato"]["cobertura_nao_prova_qualidade"] is True


def test_cobertura_exige_diversidade_negacoes_e_hard_negatives_no_dev() -> None:
    dev = [
        {
            "text": "abaixa o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "down",
            "family": "volume_direto",
            "source": "NORMAL_COMMAND",
            "domain": "audio",
        },
        {
            "text": "diminui o som",
            "intent": "VOLUME",
            "is_command": True,
            "negated": False,
            "action": "down",
            "family": "volume_direto",
            "source": "MANUAL_PARAPHRASE",
            "domain": "audio",
        },
        {
            "text": "não abaixa o volume",
            "intent": "VOLUME",
            "is_command": True,
            "negated": True,
            "action": "down",
            "family": "volume_negado",
            "source": "HARD_NEGATIVE",
            "domain": "audio",
        },
        {
            "text": "o volume está alto",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "family": "volume_comentario",
            "source": "HARD_NEGATIVE",
            "domain": "audio",
        },
    ]
    frozen = [
        {
            "text": "não reduz o áudio",
            "intent": "VOLUME",
            "is_command": True,
            "negated": True,
            "action": "down",
            "family": "volume_negado_frozen",
            "source": "HARD_NEGATIVE",
            "domain": "audio",
        },
        {
            "text": "esse som ficou forte",
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "family": "volume_comentario_frozen",
            "source": "HARD_NEGATIVE",
            "domain": "audio",
        },
    ]

    relatorio = analisar_cobertura_dataset(
        dev,
        frozen,
        intents_catalogadas={"VOLUME"},
        comandos_planejados=[
            {
                "intent": "VOLUME",
                "action": "down",
                "domain": "audio",
                "risk": "LOW_RISK",
                "operational_influence_enabled": False,
            }
        ],
        meta_minima_dev=3,
        meta_maxima_dev=4,
        meta_minima_familias_dev=3,
        meta_minima_negados_dev=2,
        meta_minima_hard_negatives_dev_por_dominio=2,
    )

    comando = relatorio["por_comando"]["VOLUME:down"]
    assert comando["status_meta_dev"] == "faixa_planejada"
    assert comando["faltam_familias_dev"] == 1
    assert comando["faltam_negados_dev"] == 1
    assert comando["cotas_coleta_atendidas"] is False
    assert relatorio["por_dominio"]["audio"]["hard_negatives_dev"] == 1
    assert relatorio["por_dominio"]["audio"]["faltam_hard_negatives_dev"] == 1
    assert relatorio["todos_comandos_com_cotas_minimas_dev"] is False
    assert relatorio["todos_dominios_com_hard_negatives_minimos_dev"] is False
    assert relatorio["contrato"]["cotas_nao_provam_qualidade"] is True


def test_hard_negative_de_dominio_sem_variante_nao_cria_gate_acidental() -> None:
    def hard_negative(texto: str, dominio: str, familia: str) -> dict:
        return {
            "text": texto,
            "intent": "NONE",
            "is_command": False,
            "negated": False,
            "action": "none",
            "family": familia,
            "source": "HARD_NEGATIVE",
            "domain": dominio,
        }

    relatorio = analisar_cobertura_dataset(
        [
            hard_negative("o som está alto", "audio", "audio_comentario"),
            hard_negative("ontem mexi no volume", "audio", "audio_relato"),
            hard_negative("hoje foi um dia longo", "conversation", "conversa_ood"),
        ],
        [],
        intents_catalogadas={"VOLUME"},
        comandos_planejados=[
            {
                "intent": "VOLUME",
                "action": "down",
                "domain": "audio",
                "risk": "LOW_RISK",
                "operational_influence_enabled": False,
            }
        ],
        meta_minima_dev=1,
        meta_maxima_dev=2,
        meta_minima_familias_dev=1,
        meta_minima_negados_dev=1,
        meta_minima_hard_negatives_dev_por_dominio=2,
    )

    assert relatorio["por_dominio"]["audio"]["cota_aplicavel"] is True
    assert relatorio["por_dominio"]["conversation"]["cota_aplicavel"] is False
    assert relatorio["por_dominio"]["conversation"]["faltam_hard_negatives_dev"] == 0
    assert relatorio["todos_dominios_com_hard_negatives_minimos_dev"] is True


def test_cobertura_nao_transforma_acao_none_negada_em_variante_de_comando() -> None:
    relatorio = analisar_cobertura_dataset(
        [
            {
                "text": "não mexe em nenhum dispositivo",
                "intent": "IOT_CONTROL",
                "is_command": True,
                "negated": True,
                "action": "none",
                "family": "iot_negado_geral",
                "source": "HARD_NEGATIVE",
                "domain": "iot",
            }
        ],
        [],
        intents_catalogadas={"IOT_CONTROL"},
        meta_minima_dev=3,
        meta_maxima_dev=4,
    )

    assert "IOT_CONTROL:none" not in relatorio["por_comando"]
    assert relatorio["comandos_sem_acao"]["dev"] == 1
    assert relatorio["por_intent"]["IOT_CONTROL"]["dev"] == 1


def test_catalogo_explicito_revela_variante_planejada_ainda_sem_exemplos() -> None:
    catalogo = validar_catalogo_variantes(
        [
            {
                "intent": "VOLUME",
                "action": "down",
                "domain": "audio",
                "risk": "LOW_RISK",
                "operational_influence_enabled": False,
            },
            {
                "intent": "VOLUME",
                "action": "up",
                "domain": "audio",
                "risk": "LOW_RISK",
                "operational_influence_enabled": False,
            },
        ],
        intents_catalogadas={"VOLUME"},
    )
    relatorio = analisar_cobertura_dataset(
        [
            {
                "text": "abaixa o volume",
                "intent": "VOLUME",
                "is_command": True,
                "negated": False,
                "action": "down",
                "family": "volume_down",
                "source": "NORMAL_COMMAND",
                "domain": "audio",
            }
        ],
        [],
        intents_catalogadas={"VOLUME"},
        comandos_planejados=catalogo,
        meta_minima_dev=3,
        meta_maxima_dev=4,
    )

    assert relatorio["por_comando"]["VOLUME:up"]["dev"] == 0
    assert relatorio["por_comando"]["VOLUME:up"]["declarada"] is True
    assert relatorio["por_comando"]["VOLUME:up"]["faltam_para_meta_dev"] == 3
    assert relatorio["comandos_observados_nao_declarados"] == []


def test_catalogo_declara_list_windows_apenas_para_cobertura_shadow() -> None:
    base = (
        __import__("pathlib").Path(__file__).parents[1]
        / "mente_laylay"
        / "neural"
        / "datasets"
    )
    manifesto = carregar_manifesto_variantes(
        base / "catalogo_variantes_v0.json",
        intents_catalogadas={
            "VOLUME", "APP_OPEN", "CLOSE_APP", "CLOSE_TAB", "SEARCH",
            "OPEN_URL", "MUSIC_SEARCH", "MEDIA_CONTROL", "IOT_CONTROL",
            "FILE_SEARCH", "FILE_READ", "WEATHER", "LIST_TABS",
            "LIST_WINDOWS",
        },
    )

    variante = next(
        item for item in manifesto["variants"]
        if item["intent"] == "LIST_WINDOWS" and item["action"] == "list"
    )
    assert variante == {
        "intent": "LIST_WINDOWS",
        "action": "list",
        "domain": "app",
        "risk": "LOW_RISK",
        "operational_influence_enabled": False,
    }
    assert manifesto["operational_influence_enabled"] is False


def test_catalogo_de_variantes_rejeita_acao_none_e_influencia_habilitada() -> None:
    base = {
        "intent": "IOT_CONTROL",
        "domain": "iot",
        "risk": "REVERSIBLE",
        "operational_influence_enabled": False,
    }
    with pytest.raises(ValueError, match="action none"):
        validar_catalogo_variantes(
            [{**base, "action": "none"}],
            intents_catalogadas={"IOT_CONTROL"},
        )
    with pytest.raises(ValueError, match="influência operacional"):
        validar_catalogo_variantes(
            [{**base, "action": "on", "operational_influence_enabled": True}],
            intents_catalogadas={"IOT_CONTROL"},
        )


def test_manifesto_fixa_cotas_de_coleta_sem_habilitar_influencia() -> None:
    manifesto = validar_manifesto_variantes(
        {
            "schema_version": 1,
            "purpose": "dataset_coverage_only",
            "operational_influence_enabled": False,
            "target_dev_examples_per_variant": {"minimum": 150, "maximum": 200},
            "quality_targets": {
                "minimum_linguistic_families_dev_per_variant": 12,
                "minimum_negated_dev_per_variant": 15,
                "minimum_hard_negatives_dev_per_domain": 30,
            },
            "variants": [
                {
                    "intent": "VOLUME",
                    "action": "down",
                    "domain": "audio",
                    "risk": "LOW_RISK",
                    "operational_influence_enabled": False,
                }
            ],
        },
        intents_catalogadas={"VOLUME"},
    )

    assert manifesto["target_dev_examples_per_variant"] == {
        "minimum": 150,
        "maximum": 200,
    }
    assert manifesto["quality_targets"]["minimum_negated_dev_per_variant"] == 15
    assert manifesto["operational_influence_enabled"] is False

    with pytest.raises(ValueError, match="influência operacional"):
        validar_manifesto_variantes(
            {
                **manifesto,
                "operational_influence_enabled": True,
            },
            intents_catalogadas={"VOLUME"},
        )


def test_auditoria_reprova_parafrase_quase_identica_entre_dev_e_challenge() -> None:
    dev = [
        {
            "text": "isso está alto demais, dá uma baixada",
            "intent": "VOLUME",
            "family": "volume_indireto_a",
        },
        {
            "text": "abre o chrome",
            "intent": "APP_OPEN",
            "family": "app_abrir_a",
        },
    ]
    frozen = [
        {
            "text": "isso tá alto demais, dá uma baixada",
            "intent": "VOLUME",
            "family": "volume_indireto_b",
        }
    ]

    relatorio = auditar_leakage_dataset(dev, frozen, limiar_similaridade=0.9)

    assert relatorio["aprovado"] is False
    assert relatorio["totais"]["pares_quase_duplicados"] == 1
    assert relatorio["quase_duplicados"][0]["similaridade"] > 0.96
    assert relatorio["quase_duplicados"][0]["mesmo_intent"] is True
    assert relatorio["contrato"]["altera_dataset"] is False


def test_auditoria_reprova_familia_compartilhada_mesmo_sem_texto_parecido() -> None:
    relatorio = auditar_leakage_dataset(
        [{"text": "abaixa o volume", "intent": "VOLUME", "family": "familia_x"}],
        [{"text": "deixa o som menor", "intent": "VOLUME", "family": "familia_x"}],
        limiar_similaridade=0.99,
    )

    assert relatorio["familias_compartilhadas"] == ["familia_x"]
    assert relatorio["aprovado"] is False


def test_dev_e_frozen_reais_nao_possuem_leakage_lexical_detectado() -> None:
    base = __import__("pathlib").Path(__file__).parents[1] / "mente_laylay" / "neural"
    catalogo = __import__(
        "mente_laylay.especialistas.capacidades",
        fromlist=["intents_registradas"],
    ).intents_registradas()
    dev = carregar_jsonl(
        base / "datasets" / "dev_v0.jsonl",
        intents_permitidas=catalogo,
    )
    frozen = carregar_jsonl(
        base / "datasets" / "frozen_v0.jsonl",
        intents_permitidas=catalogo,
    )

    relatorio = auditar_leakage_dataset(dev, frozen, limiar_similaridade=0.9)

    assert relatorio["aprovado"] is True, relatorio
