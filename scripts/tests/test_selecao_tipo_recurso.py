"""Tipo explícito vence candidato genérico sem autorizar efeitos por si só."""
from functools import partial

import pytest

from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.playlist_mental import limpar_nome_playlist


CASOS = [
    ("coloca a playlist Som do Silencio", "PLAYLIST_PLAY", {"nome_playlist": "som do silencio"}, "VOLUME", {"acao": "mute"}),
    ("coloca um video do jazzghost", "SEARCH", {"query": "jazzghost", "engine": "youtube"}, "MUSIC_SEARCH", {"query": "video do jazzghost"}),
    ("coloca a musica Volume em 40", "MUSIC_SEARCH", {"query": "volume em 40"}, "VOLUME", {"acao": "set", "nivel_volume": 40}),
    ("abre o aplicativo Arquivo Vivo", "APP_OPEN", {"nome_app": "arquivo vivo"}, "MUSIC_SEARCH", {"query": "arquivo vivo"}),
    ("abre o site Musica de Ontem", "OPEN_URL", {"alvo": "musica de ontem"}, "MUSIC_SEARCH", {"query": "musica de ontem"}),
    ("abre o arquivo musica.txt", "FILE_SEARCH", {"query": "musica.txt"}, "APP_OPEN", {"nome_app": "musica.txt"}),
    ("cria a pasta Jazz", "CREATE_FOLDER", {"nome": "Jazz"}, "MUSIC_SEARCH", {"query": "jazz"}),
    ("liga a lampada do quarto", "IOT_CONTROL", {"acao": "ligar", "alvo": "lampada_quarto"}, "MUSIC_SEARCH", {"query": "lampada do quarto"}),
]


@pytest.mark.parametrize("texto,intent,params,intent_errado,params_errados", CASOS)
def test_arbitro_rejeita_candidato_incompativel_mesmo_com_maior_confianca(texto, intent, params, intent_errado, params_errados):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True  # RED precisa alcançar a disputa.
    certo = {"intent": intent, "params": params}
    errado = {"intent": intent_errado, "params": params_errados}
    r = arbitrar_turno(texto, [
        CandidatoDecisao("comando_explicito", errado, "generico", .99),
        CandidatoDecisao("comando_explicito", certo, "especifico", .8),
    ], turno=turno)
    assert r["decisao"] == certo, r
    assert any(c["origem"] == "generico" for c in r["rejeitados"])


@pytest.mark.parametrize("texto,nome", [
    ("coloca a playlist Som do Silencio", "som do silencio"),
    ("coloca a playlist Volume em 40", "volume em 40"),
    ("coloca a playlist Mais Alto", "mais alto"),
])
def test_detector_cede_palavra_interna_ao_owner_do_tipo_nomeado(texto, nome):
    ctx = {"normalizar_texto": normalizar_texto, "limpar_nome_playlist": limpar_nome_playlist,
        "extrair_intencao_abrir_app": partial(extrair_intencao_abrir_app,
            normalizar_texto=normalizar_texto, limpar_destino=lambda t: t,
            apps_map={}, sites_diretos={})}
    assert detectar_intencao_deterministica_mente(texto, ctx) == {
        "intent": "PLAYLIST_PLAY", "params": {"nome_playlist": nome}}


@pytest.mark.parametrize("texto", [
    'coloca a musica "Video Killed the Radio Star"', 'coloca a playlist "Som do Silencio"',
    "abre o aplicativo Arquivo Vivo", "abre o site Musica de Ontem",
])
def test_pergunta_e_negacao_nao_ganham_autoridade_por_ter_tipo(texto):
    for negado in ("não " + texto, "como eu faria para " + texto + "?"):
        turno = classificar_modalidade_turno(negado)
        assert turno["autoriza_execucao"] is False
        r = arbitrar_turno(negado, [CandidatoDecisao("comando_explicito",
            {"intent": "MUSIC_SEARCH", "params": {"query": "inventada"}}, "adversarial", 1)], turno=turno)
        assert not r["decisao"]


@pytest.mark.parametrize("texto", ['abre "Arquivo Vivo"', 'toca "Video Killed the Radio Star"'])
def test_nome_literal_sem_tipo_externo_nao_e_reclassificado_pela_palavra_interna(texto):
    certo = {"intent": "APP_OPEN" if texto.startswith("abre") else "MUSIC_SEARCH", "params": {}}
    r = arbitrar_turno(texto, [CandidatoDecisao("comando_explicito", certo, "teste", .9)],
        turno=classificar_modalidade_turno(texto))
    assert r["decisao"] == certo


def test_fallback_ai_nao_reintroduz_domino_incompativel_rejeitado():
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    texto = "coloca um video do jazzghost"
    arbitragens = []
    r, rota = resolver_intencao(texto, "teste", {
        "normalizar_texto": normalizar_texto, "turno_atual": classificar_modalidade_turno(texto),
        "detectar_intencao_deterministica": lambda *_: None,
        "registrar_arbitragem_turno": lambda _texto, r: arbitragens.append(r),
        "tentar_intencao_ai_primeiro": lambda *_: {"intent": "MUSIC_SEARCH", "params": {"query": "jazzghost"}},
    })
    assert r is None and rota == ""
    assert any("tipo explícito" in c["motivo"] for a in arbitragens for c in a["rejeitados"])


