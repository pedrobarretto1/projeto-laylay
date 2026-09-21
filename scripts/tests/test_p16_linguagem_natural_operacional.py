from __future__ import annotations

import time
from datetime import datetime

import pytest

from mente_laylay.autonomia.agendamento_mental import (
    extrair_agendamento_local,
    extrair_complemento_temporal_lembrete,
    extrair_duracao_relativa,
)
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime, resolver_intencao
from mente_laylay.autonomia.executor_agenda import (
    DependenciasExecutorAgenda,
    executar_intencao_agenda,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_volume_ou_midia,
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.cognicao.normalizacao_linguagem import (
    corrigir_erros_portugues_operacionais,
    normalizar_texto,
)
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.especialistas.caixa_entrada_pessoal import CaixaEntradaPessoalRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)


def _contexto_deterministico(*, mente: dict | None = None) -> dict:
    return {
        "normalizar_texto": normalizar_texto,
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(
                texto, normalizar_texto=normalizar_texto,
            )
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "resolver_consulta_recurso_local": lambda _texto: None,
        "mente_integrada_estado": mente or {},
        "sites_diretos": {},
        "apps_map": {},
    }


def _caixa(tmp_path) -> CaixaEntradaPessoalRuntime:
    return CaixaEntradaPessoalRuntime(
        caminho=tmp_path / "caixa.json",
        falar=lambda *_args: None,
        registrar_resultado=lambda *_args, **_kwargs: None,
        contexto_getter=lambda: {"messages": []},
        agora=lambda: datetime(2026, 8, 2, 10, 0),
        log=lambda *_args: None,
    )


def test_p16_caixa_entende_pedidos_naturais_de_ideias(tmp_path) -> None:
    runtime = _caixa(tmp_path)

    for texto in (
        "me fale minhas ideias",
        "me conta as minhas ideias",
        "quero ver minhas notas",
    ):
        assert runtime.detectar(texto) == "listar"

    assert runtime.detectar("me fale uma ideia nova para o avatar") == ""


@pytest.mark.parametrize("origem", ["terminal", "voz"])
def test_p16_agenda_natural_e_resolvida_antes_da_llm_em_toda_entrada(origem: str) -> None:
    resultado, rota = resolver_intencao(
        "quais compromissos eu tenho?",
        origem,
        {
            "normalizar_texto": normalizar_texto,
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda texto: extrair_agendamento_local(
                texto, normalizar_texto,
            ),
            "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
                AssertionError("a consulta da agenda não pode chegar à LLM")
            ),
        },
    )

    assert rota == "agenda"
    assert resultado == {"intent": "LISTAR_AGENDAMENTOS", "params": {}}


def test_p16_duracao_unica_cobre_segundos_minutos_horas_e_numero_por_extenso() -> None:
    segundos = extrair_duracao_relativa("daqui a trinta segundos")
    minutos = extrair_duracao_relativa("em quinze minutos")
    horas = extrair_duracao_relativa("daqui a duas horas")
    assert segundos and segundos["atraso_segundos"] == 30
    assert minutos and minutos["atraso_segundos"] == 900
    assert horas and horas["atraso_segundos"] == 7200

    for texto, segundos in (
        ("trinta segundos", 30),
        ("em 15 minutos", 900),
        ("duas horas", 7200),
    ):
        assert extrair_complemento_temporal_lembrete(texto) == {
            "atraso_segundos": segundos,
            "complemento_pendente": True,
        }


