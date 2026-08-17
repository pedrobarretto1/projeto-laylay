# -*- coding: utf-8 -*-
"""M1 / turno 149 — contrato revisado do candidato.

Fala real:
"Vai para a próxima faixa e adiciona essa também na caos sonora."

Escopo:
- reconhecer a primeira etapa sem promover ``vai`` globalmente;
- preservar autoridade do turno composto;
- reutilizar apenas a playlist recente realmente nomeada;
- provar o plano determinístico de duas etapas.
"""

from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.autonomia.detectores_playlist import (
    detectar_playlist_contextual_musica_atual,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno


FALA_M1 = "Vai para a próxima faixa e adiciona essa também na caos sonora."


def _params(**kwargs):
    return kwargs


def _limpar_nome(valor):
    return str(valor or "").strip(" .,!?:;")


# ---------------------------------------------------------------------------
# REDS DO BASELINE
# ---------------------------------------------------------------------------

def test_m1_red_01_segmenta_vai_e_adiciona_em_duas_etapas():
    partes = segmentar_comandos_em_cadeia(FALA_M1)
    assert partes == [
        "Vai para a próxima faixa",
        "adiciona essa também na caos sonora",
    ]


def test_m1_red_02_vai_para_proxima_faixa_concede_autoridade():
    turno = classificar_modalidade_turno("Vai para a próxima faixa.")
    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno
    assert turno["acao_explicita"] is True, turno


def test_m1_red_03_composto_inteiro_preserva_autoridade():
    turno = classificar_modalidade_turno(FALA_M1)
    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno
    assert turno["acao_explicita"] is True, turno


def test_m1_red_04_adiciona_essa_tambem_reusa_playlist_recente_nomeada():
    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa também na caos sonora",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "caos sonora", resultado
    assert resultado["params"].get("referencia_contextual") is True, resultado


def test_m1_red_05_fala_real_produz_duas_intencoes_na_ordem():
    turno = classificar_modalidade_turno(FALA_M1)
    assert turno["autoriza_execucao"] is True, turno

    partes = segmentar_comandos_em_cadeia(FALA_M1)
    assert len(partes) == 2, partes

    primeira = detectar_volume_ou_midia(
        partes[0].casefold(),
        params_cb=_params,
        contexto_musical_ativo=True,
    )
    segunda = detectar_playlist_contextual_musica_atual(
        partes[1].casefold(),
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )

    assert primeira and primeira["intent"] == "MEDIA_CONTROL", primeira
    assert primeira["params"]["acao"] == "next", primeira
    assert segunda and segunda["intent"] == "PLAYLIST_ADD", segunda
    assert segunda["params"]["nome_playlist"] == "caos sonora", segunda


# ---------------------------------------------------------------------------
# GUARDAS
# ---------------------------------------------------------------------------

def test_m1_guard_01_detector_midia_ja_enxerga_next_na_fala_real():
    resultado = detectar_volume_ou_midia(
        FALA_M1.casefold().strip(" .,!?:;"),
        params_cb=_params,
        contexto_musical_ativo=True,
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "MEDIA_CONTROL", resultado
    assert resultado["params"]["acao"] == "next", resultado


def test_m1_guard_02_proxima_faixa_canonica_continua_autorizada():
    turno = classificar_modalidade_turno("Próxima faixa.")
    assert turno["modalidade"] == "comando", turno
    assert turno["autoriza_execucao"] is True, turno


def test_m1_guard_03_vai_chover_nao_autoriza_execucao():
    turno = classificar_modalidade_turno("Vai chover amanhã.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_guard_04_narrativa_com_vai_nao_autoriza_execucao():
    turno = classificar_modalidade_turno("Meu irmão vai para a escola amanhã.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_guard_05_segmentador_nao_promove_vai_narrativo():
    texto = "Vai chover e depois adiciona essa música na playlist rock."
    partes = segmentar_comandos_em_cadeia(texto)
    assert len(partes) == 1, partes


def test_m1_guard_06_atalho_essa_tambem_existente_permanece_valido():
    resultado = detectar_playlist_contextual_musica_atual(
        "essa também",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "caos sonora", resultado
    assert resultado["params"].get("referencia_contextual") is True, resultado


def test_m1_guard_07_nome_diferente_nao_reusa_playlist_recente():
    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa também na rock",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert resultado is None, resultado


def test_m1_guard_08_forma_explicita_com_palavra_playlist_permanece_valida():
    resultado = detectar_playlist_contextual_musica_atual(
        "adiciona essa música na playlist rock",
        params_cb=_params,
        limpar_nome_playlist=_limpar_nome,
        ultima_playlist="caos sonora",
    )
    assert isinstance(resultado, dict), resultado
    assert resultado["intent"] == "PLAYLIST_ADD", resultado
    assert resultado["params"]["nome_playlist"] == "rock", resultado


def test_m1_guard_09_vai_para_proxima_reuniao_nao_autoriza():
    turno = classificar_modalidade_turno("Vai para a próxima reunião amanhã.")
    assert turno["autoriza_execucao"] is False, turno


def test_m1_guard_10_faixa_nao_musical_com_complemento_nao_autoriza():
    turno = classificar_modalidade_turno("Vai para a próxima faixa da estrada.")
    assert turno["autoriza_execucao"] is False, turno
