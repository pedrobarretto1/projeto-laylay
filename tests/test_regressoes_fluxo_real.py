from __future__ import annotations

import time

from unittest.mock import patch

from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas
from mente_laylay.autonomia.modo_chat import ModoChatRuntime
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_clima,
    detectar_musica_ou_playlist_direta,
    detectar_playlist_laylay,
    detectar_playlist_usuario,
    extrair_intencao_abrir_app,
    preparar_entrada_deterministica,
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    DeteccaoDeterministicaRuntime,
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.coordenador_intencao import (
    resolver_intencao,
    resolver_referencias_da_intencao,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt
from mente_laylay.memoria_mental.contexto_compartilhado import texto_depende_de_contexto
from mente_laylay.memoria_mental.playlist_mental import pedido_lista_geral_playlist
from mente_laylay.memoria_mental.mapa_recursos import MapaRecursosRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.conversa_natural import (
    classificar_conversa_curta_local,
    responder_conversa_curta_por_tipo,
)
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def _params(**kwargs):
    return kwargs


def test_referencia_contextual_usa_palavras_inteiras() -> None:
    normalizar = lambda texto: str(texto).casefold()

    assert texto_depende_de_contexto("pesquisa isso", normalizar) is True
    assert texto_depende_de_contexto("abre o telefone", normalizar) is False


def test_busca_contextual_resolve_assunto_e_nunca_pesquisa_pronome_cru() -> None:
    retrato = {
        "referencia_resolvida": {"tipo": "jogo", "nome": "Hytale"},
    }
    resolvida = resolver_referencias_da_intencao(
        {"intent": "SEARCH", "params": {"query": "isso", "engine": "google"}},
        retrato,
    )

    assert resolvida is not None
    assert resolvida["params"]["query"] == "Hytale"
    assert resolvida["params"]["query_original"] == "isso"
    assert resolver_referencias_da_intencao(
        {"intent": "SEARCH", "params": {"query": "isso", "engine": "google"}},
        {},
    ) is None


def test_alvos_genericos_resolvem_por_dominio_e_bloqueiam_sem_memoria() -> None:
    app = resolver_referencias_da_intencao(
        {"intent": "APP_OPEN", "params": {"nome_app": "esse aplicativo"}},
        {"referencia_resolvida": {"tipo": "janela", "nome": "Visual Studio Code"}},
    )
    arquivo = resolver_referencias_da_intencao(
        {"intent": "DELETE_ITEM", "params": {"alvo": "esse arquivo"}},
        {"referencia_resolvida": {"tipo": "arquivo", "nome": "anotacoes.txt"}},
    )

    assert app is not None and app["params"]["nome_app"] == "Visual Studio Code"
    assert arquivo is not None and arquivo["params"]["alvo"] == "anotacoes.txt"
    assert resolver_referencias_da_intencao(
        {"intent": "DELETE_ITEM", "params": {"alvo": "esse arquivo"}}, {}
    ) is None


def test_app_composto_separa_filtro_de_foco_e_resolve_referencia() -> None:
    detectada = extrair_intencao_abrir_app(
        "abre ele e deixa em foco",
        normalizar_texto=lambda texto: str(texto).casefold(),
        limpar_destino=lambda texto: texto,
        apps_map={},
        sites_diretos={},
    )

    assert detectada == {
        "intent": "APP_OPEN",
        "params": {"nome_app": "ele", "modo": "focus"},
    }
    resolvida = resolver_referencias_da_intencao(
        detectada,
        {
            "referencia_resolvida": {
                "tipo": "janela",
                "nome": "Visual Studio Code",
            },
        },
    )
    assert resolvida == {
        "intent": "APP_OPEN",
        "params": {
            "nome_app": "Visual Studio Code",
            "nome_app_original": "ele",
            "modo": "focus",
            "referencia_contextual": True,
        },
    }
    assert resolver_referencias_da_intencao(detectada, {}) is None


def test_barreira_limpa_complemento_de_foco_de_qualquer_origem() -> None:
    resolvida = resolver_referencias_da_intencao(
        {
            "intent": "APP_OPEN",
            "params": {"nome_app": "Opera e deixa a janela em foco"},
        },
        {},
    )

    assert resolvida == {
        "intent": "APP_OPEN",
        "params": {"nome_app": "Opera", "modo": "focus"},
    }

    referencia = resolver_referencias_da_intencao(
        {
            "intent": "APP_OPEN",
            "params": {"nome_app": "ele e deixa em foco"},
        },
        {
            "referencia_resolvida": {
                "tipo": "app",
                "nome": "Opera",
            },
        },
    )
    assert referencia is not None
    assert referencia["params"]["nome_app"] == "Opera"
    assert referencia["params"]["nome_app_original"] == "ele"
    assert referencia["params"]["referencia_contextual"] is True
    assert referencia["params"]["modo"] == "focus"


def test_comando_composto_nao_executa_pronome_sem_referencia() -> None:
    assert resolver_referencias_da_intencao(
        {
            "intent": "APP_OPEN",
            "params": {"nome_app": "ela e traz pra frente"},
        },
        {},
    ) is None


def test_turno_real_limpa_comando_composto_antes_da_arbitragem() -> None:
    resultado, _rota = resolver_intencao(
        "abre ele e deixa em foco",
        "pre-ia",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "APP_OPEN",
                "params": {"nome_app": "ele e deixa em foco"},
            },
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "turno_atual": {"modalidade": "comando", "autoriza_execucao": True},
            "retrato_turno_atual": {
                "referencia_resolvida": {
                    "tipo": "janela",
                    "nome": "Visual Studio Code",
                },
            },
        },
    )

    assert resultado is not None
    assert resultado["intent"] == "APP_OPEN"
    assert resultado["params"]["nome_app"] == "Visual Studio Code"
    assert resultado["params"]["modo"] == "focus"


