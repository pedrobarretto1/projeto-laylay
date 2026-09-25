from __future__ import annotations

import time

from mente_laylay.emocoes.avaliador_eventos import (
    AvaliadorEventosEmocionaisRuntime,
    contextualizar_fala_evento,
)
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def _resultado(
    status: str,
    *,
    intent: str = "APP_OPEN",
    alvo: str = "Opera",
    executou: bool = True,
    confirmado: bool = True,
    texto: str = "abre o opera",
    params: dict | None = None,
    contexto: dict | None = None,
) -> ResultadoAcao:
    return ResultadoAcao(
        intent=intent,
        status=status,
        alvo=alvo,
        executou=executou,
        confirmado=confirmado,
        texto_usuario=texto,
        params=params or {},
        contexto=contexto or {},
    )


def _evento_local(*, arco: str, repeticoes: int, provocacao: int) -> dict:
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="estado do Opera confirmado",
        evidencia_ref=f"resultado:opera:{repeticoes}",
        natureza_evidencia="fato_observado", responsabilidade="usuario",
        confianca=0.96, relevancia=0.95, novidade=0.5,
        intensidade=2, sensibilidade="normal", alvo="Opera",
        permite_expressao=True, emocao="debochada", nivel=2,
        arco=arco, ts=time.time(),
    )
    evento.update({"repeticoes": repeticoes, "provocacao_usuario": provocacao})
    return evento


def test_app_visivel_permite_provocacao_ao_usuario_com_evidencia_forte() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    avaliacao = runtime.avaliar(_resultado(
        "ja_aberto_focado", executou=False,
    ))

    assert avaliacao["responsabilidade"] == "usuario"
    assert avaliacao["confianca"] >= 0.90
    assert avaliacao["emocao"] == "debochada"
    assert avaliacao["provocacao_usuario"] == 1
    assert avaliacao["permite_expressao"] is True


def test_status_ja_satisfeito_sem_receipt_de_nao_acao_nao_culpa_usuario() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    for executou in (True, None):
        avaliacao = runtime.avaliar(_resultado(
            "ja_aberto_focado", executou=executou, confirmado=True,
        ))
        assert avaliacao["permite_expressao"] is False
        assert avaliacao["provocacao_usuario"] == 0
        assert avaliacao["responsabilidade"] != "usuario"


def test_repeticao_visivel_escala_ate_bronca_brava_sem_mudar_o_fato() -> None:
    agora = [100.0]
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: agora[0])
    primeira = runtime.avaliar(_resultado("ja_aberto_focado", executou=False))
    agora[0] += 2
    segunda = runtime.avaliar(_resultado("ja_aberto_focado", executou=False))
    agora[0] += 2
    terceira = runtime.avaliar(_resultado("ja_aberto_focado", executou=False))
    agora[0] += 2
    quarta = runtime.avaliar(_resultado("ja_aberto_focado", executou=False))

    assert primeira["emocao"] == "debochada"
    assert segunda["repeticoes"] == 2
    assert segunda["provocacao_usuario"] == 2
    assert segunda["nivel"] == 2
    assert terceira["emocao"] == "irritada"
    assert terceira["arco"] == "bronca_brincalhona"
    assert terceira["provocacao_usuario"] == 3
    assert quarta["emocao"] == "brava"
    assert quarta["nivel"] == 3
    assert quarta["provocacao_usuario"] == 3
    assert "4 pedidos redundantes" in quarta["causa"]


def test_bronca_brincalhona_local_fica_mais_forte_na_quarta_repeticao() -> None:
    fala = contextualizar_fala_evento(
        "Opera já estava aberto e em foco.",
        _evento_local(arco="bronca_brincalhona", repeticoes=4, provocacao=3),
    )

    assert fala.startswith("Opera já estava aberto e em foco.")
    assert "opera" in fala.casefold()
    assert any(marcador in fala.casefold() for marcador in ("quarta", "quatro"))
    assert len(fala.split(". ")) <= 2


