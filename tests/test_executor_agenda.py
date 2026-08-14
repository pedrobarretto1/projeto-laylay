from __future__ import annotations

import time

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_agenda import (
    DependenciasExecutorAgenda,
    executar_intencao_agenda,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao


def _dependencias(eventos: list[tuple]) -> DependenciasExecutorAgenda:
    return DependenciasExecutorAgenda(
        marcar_resultado=lambda status, **kwargs: eventos.append(("resultado", status, kwargs)),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, kwargs)
        ),
    )


def _transacao(lista: list):
    def executar(mutador):
        mutador(lista)
        return True

    return executar


def test_executor_agenda_nao_interfere_em_outro_dominio() -> None:
    eventos: list[tuple] = []

    despacho = executar_intencao_agenda(
        "VOLUME", {}, "volume em 30", {}, _dependencias(eventos)
    )

    assert despacho == ResultadoDespacho.nao_tratado()
    assert eventos == []


def test_lembrete_dela_usa_ideia_publicada_pela_caixa_de_entrada() -> None:
    eventos: list[tuple] = []
    agenda: list[dict] = []

    despacho = executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {"descricao": "dela", "hora_alvo": "11:00", "data_hora": "amanha"},
        "me lembra dela amanhã às 11 horas",
        {
            "_agendamentos_transacionar": _transacao(agenda),
            "ultima_habilidade": "caixa_entrada",
            "ultimo_alvo": "Criar uma aparência espacial para o avatar",
            "ultimas_entradas": [],
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert agenda[0]["descricao"] == "Criar uma aparência espacial para o avatar"


def test_agendar_acao_relativa_preserva_intencao_para_disparo() -> None:
    eventos: list[tuple] = []
    agenda: list[dict] = []
    antes = time.time()

    despacho = executar_intencao_agenda(
        "AGENDAR_ACAO",
        {
            "atraso_segundos": 120,
            "acao_agendada": {"intent": "APP_OPEN", "params": {"nome_app": "discord"}},
        },
        "abre o discord daqui dois minutos",
        {"_agendamentos_transacionar": _transacao(agenda)},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert len(agenda) == 1
    assert agenda[0]["intencao_no_disparo"] == {
        "intent": "APP_OPEN",
        "params": {"nome_app": "discord"},
    }
    assert antes + 119 <= agenda[0]["ts_execucao"] <= time.time() + 121
    assert eventos[0] == (
        "resultado", "acao_agendada",
        {"executou": True, "confirmado": True},
    )


def test_reagendamento_substitui_apenas_mesma_acao_e_alvo() -> None:
    eventos: list[tuple] = []
    agenda = [{
        "id": "antigo",
        "ativo": True,
        "intencao_no_disparo": {
            "intent": "APP_OPEN",
            "params": {"nome_app": "discord"},
        },
    }]

    executar_intencao_agenda(
        "AGENDAR_ACAO",
        {
            "atraso_segundos": 60,
            "substituir_agendamento_anterior": True,
            "acao_agendada": {"intent": "APP_OPEN", "params": {"nome_app": "discord"}},
        },
        "abre o discord daqui um minuto",
        {"_agendamentos_transacionar": _transacao(agenda)},
        _dependencias(eventos),
    )

    assert len(agenda) == 1
    assert agenda[0]["id"] != "antigo"


def test_lembrete_sem_horario_registra_pendencia_sem_salvar() -> None:
    eventos: list[tuple] = []
    agenda: list[dict] = []
    registros: list[tuple] = []
    falas: list[str] = []

    despacho = executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {"descricao": "campeonato"},
        "me lembra do campeonato",
        {
            "_agendamentos_transacionar": _transacao(agenda),
            "_registrar_mente_curta": lambda *args: registros.append(args),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert agenda == []
    assert registros[-1][2:] == (
        "AGENDAR_LEMBRETE", "campeonato", "", "agenda"
    )
    assert falas


def test_complemento_de_horario_reaproveita_alvo_e_dia_pendentes() -> None:
    eventos: list[tuple] = []
    agenda: list[dict] = []

    despacho = executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {"hora": "06:00"},
        "às seis",
        {
            "ultima_intencao": "AGENDAR_LEMBRETE",
            "ultima_habilidade": "agenda",
            "ultimo_alvo": "campeonato de arremesso de peso",
            "ultimo_escopo": "sexta",
            "_agendamentos_transacionar": _transacao(agenda),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert agenda[0]["descricao"] == "campeonato de arremesso de peso"
    assert eventos[0] == (
        "resultado", "lembrete_agendado",
        {"executou": True, "confirmado": True},
    )


def test_listagem_omite_agendamentos_inativos() -> None:
    eventos: list[tuple] = []
    recebidos: list[list] = []
    falas: list[str] = []

    despacho = executar_intencao_agenda(
        "LISTAR_AGENDAMENTOS",
        {},
        "mostra minha agenda",
        {
            "_agendamentos_load": lambda: [
                {"nome": "ativo", "ativo": True},
                {"nome": "cancelado", "ativo": False},
            ],
            "_fala_agendamentos_estilosa": lambda itens: recebidos.append(itens) or "Um compromisso.",
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert recebidos == [[{"nome": "ativo", "ativo": True}]]
    assert falas == ["Um compromisso."]
    assert eventos == [(
        "resultado", "agendamentos_listados",
        {
            "executou": True,
            "confirmado": True,
            "detalhe": "1 agendamento(s) ativo(s) lido(s)",
        },
    )]


def test_cancelamento_marca_item_inativo_e_confirma_persistencia() -> None:
    eventos: list[tuple] = []
    agenda = [{"id": "abc", "nome": "consulta médica", "ativo": True}]

    despacho = executar_intencao_agenda(
        "CANCELAR_AGENDAMENTO",
        {"alvo": "consulta"},
        "cancela a consulta",
        {"_agendamentos_transacionar": _transacao(agenda)},
        _dependencias(eventos),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert agenda[0]["ativo"] is False
    assert eventos[0] == (
        "resultado", "agendamento_cancelado",
        {"executou": True, "confirmado": True},
    )


def test_cancelamento_usa_descricao_completa_quando_nome_esta_truncado() -> None:
    eventos: list[tuple] = []
    agenda = [{
        "id": "e888d76c",
        "nome": "melhorar a cobertura do roteir",
        "descricao": "melhorar a cobertura do roteiro automatizado",
        "ativo": True,
    }]

    executar_intencao_agenda(
        "CANCELAR_AGENDAMENTO",
        {"alvo": "melhorar a cobertura do roteiro automatizado"},
        "Cancela o lembrete de melhorar a cobertura do roteiro automatizado.",
        {"_agendamentos_transacionar": _transacao(agenda)},
        _dependencias(eventos),
    )

    assert agenda[0]["ativo"] is False
    assert eventos[0][0:2] == ("resultado", "agendamento_cancelado")
    assert eventos[0][2]["confirmado"] is True


def test_roteador_principal_delega_lembrete_ao_executor_agenda() -> None:
    agenda: list[dict] = []
    resultados = []

    retorno = executar_intencao(
        {"intent": "AGENDAR_LEMBRETE", "params": {"descricao": "água", "minutos": 5}},
        "me lembra de beber água em cinco minutos",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_agendamentos_transacionar": _transacao(agenda),
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: resultados.append(
                contrato
            ),
            "falar_com_lipsync": lambda *_args: None,
        },
    )

    assert retorno is True
    assert agenda and agenda[0]["descricao"] == "água"
    assert resultados and resultados[0].status == "lembrete_agendado"
