"""Ato social anterior não substitui a resposta ao relato conversacional atual.

O modelo é apenas proponente. Estes testes exercitam os owners reais da leitura,
do contrato e da aceitação; não chamam modelo, voz, pesquisa ou executor.
"""

from __future__ import annotations

from typing import Any

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa


RELATO_LITERAL = (
    "meu dia ta ate que bom, estou importante o ultrakill para jogar no navegador "
    "e esta ficando muito bom"
)
FALA_PUBLICADA = (
    "Oi, tudo bem comigo! Adoro ver que você está se divertindo com o Ultrakill "
    "no navegador — é um jogo incrível, mesmo assim não jogamos juntos, mas é "
    "sempre bom ver que alguém está se conectando com algo que realmente faz sentido."
)
RESPOSTA_ANTERIOR = (
    "Meu dia tá tranquilo, sem muito movimento, só conversando com você. "
    "Deixa eu saber como tá o seu, se quiser contar."
)


def _plano_atual(texto: str) -> dict[str, Any]:
    historico = [
        {"role": "user", "content": "oi lay, tudo bem com voce?"},
        {"role": "assistant", "content": "Oi! Tudo bem comigo."},
        {"role": "user", "content": "como ta o seu dia?"},
        {"role": "assistant", "content": RESPOSTA_ANTERIOR},
    ]
    mente = {"messages": historico, "ultima_resposta": RESPOSTA_ANTERIOR}
    turno = classificar_modalidade_turno(texto)
    funcao = analisar_funcao_comunicativa(texto)
    turno["funcao_comunicativa"] = funcao
    plano = planejar_turno(texto, turno=turno, mente=mente)
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto,
        turno=turno,
        plano=plano,
        funcao_comunicativa=funcao,
        mente=mente,
        falas_recentes=[historico[1]["content"], RESPOSTA_ANTERIOR],
    )
    return plano


@pytest.mark.parametrize(
    "texto,fala",
    [
        pytest.param(RELATO_LITERAL, FALA_PUBLICADA, id="relato-literal-publicado"),
        pytest.param(
            "Estou adaptando um jogo para rodar no navegador e está ficando bom.",
            "Oi, tudo bem comigo! O jogo no navegador está ficando bom.",
            id="outro-jogo-mesmo-contrato",
        ),
        pytest.param(
            "Hoje terminei de organizar minhas notas no navegador.",
            "Olá! Você terminou de organizar suas notas no navegador.",
            id="notas-saudacao-antiga",
        ),
        pytest.param(
            "Estou preparando a apresentação e já terminei os slides.",
            "Estou bem, obrigada por perguntar. Você terminou os slides da apresentação.",
            id="bem-estar-sem-pergunta-atual",
        ),
    ],
)
def test_relato_nao_admite_reinicio_social_mesmo_com_ancora_tematica(
    texto: str, fala: str,
) -> None:
    plano = _plano_atual(texto)
    contrato = plano["contrato_fala"]
    assert contrato["atos"] == ["conversa"]
    assert contrato["roteiro_concreto"]["estrategia"] == "resposta_direta"
    assert contrato["autoriza_execucao"] is False

    resultado = validar_aderencia_contrato_fala(
        texto, fala, contrato_fala=contrato, turno_id=plano["id"],
        ultima_resposta=RESPOSTA_ANTERIOR,
    )
    assert resultado["aceita"] is False, (
        "A aceitação confundiu âncora temática com resposta ao ato atual: "
        f"{resultado}"
    )
    assert resultado["requer_reparo"] is True


def test_juiz_compartilhado_nao_publica_reinicio_social_do_relato_literal() -> None:
    plano = _plano_atual(RELATO_LITERAL)
    resultado = verificar_fala_turno(
        FALA_PUBLICADA, plano=plano, ultima_resposta=RESPOSTA_ANTERIOR,
    )
    assert resultado["aceita"] is False, (
        "O juiz final publicou a resposta à saudação antiga no lugar do ato atual: "
        f"{resultado}"
    )


