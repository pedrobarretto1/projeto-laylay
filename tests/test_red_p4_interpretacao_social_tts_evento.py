"""P4 RED — atitude social nasce na cognicao e governa a expressao do TTS."""

from __future__ import annotations

from typing import Any

from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
from mente_laylay.integracao.registro_conversa_llm import (
    PacotePrompt,
    PedidoModelo,
    ResultadoModelo,
)


def _evento_reves_apos_confianca() -> dict[str, Any]:
    return {
        "natureza": "evento",
        "origem": "observador_jogo",
        "tipo": "presenca_celebracao",
        "conteudo": (
            "Pedro caiu na primeira curva depois de afirmar que dominava a pista."
        ),
        "evidencia": {
            "descricao": (
                "Pedro caiu na primeira curva depois de afirmar que dominava a pista."
            ),
            "itens": ["queda confirmada", "primeira curva visivel"],
            "dominio": "jogo",
            "categoria": "celebracao",
        },
        "confianca": 0.98,
        "trace_id": "presenca:jogo:celebracao:queda-curva",
        "autoridade_usuario": False,
        "permissao_execucao": False,
    }


def test_red_p4_contrato_evento_materializa_direcao_social_estruturada() -> None:
    evento = _evento_reves_apos_confianca()

    contrato = construir_contrato_semantico_evento(
        evento,
        mente={"ultima_entrada": "Essa pista eu domino facil."},
    )

    direcao = dict(contrato["direcao_social"])
    assert direcao["gatilho"] == evento["trace_id"]
    assert direcao["alvo"] == "Pedro"
    assert direcao["objetivo"] == "provocar_brincando"
    assert direcao["atitude"] == "debochada"
    assert direcao["emocao"] == "debochada"
    assert direcao["nivel"] in {1, 2}
    assert direcao["confianca"] >= 0.90
    assert "pista" in direcao["ancora_contextual"].casefold()
    assert direcao["autoriza_execucao"] is False
    assert contrato["autoriza_execucao"] is False


def test_red_p4_vulnerabilidade_recente_veta_deboche_do_mesmo_evento() -> None:
    contrato = construir_contrato_semantico_evento(
        _evento_reves_apos_confianca(),
        mente={
            "ultima_entrada": (
                "Estou muito mal hoje; por favor fica comigo e sem piada agora."
            ),
        },
    )

    direcao = dict(contrato["direcao_social"])
    assert direcao["objetivo"] == "acompanhar_sem_deboche"
    assert direcao["atitude"] == "acolhedora"
    assert direcao["emocao"] in {"calma", "triste"}
    assert direcao["nivel"] == 1
    assert direcao["permite_humor"] is False
    assert direcao["autoriza_execucao"] is False


def test_p4_celebracao_sem_contraste_recente_nao_inventa_provocacao() -> None:
    evento = _evento_reves_apos_confianca()
    evento.update(
        conteudo="Pedro encontrou um item raro no fim da exploracao.",
        evidencia={
            **dict(evento["evidencia"]),
            "descricao": "Pedro encontrou um item raro no fim da exploracao.",
            "itens": ["item raro visivel", "coleta confirmada"],
        },
        trace_id="presenca:jogo:celebracao:item-raro",
    )

    contrato = construir_contrato_semantico_evento(
        evento,
        mente={"ultima_entrada": "Estou olhando o mapa dessa regiao."},
    )

    direcao = dict(contrato["direcao_social"])
    assert direcao["objetivo"] == "celebrar_junto"
    assert direcao["atitude"] == "animada"
    assert direcao["emocao"] == "alegre"
    assert direcao["autoriza_execucao"] is False


class _Prompt:
    def preparar_pacote(self, texto: str) -> PacotePrompt:
        assert texto == ""
        return PacotePrompt(mensagens=(
            {"role": "system", "content": "Personalidade canonica."},
        ))


class _Modelo:
    def __init__(self) -> None:
        self.pedidos: list[PedidoModelo] = []

    def executar(self, pedido: PedidoModelo) -> ResultadoModelo:
        self.pedidos.append(pedido)
        return ResultadoModelo(
            texto='{"fala":"E a pista era facil, ne?","comandos":[]}',
            sucesso=True,
            rota="teste",
        )


def test_red_p4_resposta_evento_usa_expressao_da_cognicao_nao_da_fonte() -> None:
    evento = _evento_reves_apos_confianca()
    contrato = construir_contrato_semantico_evento(
        evento,
        mente={"ultima_entrada": "Essa pista eu domino facil."},
    )
    turno = {
        "natureza_entrada": "evento",
        "entrada_cognitiva": evento,
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
        "contrato_fala": contrato,
    }
    agendamentos: list[tuple[Any, ...]] = []
    runtime = RespostaEventoRuntime(
        preparacao_prompt=_Prompt(),
        modelo_llm=_Modelo(),
        agendar_fala_proativa=lambda *args, **kwargs: (
            agendamentos.append((*args, kwargs)) or True
        ),
        limpar_texto_fala=lambda texto: texto,
        log=lambda _texto: None,
    )

    resultado = runtime.processar(
        turno,
        dominio="jogo",
        categoria="celebracao",
        # Uma fonte perceptiva pode sugerir qualquer tom; nao e dona dele.
        emocao="irritada",
        nivel=3,
    )

    assert resultado["status"] == "agendada"
    assert agendamentos == [(
        "presenca_jogo",
        "E a pista era facil, ne?",
        "debochada",
        contrato["direcao_social"]["nivel"],
        {},
    )]
    assert resultado["direcao_social"] == contrato["direcao_social"]
    assert resultado["autoriza_execucao"] is False
