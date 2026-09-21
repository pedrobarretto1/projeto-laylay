# REGRESSAO_118_V1_20260814
# -*- coding: utf-8 -*-
"""Regressões reproduzidas pelo roteiro automatizado de 118 turnos."""

from mente_laylay.autonomia.pre_fluxo_contextual import processar_consulta_sistema_local
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
    resolver_continuacao_aditiva,
)
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
)
from mente_laylay.personalidade.planejador_resposta import (
    classificar_resultado,
    planejar_resposta_acao,
)
from mente_laylay.integracao.composicao_entrada_interacao import (
    DEPENDENCIAS_COMANDOS_IMEDIATOS,
    ComposicaoEntradaInteracaoRuntime,
)

# REGRESSAO_APP_READONLY_COMPOSICAO_20260814


def test_consulta_app_eh_read_only():
    falas = []
    registros = []

    tratado, rota = processar_consulta_sistema_local(
        {
            "_resolver_alvo_ambiente": lambda nome: {
                "programa_aberto": True,
                "programa_em_foco": False,
            },
            "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
            "mente_integrada_estado": {},
        },
        "O Opera continua aberto?",
    )

    assert tratado is True
    assert rota == "consulta_estado_programa"
    assert falas == ["Opera está aberto, mas não está em foco."]
    contrato = registros[-1][0][0]
    assert contrato["intent"] == "LIST_WINDOWS"
    assert contrato["status"] == "estado_app_consultado"


def test_prioridade_read_only_fica_antes_da_cadeia_generica():
    import inspect
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime

    fonte = inspect.getsource(ComandosImediatosRuntime.processar_prioritarios)
    assert fonte.index("PRIORIDADE:SISTEMA:LEITURA") < fonte.index(
        'ns.get("processar_comandos_em_cadeia")'
    )


def test_resolver_alvo_ambiente_faz_parte_da_allowlist_dos_comandos_imediatos():
    assert "_resolver_alvo_ambiente" in DEPENDENCIAS_COMANDOS_IMEDIATOS


def test_composicao_entrega_resolver_alvo_ambiente_ao_runtime_de_comandos():
    snapshots = []

    class ComandosFake:
        def processar_prioritarios(self, _texto):
            return False

    class ChatFake:
        pass

    class DeteccaoFake:
        pass

    class RegistroFake:
        memoria_pessoas = object()
        iot = object()

    def comandos_factory(*, namespace_getter, **_kwargs):
        snapshots.append(namespace_getter())
        return ComandosFake()

    def chat_factory(**_kwargs):
        return ChatFake()

    servicos_iniciais = {
        "_resolver_alvo_ambiente": lambda nome: {
            "programa_aberto": nome.casefold() == "opera",
            "programa_em_foco": False,
        },
    }

    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos=servicos_iniciais,
        estado_mental_getter=lambda: {},
        sites_diretos={},
        apps_map={},
        registros_principais=RegistroFake(),
        deteccao_factory=lambda **_kwargs: DeteccaoFake(),
        comandos_factory=comandos_factory,
        chat_factory=chat_factory,
    )

    runtime.conectar(
        servicos={
            "_resolver_alvo_ambiente": servicos_iniciais["_resolver_alvo_ambiente"],
            "resolver_comando_natural": lambda *_args, **_kwargs: (None, ""),
        },
        loop_getter=lambda: None,
        estado_chat_getter=lambda: {},
        memoria_sqlite=object(),
    )

    assert snapshots
    snapshot = snapshots[-1]
    assert callable(snapshot.get("_resolver_alvo_ambiente"))
    assert snapshot["_resolver_alvo_ambiente"]("Opera") == {
        "programa_aberto": True,
        "programa_em_foco": False,
    }


def test_essa_tambem_sobrevive_ao_media_control_do_mesmo_dominio():
    estado = {}
    estado = registrar_evento_continuidade(
        estado,
        evento="resultado",
        intent="PLAYLIST_ADD",
        alvo="auditoria sonora",
        params={"nome_playlist": "auditoria sonora"},
        status="playlist_musica_adicionada",
        origem="teste_regressao",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="resultado",
        intent="MEDIA_CONTROL",
        alvo="proxima faixa",
        params={"acao": "next"},
        status="midia_next_playlist",
        origem="teste_regressao",
    )

    assert resolver_continuacao_aditiva(estado, texto="Essa também.") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "auditoria sonora",
            "referencia_contextual": True,
        },
    }


def test_lembrete_duplicado_e_noop_confirmado_e_nao_incerteza():
    assert "lembrete_ja_agendado" in STATUS_RESULTADO_JA_SATISFEITO
    resultado = ResultadoAcao(
        intent="AGENDAR_LEMBRETE",
        status="lembrete_ja_agendado",
        alvo="revisar a interface da aba Sistema amanhã às 15:20",
        executou=False,
        confirmado=True,
    )
    assert classificar_resultado(resultado) == "sem_acao"

    plano = planejar_resposta_acao(
        resultado,
        "Enviei o comando, mas não consegui confirmar o resultado.",
    )
    fala = plano.fala.casefold()
    assert plano.classe == "sem_acao"
    assert "não consegui confirmar" not in fala
    assert "nao consegui confirmar" not in fala
    assert "já" in fala or "ja" in fala
