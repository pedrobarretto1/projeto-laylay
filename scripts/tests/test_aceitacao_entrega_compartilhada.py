"""Aceitação comunicativa conserva os canais, sem confirmar áudio ou efeito."""
from dataclasses import replace

import pytest

from mente_laylay.autonomia.finalizacao_execucao_ia import finalizar_execucao_resposta_ia
from scripts.tests.test_vinculo_fala_resultado import runtime_audio, receipt


def runtime_entrega():
    runtime, estado, voz = runtime_audio()
    plano = estado.obter_copia("mental", "plano_turno_atual", {})
    estado.atualizar_campos("mental", plano_turno_atual={**plano, "fase": "planejado"})
    return runtime, estado, voz


@pytest.mark.parametrize("texto_aceito,voz_aceita", [(True, False), (True, True), (False, True), (False, False)])
def test_aceitacao_e_continuidade_usam_os_canais_disponiveis(texto_aceito, voz_aceita):
    runtime, estado, voz = runtime_entrega()
    voz.falar = lambda *_args, **_kwargs: voz_aceita
    textos, falas = [], []
    runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto) or texto_aceito)
    runtime.registrar_observador_fala_final(lambda texto, *_a, **_k: falas.append(texto))
    fala = "Resposta desta ocorrência."
    aceita = runtime.falar(fala)
    assert textos == [fala], "Tentativa do observador não é seu aceite."
    assert falas == ([fala] if voz_aceita else [])
    assert runtime.textos_publicados_turno("origem") == ((fala,) if texto_aceito else ())
    fontes = estado.obter_copia("mental", "registro_semantico", {}).get("falas_observadas", [])
    assert [f["canais"] for f in fontes] == ([["texto_publicado"]] if texto_aceito else [])
    assert aceita is (texto_aceito or voz_aceita), "Texto entregue foi reduzido ao bool da voz."
    if aceita:
        assert estado.mental["ultima_resposta"] == fala
        assert estado.mental["continuidade_fala_ts"] > 0
    else:
        assert not estado.mental.get("ultima_resposta")


@pytest.mark.parametrize("retorno_texto", [True, None])
def test_texto_confirmado_sem_voz_nao_libera_repeticao_do_mesmo_resultado(retorno_texto):
    runtime, estado, voz = runtime_entrega()
    voz.falar = lambda *_a, **_k: False
    textos = []
    runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto) or retorno_texto)
    resultado = receipt()
    assert runtime.falar_resultado_operacional(resultado, "Pausei a música.") is True
    assert runtime.falar_resultado_operacional(resultado, "A música foi pausada.") is True
    assert textos == ["Pausei a música."]
    assert runtime.diagnostico()["duplicadas_suprimidas"] == 1
    assert runtime.diagnostico()["rejeitadas_entrega"] == 0
    fontes = estado.obter_copia("mental", "registro_semantico", {})["falas_observadas"]
    assert len(fontes) == 1 and fontes[0]["canais"] == ["texto_publicado"]


def test_falha_dos_dois_canais_permite_nova_tentativa_e_nao_confirma_entrega():
    runtime, estado, voz = runtime_entrega()
    aceites = iter([False, True])
    voz.falar = lambda *_a, **_k: False
    runtime.registrar_observador_texto_final(lambda *_a, **_k: next(aceites))
    assert runtime.falar_resultado_operacional(receipt(), "Pausei a música.") is False
    assert not estado.obter_copia("mental", "registro_semantico", {}).get("falas_observadas")
    assert runtime.falar_resultado_operacional(receipt(), "Pausei a música.") is True
    assert runtime.diagnostico()["rejeitadas_entrega"] == 1


def test_observador_que_falha_nao_apaga_aceite_de_outro_consumidor():
    runtime, estado, voz = runtime_entrega()
    voz.falar = lambda *_a, **_k: False
    def consumidor_indisponivel(*_args, **_kwargs):
        raise RuntimeError("consumidor indisponível")
    runtime.registrar_observador_texto_final(consumidor_indisponivel)
    runtime.registrar_observador_texto_final(lambda *_a, **_k: True)
    assert runtime.falar("Resposta disponível por texto.") is True
    assert estado.mental["ultima_resposta"] == "Resposta disponível por texto."


def test_novos_resultados_e_novo_turno_nao_sao_silenciados_pelo_aceite_textual():
    runtime, estado, voz = runtime_entrega()
    voz.falar = lambda *_a, **_k: False
    textos = []
    runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto) or True)
    assert runtime.falar_resultado_operacional(receipt(), "Pausei a música.")
    outro = replace(receipt("arquivo"), intent="CREATE_FILE", status="arquivo_criado", alvo="relatorio.txt")
    assert runtime.falar_resultado_operacional(outro, "Criei relatorio.txt.")
    estado.atualizar_campos("mental", turno_atual={"id": "outro"},
        plano_turno_atual={"id": "outro", "requer_execucao": True})
    assert runtime.falar_resultado_operacional(receipt(), "Pausei a música novamente.")
    assert len(textos) == 3


@pytest.mark.parametrize("aceita", [False, True])
def test_finalizacao_nao_declara_audio_entregue_a_partir_de_aceitacao(aceita):
    resultado = finalizar_execucao_resposta_ia({
        "messages": [], "falar_com_lipsync": lambda *_args: aceita,
        "enviar_mensagem": lambda *_args, **_kwargs: "",
        "limpar_resposta_da_ia": lambda texto: (texto, []),
        "verificar_fala_turno": lambda fala, **_kwargs: {"aceita": True, "fala": fala},
    }, [], [], "Esta é a resposta.", False, False, False)
    assert resultado["audio_entregue"] is None, "Aceitação não é receipt de reprodução."
    assert resultado["entrega_aceita"] is aceita
