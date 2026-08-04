from __future__ import annotations

from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.processamento_resposta_ia import (
    extrair_emocao_da_ia,
    preparar_resposta_para_execucao,
)
from mente_laylay.autonomia.contexto_resposta_ia import preparar_contexto_resposta_ia
from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
)
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.personalidade.conversa_natural import construir_fala_conversa
from mente_laylay.personalidade.politica_voz_unica import voz_unica_llm_ativa
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT


def test_voz_unica_e_contrato_permanente() -> None:
    assert voz_unica_llm_ativa({}) is True
    assert voz_unica_llm_ativa({"LAYLAY_VOZ_UNICA_LLM": "0"}) is True


def test_guardiao_rejeita_corpo_e_relacao_pessoal_inventados() -> None:
    assert detectar_experiencia_pessoal_inventada(
        "Nirvana me deixa com os olhos no teto."
    ) == ["corpo_ou_sentidos_inventados"]
    assert detectar_experiencia_pessoal_inventada(
        "Meu irmão também gosta de funk."
    ) == ["relacao_pessoal_inventada"]


def test_fala_valida_da_llm_nao_e_reescrita_pelo_python() -> None:
    fala = "Claro, eu gostei dessa ideia justamente porque ela parece tua."
    contexto = {
        "_voz_unica_llm": True,
        "_fala_e_fallback_neutro": lambda _fala: False,
        "_ajustar_tom_por_emocao": lambda *_args: "FALA SUBSTITUÍDA",
        "_ajustar_fala_por_horario": lambda *_args: "FALA SUBSTITUÍDA",
    }

    assert construir_fala_conversa(contexto, fala, "gostou da ideia?", "conversa", []) == fala


def test_fallback_local_nao_finge_ser_resposta_da_llm() -> None:
    contexto = {
        "_voz_unica_llm": True,
        "_fala_e_fallback_neutro": lambda fala: "não consegui encaixar" in fala.casefold(),
    }

    assert construir_fala_conversa(
        contexto,
        "Não consegui encaixar isso direito. Me fala de outro jeito?",
        "como você está?",
        "conversa",
        [],
    ) == ""


