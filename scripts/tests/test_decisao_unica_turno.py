from __future__ import annotations

import threading
import time

import pytest

import mente_laylay.autonomia.coordenador_intencao as coordenador_intencao
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.cognicao.arbitro_turno import arbitrar_turno
from mente_laylay.cognicao.decisao_turno import (
    consolidar_arbitragem,
    filtrar_comandos_pelo_turno,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    alinhar_identidade_plano_revisao,
    aplicar_repeticao_operacional_ao_turno,
)
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.resultado_acao import (
    interpretar_tratamento_operacional,
    marcar_tratamento_operacional,
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


def _contratos_reais_do_filtro(texto: str) -> tuple[dict, dict, dict]:
    turno = classificar_modalidade_turno(texto)
    retrato, _entidades = construir_retrato_turno(
        texto, turno=turno, mente={}, contexto_perceptivo={},
    )
    turno["retrato_id"] = retrato["id"]
    plano = planejar_turno(texto, turno=turno, mente={})
    assert turno["id"] == plano["id"] == retrato["id"]
    assert plano["decisao_turno"]["turno_id"] == turno["id"]
    assert plano["retrato_id"] == turno["retrato_id"]
    assert turno["autoriza_execucao"] is True
    return turno, plano, retrato


@pytest.mark.parametrize("texto, intent", [
    ("cria a playlist foco", "PLAYLIST_CREATE"),
    ("liga a lâmpada do quarto", "IOT_CONTROL"),
])
def test_filtro_aceita_comando_com_turno_plano_e_retrato_coerentes(texto: str, intent: str) -> None:
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    comando = {"intent": intent}

    filtrado = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)

    assert filtrado["autoriza_execucao"] is True
    assert filtrado["comandos"] == [comando]
    assert filtrado["rejeitados"] == []


@pytest.mark.parametrize("divergencia", [
    "turno_id", "plano_id", "decisao_turno_id", "retrato_id", "turno_retrato_id",
    "plano_retrato_id", "turno_texto", "plano_texto", "retrato_texto", "retrato_sem_id",
])
def test_filtro_nao_combina_autoridade_com_snapshot_de_outra_ocorrencia(divergencia: str) -> None:
    turno, plano, retrato = _contratos_reais_do_filtro("cria a playlist foco")
    outro_id = turno["id"] + 1
    if divergencia == "turno_id":
        turno["id"] = outro_id
    elif divergencia == "plano_id":
        plano["id"] = outro_id
    elif divergencia == "decisao_turno_id":
        plano["decisao_turno"]["turno_id"] = outro_id
    elif divergencia == "retrato_id":
        retrato["id"] = outro_id
    elif divergencia == "turno_retrato_id":
        turno["retrato_id"] = outro_id
    elif divergencia == "plano_retrato_id":
        plano["retrato_id"] = outro_id
    elif divergencia == "turno_texto":
        turno["texto"] = "apaga o arquivo foco"
    elif divergencia == "plano_texto":
        plano["texto_usuario"] = "apaga o arquivo foco"
    elif divergencia == "retrato_texto":
        retrato["texto"] = "apaga o arquivo foco"
    else:
        retrato.pop("id")

    filtrado = filtrar_comandos_pelo_turno(
        [{"intent": "PLAYLIST_CREATE"}], turno=turno, plano=plano, retrato=retrato,
    )

    assert filtrado["autoriza_execucao"] is False
    assert filtrado["comandos"] == []
    assert "incoerente" in filtrado["rejeitados"][0]["motivo"]


@pytest.mark.parametrize("texto, intent", [
    ("cria a playlist foco", "DELETE_ITEM"),
    ("liga a lâmpada do quarto", "APP_OPEN"),
])
def test_retrato_de_outro_turno_nao_libera_intent_alheio_ao_pedido(texto: str, intent: str) -> None:
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    comando = {"intent": intent}
    controle = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)
    assert controle["comandos"] == []
    assert controle["rejeitados"][0]["motivo"] == "intenção incompatível com a operação explícita"
    retrato.update(id=turno["id"] + 1, texto="pedido de outra ocorrência", intents_permitidos=[intent])

    filtrado = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)

    assert filtrado["autoriza_execucao"] is False
    assert filtrado["comandos"] == []
    assert "incoerente" in filtrado["rejeitados"][0]["motivo"]


