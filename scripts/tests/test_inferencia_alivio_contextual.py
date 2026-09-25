"""Inferência local só com conclusão e liberação ancoradas na fala do usuário."""

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_leitura_emocional_usuario
from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
from mente_laylay.cognicao.leitura_semantica_turno import normalizar_leitura_semantica
from mente_laylay.cognicao.orquestrador_turno_runtime import registrar_leitura_semantica_principal
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural


@pytest.mark.parametrize("texto", [
    "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso.",
    "Acabei a monografia que me prendia havia meses. Agora posso respirar.",
    "Resolvi o problema que me consumia há dias; finalmente estou livre disso.",
    "Depois de semanas de tensão, finalizei o trabalho e tirei esse peso das costas.",
])
def test_carga_resolvida_com_liberacao_produz_inferencia_causal(texto):
    leitura = analisar_intencao_emocional(texto)
    evento = criar_evento_leitura_emocional_usuario(leitura, turno_id="teste")

    assert leitura["emocao"] == "alivio"
    assert leitura["natureza_evidencia"] == "inferencia"
    assert leitura["trecho_evidencia"].casefold() in texto.casefold()
    assert leitura["causa"]
    assert evento["origem"] == "inferencia_contextual_usuario"
    assert evento["natureza_evidencia"] == "inferencia"
    assert evento["intensidade"] == 2
    assert evento["permite_expressao"] is False
    assert evento["autoriza_execucao"] is False


@pytest.mark.parametrize("texto", [
    "Entreguei o relatório de rotina hoje.",
    "Depois de semanas, entreguei o projeto.",
    "Tirei um peso das costas no treino e entreguei o relatório.",
    "Se eu entregasse o projeto, tiraria um peso das costas.",
    "Não entreguei o projeto; continuo preso nisso.",
    'Escreva a frase "tirei um peso das costas depois de entregar o projeto".',
    "Finalmente ela entregou o projeto e tirou um peso das costas.",
    "Ele disse: 'Finalmente tirei um peso das costas: entreguei o projeto depois de semanas preso nisso.'",
    "Li no diário dela: 'Entreguei o projeto após semanas preso nisso e tirei um peso das costas.'",
    "Entreguei o projeto depois de semanas preso nisso, mas não tirei peso nenhum das costas.",
    "Resolvi o problema que me consumia há dias, mas ainda não estou livre disso.",
])
def test_ausencia_de_autoria_conclusao_ou_liberacao_nao_inventa_alivio(texto):
    leitura = analisar_intencao_emocional(texto)

    assert leitura.get("emocao") != "alivio"


def test_sentimento_declarado_preserva_natureza_social_contra_rotulo_inferido_da_llm():
    texto = "Estou um pouco triste hoje."
    leitura_direta = analisar_intencao_emocional(texto)
    evento_direto = criar_evento_leitura_emocional_usuario(leitura_direta, turno_id="direto")
    estado = EstadoCompartilhadoRuntime(
        mental={
            "turno_atual": {"id": "direto", "evento_emocional_causal": evento_direto},
            "plano_turno_atual": {"id": "direto", "texto_usuario": texto,
                                  "evento_emocional_causal": evento_direto},
        },
        memoria_conversa={"messages": []},
    )
    proposta = normalizar_leitura_semantica({
        "atos": [{"tipo": "relato"}],
        "leitura_emocional": {
            "estado_usuario": "tristeza", "intensidade": 1,
            "causa_expressa": "tristeza relatada hoje",
            "trecho_evidencia": "Estou um pouco triste",
            "natureza_evidencia": "inferencia", "confianca": 0.99,
        },
    }, texto=texto, origem="llm_principal")
    assert proposta["leitura_emocional"]["valida"]

    registrar_leitura_semantica_principal(
        lambda: {"_estado_compartilhado_runtime": estado, "print": lambda *_: None},
        texto, proposta,
    )

    assert estado.mental["plano_turno_atual"]["evento_emocional_causal"] == evento_direto
    assert estado.mental["turno_atual"]["leitura_semantica_principal"]


@pytest.mark.parametrize(("texto", "termos"), [
    (
        "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso.",
        ("projeto", "semanas"),
    ),
    (
        "Acabei a monografia que me prendia havia meses. Agora posso respirar.",
        ("monografia", "meses"),
    ),
])
def test_contingencia_sem_llm_retoma_causa_publicada_sem_chamada_extra(texto, termos):
    leitura = analisar_intencao_emocional(texto)
    evento = criar_evento_leitura_emocional_usuario(leitura, turno_id="alivio")
    contexto = {"plano_turno_atual": {"texto_usuario": texto, "evento_emocional_causal": evento}}

    fala = fala_contingencia_natural(texto, contexto=contexto, motivo_falha="orcamento_limite_chamadas")

    assert all(termo in fala.casefold() for termo in termos)
    assert "limite de tentativas" not in fala.casefold()


def test_contingencia_nao_reutiliza_inferencia_de_outro_turno():
    texto = "Resolvi o problema que me consumia há dias; finalmente estou livre disso."
    evento = criar_evento_leitura_emocional_usuario(analisar_intencao_emocional(texto), turno_id="anterior")
    contexto = {"plano_turno_atual": {"texto_usuario": "outro assunto", "evento_emocional_causal": evento}}

    fala = fala_contingencia_natural(texto, contexto=contexto, motivo_falha="orcamento_limite_chamadas")

    assert "resol" not in fala.casefold()


@pytest.mark.parametrize(("texto", "marcador", "ausente"), [
    ("Estou muito feliz porque terminei um projeto.", "projeto", "bolsa"),
    ("Estou muito feliz porque recebi uma bolsa de estudos.", "bolsa", "projeto"),
])
def test_contingencia_de_alegria_retoma_motivo_sem_inventar_outro(
    texto, marcador, ausente,
):
    evento = criar_evento_leitura_emocional_usuario(
        analisar_intencao_emocional(texto), turno_id="alegria",
    )
    contexto = {"plano_turno_atual": {
        "texto_usuario": texto,
        "evento_emocional_causal": evento,
    }}

    for _ in range(3):
        fala = fala_contingencia_natural(
            texto, contexto=contexto, motivo_falha="orcamento_limite_chamadas",
        ).casefold()
        assert "feliz" in fala
        assert marcador in fala
        assert ausente not in fala
