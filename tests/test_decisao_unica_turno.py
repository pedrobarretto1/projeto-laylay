from __future__ import annotations

import threading
import time

import mente_laylay.autonomia.coordenador_intencao as coordenador_intencao
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.cognicao.decisao_turno import (
    consolidar_arbitragem,
    filtrar_comandos_pelo_turno,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    aplicar_repeticao_operacional_ao_turno,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
    resolver_repeticao_ultima_acao,
)


def _turno(modalidade: str, *, autoriza: bool) -> dict:
    return {
        "id": 101,
        "modalidade": modalidade,
        "modalidade_geral": modalidade,
        "ato_principal": modalidade,
        "autoriza_execucao": autoriza,
        "confianca": 0.96,
        "segmentos": [{
            "modalidade": modalidade,
            "texto": "abre o youtube" if autoriza else "você conhece o youtube?",
        }],
    }


def _contexto_resolucao(turno: dict, intent_ia: dict, registros: list) -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "extrair_agendamento": lambda _texto: None,
        "extrair_acao_agendada": lambda _texto: None,
        "texto_cancela_acao_agora": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: None,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": lambda _texto: intent_ia,
        "registrar_arbitragem_turno": lambda texto, resultado: registros.append(
            (texto, resultado)
        ),
        "turno_atual": turno,
        "retrato_turno_atual": {},
    }


class _ContextoExecucaoMutavel:
    def __init__(self, turno: dict, plano: dict | None = None) -> None:
        self.turno = turno
        self.plano = plano

    def montar(self) -> dict:
        contexto = {"turno_atual": dict(self.turno)}
        if self.plano is not None:
            contexto["plano_turno_atual"] = dict(self.plano)
        return contexto


def _ciclo_execucao(turno: dict) -> CicloComandosRuntime:
    return CicloComandosRuntime(
        namespace_getter=dict,
        contexto_intencao_runtime=_ContextoExecucaoMutavel(turno),
        log=lambda *_args: None,
    )


def test_conversa_recebe_dono_social_sem_autorizacao_de_acao() -> None:
    turno = _turno("pergunta", autoriza=False)
    plano = planejar_turno("você conhece o YouTube?", turno=turno, mente={})

    assert plano["decisao_turno"]["proprietario"] == "conversa"
    assert plano["decisao_turno"]["permite_acao"] is False


def test_comando_explicito_recebe_dono_operacional() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})

    assert plano["decisao_turno"]["proprietario"] == "operacional"
    assert plano["decisao_turno"]["permite_acao"] is True


def test_tenta_de_novo_recupera_acao_iot_falha_e_autoriza_execucao() -> None:
    comando = {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_cor", "alvo": "lampada_quarto", "cor": "roxo",
            "rgb": (128, 0, 255),
        },
        "status": "indisponivel",
        "confirmado": False,
    }
    mente = registrar_resultado_execucao(
        {}, comando, "deixa a luz roxa", True, origem="contexto_iot"
    )
    repeticao = resolver_repeticao_ultima_acao(
        "tenta de novo", mente, lambda texto: str(texto).casefold().strip()
    )
    turno = aplicar_repeticao_operacional_ao_turno(
        _turno("conversa", autoriza=False), repeticao
    )

    assert repeticao == {"intent": "IOT_CONTROL", "params": comando["params"]}
    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True
    assert turno["requer_esclarecimento"] is False
    assert turno["repeticao_operacional"] == repeticao


def test_comando_json_da_ia_e_bloqueado_em_conversa() -> None:
    turno = _turno("pergunta", autoriza=False)
    plano = planejar_turno("você conhece o YouTube?", turno=turno, mente={})
    resultado = filtrar_comandos_pelo_turno(
        [{"intent": "OPEN_URL", "params": {"url": "https://youtube.com"}}],
        turno=turno,
        plano=plano,
        retrato={},
    )

    assert resultado["comandos"] == []
    assert resultado["rejeitados"][0]["intent"] == "OPEN_URL"
    assert "não autorizou" in resultado["rejeitados"][0]["motivo"]


def test_comando_de_midia_e_bloqueado_em_pergunta_de_identidade() -> None:
    texto = "você é só um chatbot?"
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    resultado = filtrar_comandos_pelo_turno(
        [{"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}],
        turno=turno,
        plano=plano,
        retrato={},
    )

    assert resultado["comandos"] == []
    assert resultado["autoriza_execucao"] is False
    assert resultado["rejeitados"] == [{
        "intent": "MEDIA_CONTROL",
        "motivo": "turno não autorizou execução",
    }]


def test_comando_json_continua_permitido_em_pedido_explicito() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})
    comando = {"intent": "OPEN_URL", "params": {"url": "https://youtube.com"}}
    resultado = filtrar_comandos_pelo_turno(
        [comando], turno=turno, plano=plano, retrato={},
    )

    assert resultado["comandos"] == [comando]
    assert resultado["rejeitados"] == []


