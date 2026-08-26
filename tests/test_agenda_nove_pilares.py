from __future__ import annotations

import datetime as dt

from mente_laylay.autonomia.agendamento_mental import (
    AgendaRuntime,
    extrair_agendamento_local,
    extrair_complemento_temporal_lembrete,
)
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime, resolver_intencao
from mente_laylay.autonomia.executor_agenda import (
    DependenciasExecutorAgenda,
    executar_intencao_agenda,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _pendencia(agora: list[float] | None = None, eventos: list | None = None):
    estado: dict = {}
    relogio = agora or [100.0]

    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    runtime = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        agora=lambda: relogio[0],
        evento_cb=(lambda evento, item: eventos.append((evento, item))) if eventos is not None else None,
        log=lambda *_args: None,
    )
    return runtime, estado


def _deps(eventos: list[tuple]) -> DependenciasExecutorAgenda:
    return DependenciasExecutorAgenda(
        marcar_resultado=lambda status, **dados: eventos.append(("resultado", status, dados)),
        falar_por_status=lambda status, fala, **dados: eventos.append(("fala", status, fala, dados)),
    )


def _transacao(lista: list, *, sucesso: bool = True):
    def executar(mutador):
        mutador(lista)
        return sucesso

    return executar


def test_linguagem_real_preserva_relogio_que_normalizador_remove() -> None:
    resultado = extrair_agendamento_local(
        "isso eu vou, pode me lembra de lavar ele as 14:30",
        normalizar_texto,
    )

    assert resultado == {
        "intent": "AGENDAR_LEMBRETE",
        "params": {"descricao": "lavar ele", "hora_alvo": "14:30"},
    }


def test_horario_natural_com_amanha_e_absoluto_e_preserva_laylay() -> None:
    for texto in (
        "me lembra amanhã 10 horas de testar a Laylay",
        "me lembra amanhã às 10 horas de testar a Laylay",
    ):
        resultado = extrair_agendamento_local(texto, normalizar_texto)

        assert resultado == {
            "intent": "AGENDAR_LEMBRETE",
            "params": {
                "descricao": "testar a Laylay",
                "hora_alvo": "10:00",
                "data_hora": "amanha",
            },
        }


def test_referencia_dela_nao_e_cortada_pelo_prefixo_de_lembrete() -> None:
    resultado = extrair_agendamento_local(
        "me lembra dela amanhã às 11 horas",
        normalizar_texto,
    )

    assert resultado == {
        "intent": "AGENDAR_LEMBRETE",
        "params": {
            "descricao": "dela",
            "hora_alvo": "11:00",
            "data_hora": "amanha",
        },
    }


def test_complemento_com_data_nao_confunde_horario_com_duracao() -> None:
    horario = extrair_complemento_temporal_lembrete(
        "10 horas",
        referencia_data="amanhã",
    )
    duracao = extrair_complemento_temporal_lembrete(
        "daqui 10 horas",
        referencia_data="amanhã",
    )

    assert horario == {
        "hora_alvo": "10:00",
        "complemento_pendente": True,
    }
    assert duracao == {
        "atraso_segundos": 36_000,
        "complemento_pendente": True,
    }


def test_reagendamento_contextual_preserva_alvo_e_substitui_horario() -> None:
    comando = extrair_agendamento_local(
        "Troca para amanhã às 22 horas.",
        normalizar_texto,
    )
    assert comando == {
        "intent": "AGENDAR_LEMBRETE",
        "params": {
            "descricao": "isso",
            "reagendamento_contextual": True,
            "substituir_lembrete_anterior": True,
            "hora_alvo": "22:00",
            "data_hora": "amanha",
        },
    }

    agenda = [{
        "id": "anterior",
        "tipo": "once",
        "ts_execucao": 1.0,
        "descricao": "revisar o teste",
        "ativo": True,
        "origem": "pedido_usuario",
    }]
    eventos: list[tuple] = []
    executar_intencao_agenda(
        comando["intent"],
        comando["params"],
        "Troca para amanhã às 22 horas.",
        {
            "_agendamentos_transacionar": _transacao(agenda),
            "ultima_intencao": "AGENDAR_LEMBRETE",
            "ultima_habilidade": "agenda",
            "ultimo_alvo": "revisar o teste",
            "ultimas_entradas": [],
        },
        _deps(eventos),
    )

    assert len(agenda) == 1
    assert agenda[0]["id"] != "anterior"
    assert agenda[0]["descricao"] == "revisar o teste"
    instante = dt.datetime.fromtimestamp(agenda[0]["ts_execucao"])
    assert (instante.hour, instante.minute) == (22, 0)
    assert any(
        evento[0] == "resultado" and evento[1] == "lembrete_reagendado"
        for evento in eventos
    )


