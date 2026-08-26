from __future__ import annotations

import pytest
from pathlib import Path

from mente_laylay.emocoes.avaliador_eventos import (
    AvaliadorEventosEmocionaisRuntime,
)
from mente_laylay.emocoes.contrato_causal import (
    NATUREZAS_EVIDENCIA_EMOCIONAL,
    criar_evento_emocional_causal,
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
from mente_laylay.memoria_mental.eventos_emocionais import (
    estado_eventos_emocionais_inicial,
    publicar_evento_emocional_causal,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.qualidade_comunicacao import (
    contingencia_comunicacao,
)
from mente_laylay.cognicao.validacao_contrato_fala import (
    validar_aderencia_contrato_fala,
)
from mente_laylay.personalidade.contingencia_natural import (
    fala_contingencia_natural,
)


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
        "ts": 100.0,
        "validade_s": 120.0,
    }
    base.update(campos)
    return criar_evento_emocional_causal(**base)


def test_contrato_causal_representa_todos_os_campos_e_nao_autoriza_acao() -> None:
    evento = _evento()

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


@pytest.mark.parametrize(
    ("texto", "evento", "marcadores"),
    (
        (
            "Estou um pouco triste hoje.",
            _evento(
                origem="contingencia_lexical_usuario",
                intensidade=1,
                sensibilidade="vulneravel",
            ),
            ("trist", "ouvi", "entendo"),
        ),
        (
            "Estou muito feliz porque terminei um projeto.",
            _evento(
                origem="contingencia_lexical_usuario",
                causa="alegria explicitamente relatada no turno atual",
                intensidade=3,
                sensibilidade="sensivel",
            ),
            ("feliz", "projeto", "parab"),
        ),
    ),
)
def test_contingencia_consumidora_do_evento_causal_reconhece_estado_explicito(
    texto,
    evento,
    marcadores,
) -> None:
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
    raiz = Path(__file__).resolve().parents[1]
    configuracao = carregar_configuracao_roteiro(
        raiz / "roteiro_teste_personalidade_viva_p15.py"
    )

    assert len(configuracao.comandos) == 7
    assert set(configuracao.expectativas_semanticas) == set(range(1, 8))
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