def test_fechar_essa_aba_e_comando_explicito_da_aba_atual() -> None:
    resultado, rota = resolver_intencao(
        "fecha essa aba",
        "pre-ia",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "CLOSE_TAB", "params": {},
            },
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "turno_atual": {"modalidade": "comando", "autoriza_execucao": True},
            "retrato_turno_atual": {},
        },
    )

    assert resultado == {"intent": "CLOSE_TAB", "params": {}}
    assert rota == "deterministico-explicito"


def test_musica_para_jogar_e_comando_local_mesmo_com_contexto_do_jogo() -> None:
    texto = "coloca uma musica para jogar minecraft"
    detector = detectar_musica_ou_playlist_direta(
        texto,
        params_cb=lambda **dados: dados,
        detectar_playlist_nome_direto=lambda _valor: "",
        normalizar_query_musical=lambda valor: str(valor).strip(),
    )
    chamadas_ia = []
    resultado, rota = resolver_intencao(
        texto,
        "pre-ia",
        {
            "normalizar_texto": lambda valor: str(valor).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: detector,
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: chamadas_ia.append(_texto),
            "registrar_arbitragem_turno": lambda *_args: None,
            "turno_atual": classificar_modalidade_turno(texto),
            "retrato_turno_atual": {"modo_jogo_ativo": True},
        },
    )

    assert resultado == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "musica para jogar minecraft"},
    }
    assert rota == "deterministico-explicito"
    assert chamadas_ia == []


def test_filtro_ia_first_nao_descarta_verbo_operacional_direto() -> None:
    preparo = preparar_entrada_deterministica(
        "coloca uma musica para jogar minecraft",
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_conversa_casual_sem_acao=lambda _texto: False,
        texto_bloqueia_playlist_agora=lambda _texto: False,
        texto_social_curto=lambda _texto: False,
        ignorar_token_solto=lambda _texto: False,
        # Reproduz a condição real que causava a regressão: o classificador
        # legado prefere IA sempre que encontra "coloca" e "musica".
        fluxo_prioritario_da_ia=lambda _texto: True,
        texto_expresso_melhor_no_deterministico=lambda _texto: False,
        texto_depende_de_contexto=lambda _texto: False,
        limpar_destino_pc_b=lambda texto: texto,
    )

    assert preparo["status"] == "ok"
    assert preparo["texto_normalizado"] == "coloca uma musica para jogar minecraft"


def test_filtro_ia_first_preserva_fala_ambigua_para_a_llm() -> None:
    preparo = preparar_entrada_deterministica(
        "essa musica seria legal aqui",
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_conversa_casual_sem_acao=lambda _texto: False,
        texto_bloqueia_playlist_agora=lambda _texto: False,
        texto_social_curto=lambda _texto: False,
        ignorar_token_solto=lambda _texto: False,
        fluxo_prioritario_da_ia=lambda _texto: True,
        texto_expresso_melhor_no_deterministico=lambda _texto: False,
        texto_depende_de_contexto=lambda _texto: False,
        limpar_destino_pc_b=lambda texto: texto,
    )

    assert preparo["status"] == "ignorar"


def test_busca_contextual_nao_e_descartada_antes_do_detector() -> None:
    preparo = preparar_entrada_deterministica(
        "pesquisa isso",
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_conversa_casual_sem_acao=lambda _texto: False,
        texto_bloqueia_playlist_agora=lambda _texto: False,
        texto_social_curto=lambda _texto: False,
        ignorar_token_solto=lambda _texto: False,
        fluxo_prioritario_da_ia=lambda _texto: False,
        texto_expresso_melhor_no_deterministico=lambda _texto: False,
        texto_depende_de_contexto=lambda _texto: True,
        limpar_destino_pc_b=lambda texto: texto,
    )

    assert preparo["status"] == "ok"