def test_reparo_de_reinicio_social_preserva_fonte_atual_sem_reoferecer_a_saudacao_antiga():
    import json
    from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_reparo_comunicacao
    plano = _plano_atual(RELATO_LITERAL)
    avaliacao = verificar_fala_turno(FALA_PUBLICADA, plano=plano)
    assert 'reinicio_social_sem_ato_atual' in avaliacao['problemas']
    pacote = montar_mensagens_reparo_comunicacao(RELATO_LITERAL, FALA_PUBLICADA, avaliacao,
        mensagens=[{'role': 'user', 'content': 'oi lay, tudo bem com voce?'},
                   {'role': 'assistant', 'content': 'Oi, tudo bem comigo!'},
                   {'role': 'user', 'content': RELATO_LITERAL}])
    dados = json.loads(pacote[-1]['content'])
    assert not any(m['role'] == 'assistant' for m in dados.get('troca_recente', ()))
    assert 'rascunho_rejeitado' not in dados
    assert RELATO_LITERAL in str(dados)


def test_reparo_de_perspectiva_do_relato_tambem_preserva_ato_atual():
    import json
    from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_reparo_comunicacao
    plano = _plano_atual(RELATO_LITERAL)
    avaliacao = verificar_fala_turno('Meu dia tá calmo e estou fazendo o Ultrakill no navegador.', plano=plano)
    assert 'perspectiva_enunciador_invertida' in avaliacao['problemas']
    assert avaliacao['contrato_reparo'].get('relato_atual', {}).get('texto') == RELATO_LITERAL
    pacote = montar_mensagens_reparo_comunicacao(RELATO_LITERAL, 'Meu dia tá calmo.', avaliacao,
        mensagens=[{'role': 'user', 'content': 'como ta o seu dia?'},
                   {'role': 'assistant', 'content': 'Meu dia tá calmo.'},
                   {'role': 'user', 'content': RELATO_LITERAL}])
    dados = json.loads(pacote[-1]['content'])
    assert dados['mensagem_atual'] == RELATO_LITERAL
    assert 'como ta o seu dia?' not in str(dados)
    assert 'rascunho_rejeitado' not in dados


@pytest.mark.parametrize(
    "texto,fala",
    [
        pytest.param(
            "oi lay, tudo bem com voce?", "Oi! Tudo bem comigo.",
            id="saudacao-atual",
        ),
        pytest.param(
            "Oi, lay. Terminei de organizar minhas notas.",
            "Oi! Você terminou de organizar suas notas.",
            id="saudacao-atual-com-relato",
        ),
        pytest.param(
            'A primeira linha do meu texto é "Oi!".',
            'A primeira linha do texto é "Oi!".',
            id="saudacao-como-citacao",
        ),
        pytest.param(
            'Repete literalmente: "Oi, tudo bem comigo!"',
            'Oi, tudo bem comigo!',
            id="repeticao-explicita",
        ),
        pytest.param(
            "Você perguntou como foi meu dia e eu não respondi. "
            "Agora quero saber: como você está?",
            "Tudo bem comigo, obrigada por perguntar.",
            id="retomada-explicita-bem-estar",
        ),
        pytest.param(
            RELATO_LITERAL,
            "Que bom que seu dia está bom e você está satisfeito com o resultado no navegador.",
            id="relato-atual-sem-inferir-verbo-ambigua",
        ),
        pytest.param(
            "Agora estou organizando minhas notas no navegador.",
            "As notas estão sendo organizadas no navegador.",
            id="relato-atual-segundo-dominio",
        ),
    ],
)
def test_reconhecimento_social_ou_citacao_so_continuam_quando_pertinentes(
    texto: str, fala: str,
) -> None:
    plano = _plano_atual(texto)
    resultado = validar_aderencia_contrato_fala(
        texto, fala, contrato_fala=plano["contrato_fala"], turno_id=plano["id"],
        ultima_resposta=RESPOSTA_ANTERIOR,
    )
    assert resultado["aceita"] is True, resultado
