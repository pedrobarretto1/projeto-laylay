from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
)
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.qualidade_comunicacao import contingencia_comunicacao
from mente_laylay.personalidade.diretor_fala import dirigir_fala
from mente_laylay.personalidade.perfil_amizade import (
    CONTRATO_AMIZADE_PROMPT,
    PERFIL_PERSONALIDADE,
    formatar_postura_para_prompt,
    selecionar_postura_amizade,
)


def _mente(funcao: str = "informacao", *, operacional: bool = False) -> dict:
    return {
        "especialistas_turno_atual": {
            "social": {
                "funcao": funcao,
                "permite_pergunta": True,
                "politica_resposta": "responder_diretamente",
            },
            "operacional": {"ativo": operacional},
        }
    }


def test_essencia_canonica_preserva_amizade_deboche_e_clareza() -> None:
    assert PERFIL_PERSONALIDADE["relacao"] == "amiga_proxima_sem_intimidade_inventada"
    assert PERFIL_PERSONALIDADE["humor"] == "debochado_seco_afetuoso_com_timing"
    assert "Converse como uma amiga próxima" in CONTRATO_AMIZADE_PROMPT
    assert "Seja solta sem ser aleatória" in CONTRATO_AMIZADE_PROMPT
    assert "responda primeiro e só então acrescente personalidade" in CONTRATO_AMIZADE_PROMPT


def test_postura_acolhedora_bloqueia_deboche_em_vulnerabilidade() -> None:
    postura = selecionar_postura_amizade(
        "Hoje eu tô um pouco cansado",
        estado_mental=_mente("desabafo"),
    )

    assert postura.nome == "acolhedora"
    assert postura.humor == "bloqueado"
    assert postura.max_tirada == 0


def test_postura_opinativa_pede_posicao_clara() -> None:
    postura = selecionar_postura_amizade(
        "Você prefere rock ou metal?",
        estado_mental=_mente(),
    )

    assert postura.nome == "opinativa"
    assert "posição clara" in postura.objetivo


def test_pergunta_social_recebe_postura_curta_sem_conselho_automatico() -> None:
    postura = selecionar_postura_amizade(
        "Tudo bem com você, Lay?",
        estado_mental=_mente(),
    )

    assert postura.nome == "reciproca_social"
    assert postura.max_frases == 2
    assert "não inventar corpo, fome ou sono" in postura.objetivo


def test_postura_operacional_nao_autoriza_pergunta_ou_execucao() -> None:
    postura = selecionar_postura_amizade(
        "abre o Opera",
        estado_mental=_mente(operacional=True),
    )
    contexto = formatar_postura_para_prompt(postura)

    assert postura.nome == "operacional_amigavel"
    assert postura.permite_pergunta is False
    assert "não cria, autoriza, altera nem confirma comandos" in contexto


def test_prompt_do_turno_recebe_postura_social_sem_inflar_identidade() -> None:
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE",
        estado_getter=lambda: {
            "messages": [],
            "turno_atual": {"modalidade": "conversa"},
            "especialistas_turno_atual": _mente("desabafo")["especialistas_turno_atual"],
        },
    )

    _mensagens, prompt = runtime.preparar("Hoje eu tô cansado")

    assert "POSTURA SOCIAL DESTE TURNO" in prompt
    assert "Postura: acolhedora" in prompt
    assert "não cria, autoriza, altera nem confirma comandos" in prompt


def test_diretor_publica_a_mesma_postura_usada_na_voz() -> None:
    direcao = dirigir_fala(
        "Entendo que o dia pesou. Vai no seu ritmo.",
        texto_usuario="Hoje eu tô cansado",
        estado_mental=_mente("desabafo"),
    )

    assert direcao["postura_amizade"]["nome"] == "acolhedora"
    assert direcao["humor"] == "nenhum"
    assert direcao["perfil_personalidade"] == PERFIL_PERSONALIDADE


def test_qualidade_rejeita_atendimento_que_ignora_estado_pessoal() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "Hoje eu tô um pouco cansado",
        "Posso oferecer algumas opções de atividades para esta noite?",
    )

    assert "estado_pessoal_nao_reconhecido" in avaliacao["problemas"]


def test_qualidade_rejeita_narracao_mecanica_e_interrogatorio() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "Você prefere rock ou metal?",
        "A pergunta é se eu prefiro rock ou metal. Eu prefiro rock. E você? Por quê?",
    )

    assert "narracao_mecanica_da_resposta" in avaliacao["problemas"]
    assert "perguntas_em_excesso" in avaliacao["problemas"]


def test_guardiao_rejeita_fome_e_corpo_fisico_da_laylay() -> None:
    fome = detectar_experiencia_pessoal_inventada(
        "Tá quase me matando de fome, mas ainda tô aqui."
    )
    corpo = detectar_experiencia_pessoal_inventada(
        "Hoje tô com o corpo em casa e a mente em outro lugar."
    )

    assert "corpo_ou_sentidos_inventados" in fome
    assert "corpo_ou_sentidos_inventados" in corpo


def test_pergunta_social_nao_vira_exercicio_de_respiracao() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "Tudo bem com você, Lay?",
        (
            "Tô bem. Se você tá cansado, respira 4 segundos, segura 4 e "
            "expira 6. Quer mais um exercício?"
        ),
    )

    assert "conselho_nao_solicitado_em_pergunta_social" in avaliacao["problemas"]


def test_contingencia_de_cansaco_e_humana_e_nao_usa_fallback_generico() -> None:
    fala = contingencia_comunicacao("Hoje eu tô meio cansado")

    assert "pega mais leve" in fala.casefold()
    assert "minha resposta não fechou" not in fala.casefold()


def test_caminho_real_substitui_fome_inventada_por_resposta_social() -> None:
    resposta = preparar_resposta_para_execucao(
        "oi lay, como voce esta?",
        '{"fala":"Tá quase me matando de fome, mas ainda tô aqui.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: (
            '{"fala":"Tô com o corpo em casa e a mente longe.","comandos":[]}'
        ),
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        log=lambda _texto: None,
    )

    assert resposta["fala"] == "Tô bem por aqui. E você, como tá?"
    assert not detectar_experiencia_pessoal_inventada(resposta["fala"])


def test_caminho_real_nao_entrega_fallback_generico_ao_relato_de_cansaco() -> None:
    resposta = preparar_resposta_para_execucao(
        "hoje eu to meio cansado",
        '{"fala":"Entendi.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: (
            '{"fala":"Peguei o que você disse.","comandos":[]}'
        ),
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        log=lambda _texto: None,
    )

    assert "pega mais leve" in resposta["fala"].casefold()
    assert "minha resposta não fechou" not in resposta["fala"].casefold()


def test_poesia_decorativa_so_passa_quando_o_pedido_e_criativo() -> None:
    comum = avaliar_qualidade_comunicacao(
        "Tudo bem com você?",
        "Meu coração bate no universo e as estrelas acordam minha alma.",
    )
    criativo = avaliar_qualidade_comunicacao(
        "Escreve um poema sobre o universo",
        "As estrelas atravessam a alma enquanto o universo respira.",
    )

    assert "poesia_decorativa_sem_contexto" in comum["problemas"]
    assert "poesia_decorativa_sem_contexto" not in criativo["problemas"]