def test_comando_explicito_nao_e_desviado_para_ia_pelos_filtros_de_conversa() -> None:
    for texto in (
        "coloca essa música na playlist alternativo",
        "coloca o volume em 30",
        "pula esse anúncio",
        "abre a calculadora",
    ):
        preparo = preparar_entrada_deterministica(
            texto,
            normalizar_texto=lambda valor: str(valor).casefold(),
            texto_conversa_casual_sem_acao=lambda _valor: True,
            texto_bloqueia_playlist_agora=lambda _valor: False,
            texto_social_curto=lambda _valor: True,
            ignorar_token_solto=lambda _valor: False,
            fluxo_prioritario_da_ia=lambda _valor: True,
            texto_expresso_melhor_no_deterministico=lambda valor: (
                texto_expresso_melhor_no_deterministico(
                    valor, normalizar_texto=lambda item: str(item).casefold(),
                )
            ),
            texto_depende_de_contexto=lambda _valor: True,
            limpar_destino_pc_b=lambda valor: valor,
        )

        assert preparo["status"] == "ok", texto


def test_playlist_add_no_modo_jogo_chega_ao_roteador_local_mesmo_com_ia_prioritaria() -> None:
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(
                texto, normalizar_texto=lambda item: str(item).casefold(),
            )
        ),
        "texto_depende_de_contexto": lambda _texto: True,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "alternativo",
        "modo_jogo_contexto": lambda: {
            "ativo": True, "titulo": "Path of Exile 2", "processo": "poe2.exe",
        },
        "visao_jogo_tem_analise_recente": lambda: False,
        "sites_diretos": {}, "apps_map": {},
    }

    assert detectar_intencao_deterministica_mente(
        "coloca essa música na playlist alternativo", contexto,
    ) == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "alternativo"},
    }
    contexto["extrair_nome_playlist"] = lambda _texto: "rei do pop"
    assert detectar_intencao_deterministica_mente(
        "coloca a playlist rei do pop", contexto,
    ) == {
        "intent": "PLAYLIST_PLAY",
        "params": {"nome_playlist": "rei do pop"},
    }
    assert detectar_intencao_deterministica_mente(
        "coloca na playlist rei do pop", contexto,
    ) == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "rei do pop"},
    }
    assert detectar_intencao_deterministica_mente(
        "coloca o volume em 30", contexto,
    ) == {
        "intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 30},
    }
    assert detectar_intencao_deterministica_mente(
        "pula esse anúncio", contexto,
    ) == {
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "skip_ad", "platform": "youtube"},
    }
    contexto["extrair_intencao_abrir_app"] = lambda _texto: {
        "intent": "APP_OPEN", "params": {"nome_app": "calculadora"},
    }
    assert detectar_intencao_deterministica_mente(
        "abre a calculadora", contexto,
    ) == {
        "intent": "APP_OPEN", "params": {"nome_app": "calculadora"},
    }


def test_apagar_essa_playlist_resolve_nome_recente_antes_de_executar() -> None:
    detectada = detectar_playlist_usuario(
        "apaga essa playlist",
        params_cb=_params,
        limpar_nome_playlist=lambda texto: str(texto).strip(),
        extrair_nome_playlist=lambda _texto: "",
    )
    resolvida = resolver_referencias_da_intencao(
        detectada,
        {"referencia_resolvida": {"tipo": "playlist", "nome": "alternativo"}},
    )

    assert detectada == {
        "intent": "PLAYLIST_DELETE",
        "params": {"nome_playlist": "essa playlist"},
    }
    assert resolvida is not None
    assert resolvida["params"]["nome_playlist"] == "alternativo"
    assert resolver_referencias_da_intencao(detectada, {}) is None


def test_clima_aceita_qual_o_clima_de_boituva() -> None:
    resultado = detectar_clima("qual o clima de boituva", params_cb=_params)
    assert resultado == {"intent": "WEATHER", "params": {"local": "boituva"}}


def test_clima_de_hoje_e_prioritario_e_nao_inventa_localidade() -> None:
    assert texto_expresso_melhor_no_deterministico(
        "qual o clima de hoje",
        normalizar_texto=lambda texto: str(texto).casefold(),
    )
    assert detectar_clima("qual o clima de hoje", params_cb=_params) == {
        "intent": "WEATHER",
        "params": {},
    }


def test_lista_geral_aceita_quais_minhas_playlists() -> None:
    assert pedido_lista_geral_playlist("quais minhas playlists", {})


