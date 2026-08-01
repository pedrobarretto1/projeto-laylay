from __future__ import annotations

import json

from mente_laylay.autonomia.processamento_resposta_ia import (
    preparar_resposta_para_execucao,
)
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
)
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno


class _MemoriaSemAprendizado:
    def salvar_aprendizados_semanticos(self, _itens):
        raise AssertionError("rascunho conversacional não deveria criar aprendizado")


def _plano_musical(nome: str = "Nirvana") -> dict:
    return {
        "texto_usuario": f"você gosta de {nome}?",
        "dominio": "musica",
        "referencia_resolvida": {
            "tipo": "artista",
            "nome": nome,
            "origem": "nome_curto_contextual",
        },
        "comandos": [],
    }


def test_resposta_so_com_claro_nao_cumpre_pedido_de_descricao() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "pode me mandar uma descrição das skins?",
        "Claro!",
    )
    assert avaliacao["aceita"] is False
    assert "resposta_incompleta" in avaliacao["problemas"]
    assert "entrega_prometida_ausente" in avaliacao["problemas"]


def test_fragmento_ah_mas_e_bloqueado_antes_da_voz() -> None:
    resultado = verificar_fala_turno(
        "Ah... Mas.",
        plano={
            "texto_usuario": "mas tem alguma música que você gosta bastante?",
            "dominio": "musica",
            "comandos": [],
        },
    )
    assert resultado["aceita"] is False
    assert resultado["acao"] == "reparar"
    assert "resposta_incompleta" in resultado["problemas"]


def test_nirvana_musical_nao_pode_derivar_para_conceito_filosofico() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "você gosta de Nirvana?",
        "Nirvana é um estado de paz e libertação do sofrimento.",
        plano=_plano_musical(),
    )
    assert avaliacao["aceita"] is False
    assert "pergunta_direta_nao_respondida" in avaliacao["problemas"]
    assert "deriva_de_dominio" in avaliacao["problemas"]


def test_opiniao_musical_natural_e_fundamentada_pelo_foco_e_aceita() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "você gosta de Nirvana?",
        "Gosto da mistura de peso e vulnerabilidade da banda.",
        plano=_plano_musical(),
    )
    assert avaliacao["aceita"] is True


def test_relato_de_limpeza_nao_recebe_receita_especifica_inventada() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "eu tô pensando em lavar o banheiro hoje",
        "Use sal com sabão daquela marca e jogue tudo no piso.",
    )
    assert avaliacao["aceita"] is False
    assert "conselho_especifico_nao_solicitado" in avaliacao["problemas"]


def test_nome_curto_recupera_tipo_da_entidade_musical_recente() -> None:
    retrato, _entidades = construir_retrato_turno(
        "você gosta de nirvana?",
        turno={"modalidade": "pergunta", "id": 7},
        mente={
            "entidades_recentes": {
                "musica": {
                    "tipo": "artista",
                    "nome": "Nirvana",
                    "origem": "reproducao_confirmada",
                    "ts": 100.0,
                },
            },
        },
        contexto_perceptivo={},
        playlist_state={},
        jogo_contexto={},
        agora=110.0,
    )
    assert retrato["entidade_explicita"]["nome"] == "Nirvana"
    assert retrato["referencia_resolvida"]["tipo"] == "artista"

    plano = planejar_turno(
        "você gosta de nirvana?",
        turno={
            "modalidade": "pergunta",
            "ato_principal": "pergunta",
            "referencia_resolvida": retrato["referencia_resolvida"],
        },
    )
    assert plano["dominio"] == "musica"


def test_reparo_semantico_usa_uma_chamada_e_descarta_o_rascunho() -> None:
    chamadas = []

    def reparar(mensagens, **_kwargs):
        chamadas.append(mensagens)
        return json.dumps({
            "fala": (
                "A medieval poderia ter capa curta e detalhes de metal; a cyberpunk, "
                "néon e visor translúcido; e a nebulosa, cores profundas com pontos de luz."
            ),
            "comandos": [],
        }, ensure_ascii=False)

    resposta = preparar_resposta_para_execucao(
        "pode me mandar uma descrição das skins?",
        '{"fala":"Claro!","comandos":[]}',
        enviar_mensagem_cb=reparar,
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=_MemoriaSemAprendizado(),
        contexto_comunicacao={
            "plano_turno": {"dominio": "conversa", "comandos": []},
            "mensagens": [
                {"role": "user", "content": "pensei em skins medieval e cyberpunk"},
                {"role": "assistant", "content": "As duas podem ficar bem diferentes."},
            ],
        },
        log=lambda *_args: None,
    )
    assert len(chamadas) == 1
    assert "medieval" in resposta["fala"].casefold()
    assert resposta["fala"] != "Claro!"
    assert resposta["comandos"] == []
    assert resposta["autocorrigida"] is True


def test_falha_do_reparo_semantico_usa_contingencia_contextual() -> None:
    resposta = preparar_resposta_para_execucao(
        "você gosta de Nirvana?",
        '{"fala":"Nirvana é um estado de paz espiritual.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=_MemoriaSemAprendizado(),
        contexto_comunicacao={"plano_turno": _plano_musical()},
        log=lambda *_args: None,
    )
    assert "Nirvana" in resposta["fala"]
    assert "estado de paz" not in resposta["fala"]
    assert resposta["comandos"] == []