def test_reagendamento_sem_ultimo_lembrete_nao_cria_item_generico() -> None:
    agenda: list[dict] = []
    eventos: list[tuple] = []

    executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {
            "descricao": "isso",
            "reagendamento_contextual": True,
            "substituir_lembrete_anterior": True,
            "hora_alvo": "22:00",
            "data_hora": "amanha",
        },
        "Troca para amanhã às 22 horas.",
        {"_agendamentos_transacionar": _transacao(agenda)},
        _deps(eventos),
    )

    assert agenda == []
    assert eventos[0][1] == "alvo_ausente"


def test_pedido_incompleto_publica_pendencia_canonica_sem_fingir_execucao() -> None:
    runtime, _estado = _pendencia()
    eventos: list[tuple] = []

    executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {"descricao": "lavar o banheiro"},
        "me lembra de lavar o banheiro",
        {
            "_pendencia_acao_runtime": runtime,
            "_registrar_mente_curta": lambda *_args: None,
            "falar_com_lipsync": lambda *_args: None,
        },
        _deps(eventos),
    )

    pendencia = runtime.obter()
    assert pendencia and pendencia["origem"] == "agenda"
    assert pendencia["metadados"]["descricao"] == "lavar o banheiro"
    resultado = next(item for item in eventos if item[0] == "resultado")
    assert resultado[1] == "aguardando_complemento"
    assert resultado[2]["executou"] is False
    assert resultado[2]["confirmado"] is False


def test_continuacao_natural_completa_mesma_pendencia_e_persiste_origem() -> None:
    runtime, _estado = _pendencia()
    runtime.registrar(
        origem="agenda",
        acao="completar_lembrete",
        pergunta="Qual horário?",
        referencia="lavar o banheiro",
        metadados={"descricao": "lavar o banheiro", "referencia_data": ""},
    )
    pendencia = runtime.obter()
    resultado, rota = resolver_intencao(
        "14:30",
        "terminal",
        {
            "normalizar_texto": normalizar_texto,
            "extrair_agendamento": lambda texto: extrair_agendamento_local(texto, normalizar_texto),
            "pendencia_agenda": pendencia,
        },
    )
    assert rota == "agenda-continuacao"
    assert resultado and resultado["params"]["hora_alvo"] == "14:30"

    agenda: list[dict] = []
    eventos: list[tuple] = []
    executar_intencao_agenda(
        resultado["intent"],
        resultado["params"],
        "14:30",
        {
            "_pendencia_acao_runtime": runtime,
            "_agendamentos_transacionar": _transacao(agenda),
        },
        _deps(eventos),
    )

    assert runtime.obter() is None
    assert agenda[0]["descricao"] == "lavar o banheiro"
    assert agenda[0]["origem"] == "pedido_usuario"
    assert agenda[0]["evidencia"] == "persistencia_local"


def test_recusa_natural_cancela_so_a_pendencia_sem_criar_lembrete() -> None:
    runtime, _estado = _pendencia()
    runtime.registrar(
        origem="agenda", acao="completar_lembrete", pergunta="Qual horário?",
        referencia="água", metadados={"descricao": "beber água"},
    )
    resultado, rota = resolver_intencao(
        "não, deixa quieto",
        "terminal",
        {
            "normalizar_texto": normalizar_texto,
            "extrair_agendamento": lambda texto: extrair_agendamento_local(texto, normalizar_texto),
            "pendencia_agenda": runtime.obter(),
        },
    )
    assert rota == "agenda-continuacao"
    assert resultado and resultado["params"]["cancelar_pendente"] is True

    eventos: list[tuple] = []
    executar_intencao_agenda(
        "AGENDAR_LEMBRETE", resultado["params"], "não, deixa quieto",
        {"_pendencia_acao_runtime": runtime, "falar_com_lipsync": lambda *_args: None},
        _deps(eventos),
    )
    assert runtime.obter() is None
    assert ("resultado", "lembrete_pendente_cancelado", {
        "executou": False, "confirmado": True,
    }) in eventos


def test_pergunta_hipotese_e_negacao_nao_autorizam_agenda() -> None:
    for texto in (
        "como eu faria para criar um lembrete?",
        "você consegue me lembrar de beber água às 14:30?",
        "se eu pedir para me lembrar de algo, você consegue?",
        "não me lembra de beber água às 14:30",
        "não cancela o lembrete de beber água",
    ):
        assert extrair_agendamento_local(texto, normalizar_texto) is None