def test_playlists_criadas_pela_laylay_nao_herdam_a_ultima_do_usuario() -> None:
    for texto in (
        "quais playlists voce criou?",
        "quais playlists você montou?",
        "que playlists são suas?",
    ):
        assert detectar_playlist_laylay(
            texto,
            params_cb=_params,
            limpar_nome_playlist=lambda valor: str(valor).strip(),
        ) == {
            "intent": "LAYLAY_PLAYLIST_LIST",
            "params": {"nome_playlist": ""},
        }


def test_curadoria_entende_ordinal_reproducao_e_copia_contextual() -> None:
    limpar = lambda valor: str(valor).strip(" ?")
    assert detectar_playlist_laylay(
        "quais músicas tem na sua primeira playlist?",
        params_cb=_params,
        limpar_nome_playlist=limpar,
    ) == {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": {"nome_playlist": "#1"},
    }
    assert detectar_playlist_laylay(
        "toca uma das suas playlists",
        params_cb=_params,
        limpar_nome_playlist=limpar,
    ) == {
        "intent": "LAYLAY_PLAYLIST_PLAY",
        "params": {"nome_playlist": ""},
    }
    assert detectar_playlist_laylay(
        "copia uma música dessa playlist para minha playlist teste curadoria",
        params_cb=_params,
        limpar_nome_playlist=limpar,
        playlist_laylay_recente="xodós que eu separei",
    ) == {
        "intent": "LAYLAY_PLAYLIST_COPY",
        "params": {
            "musica": "__primeira__",
            "origem": "xodós que eu separei",
            "destino": "teste curadoria",
            "referencia_contextual": True,
        },
    }


def test_lista_geral_de_playlist_e_consulta_local_autorizada() -> None:
    turno = classificar_modalidade_turno("quais minhas playlists")

    assert turno["modalidade"] == "comando"
    assert turno["natureza_acao"] == "consulta"
    assert turno["autoriza_execucao"] is True


def test_consulta_natural_de_faixas_nomeadas_e_operacao_de_leitura() -> None:
    texto = "quais músicas eu tenho em kamaitachi"
    turno = classificar_modalidade_turno(texto)
    detectada = detectar_playlist_usuario(
        texto,
        params_cb=_params,
        limpar_nome_playlist=lambda valor: str(valor).strip(),
        extrair_nome_playlist=lambda _texto: "",
    )

    assert turno["modalidade"] == "comando"
    assert turno["natureza_acao"] == "consulta"
    assert turno["autoriza_execucao"] is True
    assert detectada == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "kamaitachi"},
    }


def test_quantidade_de_playlist_com_nome_repetido_e_lida_localmente() -> None:
    texto = "quantas musicas tem a playlist sendo sendo"
    turno = classificar_modalidade_turno(texto)
    detectada = detectar_playlist_usuario(
        texto,
        params_cb=_params,
        limpar_nome_playlist=lambda valor: str(valor).strip(),
        extrair_nome_playlist=lambda _texto: "",
    )

    assert turno["modalidade"] == "comando"
    assert turno["natureza_acao"] == "consulta"
    assert turno["autoriza_execucao"] is True
    assert detectada == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "sendo sendo"},
    }


def test_variantes_de_quantidade_preservam_nome_completo_da_playlist() -> None:
    casos = (
        "quantas faixas existem na playlist sendo sendo?",
        "quais músicas a playlist sendo sendo tem?",
    )

    for texto in casos:
        assert detectar_playlist_usuario(
            texto,
            params_cb=_params,
            limpar_nome_playlist=lambda valor: str(valor).strip().rstrip("?"),
            extrair_nome_playlist=lambda _texto: "",
        ) == {
            "intent": "PLAYLIST_LIST",
            "params": {"nome_playlist": "sendo sendo"},
        }


def test_o_que_tem_em_nome_real_consulta_playlist_sem_inventar_assunto() -> None:
    resolver_nome = lambda nome: "kamaitachi" if str(nome).strip() == "kamaitachi" else ""
    detectada = detectar_playlist_usuario(
        "o que tem em kamaitachi",
        params_cb=_params,
        limpar_nome_playlist=lambda valor: str(valor).strip(),
        extrair_nome_playlist=lambda _texto: "",
        detectar_playlist_nome_direto=resolver_nome,
    )
    desconhecida = detectar_playlist_usuario(
        "o que tem em boituva",
        params_cb=_params,
        limpar_nome_playlist=lambda valor: str(valor).strip(),
        extrair_nome_playlist=lambda _texto: "",
        detectar_playlist_nome_direto=resolver_nome,
    )

    assert detectada == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "kamaitachi"},
    }
    assert desconhecida is None


