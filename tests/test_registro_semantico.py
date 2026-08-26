from __future__ import annotations

from mente_laylay.autonomia.coordenador_intencao import resolver_referencias_da_intencao
from mente_laylay.memoria_mental.registro_semantico import (
    atualizar_registro_turno,
    estado_registro_semantico_inicial,
    registrar_alegacao,
    registrar_entidade,
    registrar_interacao_semantica,
    renovar_registro_semantico_sessao,
    resolver_referencia_pontuada,
    resumo_registro_semantico_para_prompt,
)


def _tim_maia(registro=None, agora=100.0):
    return registrar_entidade(
        registro or estado_registro_semantico_inicial(),
        {"tipo": "artista", "nome": "Tim Maia"},
        agora=agora,
    )


def test_registro_mantem_entidade_e_pilha_de_assuntos() -> None:
    registro = atualizar_registro_turno(
        estado_registro_semantico_inicial(),
        "o que acha do Tim Maia?",
        retrato={"entidade_explicita": {"tipo": "artista", "nome": "Tim Maia"}},
        agora=100.0,
    )
    registro = atualizar_registro_turno(
        registro,
        "e o jogo Soulframe?",
        retrato={"entidade_explicita": {"tipo": "jogo", "nome": "Soulframe"}},
        agora=110.0,
    )
    assert registro["entidades"][registro["entidade_ativa_id"]]["nome"] == "Soulframe"
    assert [item["status"] for item in registro["assuntos"]] == ["pausado", "ativo"]


def test_fala_da_laylay_nao_vira_fato_sem_fonte() -> None:
    registro = registrar_alegacao(
        estado_registro_semantico_inicial(),
        "Tim Maia foi deputado federal.",
        autor="laylay",
        sujeito="Tim Maia",
        agora=100.0,
    )
    alegacao = registro["alegacoes"][-1]
    assert alegacao["status"] == "incerto"
    assert alegacao["confianca"] == 0.35
    resumo = resumo_registro_semantico_para_prompt(registro, agora=101.0)
    assert "Tim Maia foi deputado federal" not in resumo


def test_relato_do_usuario_e_guardado_com_autoria() -> None:
    registro = registrar_alegacao(
        estado_registro_semantico_inicial(),
        "sexta eu participo de um campeonato de arremessamento de peso",
        autor="usuario",
        sujeito="Pedro",
        agora=100.0,
    )
    alegacao = registro["alegacoes"][-1]
    assert alegacao["status"] == "relatado_pelo_usuario"
    assert alegacao["autor"] == "usuario"
    resumo = resumo_registro_semantico_para_prompt(registro, agora=101.0)
    assert "memória do usuário; apenas contexto pessoal" in resumo
    assert "não como prova sobre o mundo" in resumo


def test_opiniao_da_laylay_fica_rotulada_como_subjetiva() -> None:
    registro = registrar_alegacao(
        estado_registro_semantico_inicial(),
        "Na minha opinião, roxo parece aconchegante.",
        autor="laylay",
        sujeito="cor roxa",
        agora=100.0,
    )
    resumo = resumo_registro_semantico_para_prompt(registro, agora=101.0)

    assert "opinião da Laylay; não é fato" in resumo


def test_comando_e_pergunta_nao_sao_promovidos_a_alegacao() -> None:
    registro = registrar_alegacao(
        estado_registro_semantico_inicial(),
        "coloca uma música dele para mim",
        autor="usuario",
        sujeito="Tim Maia",
        agora=100.0,
    )
    registro = registrar_alegacao(
        registro,
        "Tim Maia foi político?",
        autor="usuario",
        sujeito="Tim Maia",
        agora=101.0,
    )
    assert not registro["alegacoes"]


def test_resposta_mista_guarda_declaracao_mas_nao_pergunta_final() -> None:
    registro = registrar_interacao_semantica(
        estado_registro_semantico_inicial(),
        resposta_laylay="Tim Maia foi um cantor brasileiro. Você gosta das músicas dele?",
        assunto="Tim Maia",
        agora=100.0,
    )
    assert len(registro["alegacoes"]) == 1
    assert registro["alegacoes"][0]["texto"] == "Tim Maia foi um cantor brasileiro."


def test_correcao_rebaixa_alegacao_anterior_e_fica_duravel() -> None:
    registro = registrar_alegacao(
        _tim_maia(),
        "Tim Maia teve carreira política.",
        autor="laylay",
        sujeito="Tim Maia",
        agora=101.0,
    )
    registro = atualizar_registro_turno(
        registro,
        "não Lay, isso não é verdade",
        retrato={},
        funcao="correcao",
        agora=102.0,
    )
    assert registro["alegacoes"][-1]["status"] == "corrigido"
    assert registro["correcoes"]


def test_referencia_pontuada_prefere_artista_ativo_a_playlist_e_janela() -> None:
    registro = _tim_maia(agora=100.0)
    resolucao = resolver_referencia_pontuada(
        "coloca uma música dele",
        entidades_recentes={
            "artista": {"tipo": "artista", "nome": "Tim Maia", "origem": "nome_explicito", "ts": 100.0},
            "playlist": {"tipo": "playlist", "nome": "alternativo", "origem": "reprodutor", "ts": 101.0},
            "janela": {"tipo": "janela", "nome": "PyCharm", "origem": "janela_ativa", "ts": 101.0},
        },
        registro=registro,
        operacao="musica_do_referente",
        agora=101.0,
    )
    assert resolucao["resolvida"]["nome"] == "Tim Maia"
    assert resolucao["candidatos"][0]["nome"] == "Tim Maia"
    assert resolucao["candidatos"][0]["pontuacao"] > resolucao["candidatos"][1]["pontuacao"]


def test_ttl_curto_impede_janela_antiga_de_roubar_pronome() -> None:
    resolucao = resolver_referencia_pontuada(
        "fecha ela",
        entidades_recentes={
            "janela": {"tipo": "janela", "nome": "Chrome", "origem": "janela_ativa", "ts": 1.0},
        },
        agora=100.0,
    )
    assert not resolucao["resolvida"]


def test_fronteira_de_execucao_resolve_ou_bloqueia_alvo_generico() -> None:
    resolvida = resolver_referencias_da_intencao(
        {"intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "ela"}},
        {"referencia_resolvida": {"tipo": "iot", "nome": "lâmpada do quarto"}},
    )
    assert resolvida is not None
    assert resolvida["params"]["alvo"] == "lâmpada do quarto"
    assert resolver_referencias_da_intencao(
        {"intent": "DELETE_ITEM", "params": {"alvo": "isso"}},
        {},
    ) is None


def test_nova_sessao_encerra_assunto_e_descarta_alegacao_incerta_da_laylay() -> None:
    registro = atualizar_registro_turno(
        estado_registro_semantico_inicial(),
        "Tim Maia",
        retrato={"entidade_explicita": {"tipo": "artista", "nome": "Tim Maia"}},
        agora=100.0,
    )
    registro = registrar_alegacao(
        registro, "Tim Maia foi político.", autor="laylay", sujeito="Tim Maia", agora=101.0,
    )
    renovado = renovar_registro_semantico_sessao(registro, agora=200.0)
    assert renovado["entidade_ativa_id"] == ""
    assert renovado["assunto_ativo_id"] == ""
    assert renovado["assuntos"][-1]["status"] == "encerrado"
    assert not renovado["alegacoes"]
