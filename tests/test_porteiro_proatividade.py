from __future__ import annotations

import ast
from pathlib import Path
import threading
import time

from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.personalidade.voz_runtime import VozRuntime


class TimerControlado:
    criados = []

    def __init__(self, atraso, callback):
        self.atraso = float(atraso)
        self.callback = callback
        self.daemon = False
        self.ativo = False
        self.__class__.criados.append(self)

    def is_alive(self):
        return self.ativo

    def start(self):
        self.ativo = True


def _voz(*, avaliador=None, permitida=lambda: True) -> VozRuntime:
    TimerControlado.criados = []
    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=None, sounddevice_mod=None, soundfile_mod=None, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        proativa_permitida_cb=permitida,
        avaliar_proatividade_cb=avaliador,
        chave_turno_cb=lambda: 77.0,
        interrupt_event=threading.Event(),
        timer_factory=TimerControlado,
    )
    runtime.worker_started = True
    return runtime


def test_observacao_comum_e_adiada_durante_resposta() -> None:
    agora = [100.0]
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {}, agora=lambda: agora[0],
    )

    decisao = porteiro.avaliar(
        tipo="contexto_janela", texto="O código está rendendo.",
        turno_ativo=True, mesclar_turno=True,
    )

    assert decisao["acao"] == "adiar"
    assert "resposta do usuário" in " ".join(decisao["motivos"])


def test_lembrete_importante_pode_ser_mesclado_ao_turno() -> None:
    porteiro = PorteiroProatividadeRuntime(contexto_getter=lambda: {}, agora=lambda: 100.0)

    decisao = porteiro.avaliar(
        tipo="lembrete", texto="Seu compromisso começa em cinco minutos.",
        turno_ativo=True, mesclar_turno=True,
    )

    assert decisao["acao"] == "mesclar"


def test_proatividade_e_descartada_em_momento_sensivel() -> None:
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {
            "modo_chat": True,
            "conversa_ativa": True,
            "funcao_comunicativa": "desabafo",
            "ultima_entrada_ts": 99.0,
        },
        agora=lambda: 100.0,
    )

    decisao = porteiro.avaliar(
        tipo="rotina", texto="Quer uma música de foco?",
    )

    assert decisao["acao"] == "descartar"
    assert decisao["pontuacao"] == 0


def test_presenca_validada_nao_e_bloqueada_so_por_jogo_e_chat_abertos() -> None:
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {
            "modo_chat": True,
            "conversa_ativa": True,
            "modo_jogo_ativo": True,
            "ultima_entrada_ts": 0.0,
        },
        agora=lambda: 1000.0,
    )

    decisao = porteiro.avaliar(
        tipo="presenca_jogo",
        texto="Essa área nova ficou bonita demais.",
    )

    assert decisao["acao"] == "emitir"
    assert "presença contextual segura" in " ".join(decisao["motivos"])


def test_presenca_de_jogo_ainda_espera_entrada_recente() -> None:
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {
            "modo_chat": True,
            "modo_jogo_ativo": True,
            "ultima_entrada_ts": 990.0,
        },
        agora=lambda: 1000.0,
    )

    decisao = porteiro.avaliar(
        tipo="presenca_jogo", texto="Essa luta foi bonita.",
    )

    assert decisao["acao"] == "adiar"
    assert "entrada recente" in " ".join(decisao["motivos"])


def test_sugestao_equivalente_nao_se_repete() -> None:
    agora = [100.0]
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {}, agora=lambda: agora[0],
    )
    primeira = porteiro.avaliar(tipo="briefing", texto="Hoje está ensolarado.")
    agora[0] += 30.0
    segunda = porteiro.avaliar(tipo="briefing", texto="Hoje está ensolarado.")

    assert primeira["acao"] == "emitir"
    assert segunda["acao"] == "descartar"
    assert "já apareceu" in " ".join(segunda["motivos"])


