from __future__ import annotations

import time

from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno
from mente_laylay.memoria_mental.contexto_imediato import (
    ContextoImediatoRuntime,
    _dominio_restrito_referencia,
    _resultado_compativel_com_dominio,
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)
from mente_laylay.memoria_mental.registro_semantico import resolver_referencia_pontuada


def _continuidade(dominio, intent, alvo, params=None):
    agora = time.time()
    return {
        "versao": 1,
        "dominio_ativo": dominio,
        "dominios": {
            dominio: {
                "dominio": dominio, "intent": intent, "alvo": alvo,
                "params": dict(params or {}), "status": "executado",
                "ativa": True, "ts": agora, "expira_em": agora + 600.0,
            }
        },
        "historico": [], "ts": agora,
    }


def test_playlist_explicita_elimina_arquivo_antigo():
    agora = time.time()
    r = resolver_referencia_pontuada(
        "Mostra a playlist caos sonora e depois apaga ela.",
        entidades_recentes={
            "arquivo": {
                "tipo": "arquivo", "nome": "correcao.txt",
                "origem": "nome_explicito", "ts": agora - 1.0,
            },
            "playlist": {
                "tipo": "playlist", "nome": "caos sonora",
                "origem": "foco_mental", "ts": agora - 8.0,
            },
        },
        registro={}, agora=agora,
    )
    assert r["dominio_restrito"] == "musica"
    assert r["resolvida"]["tipo"] == "playlist"
    arquivo = next(x for x in r["candidatos"] if x["tipo"] == "arquivo")
    assert arquivo["compativel_dominio"] is False
    assert arquivo["pontuacao"] == 0.0


def test_apaga_pronome_mantem_playlist_ativa():
    estado = {
        "ts": time.time(),
        "continuidade_geral": _continuidade(
            "musica", "PLAYLIST_LIST", "caos sonora",
            {"nome_playlist": "caos sonora"},
        ),
        "ultima_acao_intent": "PLAYLIST_LIST",
        "ultima_acao_params": {"nome_playlist": "caos sonora"},
        "ultima_acao_promovivel": True,
    }
    ref = referencia_contextual_imediata(
        mente_integrada_estado=estado, foco_vivo={},
        texto_atual="apaga ela", ultima_playlist="caos sonora",
        normalizar_texto=lambda x: str(x).casefold(), ttl_s=300.0,
    )
    assert ref["tipo"] == "playlist"
    assert ref["alvo"] == "caos sonora"


def test_playlist_contextual_materializa_playlist_delete():
    r = resolver_comando_acao_geral_contextual(
        "apaga ela",
        {
            "tipo": "playlist", "alvo": "caos sonora",
            "intencao": "PLAYLIST_LIST",
            "params": {"nome_playlist": "caos sonora"},
        },
        ultima_playlist="caos sonora",
    )
    assert r["intent"] == "PLAYLIST_DELETE"
    assert r["params"]["nome_playlist"] == "caos sonora"


def test_dominio_musica_rejeita_delete_item():
    assert not _resultado_compativel_com_dominio(
        {"intent": "DELETE_ITEM", "params": {"alvo": "correcao.txt"}}, "musica"
    )
    assert _resultado_compativel_com_dominio(
        {"intent": "PLAYLIST_DELETE", "params": {"nome_playlist": "caos sonora"}},
        "musica",
    )


def test_pronome_mutante_usa_dominio_ativo():
    estado = {"continuidade_geral": _continuidade(
        "musica", "PLAYLIST_LIST", "caos sonora"
    )}
    assert _dominio_restrito_referencia("apaga ela", estado) == "musica"


def test_pronome_mutante_sem_dominio_falha_fechado():
    estado = {"continuidade_geral": {
        "dominio_ativo": "", "dominios": {}, "historico": [], "ts": time.time()
    }}
    assert _dominio_restrito_referencia("apaga ela", estado) == ""


def test_seletor_pronome_rejeita_foco_de_outro_dominio():
    agora = time.time()
    mente = {
        "continuidade_geral": _continuidade(
            "musica", "PLAYLIST_LIST", "caos sonora"
        ),
        "focos_por_dominio": {
            "arquivo": {"alvo": "correcao.txt", "topico": "correcao.txt", "ts": agora - 1},
            "musica": {"alvo": "caos sonora", "topico": "caos sonora", "ts": agora - 5},
        },
        "continuidade_fala_ts": agora,
    }
    r = selecionar_contexto_turno(
        "apaga ela",
        turno={"modalidade": "comando", "texto": "apaga ela", "texto_operacional": "apaga ela"},
        mente=mente, contexto_perceptivo={},
    )
    assert any(x["dominio"] == "musica" for x in r["selecionados"])
    assert not any(x["dominio"] == "arquivo" for x in r["selecionados"])


