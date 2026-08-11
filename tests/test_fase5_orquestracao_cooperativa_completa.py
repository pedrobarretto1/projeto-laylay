from __future__ import annotations

from mente_laylay.autonomia.governanca_cooperacao import (
    GovernancaPlanoCooperativoRuntime,
)
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.orquestracao_cooperativa import (
    OrquestradorCooperativoRuntime,
)
from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
from mente_laylay.integracao.adaptadores_composicao import (
    publicar_curadoria_musical_cooperativa,
)


def _orquestrador(
    *, executar=lambda *_args: False,
) -> tuple[OrquestradorCooperativoRuntime, QuadroCooperacaoRuntime]:
    quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda *_args: None)
    runtime = OrquestradorCooperativoRuntime(
        quadro=quadro,
        clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "",
        executar_intencao=executar,
        resolver_caminho=lambda valor: valor,
        falar=lambda *_args: None,
        autorizar_acao=lambda *_args, **_kwargs: {
            "permitido": True,
            "motivo": "pedido_explicito",
        },
        log=lambda *_args: None,
    )
    return runtime, quadro


def test_governanca_sem_porteiro_falha_fechada() -> None:
    quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda *_args: None)
    plano = quadro.criar_plano(
        objetivo="teste sem porteiro",
        evento_ids=(),
        etapas=({"id": "acao", "acao": "agir", "intent": "APP_OPEN"},),
        confianca=1.0,
        risco="baixo",
        autorizacao="explicita_no_pedido",
    )
    governanca = GovernancaPlanoCooperativoRuntime(
        quadro=quadro,
        log=lambda *_args: None,
    )

    decisao = governanca.avaliar_autorizacao(
        plano,
        plano["etapas"][0],
        {"texto": "abre o Opera", "confirmado": True},
    )

    assert decisao == {
        "permitido": False,
        "motivo": "porteiro_indisponivel",
    }


def test_caixa_para_agenda_nao_vira_sucesso_quando_agenda_falha() -> None:
    referencia: list[OrquestradorCooperativoRuntime] = []

    def executar(_comando, _texto) -> bool:
        referencia[0].registrar_resultado_agenda(
            "agendar_lembrete",
            alvo="Revisar avatar espacial",
            confirmado=False,
        )
        return True

    runtime, quadro = _orquestrador(executar=executar)
    referencia.append(runtime)

    resultado = runtime.processar_caixa_para_agenda(
        item_salvo={
            "id": "nota-avatar",
            "titulo": "Revisar avatar espacial",
            "conteudo": "Criar uma aparência espacial para o avatar",
        },
        comando_agenda={
            "intent": "AGENDAR_LEMBRETE",
            "params": {
                "descricao": "Revisar avatar espacial",
                "hora_alvo": "11:00",
            },
        },
        texto_agenda="me lembra dela amanhã às 11 horas",
    )

    plano = quadro.snapshot()["planos_recentes"][-1]
    assert resultado["ok"] is False
    assert plano["estado"] == "falhou"
    assert [etapa["estado"] for etapa in plano["etapas"]] == [
        "confirmado", "falhou",
    ]
    assert plano["resultado"]["confirmado"] is False
    assert plano["etapas"][0]["resultado"]["evidencia"] == "nota_persistida_relida"


def test_caixa_para_agenda_confirma_as_duas_etapas_com_evidencia() -> None:
    referencia: list[OrquestradorCooperativoRuntime] = []

    def executar(_comando, _texto) -> bool:
        referencia[0].registrar_resultado_agenda(
            "agendar_lembrete",
            alvo="Revisar avatar espacial",
            confirmado=True,
        )
        return True

    runtime, quadro = _orquestrador(executar=executar)
    referencia.append(runtime)

    resultado = runtime.processar_caixa_para_agenda(
        item_salvo={
            "id": "nota-avatar",
            "titulo": "Revisar avatar espacial",
            "conteudo": "Criar uma aparência espacial para o avatar",
        },
        comando_agenda={
            "intent": "AGENDAR_LEMBRETE",
            "params": {
                "descricao": "Revisar avatar espacial",
                "hora_alvo": "11:00",
            },
        },
        texto_agenda="me lembra dela amanhã às 11 horas",
    )

    plano = quadro.snapshot()["planos_recentes"][-1]
    assert resultado["ok"] is True
    assert resultado["status"] == "plano_confirmado"
    assert plano["resultado"]["confirmado"] is True
    assert [etapa["estado"] for etapa in plano["etapas"]] == [
        "confirmado", "confirmado",
    ]
    assert plano["etapas"][1]["resultado"]["evidencia"] == (
        "persistencia_local_confirmada"
    )


