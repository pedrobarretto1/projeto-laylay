from __future__ import annotations

import asyncio
import threading
import time

from mente_laylay.autonomia.pre_fluxo_contextual import (
    analisar_intencao_com_porteiro,
    texto_eh_conversa_social_sem_comando,
    texto_deve_evitar_llm_de_comando,
)
from mente_laylay.autonomia.porteiro_acoes import texto_conversa_casual_sem_acao
from mente_laylay.autonomia.processamento_resposta_ia import filtrar_comandos_sem_pedido_atual
from mente_laylay.cognicao.conversa_sobre_capacidades import (
    resposta_conversa_sobre_capacidade,
    texto_discute_capacidade_futura,
)
from mente_laylay.cognicao.interpretacao_intencao import InterpretacaoIntencaoRuntime
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social
from mente_laylay.cognicao.resumo_conteudo import (
    ResumoConteudoRuntime,
    _limpar_texto_capturado,
    resumir_pagina_ou_video,
)
from mente_laylay.integracao.llm_http import post_chat_llm
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta
from mente_laylay.memoria_mental.sessao_conversa import (
    renovar_contexto_sessao,
    texto_encerra_conversa,
)
from mente_laylay.memoria_mental.musica_conversacional import (
    sugestao_musical_nova_conversacional,
    texto_pede_direcao_musical_generica,
)
from mente_laylay.personalidade.conversa_natural import (
    classificar_conversa_curta_local,
    construir_fala_conversa,
    responder_agradecimento_ou_elogio,
    responder_conversa_curta_por_tipo,
    tipo_reconhecimento_afetivo,
)
from mente_laylay.emocoes.perfil_emocional import limpar_para_voz
from mente_laylay.personalidade.oralidade import naturalizar_texto_para_fala
from mente_laylay.personalidade.ritmo_natural import ajustar_uso_natural_nome
from mente_laylay.personalidade.abertura_chat import AberturaChatRuntime
from mente_laylay.autonomia.modo_chat import InteracaoChatRuntime


def _ctx_conversa_basico() -> dict:
    return {"_normalizar_texto_com_apelidos": lambda texto: str(texto or "").casefold()}


def test_atalho_do_chat_usa_abertura_local_sem_acordar_llm() -> None:
    chamadas = []

    class AberturaFake:
        def gerar_local(self, tipo):
            chamadas.append(("local", tipo))
            return "Tô te ouvindo."

        def gerar(self):
            chamadas.append(("llm", "chat"))
            return "não deveria acontecer"

    runtime = InteracaoChatRuntime(
        estado_runtime_getter=lambda: None,
        modo_chat_runtime_getter=lambda: None,
        abertura_runtime_getter=lambda: AberturaFake(),
        processar_texto=lambda *_args: None,
        escutar_terminal=lambda *_args, **_kwargs: None,
        keyboard_mod=None,
        hotkey_liga="f10",
        hotkey_desliga="f11",
        stdin_getter=lambda: None,
        raw_print=lambda *_args: None,
        print_lock=None,
    )

    assert runtime.gerar_abertura() == "Tô te ouvindo."
    assert chamadas == [("local", "chat")]


def test_perguntas_sociais_naturais_sao_reconhecidas_sem_frase_exata() -> None:
    ctx = _ctx_conversa_basico()
    assert classificar_conversa_curta_local(ctx, "como que voce ta?")["tipo"] == "WELLBEING"
    assert classificar_conversa_curta_local(
        ctx, "tem algum assunto para a gente conversar?"
    )["tipo"] == "PERSONAL_CHAT"


def test_bem_estar_usa_perspectiva_e_contexto_em_vez_da_expressao_isolada() -> None:
    mente = {
        "ultima_resposta": "Tô bem. Cabeça no lugar. Mas e você, tá tudo bem por aí?",
    }
    ctx = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto or "").casefold(),
        "mente_integrada_estado": mente,
    }

    assert classificar_conversa_curta_local(ctx, "ta tudo bem sim")["tipo"] == "WELLBEING_REPLY"
    assert classificar_conversa_curta_local(ctx, "ta tudo bem por aqui")["tipo"] == "WELLBEING_REPLY"
    assert classificar_conversa_curta_local(ctx, "eu estou bem")["tipo"] == "WELLBEING_REPLY"
    assert classificar_conversa_curta_local(ctx, "ta tudo bem?")["tipo"] == "WELLBEING"
    assert classificar_conversa_curta_local(ctx, "tudo bem com voce lay?")["tipo"] == "WELLBEING"