def test_aprendizado_recebe_aceitacao_correcao_recusa_repeticao_e_silencio() -> None:
    agora = [100.0]
    eventos_pendencia: list[tuple] = []
    runtime, _estado = _pendencia(agora, eventos_pendencia)
    feedbacks: list[str] = []
    runtime.registrar(
        origem="agenda", acao="completar_lembrete", pergunta="Qual horário?",
        referencia="água", metadados={"descricao": "água"}, ttl_s=1,
    )
    agora[0] = 102.0
    assert runtime.obter() is None
    assert any(evento == "expirada" for evento, _item in eventos_pendencia)

    agenda: list[dict] = []
    executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {"descricao": "água", "hora_alvo": "14:30", "complemento_pendente": True},
        "14:30",
        {
            "_agendamentos_transacionar": _transacao(agenda),
            "_registrar_feedback_agenda": lambda evento, _dados: feedbacks.append(evento),
        },
        _deps([]),
    )
    assert "correcao" in feedbacks


def test_troca_clara_de_dominio_encerra_pendencia_da_agenda() -> None:
    runtime, estado = _pendencia()
    runtime.registrar(
        origem="agenda",
        acao="completar_lembrete",
        pergunta="Qual horário?",
        referencia="água",
        metadados={"descricao": "beber água", "referencia_data": "amanhã"},
    )

    class Contexto:
        def montar(self):
            return {
                "_pendencia_acao_runtime": runtime,
                "turno_atual": {
                    "id": "troca-dominio",
                    "modalidade": "comando",
                    "modalidade_geral": "comando",
                    "autoriza_execucao": True,
                },
                "retrato_turno_atual": {},
                "registrar_arbitragem_turno": lambda *_args: None,
            }

    interpretador = type(
        "Interpretador",
        (),
        {
            "tentar_ai_primeiro": lambda _self, _texto: {
                "intent": "APP_OPEN",
                "params": {"nome_app": "chrome"},
            },
        },
    )()
    servicos = {
        "_interpretacao_intencao_runtime": interpretador,
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_cancela_acao_agora": lambda _texto: False,
        "_resolver_comando_midia_contextual_forcado": lambda _texto: None,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_comando_acao_geral_contextual_forcado": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "detectar_intencao_deterministica": lambda _texto: None,
        "_extrair_agendamento_local": lambda texto: extrair_agendamento_local(
            texto, normalizar_texto,
        ),
        "_extrair_acao_agendada_local": lambda _texto: None,
        "_texto_parece_consulta_operacional": lambda _texto: True,
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: servicos,
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )

    resultado, _rota = ciclo.resolver_comando_natural("abre o chrome", "terminal")

    assert resultado and resultado["intent"] == "APP_OPEN"
    assert runtime.obter() is None
    assert estado["ultima_pendencia_acao"]["status"] == "substituida_por_troca_dominio"


def test_cooperacao_nao_publica_falha_como_confirmacao_total() -> None:
    publicados: list[dict] = []
    agenda: list[dict] = []

    executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {"descricao": "água", "minutos": 5},
        "me lembra de água em cinco minutos",
        {
            "_agendamentos_transacionar": _transacao(agenda, sucesso=False),
            "_publicar_evento_agenda_cooperativo": (
                lambda operacao, **dados: publicados.append({"operacao": operacao, **dados})
            ),
        },
        _deps([]),
    )

    assert publicados == [{
        "operacao": "agendar_lembrete", "alvo": "água", "confirmado": False,
    }]


def test_diagnostico_da_agenda_e_catalogo_vivo_nao_expoem_conteudo(tmp_path) -> None:
    arquivo = tmp_path / "agenda.json"
    runtime = AgendaRuntime(
        str(arquivo),
        falar_cb=lambda *_args: None,
        abrir_programa_cb=lambda *_args: None,
        enviar_pc_b_cb=lambda *_args: None,
        enviar_chrome_local_cb=lambda *_args: None,
        executar_comando_conteudo_cb=lambda *_args: None,
        log=lambda *_args: None,
    )
    runtime.save([{
        "id": "segredo", "descricao": "consulta privada", "ativo": True,
        "tipo": "once", "ts_execucao": 9999999999,
    }])
    diagnostico = runtime.diagnostico()

    assert diagnostico["agendamentos_ativos"] == 1
    assert diagnostico["conteudo_exposto"] is False
    assert "consulta privada" not in repr(diagnostico)

    mapa = MapaHabilidadesRuntime(
        saude_getter=lambda: {"agenda": {"status": "indisponivel"}},
    )
    assert mapa.snapshot()["dominios"]["agenda"]["estado"] == "indisponivel"
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue criar lembretes?"
    )
    assert "não está disponível" in resposta
