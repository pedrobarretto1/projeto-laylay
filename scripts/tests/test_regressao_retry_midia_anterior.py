from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
    resolver_repeticao_ultima_acao,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_musica_ou_playlist_direta,
    detectar_volume_ou_midia,
)


@pytest.mark.parametrize(
    "texto",
    (
        "coloca na musica de antes",
        "coloca a música de antes",
        "toca a faixa de antes",
    ),
)
def test_musica_de_antes_e_controle_prev_nao_busca(texto: str) -> None:
    assert detectar_volume_ou_midia(
        texto.casefold(),
        params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=True,
    ) == {
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "prev"},
    }


@pytest.mark.parametrize(
    "texto",
    (
        "coloca a musica anterior",
        "volta para a de antes",
        "coloca a musica de antes",
    ),
)
def test_cadeia_real_recupera_contexto_da_falha_prev_sem_playlist_ativa(
    texto: str,
) -> None:
    from mente_laylay.autonomia.roteador_deterministico import (
        texto_expresso_melhor_no_deterministico,
    )

    contexto = {
        "normalizar_texto": normalizar_texto,
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda fala: (
            texto_expresso_melhor_no_deterministico(
                fala,
                normalizar_texto=normalizar_texto,
            )
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda fala: fala,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "resolver_consulta_recurso_local": lambda _texto: None,
        # Reproduz o estado observado: nenhuma playlist própria ativa, mas o
        # último efeito musical foi a tentativa confirmadamente falha de prev.
        "contexto_musical_ativo": lambda: False,
        "mente_integrada_estado": {
            "ultima_acao_intent": "MEDIA_CONTROL",
            "ultima_acao_status": "falha_execucao",
            "ultima_acao_params": {"acao": "prev", "platform": "music"},
            "ultima_acao_ok": False,
            "ultima_acao_confirmada": False,
        },
        "sites_diretos": {},
        "apps_map": {},
    }

    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True
    assert turno["veto_execucao_operacional"] is False
    assert detectar_intencao_deterministica_mente(texto, contexto) == {
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "prev"},
    }


def test_guard_titulo_com_antes_continua_sendo_busca_musical() -> None:
    assert detectar_musica_ou_playlist_direta(
        "coloca a musica antes do amanhecer",
        "coloca a musica antes do amanhecer",
        "coloca a musica Antes do Amanhecer",
        params_cb=lambda **kwargs: kwargs,
        detectar_playlist_nome_direto=lambda _texto: "",
        normalizar_query_musical=lambda texto: texto,
    ) == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "musica antes do amanhecer"},
    }


def test_guard_musica_de_antes_sem_contexto_nao_inventa_busca() -> None:
    assert detectar_musica_ou_playlist_direta(
        "coloca a musica de antes",
        "coloca a musica de antes",
        "coloca a música de antes",
        params_cb=lambda **kwargs: kwargs,
        detectar_playlist_nome_direto=lambda _texto: "",
        normalizar_query_musical=lambda texto: texto,
    ) is None


def test_retry_de_falha_musical_atravessa_modalidade_conversacional() -> None:
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple[tuple, dict]] = []
    estado = SimpleNamespace(mental={
        "turno_atual": {
            "modalidade": "conversa",
            "modalidade_geral": "conversa",
            "autoriza_execucao": False,
            "natureza_acao": "nenhuma",
            "motivo": "fala sem marcador operacional dominante",
        },
    })
    repeticao = {
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "prev", "platform": "music"},
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_tem_comando_explicito": lambda _texto: False,
            "_resolver_repeticao_ultima_acao": (
                lambda texto: repeticao if texto == "tenta de novo" else None
            ),
            "executar_intencao": lambda comando, texto: (
                execucoes.append((dict(comando), texto)) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("tenta de novo") is True
    assert execucoes == [(repeticao, "tenta de novo")]
    assert registros[-1][1]["origem"] == "prioritario_repeticao_canonica"


def test_integracao_recibo_real_de_prev_falho_e_reexecutado() -> None:
    mental = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "MEDIA_CONTROL",
            "params": {"acao": "prev", "platform": "music"},
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
        },
        "volta para a anterior",
    )
    mental["turno_atual"] = {
        "modalidade": "conversa",
        "autoriza_execucao": False,
        "motivo": "fala sem marcador operacional dominante",
    }
    estado = SimpleNamespace(mental=mental)
    execucoes: list[dict] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_resolver_repeticao_ultima_acao": lambda texto: (
                resolver_repeticao_ultima_acao(texto, mental, str.casefold)
            ),
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(dict(comando)) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("tenta de novo") is True
    assert execucoes == [{
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "prev", "platform": "music"},
    }]