def test_p16_lembrete_separa_descricao_do_tempo_e_executor_preserva_ambos() -> None:
    resultado = extrair_agendamento_local(
        "me lembra da consulta de dentista daqui a duas horas",
        normalizar_texto,
    )
    assert resultado == {
        "intent": "AGENDAR_LEMBRETE",
        "params": {
            "descricao": "consulta de dentista",
            "atraso_segundos": 7200,
        },
    }

    agenda: list[dict] = []
    eventos: list[tuple] = []
    falas: list[str] = []
    antes = time.time()

    executar_intencao_agenda(
        resultado["intent"],
        resultado["params"],
        "me lembra da consulta de dentista daqui a duas horas",
        {
            "_agendamentos_transacionar": lambda mutador: mutador(agenda) is None,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        DependenciasExecutorAgenda(
            marcar_resultado=lambda status, **dados: eventos.append((status, dados)),
            falar_por_status=lambda _status, fala, **_dados: falas.append(fala),
        ),
    )

    assert agenda[0]["descricao"] == "consulta de dentista"
    assert "daqui" not in agenda[0]["descricao"]
    assert antes + 7199 <= agenda[0]["ts_execucao"] <= time.time() + 7201
    assert eventos[0][0] == "lembrete_agendado"
    assert any("2 horas" in fala for fala in falas)


def test_p16_clima_atual_atravessa_filtro_casual_sem_chamar_llm() -> None:
    contexto = _contexto_deterministico()

    assert detectar_intencao_deterministica_mente(
        "vai chover hoje?", contexto,
    ) == {"intent": "WEATHER", "params": {}}

    corrigido, _eventos = corrigir_erros_portugues_operacionais(
        "qual a temperatira hoje?",
    )
    assert corrigido == "qual a temperatura hoje?"
    assert detectar_intencao_deterministica_mente(corrigido, contexto) == {
        "intent": "WEATHER", "params": {},
    }


def test_p16_fala_conversacional_nao_inventa_clima_sem_evidencia() -> None:
    verificacao = verificar_fala_turno(
        "Agora está fazendo 31 graus e vai chover.",
        plano={
            "texto_usuario": "vai chover hoje?",
            "ato_principal": "pergunta",
            "dominio": "conversa",
        },
    )

    assert "31 graus" not in verificacao["fala"]
    assert "Não consegui consultar" in verificacao["fala"]
    assert "clima_atual_sem_evidencia" in verificacao["problemas"]


def test_p16_erro_leve_de_midia_preserva_proxima_faixa_sem_fuzzy_em_conversa() -> None:
    corrigido, eventos = corrigir_erros_portugues_operacionais(
        "pasa para a proxma faixa",
    )
    assert corrigido == "pasa para a proxima faixa"
    assert eventos
    assert detectar_volume_ou_midia(
        corrigido,
        params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=True,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}}
    assert detectar_volume_ou_midia(
        "na proxima reuniao passa o relatorio",
        params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=True,
    ) is None


def test_p16_urgencia_de_email_usa_continuidade_de_resultado_observado() -> None:
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "EMAIL_READ",
            "params": {},
            "status": "emails_lidos",
            "executou": True,
            "confirmado": True,
        },
        "quais emails novos eu tenho?",
    )

    assert detectar_intencao_deterministica_mente(
        "algum deles é urgente?",
        _contexto_deterministico(mente=estado),
    ) == {
        "intent": "EMAIL_READ",
        "params": {"urgentes": True, "referencia_contextual": True},
    }
    assert detectar_intencao_deterministica_mente(
        "isso parece urgente?",
        _contexto_deterministico(),
    ) is None


def test_p16_email_hifenizado_sobrevive_a_normalizacao_ortografica() -> None:
    assert detectar_intencao_deterministica_mente(
        "quais e-mails novos eu tenho?",
        _contexto_deterministico(),
    ) == {"intent": "EMAIL_READ", "params": {}}


class _InterpretadorNulo:
    def tentar_ai_primeiro(self, _texto: str):
        return None


class _ContextoCiclo:
    def montar(self) -> dict:
        return {
            "turno_atual": {
                "id": "p16",
                "modalidade": "pergunta",
                "modalidade_geral": "pergunta",
                "autoriza_execucao": False,
            },
            "retrato_turno_atual": {},
            "registrar_arbitragem_turno": lambda *_args: None,
        }


def test_p16_metricas_separam_habilidade_moldura_comando_perdido_e_conversa() -> None:
    servicos = {
        "_interpretacao_intencao_runtime": _InterpretadorNulo(),
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_cancela_acao_agora": lambda _texto: False,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_extrair_agendamento_local": lambda _texto: None,
        "_extrair_acao_agendada_local": lambda _texto: None,
        "detectar_intencao_deterministica": lambda texto: (
            {"intent": "INBOX_LIST", "params": {}}
            if "ideias" in texto else None
        ),
        "_texto_parece_consulta_operacional": lambda texto: "comando perdido" in texto,
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: servicos,
        contexto_intencao_runtime=_ContextoCiclo(),
        log=lambda *_args: None,
    )

    assert ciclo.resolver_comando_natural("me fale minhas ideias", "terminal")[0]
    assert ciclo.resolver_comando_natural("comando perdido", "voz") == (None, "")
    assert ciclo.resolver_comando_natural("gosto de rock", "terminal") == (None, "")

    diagnostico = ciclo.diagnostico_linguagem_natural()
    assert diagnostico["por_habilidade"]["caixa_entrada"] == 1
    assert diagnostico["por_moldura"]["pergunta"] == 1
    assert diagnostico["comandos_nao_reconhecidos"] == 1
    assert diagnostico["conversas_legitimas"] == 1
    assert "texto" not in diagnostico