def test_composicao_real_caixa_agenda_usa_orquestrador_e_executor_canonico() -> None:
    class Caixa:
        @staticmethod
        def processar(_texto: str) -> bool:
            return True

        @staticmethod
        def ultimo_item_salvo() -> dict:
            return {
                "id": "nota-integrada",
                "titulo": "Testar a Laylay",
                "conteudo": "Testar a Laylay",
            }

    referencia: list[OrquestradorCooperativoRuntime] = []
    comandos: list[dict] = []

    def executar(comando: dict, _texto: str) -> bool:
        comandos.append(dict(comando))
        referencia[0].registrar_resultado_agenda(
            "agendar_lembrete",
            alvo=str((comando.get("params") or {}).get("descricao") or ""),
            confirmado=True,
        )
        return True

    orquestrador, quadro = _orquestrador(executar=executar)
    referencia.append(orquestrador)
    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_caixa_entrada_pessoal_runtime": Caixa(),
        "_orquestrador_cooperativo_runtime": orquestrador,
        "resolver_comando_natural": lambda _texto, _origem: ({
            "intent": "AGENDAR_LEMBRETE",
            "params": {"dia": "amanhã", "hora": "11:00"},
        }, "agenda"),
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "processar_comandos_em_cadeia": lambda *_args: False,
    }
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert imediato.processar_prioritarios(
        "Guarda essa ideia e me lembra dela amanhã às 11 horas"
    ) is True

    assert len(comandos) == 1
    assert comandos[0]["params"]["descricao"] == "Testar a Laylay"
    assert comandos[0]["params"]["referencia_nota"] == "nota-integrada"
    plano = quadro.snapshot()["planos_recentes"][-1]
    assert plano["estado"] == "confirmado"
    assert plano["resultado"]["confirmado"] is True


class _InvestigadorParcial:
    @staticmethod
    def pesquisar(_conteudo: str) -> dict:
        return {
            "ok": False,
            "consulta": "HTTP 500",
            "resultados": [],
        }

    @staticmethod
    def sintetizar(_conteudo: str, *, consulta: str, resultados: list) -> dict:
        assert consulta == "HTTP 500"
        assert resultados == []
        return {
            "ok": True,
            "fala": "É um erro interno; sem fontes disponíveis, confira os logs.",
            "consulta": consulta,
            "fontes": [],
            "pesquisa_web": False,
            "sintese_llm": False,
        }


def test_clipboard_pesquisa_llm_preserva_privacidade_e_falha_parcial() -> None:
    runtime, quadro = _orquestrador()
    segredo = "HTTP 500 senha=nao-publicar-conteudo-bruto"

    resultado = runtime.processar_investigacao_clipboard(
        segredo,
        investigador=_InvestigadorParcial(),
    )

    snapshot = quadro.snapshot()
    plano = snapshot["planos_recentes"][-1]
    assert resultado["ok"] is True
    assert resultado["cooperacao"]["status"] == "plano_confirmado_com_falha_parcial"
    assert plano["estado"] == "confirmado"
    assert [etapa["estado"] for etapa in plano["etapas"]] == [
        "confirmado", "falhou", "confirmado",
    ]
    assert plano["resultado"]["falhas_parciais"] == 1
    assert segredo not in str(snapshot)
    assert "nao-publicar" not in str(snapshot)
    assert quadro.diagnostico()["referencias_ativas"] == 0


def test_clipboard_sem_porteiro_nao_pesquisa_nem_chama_llm() -> None:
    class InvestigadorEspiao:
        chamadas = 0

        @classmethod
        def pesquisar(cls, _conteudo: str) -> dict:
            cls.chamadas += 1
            return {"resultados": [{"titulo": "não deveria existir"}]}

        @classmethod
        def sintetizar(cls, *_args, **_kwargs) -> dict:
            cls.chamadas += 1
            return {"ok": True, "fala": "não deveria ser chamada"}

    quadro = QuadroCooperacaoRuntime(modo="ativo", log=lambda *_args: None)
    runtime = OrquestradorCooperativoRuntime(
        quadro=quadro,
        clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "",
        executar_intencao=lambda *_args: True,
        resolver_caminho=lambda valor: valor,
        falar=lambda *_args: None,
        autorizar_acao=None,
        log=lambda *_args: None,
    )
    segredo = "token-super-secreto-no-clipboard"

    resultado = runtime.processar_investigacao_clipboard(
        segredo,
        investigador=InvestigadorEspiao(),
    )

    snapshot = quadro.snapshot()
    plano = snapshot["planos_recentes"][-1]
    assert resultado["ok"] is False
    assert InvestigadorEspiao.chamadas == 0
    assert plano["estado"] == "falhou"
    assert plano["etapas"][0]["estado"] == "bloqueado"
    assert segredo not in str(snapshot)
    assert quadro.diagnostico()["referencias_ativas"] == 0


def test_curadoria_publica_plano_com_fontes_dependencias_e_evidencias() -> None:
    runtime, quadro = _orquestrador()

    assert runtime.registrar_curadoria_musical({
        "playlists_usuario": 3,
        "registros_historico": 20,
        "curadorias": 3,
    }) is True

    snapshot = quadro.snapshot()
    plano = snapshot["planos_recentes"][-1]
    evento = snapshot["eventos_recentes"][-1]
    assert plano["estado"] == "confirmado"
    assert plano["resultado"]["status"] == "plano_confirmado"
    assert [etapa["habilidade"] for etapa in plano["etapas"]] == [
        "playlists_usuario", "aprendizado_musical", "playlist_laylay",
    ]
    assert plano["etapas"][2]["depende_de"] == ["playlists"]
    assert plano["etapas"][2]["resultado"]["evidencia"] == "persistencia_relida"
    assert "persistencia_relida" in evento["evidencias"]
    assert quadro.diagnostico()["modo"] == "ativo"


def test_adaptador_de_curadoria_entrega_resumo_ao_orquestrador() -> None:
    recebidos: list[dict] = []

    assert publicar_curadoria_musical_cooperativa(
        {
            "playlists_usuario": 2,
            "registros_historico": 8,
            "curadorias": 3,
        },
        publicar_getter=lambda: (
            lambda resumo: recebidos.append(dict(resumo)) or True
        ),
    ) is True
    assert recebidos == [{
        "playlists_usuario": 2,
        "registros_historico": 8,
        "curadorias": 3,
    }]
