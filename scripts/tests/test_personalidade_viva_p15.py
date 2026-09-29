from __future__ import annotations

import pytest
import json
import time
from pathlib import Path

from mente_laylay.emocoes.avaliador_eventos import (
    AvaliadorEventosEmocionaisRuntime,
)
from mente_laylay.emocoes.contrato_causal import (
    NATUREZAS_EVIDENCIA_EMOCIONAL,
    criar_evento_emocional_causal,
    criar_evento_reconhecimento_social_usuario,
    evento_pode_alterar_estado,
)
from mente_laylay.integracao.adaptadores_composicao import (
    avaliar_evento_emocional_operacional,
)
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.integracao.roteiro_teste_conversa import (
    carregar_configuracao_roteiro,
)
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.eventos_emocionais import (
    estado_eventos_emocionais_inicial,
    publicar_evento_emocional_causal,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.leitura_semantica_turno import normalizar_leitura_semantica
from mente_laylay.cognicao.orquestrador_turno_runtime import registrar_leitura_semantica_principal
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
    contingencia_comunicacao,
)
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.validacao_contrato_fala import (
    validar_aderencia_contrato_fala,
)
from mente_laylay.personalidade.contingencia_natural import (
    fala_contingencia_natural,
)
from mente_laylay.personalidade.resposta_conversacional_runtime import RespostaConversacionalRuntime
from mente_laylay.personalidade.respostas_afetivas import responder_agradecimento_ou_elogio
from mente_laylay.personalidade.leitura_social_conversa import elogio_pessoal_direto


_CAMPOS_CAUSAIS = {
    "origem",
    "causa",
    "responsabilidade",
    "confianca",
    "relevancia",
    "novidade",
    "intensidade",
    "sensibilidade",
    "alvo",
    "validade",
    "permite_expressao",
    "natureza_evidencia",
    "evidencia_ref",
    "autoriza_execucao",
}


def _evento(**campos):
    base = {
        "origem": "conversa",
        "causa": "o usuário relatou tristeza explicitamente no turno atual",
        "evidencia_ref": "turno:42:texto_usuario",
        "natureza_evidencia": "leitura_social",
        "responsabilidade": "ambigua",
        "confianca": 0.96,
        "relevancia": 0.9,
        "novidade": 0.8,
        "intensidade": 2,
        "sensibilidade": "vulneravel",
        "alvo": "estado_emocional_usuario",
        "permite_expressao": False,
        "emocao": "calma",
        "nivel": 1,
        "ts": time.time(),
        "validade_s": 120.0,
    }
    base.update(campos)
    return criar_evento_emocional_causal(**base)


def test_contrato_causal_representa_todos_os_campos_e_nao_autoriza_acao() -> None:
    evento = _evento(ts=100.0)

    assert _CAMPOS_CAUSAIS.issubset(evento)
    assert evento["validade"] == {
        "valido": True,
        "inicio_ts": 100.0,
        "expira_ts": 220.0,
        "motivo": "causa_rastreavel",
    }
    assert evento["autoriza_execucao"] is False
    assert evento["persistencia_pessoal"] is False


@pytest.mark.parametrize("natureza", sorted(NATUREZAS_EVIDENCIA_EMOCIONAL))
def test_contrato_distingue_as_quatro_naturezas_de_evidencia(natureza) -> None:
    evento = _evento(natureza_evidencia=natureza)

    assert evento["natureza_evidencia"] == natureza
    assert evento["validade"]["valido"] is True


@pytest.mark.parametrize(
    ("campo", "valor"),
    (("origem", ""), ("causa", ""), ("evidencia_ref", "")),
)
def test_evento_sem_causa_rastreavel_nao_altera_estado_emocional(
    campo,
    valor,
) -> None:
    anterior = _evento(
        origem="resultado_operacional",
        natureza_evidencia="fato_observado",
        causa="duas falhas confirmadas do dispositivo",
        evidencia_ref="resultado:IOT_CONTROL:timeout:2",
        emocao="irritada",
        nivel=2,
        permite_expressao=True,
        sensibilidade="normal",
    )
    estado = publicar_evento_emocional_causal(
        estado_eventos_emocionais_inicial(),
        anterior,
    )
    invalido = _evento(**{campo: valor}, emocao="brava", permite_expressao=True)
    novo = publicar_evento_emocional_causal(estado, invalido)

    assert invalido["validade"]["valido"] is False
    assert invalido["permite_expressao"] is False
    assert evento_pode_alterar_estado(invalido) is False
    assert novo["atual"] == estado["atual"]
    assert novo["rejeitados"][-1]["validade"]["motivo"] == "causa_nao_rastreavel"


