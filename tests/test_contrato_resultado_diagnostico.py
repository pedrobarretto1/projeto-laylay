from __future__ import annotations

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.executor_sistema import (
    DependenciasExecutorSistema,
    executar_intencao_sistema,
)
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.orquestrador_turno_runtime import atualizar_planejamento_turno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno
from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    AdaptadoresAplicacaoRuntime,
)
from mente_laylay.memoria_mental.diagnostico_mente import construir_diagnostico_mente
from mente_laylay.memoria_mental.formatacao_diagnostico import (
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    normalizar_resultado_acao,
)


class _EstadoPlano:
    def __init__(self, plano: dict | None = None) -> None:
        self.mental = {"plano_turno_atual": dict(plano or {})}

    def atualizar_campos(self, dominio: str, **campos) -> None:
        assert dominio == "mental"
        self.mental.update(campos)


def test_notificacoes_preservam_resultado_confirmado_ate_a_fala() -> None:
    eventos: list[tuple] = []
    deps = DependenciasExecutorSistema(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda status, fala, **kwargs: eventos.append(
            ("fala", status, fala, kwargs)
        ),
    )

    despacho = executar_intencao_sistema(
        "NOTIFICATIONS",
        {"acao": "importantes"},
        "pc_a",
        {
            "falar_com_lipsync": lambda *_args: None,
            "_central_notificacoes_executar": lambda _params: {
                "ok": True,
                "status": "notificacoes_lidas",
                "fala": "Tenho dois avisos importantes.",
            },
        },
        deps,
    )

    assert despacho.retorno is True
    assert eventos[0] == (
        "resultado",
        "notificacoes_lidas",
        {"executou": True, "confirmado": True},
    )
    assert eventos[1][3]["executou"] is True
    assert eventos[1][3]["confirmado"] is True


def test_notificacoes_lidas_sao_resultado_confirmavel_e_fala_nao_inventa_incerteza() -> None:
    resultado = normalizar_resultado_acao({
        "intent": "NOTIFICATIONS",
        "status": "notificacoes_lidas",
        "executou": True,
    })
    entregas: list[tuple] = []
    adaptador = AdaptadorResultadoOperacional(
        {"intent": "NOTIFICATIONS"},
        {"acao": "importantes"},
        "quais notificações são importantes?",
        "pc_a",
        {
            "falar_com_lipsync": lambda *_args: None,
            "_falar_resultado_operacional": lambda *args: entregas.append(args),
        },
    )

    adaptador.falar_por_status(
        "notificacoes_lidas",
        "Tenho dois avisos importantes.",
        alvo="notificações",
        executou=True,
        confirmado=True,
    )

    assert resultado.confirmado is True
    contrato, fala, _emocao, _nivel = entregas[0]
    assert contrato.executou is True
    assert contrato.confirmado is True
    assert fala == "Tenho dois avisos importantes."
    assert "não consegui confirmar" not in fala.casefold()


def test_resultado_propaga_tipo_e_evidencia_de_confirmacao_ao_plano() -> None:
    estado = _EstadoPlano({"fase": "executado", "comandos": []})
    namespace = {
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": lambda *_args: None,
    }
    adaptador = AdaptadoresAplicacaoRuntime(lambda: namespace)

    adaptador.registrar_resultado_execucao(
        ResultadoAcao(
            intent="NOTIFICATIONS",
            status="notificacoes_lidas",
            executou=True,
            confirmado=True,
        ),
        "quais notificações são importantes?",
        True,
    )

    comando = estado.mental["plano_turno_atual"]["comandos"][0]
    assert comando["confirmacao_oferecida"] == "persistencia_local"
    assert "central persiste" in comando["evidencia_confirmacao"]


def test_mescla_do_plano_nao_apaga_evidencia_ja_registrada() -> None:
    estado = _EstadoPlano({
        "fase": "executado",
        "comandos": [{
            "intent": "NOTIFICATIONS",
            "status": "notificacoes_lidas",
            "executou": True,
            "confirmado": True,
            "confirmacao_oferecida": "persistencia_local",
            "evidencia_confirmacao": "a central persiste a triagem",
        }],
    })
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": lambda *_args, **_kwargs: [],
        "print": lambda *_args: None,
    }

    atualizar_planejamento_turno(
        lambda: namespace,
        "tratado_prioritario",
        comandos=[{
            "intent": "NOTIFICATIONS",
            "status": "notificacoes_lidas",
            "executou": True,
            "confirmado": True,
        }],
    )

    comando = estado.mental["plano_turno_atual"]["comandos"][0]
    assert comando["confirmacao_oferecida"] == "persistencia_local"
    assert comando["evidencia_confirmacao"] == "a central persiste a triagem"


def test_guardiao_rejeita_segunda_etapa_sem_resultado_correspondente() -> None:
    validacao = validar_alegacoes_da_fala(
        "Guardei como ideia e marquei para você rever amanhã.",
        plano={
            "texto_usuario": (
                "anota a ideia de melhorar o avatar e cria um lembrete para amanhã"
            ),
            "comandos": [{
                "intent": "INBOX_ADD",
                "status": "nota_guardada",
                "executou": True,
                "confirmado": True,
            }],
        },
        origem="resposta_ia",
    )

    assert "etapa_agendamento_sem_resultado" in validacao["problemas"]
    assert "Guardei a ideia" in validacao["fala"]
    assert "não criei nem confirmei o lembrete" in validacao["fala"]


def test_guardiao_nao_declara_conclusao_total_de_plano_parcial() -> None:
    validacao = validar_alegacoes_da_fala(
        "Concluí todas as etapas; o pedido completo está pronto.",
        plano={"comandos": [
            {
                "intent": "INBOX_ADD",
                "status": "nota_guardada",
                "executou": True,
                "confirmado": True,
            },
            {
                "intent": "AGENDAR_LEMBRETE",
                "status": "aguardando_complemento",
                "executou": False,
                "confirmado": False,
            },
        ]},
        origem="resposta_ia",
    )

    assert "conclusao_total_com_plano_parcial" in validacao["problemas"]
    assert "apenas a etapa confirmada" in validacao["fala"]
    assert "todas as etapas" not in validacao["fala"].casefold()


def test_diagnostico_separa_estrutura_saudavel_de_operacao_degradada_sem_probe() -> None:
    diagnostico = construir_diagnostico_mente(
        {
            "mental": {
                "diagnostico_falhas": [{
                    "componente": "resposta_llm",
                    "codigo": "qualidade_comunicacao_nao_reparada",
                    "classe": "degradacao",
                    "impacto": "turno",
                    "fallback": "contingencia_conversacional",
                }],
            },
            "conversacional": {},
            "percepcao": {},
            "continuidades": {},
        },
        {"llm": {"status": "saudavel"}},
    )

    assert diagnostico["saude_estrutural"]["saudavel"] == 1
    assert diagnostico["saude_estrutural"]["degradado"] == 0
    assert diagnostico["saude_operacional"]["estado"] == "degradado"
    assert diagnostico["saude_operacional"]["falhas_impactantes"] == 1
    assert diagnostico["saude_operacional"]["probes_executados"] is False
    texto = formatar_diagnostico_terminal(diagnostico)
    assert "(saúde estrutural)" in texto
    assert "operação observada: estado=degradado" in texto
    assert "probes=False" in texto
