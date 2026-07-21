from __future__ import annotations

from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt


def test_retrato_resolve_esse_jogo_mesmo_com_terminal_em_foco() -> None:
    retrato, recentes = construir_retrato_turno(
        "esse jogo é muito legal",
        turno={"id": 10, "modalidade": "reacao"},
        mente={},
        contexto_perceptivo={"exe": "cmd.exe", "title": "Prompt de Comando"},
        jogo_contexto={"ativo": True, "processo": "Soulframe.x64.exe", "titulo": "Soulframe"},
        agora=100.0,
    )

    assert retrato["referencia_tipo"] == "jogo"
    assert retrato["referencia_resolvida"]["nome"] == "Soulframe"
    assert recentes["jogo"]["nome"] == "Soulframe"


def test_retrato_congela_a_necessidade_de_atualidade_do_turno() -> None:
    retrato, _ = construir_retrato_turno(
        "quando vai sair o GTA 6?",
        turno={"id": 9, "modalidade": "pergunta"},
        mente={},
        contexto_perceptivo={},
        agora=100.0,
    )

    assert retrato["atualidade_factual"]["depende_atualidade"] is True
    assert retrato["atualidade_factual"]["classe"] == "agenda_ou_disponibilidade"


def test_retrato_preserva_seu_jorge_como_nome_inteiro() -> None:
    retrato, recentes = construir_retrato_turno(
        "você gosta do seu jorge?",
        turno={"id": 20, "modalidade": "pergunta"},
        mente={},
        contexto_perceptivo={"exe": "pycharm64.exe", "title": "laylay.py"},
        agora=100.0,
    )

    assert retrato["entidade_explicita"]["nome"] == "Seu Jorge"
    assert retrato["referencia_resolvida"]["nome"] == "Seu Jorge"
    assert recentes["referencia_nomeada"]["nome"] == "Seu Jorge"


def test_correcao_promove_artista_e_pronome_dele_nao_aponta_para_janela() -> None:
    correcao, recentes = construir_retrato_turno(
        "não lay, tô falando do artista seu jorge",
        turno={"id": 21, "modalidade": "correcao"},
        mente={},
        contexto_perceptivo={"exe": "pycharm64.exe", "title": "laylay.py"},
        agora=100.0,
    )
    assert correcao["entidade_explicita"] == {
        "tipo": "artista", "nome": "Seu Jorge", "origem": "nome_explicito",
    }

    seguinte, _ = construir_retrato_turno(
        "você gosta dele?",
        turno={"id": 22, "modalidade": "pergunta"},
        mente={"entidades_recentes": recentes},
        contexto_perceptivo={"exe": "pycharm64.exe", "title": "laylay.py"},
        playlist_state={"name": "alternativo", "index": 1},
        agora=101.0,
    )
    assert seguinte["referencia_tipo"] == "artista"
    assert seguinte["referencia_resolvida"]["nome"] == "Seu Jorge"


def test_pedido_de_musica_do_artista_limita_a_busca() -> None:
    retrato, _ = construir_retrato_turno(
        "coloca uma música dele para mim",
        turno={"id": 23, "modalidade": "comando"},
        mente={"entidades_recentes": {
            "artista": {
                "tipo": "artista", "nome": "Seu Jorge", "origem": "nome_explicito", "ts": 99.0,
            }
        }},
        contexto_perceptivo={},
        agora=100.0,
    )
    assert retrato["referencia_resolvida"]["nome"] == "Seu Jorge"
    assert retrato["operacao_explicita"] == "musica_do_referente"
    assert retrato["intents_permitidos"] == ["MUSIC_SEARCH"]


def test_pergunta_de_opiniao_registra_tim_maia_como_entidade() -> None:
    retrato, recentes = construir_retrato_turno(
        "o que você acha do tim maia?",
        turno={"id": 24, "modalidade": "pergunta"},
        mente={},
        contexto_perceptivo={},
        agora=100.0,
    )
    assert retrato["entidade_explicita"]["nome"] == "Tim Maia"
    assert retrato["referencia_resolvida"]["nome"] == "Tim Maia"
    assert recentes["referencia_nomeada"]["nome"] == "Tim Maia"


def test_operacao_playlist_limita_intents_herdados() -> None:
    retrato, _ = construir_retrato_turno(
        "coloca essa música na playlist anime",
        turno={"id": 11, "modalidade": "comando"},
        mente={"entidades_recentes": {"musica": {
            "tipo": "musica", "nome": "O Sol e a Lua", "origem": "player", "ts": 99.0,
        }}},
        contexto_perceptivo={},
        agora=100.0,
    )

    assert retrato["operacao_explicita"] == "playlist_adicionar"
    assert retrato["intents_permitidos"] == ["PLAYLIST_ADD"]

    resultado = arbitrar_turno(
        retrato["texto"],
        [
            CandidatoDecisao(
                "comando_contextual",
                {"intent": "MEDIA_CONTROL", "params": {"acao": "replay"}},
                "contexto-geral",
                0.80,
            ),
            CandidatoDecisao(
                "comando_explicito",
                {"intent": "PLAYLIST_ADD", "params": {"nome_playlist": "anime"}},
                "deterministico",
                0.98,
            ),
        ],
        turno={"modalidade": "comando"},
        retrato=retrato,
    )

    assert resultado["decisao"]["intent"] == "PLAYLIST_ADD"
    assert any("playlist_adicionar" in item["motivo"] for item in resultado["rejeitados"])


def test_comentario_sobre_jogo_nao_herda_comando_de_musica() -> None:
    retrato, _ = construir_retrato_turno(
        "esse jogo é muito legal",
        turno={"id": 12, "modalidade": "reacao"},
        mente={},
        contexto_perceptivo={},
        jogo_contexto={"ativo": True, "processo": "Soulframe.x64.exe", "titulo": "Soulframe"},
        agora=100.0,
    )
    resultado = arbitrar_turno(
        retrato["texto"],
        [CandidatoDecisao(
            "comando_contextual",
            {"intent": "MEDIA_CONTROL", "params": {"acao": "replay"}},
            "contexto-midia",
            0.82,
        )],
        turno={"modalidade": "reacao"},
        retrato=retrato,
    )

    assert resultado["decisao"] is None
    assert "sem verbo operacional" in resultado["rejeitados"][0]["motivo"]


def test_modelo_recebe_retrato_congelado_em_vez_de_inventar_referencia() -> None:
    retrato, _ = construir_retrato_turno(
        "esse jogo é muito legal",
        turno={"id": 13, "modalidade": "reacao"},
        mente={},
        contexto_perceptivo={"exe": "cmd.exe", "title": "Prompt de Comando"},
        jogo_contexto={"ativo": True, "processo": "Soulframe.x64.exe", "titulo": "Soulframe"},
        agora=100.0,
    )
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario="esse jogo é muito legal",
        ctx={"exe": "cmd.exe", "title": "Prompt de Comando"},
        percepcao={},
        mente={
            "turno_atual": {"id": 13, "modalidade": "reacao"},
            "retrato_turno_atual": retrato,
        },
    )

    assert "RETRATO CONGELADO DESTE TURNO" in prompt
    assert "jogo=Soulframe" in prompt
    assert "referência=jogo:Soulframe" in prompt