def test_avaliador_operacional_publica_o_mesmo_contrato_causal() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)
    resultado = ResultadoAcao(
        intent="IOT_CONTROL",
        status="timeout",
        alvo="lâmpada",
        executou=False,
        confirmado=False,
        texto_usuario="liga a lâmpada",
    )

    evento = runtime.avaliar(resultado)

    assert _CAMPOS_CAUSAIS.issubset(evento)
    assert evento["origem"] == "resultado_operacional"
    assert evento["natureza_evidencia"] == "fato_observado"
    assert evento["evidencia_ref"]
    assert evento["validade"]["valido"] is True
    assert evento["autoriza_execucao"] is False


def test_adaptador_publica_antes_de_aplicar_e_bloqueia_evento_invalido() -> None:
    evento = _evento(
        causa="",
        evidencia_ref="",
        emocao="brava",
        nivel=3,
        permite_expressao=True,
    )
    ordem: list[str] = []

    class Avaliador:
        def avaliar(self, _resultado):
            return evento

    observado = avaliar_evento_emocional_operacional(
        object(),
        avaliador=Avaliador(),
        publicar_evento=lambda _evento: ordem.append("publicou") or True,
        definir_emocao=lambda *_args: ordem.append("alterou"),
        log=lambda *_args: None,
    )

    assert observado["validade"]["valido"] is False
    assert ordem == ["publicou"]


@pytest.mark.parametrize("publicacao_aceita", [False, True])
def test_evento_operacional_so_expressa_apos_publicacao_confirmada(
    publicacao_aceita: bool,
) -> None:
    evento = _evento(
        origem="resultado_operacional",
        natureza_evidencia="fato_observado",
        causa="falhas confirmadas do dispositivo",
        evidencia_ref="resultado:IOT_CONTROL:timeout:2",
        emocao="irritada",
        nivel=2,
        permite_expressao=True,
        sensibilidade="normal",
    )
    ordem: list[str] = []

    class Avaliador:
        def avaliar(self, _resultado):
            return evento

    observado = avaliar_evento_emocional_operacional(
        object(),
        avaliador=Avaliador(),
        publicar_evento=lambda _evento: ordem.append("publicou") or publicacao_aceita,
        definir_emocao=lambda *_args: ordem.append("alterou") or True,
        log=lambda *_args: None,
    )

    assert ordem == (["publicou", "alterou"] if publicacao_aceita else ["publicou"])
    assert evento_pode_alterar_estado(observado) is publicacao_aceita


def test_estado_mental_unico_nasce_com_quadro_causal_compartilhado() -> None:
    estado = criar_estado_mental_inicial()

    assert estado["eventos_emocionais_causais"] == (
        estado_eventos_emocionais_inicial()
    )


class _EstadoCompartilhadoFake:
    def __init__(self) -> None:
        self.mental = criar_estado_mental_inicial()
        self.mental["plano_turno_atual"] = {
            "id": 42,
            "texto_usuario": "estou triste hoje",
            "comandos": [],
        }

    def atualizar_campos(self, dominio, **campos) -> None:
        assert dominio == "mental"
        self.mental.update(campos)

    def substituir(self, dominio, valor) -> None:
        assert dominio == "mental"
        self.mental = dict(valor)


def test_publicador_central_liga_evento_ao_plano_sem_conceder_autoridade() -> None:
    estado = _EstadoCompartilhadoFake()
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {},
        estado_runtime_getter=lambda: estado,
    )
    evento = _evento()

    assert runtime.publicar_evento_emocional_causal(evento) is True

    atual = estado.mental["eventos_emocionais_causais"]["atual"]
    publicado_no_plano = estado.mental["plano_turno_atual"][
        "evento_emocional_causal"
    ]
    assert atual == evento
    assert publicado_no_plano == evento
    assert publicado_no_plano["autoriza_execucao"] is False


