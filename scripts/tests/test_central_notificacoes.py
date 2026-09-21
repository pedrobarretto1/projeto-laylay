from __future__ import annotations

import json
from pathlib import Path
import threading

from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.personalidade.voz_runtime import VozRuntime


class _TimerControlado:
    def __init__(self, atraso, callback):
        self.atraso = float(atraso)
        self.callback = callback
        self.daemon = False
        self.ativo = False

    def is_alive(self):
        return self.ativo

    def start(self):
        self.ativo = True


def _runtime(tmp_path: Path, **kwargs) -> CentralNotificacoesRuntime:
    return CentralNotificacoesRuntime(
        str(tmp_path / "central.json"),
        log=lambda *_: None,
        **kwargs,
    )


def test_promocao_e_guardada_sem_falar_e_sem_duplicar(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
        time_cb=lambda: 1000.0,
    )
    email = {
        "uid": "uid:1",
        "origem": "email",
        "remetente": "Loja",
        "assunto": "Oferta imperdível: 50% de desconto",
    }

    assert central.ingerir_emails([email]) == {"uid:1"}
    assert central.ingerir_emails([email]) == {"uid:1"}
    assert falas == []
    assert central.diagnostico()["eventos"] == 1
    assert "Agrupei 1 promoção" in central.resumo()


def test_seguranca_usa_fila_mesmo_durante_jogo(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        modo_jogo_getter=lambda: True,
        conversa_ativa_getter=lambda: True,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
    )

    aceitos = central.ingerir_emails([{
        "uid": "uid:seg",
        "remetente": "Conta",
        "assunto": "Tentativa de login detectada",
        "possivel_golpe": True,
    }])

    assert aceitos == {"uid:seg"}
    assert len(falas) == 1
    assert falas[0][0] == "seguranca"
    assert "segurança" in falas[0][1].casefold()


def test_aviso_normal_ocupado_e_transferido_para_fila_sem_ser_perdido(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        modo_jogo_getter=lambda: True,
        agendar_fala_cb=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
    )

    central.ingerir([{
        "id": "sistema:1",
        "origem": "sistema",
        "titulo": "Atualização concluída",
    }])

    assert len(falas) == 1
    assert falas[0][1]["preservar_ate_entrega"] is True
    assert callable(falas[0][1]["ao_concluir"])
    assert "Atualização concluída" in central.resumo()


def test_lote_de_emails_so_e_anunciado_apos_receipt_da_voz(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        agendar_fala_cb=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
    )

    assert central.ingerir_emails([
        {
            "uid": "uid:normal-1",
            "remetente": "Pessoa A",
            "assunto": "Mensagem nova A",
        },
        {
            "uid": "uid:normal-2",
            "remetente": "Pessoa B",
            "assunto": "Mensagem nova B",
        },
    ]) == {"uid:normal-1", "uid:normal-2"}

    assert len(falas) == 1
    assert falas[0][0][0] == "emails"
    antes = json.loads((tmp_path / "central.json").read_text(encoding="utf-8"))
    assert [evento["anunciado"] for evento in antes["eventos"]] == [False, False]

    falas[0][1]["ao_concluir"](True, "entregue")

    depois = json.loads((tmp_path / "central.json").read_text(encoding="utf-8"))
    assert [evento["anunciado"] for evento in depois["eventos"]] == [True, True]


def test_falha_da_voz_nao_produz_confirmacao_falsa_de_anuncio(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        agendar_fala_cb=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
    )

    central.ingerir_emails([{
        "uid": "uid:falha-voz",
        "remetente": "Pessoa",
        "assunto": "Mensagem que ainda precisa ser entregue",
    }])
    falas[0][1]["ao_concluir"](False, "fila_recusou")

    estado = json.loads((tmp_path / "central.json").read_text(encoding="utf-8"))
    assert estado["eventos"][0]["anunciado"] is False
    assert central.diagnostico()["pendentes"] == 1