@pytest.mark.parametrize("texto, comando", [
    ("Abre o Opera... não, abre a Calculadora.", {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}),
    ("Liga a lâmpada... não, deixa desligada.", {"intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "lâmpada"}}),
])
def test_filtro_preserva_revisao_legitima_com_original_e_operacional_separados(
    texto: str, comando: dict,
) -> None:
    revisao = resolver_revisao_intra_turno(texto)
    assert revisao["detectada"] and revisao["resolvida"] and not revisao["cancelada"]
    efetivo = revisao["texto_operacional_efetivo"]
    turno, plano, retrato = _contratos_reais_do_filtro(efetivo)
    turno.update(texto=texto, texto_original=texto, texto_operacional_efetivo=efetivo, revisao_intra_turno=revisao)
    plano = alinhar_identidade_plano_revisao(
        plano, texto_original=texto, texto_operacional_efetivo=efetivo, revisao_intra_turno=revisao,
    )
    assert plano["texto_usuario"] != retrato["texto"]
    assert plano["texto_operacional_efetivo"] == retrato["texto"]

    filtrado = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)

    assert filtrado["autoriza_execucao"] is True
    assert filtrado["comandos"] == [comando]


@pytest.mark.parametrize("retrato", [None, {}])
def test_filtro_preserva_contrato_legado_sem_referencia_a_retrato(retrato: dict | None) -> None:
    turno = classificar_modalidade_turno("abre a Calculadora")
    plano = planejar_turno("abre a Calculadora", turno=turno, mente={})
    assert not turno.get("retrato_id") and not plano.get("retrato_id")
    comando = {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}

    filtrado = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)

    assert filtrado["autoriza_execucao"] is True
    assert filtrado["comandos"] == [comando]


def test_filtro_nao_ignora_retrato_referenciado_que_desapareceu() -> None:
    turno, plano, _retrato = _contratos_reais_do_filtro("cria a playlist foco")

    filtrado = filtrar_comandos_pelo_turno(
        [{"intent": "PLAYLIST_CREATE"}], turno=turno, plano=plano, retrato={},
    )

    assert filtrado["autoriza_execucao"] is False
    assert filtrado["comandos"] == []


def test_filtro_sem_retrato_tambem_recusa_plano_com_id_divergente() -> None:
    turno = classificar_modalidade_turno("abre a Calculadora")
    plano = planejar_turno("abre a Calculadora", turno=turno, mente={})
    plano["id"] = turno["id"] + 1

    filtrado = filtrar_comandos_pelo_turno([{"intent": "APP_OPEN"}], turno=turno, plano=plano)

    assert filtrado["autoriza_execucao"] is False
    assert filtrado["comandos"] == []


@pytest.mark.parametrize("dono, campo", [
    ("turno", "id"), ("plano", "id"), ("decisao", "turno_id"),
    ("turno", "retrato_id"), ("plano", "retrato_id"),
    ("turno", "texto"), ("plano", "texto_usuario"), ("retrato", "texto"),
])
def test_filtro_moderno_recusa_identidade_incompleta(dono: str, campo: str) -> None:
    turno, plano, retrato = _contratos_reais_do_filtro("cria a playlist foco")
    contratos = {"turno": turno, "plano": plano, "retrato": retrato, "decisao": plano["decisao_turno"]}
    contratos[dono].pop(campo)

    filtrado = filtrar_comandos_pelo_turno(
        [{"intent": "PLAYLIST_CREATE"}], turno=turno, plano=plano, retrato=retrato,
    )

    assert filtrado["autoriza_execucao"] is False
    assert filtrado["comandos"] == []
    assert "incoerente" in filtrado["rejeitados"][0]["motivo"]