def test_consulta_natural_de_playlist_vence_conversa_generativa() -> None:
    resultado, rota = resolver_intencao(
        "o que tem em kamaitachi",
        "pre-ia",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: False,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "PLAYLIST_LIST",
                "params": {"nome_playlist": "kamaitachi"},
            },
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
                AssertionError("uma playlist real deve ser lida antes da conversa")
            ),
            "turno_atual": classificar_modalidade_turno("o que tem em kamaitachi"),
            "retrato_turno_atual": {},
            "registrar_arbitragem_turno": lambda *_args: None,
        },
    )

    assert rota == "deterministico"
    assert resultado == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "kamaitachi"},
    }


def test_consulta_de_recurso_atravessa_o_roteador_real_antes_do_filtro_casual() -> None:
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "modo_jogo_contexto": lambda: {},
        "visao_jogo_tem_analise_recente": lambda: False,
        "resolver_consulta_recurso_local": lambda texto: (
            {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": "trap"}}
            if "trap" in texto.casefold() else None
        ),
        "sites_diretos": {},
        "apps_map": {},
    }

    assert detectar_intencao_deterministica_mente("o que tem em trap", contexto) == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "trap"},
    }


def test_lista_iot_atravessa_filtro_casual_como_leitura_segura() -> None:
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda texto, _estado: (
            {"intent": "IOT_LIST", "params": {"ambiente": ""}}
            if "dispositivos" in texto else None
        ),
        "detectar_sugestao_indireta": lambda *_args: None,
        "modo_jogo_contexto": lambda: {},
        "visao_jogo_tem_analise_recente": lambda: False,
        "resolver_consulta_recurso_local": lambda _texto: None,
        "sites_diretos": {},
        "apps_map": {},
    }

    assert detectar_intencao_deterministica_mente(
        "quais dispositivos estão disponíveis?", contexto,
    ) == {"intent": "IOT_LIST", "params": {"ambiente": ""}}


def test_runtime_real_injeta_resolvedor_geral_de_recursos() -> None:
    namespace = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_bloqueia_playlist_agora": lambda _texto: False,
        "_texto_social_curto": lambda _texto: True,
        "_ignorar_token_solto": lambda _texto: False,
        "_fluxo_prioritario_da_ia": lambda _texto: True,
        "_texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "_texto_depende_de_contexto": lambda _texto: False,
        "_limpar_destino_pc_b": lambda texto: texto,
        "_target_from_params": lambda _params, _texto: "pc_a",
        "_detectar_intencao_iot": lambda *_args: None,
        "_detectar_sugestao_indireta": lambda *_args: None,
        "_resolver_consulta_recurso_local": lambda texto: (
            {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": "kamaitachi"}}
            if "kamaitachi" in texto.casefold() else None
        ),
    }
    runtime = DeteccaoDeterministicaRuntime(
        namespace_getter=lambda: namespace,
        estado_getter=lambda: {},
        sites_diretos={},
        apps_map={},
    )

    assert runtime.detectar("o que tem em kamaitachi?") == {
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "kamaitachi"},
    }


def test_lista_geral_chega_ao_intent_local_sem_passar_pela_llm() -> None:
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "",
        "sites_diretos": {},
        "apps_map": {},
    }

    assert detectar_intencao_deterministica_mente(
        "quais minhas playlists", contexto
    ) == {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": ""}}


def test_autoria_da_curadoria_atravessa_o_roteador_com_intent_proprio() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists do usuário",
        termos=("playlist", "playlists"),
        leitor=lambda _texto: {"playlists": [{"nome": "anime", "total": 24}]},
        intent_consulta="PLAYLIST_LIST",
    )
    mapa.registrar(
        "playlists_laylay",
        arquivo="playlists_da_laylay.json",
        descricao="curadorias da Laylay",
        termos=("suas playlists", "playlists que voce criou", "playlists voce criou"),
        leitor=lambda _texto: {
            "playlists": [{"nome": "xodos_que_eu_seperei", "total": 20}],
        },
        intent_consulta="LAYLAY_PLAYLIST_LIST",
    )
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: True,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "anime",
        "sites_diretos": {},
        "apps_map": {},
        # É a mesma precedência do caminho real: o mapa de recursos roda antes
        # dos detectores de domínio. A regressão só está coberta se a autoria
        # sobreviver a essa etapa, e não apenas ao detector isolado.
        "resolver_consulta_recurso_local": mapa.resolver_consulta,
    }

    assert detectar_intencao_deterministica_mente(
        "quais playlists voce criou?", contexto,
    ) == {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": {},
    }


