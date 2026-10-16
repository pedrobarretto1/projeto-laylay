"""A fala entregue retém sua fonte histórica sem adquirir poder operacional."""
from dataclasses import replace
import time

import pytest

from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, recuperar_evidencia_da_fala,
    renovar_registro_semantico_sessao, resumo_registro_semantico_para_prompt,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime
from mente_laylay.personalidade.diretor_fala import dirigir_fala
from mente_laylay.memoria_mental.continuidade_contexto import registrar_continuidade_da_fala


def receipt(identidade="acao-a", *, confirmado=True):
    return ResultadoAcao(intent="MEDIA_CONTROL", params={"acao": "pause"},
        status="pausado" if confirmado else "falha_execucao", alvo="música",
        id_solicitacao=identidade, origem="executor", executou=confirmado,
        confirmado=confirmado, evidencia_confirmacao="evidencia-" + identidade)


def guardar(registro=None, *, identidade="fala-a", fala="Pausei a música.", resultados=None,
            canal="texto_publicado", agora=100.0):
    return registrar_fala_observada(registro, ocorrencia_id=identidade,
        turno_id="turno-origem", fala=fala,
        resultados=(receipt(),) if resultados is None else resultados, canal=canal, agora=agora)


def consultar(registro, *, texto='Quando você disse "Pausei a música.", em que se baseou?', agora=101.0):
    return recuperar_evidencia_da_fala(texto, {"registro_semantico": registro,
        "ultima_acao_contrato": receipt("outra-acao").como_dict()}, agora=agora)


def test_receipt_da_propria_ocorrencia_sobrevive_a_outra_acao_sem_promover_texto_a_fato():
    registro = guardar()
    evidencia = consultar(registro)
    assert evidencia["falas"][0]["resultados"][0]["id_solicitacao"] == "acao-a"
    assert "outra-acao" not in str(evidencia)
    assert evidencia["autoriza_execucao"] is False
    assert not registro["alegacoes"]
    assert "Pausei a música." not in resumo_registro_semantico_para_prompt(registro, agora=101)


def test_composto_conserva_falha_parcial_e_snapshots_nao_compartilham_mutacao():
    registro = guardar(resultados=(receipt(), receipt("acao-b", confirmado=False)))
    evidencia = consultar(registro)
    resultados = evidencia["falas"][0]["resultados"]
    assert [r["confirmado"] for r in resultados] == [True, False]
    resultados[0]["confirmado"] = False
    assert consultar(registro)["falas"][0]["resultados"][0]["confirmado"] is True


def test_fala_sem_receipt_nao_empresta_confirmacao_da_ultima_acao():
    evidencia = consultar(guardar(resultados=()))
    assert evidencia["falas"][0]["resultados"] == []
    assert evidencia["autoriza_execucao"] is False


def test_estado_ja_satisfeito_nao_vira_nova_execucao_no_historico():
    idempotente = replace(receipt(), executou=False, confirmado=True, status="ja_satisfeito")
    resultado = consultar(guardar(resultados=(idempotente,)))["falas"][0]["resultados"][0]
    assert resultado["confirmado"] is True and resultado["executou"] is False


def test_retencao_limitada_nao_reintroduz_fonte_removida():
    registro = None
    for indice in range(26):
        registro = guardar(registro, identidade=f"fala-{indice}", fala=f"Resposta histórica número {indice}.")
    assert len(registro["falas_observadas"]) == 24
    assert not consultar(registro, texto='Quando disse "Resposta histórica número 0."?')
    assert consultar(registro, texto='Quando disse "Resposta histórica número 25."?')


@pytest.mark.parametrize("invalido", [
    {"origem": "executor", "id_solicitacao": "fabricado"},
    replace(receipt(), origem="llm"), replace(receipt(), id_solicitacao=""),
])
def test_resultado_nao_tipado_ou_sem_origem_nao_adquire_vinculo(invalido):
    with pytest.raises(ValueError, match="receipt tipado"):
        guardar(resultados=(invalido,))


def test_dois_canais_da_mesma_ocorrencia_nao_duplicam_nem_renovam_validade():
    registro = guardar()
    novo = guardar(registro, canal="audio_reproducao_confirmada", agora=200)
    assert len(novo["falas_observadas"]) == 1
    assert novo["falas_observadas"][0]["canais"] == ["texto_publicado", "audio_reproducao_confirmada"]
    assert novo["falas_observadas"][0]["ts"] == 100
    assert registro["falas_observadas"][0]["canais"] == ["texto_publicado"]


@pytest.mark.parametrize("alteracao", [
    {"fala": "Agora apaguei o arquivo."},
    {"resultados": (receipt("outro-receipt"),)},
])
def test_publicacao_tardia_nao_reescreve_fonte_ou_conteudo_da_ocorrencia(alteracao):
    with pytest.raises(ValueError, match="reescrever"):
        guardar(guardar(), **alteracao)