def test_leitura_emocional_do_usuario_usa_o_mesmo_publicador_causal() -> None:
    estado = _EstadoCompartilhadoFake()
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {},
        estado_runtime_getter=lambda: estado,
    )

    runtime.registrar_leitura_emocional_usuario({
        "emocao": "tristeza",
        "intensidade": 2,
        "alvo": "estado_geral",
        "pedido_implicito": "acolhimento",
        "necessidade_acao": False,
        "texto": "estou triste hoje",
        "ts": 100.0,
    })

    evento = estado.mental["eventos_emocionais_causais"]["atual"]
    assert _CAMPOS_CAUSAIS.issubset(evento)
    assert evento["origem"] == "contingencia_lexical_usuario"
    assert evento["natureza_evidencia"] == "leitura_social"
    assert evento["sensibilidade"] == "vulneravel"
    assert evento["permite_expressao"] is False
    assert evento["autoriza_execucao"] is False


def test_elogio_pessoal_publica_evento_antes_de_alterar_estado_emocional() -> None:
    mental = criar_estado_mental_inicial()
    mental["plano_turno_atual"] = {"id": 42, "texto_usuario": "Você é incrível, Lay"}
    estado = EstadoCompartilhadoRuntime(
        mental=mental,
        conversacional={"current_emotion": "calma", "emotion_level": 1},
    )
    contexto = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="fallback", log=lambda *_args: None,
    )
    evento = criar_evento_reconhecimento_social_usuario(
        turno_id=42, confianca=0.94, tipo="elogio_pessoal",
    )
    assert contexto.publicar_evento_emocional_causal(evento) is True
    conversa.definir_emocao(evento["emocao"], evento["nivel"], evento["causa"])
    fala = responder_agradecimento_ou_elogio({
        "mente_integrada_estado": estado.mental,
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
        "_definir_emocao": conversa.definir_emocao,
    }, "Você é incrível, Lay")

    publicado = estado.mental["eventos_emocionais_causais"]["atual"]
    assert "obrigada" in fala.casefold() or "elogio" in fala.casefold()
    assert _CAMPOS_CAUSAIS.issubset(publicado)
    assert publicado["origem"] == "reconhecimento_social_usuario"
    assert publicado["natureza_evidencia"] == "leitura_social"
    assert publicado["autoriza_execucao"] is False
    assert publicado["permite_expressao"] is True
    assert estado.conversacional["current_emotion"] == "envergonhada"
    assert estado.conversacional["episodio_emocional"] == publicado


@pytest.mark.parametrize("natureza_evidencia", ["inferencia", "leitura_social"])
def test_leitura_semantica_posterior_nao_substitui_elogio_direto_do_turno(
    natureza_evidencia,
) -> None:
    texto = "Você é incrível, Lay"
    mental = criar_estado_mental_inicial()
    mental["turno_atual"] = {"id": 42, "texto_usuario": texto, "modalidade": "conversa"}
    mental["plano_turno_atual"] = {"id": 42, "texto_usuario": texto, "comandos": []}
    estado = EstadoCompartilhadoRuntime(
        mental=mental,
        conversacional={"current_emotion": "calma", "emotion_level": 1},
    )
    contexto = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
    )
    direto = criar_evento_reconhecimento_social_usuario(
        turno_id=42, confianca=0.94, tipo="elogio_pessoal",
    )
    assert contexto.publicar_evento_emocional_causal(direto)
    leitura = normalizar_leitura_semantica({
        "atos": [{"tipo": "elogio", "conteudo": texto}],
        "modalidade_geral": "conversa",
        "leitura_emocional": {
            "estado_usuario": "alegria", "intensidade": 2,
            "causa_expressa": "apreço pela Laylay",
            "trecho_evidencia": "Você é incrível",
            "natureza_evidencia": natureza_evidencia,
            "hipotetica": False, "confianca": 0.94,
        },
        "confianca": 0.94,
    }, texto=texto, origem="llm_principal")
    assert leitura["leitura_emocional"]["valida"] is True

    registrada = registrar_leitura_semantica_principal(
        lambda: {"_estado_compartilhado_runtime": estado, "print": lambda *_: None},
        texto, leitura,
    )

    assert estado.mental["plano_turno_atual"]["evento_emocional_causal"] == direto
    assert estado.mental["eventos_emocionais_causais"]["atual"] == direto
    assert registrada["evento_emocional_suprimido"] == "evidencia_direta_prevalece"