def test_adicionar_faixa_em_playlist_explicita_vence_ia_com_contexto() -> None:
    resultado, rota = resolver_intencao(
        "coloca essa música na playlist alternativo",
        "pre-ia",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "PLAYLIST_ADD",
                "params": {"nome_playlist": "alternativo"},
            },
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
                AssertionError("pedido explícito não pode cair na IA")
            ),
            "turno_atual": {"modalidade": "comando", "autoriza_execucao": True},
            "retrato_turno_atual": {
                "operacao_explicita": "playlist_adicionar",
                "intents_permitidos": ["PLAYLIST_ADD"],
            },
            "registrar_arbitragem_turno": lambda *_args: None,
        },
    )
    assert rota == "deterministico-explicito"
    assert resultado == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "alternativo"},
    }


def test_playlist_add_prioriza_faixa_registrada_pelo_player() -> None:
    adicionadas = []
    falas = []
    estado = {
        "musica_atual_titulo": "Duality - Slipknot",
        "musica_atual_url": "https://www.youtube.com/watch?v=6fVE8kSM43I",
        "musica_atual_status": "tocando",
        "musica_atual_ts": __import__("time").time(),
    }
    class _Operacoes:
        def faixa_atual(self):
            return {
                "url": estado["musica_atual_url"],
                "title": estado["musica_atual_titulo"],
                "canal": "",
            }

        def adicionar_faixa(self, nome, url, titulo, canal):
            adicionadas.append((nome, url, titulo, canal))
            return True

        def definir_ultima_playlist(self, _nome):
            return None

    assert executar_intencao(
        {"intent": "PLAYLIST_ADD", "params": {"nome_playlist": "alternativo"}},
        "coloca essa música na playlist alternativo",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_musica_estado_get": lambda chave, padrao=None: estado.get(chave, padrao),
            "solicitar_aba_ativa": lambda: (_ for _ in ()).throw(
                AssertionError("a aba é apenas fallback")
            ),
            "ADD_TO_PLAYLIST": lambda nome, url, titulo, canal: (
                adicionadas.append((nome, url, titulo, canal)) or True
            ),
            "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "set_ultima_playlist": lambda _valor: None,
            "_yt_clean_title": lambda titulo: titulo,
            "_registro_musica_operacoes_runtime": _Operacoes(),
        },
    ) is True
    assert adicionadas == [(
        "alternativo",
        "https://www.youtube.com/watch?v=6fVE8kSM43I",
        "Duality - Slipknot",
        "",
    )]
    assert falas and "alternativo" in falas[0]


def test_coordenador_escolhe_inventario_local_e_nao_consulta_llm() -> None:
    texto = "quais minhas playlists"
    turno = classificar_modalidade_turno(texto)
    contexto = {
        "normalizar_texto": lambda valor: str(valor).casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "extrair_agendamento": lambda _texto: None,
        "extrair_acao_agendada": lambda _texto: None,
        "texto_cancela_acao_agora": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: {
            "intent": "PLAYLIST_LIST", "params": {"nome_playlist": ""},
        },
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "interpretar_comando_local_rapido": lambda _texto: None,
        "analisar_intencao": lambda _texto: (_ for _ in ()).throw(
            AssertionError("a LLM não pode listar o inventário local")
        ),
        "retrato_turno_atual": {
            "modalidade": turno["modalidade"],
            "autoriza_execucao": turno["autoriza_execucao"],
        },
    }

    resultado, rota = resolver_intencao(texto, "teste", contexto)

    assert rota == "deterministico"
    assert resultado == {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": ""}}


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


def test_opiniao_sobre_genero_homonimo_nao_toca_nem_lista_playlist() -> None:
    for frase in (
        "o que você acha de rock?",
        "o que acha do gênero rock?",
        "acha do gênero rock?",
    ):
        resultado = detectar_musica_ou_playlist_direta(
            frase,
            texto_bruto=frase,
            params_cb=_params,
            detectar_playlist_nome_direto=lambda texto: (
                "rock" if "rock" in texto.casefold() else ""
            ),
            normalizar_query_musical=lambda texto: texto,
        )
        assert resultado is None


def test_opiniao_sobre_rock_atravessa_roteador_real_sem_comando() -> None:
    mapa = MapaRecursosRuntime()
    mapa.registrar(
        "playlists_usuario",
        arquivo="playlists.json",
        descricao="playlists reais",
        termos=("playlist", "musicas salvas"),
        leitor=lambda texto: {
            "detalhe": (
                {"nome": "rock", "titulos": ["Faixa real"]}
                if "rock" in texto.casefold() else {}
            ),
        },
        intent_consulta="PLAYLIST_LIST",
        parametro_detalhe="nome_playlist",
    )
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "modo_jogo_contexto": lambda: {},
        "visao_jogo_tem_analise_recente": lambda: False,
        "resolver_consulta_recurso_local": mapa.resolver_consulta,
        "detectar_playlist_nome_direto": lambda texto: (
            "rock" if "rock" in str(texto).casefold() else ""
        ),
        "normalizar_query_musical": lambda texto: texto,
        "sites_diretos": {},
        "apps_map": {},
    }

    assert detectar_intencao_deterministica_mente(
        "o que você acha de rock?", contexto,
    ) is None
    assert detectar_intencao_deterministica_mente(
        "o que tem em rock?", contexto,
    ) == {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": "rock"}}


def test_formas_naturais_de_acha_chegam_ao_classificador_de_opiniao() -> None:
    contexto = {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "mente_integrada_estado": {},
    }
    for frase in (
        "o que você acha de rock?",
        "o que acha do gênero rock?",
        "acha do gênero rock?",
        "qual sua opinião sobre rock?",
    ):
        assert classificar_conversa_curta_local(contexto, frase)["tipo"] == "OPINION"


def test_rock_pesado_preserva_genero_em_vez_de_abrir_playlist_rock() -> None:
    from mente_laylay.memoria_mental.playlist_mental import detectar_playlist_nome_direto

    playlists = {"rock": [{"url": "https://example.test/rock"}]}
    resultado = detectar_musica_ou_playlist_direta(
        "coloca um rock pesado",
        texto_sem_destino="coloca um rock pesado",
        texto_bruto="coloca um rock pesado",
        params_cb=_params,
        detectar_playlist_nome_direto=lambda texto: detectar_playlist_nome_direto(
            texto, playlists
        ),
        normalizar_query_musical=lambda texto: texto,
    )

    assert resultado == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "rock pesado"},
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


