from __future__ import annotations

from mente_laylay.autonomia.agendamento_mental import (
    AgendaRuntime,
    extrair_agendamento_local,
)
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
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