def test_resposta_de_bem_estar_nao_repete_a_pergunta_para_pedro() -> None:
    ctx = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto or "").casefold(),
        "_normalizar_texto_curto": lambda texto: str(texto or "").casefold(),
        "_ajustar_fala_por_horario": lambda fala, *_args: fala,
        "mente_integrada_estado": {
            "ultima_resposta": "Tô bem. E você, como tá?",
        },
        "foco_vivo": {},
    }

    for texto in ("ta tudo bem sim", "ta tudo bem por aqui", "eu estou bem"):
        leitura = classificar_conversa_curta_local(ctx, texto)
        fala = responder_conversa_curta_por_tipo(ctx, leitura["tipo"], texto)
        assert "?" not in fala


def test_recusa_com_novo_assunto_nao_vira_cancelamento_operacional() -> None:
    ctx = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto or "").casefold(),
        "_normalizar_texto_curto": lambda texto: str(texto or "").casefold(),
        "mente_integrada_estado": {},
    }
    texto = "precisa nao eu vou sair para comer ja"

    assert classificar_conversa_curta_local(ctx, texto) == {}
    assert construir_fala_conversa(ctx, "", texto, "conversa", []) == ""


def test_correcao_atual_prevalece_sobre_agradecimento_semantico_antigo() -> None:
    ctx = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto or "").casefold(),
        "_normalizar_texto_curto": lambda texto: str(texto or "").casefold(),
        "_texto_social_curto": lambda _texto: True,
        "_texto_conversa_casual_sem_acao": lambda _texto: True,
        "_texto_tem_comando_explicito": lambda _texto: False,
        "mente_integrada_estado": {
            "turno_atual": {
                "modalidade": "correcao",
                "leitura_semantica": {
                    "uso_conversacional": True,
                    "atos": [{"tipo": "agradecimento", "confianca": 0.91}],
                },
            },
        },
    }
    texto = "não lay, eu ainda estou no menu"

    assert classificar_conversa_curta_local(ctx, texto) == {}
    assert texto_eh_conversa_social_sem_comando(ctx, texto) is False


def test_recusa_isolada_so_cancela_quando_ha_pendencia_operacional() -> None:
    base = {
        "_normalizar_texto_com_apelidos": lambda texto: str(texto or "").casefold(),
        "_normalizar_texto_curto": lambda texto: str(texto or "").casefold(),
        "_ajustar_fala_por_horario": lambda fala, *_args: fala,
    }
    sem_pendencia = dict(base, mente_integrada_estado={})
    com_pendencia = dict(base, mente_integrada_estado={
        "pendencia_atual": {
            "status": "ativa", "dominio": "iot", "intencao": "IOT_CONTROL",
        },
    })

    leitura_sem_pendencia = classificar_conversa_curta_local(sem_pendencia, "nao precisa")
    assert leitura_sem_pendencia.get("tipo") != "SOFT_DECLINE"
    assert responder_conversa_curta_por_tipo(
        sem_pendencia, leitura_sem_pendencia.get("tipo", ""), "nao precisa"
    ) == ""
    leitura = classificar_conversa_curta_local(com_pendencia, "nao precisa")
    assert leitura["tipo"] == "SOFT_DECLINE"
    fala = responder_conversa_curta_por_tipo(com_pendencia, "SOFT_DECLINE", "nao precisa")
    assert fala


def test_fala_social_ambigua_sem_contexto_nao_e_forcada_localmente() -> None:
    assert analisar_ato_social("tudo bem")["tipo"] == "AMBIGUO"
    assert classificar_conversa_curta_local(_ctx_conversa_basico(), "tudo bem") == {}


def test_palavra_bem_em_outro_assunto_nao_vira_bem_estar() -> None:
    leitura = classificar_conversa_curta_local(_ctx_conversa_basico(), "esse jogo roda bem?")
    assert leitura["tipo"] == "QUESTION"


def test_pergunta_sobre_qualquer_tema_nao_vira_desabafo_positivo() -> None:
    ctx = _ctx_conversa_basico()
    texto = "voce viu que vai sair um jogo novo? estou muito animado para jogar"
    assert texto_conversa_casual_sem_acao(texto)
    assert classificar_conversa_curta_local(ctx, texto) == {}
    assert construir_fala_conversa(ctx, "", texto, "conversa", []) == ""


def test_alegria_sem_pergunta_recebe_resposta_positiva() -> None:
    ctx = _ctx_conversa_basico()
    texto = "estou muito animado com meu projeto"
    leitura = classificar_conversa_curta_local(ctx, texto)
    assert leitura["tipo"] == "EMOTIONAL_STATE"
    fala = responder_conversa_curta_por_tipo(ctx, "EMOTIONAL_STATE", texto).casefold()
    assert "solução" not in fala
    assert any(palavra in fala for palavra in ("anima", "empolg", "curiosa"))


