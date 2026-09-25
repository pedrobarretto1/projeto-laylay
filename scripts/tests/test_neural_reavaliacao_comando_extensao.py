from __future__ import annotations

from mente_laylay.neural.modelo import (
    ExtensaoIntentNeural,
    ModeloNeuralComandos,
    enriquecer_texto_features_comando,
    enriquecer_texto_features_comando_pragmatica_estado_v6_sparse,
    enriquecer_texto_features_comando_contexto_v7_sparse,
    extrair_clausula_operacional_contexto_v1,
)
from mente_laylay.neural.runtime import EspecialistaNeuralComandosRuntime


class _Binario:
    classes_ = [False, True]

    def __init__(self, positivo: bool, prob: float = 0.95) -> None:
        self.positivo = positivo
        self.prob = prob

    def predict(self, entradas):
        return [self.positivo for _ in entradas]

    def predict_proba(self, entradas):
        p_true = self.prob if self.positivo else 1.0 - self.prob
        return [[1.0 - p_true, p_true] for _ in entradas]


def _modelo(*, comando: bool, reavaliar: bool) -> ModeloNeuralComandos:
    head = _Binario(comando)
    modelo = ModeloNeuralComandos(
        versao="teste-reavaliacao",
        cabeca_intent=head,
        cabeca_comando=head,
        cabeca_negacao=_Binario(False),
        cabeca_acao=head,
        limiar_comando=0.65,
        reavaliar_comando_apos_extensao=reavaliar,
    )
    modelo.extensoes_intent = {
        "VOLUME": ExtensaoIntentNeural(
            intent="VOLUME",
            action="down",
            detector=_Binario(True, 0.99),
            limiar=0.925,
            versao="estado-teste",
        )
    }
    return modelo


def _base(*, negated: bool = False) -> dict:
    return {
        "intent": "NONE",
        "gate_intent": "NONE",
        "params": {},
        "raw_action": "none",
        "is_command": False,
        "raw_is_command": False,
        "command_veto_reason": "intent_desconhecida",
        "command_probability": 0.10,
        "command_threshold": 0.65,
        "command_head_scope": "GLOBAL",
        "command_head_variant": "legado",
        "negated": negated,
        "ood": True,
        "ood_calibrated": False,
        "confidence": {
            "intent": 0.1, "intent_gate": 0.1, "command": 0.1,
            "negation": 0.99, "action": 0.1,
        },
    }
def test_flag_desligada_preserva_decisao_de_comando_legada():
    modelo = _modelo(comando=True, reavaliar=False)
    observado = modelo._aplicar_extensoes_intent("o volume está alto", _base())
    assert observado["intent"] == "VOLUME"
    assert observado["raw_action"] == "down"
    assert observado["raw_is_command"] is False
    assert observado["is_command"] is False
    assert observado.get("command_gate_recomputed_after_extension") is not True


def test_flag_ligada_exige_head_de_comando_independente():
    modelo = _modelo(comando=True, reavaliar=True)
    observado = modelo._aplicar_extensoes_intent("o volume está alto", _base())
    assert observado["intent"] == "VOLUME"
    assert observado["raw_action"] == "down"
    assert observado["raw_is_command"] is True
    assert observado["is_command"] is True
    assert observado["command_probability"] == 0.95
    assert observado["command_gate_recomputed_after_extension"] is True


def test_extensao_nao_inventa_comando_quando_head_recusa():
    modelo = _modelo(comando=False, reavaliar=True)
    observado = modelo._aplicar_extensoes_intent("o volume está alto", _base())
    assert observado["intent"] == "VOLUME"
    assert observado["raw_action"] == "down"
    assert observado["raw_is_command"] is False
    assert observado["is_command"] is False
def test_negacao_continua_bloqueando_execucao_apos_reavaliacao():
    modelo = _modelo(comando=True, reavaliar=True)
    observado = modelo._aplicar_extensoes_intent(
        "não abaixa o volume", _base(negated=True)
    )
    assert observado["is_command"] is True
    assert observado["negated"] is True
    assert EspecialistaNeuralComandosRuntime._comando_executavel(observado) is False


