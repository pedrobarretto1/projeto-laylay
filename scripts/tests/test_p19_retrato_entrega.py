"""Expressão publicada é temporária e não confere autoridade causal."""

from dataclasses import FrozenInstanceError
import threading
import time

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.memoria_mental.conversas_runtime import capturar_contexto_conversa
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.retrato_entrega import (
    criar_retrato_entrega_fala,
    ler_retrato_entrega_fala,
)


def _estado_causal():
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="efeito confirmado",
        evidencia_ref="resultado:geral:confirmado", natureza_evidencia="fato_observado",
        permite_expressao=True, emocao="irritada", nivel=1, ts=100.0,
    )
    return aplicar_evento_emocional({}, evento, agora=100.0)


def test_retrato_publicado_nao_muda_com_causa_nova_nem_renova_validade():
    estado = _estado_causal()
    retrato = criar_retrato_entrega_fala(estado, mensagem_id="turno:A", agora=101.0)
    estado["current_emotion"] = "alegre"
    estado["emotion_level"] = 3
    estado["episodio_emocional"]["evidencia_ref"] = "resultado:B"

    assert (retrato.emocao, retrato.nivel, retrato.evidencia_ref) == (
        "irritada", 1, "resultado:geral:confirmado",
    )
    with pytest.raises(FrozenInstanceError):
        retrato.nivel = 3
    assert ler_retrato_entrega_fala(retrato.como_dict()) == retrato
    assert criar_retrato_entrega_fala(_estado_causal(), agora=500.0).emocao == "calma"


@pytest.mark.parametrize("estado", [None, [], {"current_emotion": "brava"},
    {"current_emotion": "irritada", "episodio_emocional": "sem causa"}])
def test_tom_sem_causa_vigente_publica_retrato_neutro(estado):
    retrato = criar_retrato_entrega_fala(estado, agora=101.0)
    assert (retrato.emocao, retrato.nivel, retrato.evidencia_ref) == ("calma", 1, "")


@pytest.mark.parametrize("alteracao", [
    {"mensagem_id": ""}, {"nivel": 4}, {"nivel": "invalido"},
    {"evidencia_ref": ""}, {"publicado_ts": float("nan")},
    {"emocao": ""}, {"emocao": "calma", "nivel": 3},
])
def test_projecao_visual_incompleta_nao_se_torna_retrato(alteracao):
    dados = criar_retrato_entrega_fala(_estado_causal(), agora=101.0).como_dict()
    dados.update(alteracao)
    assert ler_retrato_entrega_fala(dados) is None


def test_retrato_da_entrega_nao_e_memoria_duravel_da_conversa():
    retrato = criar_retrato_entrega_fala(_estado_causal(), agora=101.0)
    estado = EstadoCompartilhadoRuntime(conversacional={
        **_estado_causal(), "retrato_entrega_fala": retrato.como_dict(),
        "is_speaking": True, "audio_playing": True,
    })
    persistivel = capturar_contexto_conversa(estado)
    assert "retrato_entrega_fala" not in persistivel["conversacional"]
    assert "audio_playing" not in persistivel["conversacional"]
    assert "is_speaking" not in persistivel["conversacional"]


@pytest.mark.parametrize("emocao", ["feliz", "animada", "irritada", "alegre"])
def test_transporte_nao_reclassifica_rotulo_ja_aceito_pelo_owner_causal(emocao):
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="efeito confirmado",
        evidencia_ref="resultado:geral:rotulo", natureza_evidencia="fato_observado",
        permite_expressao=True, emocao=emocao, nivel=2, ts=100.0,
    )
    estado = aplicar_evento_emocional({}, evento, agora=100.0)
    retrato = criar_retrato_entrega_fala(estado, agora=101.0)
    assert (retrato.emocao, retrato.nivel) == (emocao, 2)
    assert ler_retrato_entrega_fala(retrato.como_dict()) == retrato


@pytest.mark.parametrize("entregue", [True, False])
def test_candidato_substituido_com_espera_so_retorna_apos_receipt_da_fila(entregue):
    from scripts.tests.test_voz_filas_isoladas import _runtime

    runtime = _runtime()
    runtime.chave_turno_cb = lambda: 25.0
    runtime.iniciar_worker = lambda: None
    assert runtime.falar("Aguarde.")
    retorno = []
    terminou = threading.Event()
    def substituir():
        retorno.append(runtime.falar("Resultado consolidado da resposta.", wait=True))
        terminou.set()
    substituicao = threading.Thread(target=substituir, daemon=True)
    substituicao.start()
    prazo = time.monotonic() + 2.0
    while runtime._pedido_turno_pendente["texto"] == "Aguarde." and time.monotonic() < prazo:
        time.sleep(.001)
    assert runtime._pedido_turno_pendente["texto"] == "Resultado consolidado da resposta."
    voltou_antes_da_entrega = terminou.is_set()
    def reproduzir(*_args):
        runtime.stop_event.set()
        return entregue
    runtime.reproduzir_fala = reproduzir
    runtime.worker_de_falas()
    substituicao.join(timeout=2.0)
    assert not substituicao.is_alive()
    assert voltou_antes_da_entrega is False, "aceitar substituição não confirma entrega"
    assert retorno == [entregue]


def test_catalogo_e_pergunta_natural_explicam_expressao_da_entrega():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime

    mapa = MapaHabilidadesRuntime()
    pergunta = "Você consegue sincronizar seu avatar com a voz e intensidade emocional?"
    for texto in (mapa.snapshot()["dominios"]["avatar"]["descricao"],
                  mapa.contexto_para_prompt(pergunta),
                  mapa.responder_pergunta_capacidade(pergunta)):
        assert "cada fala" in texto
        assert "intensidade" in texto and "movimento" in texto
    assert mapa.diagnostico()["autoriza_execucao"] is False


def test_consciencia_nao_promete_avatar_indisponivel_por_personalidade_disponivel():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime

    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {"dominios": {
        "avatar": {"estado": "indisponivel", "motivo": "sem_recurso_visual"},
    }})
    assert mapa.snapshot()["dominios"]["personalidade"]["estado"] == "disponivel"
    resposta = mapa.responder_pergunta_capacidade(
        "Você consegue sincronizar seu avatar com a voz e intensidade emocional?")
    assert "indisponível" in resposta
    assert "tenho um avatar" not in resposta.casefold()