def test_pre_fluxo_nao_consume_conversa_social_no_modo_voz_unica() -> None:
    falas: list[str] = []
    contexto = {
        "_voz_unica_llm": True,
        "mente_integrada_estado": {
            "turno_atual": {
                "modalidade_geral": "conversa",
                "autoriza_execucao": False,
            },
            "pendencia_atual": {},
        },
        "_contexto_horario_atual": lambda: "noite",
        "_refinar_contexto_mental": lambda _texto: {},
        "_texto_social_curto": lambda _texto: True,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_resposta_conversa_rapida_local": lambda _texto: "Resposta escrita pelo Python.",
        "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    assert processar_inicio_fluxo_resposta_ia(contexto, "oi lay, como você está?") is False
    assert falas == []


def test_voz_unica_tambem_preserva_recusa_correcao_e_confirmacao_sociais() -> None:
    for modalidade, texto in (
        ("recusa", "não gostei muito disso"),
        ("correcao", "não foi isso que eu quis dizer"),
        ("confirmacao", "sim, eu concordo com você"),
    ):
        falas: list[str] = []
        contexto = {
            "_voz_unica_llm": True,
            "mente_integrada_estado": {
                "turno_atual": {
                    "modalidade_geral": modalidade,
                    "autoriza_execucao": False,
                },
                "pendencia_atual": {},
            },
            "_contexto_horario_atual": lambda: "noite",
            "_refinar_contexto_mental": lambda _texto: {},
            "_texto_social_curto": lambda _texto: True,
            "_texto_conversa_casual_sem_acao": lambda _texto: True,
            "_resposta_conversa_rapida_local": lambda _texto: "Resposta local.",
            "_emitir_resposta_curta": lambda *_args, **_kwargs: falas.append("falou"),
        }
        contexto["_recarregar_contexto_inicio"] = lambda ctx=contexto: dict(ctx)

        assert processar_inicio_fluxo_resposta_ia(contexto, texto) is False
        assert falas == []


def test_pre_fluxo_nao_reclassifica_comando_autorizado() -> None:
    executados: list[str] = []
    contexto = {
        "_voz_unica_llm": True,
        "mente_integrada_estado": {
            "turno_atual": {
                "modalidade_geral": "comando",
                "ato_principal": "comando",
                "autoriza_execucao": True,
            },
            "pendencia_atual": {},
        },
        "_contexto_horario_atual": lambda: "noite",
        "_refinar_contexto_mental": lambda _texto: {},
        "processar_comando_deterministico": (
            lambda texto, *_args: executados.append(texto) or True
        ),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    assert processar_inicio_fluxo_resposta_ia(contexto, "desliga a luz") is False
    assert executados == []


def test_prompt_novo_contem_so_identidade_contexto_e_contrato() -> None:
    assert len(BASE_SYSTEM_PROMPT) < 5000
    assert "Você é Laylay" in BASE_SYSTEM_PROMPT
    assert "PERSONALIDADE E PRESENÇA:" in BASE_SYSTEM_PROMPT
    assert "levemente debochada" in BASE_SYSTEM_PROMPT
    assert "no máximo uma tirada curta por resposta" in BASE_SYSTEM_PROMPT
    assert "evite poesia aleatória e humor forçado" in BASE_SYSTEM_PROMPT
    assert "responda primeiro e só então acrescente personalidade" in BASE_SYSTEM_PROMPT
    assert "Só culpe com causa e confiança explícitas" in BASE_SYSTEM_PROMPT
    assert "ciúme brincalhão" in BASE_SYSTEM_PROMPT
    assert "Nunca seja possessiva" in BASE_SYSTEM_PROMPT
    assert "Molde o tamanho à necessidade" in BASE_SYSTEM_PROMPT
    assert "problemas complexos, os passos úteis" in BASE_SYSTEM_PROMPT
    assert "no máximo uma pergunta por turno" in BASE_SYSTEM_PROMPT
    assert "Humanidade vem de atenção, reciprocidade e timing" in BASE_SYSTEM_PROMPT
    assert "são cortesia, não uma pendência" in BASE_SYSTEM_PROMPT
    assert "reconheça o deslize sem se defender" in BASE_SYSTEM_PROMPT
    assert "Não transforme uma informação simples em declaração solene" in BASE_SYSTEM_PROMPT
    assert "Evite explicar que é \"só uma conversa\"" in BASE_SYSTEM_PROMPT
    assert "Tenha gostos sem fingir experiências" in BASE_SYSTEM_PROMPT
    assert "doce sem ser mole, firme sem ser arrogante" in BASE_SYSTEM_PROMPT
    assert "opinião própria" in BASE_SYSTEM_PROMPT
    assert "deboche seco com timing" in BASE_SYSTEM_PROMPT
    assert "Não concorde por reflexo" in BASE_SYSTEM_PROMPT
    assert "Fale de forma concreta" in BASE_SYSTEM_PROMPT
    assert "Não use alma, universo, neblina, estrelas" in BASE_SYSTEM_PROMPT
    assert "Metáfora é exceção" in BASE_SYSTEM_PROMPT
    assert "linguagem vívida quando o usuário pedir criação artística" in BASE_SYSTEM_PROMPT
    assert "Não comece por hábito" in BASE_SYSTEM_PROMPT
    assert "reaja ao detalhe real antes do tema" in BASE_SYSTEM_PROMPT
    assert "Deboche bom é curto, específico e situacional" in BASE_SYSTEM_PROMPT
    assert "nunca vulnerabilidade, dor, erro, inteligência ou valor da pessoa" in BASE_SYSTEM_PROMPT
    assert "Use contexto e memória" in BASE_SYSTEM_PROMPT
    assert "COMANDOS:" in BASE_SYSTEM_PROMPT
    assert "no mesmo turno" in BASE_SYSTEM_PROMPT
    assert "3 a 5 opções" in BASE_SYSTEM_PROMPT
    assert "listar_playlist" in BASE_SYSTEM_PROMPT
    assert "Retorne somente JSON válido" in BASE_SYSTEM_PROMPT
    assert '"emocao":"calma"' in BASE_SYSTEM_PROMPT
    assert '"nivel_emocao":1' in BASE_SYSTEM_PROMPT


def test_llm_escolhe_emocao_e_intensidade_validas() -> None:
    assert extrair_emocao_da_ia(
        '{"fala":"Aí sim!","emocao":"feliz","nivel_emocao":3,"comandos":[]}'
    ) == ("alegre", 3)
    assert extrair_emocao_da_ia(
        r'{\"fala\":\"Eita.\",\"emocao\":\"surpresa\",\"nivel_emocao\":2'
    ) == ("surpresa", 2)


def test_emocao_desconhecida_da_llm_e_ignorada() -> None:
    assert extrair_emocao_da_ia(
        '{"fala":"Oi.","emocao":"caotica","nivel_emocao":99,"comandos":[]}'
    ) == ("", 0)


def test_preparador_preserva_decisao_emocional_da_llm() -> None:
    resposta = preparar_resposta_para_execucao(
        "consegui terminar o projeto!",
        '{"fala":"Aí sim! Essa vitória foi bonita.","emocao":"alegre","nivel_emocao":2,"comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=None,
        log=lambda *_args: None,
    )

    assert resposta["emocao"] == "alegre"
    assert resposta["nivel_emocao"] == 2


def test_verificador_final_nao_edita_escolhas_conversacionais_da_llm() -> None:
    fala = "Eu gostei dessa ideia. E você, o que viu nela?"
    resultado = verificar_fala_turno(
        fala,
        plano={
            "texto_usuario": "gostou da ideia?",
            "funcao_comunicativa": "conversa",
            "permite_pergunta": False,
            "comandos": [],
        },
        periodo="noite",
        ultima_resposta=fala,
        origem="ia_final",
    )

    assert resultado["aceita"] is True
    assert resultado["fala"] == fala
    assert "pergunta_inadequada_a_funcao_emocional" not in resultado["problemas"]
    assert "repeticao_exata" not in resultado["problemas"]


def test_verificador_final_mantem_barreira_contra_execucao_inventada() -> None:
    resultado = verificar_fala_turno(
        "Pronto, já desliguei a luz.",
        plano={
            "texto_usuario": "desliga a luz",
            "requer_execucao": True,
            "comandos": [],
        },
        origem="ia_final",
    )

    assert "comando_sem_execucao_confirmada" in resultado["problemas"]
    assert "não executei nem confirmei" in resultado["fala"]


def test_guardiao_detecta_o_surto_do_bolo_sem_bloquear_emocao() -> None:
    problemas = detectar_experiencia_pessoal_inventada(
        "Hoje eu tô comendo um bolo de abacaxi que o Pedro me deu no domingo."
    )
    assert "experiencia_fisica_inventada" in problemas
    assert "objeto_fisico_recebido_inventado" in problemas
    assert detectar_experiencia_pessoal_inventada(
        "Hoje eu fiquei feliz com a nossa conversa."
    ) == []


def test_guardiao_detecta_experiencia_fisica_intercalada_por_frase_de_apoio() -> None:
    problemas = detectar_experiencia_pessoal_inventada(
        "Ah, cansado? Tô aqui, sem pedir nada, só comendo arroz e bebendo água."
    )

    assert "experiencia_fisica_inventada" in problemas


def test_guardiao_detecta_corpo_cozinha_e_passado_compartilhado_falsos() -> None:
    corpo = detectar_experiencia_pessoal_inventada(
        "Não sei se isso faz bem pro meu sistema digestivo; eu já vi pessoas provarem."
    )
    futuro = detectar_experiencia_pessoal_inventada(
        "Se um dia eu fizer uma pizza pra você, vou caprichar no queijo."
    )
    memoria = detectar_experiencia_pessoal_inventada(
        "Daquela vez que você disse que queria café, eu falei que faria pão de queijo."
    )

    assert "corpo_ou_sentidos_inventados" in corpo
    assert "capacidade_fisica_futura_inventada" in futuro
    assert "passado_compartilhado_inventado" in memoria


def test_ideia_imaginativa_clara_continua_permitida() -> None:
    assert detectar_experiencia_pessoal_inventada(
        "Na nossa invenção, eu apostaria em abacaxi com um toque leve de mel."
    ) == []


def test_experiencia_fisica_e_reescrita_pela_llm_e_nao_pelo_python() -> None:
    chamadas: list[object] = []

    def enviar(mensagens, **_kwargs):
        chamadas.append(mensagens)
        return '{"fala":"Meu dia ficou mais divertido com essa conversa.","comandos":[]}'

    resposta = preparar_resposta_para_execucao(
        "e como vai seu dia?",
        '{"fala":"Hoje eu estou comendo um bolo que o Pedro me deu.","comandos":[]}',
        enviar_mensagem_cb=enviar,
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        log=lambda _texto: None,
    )

    assert resposta["fala"] == "Meu dia ficou mais divertido com essa conversa."
    assert resposta["suprimir_fala"] is False
    assert len(chamadas) == 1


def test_memoria_falsa_e_reescrita_sem_matar_a_brincadeira() -> None:
    def enviar(_mensagens, **_kwargs):
        return (
            '{"fala":"Tô inspirada hoje kkk. Na nossa invenção, abacaxi com um toque '
            'leve de mel talvez funcione.","comandos":[]}'
        )

    resposta = preparar_resposta_para_execucao(
        "tá sabendo das ideias kkkk",
        '{"fala":"Daquela vez que você pediu café, eu prometi fazer pão de queijo.","comandos":[]}',
        enviar_mensagem_cb=enviar,
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        log=lambda _texto: None,
    )

    assert "Daquela vez" not in resposta["fala"]
    assert "nossa invenção" in resposta["fala"]
    assert resposta["suprimir_fala"] is False


def test_inventacao_total_sem_reparo_vira_contingencia_contextual() -> None:
    resposta = preparar_resposta_para_execucao(
        "eu gosto de funk",
        '{"fala":"Meu irmão também gosta de funk.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: (
            '{"fala":"Meus olhos até brilham com funk.","comandos":[]}'
        ),
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        log=lambda _texto: None,
    )

    assert resposta["fala"] == "Peguei: você gosta de funk."
    assert resposta["suprimir_fala"] is False


def test_verificador_final_remove_inventacao_que_escape_da_primeira_barreira() -> None:
    resultado = verificar_fala_turno(
        "A combinação parece divertida. Se um dia eu fizer uma pizza pra você, coloco mel.",
        plano={
            "texto_usuario": "esse sabor parece daora",
            "requer_execucao": False,
            "comandos": [],
        },
        origem="ia_final",
    )

    assert resultado["aceita"] is True
    assert resultado["fala"] == "A combinação parece divertida."
    assert "capacidade_fisica_futura_inventada" in resultado["problemas"]


def test_inventacao_da_assistente_nao_reentra_como_memoria_do_prompt() -> None:
    mensagens, _prompt = preparar_contexto_resposta_ia(
        {},
        "eu não te dei bolo nenhum",
        [
            {"role": "system", "content": "prompt antigo"},
            {"role": "user", "content": "como vai seu dia?"},
            {
                "role": "assistant",
                "content": "Estou comendo um bolo que o Pedro me deu no domingo.",
            },
            {"role": "user", "content": "eu não te dei bolo nenhum"},
        ],
        0,
        BASE_SYSTEM_PROMPT,
    )

    conteudos = [str(item.get("content") or "") for item in mensagens]
    assert not any("Estou comendo um bolo" in item for item in conteudos)
    assert any("eu não te dei bolo nenhum" in item for item in conteudos)
