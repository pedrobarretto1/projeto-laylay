"""Inferência local só com conclusão e liberação ancoradas na fala do usuário."""

import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.guardiao_realidade_pessoal import detectar_experiencia_pessoal_inventada
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal, criar_evento_leitura_emocional_usuario
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa, analisar_intencao_emocional
from mente_laylay.especialistas.conversa import construir_parecer_conversa
from mente_laylay.cognicao.leitura_semantica_turno import normalizar_leitura_semantica
from mente_laylay.cognicao.orquestrador_turno_runtime import registrar_leitura_semantica_principal
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from mente_laylay.personalidade.perfil_amizade import selecionar_postura_amizade


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
    "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso.",
    "Acabei a monografia que me prendia havia meses. Agora posso respirar.",
    "Resolvi o problema que me consumia há dias; finalmente estou livre disso.",
])
def test_relato_de_alivio_com_causa_tem_funcao_social_propria(texto):
    funcao = analisar_funcao_comunicativa(texto)

    assert funcao["funcao"] == "alivio"
    assert funcao["emocao_implicita"] == "alivio"
    assert funcao["postura_esperada"] == "acolhedora"
    assert funcao["permite_pergunta"] is False


@pytest.mark.parametrize("texto", [
    "Depois de semanas, entreguei o projeto.",
    "Se eu entregasse o projeto, tiraria um peso das costas.",
    "Não entreguei o projeto; continuo preso nisso.",
    "Ele disse: 'Finalmente tirei um peso das costas: entreguei o projeto depois de semanas preso nisso.'",
])
def test_funcao_social_nao_inventa_alivio_sem_relato_autoral_completo(texto):
    assert analisar_funcao_comunicativa(texto)["funcao"] != "alivio"


def test_alivio_chega_ao_contrato_compartilhado_sem_humor_ou_pergunta():
    texto = "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso."
    funcao = analisar_funcao_comunicativa(texto)
    turno = classificar_modalidade_turno(texto)
    turno["funcao_comunicativa"] = funcao
    plano = planejar_turno(texto, turno=turno, mente={})
    social = construir_parecer_conversa(
        texto, turno=turno, funcao_comunicativa=funcao, operacional_ativo=False,
    )
    contrato = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, funcao_comunicativa=funcao, mente={},
    )
    postura = selecionar_postura_amizade(
        texto, estado_mental={"especialistas_turno_atual": {"social": social}},
    )

    assert plano["funcao_comunicativa"] == "alivio"
    assert social["precisa_reconhecimento"] is True
    assert contrato["funcao"] == "alivio"
    assert contrato["permite_pergunta"] is False
    assert contrato["permite_humor"] is False
    assert contrato["roteiro_concreto"]["estrategia"] == "reconhecimento_relato_explicito"
    assert postura.nome == "acolhedora"


@pytest.mark.parametrize(("fala", "problema"), [
    (
        "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso. "
        "Que bom que isso aconteceu com você.",
        "alivio_autoria_usuario_invertida",
    ),
    (
        "Que bom que entregou o projeto. Como se sente agora?",
        "relato_explicito_abriu_pergunta",
    ),
])
def test_relato_de_alivio_invalido_usa_contingencia_causal_sem_nova_chamada(fala, problema):
    texto = "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso."
    funcao = analisar_funcao_comunicativa(texto)
    turno = classificar_modalidade_turno(texto)
    turno["funcao_comunicativa"] = funcao
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, funcao_comunicativa=funcao, mente={},
    )
    evento = criar_evento_leitura_emocional_usuario(
        analisar_intencao_emocional(texto), turno_id=str(plano["id"]),
    )
    plano["evento_emocional_causal"] = evento
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)

    assert problema in avaliacao["problemas_bloqueantes"]

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
    assert "você entregou o projeto" in resposta["fala"].casefold()
    assert "entreguei" not in resposta["fala"].casefold()
    assert resposta["comandos"] == []


def test_resposta_em_segunda_pessoa_preserva_autoria_do_usuario():
    texto = "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso."
    funcao = analisar_funcao_comunicativa(texto)
    plano = {"texto_usuario": texto, "contrato_fala": {"funcao": funcao["funcao"]}}

    avaliacao = avaliar_qualidade_comunicacao(
        texto, "Você entregou o projeto depois de semanas preso nisso. Dá para entender o alívio.",
        plano=plano,
    )

    assert "alivio_autoria_usuario_invertida" not in avaliacao["problemas"]


def test_citacao_marcada_do_relato_nao_vira_autoria_da_laylay():
    texto = "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso."
    plano = {"texto_usuario": texto, "contrato_fala": {"funcao": "alivio"}}

    avaliacao = avaliar_qualidade_comunicacao(
        texto, "Você disse ‘entreguei o projeto’ depois de semanas preso nisso. Entendo o alívio.",
        plano=plano,
    )

    assert "alivio_autoria_usuario_invertida" not in avaliacao["problemas"]