def test_filtro_recusa_visao_operacional_divergente_apos_revisao() -> None:
    original = "Abre o Opera... não, abre a Calculadora."
    revisao = resolver_revisao_intra_turno(original)
    efetivo = revisao["texto_operacional_efetivo"]
    turno, plano, retrato = _contratos_reais_do_filtro(efetivo)
    turno.update(texto=original, texto_original=original, texto_operacional_efetivo=efetivo)
    plano = alinhar_identidade_plano_revisao(
        plano, texto_original=original, texto_operacional_efetivo=efetivo, revisao_intra_turno=revisao,
    )
    plano["texto_operacional_efetivo"] = "abre o Opera"

    filtrado = filtrar_comandos_pelo_turno(
        [{"intent": "APP_OPEN"}], turno=turno, plano=plano, retrato=retrato,
    )

    assert filtrado["autoriza_execucao"] is False
    assert filtrado["comandos"] == []


def test_filtro_preserva_ids_serializados_e_limite_textual_canonico() -> None:
    texto = "cria a playlist foco " + "x" * 510
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    assert len(plano["texto_usuario"]) == len(retrato["texto"]) == 500
    turno["texto"] = "  " + texto + "  "
    plano["id"] = str(plano["id"])
    plano["decisao_turno"]["turno_id"] = str(plano["decisao_turno"]["turno_id"])
    comando = {"intent": "PLAYLIST_CREATE"}

    filtrado = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)

    assert filtrado["autoriza_execucao"] is True
    assert filtrado["comandos"] == [comando]


def test_filtro_preserva_lista_legada_sem_identidade_de_retrato() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})
    retrato = {"intents_permitidos": ["OPEN_URL"]}
    comando = {"intent": "OPEN_URL"}

    filtrado = filtrar_comandos_pelo_turno([comando], turno=turno, plano=plano, retrato=retrato)

    assert filtrado["autoriza_execucao"] is True
    assert filtrado["comandos"] == [comando]
    recusado = filtrar_comandos_pelo_turno(
        [{"intent": "DELETE_ITEM"}], turno=turno, plano=plano, retrato=retrato,
    )
    assert recusado["comandos"] == []
    assert recusado["rejeitados"][0]["motivo"] == "intenção incompatível com a operação explícita"


def test_detector_sem_candidato_nao_revoga_pedido_explicito() -> None:
    turno = _turno("comando", autoriza=True)
    plano = planejar_turno("abre o YouTube", turno=turno, mente={})

    contrato = consolidar_arbitragem(
        plano["decisao_turno"],
        {"decisao": None, "rejeitados": [], "origem": ""},
    )

    assert contrato["permite_acao"] is True
    assert contrato["status"] == "aguardando_intencao"


def test_pedido_contextual_sem_vencedor_nem_referente_falha_fechado() -> None:
    turno = classificar_modalidade_turno("continua")
    plano = planejar_turno("continua", turno=turno, mente={})
    arbitragem = arbitrar_turno(
        "continua",
        [],
        turno=turno,
        retrato={"referencia_resolvida": {}},
    )

    contrato = consolidar_arbitragem(
        plano["decisao_turno"],
        arbitragem,
    )

    assert arbitragem["depende_contexto"] is True
    assert contrato["permite_acao"] is False
    assert contrato["proprietario"] == "conversa"
    assert contrato["requer_esclarecimento"] is True
    assert contrato["status"] == "sem_acao"


def test_pedido_contextual_com_referente_pode_aguardar_especialista() -> None:
    turno = classificar_modalidade_turno("continua")
    plano = planejar_turno("continua", turno=turno, mente={})

    contrato = consolidar_arbitragem(
        plano["decisao_turno"],
        {
            "decisao": None,
            "rejeitados": [],
            "depende_contexto": True,
            "referencia_resolvida": {
                "tipo": "musica",
                "nome": "faixa atual",
                "origem": "reprodutor_atual",
            },
        },
    )

    assert contrato["permite_acao"] is True
    assert contrato["requer_esclarecimento"] is False
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


