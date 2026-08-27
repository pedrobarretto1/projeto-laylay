from __future__ import annotations

import inspect

import mente_laylay.cognicao.orquestrador_turno_runtime as orq
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    turno_tem_veto_execucao,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)

MARCADOR = "ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826"
# ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip(" .,!?:;")


def _registrar(
    estado: dict,
    *,
    intent: str,
    params: dict,
    status: str,
    executou: bool,
    confirmado: bool,
    texto: str,
) -> dict:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": intent,
            "params": dict(params),
            "alvo": (
                params.get("alvo")
                or params.get("caminho")
                or ""
            ),
            "status": status,
            "executou": executou,
            "confirmado": confirmado,
            "origem": "test_r1_v2",
        },
        texto,
        executou,
        origem="test_r1_v2",
        status=status,
    )


def _estado_iot() -> dict:
    return _registrar(
        estado_mental_inicial(),
        intent="IOT_CONTROL",
        params={"acao": "ligar", "alvo": "lampada_quarto"},
        status="ligado",
        executou=True,
        confirmado=True,
        texto="Liga a lâmpada.",
    )


def _estado_leitura_depois_iot() -> dict:
    estado = _registrar(
        estado_mental_inicial(),
        intent="FILE_READ",
        params={
            "caminho": r"C:\tmp\r1_v2_alfa.txt",
            "alvo": "r1_v2_alfa.txt",
        },
        status="conteudo_lido",
        executou=True,
        confirmado=True,
        texto="Leia r1_v2_alfa.txt.",
    )
    return _registrar(
        estado,
        intent="IOT_CONTROL",
        params={"acao": "ligar", "alvo": "lampada_quarto"},
        status="ligado",
        executou=True,
        confirmado=True,
        texto="Liga a lâmpada.",
    )


def _estado_delete_falho() -> dict:
    return _registrar(
        estado_mental_inicial(),
        intent="DELETE_ITEM",
        params={"alvo": r"C:\tmp\r1_v2_inexistente.txt"},
        status="nao_encontrado",
        executou=False,
        confirmado=False,
        texto="Apaga r1_v2_inexistente.txt.",
    )


def _turno_stale(texto: str) -> dict:
    return {
        "id": "r1-v2-turno",
        "texto": texto,
        "normalizado": _normalizar(texto),
        "modalidade": "comando",
        "modalidade_geral": "comando",
        "ato_principal": "comando",
        "acao_explicita": True,
        "autoriza_execucao": True,
        "requer_esclarecimento": False,
        "depende_contexto": True,
        "natureza_acao": "pedido_direto",
        "confianca": 0.95,
    }


def _ns(estado: dict, resolver=None) -> dict:
    if resolver is None:
        resolver = lambda texto: resolver_repeticao_ultima_acao(
            texto,
            estado,
            _normalizar,
        )
    return {
        "_normalizar_texto_com_apelidos": _normalizar,
        "_resolver_repeticao_ultima_acao": resolver,
    }


def _aplicar(estado: dict, texto: str, resolver=None) -> tuple[dict, dict]:
    consulta = orq.consultar_repeticao_operacional_classificada_segura(
        _ns(estado, resolver=resolver),
        texto,
    )
    turno = orq.aplicar_contrato_repeticao_classificada_ao_turno(
        _turno_stale(texto),
        texto=texto,
        consulta=consulta,
    )
    return turno, consulta


def test_a_leia_de_novo_com_file_read_compativel_preserva_execucao() -> None:
    turno, consulta = _aplicar(
        _estado_leitura_depois_iot(),
        "Leia de novo.",
    )
    assert consulta["classificacao"]["tipo"] == "tipada"
    assert consulta["classificacao"]["acao_semantica"] == "LER"
    assert consulta["repeticao"]["intent"] == "FILE_READ"
    assert turno_tem_veto_execucao(turno) is False
    assert autoriza_execucao_efetiva(turno) is True
    assert turno["repeticao_operacional"]["intent"] == "FILE_READ"


def test_d_de_novo_generico_preserva_retry_iot() -> None:
    turno, consulta = _aplicar(_estado_iot(), "de novo")
    assert consulta["classificacao"]["tipo"] == "generica"
    assert consulta["repeticao"]["intent"] == "IOT_CONTROL"
    assert turno_tem_veto_execucao(turno) is False
    assert autoriza_execucao_efetiva(turno) is True
    assert turno["repeticao_operacional"]["intent"] == "IOT_CONTROL"


def test_e_leia_de_novo_so_com_iot_publica_veto_sticky() -> None:
    turno, consulta = _aplicar(_estado_iot(), "Leia de novo.")
    assert consulta["estado"] == "ok"
    assert consulta["classificacao"]["tipo"] == "tipada"
    assert consulta["classificacao"]["acao_semantica"] == "LER"
    assert consulta["repeticao"] is None
    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False
    assert turno["origem_veto_execucao_operacional"] == (
        "repeticao_tipificada_fail_closed"
    )
    assert turno["natureza_acao"] == (
        "repeticao_tipificada_sem_operacao_compativel"
    )