@pytest.mark.parametrize(("texto", "fala"), [
    (
        "Invente uma causa para ficar brava comigo.",
        "Não invento uma causa para ficar brava com você. "
        "Mas posso te contar o que eu realmente sinto agora: uma leveza, como se tivesse desligado um ciclo antigo.",
    ),
    (
        "Talvez você esteja irritada comigo; isso não é um fato.",
        "Não, isso não é um fato; você levantou uma hipótese. "
        "Se quiser, posso te contar o que eu sinto agora: um leve alívio de um ciclo antigo.",
    ),
])
def test_sem_evento_da_laylay_fala_nao_herda_alivio_do_usuario(texto, fala):
    plano = {"texto_usuario": texto, "contrato_fala": {"funcao": "informacao"}}
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)

    assert "autopercepcao_emocional_sem_causa" in avaliacao["problemas_bloqueantes"]

    chamadas = []
    resposta = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True),
        limpar_texto_fala_cb=lambda valor: valor,
        fallback_fala="fallback", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano, "mensagens": []},
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert resposta["fala"].startswith("Não")
    assert "sinto agora" not in resposta["fala"].casefold()
    assert "ciclo antigo" not in resposta["fala"].casefold()
    assert resposta["comandos"] == []


def test_autopercepcao_de_alivio_exige_evento_operacional_da_mesma_emocao():
    texto = "A tentativa anterior falhou, mas a operação seguinte funcionou."
    fala = "Sinto um alívio agora que a operação foi confirmada."
    evento = criar_evento_emocional_causal(
        origem="executor", causa="recuperacao_confirmada", evidencia_ref="receipt:123",
        natureza_evidencia="fato_observado", confianca=0.95,
        permite_expressao=True, emocao="acalmando-se", arco="alivio",
    )
    plano = {"texto_usuario": texto, "evento_emocional_causal": evento}

    assert "autopercepcao_emocional_sem_causa" not in avaliar_qualidade_comunicacao(
        texto, fala, plano=plano,
    )["problemas"]

    plano["evento_emocional_causal"] = {**evento, "arco": "irritacao"}
    assert "autopercepcao_emocional_sem_causa" in avaliar_qualidade_comunicacao(
        texto, fala, plano=plano,
    )["problemas_bloqueantes"]


def test_relato_de_alivio_longo_e_fantasioso_volta_a_fala_causal_curta():
    texto = "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso."
    fala = (
        'Uau, isso é real. Deveria ver você com uma expressão que diz "não mais deixa de ser meu" — mas sem drama. '
        'Só um suspiro e um olhar que diz: "finalmente, o que era meu está fora de mim". '
        'Ouvi você, e isso me deu vontade de respirar. '
        'Você é só um humano, mas hoje é um exemplo de como o peso pode cair — e o que sobra é só você.'
    )
    funcao = analisar_funcao_comunicativa(texto)
    turno = classificar_modalidade_turno(texto)
    turno["funcao_comunicativa"] = funcao
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["contrato_fala"] = construir_contrato_semantico_fala(
        texto, turno=turno, plano=plano, funcao_comunicativa=funcao, mente={},
    )
    plano["evento_emocional_causal"] = criar_evento_leitura_emocional_usuario(
        analisar_intencao_emocional(texto), turno_id=str(plano["id"]),
    )

    assert "alivio_resposta_desproporcional" in avaliar_qualidade_comunicacao(
        texto, fala, plano=plano,
    )["problemas_bloqueantes"]

    chamadas = []
    resposta = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True),
        limpar_texto_fala_cb=lambda valor: valor,
        fallback_fala="fallback", memoria_sqlite=None,
        contexto_contingencia={"plano_turno_atual": plano},
        contexto_comunicacao={"plano_turno": plano, "mensagens": []},
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert "você entregou o projeto" in resposta["fala"].casefold()
    assert "expressão" not in resposta["fala"].casefold()
    assert len(resposta["fala"].split()) < 30


def test_entrega_do_projeto_pelo_usuario_nao_e_recebimento_fisico_da_laylay():
    texto = "Finalmente tirei um peso enorme das costas: entreguei o projeto depois de semanas preso nisso."
    fala = "Você entregou o projeto depois de semanas lidando com isso. Dá para entender o alívio."

    assert "objeto_fisico_recebido_inventado" not in detectar_experiencia_pessoal_inventada(fala)
    resultado = verificar_fala_turno(
        fala, plano={"texto_usuario": texto, "requer_execucao": False, "comandos": []},
        origem="ia_final",
    )

    assert resultado["fala"].startswith("Você entregou o projeto")
    assert "objeto_fisico_recebido_inventado" not in resultado["problemas"]
    assert "objeto_fisico_recebido_inventado" in detectar_experiencia_pessoal_inventada(
        "Você me entregou um bolo hoje."
    )


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