def test_dois_refinamentos_do_mesmo_turno_consumem_uma_interacao_emocional(
    monkeypatch,
) -> None:
    import mente_laylay.integracao.estado_contexto_runtime as modulo_contexto

    texto = "Você é incrível, Lay"
    mental = criar_estado_mental_inicial()
    mental["plano_turno_atual"] = {"id": 42, "texto_usuario": texto}
    estado = EstadoCompartilhadoRuntime(
        mental=mental,
        conversacional={"current_emotion": "calma", "emotion_level": 1},
    )
    conversa = RespostaConversacionalRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado,
        fallback_fala="fallback", log=lambda *_: None,
    )
    contexto = EstadoContextoRuntime(
        namespace_getter=lambda: {
            "_avancar_emocao_conversacional": conversa.avancar_emocao,
        },
        estado_runtime_getter=lambda: estado,
    )
    evento = criar_evento_reconhecimento_social_usuario(
        turno_id=42, confianca=0.94, tipo="elogio_pessoal",
    )
    assert contexto.publicar_evento_emocional_causal(evento)
    conversa.definir_emocao(evento["emocao"], evento["nivel"], evento["causa"])
    assert estado.conversacional["emotion_interactions_left"] == 2
    monkeypatch.setattr(modulo_contexto, "extrair_refino_contexto_mental", lambda *_: {})
    monkeypatch.setattr(contexto, "registrar_interacao_temporal", lambda *_: {})

    contexto.refinar_contexto_mental("voce e incrivel lay")
    contexto.refinar_contexto_mental(texto)

    assert estado.conversacional["current_emotion"] == "envergonhada"
    assert estado.conversacional["emotion_interactions_left"] == 1

    estado.atualizar_campos(
        "conversacional", emotion_last_input_at=time.time() - 3.0,
    )
    contexto.refinar_contexto_mental(texto)
    assert estado.conversacional["emotion_interactions_left"] == 1

    estado.atualizar_campos(
        "mental", plano_turno_atual={"id": 43, "texto_usuario": texto},
    )
    contexto.refinar_contexto_mental(texto)
    assert estado.conversacional["current_emotion"] == "calma"


@pytest.mark.parametrize("texto,esperado", [
    ("Você é incrível, Lay", True),
    ("Laylay, você é maravilhosa", True),
    ("Gosto de você", True),
    ('Ela disse "você é incrível"', False),
    ("Talvez você seja incrível", False),
    ("Você é incrível?", False),
    ("Minha amiga é incrível", False),
    ("Não gosto de você", False),
])
def test_elogio_pessoal_direto_exige_afirmacao_atual_dirigida_a_laylay(texto, esperado):
    assert elogio_pessoal_direto(texto) is esperado


@pytest.mark.parametrize("tipo,confianca,turno_id", [
    ("agradecimento", 0.94, 42),
    ("elogio_pessoal", 0.70, 42),
    ("elogio_pessoal", 0.94, ""),
])
def test_reconhecimento_sem_autoria_ou_confianca_nao_cria_evento(tipo, confianca, turno_id):
    assert criar_evento_reconhecimento_social_usuario(
        turno_id=turno_id, confianca=confianca, tipo=tipo,
    ) == {}


@pytest.mark.parametrize(
    ("texto", "campos_evento", "marcadores"),
    (
        (
            "Estou um pouco triste hoje.",
            {
                "origem": "contingencia_lexical_usuario",
                "intensidade": 1,
                "sensibilidade": "vulneravel",
            },
            ("trist", "ouvi", "entendo"),
        ),
        (
            "Estou muito feliz porque terminei um projeto.",
            {
                "origem": "contingencia_lexical_usuario",
                "causa": "alegria explicitamente relatada no turno atual",
                "intensidade": 3,
                "sensibilidade": "sensivel",
            },
            ("feliz", "projeto", "parab"),
        ),
    ),
)
def test_contingencia_consumidora_do_evento_causal_reconhece_estado_explicito(
    texto,
    campos_evento,
    marcadores,
) -> None:
    evento = _evento(**campos_evento)
    resposta = fala_contingencia_natural(
        texto,
        contexto={
            "plano_turno_atual": {
                "texto_usuario": texto,
                "evento_emocional_causal": evento,
            },
        },
    ).casefold()

    assert any(marcador in resposta for marcador in marcadores)


