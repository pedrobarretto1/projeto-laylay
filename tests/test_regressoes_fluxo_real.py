from __future__ import annotations

from unittest.mock import patch

from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas
from mente_laylay.autonomia.modo_chat import ModoChatRuntime
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_clima,
    detectar_musica_ou_playlist_direta,
)
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt
from mente_laylay.memoria_mental.playlist_mental import pedido_lista_geral_playlist
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.conversa_natural import (
    classificar_conversa_curta_local,
    responder_conversa_curta_por_tipo,
)
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def _params(**kwargs):
    return kwargs


def test_clima_aceita_qual_o_clima_de_boituva() -> None:
    resultado = detectar_clima("qual o clima de boituva", params_cb=_params)
    assert resultado == {"intent": "WEATHER", "params": {"local": "boituva"}}


def test_lista_geral_aceita_quais_minhas_playlists() -> None:
    assert pedido_lista_geral_playlist("quais minhas playlists", {})


def test_playlist_conhecida_vence_busca_generica_com_palavra_musica() -> None:
    resultado = detectar_musica_ou_playlist_direta(
        "coloca musica brasileira",
        texto_bruto="coloca música brasileira",
        params_cb=_params,
        detectar_playlist_nome_direto=lambda texto: "música brasileira" if "brasileira" in texto else "",
        normalizar_query_musical=lambda texto: texto,
    )
    assert resultado == {
        "intent": "PLAYLIST_PLAY",
        "params": {"nome_playlist": "música brasileira"},
    }


def test_erro_tduo_e_corrigido_sem_fuzzy_amplo() -> None:
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
    )
    assert runtime.normalizar_com_apelidos("tduo bem com voce lay?") == "tudo bem com voce lay?"
    ctx = {
        "_normalizar_texto_curto": lambda texto: str(texto).casefold(),
        "_normalizar_texto_com_apelidos": runtime.normalizar_com_apelidos,
    }
    assert classificar_conversa_curta_local(ctx, "tduo bem com voce lay?")["tipo"] == "WELLBEING"


def test_que_bom_e_reacao_breve_sem_pergunta_automatica() -> None:
    ctx = {
        "_normalizar_texto_curto": lambda texto: str(texto).casefold(),
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "mente_integrada_estado": {"ultima_resposta": "Tô bem, presente e prestando atenção em você."},
        "foco_vivo": {},
    }
    leitura = classificar_conversa_curta_local(ctx, "que bom lay")
    assert leitura["tipo"] == "POSITIVE_ACK"
    fala = responder_conversa_curta_por_tipo(ctx, leitura["tipo"], "que bom lay")
    assert "?" not in fala
    assert "como posso" not in fala.casefold()


def test_confirmacao_de_capacidade_climatica_nao_contradiz_execucao() -> None:
    ctx = {
        "_normalizar_texto_curto": lambda texto: str(texto).casefold(),
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "mente_integrada_estado": {
            "ultima_acao_intent": "WEATHER",
            "ultima_acao_confirmada": True,
        },
        "foco_vivo": {},
    }
    leitura = classificar_conversa_curta_local(ctx, "então você consegue ver o clima né")
    assert leitura["tipo"] == "CAPABILITY_CHECK"
    fala = responder_conversa_curta_por_tipo(ctx, leitura["tipo"], "então você consegue ver o clima né")
    assert "consigo sim" in fala.casefold()


def test_pergunta_tem_certeza_recebe_ultima_acao_no_contexto() -> None:
    texto = "tem certeza que você não consegue?"
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno)
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario=texto,
        ctx={},
        percepcao={},
        mente={
            "turno_atual": turno,
            "plano_turno_atual": plano,
            "ultima_acao_intent": "WEATHER",
            "ultima_acao_status": "clima_consultado",
            "ultima_acao_confirmada": True,
            "ultima_acao_ok": True,
            "ultima_acao_alvo": "Boituva",
            "ultima_afirmacao": "Agora em Boituva está 21 graus.",
            "continuidade_fala_ts": 9999999999.0,
        },
    )
    assert "Ultima acao real" in prompt
    assert "WEATHER" in prompt


def test_plano_preserva_status_real_do_comando() -> None:
    plano = planejar_turno("abre a steam", turno=classificar_modalidade_turno("abre a steam"))
    plano = atualizar_plano_turno(
        plano,
        fase="executado",
        comandos=[{
            "intent": "APP_OPEN", "alvo": "steam", "status": "app_focado",
            "executou": True, "confirmado": True,
        }],
    )
    assert plano["comandos"][0]["status"] == "app_focado"
    assert plano["comandos"][0]["confirmado"] is True


def test_jogo_lento_pode_aparecer_na_segunda_janela_de_confirmacao() -> None:
    leituras = {"total": 0}

    def estado(_nome):
        leituras["total"] += 1
        aberto = leituras["total"] >= 10
        return {"programa_aberto": aberto, "programa_em_foco": aberto}

    with patch("mente_laylay.autonomia.habilidade_janelas.time.sleep", lambda _s: None):
        resultado = executar_habilidade_janelas(
            "APP_OPEN",
            {"nome_app": "fragpunk"},
            {
                "APPS_MAP": {"fragpunk": "fragpunk"},
                "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
                "_resolver_alvo_ambiente": estado,
                "abrir_programa": lambda _nome: True,
                "focar_janela_app": lambda _nome: True,
            },
        )
    assert resultado["status"] == "app_focado"
    assert resultado["ok"] is True


def test_abertura_aceita_sem_processo_retorna_incerta_e_nao_falha() -> None:
    with patch("mente_laylay.autonomia.habilidade_janelas.time.sleep", lambda _s: None):
        resultado = executar_habilidade_janelas(
            "APP_OPEN",
            {"nome_app": "jogo lento"},
            {
                "APPS_MAP": {"jogo lento": "jogo lento"},
                "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
                "_resolver_alvo_ambiente": lambda _nome: {"programa_aberto": False},
                "abrir_programa": lambda _nome: True,
            },
        )
    assert resultado["status"] == "abertura_solicitada"
    assert resultado["ok"] is True


def test_fala_de_foco_nao_duplica_confirmacao_da_steam() -> None:
    fala = planejar_resposta_acao(
        ResultadoAcao(
            intent="APP_OPEN", status="app_focado", alvo="steam",
            executou=True, confirmado=True,
        ),
        "Steam já existia aí, só trouxe pro foco.",
    ).fala
    assert fala == "Steam já existia aí, só trouxe pro foco."


def test_chat_pode_abrir_sem_repetir_saudacao_recente() -> None:
    falas = []
    runtime = ModoChatRuntime(
        estado_getter=lambda: {"modo_chat": False},
        estado_setter=lambda _ativo: None,
        messages_getter=lambda: [],
        fala_confirmacao=lambda *_args, **_kwargs: "fallback",
        gerar_abertura=lambda: "Olá de novo.",
        falar=lambda fala, *_args: falas.append(fala),
        salvar_memoria=lambda: None,
        deve_emitir_fala=lambda ativo: not ativo,
    )
    resultado = runtime.definir(True, origem="hotkey")
    assert resultado["emitido"] is False
    assert falas == []