def test_candidato_vazio_nao_consumira_pedido_para_outro_owner():
    r = detectar_intencao_deterministica_mente("coloca a musica duality", {
        "normalizar_texto": normalizar_texto,
        "resolver_consulta_recurso_local": lambda *_: {},
        "detectar_intencao_iot": lambda *_: {},
        "detectar_sugestao_indireta": lambda *_: {},
    })
    assert r == {"intent": "MUSIC_SEARCH", "params": {"query": "duality"}}


def test_copia_normalizada_conserva_literal_da_mesma_fala_na_arbitragem():
    texto = 'abre "Arquivo Vivo"'
    certo = {"intent": "APP_OPEN", "params": {"nome_app": "Arquivo Vivo"}}
    r = arbitrar_turno(normalizar_texto(texto), [CandidatoDecisao("comando_explicito", certo, "teste", .9)],
        turno=classificar_modalidade_turno(texto))
    assert r["decisao"] == certo and r["tipo_recurso_pedido"] == ""


def test_fala_alheia_nao_fornece_literalidade_ao_candidato_atual():
    texto = "abre o arquivo musica.txt"
    r = arbitrar_turno(texto, [CandidatoDecisao("comando_explicito",
        {"intent": "APP_OPEN", "params": {"nome_app": "musica.txt"}}, "errado", .99)],
        turno=classificar_modalidade_turno('abre "Arquivo Vivo"'))
    assert r["decisao"] is None and r["tipo_recurso_pedido"] == "arquivo"


@pytest.mark.parametrize("texto,tipo", [
    ("pode colocar a playlist Jazz", "playlist"),
    ("preciso que você abra o site github", "site"),
    ("pode abrir o arquivo musica.txt", "arquivo"),
    ('abre "Arquivo Vivo"', ""),
    ("toca a musica Video Killed the Radio Star", "musica"),
    ("abre a calculadora e pausa a música", ""),
])
def test_leitura_nominal_compartilhada_nao_e_um_parser_de_nomes_ou_de_turnos_mistos(texto, tipo):
    from mente_laylay.cognicao.gramatica_operacional import tipo_recurso_pedido_direto
    assert tipo_recurso_pedido_direto(texto) == tipo


@pytest.mark.parametrize("texto,intent", [
    ("abre o app chamado Arquivo Vivo", "APP_OPEN"),
    ("abre o site Arquivo Vivo", "OPEN_URL"),
    ("coloca a musica Arquivo de Texto", "MUSIC_SEARCH"),
    ("abre o arquivo playlist jazz.txt", "FILE_SEARCH"),
    ("abre o site Lampada do Quarto", "OPEN_URL"),
    ("abre o app chamado Playlist Viva", "APP_OPEN"),
])
def test_retrato_nao_projeta_restricao_a_partir_da_palavra_interna_do_nome(texto, intent):
    from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    assert not retrato["intents_permitidos"] or intent in retrato["intents_permitidos"], retrato
    certo = {"intent": intent, "params": {}}
    r = arbitrar_turno(texto, [CandidatoDecisao("comando_explicito", certo, "owner", .9)],
        turno=turno, retrato=retrato)
    assert r["decisao"] == certo


@pytest.mark.parametrize("texto,intents", [
    ("coloca a playlist Som do Silencio e abre a calculadora", ["PLAYLIST_PLAY", "APP_OPEN"]),
    ("abre o site Musica de Ontem; quando eu confirmar, coloca a playlist Som do Silencio", ["OPEN_URL"]),
    ("abre o app chamado Arquivo Vivo; não liga a lampada do quarto", ["APP_OPEN"]),
])
def test_selecao_por_tipo_em_atos_nao_mistura_autorizacao_do_conjunto(texto, intents):
    # Componentes reais, sem executor: não equivale à entrega do composto.
    from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
    ctx = {"normalizar_texto": normalizar_texto, "limpar_nome_playlist": limpar_nome_playlist,
        "extrair_intencao_abrir_app": partial(extrair_intencao_abrir_app,
            normalizar_texto=normalizar_texto, limpar_destino=lambda t: t,
            apps_map={}, sites_diretos={})}
    aceitos = []
    segmentos = classificar_modalidade_turno(texto)["segmentos"]
    assert any(ato["autoriza_execucao"] for ato in segmentos), "primeira fronteira: comando independente perdido na classificação"
    for ato in segmentos:
        if not ato["autoriza_execucao"]:
            continue
        fonte = ato["texto"]
        candidato = detectar_intencao_deterministica_mente(fonte, ctx)
        assert candidato is not None
        turno = classificar_modalidade_turno(fonte)
        retrato, _ = construir_retrato_turno(fonte, turno=turno, mente={}, contexto_perceptivo={})
        r = arbitrar_turno(fonte, [CandidatoDecisao("comando_explicito", candidato, "detector", .9)],
            turno=turno, retrato=retrato)
        assert r["decisao"]
        aceitos.append(r["decisao"]["intent"])
    assert aceitos == intents