@pytest.mark.parametrize("agora", [99, 1001, float("nan"), float("inf")])
def test_fonte_expirada_futura_ou_relogio_invalido_nao_sustenta_fala(agora):
    assert not consultar(guardar(), agora=agora)


def test_mesma_citacao_em_ocorrencias_distintas_expoe_ambiguidade():
    registro = guardar()
    registro = guardar(registro, identidade="fala-b", resultados=(receipt("acao-b"),), agora=101)
    evidencia = consultar(registro, agora=102)
    assert evidencia["referencia_ambigua"] is True
    assert {f["resultados"][0]["id_solicitacao"] for f in evidencia["falas"]} == {"acao-a", "acao-b"}


def test_renovacao_nao_restaura_fontes_efemeras_de_outra_sessao():
    registro = renovar_registro_semantico_sessao(guardar(), agora=102)
    assert not consultar(registro, agora=103)
    mental, _, _ = renovar_contexto_sessao({"registro_semantico": guardar()}, {}, [],
        motivo="troca_conversa", ativa=True, agora=102)
    assert not consultar(mental["registro_semantico"], agora=103)


def test_assunto_independente_nao_recupera_receipt_por_coincidencia_de_dominio():
    assert not consultar(guardar(), texto="Você gosta de música?")


def test_referencia_anaforica_usa_o_seletor_contextual_existente():
    agora = time.time()
    registro = guardar(agora=agora)
    mente = {"registro_semantico": registro, "ultima_resposta": "Pausei a música.",
        "continuidade_fala_ts": agora, "turno_atual": {"modalidade": "pergunta"}}
    evidencia = recuperar_evidencia_da_fala("Por que você disse isso?", mente, agora=agora)
    assert evidencia["falas"][0]["resultados"][0]["id_solicitacao"] == "acao-a"


class VozPendente:
    def __init__(self):
        self.callback = None

    def falar(self, *_args, **kwargs):
        self.callback = kwargs.get("_ao_concluir_entrega")
        return True


def runtime_audio():
    estado = criar_estado_compartilhado_runtime()
    estado.atualizar_campos("mental", turno_atual={"id": "origem"},
        plano_turno_atual={"id": "origem", "requer_execucao": True}, sessao_conversa_ts=10.0)
    voz = VozPendente()
    runtime = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado, "_voz_runtime": voz,
        "_dirigir_fala_mente": dirigir_fala,
        "_registrar_continuidade_da_fala_mente": registrar_continuidade_da_fala,
        "print": lambda _: None,
    })
    return runtime, estado, voz


def test_fila_aceita_nao_confirma_entrega_e_callback_usa_a_ocorrencia_original():
    runtime, estado, voz = runtime_audio()
    assert runtime.falar_resultado_operacional(receipt(), "Pausei a música.")
    assert not estado.obter_copia("mental", "registro_semantico", {}).get("falas_observadas")
    estado.atualizar_campos("mental", turno_atual={"id": "novo"},
        plano_turno_atual={"id": "novo", "requer_execucao": False})
    voz.callback(True, "Pausei a música.")
    falas = estado.obter_copia("mental", "registro_semantico", {})["falas_observadas"]
    assert len(falas) == 1 and falas[0]["turno_id"] == "origem"
    assert estado.mental["turno_atual"]["id"] == "novo"


def test_falha_de_audio_nao_produz_fonte_comunicativa():
    runtime, estado, voz = runtime_audio()
    runtime.falar_resultado_operacional(receipt(), "Pausei a música.")
    voz.callback(False, "Pausei a música.")
    assert not estado.obter_copia("mental", "registro_semantico", {}).get("falas_observadas")


def test_callback_de_outro_conteudo_nao_empresta_receipts_da_fala_original():
    runtime, estado, voz = runtime_audio()
    runtime.falar_resultado_operacional(receipt(), "Pausei a música.")
    voz.callback(True, "Outro candidato foi reproduzido.")
    assert not estado.obter_copia("mental", "registro_semantico", {}).get("falas_observadas")


def test_callback_de_audio_de_outro_chat_nao_contamina_registro_atual():
    runtime, estado, voz = runtime_audio()
    runtime.falar_resultado_operacional(receipt(), "Pausei a música.")
    mental, _, _ = renovar_contexto_sessao(estado.retrato_dominio("mental"), {}, [],
        motivo="troca_conversa", ativa=True, agora=20.0)
    estado.substituir("mental", mental)
    voz.callback(True, "Pausei a música.")
    assert not estado.obter_copia("mental", "registro_semantico", {})["falas_observadas"]