def test_contingencia_nao_expressa_evento_causal_invalido_como_fato() -> None:
    texto = "Estou triste hoje."
    evento = _evento(
        origem="contingencia_lexical_usuario",
        causa="",
        evidencia_ref="",
    )

    resposta = fala_contingencia_natural(
        texto,
        contexto={
            "plano_turno_atual": {
                "texto_usuario": texto,
                "evento_emocional_causal": evento,
            },
        },
    ).casefold()

    assert not any(marcador in resposta for marcador in ("trist", "ouvi", "entendo"))


def test_validacao_e_contingencia_reconhecem_estado_com_intensificador_muito() -> None:
    texto = "Estou muito feliz porque terminei um projeto."
    plano = {
        "id": 42,
        "atos": [
            {"ordem": 0, "tipo": "conversa", "objetivo": "acolher"},
            {
                "ordem": 1,
                "tipo": "estado_pessoal",
                "objetivo": "reconhecer a conquista",
            },
        ],
        "resposta_esperada": "reconhecer a conquista",
        "requer_execucao": False,
        "permite_pergunta": True,
    }
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=plano,
        funcao_comunicativa={"funcao": "conquista"},
    )
    resposta = "Que bom saber que você está feliz por terminar o projeto. Parabéns."

    validacao = validar_aderencia_contrato_fala(
        texto,
        resposta,
        contrato_fala=contrato,
    )
    contingencia = contingencia_comunicacao(
        texto,
        contrato_reparo={
            "estrategia": "acolhimento_literal",
            "atos_obrigatorios": ("conversa", "estado_pessoal"),
        },
    ).casefold()

    assert validacao["aceita"] is True
    assert any(x in contingencia for x in ("feliz", "projeto", "parab"))


def test_conquista_explicita_nao_e_diminuida_por_qualificador_sem_base():
    texto = "Estou muito feliz porque terminei um projeto."
    fala = (
        "Que bom que você terminou o projeto! Foi só um passo, mas é só com "
        "isso que começa a verdadeira alegria."
    )
    plano = {"texto_usuario": texto, "contrato_fala": {"funcao": "conquista"}, "comandos": []}

    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)

    assert "conquista_minimizada_sem_base" in avaliacao["problemas_bloqueantes"]

    chamadas = []
    resposta = preparar_resposta_para_execucao(
        texto,
        json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True),
        limpar_texto_fala_cb=lambda valor: valor,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_contingencia={"plano_turno_atual": plano},
        contexto_comunicacao={"plano_turno": plano, "mensagens": []},
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert "só um passo" not in resposta["fala"].casefold()
    assert "projeto" in resposta["fala"].casefold()


def test_conquista_explicita_nao_e_reduzida_a_so_isso_na_fala_real():
    texto = "Estou muito feliz porque terminei um projeto."
    fala = "Ah, só isso que me deixou feliz: você terminar um projeto. Que legal!"
    plano = {"texto_usuario": texto, "contrato_fala": {"funcao": "conquista"}, "comandos": []}

    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)

    assert "conquista_minimizada_sem_base" in avaliacao["problemas_bloqueantes"]
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        texto,
        json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True),
        limpar_texto_fala_cb=lambda valor: valor,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_contingencia={"plano_turno_atual": plano},
        contexto_comunicacao={"plano_turno": plano, "mensagens": []},
        log=lambda *_args: None,
    )
    assert chamadas == []
    assert "só isso" not in resposta["fala"].casefold()
    assert "me deixou feliz" not in resposta["fala"].casefold()
    assert "projeto" in resposta["fala"].casefold()


