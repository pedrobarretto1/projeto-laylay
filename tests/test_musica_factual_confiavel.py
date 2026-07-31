import time

from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_resposta_pendencia_prioritaria,
)
from mente_laylay.cognicao.fundamentacao_factual import (
    extrair_tema_fundamentacao,
    validar_fala_com_fundamentacao,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.contexto_compartilhado import (
    classificar_pergunta_com_proposito,
    registrar_oferta_pendente,
)
from mente_laylay.memoria_mental.musica_conversacional_runtime import (
    MusicaConversacionalRuntime,
)


def _norm(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _runtime_musical(resultados=None):
    falas = []
    registros = []
    execucoes = []
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: {},
        normalizar_texto=_norm,
        falar=lambda fala, *_: falas.append(fala),
        registrar_mente_curta=lambda *args, **kwargs: registros.append((args, kwargs)),
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *args, **kwargs: None,
        buscar_resultados_musicais=lambda query, limite: list(resultados or []),
    )
    return runtime, falas, registros, execucoes


def test_pergunta_ja_ouviu_extrai_artista_para_fundamentacao() -> None:
    assert extrair_tema_fundamentacao("você já ouviu MF DOOM?") == "MF DOOM"
    assert extrair_tema_fundamentacao("você já ouviu falar do MF DOOM?") == "MF DOOM"


def test_fundamentacao_bloqueia_experiencia_musical_pessoal_inventada() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Eu ouvi umas músicas dele e acompanho o trabalho.",
        fundamentacao={"tema": "MF DOOM", "confiavel": False},
        texto_usuario="você já ouviu MF DOOM?",
    )
    assert "familiaridade_inventada" in resultado["problemas"]
    assert "ouvi umas músicas" not in resultado["fala"]


def test_personalidade_pode_expressar_gosto_sem_inventar_uma_lembranca() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Gosto do jeito enigmático que essa descrição apresenta.",
        fundamentacao={
            "tema": "MF DOOM",
            "titulo": "MF DOOM",
            "resumo": "A descrição disponível apresenta MF DOOM de maneira enigmática.",
            "confiavel": True,
        },
        texto_usuario="você gosta de MF DOOM?",
    )
    assert resultado["acao"] == "aceita"
    assert resultado["fala"].startswith("Gosto")


def test_titulos_musicais_sem_evidencia_nao_chegam_a_fala() -> None:
    resultado = verificar_fala_turno(
        'Então aqui vai: "The City" e "Mystery of Love" são clássicos dele.',
        plano={"texto_usuario": "quero sim", "dominio": "musica"},
    )
    assert "obra_sem_evidencia" in resultado["problemas"]
    assert "The City" not in resultado["fala"]
    assert "Mystery of Love" not in resultado["fala"]


def test_oferta_de_recomendar_faixas_vira_pendencia_musical_com_contexto() -> None:
    fala = "Posso sugerir algumas faixas ou discos que você talvez não tenha ouvido. Quer?"
    classificacao = classificar_pergunta_com_proposito(fala)
    assert classificacao["proposito"] == "recomendacao_musical"
    mente = registrar_oferta_pendente({}, fala, alvo_contexto="MF DOOM")
    assert mente["oferta_pendente"]["modo"] == "recomendar_artista"
    assert mente["oferta_pendente"]["contexto"] == "MF DOOM"


def test_quero_sim_resolve_oferta_com_recomendacao_verificada() -> None:
    chamadas = []
    ctx = {
        "mente_integrada_estado": {
            "oferta_pendente": {
                "modo": "recomendar_artista",
                "contexto": "MF DOOM",
                "ts": time.time(),
            },
            "turno_atual": {"modalidade": "confirmacao"},
        },
        "_recomendar_musica_verificada": lambda artista, texto: chamadas.append((artista, texto)) or True,
    }
    tratado, etapa = processar_resposta_pendencia_prioritaria(ctx, "quero sim")
    assert tratado is True
    assert etapa == "recomendacao_musical_verificada"
    assert chamadas == [("MF DOOM", "quero sim")]


def test_recomendacao_observada_distingue_sugerir_de_tocar() -> None:
    runtime, falas, _registros, execucoes = _runtime_musical([{
        "title": "MF DOOM - Doomsday (Official Audio)",
        "channel": "MF DOOM",
        "url": "https://www.youtube.com/watch?v=12345678901",
    }])
    assert runtime.recomendar_artista_verificado("MF DOOM", "quero sim") is True
    assert "faixa real" in falas[-1]
    assert "ainda não toquei" in falas[-1]
    assert execucoes == []


def test_cobranca_de_musica_nao_inventa_execucao() -> None:
    runtime, falas, _registros, execucoes = _runtime_musical([])
    runtime._sugestao_pendente = {"titulo": "MF DOOM Doomsday", "ts": time.time()}
    assert runtime.processar_confirmacao("cadê a música?") is True
    assert "ainda não toquei" in falas[-1]
    assert execucoes == []


def test_expectativa_passada_nao_autoriza_comando() -> None:
    turno = classificar_modalidade_turno("achei que você ia colocar alguma música")
    assert turno["modalidade"] == "reacao"
    assert turno["autoriza_execucao"] is False
