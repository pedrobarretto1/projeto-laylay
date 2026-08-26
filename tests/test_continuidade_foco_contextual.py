import time

from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_comentario_resultado_operacional,
)
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.continuidade_conversa import (
    detectar_comentario_resultado_operacional,
    extrair_topico_conversa,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.musica_conversacional import (
    texto_pede_direcao_musical_generica,
)
from mente_laylay.personalidade.resposta_conversacional_runtime import (
    RespostaConversacionalRuntime,
)


def _normalizar(texto: str) -> str:
    return str(texto or "").strip().casefold()


def _mente_cor_recente():
    return {
        "ultima_acao_intent": "IOT_CONTROL",
        "ultima_acao_alvo": "lâmpada do quarto",
        "ultima_acao_params": {
            "acao": "ajustar_cor",
            "alvo": "lampada_quarto",
            "cor": "vermelho vinho",
        },
        "ultima_acao_ts": time.time(),
    }


def test_comentario_de_cor_prioriza_resultado_operacional_recente():
    comentario = detectar_comentario_resultado_operacional(
        "parece mais um rosa isso aí",
        _mente_cor_recente(),
    )
    assert comentario is not None
    assert comentario["tipo"] == "aparencia_cor"
    assert comentario["cor_percebida"] == "rosa"
    assert comentario["cor_pedida"] == "vermelho vinho"


def test_pedido_explicito_nao_vira_comentario_sobre_resultado():
    assert detectar_comentario_resultado_operacional(
        "deixa a luz rosa",
        _mente_cor_recente(),
    ) is None


def test_pre_fluxo_responde_comentario_e_suspende_assunto_antigo():
    falas = []
    suspensoes = []
    contexto = {
        "mente_integrada_estado": _mente_cor_recente(),
        "_suspender_topico_conversacional": suspensoes.append,
        "_emitir_resposta_curta": lambda texto, fala, **kwargs: falas.append(fala) or True,
    }
    tratado, etapa = processar_comentario_resultado_operacional(
        contexto,
        "parece mais um rosa isso aí",
    )
    assert tratado is True
    assert etapa == "comentario_resultado_operacional"
    assert suspensoes == ["comentario_resultado_operacional"]
    assert "rosa" in falas[0]
    assert "vermelho vinho" in falas[0]


def test_troca_de_praia_para_inteligencia_artificial_fecha_foco_anterior():
    estado = EstadoCompartilhadoRuntime(
        mental={
            "foco_conversacional_topico": "praia",
            "pendencia_atual": {"status": "ativa", "dominio": "arquivos"},
        },
        conversacional={
            "ultimo_topico_conversa": "praia",
            "ultimo_topico_ts": time.time(),
            "topicos_conversa_recente": ["praia"],
        },
    )
    runtime = RespostaConversacionalRuntime(
        namespace_getter=lambda: {"_normalizar_texto_curto": _normalizar},
        estado_runtime_getter=lambda: estado,
        fallback_fala="fallback",
    )
    runtime.atualizar_memoria_topicos("me explica o que é inteligência artificial")
    assert estado.conversacional["ultimo_topico_conversa"] == "inteligência artificial"
    assert estado.mental["foco_conversacional_topico"] == ""
    assert estado.mental["pendencia_atual"]["dominio"] == "arquivos"
    assert estado.mental["assuntos_encerrados"][-1]["topico"] == "praia"


def test_extracao_nao_reduz_inteligencia_artificial_para_ia():
    assert extrair_topico_conversa(
        "me explica inteligência artificial",
        "praia",
        normalizar_texto_curto=_normalizar,
    ) == "inteligência artificial"


def test_verificador_nao_substitui_repeticao_por_fala_local():
    anterior = "E você, Pedro? O que você vê quando olha para dentro do espelho?"
    resultado = verificar_fala_turno(
        anterior,
        plano={"texto_usuario": "acho que eu vejo um cara normal", "dominio": "conversa"},
        ultima_resposta=anterior,
    )
    assert "repeticao_exata" not in resultado["problemas"]
    assert resultado["fala"] == anterior


def test_verificador_nao_reescreve_repeticao_semantica_da_llm():
    resultado = verificar_fala_turno(
        "A praia é tranquila e bonita, com ondas calmas e um céu muito azul.",
        plano={"texto_usuario": "agora quero falar de inteligência artificial", "dominio": "conversa"},
        ultima_resposta="A praia é muito tranquila e bonita, com ondas calmas sob um céu azul.",
    )
    assert "repeticao_semantica" not in resultado["problemas"]
    assert "praia" in resultado["fala"].casefold()


def test_que_tal_uma_musica_de_praia_e_recomendacao_nao_geracao_de_letra():
    assert texto_pede_direcao_musical_generica(
        "que tal uma música de praia",
        estado_mental={},
        normalizar_texto=_normalizar,
    ) is True