def test_transcricao_de_baixa_confianca_nao_culpa_usuario() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    avaliacao = runtime.avaliar(_resultado(
        "ja_aberto_focado", executou=False, params={"confianca": 0.72},
    ))

    assert avaliacao["provocacao_usuario"] == 0
    assert avaliacao["permite_expressao"] is False
    assert avaliacao["emocao"] == "calma"


def test_vulnerabilidade_suspende_deboche_mesmo_com_app_visivel() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    avaliacao = runtime.avaliar(_resultado(
        "ja_aberto_focado", executou=False,
        texto="estou triste, abre o opera para mim",
    ))

    assert avaliacao["responsabilidade"] == "usuario"
    assert avaliacao["permite_expressao"] is False


def test_falha_repetida_do_sistema_gera_irritacao_compartilhada() -> None:
    agora = [100.0]
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: agora[0])
    falha = _resultado(
        "indisponivel", intent="IOT_CONTROL", alvo="lâmpada",
        executou=False, confirmado=False, texto="liga a luz",
    )
    primeira = runtime.avaliar(falha)
    agora[0] += 2
    segunda = runtime.avaliar(falha)
    agora[0] += 2
    terceira = runtime.avaliar(falha)

    assert primeira["emocao"] == "calma"
    assert segunda["emocao"] == "irritada"
    assert segunda["nivel"] == 1
    assert terceira["emocao"] == "irritada"
    assert terceira["nivel"] == 2
    assert terceira["responsabilidade"] == "sistema"


def test_sucesso_depois_de_falhas_cria_alivio_sem_apagar_historico() -> None:
    agora = [100.0]
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: agora[0])
    falha = _resultado(
        "indisponivel", intent="IOT_CONTROL", alvo="lâmpada",
        executou=False, confirmado=False, texto="liga a luz",
    )
    runtime.avaliar(falha)
    agora[0] += 1
    runtime.avaliar(falha)
    agora[0] += 1

    recuperacao = runtime.avaliar(_resultado(
        "ligado", intent="IOT_CONTROL", alvo="lâmpada", texto="tenta de novo",
    ))

    assert recuperacao["emocao"] == "acalmando-se"
    assert recuperacao["arco"] == "alivio"
    assert recuperacao["permite_expressao"] is True
    assert runtime.diagnostico()["recuperacoes"] == 1


def test_falha_ambigua_nao_inventa_culpado() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    avaliacao = runtime.avaliar(_resultado(
        "nao_encontrado", executou=False, confirmado=False,
    ))

    assert avaliacao["responsabilidade"] == "ambigua"
    assert avaliacao["permite_expressao"] is False


def test_responsabilidade_explicita_da_laylay_produz_autorreparo() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    avaliacao = runtime.avaliar(_resultado(
        "alvo_ausente",
        executou=False,
        confirmado=False,
        contexto={"responsabilidade": "laylay", "confianca_responsabilidade": 0.98},
    ))

    assert avaliacao["arco"] == "autorreparo"
    assert avaliacao["emocao"] == "envergonhada"
    assert avaliacao["permite_expressao"] is True


def test_expressao_preserva_resultado_e_acrescenta_uma_unica_tirada() -> None:
    fala = contextualizar_fala_evento(
        "Opera já estava aberto e em foco.",
        _evento_local(arco="provocacao_afetuosa", repeticoes=1, provocacao=1),
    )

    assert fala.startswith("Opera já estava aberto e em foco.")
    assert fala.casefold().count("opera") >= 2
    assert len(fala.split(". ")) <= 2


def test_nao_acao_confirmada_continua_sendo_redundancia_e_nao_falha() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)

    avaliacao = runtime.avaliar(_resultado(
        "ja_estava_ligado", executou=False, confirmado=True,
    ))

    assert avaliacao["responsabilidade"] == "usuario"
    assert avaliacao["arco"] == "provocacao_afetuosa"
    assert avaliacao["permite_expressao"] is True