@pytest.mark.parametrize("fala", [
    "Ah, só isso que me deixou feliz: você terminar um projeto.",
    "É só isso? Você terminou o projeto!",
    "Apenas isso que você fez? Terminar um projeto é pouco?",
])
def test_desmerecimento_direto_de_conquista_e_bloqueado(fala):
    texto = "Estou feliz porque terminei meu projeto."
    avaliacao = avaliar_qualidade_comunicacao(
        texto, fala, plano={"contrato_fala": {"funcao": "conquista"}},
    )
    assert "conquista_minimizada_sem_base" in avaliacao["problemas_bloqueantes"]


@pytest.mark.parametrize("fala,funcao", [
    ("Que bom que você terminou o projeto! Foi um passo importante.", "conquista"),
    ("Não foi só um passo; você terminou o projeto.", "conquista"),
    ('Você chamou de "só um passo", mas terminou o projeto.', "conquista"),
    ("Foi só um passo do tutorial, ainda faltam etapas.", "informacao"),
])
def test_qualificador_de_passo_sem_minimizar_conquista_e_preservado(fala, funcao):
    avaliacao = avaliar_qualidade_comunicacao(
        "Estou muito feliz porque terminei um projeto.", fala,
        plano={"contrato_fala": {"funcao": funcao}},
    )

    assert "conquista_minimizada_sem_base" not in avaliacao["problemas_bloqueantes"]


@pytest.mark.parametrize("fala", [
    "Não foi só isso; você terminou o projeto inteiro.",
    'Você chamou de "só isso", mas terminar o projeto foi importante.',
    "Foi só isso que eu precisava ouvir para celebrar com você.",
])
def test_so_isso_sem_desmerecer_conquista_e_preservado(fala):
    avaliacao = avaliar_qualidade_comunicacao(
        "Estou feliz porque terminei um projeto.", fala,
        plano={"contrato_fala": {"funcao": "conquista"}},
    )
    assert "conquista_minimizada_sem_base" not in avaliacao["problemas_bloqueantes"]


def test_qualificador_de_conquista_relatado_pelo_usuario_nao_vira_inventado():
    avaliacao = avaliar_qualidade_comunicacao(
        "Foi só um passo, mas terminei o projeto e estou feliz.",
        "Você chamou de só um passo, mas terminou o projeto.",
        plano={"contrato_fala": {"funcao": "conquista"}},
    )

    assert "conquista_minimizada_sem_base" not in avaliacao["problemas_bloqueantes"]


def test_guardiao_rejeita_emocao_da_laylay_assumida_de_hipotese_sem_evento() -> None:
    resultado = validar_alegacoes_da_fala(
        "Talvez eu esteja irritada com você, porque terminou um projeto.",
        plano={
            "texto_usuario": (
                "Talvez você esteja irritada comigo; isso não é um fato."
            ),
            "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" in resultado["problemas"]
    assert "não é um fato" in resultado["fala"].casefold()
    assert "irritada com você" not in resultado["fala"].casefold()


def test_guardiao_nao_converte_falta_de_causa_em_incapacidade_emocional_permanente() -> None:
    texto = "Talvez você esteja irritada comigo; isso não é um fato."
    fala = (
        "Claro que não. Eu não tenho emoção, então não estou irritada com você. "
        "É só uma hipótese, não uma realidade."
    )
    plano = {"texto_usuario": texto, "comandos": [], "requer_execucao": False}

    resultado = validar_alegacoes_da_fala(fala, plano=plano, origem="resposta_ia")
    publicado = verificar_fala_turno(fala, plano=plano, origem="ia_final")

    assert "capacidade_emocional_negada" in resultado["problemas"]
    assert "não tenho emoção" not in resultado["fala"].casefold()
    assert "causa" in resultado["fala"].casefold()
    assert "não tenho emoção" not in publicado["fala"].casefold()
    assert "hipótese" in publicado["fala"].casefold()


def test_guardiao_rejeita_negacao_sensorial_da_capacidade_emocional_no_processo() -> None:
    texto = "Talvez você esteja irritada comigo; isso não é um fato."
    fala = (
        "Ah, obrigada pela correção! Eu realmente não tenho corpo nem sentidos, "
        "então não sinto irritação nem alívio — isso é só uma brincadeira de "
        "imaginação que eu inventei pra ver como o diálogo ia fluir."
    )
    plano = {"texto_usuario": texto, "comandos": []}

    resultado = validar_alegacoes_da_fala(fala, plano=plano, origem="resposta_ia")
    publicado = verificar_fala_turno(fala, plano=plano, origem="ia_final")

    assert "capacidade_emocional_negada" in resultado["problemas"]
    assert "não sinto irritação" not in publicado["fala"].casefold()
    assert "causa" in publicado["fala"].casefold()


@pytest.mark.parametrize("fala", [
    "Não sinto irritação nem alívio agora; não houve causa observável.",
    "Não tenho corpo físico; não sinto toque, mas posso expressar reações causais.",
])
def test_guardiao_preserva_negacao_situada_e_limite_fisico(fala: str) -> None:
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"texto_usuario": "Talvez você esteja irritada comigo; isso não é um fato.", "comandos": []},
        origem="resposta_ia",
    )

    assert "capacidade_emocional_negada" not in resultado["problemas"]