def test_detector_sem_candidato_nao_revoga_pedido_explicito() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})

    contrato = consolidar_arbitragem(
        plano["decisao_turno"],
        {"decisao": None, "rejeitados": [], "origem": ""},
    )

    assert contrato["permite_acao"] is True
    assert contrato["status"] == "aguardando_intencao"


def test_intencao_da_ia_tambem_passa_pelo_arbitro_em_conversa() -> None:
    registros: list = []
    turno = _turno("conversa", autoriza=False)
    ctx = _contexto_resolucao(
        turno,
        {"intent": "OPEN_URL", "params": {"url": "https://rockstargames.com"}},
        registros,
    )

    intent, rota = resolver_intencao(
        "você viu que vai sair o GTA 6?", "chat", ctx,
    )

    assert intent is None
    assert rota == ""
    assert registros[-1][1]["decisao"] is None
    assert registros[-1][1]["rejeitados"]


def test_intencao_da_ia_ainda_executa_quando_o_pedido_e_explicito() -> None:
    registros: list = []
    turno = _turno("comando", autoriza=True)
    esperado = {"intent": "OPEN_URL", "params": {"url": "https://youtube.com"}}
    ctx = _contexto_resolucao(turno, esperado, registros)

    intent, rota = resolver_intencao("abre o YouTube", "chat", ctx)

    assert intent == esperado
    assert rota == "ia-first-arbitrada"
    assert registros[-1][1]["contrato_decisao"]["proprietario"] == "operacional"


def test_ia_first_classifica_consulta_natural_quando_detector_local_nao_cobrir() -> None:
    texto = "quais músicas eu tenho em kamaitachi"
    registros: list = []
    turno = classificar_modalidade_turno(texto)
    esperado = {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "kamaitachi"},
    }
    ctx = _contexto_resolucao(turno, esperado, registros)

    intent, rota = resolver_intencao(texto, "chat", ctx)

    assert intent == esperado
    assert rota == "ia-first-arbitrada"
    assert registros[-1][1]["decisao"] == esperado


def test_mesma_acao_so_e_executada_uma_vez_no_mesmo_turno(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda resultado, texto, contexto: chamadas.append(
            (resultado, texto, contexto)
        ) or True,
    )
    ciclo = _ciclo_execucao({"id": 1001})
    comando = {
        "intent": "IOT_CONTROL",
        "params": {"acao": "ligar", "alvo": "lampada_quarto"},
    }

    assert ciclo.executar_intencao(comando, "liga a luz") is True
    assert ciclo.executar_intencao(
        {
            **comando,
            "params": {
                "alvo": "lampada_quarto",
                "acao": "ligar",
                "referencia_contextual": True,
            },
        },
        "pode ligar a luz",
    ) is True

    assert len(chamadas) == 1
    diagnostico = ciclo.diagnostico_linguagem_natural()["execucao_turno"]
    assert diagnostico["iniciadas"] == 1
    assert diagnostico["reutilizadas"] == 1
    assert diagnostico["ativas"] == 0


def test_plano_ativo_usa_idempotencia_do_turno_real(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda resultado, *_args: chamadas.append(resultado) or True,
    )
    contexto = _ContextoExecucaoMutavel(
        {"id": 1010},
        {"id": 1010, "fase": "planejado"},
    )
    ciclo = CicloComandosRuntime(
        namespace_getter=dict,
        contexto_intencao_runtime=contexto,
        log=lambda *_args: None,
    )
    comando = {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}

    assert ciclo.executar_intencao(comando, "liga a luz") is True
    assert ciclo.executar_intencao(comando, "liga a luz") is True
    assert len(chamadas) == 1


def test_falha_da_acao_tambem_nao_e_reexecutada_no_mesmo_turno(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda *_args: chamadas.append(True) and False,
    )
    ciclo = _ciclo_execucao({"id": 1002})
    comando = {"intent": "APP_OPEN", "params": {"nome_app": "inexistente"}}

    assert ciclo.executar_intencao(comando, "abre o inexistente") is False
    assert ciclo.executar_intencao(comando, "abre o inexistente") is False
    assert len(chamadas) == 1


