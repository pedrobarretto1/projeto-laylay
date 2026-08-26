"""Contratos arquiteturais das fachadas preservadas pela P11."""

from mente_laylay.autonomia import detectores_playlist, higiene_resposta_ia
from mente_laylay.autonomia import processamento_resposta_ia, roteador_deterministico
from mente_laylay.memoria_mental import diagnostico_mente, formatacao_diagnostico
from mente_laylay.percepcao import janelas_sistema, planejamento_janelas
from mente_laylay.personalidade import (
    classificacao_conversa,
    continuidade_conversa_natural,
    conversa_natural,
)


def test_fachada_conversa_delega_classificacao_e_continuidade() -> None:
    assert conversa_natural.classificar_conversa_curta_local is classificacao_conversa.classificar_conversa_curta_local
    assert conversa_natural.analisar_conversa_curta_ia is classificacao_conversa.analisar_conversa_curta_ia
    assert conversa_natural.contexto_recente_indica_email is continuidade_conversa_natural.contexto_recente_indica_email
    assert conversa_natural.retomar_topico_quando_fluido is continuidade_conversa_natural.retomar_topico_quando_fluido


def test_fachada_resposta_ia_delega_higiene() -> None:
    assert processamento_resposta_ia.limpar_resposta_da_ia is higiene_resposta_ia.limpar_resposta_da_ia
    assert (
        processamento_resposta_ia.corrigir_saida_malformada_da_ia
        is higiene_resposta_ia.corrigir_saida_malformada_da_ia
    )


def test_fachada_janelas_delega_planejamento() -> None:
    assert janelas_sistema.priorizar_janelas_visiveis is planejamento_janelas.priorizar_janelas_visiveis
    assert janelas_sistema.planejar_organizacao_janelas is planejamento_janelas.planejar_organizacao_janelas


def test_fachada_roteador_delega_playlists() -> None:
    assert roteador_deterministico.detectar_playlist_usuario is detectores_playlist.detectar_playlist_usuario
    assert roteador_deterministico.detectar_playlist_laylay is detectores_playlist.detectar_playlist_laylay


def test_fachada_diagnostico_delega_formatacao() -> None:
    assert diagnostico_mente.formatar_diagnostico_terminal is formatacao_diagnostico.formatar_diagnostico_terminal