def test_guard_veto_soberano_impede_retry_mesmo_com_recibo() -> None:
    execucoes: list[dict] = []
    estado = SimpleNamespace(mental={
        "turno_atual": {
            "modalidade": "conversa",
            "autoriza_execucao": False,
            "veto_execucao_operacional": True,
        },
    })
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_tem_comando_explicito": lambda _texto: False,
            "_resolver_repeticao_ultima_acao": lambda _texto: {
                "intent": "MEDIA_CONTROL",
                "params": {"acao": "prev", "platform": "music"},
            },
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(dict(comando)) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("não tenta de novo") is False
    assert execucoes == []


def test_guard_sem_recibo_retry_curto_permanece_conversa() -> None:
    estado = SimpleNamespace(mental={
        "turno_atual": {
            "modalidade": "conversa",
            "autoriza_execucao": False,
            "motivo": "fala sem marcador operacional dominante",
        },
    })
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_tem_comando_explicito": lambda _texto: False,
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("tenta de novo") is False


def test_guard_recibo_nao_reexecutavel_nao_atravessa_modalidade() -> None:
    execucoes: list[dict] = []
    estado = SimpleNamespace(mental={
        "turno_atual": {"modalidade": "conversa", "autoriza_execucao": False},
    })
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_normalizar_texto_com_apelidos": str.casefold,
            "_texto_tem_comando_explicito": lambda _texto: False,
            "_resolver_repeticao_ultima_acao": lambda _texto: {
                "intent": "DELETE_ITEM",
                "params": {"alvo": "qualquer.txt"},
            },
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(dict(comando)) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("tenta de novo") is False
    assert execucoes == []


@pytest.mark.parametrize("comando", ("next", "prev"))
def test_guard_timeout_do_transporte_cobre_verificacao_da_extensao(
    comando: str,
) -> None:
    chamadas: list[tuple[dict, float]] = []
    contexto = {
        "ALLOWED_ACTIONS": {"youtube_control"},
        "ws_loop": object(),
        "connected_extensions": {"extensao"},
        "executar_chrome_confirmado": lambda mensagem, timeout_s: (
            chamadas.append((dict(mensagem), float(timeout_s))) or True
        ),
    }

    assert validar_e_enviar_comando(
        contexto,
        "youtube_control",
        {"command": comando},
    ) is True
    assert chamadas == [(
        {"action": "youtube_control", "command": comando},
        12.0 if comando == "prev" else 6.0,
    )]


def test_extensao_prev_aguarda_mudanca_sem_duplo_clique_cego() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "extençao_google" / "content_script.js").read_text(
        encoding="utf-8",
    )
    inicio = codigo.index('else if (cmd === "prev")')
    fim = codigo.index('else if (cmd === "replay")', inicio)
    bloco = codigo[inicio:fim]

    assert "const verifyPrev" in bloco
    assert "Date.now() - startedAt >= 2800" in bloco
    assert "setTimeout(verifyPrev, 120)" in bloco
    assert "beforeVideoId" in bloco and "currentVideoId" in bloco
    assert "currentVideoId === beforeVideoId" in bloco
    assert bloco.count("prevBtn.click()") == 1


def test_background_restaura_url_confirmada_quando_prev_do_player_nao_existe() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "extençao_google" / "background.js").read_text(
        encoding="utf-8",
    )
    bloco = codigo.split('if (cmd.action === "youtube_control") {', 1)[1].split(
        'if (cmd.action === "netflix_search") {', 1,
    )[0]

    assert "rememberConfirmedMediaNavigation" in bloco
    assert "restoreConfirmedPreviousMedia" in bloco
    assert "chrome.storage.session" in codigo
    assert 'comando === "next"' in bloco
    assert 'comando === "prev"' in bloco
    assert "previousUrl" in codigo and "currentUrl" in codigo