def test_mesma_acao_pode_ser_tentada_novamente_em_novo_turno(monkeypatch) -> None:
    chamadas = []
    turno = {"id": 1003}
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda *_args: chamadas.append(True) or True,
    )
    ciclo = _ciclo_execucao(turno)
    comando = {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}

    assert ciclo.executar_intencao(comando, "pausa") is True
    turno["id"] = 1004
    assert ciclo.executar_intencao(comando, "tenta de novo") is True
    assert len(chamadas) == 2


def test_acoes_diferentes_do_turno_misto_nao_sao_agrupadas(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda resultado, *_args: chamadas.append(resultado) or True,
    )
    ciclo = _ciclo_execucao({"id": 1005, "modalidade": "misto"})

    assert ciclo.executar_intencao(
        {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}},
        "liga a luz e coloca música",
    ) is True
    assert ciclo.executar_intencao(
        {"intent": "MUSIC_SEARCH", "params": {"query": "C418 - Sweden"}},
        "liga a luz e coloca música",
    ) is True
    assert ciclo.executar_intencao(
        {
            "intent": "MOVE_ITEM",
            "params": {"origem": "arquivo-a.txt", "destino": "arquivo-b.txt"},
        },
        "move os dois arquivos",
    ) is True
    assert ciclo.executar_intencao(
        {
            "intent": "MOVE_ITEM",
            "params": {"origem": "arquivo-c.txt", "destino": "arquivo-b.txt"},
        },
        "move os dois arquivos",
    ) is True

    assert [item["intent"] for item in chamadas] == [
        "IOT_CONTROL", "MUSIC_SEARCH", "MOVE_ITEM", "MOVE_ITEM",
    ]


def test_entregas_concorrentes_compartilham_a_mesma_execucao(monkeypatch) -> None:
    entrou_executor = threading.Event()
    liberar_executor = threading.Event()
    chamadas = []

    def executar_lento(*_args):
        chamadas.append(True)
        entrou_executor.set()
        assert liberar_executor.wait(timeout=2.0)
        return True

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executar_lento)
    ciclo = _ciclo_execucao({"id": 1006})
    comando = {"intent": "SCREEN_CAPTURE", "params": {"alvo": "tela"}}
    resultados = []

    primeira = threading.Thread(
        target=lambda: resultados.append(ciclo.executar_intencao(comando, "tira print"))
    )
    segunda = threading.Thread(
        target=lambda: resultados.append(ciclo.executar_intencao(comando, "tira print"))
    )
    primeira.start()
    assert entrou_executor.wait(timeout=2.0)
    segunda.start()
    limite = time.monotonic() + 2.0
    while (
        ciclo.diagnostico_linguagem_natural()["execucao_turno"]["aguardadas"] < 1
        and time.monotonic() < limite
    ):
        time.sleep(0.001)
    liberar_executor.set()
    primeira.join(timeout=2.0)
    segunda.join(timeout=2.0)

    assert chamadas == [True]
    assert sorted(resultados) == [True, True]
    assert ciclo.diagnostico_linguagem_natural()["execucao_turno"]["aguardadas"] == 1


def test_dispatcher_json_duplicado_tambem_converge_no_executor_canonico(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda resultado, *_args: chamadas.append(resultado) or True,
    )
    ciclo = _ciclo_execucao({"id": 1007})
    comando = {"acao": "ligar", "alvo": "lampada_quarto"}

    resultado = executar_comandos_json(
        {"executar_intencao": ciclo.executar_intencao},
        "liga a luz",
        [comando, dict(comando)],
        "",
        "comando",
        False,
        False,
        False,
    )

    assert resultado["erros"] == []
    assert len(chamadas) == 1


def test_acao_de_background_nao_herda_idempotencia_de_turno_encerrado(monkeypatch) -> None:
    chamadas = []
    turno = {"id": 1008}
    plano = {"id": 1008, "fase": "executado"}
    monkeypatch.setattr(
        coordenador_intencao,
        "executar_intencao",
        lambda resultado, *_args: chamadas.append(resultado) or True,
    )
    ciclo = CicloComandosRuntime(
        namespace_getter=dict,
        contexto_intencao_runtime=_ContextoExecucaoMutavel(turno, plano),
        log=lambda *_args: None,
    )
    comando = {"intent": "MUSIC_SEARCH", "params": {"query": "C418 - Sweden"}}

    assert ciclo.executar_intencao(comando, "ação autônoma") is True
    assert ciclo.executar_intencao(comando, "ação autônoma futura") is True
    assert len(chamadas) == 2
