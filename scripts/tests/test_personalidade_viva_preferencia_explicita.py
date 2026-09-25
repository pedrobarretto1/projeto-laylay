from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.preferencia_humor import (
    extrair_preferencia_humor,
    preferencia_humor_ativa,
    reconstruir_preferencia_humor_duravel,
    selecionar_preferencia_humor,
)
from mente_laylay.personalidade.perfil_amizade import selecionar_postura_amizade
from mente_laylay.personalidade.retrato_expressivo import construir_retrato_expressivo


def test_preferencia_explicita_e_imediata_no_prompt_e_diretor() -> None:
    agora = time.time()
    preferencia = extrair_preferencia_humor(
        "pega leve hoje", turno_id="p20-1", agora=agora,
    )
    mente = {"preferencia_humor_contextual": preferencia}

    postura = selecionar_postura_amizade("oi", estado_mental=mente)
    retrato = construir_retrato_expressivo("oi", estado_mental=mente)

    assert preferencia["origem"] == "usuario_explicito"
    assert preferencia["autoriza_execucao"] is False
    assert postura.nome == "amiga_suave"
    assert retrato.postura == "amiga_suave"
    assert retrato.orcamento_humor == 0


def test_abertura_para_brincadeira_nao_atravessa_vulnerabilidade() -> None:
    preferencia = extrair_preferencia_humor(
        "pode me zoar mais", turno_id="p20-2",
    )
    mente = {"preferencia_humor_contextual": preferencia}

    assert selecionar_postura_amizade("oi", estado_mental=mente).nome == "brincalhona"
    assert selecionar_postura_amizade(
        "kkk tô triste hoje", estado_mental=mente,
    ).nome == "acolhedora"


def test_preferencia_tem_contexto_prazo_e_nao_nasce_de_citacao() -> None:
    agora = time.time()
    preferencia = extrair_preferencia_humor(
        "pode me zoar mais hoje no jogo", turno_id="p20-3", agora=agora,
    )

    assert preferencia_humor_ativa(
        preferencia, contexto="jogo", agora=agora + 1,
    )
    assert not preferencia_humor_ativa(
        preferencia, contexto="conversa", agora=agora + 1,
    )
    assert selecionar_postura_amizade(
        "oi", estado_mental={
            "modo_jogo_ativo": True,
            "preferencias_humor_contextuais": {"jogo": preferencia},
        },
    ).nome == "brincalhona"
    assert selecionar_postura_amizade(
        "oi", estado_mental={
            "modo_jogo_ativo": False,
            "preferencias_humor_contextuais": {"jogo": preferencia},
        },
    ).nome == "amiga_descontraida"
    assert not preferencia_humor_ativa(
        preferencia, contexto="jogo", agora=agora + 86401,
    )
    assert not extrair_preferencia_humor(
        'escreva "pode me zoar mais" no arquivo', turno_id="p20-4",
    )


def test_composicao_real_do_turno_publica_preferencia_sem_autorizar_acao() -> None:
    from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1

    harness = _HarnessHS1()
    turno = harness.turnos.iniciar("pega leve hoje", origem="terminal")
    preferencia = harness.estado.mental["preferencia_humor_contextual"]

    assert turno["preferencia_humor"] == preferencia
    assert turno["autoriza_execucao"] is False
    assert preferencia["autoriza_execucao"] is False
    assert selecionar_postura_amizade(
        "oi", estado_mental=harness.estado.mental,
    ).nome == "amiga_suave"


def test_pedido_explicito_atual_substitui_preferencia_antiga_do_contexto() -> None:
    from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1

    harness = _HarnessHS1()
    anterior = extrair_preferencia_humor(
        "pode me zoar mais sempre na conversa",
        turno_id="antigo", agora=time.time() - 60,
    )
    harness.estado.atualizar_campos(
        "mental", preferencias_humor_contextuais={"conversa": anterior},
    )

    harness.turnos.iniciar("pega leve hoje", origem="terminal")

    assert harness.estado.mental["preferencia_humor_contextual"]["direcao"] == "leve"
    assert selecionar_postura_amizade(
        "oi", estado_mental=harness.estado.mental,
    ).nome == "amiga_suave"


