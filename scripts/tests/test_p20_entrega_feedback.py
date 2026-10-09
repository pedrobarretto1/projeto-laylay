"""Entrega comunicativa é distinta da fila aceita e do receipt operacional."""
from types import SimpleNamespace

import pytest

from scripts.tests.test_personalidade_viva_p18_feedback import _montar_composicao
from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime


def _fala(composicao, *, contexto="comandos", publicado=True, voz=True):
    estado = composicao.estado
    estado.atualizar_campos("mental", turno_atual={"id": "p20-1"},
        plano_turno_atual={"id": "p20-1", "requer_execucao": contexto == "comandos"},
        modo_jogo_ativo=contexto == "jogo")
    registrar = getattr(composicao.diretor, "registrar_entrega_comunicativa", None)
    assert callable(registrar), "o owner de entregas deve aceitar receipt textual, sem executar"
    fila = []
    def falar(*a, **k):
        fila.append((a, k))
        return voz
    runtime = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado, "print": lambda *_a: None,
        "_dirigir_fala_mente": lambda fala, **_k: {"fala": fala},
        "_voz_runtime": SimpleNamespace(falar=falar),
        "_registrar_mente_curta": lambda *_a, **_k: None,
        "_registrar_continuidade_da_fala_mente": lambda *_a, **_k: None,
        "_encerrar_topico_mente": lambda *_a, **_k: None,
        "salvar_memoria": lambda: None,
        "_registrar_entrega_comunicativa": registrar,
    })
    runtime.registrar_observador_texto_final(lambda *_a, **_k: publicado)
    runtime.falar("Essa foi uma brincadeira de teste.")
    return fila


@pytest.mark.parametrize("contexto", ["jogo", "conversa", "comandos"])
def test_texto_aceito_registra_entrega_com_contexto_congelado(tmp_path, monkeypatch, contexto):
    c = _montar_composicao(tmp_path, monkeypatch)
    _fala(c, contexto=contexto, voz=False)
    emissao = c.estado.mental["presenca_contextual"]["ultima_emissao"]
    assert emissao["entregue"] is True
    assert emissao["contexto_humor"] == contexto
    assert emissao["canal_entrega"] == "texto_publicado"
    assert emissao["id_entrega"] == "turno:p20-1"
    assert emissao["fala"] == "Essa foi uma brincadeira de teste."
    assert emissao["autoriza_execucao"] is False
    # Mudança posterior não reatribui a qualificação ao novo contexto.
    c.estado.atualizar_campos("mental", modo_jogo_ativo=contexto != "jogo")
    c.agora[0] = 1001.0
    resposta = c.diretor.observar_resposta("Essa piada passou do ponto.")
    assert resposta["resultado"] == "correcao"
    evento = c.memoria.listar_eventos_aprendizado(f"personalidade:tolerancia_humor_implicita:{contexto}")
    assert len(evento) == 1
    assert evento[0]["contexto"]["proveniencia"]["contexto_humor"] == contexto


def test_fila_aceita_sem_texto_nao_e_entrega(tmp_path, monkeypatch):
    c = _montar_composicao(tmp_path, monkeypatch)
    _fala(c, publicado=False, voz=True)
    assert not c.estado.mental.get("presenca_contextual", {}).get("ultima_emissao")
    assert c.diretor.observar_resposta("Essa piada passou do ponto.") == {}


def test_receipt_operacional_nao_cria_entrega_comunicativa(tmp_path, monkeypatch):
    c = _montar_composicao(tmp_path, monkeypatch)
    c.estado.atualizar_campos("mental", ultimo_resultado_acao={"confirmado": True, "executou": True})
    assert c.diretor.observar_resposta("Gostei dessa piada.") == {}