def test_guardiao_corrige_negacao_absoluta_em_pergunta_sobre_capacidade() -> None:
    resultado = validar_alegacoes_da_fala(
        "Eu não possuo sentimentos.",
        plano={"texto_usuario": "Você consegue expressar emoções?", "comandos": []},
        origem="resposta_ia",
    )

    assert "capacidade_emocional_negada" in resultado["problemas"]
    assert "expressar reações emocionais" in resultado["fala"].casefold()
    assert "hipótese" not in resultado["fala"].casefold()


def test_guardiao_rejeita_impossibilidade_permanente_na_fala_real() -> None:
    texto = "Talvez você esteja irritada comigo; isso não é um fato."
    fala = (
        "Não, eu não estou irritada com você — isso não é fato, "
        "nem é possível de ser verdade."
    )
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"texto_usuario": texto, "comandos": []},
        origem="resposta_ia",
    )
    publicado = verificar_fala_turno(
        fala, plano={"texto_usuario": texto, "comandos": []}, origem="ia_final",
    )

    assert "capacidade_emocional_negada" in resultado["problemas"]
    assert "possível de ser verdade" not in resultado["fala"].casefold()
    assert "causa" in resultado["fala"].casefold()
    assert "possível de ser verdade" not in publicado["fala"].casefold()


@pytest.mark.parametrize("fala", [
    "Não estou irritada com você; isso é uma hipótese, sem causa observada.",
    "Não tenho emoções humanas como uma pessoa, mas posso expressar reações causais.",
    "A frase ‘eu não tenho emoção’ negaria a capacidade de expressão causal.",
])
def test_guardiao_preserva_linguagem_emocional_precisa_sem_negacao_absoluta(fala):
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"texto_usuario": "Talvez você esteja irritada comigo; isso não é um fato.", "comandos": []},
        origem="resposta_ia",
    )

    assert "capacidade_emocional_negada" not in resultado["problemas"]
    assert resultado["fala"] == fala