def test_email_adiado_atravessa_central_porteiro_e_voz_ate_entrega(tmp_path: Path) -> None:
    contexto = {
        "modo_chat": True,
        "conversa_ativa": True,
        "interacao_usuario_ativa": True,
        "ultima_entrada_ts": 990.0,
    }
    porteiro = PorteiroProatividadeRuntime(
        contexto_getter=lambda: dict(contexto),
        agora=lambda: 1000.0,
    )
    voz = VozRuntime(
        fallback_fala="fallback",
        voice="voz",
        edge_tts_mod=None,
        sounddevice_mod=None,
        soundfile_mod=None,
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        proativa_permitida_cb=lambda: True,
        avaliar_proatividade_cb=porteiro.avaliar,
        chave_turno_cb=lambda: 0.0,
        interrupt_event=threading.Event(),
        timer_factory=_TimerControlado,
    )
    voz.worker_started = True
    falas = []
    voz.falar = lambda *args, **kwargs: falas.append((args, kwargs)) or True
    central = _runtime(
        tmp_path,
        modo_jogo_getter=lambda: True,
        conversa_ativa_getter=lambda: bool(contexto["conversa_ativa"]),
        agendar_fala_cb=voz.agendar_fala_proativa,
    )

    assert central.ingerir_emails([{
        "uid": "uid:integracao",
        "remetente": "Pessoa",
        "assunto": "Mensagem aguardando um momento livre",
    }]) == {"uid:integracao"}
    assert voz.proativa_buffer
    assert central.diagnostico()["pendentes"] == 1

    contexto.update({
        "modo_chat": False,
        "conversa_ativa": False,
        "interacao_usuario_ativa": False,
        "ultima_entrada_ts": 0.0,
    })
    voz.proativa_buffer[0]["nao_antes_ts"] = 0.0
    voz.flush_fala_proativa()

    assert falas
    assert voz.proativa_buffer == []
    assert central.diagnostico()["pendentes"] == 0


def test_preferencia_explicita_persiste(tmp_path: Path) -> None:
    caminho = tmp_path / "central.json"
    central = _runtime(tmp_path)

    ok, _ = central.definir_preferencia("compras", "silenciar")

    assert ok is True
    recarregada = CentralNotificacoesRuntime(str(caminho), log=lambda *_: None)
    assert recarregada.diagnostico()["preferencias"]["compras"] == "silenciar"
    assert json.loads(caminho.read_text(encoding="utf-8"))["preferencias"]["compras"] == "silenciar"


def test_linguagem_natural_controla_categoria_e_consulta(tmp_path: Path) -> None:
    central = _runtime(tmp_path)

    silenciar = central.detectar("não me avise mais sobre promoções")
    interromper = central.detectar("avisos de segurança podem me interromper")
    consulta = central.detectar("tem alguma notificação importante?")

    assert silenciar == {
        "intent": "NOTIFICATIONS",
        "params": {"acao": "silenciar", "categoria": "promocao"},
    }
    assert interromper == {
        "intent": "NOTIFICATIONS",
        "params": {"acao": "interromper", "categoria": "seguranca"},
    }
    assert consulta["params"]["acao"] == "importantes"


def test_resumo_reune_eventos_e_agenda_sem_payload_executavel(tmp_path: Path) -> None:
    central = _runtime(
        tmp_path,
        agenda_getter=lambda: [{
            "nome": "consulta amanhã",
            "ativo": True,
            "comandos_no_disparo": [{"acao": "lock_pc"}],
        }],
        modo_jogo_getter=lambda: True,
    )
    central.ingerir([{
        "id": "email:2",
        "origem": "email",
        "categoria": "financeiro",
        "titulo": "Fatura vence amanhã",
        "prioritario": True,
    }])

    texto = central.resumo()

    assert "Fatura vence amanhã" in texto
    assert "consulta amanhã" in texto
    assert "lock_pc" not in texto


def test_agendamento_e_aceito_e_passa_pela_fila(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
        time_cb=lambda: 1200.0,
    )

    assert central.ingerir_agendamento({"id": "agua"}, "Hora de beber água") is True
    assert falas and "beber água" in falas[0][1]
