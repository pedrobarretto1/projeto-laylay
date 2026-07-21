from __future__ import annotations

from mente_laylay.autonomia.porteiro_proatividade import (
    PorteiroProatividadeRuntime,
    categoria_sugestao,
)
from mente_laylay.autonomia.sugestoes_sistema import processar_confirmacao_sugestao


def test_recusas_aumentam_intervalo_somente_na_categoria_recusada() -> None:
    agora = [100.0]
    runtime = PorteiroProatividadeRuntime(contexto_getter=lambda: {}, agora=lambda: agora[0])

    primeira = runtime.registrar_feedback("musica", False)
    segunda = runtime.registrar_feedback("musica", False)

    assert primeira["intervalo_s"] == 3600.0
    assert segunda["intervalo_s"] == 7200.0
    assert segunda["recusas_consecutivas"] == 2
    assert "rotina" not in runtime.perfil_atual()
    assert runtime.avaliar(tipo="musica", texto="Quer uma música?")["acao"] == "descartar"


def test_aceitacao_reduz_recuo_gradualmente() -> None:
    runtime = PorteiroProatividadeRuntime(contexto_getter=lambda: {}, agora=lambda: 100.0)
    runtime.registrar_feedback("rotina", False)
    recusada = runtime.registrar_feedback("rotina", False)
    aceita = runtime.registrar_feedback("rotina", True)

    assert recusada["intervalo_s"] == 9600.0
    assert aceita["intervalo_s"] == 4800.0
    assert aceita["recusas_consecutivas"] == 1
    assert aceita["aceitas"] == 1


def test_perfil_e_lido_e_salvo_na_mente_compartilhada() -> None:
    estado = {"musica": {"recusas": 1, "recusas_consecutivas": 1, "intervalo_s": 3600.0}}
    gravados = []
    runtime = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {},
        agora=lambda: 200.0,
        perfil_getter=lambda: estado,
        perfil_setter=lambda perfil: gravados.append(perfil),
    )

    runtime.registrar_feedback("musica", False)

    assert gravados[-1]["musica"]["recusas"] == 2
    assert gravados[-1]["musica"]["intervalo_s"] == 7200.0


def test_jogo_reuniao_e_foco_reduzem_falas_nao_urgentes() -> None:
    contextos = (
        {"modo_jogo_ativo": True},
        {"titulo_janela": "Reunião semanal - Microsoft Teams"},
        {"assunto": "Programação"},
    )
    for contexto in contextos:
        runtime = PorteiroProatividadeRuntime(
            contexto_getter=lambda contexto=contexto: contexto,
            agora=lambda: 100.0,
        )
        decisao = runtime.avaliar(tipo="musica", texto="Quer uma música de foco?")
        assert decisao["acao"] == "descartar"
        assert any(palavra in " ".join(decisao["motivos"]) for palavra in ("jogo", "reunião", "foco"))


def test_alarm_e_seguranca_ignoram_reducao_contextual_e_adaptativa() -> None:
    runtime = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {
            "modo_jogo_ativo": True,
            "reuniao_ativa": True,
            "modo_chat": True,
            "ultima_entrada_ts": 99.0,
        },
        agora=lambda: 100.0,
    )
    runtime.registrar_feedback("alarme", False)

    primeiro = runtime.avaliar(tipo="alarme", texto="Seu alarme tocou.")
    repetido = runtime.avaliar(tipo="alarme", texto="Seu alarme tocou.")
    seguranca = runtime.avaliar(tipo="seguranca", texto="A temperatura está crítica.")

    assert primeiro["acao"] == "emitir"
    assert repetido["acao"] == "emitir"
    assert seguranca["acao"] == "emitir"
    assert "alarme" not in runtime.perfil_atual()


def test_alarme_pode_ser_mesclado_sem_ser_reduzido() -> None:
    runtime = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {"modo_jogo_ativo": True}, agora=lambda: 100.0,
    )

    decisao = runtime.avaliar(
        tipo="alarme", texto="Hora do remédio.", turno_ativo=True, mesclar_turno=True,
    )

    assert decisao["acao"] == "mesclar"
    assert decisao["pontuacao"] == 100


def test_confirmacao_de_sugestao_alimenta_perfil_adaptativo() -> None:
    feedbacks = []
    continuidade = {
        "comando_sugerido": "TIME_LIGHT_ON",
        "comando_sugerido_payload": {},
        "comando_sugerido_estado": "PENDING_CONFIRM",
        "comando_sugerido_ts": 10**10,
    }
    contexto = {
        "continuidades_get": lambda chave, padrao=None: continuidade.get(chave, padrao),
        "classificar_confirmacao_local": lambda _texto: False,
        "resetar_sugestao": lambda: None,
        "falar": lambda *_args: None,
        "resposta_conversa_local": lambda _texto: "Tudo bem.",
        "sugestao_bloqueada_ate": {},
        "registrar_feedback_proatividade": lambda tipo, aceito, **dados: feedbacks.append(
            (tipo, aceito, dados.get("comando"))
        ),
    }

    assert processar_confirmacao_sugestao(contexto, "não, deixa")
    assert feedbacks == [("horario", False, "TIME_LIGHT_ON")]


def test_mapeamento_de_comandos_mantem_categorias_independentes() -> None:
    assert categoria_sugestao("TIME_WIND_DOWN") == "horario"
    assert categoria_sugestao("SYS_MODE_GAMER") == "rotina"
    assert categoria_sugestao(
        "EXECUTE_INTENT", {"intent": {"intent": "MUSIC_SEARCH", "params": {}}},
    ) == "musica"
    assert categoria_sugestao(
        "EXECUTE_INTENT", {"intent": {"intent": "EMAIL_READ", "params": {}}},
    ) == "emails"
