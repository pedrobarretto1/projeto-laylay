from __future__ import annotations

import json

from mente_laylay.autonomia.processamento_resposta_ia import (
    preparar_resposta_para_execucao,
)
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
    contingencia_comunicacao,
    montar_mensagens_reparo_comunicacao,
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


def test_contraste_sem_predicado_e_resposta_interrompida() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "Você prefere rock ou metal?",
        (
            "Prefiro rock porque ele permite variar mais entre melodias e peso. "
            "Já o metal."
        ),
    )

    assert avaliacao["aceita"] is False
    assert "resposta_incompleta" in avaliacao["problemas_bloqueantes"]


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


def test_preferencia_pessoal_nao_pode_ser_trocada_por_tirada_sem_ancora() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "eu gosto de rock",
        "Se não tiver um riff forte, é só um som. E se tiver, é show.",
    )
    assert avaliacao["aceita"] is False
    assert "preferencia_pessoal_nao_reconhecida" in avaliacao["problemas"]


def test_preferencia_pessoal_reconhecida_com_clareza_e_aceita() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "eu gosto de rock",
        "Rock, boa. Qual banda mais te pega?",
    )
    assert avaliacao["aceita"] is True


def test_preferencia_de_terceiro_nao_pode_ser_atribuida_ao_usuario() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "minha namorada gosta de funk",
        "Você gosta de funk, então vou lembrar disso para as próximas músicas.",
    )

    assert avaliacao["aceita"] is False
    assert "preferencia_de_terceiro_atribuida_ao_usuario" in avaliacao["problemas"]


def test_contingencia_reconhece_preferencia_de_terceiro_sem_inventar() -> None:
    fala = contingencia_comunicacao(
        "tipo isso, e minha namorada gosta de funk"
    )

    assert "namorada" in fala.casefold()
    assert "funk" in fala.casefold()
    assert "você gosta" not in fala.casefold()


def test_como_assim_rejeita_referente_solto_e_nova_metafora() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "como assim?",
        (
            "Porque rock é só uma vibe de baterista que não para, e o outro "
            "que não desce. Se não tiver isso, é só um som de aparelho."
        ),
        ultima_resposta="Se não tiver um riff forte, é só um som. E se tiver, é show.",
    )
    assert avaliacao["aceita"] is False
    assert "referente_indefinido_na_resposta" in avaliacao["problemas"]
    assert "explicacao_permaneceu_nebulosa" in avaliacao["problemas"]


def test_como_assim_aceita_explicacao_literal_da_fala_anterior() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "como assim?",
        "Quis dizer que eu associo rock a riffs marcantes e energia de show.",
        ultima_resposta="Se não tiver um riff forte, é só um som. E se tiver, é show.",
    )
    assert avaliacao["aceita"] is True


def test_reexplicacao_literal_nao_pode_comecar_por_outra_metafora() -> None:
    anterior = "Prefiro rock porque ele varia mais entre melodias e peso."
    contrato = construir_contrato_semantico_fala(
        "Explica isso de um jeito simples.",
        mente={"ultima_resposta": anterior},
    )
    avaliacao = avaliar_qualidade_comunicacao(
        "Explica isso de um jeito simples.",
        "Rock é como um filme de domingo. Metal é como um filme de ação.",
        plano={"contrato_fala": contrato, "comandos": []},
        ultima_resposta=anterior,
    )

    assert avaliacao["aceita"] is False
    assert (
        "esclarecimento_comecou_por_outra_metafora"
        in avaliacao["problemas_bloqueantes"]
    )


def test_reparo_recebe_fala_anterior_e_regra_de_explicacao_direta() -> None:
    avaliacao = avaliar_qualidade_comunicacao(
        "como assim?",
        "É só uma vibe e o outro que não desce.",
        ultima_resposta="Rock me parece mais versátil.",
    )
    mensagens = montar_mensagens_reparo_comunicacao(
        "como assim?",
        "É só uma vibe e o outro que não desce.",
        avaliacao,
    )
    assert "Rock me parece mais versátil" in mensagens[1]["content"]
    assert "não tente explicar uma metáfora com outra" in mensagens[0]["content"]


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