def test_ia_nao_pode_inventar_acao_pratica_durante_conversa() -> None:
    comando = {"acao": "open_url", "url": "https://example.com"}
    permitidos, bloqueados = filtrar_comandos_sem_pedido_atual(
        "voce ja ouviu falar desse lançamento?", [comando], tipo_interacao="acao"
    )
    assert permitidos == []
    assert bloqueados == ["open_url"]

    permitidos, bloqueados = filtrar_comandos_sem_pedido_atual(
        "abre o site example.com", [comando], tipo_interacao="acao"
    )
    assert permitidos == [comando]
    assert bloqueados == []


def test_pontuacao_de_emoji_removido_nao_produz_interrogacao_com_ponto() -> None:
    assert limpar_para_voz("Tudo bem? 😊") == "Tudo bem?"
    assert naturalizar_texto_para_fala("Tudo bem?.") == "Tudo bem?"


def test_capacidade_futura_e_conversa_e_nao_comando() -> None:
    texto = "Vou te dar uma nova habilidade: você vai poder controlar a luz do quarto. Legal, não?"
    assert texto_discute_capacidade_futura(texto)
    assert "iluminação" in resposta_conversa_sobre_capacidade(texto).lower()

    ctx = {
        "_texto_tem_comando_explicito": lambda _texto: True,
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: False,
        "_texto_conversa_contextual_sem_comando": lambda _texto: False,
    }
    assert texto_deve_evitar_llm_de_comando(ctx, texto)


def test_porteiro_trata_none_como_ausencia_de_intencao() -> None:
    ctx = {
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_texto_social_curto": lambda _texto: False,
        "_texto_conversa_casual_sem_acao": lambda _texto: False,
        "_texto_conversa_contextual_sem_comando": lambda _texto: False,
        "analisar_intencao": lambda _texto: None,
    }
    assert analisar_intencao_com_porteiro(ctx, "uma frase ambígua") == ("sem_intencao", None)


def test_analisador_reaproveita_decisao_do_mesmo_texto() -> None:
    chamadas = []

    def enviar(*_args, **_kwargs):
        chamadas.append(1)
        return '{"intent":"NONE","params":{}}'

    runtime = InterpretacaoIntencaoRuntime(
        contexto_getter=lambda: {
            "enviar_mensagem": enviar,
            "estado": {},
            "normalizar_texto": lambda texto: texto.lower(),
        }
    )
    primeira = runtime.analisar("conversa repetida")
    segunda = runtime.analisar("conversa repetida")
    assert primeira == segunda
    assert len(chamadas) == 1


def test_analisador_nao_reaproveita_decisao_quando_contexto_muda() -> None:
    chamadas = []
    mente = {
        "continuidade_geral": {
            "dominio_ativo": "musica",
            "dominios": {
                "musica": {
                    "intent": "PLAYLIST_PLAY",
                    "alvo": "kamaitachi",
                    "params": {"nome_playlist": "kamaitachi"},
                }
            },
        }
    }

    def enviar(*_args, **_kwargs):
        chamadas.append(1)
        return '{"intent":"NONE","params":{}}'

    runtime = InterpretacaoIntencaoRuntime(
        contexto_getter=lambda: {
            "enviar_mensagem": enviar,
            "estado": {"mente_integrada_estado": mente},
            "normalizar_texto": lambda texto: texto.lower(),
        }
    )

    runtime.analisar("quais tem nela")
    mente["continuidade_geral"] = {
        "dominio_ativo": "iot",
        "dominios": {
            "iot": {
                "intent": "IOT_CONTROL",
                "alvo": "lampada_quarto",
                "params": {"alvo": "lampada_quarto"},
            }
        },
    }
    runtime.analisar("quais tem nela")

    assert len(chamadas) == 2


