from __future__ import annotations

import time

from mente_laylay.autonomia.processamento_resposta_ia import limpar_resposta_da_ia
from mente_laylay.autonomia.sugestoes_sistema import processar_confirmacao_sugestao
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.continuidade_semantica import resolver_continuidade_semantica
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial


def test_playlist_spotify_nao_e_oferecida_sem_executor() -> None:
    resultado = validar_alegacoes_da_fala(
        "Vou criar uma playlist com essas duas no Spotify. Quer eu fazer isso?",
        plano={"comandos": []},
        origem="resposta_ia",
    )

    assert "oferta_capacidade_nao_suportada" in resultado["problemas"]
    assert "não consigo criar uma playlist dentro do Spotify" in resultado["fala"]


def test_execucao_falsa_da_playlist_e_substituida_por_estado_real() -> None:
    resultado = verificar_fala_turno(
        'Ótimo! Vou fazer a playlist então. Pronto, já tá pronta! Vou tocar agora "Before I Forget".',
        plano={"texto_usuario": "quero sim", "comandos": [], "dominio": "musica"},
        origem="ia_final",
    )

    assert "execucao_alegada_sem_resultado" in resultado["problemas"]
    assert resultado["fala"] == "Eu me adiantei na fala, mas essa ação não foi executada nem confirmada."


def test_comentario_sobre_musica_nao_autoriza_reproducao_automatica() -> None:
    resultado = verificar_fala_turno(
        "Ótima escolha! Vou tocar pra você agora! (tocando Duality do Slipknot)",
        plano={
            "texto_usuario": "eu gosto bastante da música Duality deles",
            "comandos": [],
            "dominio": "musica",
        },
        origem="ia_final",
    )

    assert "execucao_alegada_sem_resultado" in resultado["problemas"]
    assert "tocando Duality" not in resultado["fala"]
    assert resultado["fala"] == "Eu me adiantei na fala, mas essa ação não foi executada nem confirmada."


def test_confirmacao_real_de_musica_permite_informar_reproducao() -> None:
    fala = "Vou tocar pra você agora: Duality."
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"comandos": [{
            "intent": "MUSIC_SEARCH", "executou": True,
            "confirmado": True, "status": "musica_aberta",
        }]},
        origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_pseudocomando_e_marcador_do_modelo_nao_chegam_a_fala() -> None:
    fala, comandos = limpar_resposta_da_ia(
        'Espero que goste! [.abre a playlist "Before I Forget" no Spotify] Pronto! 🤙LYL'
    )

    assert comandos == []
    assert "[.abre" not in fala
    assert "abre a playlist" not in fala
    assert "LYL" not in fala


def test_titulo_musical_inventado_e_bloqueado_sem_evidencia() -> None:
    resultado = verificar_fala_turno(
        'Aí vai uma que eu adoro: "Mythological". É bem enérgica!',
        plano={
            "texto_usuario": "que outra música do Slipknot você gosta?",
            "comandos": [],
            "dominio": "musica",
        },
        origem="ia_final",
    )

    assert "Mythological" not in resultado["fala"]
    assert "obra_sem_evidencia" in resultado["problemas"]


def test_coloca_essa_busca_ultima_musica_mencionada_em_vez_de_replay() -> None:
    mente = estado_mental_inicial()
    mente.update({
        "ultima_acao_intent": "MUSIC_SEARCH",
        "ultima_acao_params": {"query": "slipknot"},
        "ultima_habilidade": "musica",
        "ultima_musica_mencionada": {
            "titulo": "Duality", "origem": "fala_verificada", "ts": time.time(),
        },
    })

    decisao = resolver_continuidade_semantica("coloca para mim essa", mente=mente)

    assert decisao.intent == "MUSIC_SEARCH"
    assert decisao.params["query"] == "Duality"


def test_qual_erro_recupera_detalhe_da_sugestao_pendente() -> None:
    estado = {
        "comando_sugerido": "EXPLAIN_ERROR",
        "comando_sugerido_payload": {"linha": "Uncaught TypeError na página"},
        "comando_sugerido_estado": "PENDING_CONFIRM",
        "comando_sugerido_ts": time.time(),
    }
    falas: list[str] = []

    tratado = processar_confirmacao_sugestao({
        "continuidades_get": lambda chave, padrao=None: estado.get(chave, padrao),
        "falar": lambda fala, *_args: falas.append(fala),
    }, "qual erro?")

    assert tratado is True
    assert "Uncaught TypeError" in falas[-1]