def test_observacao_apenas_estilistica_nao_apaga_fala_original_nem_chama_reparo() -> None:
    chamadas = []
    original = "Entendi teu ponto. Quer continuar por aqui? Ou prefere mudar de assunto?"

    resposta = preparar_resposta_para_execucao(
        "tava falando disso só por falar",
        json.dumps({"fala": original, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=_MemoriaSemAprendizado(),
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert resposta["fala"] == original


def test_brincadeira_declarada_nao_vira_falha_tecnica_se_reparo_falhar() -> None:
    falhas = []
    resposta = preparar_resposta_para_execucao(
        "tava tirando uma onda só",
        '{"fala":"Entendi.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: '{"fala":"Tá.","comandos":[]}',
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=_MemoriaSemAprendizado(),
        registrar_falha_cb=lambda *args, **kwargs: falhas.append((args, kwargs)),
        contexto_comunicacao={
            "plano_turno": {
                "contrato_fala": construir_contrato_semantico_fala(
                    "tava tirando uma onda só"
                )
            }
        },
        log=lambda *_args: None,
    )

    assert any(
        item in resposta["fala"].casefold()
        for item in ("eu saquei", "era zoeira", "tá explicado")
    )
    assert falhas == []
    assert resposta["autocorrigida"] is True


def test_observacao_de_estilo_nao_reprova_fala_que_respondeu_o_nucleo() -> None:
    texto = "Você prefere rock ou metal?"
    contrato = construir_contrato_semantico_fala(texto)
    plano = {"texto_usuario": texto, "contrato_fala": contrato, "comandos": []}

    avaliacao = avaliar_qualidade_comunicacao(
        texto,
        "Rock, fácil.",
        plano=plano,
    )
    verificacao = verificar_fala_turno(
        "Rock, fácil.",
        plano=plano,
    )

    assert "opiniao_sem_criterio_concreto" in avaliacao["problemas"]
    assert avaliacao["problemas_bloqueantes"] == []
    assert avaliacao["aceita"] is True
    assert verificacao["aceita"] is True


def test_pergunta_de_preferencia_sem_posicao_continua_bloqueada() -> None:
    texto = "Você prefere rock ou metal?"
    contrato = construir_contrato_semantico_fala(texto)
    plano = {"texto_usuario": texto, "contrato_fala": contrato, "comandos": []}

    avaliacao = avaliar_qualidade_comunicacao(
        texto,
        "São dois estilos musicais bastante conhecidos.",
        plano=plano,
    )

    assert avaliacao["aceita"] is False
    assert "pergunta_direta_nao_respondida" in avaliacao["problemas_bloqueantes"]


def test_contingencia_responde_bem_estar_e_preferencia_sem_pedir_repeticao() -> None:
    social = contingencia_comunicacao("Oi Lay, tudo bem com você?")
    preferencia = contingencia_comunicacao("Você prefere rock ou metal?")

    assert "tô bem" in social.casefold()
    assert "e você" in social.casefold()
    assert any(opcao in preferencia.casefold() for opcao in ("rock", "metal"))
    assert "prefiro" in preferencia.casefold()
    assert "explica" not in preferencia.casefold()


def test_timeout_nao_chama_reparo_e_usa_contingencia_especifica() -> None:
    chamadas = []

    resposta = preparar_resposta_para_execucao(
        "Oi Lay, tudo bem com você?",
        "__LAYLAY_LLM_TIMEOUT__",
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True),
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=_MemoriaSemAprendizado(),
        contexto_contingencia={},
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert any(
        trecho in resposta["fala"].casefold()
        for trecho in ("tô bem", "tudo certo")
    )
    assert "tenta mais uma vez" not in resposta["fala"].casefold()


def test_registro_de_relacao_rejeita_sexualizacao_e_pergunta_soltea() -> None:
    texto = "Na verdade, Nanda é minha amiga."

    avaliacao = avaliar_qualidade_comunicacao(
        texto,
        "Qual é o seu lado mais gostoso dela?",
    )

    assert avaliacao["aceita"] is False
    assert "relacao_pessoal_sexualizada" in avaliacao["problemas_bloqueantes"]
    assert "relacao_pessoal_abriu_pergunta" in avaliacao["problemas_bloqueantes"]


def test_registro_de_relacao_aceita_fala_neutra_e_contingencia_preserva_fato() -> None:
    texto = "Na verdade, Nanda é minha amiga."
    fala_neutra = "Entendi: Nanda é sua amiga."

    avaliacao = avaliar_qualidade_comunicacao(texto, fala_neutra)
    contingencia = contingencia_comunicacao(texto)

    assert avaliacao["aceita"] is True
    assert "Nanda" in contingencia
    assert "amiga" in contingencia.casefold()
    assert "?" not in contingencia
    assert "gostoso" not in contingencia.casefold()
