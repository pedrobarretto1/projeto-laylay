from __future__ import annotations

from pathlib import Path

from mente_laylay.autonomia.preferencias_sugestoes_runtime import (
    DEPENDENCIAS_PREFERENCIAS_SUGESTOES,
)
from mente_laylay.cognicao.composicao_turno import DEPENDENCIAS_ORQUESTRACAO_TURNO
from mente_laylay.integracao.ambiente_navegacao import (
    DEPENDENCIAS_AMBIENTE_NAVEGACAO,
)
from mente_laylay.integracao.composicao_entrada_interacao import (
    DEPENDENCIAS_COMANDOS_IMEDIATOS,
    DEPENDENCIAS_CONTEXTO_CHAT,
    DEPENDENCIAS_DETECCAO,
)
from mente_laylay.integracao.composicao_estado_aplicacao import (
    DEPENDENCIAS_ADAPTADORES_APLICACAO,
    DEPENDENCIAS_ESTADO_CONTEXTO,
)
from mente_laylay.personalidade.composicao_resposta_conversacional import (
    DEPENDENCIAS_RESPOSTA_CONVERSACIONAL,
)
from mente_laylay.personalidade.orquestrador_fala_runtime import (
    DEPENDENCIAS_ORQUESTRADOR_FALA,
)


RAIZ = Path(__file__).resolve().parents[1]


def test_ponto_entrada_nao_reintroduz_consulta_global_continua() -> None:
    fonte = (RAIZ / "laylay.py").read_text(encoding="utf-8")

    assert "globals().get(" not in fonte
    assert "namespace_getter=lambda: globals()" not in fonte
    for linha in fonte.splitlines():
        if "globals()" not in linha:
            continue
        assert any(
            permitido in linha
            for permitido in (
                "servicos=globals()",
                "servicos_iniciais=globals()",
                "conectar_servicos(globals())",
                "globals(),",
            )
        ), f"uso global fora da composição: {linha.strip()}"


def test_contratos_filtrados_nao_declaram_credenciais_e_nao_duplicam_nomes() -> None:
    contratos = (
        DEPENDENCIAS_PREFERENCIAS_SUGESTOES,
        DEPENDENCIAS_ORQUESTRACAO_TURNO,
        DEPENDENCIAS_AMBIENTE_NAVEGACAO,
        DEPENDENCIAS_COMANDOS_IMEDIATOS,
        DEPENDENCIAS_CONTEXTO_CHAT,
        DEPENDENCIAS_DETECCAO,
        DEPENDENCIAS_ADAPTADORES_APLICACAO,
        DEPENDENCIAS_ESTADO_CONTEXTO,
        DEPENDENCIAS_RESPOSTA_CONVERSACIONAL,
        DEPENDENCIAS_ORQUESTRADOR_FALA,
    )
    marcadores_sensiveis = ("API_KEY", "PASSWORD", "SENHA", "SEGREDO", "SECRET")

    for contrato in contratos:
        assert len(contrato) == len(set(contrato))
        assert not any(
            marcador in nome.upper()
            for nome in contrato
            for marcador in marcadores_sensiveis
        )