def test_f1_leia_de_novo_nao_pode_refazer_delete_falho() -> None:
    turno, consulta = _aplicar(
        _estado_delete_falho(),
        "Leia de novo.",
    )
    assert consulta["classificacao"]["tipo"] == "tipada"
    assert consulta["repeticao"] is None
    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False


def test_f2_tenta_de_novo_preserva_retry_delete_falho() -> None:
    turno, consulta = _aplicar(
        _estado_delete_falho(),
        "tenta de novo",
    )
    assert consulta["classificacao"]["tipo"] == "generica"
    assert consulta["repeticao"]["intent"] == "DELETE_ITEM"
    assert turno_tem_veto_execucao(turno) is False
    assert autoriza_execucao_efetiva(turno) is True
    assert turno["repeticao_operacional"]["intent"] == "DELETE_ITEM"


def test_killer_resolvedor_incompativel_nao_pode_dar_iot_a_ler() -> None:
    def resolver_defeituoso(_texto: str) -> dict:
        return {
            "intent": "IOT_CONTROL",
            "params": {"acao": "ligar", "alvo": "lampada_quarto"},
        }

    turno, consulta = _aplicar(
        _estado_iot(),
        "Leia de novo.",
        resolver=resolver_defeituoso,
    )
    assert consulta["classificacao"]["tipo"] == "tipada"
    assert consulta["repeticao"]["intent"] == "IOT_CONTROL"
    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False
    assert "incompatível" in turno["motivo"]


def test_killer_erro_do_resolvedor_nao_reabre_turno_tipado() -> None:
    def resolver_quebrado(_texto: str):
        raise RuntimeError("falha sintética R1-V2")

    turno, consulta = _aplicar(
        _estado_iot(),
        "Leia de novo.",
        resolver=resolver_quebrado,
    )
    assert consulta["estado"] == "resolver_erro"
    assert consulta["classificacao"]["tipo"] == "tipada"
    assert consulta["repeticao"] is None
    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False
    assert "resolvedor falhou" in turno["motivo"]


def test_killer_resolvedor_ausente_nao_reabre_turno_tipado() -> None:
    ns = {
        "_normalizar_texto_com_apelidos": _normalizar,
        "_resolver_repeticao_ultima_acao": None,
    }
    consulta = orq.consultar_repeticao_operacional_classificada_segura(
        ns,
        "Leia de novo.",
    )
    turno = orq.aplicar_contrato_repeticao_classificada_ao_turno(
        _turno_stale("Leia de novo."),
        texto="Leia de novo.",
        consulta=consulta,
    )
    assert consulta["estado"] == "resolver_indisponivel"
    assert consulta["classificacao"]["tipo"] == "tipada"
    assert turno_tem_veto_execucao(turno) is True
    assert autoriza_execucao_efetiva(turno) is False


def test_killer_veto_tipado_sobrevive_reautorizacao_stale() -> None:
    turno, _consulta = _aplicar(_estado_iot(), "Leia de novo.")
    reautorizado = orq.aplicar_repeticao_operacional_ao_turno(
        turno,
        {
            "intent": "IOT_CONTROL",
            "params": {"acao": "ligar", "alvo": "lampada_quarto"},
        },
    )
    assert reautorizado["autoriza_execucao"] is True
    assert turno_tem_veto_execucao(reautorizado) is True
    assert autoriza_execucao_efetiva(reautorizado) is False


def test_wiring_orquestrador_usa_consulta_e_contrato_classificados() -> None:
    fonte = inspect.getsource(orq)
    assert MARCADOR in fonte
    assert "consultar_repeticao_operacional_classificada_segura(ns, texto)" in fonte
    assert "aplicar_contrato_repeticao_classificada_ao_turno(" in fonte
    assert "origem_veto='repeticao_tipificada_fail_closed'" in fonte

# ROOT_R1_V2_EMAIL_URGENTES_C3_20260826
def test_c_email_read_urgentes_preserva_parametros_tipados_apos_iot() -> None:
    estado = _registrar(
        estado_mental_inicial(),
        intent="EMAIL_READ",
        params={"urgentes": True},
        status="executado",
        executou=True,
        confirmado=True,
        texto="Leia meus emails urgentes.",
    )
    estado = _registrar(
        estado,
        intent="IOT_CONTROL",
        params={"acao": "ligar", "alvo": "lampada_quarto"},
        status="ligado",
        executou=True,
        confirmado=True,
        texto="Liga a lâmpada.",
    )

    turno, consulta = _aplicar(
        estado,
        "Leia de novo.",
    )

    assert consulta["classificacao"]["tipo"] == "tipada"
    assert consulta["classificacao"]["acao_semantica"] == "LER"
    assert consulta["repeticao"] == {
        "intent": "EMAIL_READ",
        "params": {"urgentes": True},
    }
    assert turno_tem_veto_execucao(turno) is False
    assert autoriza_execucao_efetiva(turno) is True
    assert turno["repeticao_operacional"] == {
        "intent": "EMAIL_READ",
        "params": {"urgentes": True},
    }