def test_v6_e_esparsa_e_nao_codifica_acao_ou_autoridade():
    texto = "o volume está alto demais"
    legado = enriquecer_texto_features_comando(texto)
    v6 = enriquecer_texto_features_comando_pragmatica_estado_v6_sparse(texto)
    assert "marcador_estado_excesso_audio" in v6
    assert v6 != legado
    assert "acao_down" not in v6
    assert "autoriza_execucao" not in v6
    assert "bloqueia_execucao" not in v6


def test_v6_sem_estado_novo_preserva_representacao_anterior():
    texto = "abaixa o volume"
    assert (
        enriquecer_texto_features_comando_pragmatica_estado_v6_sparse(texto)
        == enriquecer_texto_features_comando(texto)
    )


def test_ativador_estado_impede_extensao_fora_da_moldura():
    modelo = _modelo(comando=True, reavaliar=True)
    modelo.extensoes_intent["VOLUME"].ativacao = "estado_pragmatico_v1"
    base = _base()
    observado = modelo._aplicar_extensoes_intent("abre o chrome", base)
    assert observado is base


def test_ativador_estado_permite_extensao_quando_estado_esta_presente():
    modelo = _modelo(comando=True, reavaliar=True)
    modelo.extensoes_intent["VOLUME"].ativacao = "estado_pragmatico_v1"
    observado = modelo._aplicar_extensoes_intent("o volume está alto", _base())
    assert observado["intent"] == "VOLUME"
    assert observado["raw_action"] == "down"
    assert observado["is_command"] is True


def test_v7_marca_objetivo_indireto_sem_exigir_virgula():
    texto = "eu preciso pesquisar uma coisa no wikipedia"
    enriquecido = enriquecer_texto_features_comando_contexto_v7_sparse(texto)
    assert "marcador_objetivo_navegacao_indireto" in enriquecido


def test_v7_extrai_clausula_operacional_positiva():
    assert (
        extrair_clausula_operacional_contexto_v1(
            "estou com frio, desligue o ventilador"
        )
        == "desligue o ventilador"
    )


def test_v7_nao_recorta_clausula_operacional_negada():
    texto = "estou com frio, não desligue o ventilador"
    assert extrair_clausula_operacional_contexto_v1(texto) == texto


def test_reavaliacao_prefere_head_pos_extensao_sem_mudar_head_normal():
    modelo = _modelo(comando=False, reavaliar=True)
    modelo.cabecas_comando_extensao_por_intent["VOLUME"] = _Binario(True, 0.97)
    observado = modelo._aplicar_extensoes_intent("o volume está alto", _base())
    assert observado["is_command"] is True
    assert observado["command_probability"] == 0.97
    assert observado["command_head_variant"] == "extensao_dedicada_v1"


def test_ativador_off_exige_verbo_real_de_desligar():
    modelo = _modelo(comando=True, reavaliar=True)
    modelo.extensoes_intent = {
        "IOT_CONTROL": ExtensaoIntentNeural(
            intent="IOT_CONTROL",
            action="off",
            detector=_Binario(True, 0.99),
            limiar=0.925,
            versao="off-teste",
            ativacao="base_intent_off_verb_v1",
        )
    }
    base = _base()
    base["intent"] = "IOT_CONTROL"
    base["gate_intent"] = "IOT_CONTROL"
    assert modelo._aplicar_extensoes_intent("pode abrir a steam", base) is base
    observado = modelo._aplicar_extensoes_intent("desligue o ventilador", base)
    assert observado["intent"] == "IOT_CONTROL"
    assert observado["raw_action"] == "off"


def test_ativador_app_open_exige_sinal_de_abertura_e_bloqueia_fechamento():
    modelo = _modelo(comando=True, reavaliar=True)
    modelo.extensoes_intent = {
        "APP_OPEN": ExtensaoIntentNeural(
            intent="APP_OPEN",
            action="open",
            detector=_Binario(True, 0.99),
            limiar=0.88,
            versao="app-open-teste",
            ativacao="app_open_signal_v1",
        )
    }
    base = _base()
    assert modelo._aplicar_extensoes_intent(
        "já terminei no vscode, fecha pra mim", base
    ) is base
    observado = modelo._aplicar_extensoes_intent(
        "poderia abri a steam para mim", base
    )
    assert observado["intent"] == "APP_OPEN"
    assert observado["raw_action"] == "open"
