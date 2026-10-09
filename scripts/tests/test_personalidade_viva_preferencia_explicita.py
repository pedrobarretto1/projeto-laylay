from __future__ import annotations

import time
import math
from datetime import datetime
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("pedido", (
    "pega leve hoje nos comandos", "Laylay, vai com calma comigo sempre nos comandos",
    "pode me zoar mais nos comandos", "pode brincar mais comigo hoje nos comandos",
))
def test_preferencia_de_comandos_tem_escopo_proprio(pedido: str) -> None:
    preferencia = extrair_preferencia_humor(pedido, turno_id="comandos")
    assert preferencia.get("contexto") == "comandos"
    assert preferencia_humor_ativa(preferencia, contexto="comandos")
    assert not preferencia_humor_ativa(preferencia, contexto="conversa")
    assert not preferencia_humor_ativa(preferencia, contexto="jogo")
    assert preferencia["autoriza_execucao"] is False


def test_pega_leve_se_aplica_ao_tom_operacional_sem_mudar_resultado() -> None:
    preferencia = extrair_preferencia_humor("pega leve hoje", turno_id="leve")
    postura = selecionar_postura_amizade(
        "abra a calculadora", operacional=True,
        estado_mental={"preferencias_humor_contextuais": {"geral": preferencia}},
    )
    assert postura.nome == "operacional_amigavel"
    assert postura.humor == "bloqueado"
    assert postura.max_tirada == 0
    assert postura.permite_pergunta is False
    assert "resultado validado" in postura.objetivo


@pytest.mark.parametrize("tipo", ("conversa", "jogo"))
def test_preferencia_especifica_social_nao_muda_tom_de_comando(tipo: str) -> None:
    sufixo = "na conversa" if tipo == "conversa" else "no jogo"
    preferencia = extrair_preferencia_humor(f"pega leve hoje {sufixo}", turno_id="social")
    postura = selecionar_postura_amizade(
        "abra a calculadora", operacional=True,
        estado_mental={"modo_jogo_ativo": True,
            "preferencias_humor_contextuais": {tipo: preferencia}},
    )
    assert postura.humor == "somente_causal"


def test_abertura_operacional_nao_relaxa_limite_causal() -> None:
    preferencia = extrair_preferencia_humor("pode me zoar mais", turno_id="abertura")
    postura = selecionar_postura_amizade(
        "abra a calculadora", operacional=True,
        estado_mental={"preferencia_humor_contextual": preferencia},
    )
    assert postura.nome == "operacional_amigavel"
    assert postura.humor == "somente_causal" and postura.max_tirada == 1


@pytest.mark.parametrize("confianca", ("invalida", math.nan, math.inf, -math.inf))
def test_preferencia_duravel_invalida_fica_ausente_sem_interromper_turno(confianca) -> None:
    agora = time.time()
    valor = {"direcao": "leve", "contexto": "conversa"}
    hipotese = {"chave": "personalidade:tolerancia_humor:conversa", "status": "ativa",
        "confianca": confianca, "valor": valor}
    prova = {"confirmado_usuario": True, "origem": "pedido_explicito_usuario",
        "valor": valor, "evidencia": "turno:preferencia",
        "criado_em": datetime.fromtimestamp(agora - 1).isoformat(" ")}
    assert reconstruir_preferencia_humor_duravel(hipotese, prova, agora=agora) == {}


@pytest.mark.parametrize("pergunta", (
    "Você consegue pegar leve no humor?",
    "Você pode ajustar suas brincadeiras nos comandos?",
    "Você consegue respeitar minha preferência de humor?",
))
def test_catalogo_conhece_preferencia_explicita_e_limite_do_aprendizado(pergunta: str) -> None:
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime

    mapa = MapaHabilidadesRuntime()
    contexto = mapa.contexto_para_prompt(pergunta)
    resposta = mapa.responder_pergunta_capacidade(pergunta)
    assert "- personalidade [disponivel]" in contexto
    for texto in (contexto, resposta):
        assert "preferência explícita" in texto
        assert "jogo, conversa e comandos" in texto
        assert "recusa isolada" in texto
    assert mapa.responder_pergunta_capacidade("pega leve hoje") == ""