def test_playlit_e_corrigido_no_normalizador_canonico_e_lista_inventario() -> None:
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
    )

    normalizado = runtime.normalizar_com_apelidos("quais sao minha playlit")

    assert normalizado == "quais sao minha playlist"
    assert pedido_lista_geral_playlist(normalizado, {}) is True
    assert detectar_playlist_usuario(
        normalizado,
        texto_bruto="quais sao minha playlit",
        params_cb=_params,
        limpar_nome_playlist=lambda valor: str(valor or "").strip(),
        extrair_nome_playlist=lambda _texto: "",
    ) == {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": ""}}


def test_playlit_em_pedido_de_reproducao_vira_playlist_play() -> None:
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
    )
    normalizado = runtime.normalizar_com_apelidos("coloca a playlit sendo sendo")

    assert normalizado == "coloca a playlist sendo sendo"
    assert detectar_musica_ou_playlist_direta(
        normalizado,
        texto_bruto="coloca a playlit sendo sendo",
        params_cb=_params,
        detectar_playlist_nome_direto=lambda texto: (
            "sendo sendo" if "sendo sendo" in texto else ""
        ),
        normalizar_query_musical=lambda texto: texto,
    ) == {
        "intent": "PLAYLIST_PLAY",
        "params": {"nome_playlist": "sendo sendo"},
    }


def test_plaulist_em_pedido_de_reproducao_vira_playlist_play() -> None:
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
    )
    normalizado = runtime.normalizar_com_apelidos("coloca a plaulist sendo sendo")

    assert normalizado == "coloca a playlist sendo sendo"
    assert detectar_musica_ou_playlist_direta(
        normalizado,
        texto_bruto="coloca a plaulist sendo sendo",
        params_cb=_params,
        detectar_playlist_nome_direto=lambda texto: (
            "sendo sendo" if "sendo sendo" in texto else ""
        ),
        normalizar_query_musical=lambda texto: texto,
    ) == {
        "intent": "PLAYLIST_PLAY",
        "params": {"nome_playlist": "sendo sendo"},
    }


def test_coordenador_preserva_busca_de_codigo_se_detector_composto_degradar() -> None:
    texto = "encontra o código que controla a lâmpada"
    resultado, rota = resolver_intencao(texto, "terminal", {
        "normalizar_texto": lambda valor: str(valor or "").casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "retrato_turno_atual": {
            "modalidade": "comando", "autoriza_execucao": True,
        },
        "turno_atual": {
            "modalidade": "comando", "autoriza_execucao": True,
        },
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: None,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
            AssertionError("a busca local não deve depender da LLM")
        ),
    })

    assert rota == "deterministico-explicito"
    assert resultado == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "código que controla a lâmpada",
            "somente_projeto": False,
        },
    }


def test_coordenador_preserva_busca_de_codigo_quando_detector_retorna_none_json() -> None:
    texto = "encontra o código que controla a lâmpada"
    resultado, rota = resolver_intencao(texto, "terminal", {
        "normalizar_texto": lambda valor: str(valor or "").casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "retrato_turno_atual": {
            "modalidade": "comando", "autoriza_execucao": True,
        },
        "turno_atual": {
            "modalidade": "comando", "autoriza_execucao": True,
        },
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: {
            "intent": "NONE", "params": {},
        },
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
            AssertionError("a busca local não deve depender da LLM")
        ),
    })

    assert rota == "deterministico-explicito"
    assert resultado["intent"] == "FILE_SEARCH"
    assert resultado["params"]["query"] == "código que controla a lâmpada"