def test_consulta_natural_pode_usar_ia_first_sem_ser_bloqueada_como_conversa() -> None:
    runtime = InterpretacaoIntencaoRuntime(
        contexto_getter=lambda: {
            "enviar_mensagem": lambda *_args, **_kwargs: (
                '{"intent":"IOT_LIST","params":{}}'
            ),
            "estado": {},
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "texto_parece_consulta_operacional": lambda _texto: True,
            "texto_conversa_casual_sem_acao": lambda _texto: True,
            "texto_conversa_contextual_sem_comando": lambda _texto: True,
            "texto_social_curto": lambda _texto: False,
            "texto_bloqueia_playlist_agora": lambda _texto: False,
            "texto_pede_direcao_musical_generica": lambda _texto: False,
            "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        }
    )

    assert runtime.tentar_ai_primeiro("quais aparelhos estão disponíveis?") == {
        "intent": "IOT_LIST",
        "params": {},
    }


def test_consulta_natural_bloqueia_acao_de_escrita_proposta_pela_ia() -> None:
    runtime = InterpretacaoIntencaoRuntime(
        contexto_getter=lambda: {
            "enviar_mensagem": lambda *_args, **_kwargs: (
                '{"intent":"IOT_CONTROL","params":{"acao":"desligar","alvo":"luz"}}'
            ),
            "estado": {},
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "texto_parece_consulta_operacional": lambda _texto: True,
            "texto_conversa_casual_sem_acao": lambda _texto: True,
            "texto_conversa_contextual_sem_comando": lambda _texto: True,
            "texto_social_curto": lambda _texto: False,
            "texto_bloqueia_playlist_agora": lambda _texto: False,
            "texto_pede_direcao_musical_generica": lambda _texto: False,
            "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        }
    )

    assert runtime.tentar_ai_primeiro("qual é o estado da luz?") is None


def test_continuacao_musical_entende_estilo_geek() -> None:
    estado = {
        "ultima_resposta": "Você quer uma música de qual estilo?",
        "ultima_habilidade": "musica",
    }
    assert texto_pede_direcao_musical_generica(
        "uma mais geek",
        estado_mental=estado,
        normalizar_texto=lambda texto: texto.lower(),
    )
    sugestao = sugestao_musical_nova_conversacional(
        "uma mais geek",
        normalizar_texto=lambda texto: texto.lower(),
    )
    assert sugestao in {
        "The Living Tombstone - My Ordinary Life",
        "DAGames - Build Our Machine",
        "CG5 - I See a Dreamer",
        "JT Music - Join Us For A Bite",
    }


def test_coloca_uma_musica_e_pedido_generico_com_pendencia() -> None:
    assert texto_pede_direcao_musical_generica(
        "coloca uma música",
        estado_mental={},
        normalizar_texto=lambda texto: texto.casefold(),
    ) is True


def test_vontade_de_ouvir_musica_sem_titulo_fica_no_fluxo_musical() -> None:
    assert texto_pede_direcao_musical_generica(
        "eu queria ouvir uma música na verdade",
        estado_mental={},
        normalizar_texto=lambda texto: texto.casefold(),
    ) is True


def test_erro_500_local_preserva_assunto_da_conversa() -> None:
    class Resposta500:
        status_code = 500
        text = "erro interno"

    resposta, limite = post_chat_llm(
        {},
        {
            "messages": [
                {"role": "user", "content": "Você vai poder controlar a luz do quarto com uma habilidade nova"}
            ],
            "max_tokens": 100,
        },
        base_url="http://localhost:11434/v1",
        local_timeout=5,
        remote_timeout=5,
        bad_request_until=0,
        lock=threading.Lock(),
        requests_post=lambda *_args, **_kwargs: Resposta500(),
        print_fn=lambda *_args, **_kwargs: None,
    )
    assert resposta.status_code == 200
    assert "iluminação" in resposta.json()["choices"][0]["message"]["content"].lower()
    assert limite > 0


def test_resumo_registra_referente_e_pergunta_dela_mantem_assunto() -> None:
    registro = {
        "status": "concluido",
        "titulo": "Coxinha – Wikipédia",
        "referente": "Coxinha",
        "resumo": "Coxinha é um salgado brasileiro popular feito com massa e frango.",
        "conteudo": "A coxinha surgiu no século XIX e se popularizou no Brasil.",
        "ts": time.time(),
    }
    chamadas = []

    def enviar(_mensagens, **_kwargs):
        chamadas.append(1)
        return '{"fala":"Uma receita geral de coxinha usa farinha, caldo, frango desfiado, empanamento e óleo para fritar."}'

    ctx = {
        "mente_integrada_estado": {"ultimo_resumo_pagina": registro},
        "enviar_mensagem": enviar,
        "_extrair_json_da_ia": lambda texto: texto,
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
    }
    fala = construir_fala_conversa(
        ctx,
        "Não peguei com segurança o referente.",
        "qual a receita dela?",
        "conversa",
        [],
    )
    assert len(chamadas) == 1
    assert "farinha" in fala.casefold()
    assert "frango" in fala.casefold()


def test_conteudo_curto_da_pagina_e_recapturado_antes_de_falhar() -> None:
    respostas = [
        {"success": True, "data": {"url": "https://exemplo.test", "title": "Coxinha", "content": "curto"}},
        {
            "success": True,
            "data": {
                "url": "https://exemplo.test",
                "title": "Coxinha – História",
                "content": "Coxinha é um salgado brasileiro com uma história bastante conhecida. " * 3,
            },
        },
    ]
    registros = []
    falas = []

    async def solicitar():
        return respostas.pop(0)

    resultado = asyncio.run(resumir_pagina_ou_video(
        websocket_disponivel=lambda: True,
        solicitar_conteudo=solicitar,
        falar=lambda fala, *_args: falas.append(fala),
        enviar_mensagem=lambda *_args, **_kwargs: "Coxinha é um salgado brasileiro de massa recheada.",
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
        transcript_api=object(),
        registrar_contexto=registros.append,
        aguardar=lambda _tempo: asyncio.sleep(0),
        log=lambda *_args: None,
    ))
    assert resultado
    assert registros[-1]["status"] == "concluido"
    assert registros[-1]["referente"] == "Coxinha"
    assert "salgado" in falas[-1].casefold()


def test_resumo_de_pagina_preserva_resultado_quando_transporte_llm_falha() -> None:
    falas: list[str] = []
    registros: list[dict] = []

    def enviar_com_falha(*_args, **_kwargs):
        raise TimeoutError("modelo local não respondeu")

    resultado = asyncio.run(resumir_pagina_ou_video(
        websocket_disponivel=lambda: True,
        solicitar_conteudo=lambda: asyncio.sleep(0, result={
            "success": True,
            "data": {
                "url": "https://exemplo.test/artigo",
                "title": "Artigo sobre manutenção",
                "content": (
                    "A manutenção preventiva reduz falhas inesperadas. "
                    "O artigo recomenda testes pequenos antes da implantação."
                ),
            },
        }),
        falar=lambda fala, *_args: falas.append(fala),
        enviar_mensagem=enviar_com_falha,
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
        transcript_api=object(),
        registrar_contexto=registros.append,
        log=lambda *_args: None,
    ))

    assert resultado is True
    assert registros[-1]["status"] == "concluido"
    assert "manutenção preventiva" in falas[-1].casefold()


def test_runtime_de_resumo_sem_modelo_ainda_le_pagina_e_responde() -> None:
    falas: list[str] = []
    registros: list[dict] = []
    logs: list[str] = []

    runtime = ResumoConteudoRuntime(
        namespace_getter=lambda: {
            "websocket_disponivel": lambda: True,
            "solicitar_conteudo": lambda: asyncio.sleep(0, result={
                "success": True,
                "data": {
                    "url": "https://exemplo.test/manutencao",
                    "title": "Guia de manutenção",
                    "content": (
                        "A manutenção preventiva reduz falhas inesperadas. "
                        "Testes pequenos ajudam a validar cada mudança."
                    ),
                },
            }),
            "falar": lambda fala, *_args: falas.append(fala),
            "limpar_resposta": lambda texto: texto,
            "remover_prefixo_exec": lambda texto: texto,
            "transcript_api": object(),
            "registrar_contexto_resumo": registros.append,
        },
        log=logs.append,
    )

    assert asyncio.run(runtime.resumir()) is True
    assert any("modelo indisponível" in item for item in logs)
    assert falas and "manutenção preventiva" in falas[-1].casefold()
    assert registros[-1]["status"] == "concluido"
    assert "direto pelo texto" in falas[-1].casefold()


def test_resumo_absorve_sentinela_da_llm_e_entrega_leitura_local() -> None:
    falas: list[str] = []
    registros: list[dict] = []

    resultado = asyncio.run(resumir_pagina_ou_video(
        websocket_disponivel=lambda: True,
        solicitar_conteudo=lambda: asyncio.sleep(0, result={
            "success": True,
            "data": {
                "url": "https://exemplo.test/artigo",
                "title": "História da China - Wikipédia, a enciclopédia livre",
                "content": (
                    "Alternar o índice História da China 98 idiomas "
                    "Afrikaans العربية Беларуская বাংলা 中文 "
                    "Origem: Wikipédia, a enciclopédia livre. "
                    "Desculpe incomodar, mas nossa campanha vai acabar em breve. "
                    "É segunda-feira, pedimos que se junte aos 2 por cento de "
                    "leitores e leitoras que doam. "
                    "Os primeiros registros escritos conhecidos da história "
                    "da China pertencem à Dinastia Shang. "
                    "A civilização chinesa se desenvolveu inicialmente no "
                    "vale do rio Amarelo."
                ),
            },
        }),
        falar=lambda fala, *_args: falas.append(fala),
        enviar_mensagem=(
            lambda *_args, **_kwargs: "__LAYLAY_LLM_INDISPONIVEL__"
        ),
        # Reproduz o limpador real que pode remover os sublinhados antes da
        # barreira final da voz.
        limpar_resposta=lambda texto: str(texto).replace("_", ""),
        remover_prefixo_exec=lambda texto: texto,
        transcript_api=object(),
        registrar_contexto=registros.append,
        log=lambda *_args: None,
    ))

    assert resultado is True
    assert falas and "primeiros registros" in falas[-1].casefold()
    assert "alternar o índice" not in falas[-1].casefold()
    assert "98 idiomas" not in falas[-1].casefold()
    assert "africaans" not in falas[-1].casefold()
    assert "campanha" not in falas[-1].casefold()
    assert "2 por cento" not in falas[-1].casefold()
    assert "leitores e leitoras" not in falas[-1].casefold()
    assert "história da china”" in falas[-1].casefold()
    assert "laylayllm" not in falas[-1].casefold()
    assert registros[-1]["status"] == "concluido"
    assert registros[-1]["resumo"] == falas[-1]


def test_resumo_remove_bloco_completo_da_campanha_atual_da_wikipedia() -> None:
    falas: list[str] = []

    resultado = asyncio.run(resumir_pagina_ou_video(
        websocket_disponivel=lambda: True,
        solicitar_conteudo=lambda: asyncio.sleep(0, result={
            "success": True,
            "data": {
                "url": "https://pt.wikipedia.org/wiki/História_da_China",
                "title": "História da China - Wikipédia",
                "content": (
                    "É segunda-feira, pedimos que se junte aos 2 por cento de "
                    "leitores e leitoras que doam. Se todas as pessoas lendo "
                    "isto doassem R$ 15, atingiríamos nossa meta em poucas "
                    "horas. Doar R$ 15 Talvez depois 10 de agosto: A Wikipédia "
                    "não está à venda Desculpe, tentamos entrar em contato "
                    "antes, mas é segunda-feira, 10 de agosto, e precisamos de "
                    "ajuda. Os primeiros registros escritos conhecidos da "
                    "história da China pertencem à Dinastia Shang. A "
                    "civilização chinesa se desenvolveu inicialmente no vale "
                    "do rio Amarelo."
                ),
            },
        }),
        falar=lambda fala, *_args: falas.append(fala),
        enviar_mensagem=lambda *_args, **_kwargs: "LAYLAY_LLM_TIMEOUT",
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
        transcript_api=object(),
        log=lambda *_args: None,
    ))

    assert resultado is True
    fala = falas[-1].casefold()
    assert "primeiros registros" in fala
    assert "dinastia shang" in fala
    assert "rio amarelo" in fala
    for ruido in (
        "2 por cento",
        "r$ 15",
        "atingiríamos nossa meta",
        "talvez depois",
        "não está à venda",
        "precisamos de ajuda",
    ):
        assert ruido not in fala


def test_prompt_do_resumo_chega_limpo_e_tem_prioridade_interativa() -> None:
    chamadas: list[tuple[list[dict], dict]] = []
    falas: list[str] = []

    def enviar(mensagens, **kwargs):
        chamadas.append((mensagens, kwargs))
        return (
            "A história registrada da China começa na dinastia Shang e passa "
            "por sucessivas unificações políticas e transformações sociais."
        )

    resultado = asyncio.run(resumir_pagina_ou_video(
        websocket_disponivel=lambda: True,
        solicitar_conteudo=lambda: asyncio.sleep(0, result={
            "success": True,
            "data": {
                "url": "https://pt.wikipedia.org/wiki/História_da_China",
                "title": "História da China - Wikipédia",
                "content": (
                    "Alternar o índice História da China 98 idiomas Afrikaans "
                    "العربية Origem: Wikipédia, a enciclopédia livre. "
                    "Desculpe incomodar, mas nossa campanha vai acabar em breve. "
                    "É segunda-feira, pedimos que se junte aos 2 por cento de "
                    "leitores e leitoras que doam. Os primeiros registros "
                    "escritos conhecidos da história da China pertencem à "
                    "Dinastia Shang. A civilização chinesa surgiu no vale do "
                    "rio Amarelo."
                ),
            },
        }),
        falar=lambda fala, *_args: falas.append(fala),
        enviar_mensagem=enviar,
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
        transcript_api=object(),
        log=lambda *_args: None,
    ))

    assert resultado is True
    prompt = chamadas[0][0][0]["content"].casefold()
    opcoes = chamadas[0][1]
    assert "dinastia shang" in prompt
    assert "rio amarelo" in prompt
    assert "alternar o índice" not in prompt
    assert "98 idiomas" not in prompt
    assert "campanha" not in prompt
    assert "2 por cento" not in prompt
    assert opcoes["_prioridade_interativa"] is True
    assert opcoes["_permitir_durante_interacao"] is True
    assert falas == [
        "A história registrada da China começa na dinastia Shang e passa "
        "por sucessivas unificações políticas e transformações sociais."
    ]


def test_limpeza_preserva_artigo_legitimo_sobre_leitores_e_doacoes() -> None:
    artigo = (
        "Uma pesquisa com leitores mostrou que dois por cento fazem doações "
        "recorrentes. O estudo analisou hábitos de financiamento coletivo."
    )

    assert _limpar_texto_capturado(artigo) == artigo


def test_limpeza_da_campanha_nao_depende_de_data_valor_ou_espaco() -> None:
    capturado = (
        "Desculpe incomodar, nossa campanha vai acabar em breve. "
        "Se todas as pessoas lendo\u00a0isto doassem R$\u200b 27, "
        "atingiríamos nossa meta em poucas horas. Doar R$ 27 Talvez depois "
        "31 de dezembro: A Wikipédia não está à venda. "
        "A história documentada preserva fontes de diferentes períodos."
    )

    limpo = _limpar_texto_capturado(capturado)

    assert limpo == (
        "A história documentada preserva fontes de diferentes períodos."
    )


def test_correcao_de_capacidade_futura_fica_registrada() -> None:
    estado = registrar_mente_curta(
        {},
        texto_usuario="você ainda não tem essa habilidade, depois vou adicionar controle da luz",
        normalizar_texto_cb=lambda texto: texto.casefold(),
    )
    assert estado["capacidade_futura"]["status"] == "indisponivel"
    assert "luz" in estado["capacidade_futura"]["alvo"]

    ctx = {
        "mente_integrada_estado": estado,
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
    }
    fala = construir_fala_conversa(ctx, "", "mas você não tem ela ainda", "conversa", [])
    assert "ainda não" in fala.casefold()
    assert "indisponível" in fala.casefold()


def test_nome_pedro_complemento_nao_e_removido_com_preposicao() -> None:
    fala, _ = ajustar_uso_natural_nome(
        "Vou quebrar a monotonia no quarto do Pedro.",
        "calma",
        ultimo_uso_ts=time.time(),
    )
    assert fala == "Vou quebrar a monotonia no quarto do Pedro."


def test_resposta_neutra_nao_puxa_oferta_operacional_antiga() -> None:
    ctx = {"_normalizar_texto_curto": lambda texto: texto.casefold()}
    fala = construir_fala_conversa(
        ctx,
        'Legal! Vou poder te ajudar a acender a luz. Basta dar uma ordem simples.',
        "agora nada demais",
        "conversa",
        [],
    )
    assert "fico por aqui" in fala.casefold()
    assert "acender" not in fala.casefold()


def test_isso_depende_de_voce_continua_capacidade_registrada() -> None:
    ctx = {
        "mente_integrada_estado": {
            "capacidade_futura": {
                "alvo": "controlar a luz",
                "status": "indisponivel",
                "confirmada_disponivel": False,
            }
        },
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
    }
    fala = construir_fala_conversa(ctx, "", "isso depende de você", "conversa", [])
    assert "depende de você" in fala.casefold()
    assert "não vou agir" in fala.casefold()


def test_receita_em_markdown_vira_prosa_natural_na_voz() -> None:
    texto = """Claro! Vou passar uma receita básica.
### Massa de Coxinha
**Ingredientes:**
- **Farinha de Trigo**: 200g (1 xícara)
- **Ovos**: 3
- **Caldo de Carne**: 80ml ou água com um pouco de sal
- **Sal**: 1/2 colher de chá
### Preparo da Massa
1. **Preparar a massa:**
- Bata os ovos em um recipiente.
"""
    fala = limpar_para_voz(texto)
    assert "###" not in fala
    assert "**" not in fala
    assert "- Farinha" not in fala
    assert "Você vai precisar de 200 gramas de farinha de trigo, ou uma xícara." in fala
    assert "Também vai precisar de 3 ovos." in fala
    assert "80 mililitros de caldo de carne, ou água com um pouco de sal" in fala
    assert "meia colher de chá de sal" in fala
    assert "Primeiro, preparar a massa." in fala


def test_tutorial_numerado_ganha_conectores_orais() -> None:
    texto = """### Etapas
1. Abra o programa.
2. Escolha o arquivo.
3. Confirme a operação.
"""
    fala = naturalizar_texto_para_fala(texto)
    assert "Primeiro, abra o programa." in fala
    assert "Depois, escolha o arquivo." in fala
    assert "Em seguida, confirme a operação." in fala


def test_prosa_comum_permanece_natural_sem_reescrita_desnecessaria() -> None:
    texto = "A página conta a história da coxinha e explica como ela ficou popular."
    assert limpar_para_voz(texto) == texto


def test_metricas_compactas_viram_fala_natural() -> None:
    fala = limpar_para_voz(
        "Ensolarado, 17 graus Celsius, umidade:52% e vento:10 km/h; sistema normal."
    )
    assert "umidade em 52 por cento" in fala
    assert "vento de 10 quilômetros por hora" in fala
    assert "quilômetros/h" not in fala
    assert ";" not in fala


def test_inicio_do_programa_nao_envia_conversa_anterior_para_abertura() -> None:
    chamadas = []
    runtime = AberturaChatRuntime(
        estado_getter=lambda: {
            "messages": [
                {"role": "system", "content": "prompt"},
                {"role": "user", "content": "quais as medidas da massa?"},
                {"role": "assistant", "content": "Você vai precisar de farinha e ovos."},
            ],
            "current_emotion": "calma",
            "emotion_level": 1,
        },
        enviar_mensagem=lambda mensagens, **_kwargs: chamadas.append(mensagens) or "Olá, Pedro. Começamos uma conversa nova.",
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
    )
    fala = runtime.gerar("inicio")
    conteudo_prompt = " ".join(str(item.get("content") or "") for item in chamadas[0])
    assert "medidas da massa" not in conteudo_prompt
    assert "farinha e ovos" not in conteudo_prompt
    assert fala.startswith("Olá")


def test_abertura_local_nao_disputa_o_modelo_com_primeira_entrada() -> None:
    chamadas = []
    runtime = AberturaChatRuntime(
        estado_getter=lambda: {},
        enviar_mensagem=lambda *_args, **_kwargs: chamadas.append(True) or "Oi",
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
    )

    assert runtime.gerar_local("inicio")
    assert chamadas == []


def test_abertura_rejeita_continuacao_de_tarefa_antiga() -> None:
    runtime = AberturaChatRuntime(
        estado_getter=lambda: {"messages": [], "current_emotion": "calma", "emotion_level": 1},
        enviar_mensagem=lambda *_args, **_kwargs: "Olá! Vou te passar as medidas da massa de coxinha.",
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
    )
    fala = runtime.gerar("inicio").casefold()
    assert "coxinha" not in fala
    assert "medidas" not in fala


def test_nova_sessao_limpa_contexto_curto_mas_preserva_fatos() -> None:
    mental, conversa, mensagens = renovar_contexto_sessao(
        {
            "memoria_fato_importante": "Pedro estuda no SENAI",
            "ultima_resposta": "Receita da coxinha",
            "ultimo_resumo_pagina": {"referente": "Coxinha", "ts": time.time()},
            "pendencia_atual": {"status": "ativa"},
            "capacidade_futura": {"alvo": "luz", "ts": time.time()},
        },
        {
            "current_emotion": "alegre",
            "ultimo_topico_conversa": "coxinha",
            "topicos_conversa_recente": ["coxinha"],
        },
        [
            {"role": "system", "content": "prompt atual"},
            {"role": "user", "content": "qual a receita dela?"},
            {"role": "assistant", "content": "Use farinha."},
        ],
        motivo="inicio_programa",
        ativa=True,
    )
    assert mental["memoria_fato_importante"] == "Pedro estuda no SENAI"
    assert not mental["ultimo_resumo_pagina"]
    assert not mental["pendencia_atual"]
    assert not mental["capacidade_futura"]
    assert conversa["ultimo_topico_conversa"] == ""
    assert conversa["current_emotion"] == "calma"
    assert mensagens == [{"role": "system", "content": "prompt atual"}]


def test_despedidas_explicitas_encerram_conversa_sem_falso_positivo() -> None:
    assert texto_encerra_conversa("obrigado, era só isso")
    assert texto_encerra_conversa("por hoje é só")
    assert texto_encerra_conversa("até mais, Lay")
    assert not texto_encerra_conversa("é só colocar mais farinha")
    assert not texto_encerra_conversa("obrigado pela receita, e qual a temperatura?")


def test_agradecimento_por_receita_responde_ao_motivo_da_ajuda() -> None:
    emocoes = []
    ctx = {
        "mente_integrada_estado": {
            "ultima_resposta": "As medidas da receita são 2 xícaras de farinha, 500 mililitros de caldo e 300 gramas de frango.",
            "ultima_habilidade": "conversa",
        },
        "_definir_emocao": lambda emocao, nivel, motivo: emocoes.append((emocao, nivel, motivo)),
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
    }
    fala = responder_agradecimento_ou_elogio(ctx, "obrigado lay")
    assert tipo_reconhecimento_afetivo("obrigado lay") == "agradecimento"
    assert any(p in fala.casefold() for p in ("receita", "medidas", "quantidades"))
    assert "isso foi fofo" not in fala.casefold()
    assert emocoes == [("envergonhada", 1, "agradeceu pela ajuda")]


def test_elogio_pessoal_tem_vergonha_mais_marcada() -> None:
    emocoes = []
    ctx = {
        "mente_integrada_estado": {},
        "_definir_emocao": lambda emocao, nivel, motivo: emocoes.append((emocao, nivel, motivo)),
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
    }
    fala = responder_agradecimento_ou_elogio(ctx, "você é incrível, Lay")
    assert tipo_reconhecimento_afetivo("você é incrível, Lay") == "elogio_pessoal"
    assert any(p in fala.casefold() for p in ("obrigada", "elogio", "gostei"))
    assert emocoes == [("envergonhada", 2, "recebeu elogio")]


def test_reacoes_a_agradecimento_nao_repetem_a_mesma_fala_em_sequencia() -> None:
    ctx = {
        "mente_integrada_estado": {"ultima_resposta": "O resumo da página ficou pronto."},
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
    }
    falas = [responder_agradecimento_ou_elogio(ctx, "valeu lay") for _ in range(3)]
    assert len(set(falas)) == 3