def test_cache_preserva_tratado_sem_efeito_sem_reexecutar(monkeypatch) -> None:
    chamadas = []

    def executar(resultado, _texto, _contexto):
        chamadas.append(resultado)
        marcar_tratamento_operacional(
            resultado,
            tratado=True,
            executou=False,
            confirmado=False,
            status="nao_executado_por_politica",
            retorno_legado=True,
        )
        return True

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executar)
    ciclo = _ciclo_execucao({"id": 1009})
    primeiro = {"intent": "APP_OPEN", "params": {"nome_app": "Opera"}}
    segundo = {"intent": "APP_OPEN", "params": {"nome_app": "Opera"}}

    assert ciclo.executar_intencao(primeiro, "abre o Opera") is True
    assert ciclo.executar_intencao(segundo, "abre o Opera") is True
    assert len(chamadas) == 1

    tratamento = interpretar_tratamento_operacional(segundo, True)
    assert tratamento.tratado is True
    assert tratamento.executou is False
    assert tratamento.confirmado is False
    assert tratamento.status == "nao_executado_por_politica"
    assert tratamento.legado is False


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



def test_diagnostico_execucao_separa_legado_sem_receipt_e_confirmado(monkeypatch) -> None:
    ciclo = _ciclo_execucao(_turno("comando", autoriza=True))

    def executor_falso(resultado, _texto, _ctx):
        intent = str(resultado.get("intent") or "")
        if intent == "LEGACY_ONLY":
            return True
        if intent == "MODERNO_SEM_RECEIPT":
            marcar_tratamento_operacional(
                resultado,
                tratado=True,
                executou=None,
                confirmado=None,
                status="tratado_sem_receipt",
                retorno_legado=True,
            )
            return True
        if intent == "MODERNO_CONFIRMADO":
            marcar_tratamento_operacional(
                resultado,
                tratado=True,
                executou=True,
                confirmado=True,
                status="confirmado_teste",
                resultado_publicado=True,
                retorno_legado=True,
            )
            return True
        raise AssertionError(intent)

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor_falso)

    assert ciclo.executar_intencao({"intent": "LEGACY_ONLY"}, "legado") is True
    assert ciclo.executar_intencao(
        {"intent": "MODERNO_SEM_RECEIPT"}, "sem receipt"
    ) is True
    assert ciclo.executar_intencao(
        {"intent": "MODERNO_CONFIRMADO"}, "confirmado"
    ) is True

    contrato = ciclo.diagnostico_linguagem_natural()["contrato_execucao"]
    assert contrato["observados"] == 3
    assert contrato["legados"] == 1
    assert contrato["tratados_sem_receipt"] == 1
    assert contrato["confirmados"] == 1
    assert contrato["incertos"] == 0
    assert contrato["legados_por_intent"] == {"LEGACY_ONLY": 1}
    assert contrato["sem_receipt_por_intent"] == {"MODERNO_SEM_RECEIPT": 1}



def test_cadeia_canonica_exige_sucesso_e_para_dependentes(monkeypatch) -> None:
    chamadas = []

    def fluxo_falso(texto, origem, _ctx, **kwargs):
        chamadas.append({
            "texto": texto,
            "origem": origem,
            "estrito": kwargs.get("exigir_sucesso_habilidade"),
        })
        return False

    monkeypatch.setattr(
        coordenador_intencao,
        "executar_fluxo_intencao",
        fluxo_falso,
    )
    ciclo = _ciclo_execucao({
        "id": 1011,
        "modalidade": "comando",
        "autoriza_execucao": True,
    })

    assert ciclo.processar_cadeia(
        "abre a Calculadora, maximiza ela",
        "teste-cadeia-estrita",
    ) is True
    assert chamadas == [{
        "texto": "abre a Calculadora",
        "origem": "teste-cadeia-estrita-1",
        "estrito": True,
    }]