class EstadoFalso:
    def __init__(self, mental, ultima_playlist=""):
        self.mental = mental
        self._ultima_playlist = ultima_playlist

    def musica_get(self, chave):
        return self._ultima_playlist if chave == "ultima_playlist" else ""


class IoTAgressivo:
    def detectar(self, _texto, _mente):
        return {"intent": "IOT_CONTROL", "params": {"alvo": "lampada_quarto", "acao": "off"}}


def _runtime(mental, estrutura, ultima_playlist=""):
    estado = EstadoFalso(mental, ultima_playlist)
    servicos = {
        "_normalizar_texto_com_apelidos": lambda x: str(x).casefold().strip(),
        "_alvo_corrigido_atual": lambda: "",
        "_registrar_alvo_corrigido": lambda _x: None,
        "falar_com_lipsync": lambda *_a, **_k: None,
        "_contexto_musical_ativo": lambda: True,
        "_estrutura_arquivo_recente": lambda _ttl: dict(estrutura or {}),
        "_foco_vivo_atual": lambda **_k: {},
        "enviar_mensagem": None,
    }
    return ContextoImediatoRuntime(
        estado_runtime_getter=lambda: estado,
        servicos_iniciais=servicos, iot=IoTAgressivo(),
    )


def test_runtime_playlist_nao_cai_em_arquivo_nem_iot():
    mental = {
        "ts": time.time(), "ultima_acao_intent": "PLAYLIST_LIST",
        "ultima_intencao": "PLAYLIST_LIST", "ultima_habilidade": "playlist",
        "ultima_acao_params": {"nome_playlist": "caos sonora"},
        "ultima_acao_promovivel": True,
        "continuidade_geral": _continuidade(
            "musica", "PLAYLIST_LIST", "caos sonora",
            {"nome_playlist": "caos sonora"},
        ),
    }
    r = _runtime(
        mental,
        {"tipo": "arquivo", "caminho": r"C:\temp\correcao.txt", "arquivo_nome": "correcao.txt"},
        "caos sonora",
    ).resolver("apaga ela")
    assert r["intent"] == "PLAYLIST_DELETE"
    assert r["params"]["nome_playlist"] == "caos sonora"


def test_runtime_ambiguo_com_arquivo_antigo_nao_muta():
    mental = {
        "ts": time.time(), "ultima_acao_intent": "", "ultima_intencao": "",
        "ultima_habilidade": "", "ultima_acao_params": {},
        "continuidade_geral": {
            "dominio_ativo": "", "dominios": {}, "historico": [], "ts": time.time()
        },
    }
    r = _runtime(
        mental,
        {"tipo": "arquivo", "caminho": r"C:\temp\correcao.txt", "arquivo_nome": "correcao.txt"},
    ).resolver("apaga ela")
    assert r is None


def test_app_valido_continua_resolvendo_fecha_ele():
    mental = {
        "ts": time.time(), "ultima_acao_intent": "APP_OPEN",
        "ultima_intencao": "APP_OPEN", "ultima_habilidade": "janela",
        "ultima_acao_params": {"nome_app": "opera"},
        "ultima_acao_promovivel": True, "ultimo_app_janela": "opera",
        "ultima_acao_contrato": {
            "intent": "APP_OPEN", "alvo": "opera",
            "executou": True, "confirmado": True,
        },
        "continuidade_geral": _continuidade(
            "app", "APP_OPEN", "opera", {"nome_app": "opera"}
        ),
    }
    r = _runtime(mental, {}).resolver("fecha ele")
    assert r["intent"] == "CLOSE_APP"
    assert r["params"]["nome_app"] == "opera"

def test_deitico_anterior_usa_site_ativo():
    estado = {
        "ts": time.time(),
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultimo_site_aba": "prime video",
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        ),
    }
    assert _dominio_restrito_referencia(
        "Volta para a anterior.", estado, ttl_s=300.0
    ) == "site"


def test_site_ativo_materializa_switch_previous_tab():
    mental = {
        "ts": time.time(),
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultimo_site_aba": "prime video",
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        ),
    }
    resultado = _runtime(mental, estrutura={}).resolver(
        "Volta para a anterior."
    )
    assert resultado is not None
    assert resultado["intent"] == "SWITCH_PREVIOUS_TAB"


def test_fecha_essa_depois_de_site_vira_close_tab_nao_midia():
    mental = {
        "ts": time.time(),
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultimo_site_aba": "prime video",
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        ),
    }
    resultado = _runtime(mental, estrutura={}).resolver("Fecha essa.")
    assert resultado is not None
    assert resultado["intent"] == "CLOSE_TAB"
    assert resultado["params"]["alvo"] == "prime video"


def test_musica_anterior_explicita_continua_musica():
    mental = {
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        )
    }
    assert _dominio_restrito_referencia(
        "Volta para a música anterior.", mental, ttl_s=300.0
    ) == "musica"