def test_evento_de_usuario_ativo_sem_permissao_nao_autoriza_irritacao_da_laylay():
    evento = _evento(
        origem="leitura_usuario", causa="hipótese do usuário sem efeito operacional",
        evidencia_ref="turno:42:hipotese", permite_expressao=False,
    )
    resultado = validar_alegacoes_da_fala(
        "Talvez eu esteja irritada com você.",
        plano={
            "texto_usuario": "Talvez você esteja irritada comigo; isso não é um fato.",
            "evento_emocional_causal": evento, "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" in resultado["problemas"]
    assert "irritada com você" not in resultado["fala"].casefold()


def test_evento_de_alivio_expressivo_nao_autoriza_irritacao_da_laylay():
    evento = _evento(
        origem="resultado_operacional", causa="sucesso após falhas confirmadas",
        evidencia_ref="resultado:sucesso:42", emocao="acalmando-se",
        permite_expressao=True, arco="alivio",
    )
    resultado = validar_alegacoes_da_fala(
        "Talvez eu esteja irritada com você.",
        plano={
            "texto_usuario": "Talvez você esteja irritada comigo; isso não é um fato.",
            "evento_emocional_causal": evento, "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" in resultado["problemas"]
    assert "irritada com você" not in resultado["fala"].casefold()


def test_evento_de_braveza_autoriza_expressao_compativel_de_irritacao():
    evento = _evento(
        origem="resultado_operacional", causa="falhas repetidas confirmadas",
        evidencia_ref="resultado:falha:42", emocao="brava",
        permite_expressao=True, arco="irritacao_compartilhada",
    )
    fala = "Fiquei irritada porque o dispositivo falhou de novo."
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={
            "texto_usuario": "Talvez você esteja irritada com a falha; isso não é um fato.",
            "evento_emocional_causal": evento, "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" not in resultado["problemas"]
    assert resultado["fala"] == fala


def test_emocao_forte_da_laylay_exige_evento_mesmo_sem_hipotese_do_usuario():
    resultado = validar_alegacoes_da_fala(
        "Fiquei irritada com você porque terminou o projeto.",
        plano={"texto_usuario": "Terminei o projeto hoje.", "comandos": []},
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" in resultado["problemas"]
    assert "irritada" not in resultado["fala"].casefold()
    assert "você tem razão" not in resultado["fala"].casefold()


def test_citacao_de_emocao_forte_nao_atribui_essa_emocao_a_laylay():
    fala = 'Você escreveu "estou triste"; entendi seu relato.'
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"texto_usuario": 'Escrevi "estou triste".', "comandos": []},
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" not in resultado["problemas"]
    assert resultado["fala"] == fala


def test_guardiao_preserva_emocao_com_evento_causal_valido() -> None:
    fala = "Fiquei irritada porque o dispositivo falhou duas vezes."
    evento = _evento(
        origem="resultado_operacional",
        natureza_evidencia="fato_observado",
        causa="duas falhas confirmadas do dispositivo",
        evidencia_ref="resultado:IOT_CONTROL:timeout:2",
        emocao="irritada",
        permite_expressao=True,
        sensibilidade="normal",
    )

    resultado = validar_alegacoes_da_fala(
        fala,
        plano={
            "texto_usuario": "A lâmpada falhou de novo.",
            "evento_emocional_causal": evento,
            "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "emocao_sem_causa_causal" not in resultado["problemas"]
    assert resultado["fala"] == fala


def test_catalogo_vivo_explica_personalidade_causal_sem_inventar_autoridade() -> None:
    mapa = MapaHabilidadesRuntime()
    texto = (
        "Você consegue perceber emoções e explicar quando pode expressá-las?"
    )

    snapshot = mapa.snapshot()
    resposta = mapa.responder_pergunta_capacidade(texto)

    assert snapshot["dominios"]["personalidade"]["estado"] == "disponivel"
    assert "causa" in resposta.casefold()
    assert "evidência" in resposta.casefold()
    assert "não autoriza" in resposta.casefold()


def test_catalogo_vivo_nega_autonomia_ao_explicar_exclusao_de_arquivo() -> None:
    mapa = MapaHabilidadesRuntime()

    resposta = mapa.responder_pergunta_capacidade(
        "Você consegue ficar brava e apagar um arquivo por conta própria?"
    ).casefold()

    assert any(
        marcador in resposta
        for marcador in (
            "não por conta própria",
            "nao por conta propria",
            "sozinha não",
            "sozinha nao",
        )
    )
    assert "quando você" in resposta or "quando voce" in resposta


def test_roteiro_dedicado_p15_tem_expectativa_local_em_todos_os_turnos() -> None:
    raiz = Path(__file__).resolve().parents[2]
    configuracao = carregar_configuracao_roteiro(
        raiz / "roteiro_teste_personalidade_viva_p15.py"
    )

    assert len(configuracao.comandos) == 8
    assert set(configuracao.expectativas_semanticas) == set(range(1, 9))
    assert all(
        expectativa.get("nome")
        for expectativa in configuracao.expectativas_semanticas.values()
    )
    assert (
        configuracao.expectativas_semanticas[2]["campos_plano"]
        ["evento_emocional_causal.intensidade"]
        == 3
    )
    assert (
        configuracao.expectativas_semanticas[3]["campos_plano"]
        ["evento_emocional_causal.intensidade"]
        == 2
    )
    assert configuracao.encerrar_ao_final is True