def test_falha_da_persistencia_da_preferencia_nao_interrompe_turno() -> None:
    from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1

    harness = _HarnessHS1()

    def falhar(_preferencia: dict) -> None:
        raise OSError("banco indisponivel")

    harness.turnos._servicos["_registrar_preferencia_humor"] = falhar

    turno = harness.turnos.iniciar("pega leve sempre", origem="terminal")

    assert turno["preferencia_humor"]["direcao"] == "leve"
    assert harness.estado.mental["preferencia_humor_contextual"]["direcao"] == "leve"
    assert any("preferência de humor" in linha for linha in harness.logs)


def test_preferencia_duravel_so_retorna_com_evidencia_explicita() -> None:
    agora = time.time()
    hipotese = {
        "chave": "personalidade:tolerancia_humor:jogo",
        "status": "ativa", "confianca": 0.95,
        "valor": {"direcao": "leve", "contexto": "jogo"},
    }
    evidencia = {
        "confirmado_usuario": True,
        "origem": "pedido_explicito_usuario",
        "valor": hipotese["valor"],
        "evidencia": "turno:p20:preferencia_humor",
        "criado_em": datetime.fromtimestamp(agora - 60.0).isoformat(" "),
    }

    reconstruida = reconstruir_preferencia_humor_duravel(
        hipotese, evidencia, agora=agora,
    )

    assert preferencia_humor_ativa(
        reconstruida, contexto="jogo", agora=agora,
    )
    assert reconstruida["autoriza_execucao"] is False
    assert not reconstruir_preferencia_humor_duravel(
        hipotese, {**evidencia, "confirmado_usuario": False}, agora=agora,
    )
    assert not reconstruir_preferencia_humor_duravel(
        hipotese, {**evidencia, "valor": {"direcao": "mais_humor", "contexto": "jogo"}},
        agora=agora,
    )
    assert not reconstruir_preferencia_humor_duravel(
        hipotese, evidencia, agora=agora + 31536000.0,
    )


def test_pedido_geral_mais_recente_prevalece_sobre_aprendizado_do_contexto() -> None:
    agora = time.time()
    antigo = extrair_preferencia_humor(
        "pode me zoar mais sempre na conversa", turno_id="antigo", agora=agora - 60,
    )
    novo = extrair_preferencia_humor(
        "pega leve hoje", turno_id="novo", agora=agora,
    )

    preferencia = selecionar_preferencia_humor(
        {"conversa": antigo, "geral": novo}, contexto="conversa", agora=agora + 1,
    )

    assert preferencia["direcao"] == "leve"


def test_aprendizado_compartilhado_persiste_preferencia_explicita_com_proveniencia(
    tmp_path: Path,
) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "aprendizado.sqlite"))
    chave = "personalidade:tolerancia_humor:jogo"
    valor = {"direcao": "leve", "contexto": "jogo"}
    memoria.registrar_evidencia_aprendizado(
        chave=chave, tipo="preferencia_humor_explicita", escopo="jogo",
        valor=valor, sinal=1.0, origem="pedido_explicito_usuario",
        evidencia="turno:p20:preferencia_humor", confirmado_usuario=True,
    )

    hipotese = memoria.obter_hipotese_aprendizado(chave)
    evidencia = memoria.listar_eventos_aprendizado(chave, limit=1)[0]
    restaurada = reconstruir_preferencia_humor_duravel(
        hipotese, evidencia, agora=time.time(),
    )

    assert hipotese["status"] == "ativa"
    assert evidencia["confirmado_usuario"] is True
    assert restaurada["direcao"] == "leve"
    assert restaurada["autoriza_execucao"] is False