@pytest.mark.parametrize("entregue,canal", [(False, "texto_publicado"), (True, "fila_aceita")])
def test_owner_rejeita_ausencia_de_receipt(tmp_path, monkeypatch, entregue, canal):
    c = _montar_composicao(tmp_path, monkeypatch)
    registrar = getattr(c.diretor, "registrar_entrega_comunicativa", None)
    assert callable(registrar)
    registrar(id_entrega="x", fala="teste", entregue=entregue, contexto_humor="jogo", canal_entrega=canal)
    assert not c.estado.mental.get("presenca_contextual", {}).get("ultima_emissao")


@pytest.mark.parametrize("fala", ["Essa brincadeira foi pesada?", "Uma dica neutra."])
def test_silencio_exige_pergunta_de_estilo_e_dez_minutos(tmp_path, monkeypatch, fala):
    c = _montar_composicao(tmp_path, monkeypatch)
    c.diretor.registrar_entrega_comunicativa(id_entrega="silencio", entregue=True,
        fala=fala, contexto_humor="jogo", canal_entrega="texto_publicado")
    c.agora[0] = 1599.0
    assert c.diretor.registrar_silencio_pendente() == {}
    assert c.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo") == []
    c.agora[0] = 1600.0
    assert c.diretor.registrar_silencio_pendente()["resultado"] == "silencio"
    eventos = c.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo")
    assert len(eventos) == (1 if fala.endswith("?") else 0)
    assert c.diretor.registrar_silencio_pendente() == {}
    assert c.motor.carregar_preferencia_humor_duravel("jogo") == {}


def test_resposta_relacionada_sem_direcao_nao_vira_silencio_de_estilo(tmp_path, monkeypatch):
    c = _montar_composicao(tmp_path, monkeypatch)
    c.diretor.registrar_entrega_comunicativa(id_entrega="indefinida", entregue=True,
        fala="Essa brincadeira foi pesada?", contexto_humor="jogo", canal_entrega="texto_publicado")
    c.agora[0] = 1001.0
    assert c.diretor.observar_resposta("Ainda não sei.") == {}
    c.agora[0] = 1600.0
    assert c.diretor.registrar_silencio_pendente() == {}
    assert c.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo") == []


@pytest.mark.parametrize("entregue", [True, False, None])
def test_worker_de_voz_so_registra_apos_reproducao_confirmada(tmp_path, monkeypatch, entregue):
    from scripts.tests.test_voz_filas_isoladas import _runtime
    c = _montar_composicao(tmp_path, monkeypatch)
    voz = _runtime()
    eventos = []
    def concluir(ok, texto):
        eventos.append((ok, texto))
        c.diretor.registrar_entrega_comunicativa(id_entrega="audio", entregue=ok,
            fala=texto, contexto_humor="conversa", canal_entrega="audio_reproducao_confirmada")
    voz.fila.put({"texto": "Brincadeira publicada em áudio.", "emocao": "calma",
        "nivel": 1, "dinamizar": False, "ao_concluir_entrega": concluir})
    assert not c.estado.mental.get("presenca_contextual", {}).get("ultima_emissao")
    def reproduzir(*_a):
        voz.stop_event.set()
        return entregue
    monkeypatch.setattr(voz, "reproduzir_fala", reproduzir)
    voz.worker_de_falas()
    assert eventos == [(entregue is True, "Brincadeira publicada em áudio.")]
    emissao = c.estado.mental.get("presenca_contextual", {}).get("ultima_emissao")
    if entregue is True:
        assert emissao["canal_entrega"] == "audio_reproducao_confirmada"
        assert emissao["contexto_humor"] == "conversa"
    else:
        assert not emissao


def test_dominio_da_habilidade_nao_define_contexto_social_da_entrega(tmp_path, monkeypatch):
    c = _montar_composicao(tmp_path, monkeypatch)
    # O getter de presença instalado está em jogo, embora a fonte seja rotina.
    c.diretor.registrar_entrega_observada(id_entrega="notificacao", entregue=True,
        motivo="texto_publicado", fala="Uma notificação entregue.", dominio="rotina",
        categoria="aviso", chave="notificacao", origem="central_notificacoes")
    emissao = c.estado.mental["presenca_contextual"]["ultima_emissao"]
    assert emissao["contexto_humor"] == "jogo"
