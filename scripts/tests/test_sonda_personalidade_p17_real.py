"""Protege o veredito da sonda; fixtures não representam efeitos reais."""

import time

import pytest

from mente_laylay.integracao.roteiro_teste_conversa import carregar_configuracao_roteiro
from scripts.roteiros.sonda_personalidade_p17_real import ROTEIRO, conferir_turno


def _bronca():
    agora = time.time()
    receipt = {"intent": "APP_OPEN", "origem": "executor", "confirmado": True,
               "status": "ja_aberto_focado", "id_solicitacao": "app-5"}
    fala = "Calculadora já estava aberta e em foco. Chega de repetir esse pedido."
    item = {"status": "respondido", "processamento_concluido": True,
            "resultado_turno_concluido": True, "resposta": fala,
            "voz_silenciada": False, "voz_observada": True, "voz_concluida": True,
            "enviado_em": agora}
    plano = {"comandos": [receipt], "estado_emocional_observado": {
        "emocao": "brava", "nivel": 3, "episodio_evidencia_ref": "app-5"}}
    depois = {"turno_id": "semantico-5", "trace_id": "trace-5", "player": {
        "video_id": "video", "tab_id": 1, "repeat_enabled": False,
        "state": "paused", "observed_at": agora}, "traces": [{
            "turno_id": "trace-5", "etapas": {"tts_total": {"sucesso": True}}}]}
    registros = [
        {"turno": 5, "etapa": "fala_publicada", "mensagem_id": "turno:semantico-5"},
        {"turno": 5, "etapa": "trace_iniciado", "retorno": {"turno_id": "trace-5"}},
        {"turno": 5, "etapa": "evento", "resultado": receipt, "retorno": {
            "evidencia_ref": "app-5", "responsabilidade": "usuario",
            "natureza_evidencia": "fato_observado", "emocao": "brava", "nivel": 3}},
        {"turno": 5, "etapa": "autoria", "resultado": receipt,
         "retorno": {"usada_llm": True, "fala": fala}},
        {"turno": 5, "etapa": "modelo_retorno", "ocorrencia": "app-5",
         "chamada_id": "modelo-5", "tipo": "autoria_operacional", "sucesso": True},
        {"turno": 5, "etapa": "orcamento", "chamada_id": "modelo-5", "retorno": {
            "permitida": True, "turno_id": "trace-5", "timeout_s": 8}},
        {"turno": 5, "etapa": "http_retorno", "chamada_id": "modelo-5",
         "status": 200, "corpo": {"choices": [{"message": {"content": fala}}]}},
    ]
    return item, plano, registros, depois


def test_roteiro_tem_escopo_finito_voz_real_e_restauracao():
    config = carregar_configuracao_roteiro(ROTEIRO)
    assert len(config.comandos) == 11
    assert config.comandos[6] == "não" and config.comandos[9] == "sim"
    assert config.comandos[-1] == "alterna a repetição"
    assert config.encerrar_ao_final and config.aguardar_confirmacao_execucao
    assert not config.silenciar_voz_durante_teste


def test_prova_de_bronca_exige_toda_a_cadeia_observada():
    item, plano, registros, depois = _bronca()
    conferir_turno(5, item, plano, registros, {}, depois, {})


@pytest.mark.parametrize("etapa,erro", [
    ("modelo_retorno", "geração correlacionada"),
    ("http_retorno", "resposta real do backend"),
    ("orcamento", "orçamento de chamadas"),
])
def test_usada_llm_nao_substitui_prova_de_geracao_e_orcamento(etapa, erro):
    item, plano, registros, depois = _bronca()
    registros = [r for r in registros if r["etapa"] != etapa]
    with pytest.raises(AssertionError, match=erro):
        conferir_turno(5, item, plano, registros, {}, depois, {})


def test_geracao_de_outra_ocorrencia_nao_certifica_bronca():
    item, plano, registros, depois = _bronca()
    next(r for r in registros if r["etapa"] == "modelo_retorno")["ocorrencia"] = "app-4"
    with pytest.raises(AssertionError, match="geração correlacionada"):
        conferir_turno(5, item, plano, registros, {}, depois, {})


def test_app_ja_aberto_pode_antecipar_bronca_sem_exigir_autoria_em_turno_fixo():
    item, plano, registros, depois = _bronca()
    anterior = {"item": dict(item), "plano": plano, "depois": depois}
    for r in registros:
        r["turno"] = 4
    atuais = [dict(r, turno=5) for r in registros if r["etapa"] in {"evento", "fala_publicada", "trace_iniciado"}]
    item = dict(item, resposta="Calculadora já está aberta e em foco; não repeti a abertura.")
    conferir_turno(5, item, plano, registros + atuais, {}, depois, {4: anterior})


def test_player_antigo_e_tts_de_outro_turno_nao_certificam_prova_fisica():
    item, plano, registros, depois = _bronca()
    depois["player"]["observed_at"] -= 60
    with pytest.raises(AssertionError, match="estado fresco"):
        conferir_turno(5, item, plano, registros, {}, depois, {})
    depois["player"]["observed_at"] = time.time()
    depois["traces"][0]["turno_id"] = "turno-4"
    with pytest.raises(AssertionError, match="TTS desta fala"):
        conferir_turno(5, item, plano, registros, {}, depois, {})
