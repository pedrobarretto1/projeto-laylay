"""P19: a entrega conserva o retrato validado ao publicar texto e voz.

O subprocesso importa laylay.py e usa os owners e callbacks instalados. As
entradas causais e o relógio são controlados; apenas TTS/player e persistência
usam portas locais. Nenhum teste comprova som físico ou pixels do avatar.

Contrato: validade antes da publicação; expressão estável depois da publicação
até concluir/interromper a entrega, sem renovar a causa na mente compartilhada.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def entregas_instaladas(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("p19_entregas_instaladas")
    codigo = textwrap.dedent(r'''
        import json, os, sys, tempfile, threading, time
        from pathlib import Path
        from queue import Queue
        from types import SimpleNamespace
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica

        pasta = Path(os.environ["LAYLAY_P19_MEMORIA_TESTE"])
        (pasta / "audio").mkdir()
        tempfile.tempdir = str(pasta / "audio")
        iniciar_sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: iniciar_sqlite(
            self, str(pasta / Path(caminho or "laylay_memoria.sqlite").name))
        iniciar_resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: iniciar_resumo(
            self, pasta_memoria=str(pasta / "resumo"), **k)
        iniciar_pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: iniciar_pessoas(
            self, caminho=pasta / "pessoas.json", **k)
        iniciar_central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: iniciar_central(
            self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
            str(ident) + ".p19-entregas-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        from mente_laylay.personalidade.retrato_entrega import RetratoEntregaFala

        estado = root._estado_compartilhado_runtime
        voz = root._voz_runtime
        orquestrador = root._orquestrador_fala_runtime
        saida = {"owners": {
            "orquestrador": root.falar_com_lipsync.__self__ is orquestrador,
            "estado_voz": voz.ajustar_estado_fala_cb == root._estado_contexto_runtime.ajustar_estado_voz,
            "retrato_voz": voz.estado_emocional_getter() is estado.conversacional,
            "avatar": root._avatar_runtime.estado_getter is root._estado_visual_laylay,
            "gamebar": root._gamebar_bridge_runtime.estado_getter is root._estado_visual_laylay,
        }, "casos": {}, "modelo": 0}
        def bloquear_modelo(*_a, **_k):
            saida["modelo"] += 1
            raise AssertionError("expressão multimodal não chama a LLM")
        RegistroModeloLLM.executar = bloquear_modelo
        agora = [time.time()]
        time.time = lambda: agora[0]
        # O default time_fn capturou time.time durante a importação. A porta
        # do relógio da partial instalada deve acompanhar o relógio da causa.
        root._estado_visual_laylay.keywords["time_fn"] = lambda: agora[0]
        caso_atual = [None]
        def texto_publicado(texto, emocao, nivel, **_k):
            caso_atual[0]["texto"].append([texto, emocao, nivel])
            caso_atual[0]["texto_metadados"].append(dict(_k))
            if nome in {"troca_no_observador_textual", "modo_silencioso_com_troca", "proativa_com_troca"}:
                trocar()
            return True
        orquestrador.registrar_observador_texto_final(texto_publicado)

        def retrato_visual():
            visual = root._estado_visual_laylay()
            dados = {k: visual[k] for k in ("emotion", "level", "speaking", "activity")}
            dados["retrato"] = estado.obter_copia("conversacional", "retrato_entrega_fala", {})
            return dados

        def publicar_evento(ref, emocao, nivel):
            evento = criar_evento_emocional_causal(
                origem="resultado_operacional", causa="causa controlada " + ref,
                evidencia_ref=ref, natureza_evidencia="fato_observado",
                confianca=.97, relevancia=.95, permite_expressao=True,
                emocao=emocao, nivel=nivel, intensidade=nivel, ts=agora[0])
            assert root._estado_contexto_runtime.publicar_evento_emocional_causal(evento)
            assert root._definir_emocao_conversacional(emocao, nivel, evento["causa"])
            assert estado.conversacional["episodio_emocional"] == evento
            return evento

        nomes = (
            "estavel", "troca_na_fila", "troca_na_sintese", "troca_no_audio",
            "expirado_antes_publicacao", "expira_na_fila", "expira_no_audio",
            "interrupcao_com_troca", "fallback_com_troca", "falha_total_com_troca",
            "troca_no_observador_textual", "modo_silencioso_com_troca", "proativa_com_troca",
            "proativa_falha_total",
            "fallback_interrompido",
        )
        for indice, nome in enumerate(nomes):
            agora[0] += 500.0
            estado.substituir("mental", {
                "turno_atual": {"id": "p19:" + nome},
                "plano_turno_atual": {"id": "p19:" + nome, "requer_execucao": False,
                    "texto_usuario": "continue a conversa"},
                "ultima_entrada_ts": agora[0],
            })
            estado.substituir("conversacional", {"current_emotion": "calma", "emotion_level": 1})
            voz.fila = Queue()
            # Executamos o worker síncrono depois das transições controladas.
            # Esta flag evita a criação concorrente de um worker externo.
            voz.worker_started = True
            voz.stop_event = threading.Event()
            voz.interrupt_event = threading.Event()
            voz._ultima_solicitacao_fala = ""
            voz._ultima_chave_turno_emitida = 0.0
            voz._pedido_turno_pendente = None
            voz._turno_resposta_ativo = False
            voz._ultima_fala_normal_ts = 0.0
            voz.proativa_buffer = []
            voz._fallback_tts_disponivel = True
            voz._fallback_tts_sapi_windows = False
            voz.definir_modo_silencioso(False)
            caso = {"texto": [], "parametros_tts": [], "visual_sintese": [],
                "visual_audio": [], "metricas": [], "fallback_rates": [],
                "plays": 0, "stops": 0, "texto_metadados": [],
                "conclusoes_proativas": [], "registros_emitidos": []}
            caso_atual[0] = caso
            evento_a = publicar_evento("p19:" + nome + ":A", "irritada", 1)
            caso["evento_a"] = evento_a["evidencia_ref"]

            def trocar():
                if caso.get("evento_b"):
                    return
                agora[0] += .1
                evento_b = publicar_evento("p19:" + nome + ":B", "alegre", 2)
                caso["evento_b"] = evento_b["evidencia_ref"]

            if nome == "expirado_antes_publicacao":
                agora[0] += 300.0
            if nome == "modo_silencioso_com_troca":
                voz.definir_modo_silencioso(True)
            flush_thread = None
            if nome in {"proativa_com_troca", "proativa_falha_total"}:
                estado.atualizar_campos("mental", ultima_entrada_ts=0.0)
                estado.atualizar_campos("conversacional", modo_chat=False, conversa_ativa=False)
                caso["conclusoes_flush"] = []
                voz.proativa_buffer = [{"tipo": "briefing", "texto": "Uma conversa leve por aqui.",
                    "forcar_inicio": True,
                    "ao_concluir": lambda entregue, motivo: caso["conclusoes_flush"].append(
                        [bool(entregue), motivo])}]
                flush_thread = threading.Thread(target=voz.flush_fala_proativa, daemon=True)
                flush_thread.start()
                pedido = voz.fila.get(timeout=5)
                voz.fila.put(pedido)
                aceita = True
            else:
                aceita = root.falar_com_lipsync("Vou continuar a conversa por aqui.")
            caso["aceita"] = bool(aceita)
            if nome == "modo_silencioso_com_troca":
                caso["fila_final"] = voz.fila.qsize()
                caso["visual_final"] = retrato_visual()
                caso["mente_final"] = {"emocao": estado.conversacional["current_emotion"],
                    "nivel": estado.conversacional["emotion_level"],
                    "episodio": estado.conversacional["episodio_emocional"]["evidencia_ref"]}
                caso["retrato_transitorio_liberado"] = not bool(
                    estado.conversacional.get("retrato_entrega_fala"))
                saida["casos"][nome] = caso
                continue
            assert aceita and voz.fila.qsize() == 1, "a entrega deve chegar à fila real"
            pedido = voz.fila.queue[0]
            pedido["proativas_mescladas"] = [{
                "texto": "Observação associada à mesma entrega.",
                "ao_concluir": lambda entregue, motivo: caso["conclusoes_proativas"].append(
                    [bool(entregue), motivo]),
            }]
            voz.registrar_fala_emitida_cb = lambda *_a: caso["registros_emitidos"].append(True)
            pedido["dinamizar"] = False
            caso["fila"] = [pedido["texto"], pedido["emocao"], pedido["nivel"]]
            caso["esperado"] = [caso["texto"][0][1], caso["texto"][0][2]]
            caso["parametros_esperados"] = list(root.modular_audio_params(*caso["esperado"]))
            snapshot = pedido.get("retrato_entrega")
            caso["snapshot_tipado"] = isinstance(snapshot, RetratoEntregaFala)
            caso["snapshot_fila"] = snapshot.como_dict() if caso["snapshot_tipado"] else {}

            if nome in {"troca_na_fila", "fallback_com_troca", "falha_total_com_troca", "fallback_interrompido"}:
                trocar()
            elif nome == "expira_na_fila":
                agora[0] += 300.0

            def sintetizar(_texto, _caminho, *, rate, pitch, volume):
                caso["parametros_tts"].append([rate, pitch, volume])
                if nome == "troca_na_sintese":
                    trocar()
                caso["visual_sintese"].append(retrato_visual())
                if nome in {"fallback_com_troca", "falha_total_com_troca", "proativa_falha_total", "fallback_interrompido"}:
                    if nome in {"falha_total_com_troca", "proativa_falha_total"}:
                        voz.stop_event.set()
                    raise RuntimeError("falha controlada da porta TTS neural")
            voz._sintetizar_edge = sintetizar
            voz._selecionar_saida_audio = lambda: None
            voz.ducking_volume = lambda _ativo: None
            voz.registrar_metrica_cb = lambda n, _ms, ok, **_k: caso["metricas"].append([n, bool(ok)])

            def observar_audio():
                if nome in {"troca_no_audio", "interrupcao_com_troca"}:
                    trocar()
                elif nome == "expira_no_audio" and not caso["visual_audio"]:
                    agora[0] += 300.0
                caso["visual_audio"].append(retrato_visual())
                voz.stop_event.set()
            class Player:
                def play(self, *_a, **_k):
                    caso["plays"] += 1
                def get_stream(self):
                    observar_audio()
                    interromper = nome in {"interrupcao_com_troca", "fallback_interrompido"}
                    if interromper:
                        voz.interrupt_event.set()
                    return SimpleNamespace(active=interromper)
                def stop(self):
                    caso["stops"] += 1
                def wait(self):
                    observar_audio()
                    if nome == "fallback_interrompido":
                        voz.interrupt_event.set()
            class EngineLocal:
                def setProperty(self, chave, valor):
                    if chave == "rate":
                        caso["fallback_rates"].append(valor)
                def save_to_file(self, *_a): pass
                def runAndWait(self): pass
            voz.sd = Player()
            voz.sf = SimpleNamespace(read=lambda _p: ([0.0], 16000))
            voz.pyttsx3 = SimpleNamespace(init=lambda: EngineLocal())
            if nome in {"falha_total_com_troca", "proativa_falha_total"}:
                voz._fallback_tts_disponivel = False
            voz.worker_de_falas()
            if flush_thread is not None:
                flush_thread.join(timeout=5)
                assert not flush_thread.is_alive(), "flush proativo deve terminar após o worker"
            caso["visual_final"] = retrato_visual()
            caso["mente_final"] = {
                "emocao": estado.conversacional["current_emotion"],
                "nivel": estado.conversacional["emotion_level"],
                "episodio": estado.conversacional["episodio_emocional"]["evidencia_ref"],
            }
            caso["fila_final"] = voz.fila.qsize()
            caso["concluida"] = pedido["done_event"].is_set()
            caso["entregue"] = pedido.get("entregue")
            caso["retrato_transitorio_liberado"] = not bool(
                estado.conversacional.get("retrato_entrega_fala"))
            saida["casos"][nome] = caso

        # Falha da porta instalada durante preparação, depois de publicar o
        # retrato. O wrapper delega ao setter real nos demais campos.
        nome = "falha_preparacao"
        caso = {"texto": [], "texto_metadados": [], "metricas": [],
                "conclusoes_proativas": [], "registros_emitidos": []}
        caso_atual[0] = caso
        agora[0] += 500.0
        estado.substituir("mental", {"ultima_entrada_ts": agora[0], "turno_atual": {"id": nome}})
        estado.substituir("conversacional", {"current_emotion": "calma", "emotion_level": 1})
        voz.fila = Queue()
        voz.stop_event = threading.Event()
        voz._ultima_solicitacao_fala = ""
        voz._ultima_chave_turno_emitida = 0.0
        publicar_evento("p19:falha_preparacao:A", "irritada", 1)
        assert root.falar_com_lipsync("Ainda podemos continuar a conversa.")
        pedido = voz.fila.queue[0]
        pedido["proativas_mescladas"] = [{
            "texto": "Observação aguardando entrega.",
            "ao_concluir": lambda entregue, motivo: caso["conclusoes_proativas"].append(
                [bool(entregue), motivo]),
        }]
        voz.registrar_fala_emitida_cb = lambda *_a: caso["registros_emitidos"].append(True)
        callback_estado = voz.ajustar_estado_fala_cb
        def falhar_preparacao(chave, valor):
            if chave == "is_speaking" and valor is True:
                raise RuntimeError("porta de preparação indisponível")
            return callback_estado(chave, valor)
        voz.ajustar_estado_fala_cb = falhar_preparacao
        try:
            voz.worker_de_falas()
        except RuntimeError as erro:
            caso["erro"] = str(erro)
        finally:
            voz.ajustar_estado_fala_cb = callback_estado
        caso["retrato_transitorio_liberado"] = not bool(estado.conversacional.get("retrato_entrega_fala"))
        caso["is_speaking"] = bool(estado.conversacional.get("is_speaking"))
        caso["audio_playing"] = bool(estado.conversacional.get("audio_playing"))
        caso["concluida"] = pedido["done_event"].is_set()
        saida["casos"][nome] = caso
        saida["arquivos_audio_restantes"] = [p.name for p in (pasta / "audio").iterdir()]
        pergunta_capacidade = "Você consegue sincronizar seu avatar com a voz e intensidade emocional?"
        mapa = root._mapa_habilidades_runtime
        saida["catalogo"] = {
            "estado_avatar": mapa.snapshot()["dominios"]["avatar"]["estado"],
            "estado_personalidade": mapa.snapshot()["dominios"]["personalidade"]["estado"],
            "contexto": mapa.contexto_para_prompt(pergunta_capacidade),
            "resposta": mapa.responder_pergunta_capacidade(pergunta_capacidade),
        }
        sys.__stdout__.write("P19_ENTREGAS " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-B", "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8",
                 LAYLAY_P19_MEMORIA_TESTE=str(pasta), GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ",
                 LAYLAY_IOT_MODO="simulado", LAYLAY_MICROFONE_ATIVO="0",
                 LAYLAY_MASCOT_ENABLED="0", LAYLAY_AVATAR_ATIVO="0",
                 LAYLAY_PRESENCA="0", LAYLAY_BRIEFING_INICIAL="0"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4500:] + processo.stdout[-2000:]
    linhas = [linha.removeprefix("P19_ENTREGAS ") for linha in processo.stdout.splitlines()
              if linha.startswith("P19_ENTREGAS ")]
    assert len(linhas) == 1, processo.stdout[-2000:]
    return json.loads(linhas[0])


def test_retrato_entrega_usa_owners_instalados_e_zero_chamada_llm(entregas_instaladas):
    assert all(entregas_instaladas["owners"].values())
    assert entregas_instaladas["modelo"] == 0


@pytest.mark.parametrize("nome", [
    "estavel", "troca_na_fila", "troca_na_sintese", "troca_no_audio",
    "expirado_antes_publicacao", "expira_na_fila", "expira_no_audio",
    "interrupcao_com_troca", "fallback_com_troca",
    "troca_no_observador_textual", "proativa_com_troca",
])
def test_texto_tts_e_avatar_conservam_retrato_da_mesma_entrega(entregas_instaladas, nome):
    caso = entregas_instaladas["casos"][nome]
    esperado = ["calma", 1] if nome == "expirado_antes_publicacao" else ["irritada", 1]
    assert caso["esperado"] == esperado, "validade deve ser resolvida antes da publicação"
    assert caso["fila"][1:] == esperado, "a fila deve transportar o retrato publicado"
    assert caso["parametros_tts"] == [caso["parametros_esperados"]]
    for visual in caso["visual_sintese"]:
        assert [visual["emotion"], visual["level"]] == esperado, (
            "primeira fronteira P19: preparação visual reatribuiu a entrega ao episódio corrente"
        )
        assert visual["speaking"] is False and visual["activity"] == "thinking"
    assert caso["visual_audio"], "o caminho deve alcançar a porta de reprodução"
    for visual in caso["visual_audio"]:
        assert [visual["emotion"], visual["level"]] == esperado, (
            "primeira fronteira P19: áudio conserva o retrato da entrega, avatar usa outro episódio"
        )
        assert visual["speaking"] is True and visual["activity"] == "speaking"


@pytest.mark.parametrize("nome", [
    "troca_na_fila", "troca_na_sintese", "troca_no_audio",
    "interrupcao_com_troca", "fallback_com_troca", "falha_total_com_troca",
    "troca_no_observador_textual", "proativa_com_troca",
])
def test_termino_entrega_retorna_ao_episodio_atual_sem_reescrever_causa(entregas_instaladas, nome):
    caso = entregas_instaladas["casos"][nome]
    assert caso["mente_final"] == {"emocao": "alegre", "nivel": 2, "episodio": caso["evento_b"]}
    assert [caso["visual_final"]["emotion"], caso["visual_final"]["level"]] == ["alegre", 2]
    assert caso["visual_final"]["speaking"] is False
    assert caso["fila_final"] == 0 and caso["concluida"] is True
    assert caso["retrato_transitorio_liberado"] is True


def test_expiracao_nao_renova_episodio_pela_fala(entregas_instaladas):
    for nome in ("expirado_antes_publicacao", "expira_na_fila", "expira_no_audio"):
        caso = entregas_instaladas["casos"][nome]
        assert caso["mente_final"]["episodio"] == caso["evento_a"]
        assert [caso["visual_final"]["emotion"], caso["visual_final"]["level"]] == ["calma", 1]
        assert caso["visual_final"]["speaking"] is False
        assert caso["retrato_transitorio_liberado"] is True


def test_interrupcao_e_fallback_exercitam_portas_sem_audio_externo(entregas_instaladas):
    casos = entregas_instaladas["casos"]
    assert casos["interrupcao_com_troca"]["stops"] == 1
    fallback = casos["fallback_com_troca"]
    assert fallback["fallback_rates"] and fallback["plays"] == 1
    assert ["tts_sintese_primeiro_trecho", False] in fallback["metricas"]
    assert ["tts_total", True] in fallback["metricas"]
    falha = casos["falha_total_com_troca"]
    assert falha["plays"] == 0 and falha["visual_audio"] == []
    assert ["tts_total", False] in falha["metricas"]
    assert entregas_instaladas["arquivos_audio_restantes"] == []


@pytest.mark.parametrize("nome", [
    "estavel", "troca_na_fila", "troca_na_sintese", "troca_no_audio",
    "expirado_antes_publicacao", "expira_na_fila", "expira_no_audio",
    "interrupcao_com_troca", "fallback_com_troca", "troca_no_observador_textual",
    "proativa_com_troca",
])
def test_snapshot_da_fila_identifica_entrega_e_projecao_do_avatar(entregas_instaladas, nome):
    caso = entregas_instaladas["casos"][nome]
    assert caso["snapshot_tipado"] is True
    snapshot = caso["snapshot_fila"]
    assert [snapshot["emocao"], snapshot["nivel"]] == caso["esperado"]
    assert snapshot["evidencia_ref"] == ("" if nome == "expirado_antes_publicacao" else caso["evento_a"])
    assert snapshot["mensagem_id"] and snapshot["publicado_ts"] > 0
    if nome != "proativa_com_troca":
        assert snapshot["mensagem_id"] == caso["texto_metadados"][0]["mensagem_id"]
    for visual in (*caso["visual_sintese"], *caso["visual_audio"]):
        assert visual["retrato"] == snapshot
    assert caso["retrato_transitorio_liberado"] is True


def test_modo_silencioso_publica_texto_sem_snapshot_ou_audio(entregas_instaladas):
    caso = entregas_instaladas["casos"]["modo_silencioso_com_troca"]
    assert caso["aceita"] is True
    assert len(caso["texto"]) == 1 and caso["texto"][0][1:] == ["irritada", 1]
    assert caso["fila_final"] == 0 and caso["parametros_tts"] == [] and caso["plays"] == 0
    assert caso["mente_final"] == {"emocao": "alegre", "nivel": 2, "episodio": caso["evento_b"]}
    assert [caso["visual_final"]["emotion"], caso["visual_final"]["level"]] == ["alegre", 2]
    assert caso["visual_final"]["speaking"] is False
    assert caso["retrato_transitorio_liberado"] is True


def test_falha_na_preparacao_libera_snapshot_e_flags_de_audio(entregas_instaladas):
    caso = entregas_instaladas["casos"]["falha_preparacao"]
    assert caso.get("erro") == "porta de preparação indisponível"
    assert caso["retrato_transitorio_liberado"] is True, (
        "snapshot foi publicado antes de uma exceção fora do finally de reprodução"
    )
    assert caso["is_speaking"] is False and caso["audio_playing"] is False


def test_falha_na_preparacao_nao_confirma_entrega_de_itens_mesclados(entregas_instaladas):
    caso = entregas_instaladas["casos"]["falha_preparacao"]
    assert caso["conclusoes_proativas"], "a falha precisa concluir a espera"
    assert caso["conclusoes_proativas"][0][0] is False, (
        "preparação falhou antes do áudio, mas o callback confirmou entrega"
    )
    assert caso["registros_emitidos"] == []
    assert caso["concluida"] is True


@pytest.mark.parametrize("nome, esperado", [
    ("estavel", True), ("fallback_com_troca", True),
    ("falha_total_com_troca", False), ("interrupcao_com_troca", False),
    ("fallback_interrompido", False),
])
def test_conclusao_da_fila_reflete_entrega_confirmada_ou_interrompida(
    entregas_instaladas, nome, esperado,
):
    caso = entregas_instaladas["casos"][nome]
    if nome == "falha_total_com_troca":
        assert caso["plays"] == 0 and ["tts_total", False] in caso["metricas"]
    elif nome in {"interrupcao_com_troca", "fallback_interrompido"}:
        assert caso["stops"] == 1
    else:
        assert caso["plays"] == 1 and ["tts_total", True] in caso["metricas"]
    assert caso["conclusoes_proativas"][0][0] is esperado
    assert bool(caso["registros_emitidos"]) is esperado
    assert caso["entregue"] is esperado


@pytest.mark.parametrize("nome, esperado", [("proativa_com_troca", True),
                                           ("proativa_falha_total", False)])
def test_flush_espera_receipt_da_voz_antes_de_concluir_proatividade(
    entregas_instaladas, nome, esperado,
):
    caso = entregas_instaladas["casos"][nome]
    assert caso["concluida"] is True
    assert caso["entregue"] is esperado
    assert caso["conclusoes_flush"] and caso["conclusoes_flush"][0][0] is esperado


def test_catalogo_instalado_conhece_expressao_sem_prometer_overlay_desativado(entregas_instaladas):
    catalogo = entregas_instaladas["catalogo"]
    assert catalogo["estado_avatar"] == "indisponivel"
    assert catalogo["estado_personalidade"] == "disponivel"
    assert "cada fala" in catalogo["contexto"] and "intensidade" in catalogo["contexto"]
    assert "avatar [indisponivel]" in catalogo["contexto"]
    assert "indisponível" in catalogo["resposta"]
    assert "tenho um avatar" not in catalogo["resposta"].casefold()