def test_fila_adia_observacao_em_vez_de_anexar_na_resposta() -> None:
    runtime = _voz(avaliador=lambda **_dados: {
        "acao": "adiar", "pontuacao": 12, "adiar_s": 9.0, "validade_s": 120.0,
    })
    runtime.iniciar_turno_resposta()

    assert runtime.agendar_fala_proativa(
        "contexto_janela", "O código está rendendo.", mesclar_turno=True,
    )
    assert runtime.falar("Continuando nossa conversa sobre o jogo.")

    pedido = runtime.fila.get_nowait()
    assert "código está rendendo" not in pedido["texto"]
    assert len(runtime.proativa_buffer) == 1
    assert runtime.proativa_buffer[0]["mesclar_turno"] is False
    assert TimerControlado.criados[-1].atraso >= 9.0


def test_flush_retem_item_enquanto_conversa_continua_ativa() -> None:
    runtime = _voz(
        avaliador=lambda **_dados: {"acao": "emitir", "validade_s": 120.0},
        permitida=lambda: False,
    )
    runtime.proativa_buffer = [{
        "tipo": "rotina", "texto": "Uma rotina útil.",
        "forcar_inicio": False, "nao_antes_ts": 0.0,
        "expira_ts": time.time() + 120.0,
    }]

    runtime.flush_fala_proativa()

    assert len(runtime.proativa_buffer) == 1
    assert runtime.proativa_buffer[0]["adiamentos"] == 1
    assert TimerControlado.criados[-1].atraso >= 10.0


def test_flush_entrega_presenca_de_jogo_ja_validada_com_chat_aberto() -> None:
    falas = []
    runtime = _voz(
        avaliador=lambda **_dados: {"acao": "emitir", "validade_s": 120.0},
        permitida=lambda: False,
    )
    runtime.falar = lambda *args, **kwargs: falas.append((args, kwargs)) or True
    runtime.proativa_buffer = [{
        "tipo": "presenca_jogo", "texto": "Essa área nova tem presença.",
        "emocao": "curiosa", "nivel": 1, "forcar_inicio": False,
        "nao_antes_ts": 0.0, "expira_ts": time.time() + 120.0,
    }]

    runtime.flush_fala_proativa()

    assert falas
    assert runtime.proativa_buffer == []


def test_item_expirado_nao_fica_preso_na_fila() -> None:
    conclusoes = []
    runtime = _voz(
        avaliador=lambda **_dados: {"acao": "emitir", "validade_s": 1.0},
        permitida=lambda: False,
    )
    runtime.proativa_buffer = [{
        "tipo": "rotina", "texto": "Uma rotina antiga.",
        "forcar_inicio": False, "nao_antes_ts": 0.0,
        "expira_ts": time.time() - 1.0,
        "ao_concluir": lambda ok, motivo: conclusoes.append((ok, motivo)),
    }]

    runtime.flush_fala_proativa()

    assert runtime.proativa_buffer == []
    assert conclusoes == [(False, "expirada:conversa_ativa")]


def test_chave_da_voz_e_sincronizada_depois_do_planejamento() -> None:
    chave = [10.0]
    runtime = _voz()
    runtime.chave_turno_cb = lambda: chave[0]
    runtime.iniciar_turno_resposta()
    assert runtime._chave_turno_ativo == 10.0

    chave[0] = 11.0
    assert runtime.sincronizar_chave_turno_resposta() == 11.0
    assert runtime._chave_turno_ativo == 11.0


def test_porteiro_e_ligado_ao_runtime_de_voz_e_nao_ao_ritmo() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    keywords_por_alvo = {}
    for no in arvore.body:
        if not isinstance(no, ast.Assign) or not isinstance(no.value, ast.Call):
            continue
        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id in {
                "_voz_runtime", "_ritmo_circadiano_runtime",
            }:
                keywords_por_alvo[alvo.id] = {
                    item.arg for item in no.value.keywords if item.arg
                }

    assert "avaliar_proatividade_cb" in keywords_por_alvo["_voz_runtime"]
    assert "avaliar_proatividade_cb" not in keywords_por_alvo["_ritmo_circadiano_runtime"]