def test_coordenador_separa_preferencia_do_comando_em_turno_composto() -> None:
    texto = "eu gosto de programação, encontra o código que controla a lâmpada"
    entradas_detector: list[str] = []
    turno = classificar_modalidade_turno(texto)

    def detectar(trecho: str):
        entradas_detector.append(trecho)
        if trecho == "encontra o código que controla a lâmpada":
            return {
                "intent": "FILE_SEARCH",
                "params": {
                    "query": "código que controla a lâmpada",
                    "somente_projeto": False,
                },
            }
        return None

    resultado, rota = resolver_intencao(texto, "terminal", {
        "normalizar_texto": lambda valor: str(valor or "").casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "retrato_turno_atual": turno,
        "turno_atual": turno,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": detectar,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
    })

    assert rota == "deterministico-explicito"
    assert entradas_detector == ["encontra o código que controla a lâmpada"]
    assert resultado == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "código que controla a lâmpada",
            "somente_projeto": False,
        },
    }


def test_coordenador_recebe_termo_operacional_corrigido_em_turno_composto() -> None:
    texto = "eu gosto de programacao, encontra o codgio que controla a lampada"
    entradas_detector: list[str] = []
    linguagem = LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=normalizar_texto,
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
        log=lambda *_args: None,
    )
    turno = classificar_modalidade_turno(
        texto,
        normalizar_texto=linguagem.normalizar_com_apelidos,
    )

    def detectar(trecho: str):
        entradas_detector.append(trecho)
        if trecho == "encontra o codigo que controla a lampada":
            return {
                "intent": "FILE_SEARCH",
                "params": {
                    "query": "codigo que controla a lampada",
                    "somente_projeto": False,
                },
            }
        return None

    resultado, rota = resolver_intencao(texto, "terminal", {
        "normalizar_texto": linguagem.normalizar_com_apelidos,
        "refinar_contexto_mental": lambda _texto: None,
        "retrato_turno_atual": turno,
        "turno_atual": turno,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": detectar,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
    })

    assert rota == "deterministico-explicito"
    assert entradas_detector == ["encontra o codigo que controla a lampada"]
    assert resultado == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "codigo que controla a lampada",
            "somente_projeto": False,
        },
    }


def test_coordenador_nunca_remove_negacao_ao_recortar_turno_misto() -> None:
    entradas_detector: list[str] = []

    def detectar(trecho: str):
        entradas_detector.append(trecho)
        return None

    resolver_intencao("não desliga a luz", "terminal", {
        "normalizar_texto": lambda valor: str(valor or "").casefold(),
        "refinar_contexto_mental": lambda _texto: None,
        "retrato_turno_atual": {
            "modalidade": "misto", "autoriza_execucao": False,
        },
        "turno_atual": {
            "modalidade": "misto",
            "modalidade_geral": "misto",
            "autoriza_execucao": True,
            "texto_operacional": "desliga a luz",
        },
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": detectar,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": lambda _texto: None,
    })

    assert entradas_detector == ["não desliga a luz"]


def test_prefixo_duplicado_de_comando_e_reparado_com_conservadorismo() -> None:
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=None,
        normalizar_texto=lambda texto: str(texto).casefold(),
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
    )
    assert runtime.normalizar_com_apelidos("fecfecha o bloco de notas") == "fecha o bloco de notas"
    assert runtime.normalizar_com_apelidos("fechadura nova") == "fechadura nova"


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


def test_pois_e_continua_a_ultima_fala_em_vez_de_encerrar_o_assunto() -> None:
    texto = "pois é"
    turno = classificar_modalidade_turno(texto)
    assert turno["modalidade"] == "reacao"

    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario=texto,
        ctx={},
        percepcao={},
        mente={
            "turno_atual": turno,
            "ultima_resposta": (
                "Você trocou o cajado por uma playlist pesada. "
                "Essa combinação ficou cosmicamente ilimitada."
            ),
            "ultima_afirmacao": "Essa combinação ficou cosmicamente ilimitada.",
            "continuidade_fala_ts": time.time(),
        },
    )

    assert "Continuidade social imediata" in prompt
    assert "Essa combinação ficou cosmicamente ilimitada" in prompt
    assert "não pergunte 'o que você quer que eu faça agora?'" in prompt


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
    assert resultado["status"] == "app_iniciado_focado"
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
