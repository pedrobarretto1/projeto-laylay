"""RED arquitetural — repetição de leitura atravessa domínios.

R1-C2 responde uma pergunta específica:

    "Leia de novo." significa repetir FILE_READ
    ou repetir a última operação semanticamente compatível com LER?

Contrato protegido:

    EMAIL_READ
        -> IOT_CONTROL mais recente
        -> "Leia de novo."
        -> EMAIL_READ

A repetição genérica ("de novo") continua livre para repetir IOT_CONTROL.
Este teste não decide ainda como a classe semântica LER será representada.
"""

from __future__ import annotations

from typing import Any

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
    texto_pede_repeticao_curta,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    selecionar_continuidade_reexecutavel,
)


def _registrar_leitura_email(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "EMAIL_READ",
            "params": {},
            "status": "executado",
            "executou": True,
            "confirmado": True,
            "origem": "email",
        },
        "Leia meus emails.",
        True,
        origem="email",
        status="executado",
    )


def _registrar_iot(
    estado: dict[str, Any],
) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "desligar",
                "alvo": "lampada_quarto",
            },
            "alvo": "lampada_quarto",
            "status": "dispositivo_desligado",
            "executou": True,
            "confirmado": True,
            "origem": "iot",
        },
        "Desliga a lâmpada.",
        True,
        origem="iot",
        status="dispositivo_desligado",
    )


def _estado_email_depois_iot() -> dict[str, Any]:
    estado = estado_mental_inicial()
    estado = _registrar_leitura_email(estado)
    estado = _registrar_iot(estado)
    return estado


def test_guard_email_read_nasce_como_operacao_reexecutavel() -> None:
    """EMAIL_READ precisa existir como retry válido antes do conflito."""
    estado = _registrar_leitura_email(estado_mental_inicial())

    repetivel = selecionar_continuidade_reexecutavel(
        estado,
        classe="operacional",
        ttl_s=900.0,
    )

    assert repetivel
    assert repetivel["intent"] == "EMAIL_READ"
    assert repetivel["reexecutavel"] is True


def test_guard_iot_mais_recente_continua_vencendo_repeticao_generica() -> None:
    """C2 não pode quebrar a semântica legítima de 'de novo'."""
    estado = _estado_email_depois_iot()

    repeticao = resolver_repeticao_ultima_acao(
        "de novo",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "desligar",
            "alvo": "lampada_quarto",
        },
    }


def test_guard_cenario_nao_contem_file_read_escondido() -> None:
    """O RED precisa provar LER, não recuperar um arquivo por acidente."""
    estado = _estado_email_depois_iot()

    continuidade = dict(estado.get("continuidade_geral") or {})
    historico = [
        dict(item)
        for item in list(continuidade.get("historico") or [])
        if isinstance(item, dict)
    ]
    intents = {
        str(item.get("intent") or "").strip().upper()
        for item in historico
    }

    assert "EMAIL_READ" in intents
    assert "IOT_CONTROL" in intents
    assert "FILE_READ" not in intents

    assert texto_pede_repeticao_curta(
        "Leia de novo.",
        normalizar_texto_basico,
    ) is True


def test_red_leia_de_novo_retorna_ultima_leitura_compativel_email() -> None:
    """R1-C2: LER deve restringir o retry mesmo cruzando domínios."""
    estado = _estado_email_depois_iot()

    repeticao = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        normalizar_texto_basico,
    )

    assert repeticao is not None
    assert repeticao["intent"] == "EMAIL_READ"
