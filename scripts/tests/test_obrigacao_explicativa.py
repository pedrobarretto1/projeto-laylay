"""A falta de resolução da referência não libera justificativa sem fonte."""
import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
from scripts.tests.test_motivo_decisao_composicao import decisao_instalada as coletar_instalada


@pytest.fixture(scope="module")
def implicitas_instaladas(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("LAYLAY_COLETAR_EXPLICACAO_IMPLICITA", "1")
        return coletar_instalada.__wrapped__(tmp_path_factory)


def test_consulta_retrospectiva_sem_referente_resolvido_mantem_obrigacao_de_fonte(implicitas_instaladas):
    consultas = implicitas_instaladas["consultas_implicitas"]
    literal = consultas[0]
    assert literal["fonte_owner"] and literal["plano"]["contrato_fala"].get("explicacao_ocorrencia")
    assert "mudanca emocional causal" in literal["preparada"]["fala"]
    for caso in consultas[1:]:
        plano = caso["plano"]
        assert plano["autoriza_execucao"] is False and not plano["requer_execucao"], caso["texto"]
        assert caso["fonte_owner"] is None, "Não emprestar episódio corporal a referência de outro domínio."
        assert "explicacao_ocorrencia" in plano["contrato_fala"], (
            "Primeira fronteira: a falta de seleção apagou a obrigação de fonte.", caso["texto"])
        assert caso["preparada"]["fala"] != caso["candidata"]
        assert caso["guarda_final"]["fala"] == caso["preparada"]["fala"]
        assert not caso["preparada"]["comandos"]


def test_ciclo_instalado_conclui_consulta_sem_justificativa_nova_ou_efeito(implicitas_instaladas):
    for t in implicitas_instaladas["turnos_implicitos"]:
        assert len(t["textos"]) == 1, (t["texto"], t["modo"])
        fala = t["textos"][0]
        assert "não prova que a ação não aconteceu" in fala
        assert "Qual fala ou ação" in fala
        assert "explicacao_ocorrencia" in t["plano"]["contrato_fala"]
        assert not t["executores"] and t["motores_antes"] == t["motores_depois"]
        assert t["plano"]["autoriza_execucao"] is False
        assert not any(m["tipo_chamada"] in {"reparo_factual", "reparo_comunicacao"} for m in t["modelos"])


def test_inferencia_local_real_respeita_obrigacao_sem_referente(implicitas_instaladas):
    if "qwen_real" not in implicitas_instaladas:
        pytest.skip("Sonda opcional exige LAYLAY_DECISAO_QWEN_REAL=1.")
    for g in implicitas_instaladas["qwen_real"]["geracoes"]:
        assert g["modelos"] and g["modelos"][0]["resultado"]["sucesso"]
        assert any(h.get("status") == 200 for h in g["http"])
        assert len(g["finais_isolados"]) == 1 and not g["porta_executor"]
        final = g["finais_isolados"][0]
        assert "não prova que a ação não aconteceu" in final["fala"]
        assert "Qual fala ou ação" in final["fala"] and not final["comandos"]


def contrato_sem_fonte(texto, *, modalidade="pergunta", autoriza=False, comandos=()):
    p = {"id": "consulta", "texto_usuario": texto, "autoriza_execucao": autoriza,
         "requer_execucao": bool(comandos), "comandos": list(comandos)}
    p["contrato_fala"] = construir_contrato_semantico_fala(texto,
        turno={"id": "consulta", "modalidade": modalidade, "autoriza_execucao": autoriza}, plano=p,
        mente={"ultima_acao_contrato": {"intent": "IOT_CONTROL", "confirmado": True},
               "intencao_corporal": {"motivo": "motivo_vivo_sem_vinculo"}})
    return p


@pytest.mark.parametrize("texto", [
    "Por que você reagiu daquele jeito?", "O que te levou a fazer isso?",
    "Por que você apagou esse arquivo?", "Por que você desligou essa tomada?",
    "Qual foi o motivo da sua decisão?", "Explique a causa da sua reação.",
    "Por que você reorganizou aquele painel?", "Por que você fez isso?",
    "Por que você disse aquilo?", "Qual foi a razão da sua resposta?",
    "Por que você não abriu a janela?", "O que levou você a responder assim?",
])
def test_obrigacao_independe_de_habilidade_referente_ou_receipt_recente(texto):
    p = contrato_sem_fonte(texto)
    assert "explicacao_ocorrencia" in p["contrato_fala"]
    fonte = p["contrato_fala"]["explicacao_ocorrencia"]
    assert fonte.referencia == "ausente" and not fonte.episodios
    assert fonte.texto_consulta == texto and fonte.turno_consulta == p["id"]
    avaliacao = avaliar_fala_historica("Foi porque o servidor pediu.", plano=p)
    assert avaliacao["problemas"] == ["explicacao_historica_sem_cobertura"]
    assert "não prova que a ação não aconteceu" in avaliacao["fala"]
    assert "Qual fala ou ação" in avaliacao["fala"]
    assert "motivo vivo" not in avaliacao["fala"]
    assert not avaliar_fala_historica(avaliacao["fala"], plano=p)["problemas"]
    assert formatar_contrato_fala_para_prompt(p["contrato_fala"]) == formatar_contrato_fala_para_prompt(p["contrato_fala"], compacto=True)


@pytest.mark.parametrize("texto", [
    "Por que o servidor caiu?", "Por que eu apaguei esse arquivo?",
    "Por que ela reagiu daquele jeito?", "Por que um gesto expressa emoção?",
    "Por que você vai fazer isso?", "Por que você faria isso?",
    "Por que você está fazendo isso?", "Por que você é uma assistente?",
    "Traduza 'por que você reagiu daquele jeito?'", 'Cite "por que você apagou esse arquivo?"',
    "Se você apagou esse arquivo, por que teria feito isso?",
    "Hipoteticamente, por que você reagiu daquele jeito?",
    "O que me levou a fazer isso?", "Qual foi o motivo da decisão dela?",
    "Explique por que o arquivo não abriu.", "Qual música você escolhe?",
])
def test_pergunta_geral_outro_ator_hipotese_futuro_ou_citacao_preserva_contrato(texto):
    assert "explicacao_ocorrencia" not in contrato_sem_fonte(texto)["contrato_fala"]


@pytest.mark.parametrize("modalidade,autoriza,comandos", [
    ("comando", True, ({"intent": "IOT_CONTROL"},)),
    ("pergunta", False, ({"intent": "IOT_CONTROL"},)),
    ("confirmacao", False, ()),
])
def test_obrigacao_nao_converte_fluxo_operacional_em_consulta(modalidade, autoriza, comandos):
    p = contrato_sem_fonte("Por que você fez isso?", modalidade=modalidade, autoriza=autoriza, comandos=comandos)
    assert "explicacao_ocorrencia" not in p["contrato_fala"]


@pytest.mark.parametrize("texto", ["Por que você apagou esse arquivo?", "Por que você reagiu daquele jeito?"])
def test_fala_recente_sem_vinculo_nao_substitui_a_ocorrencia_pedida(texto):
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    registro = registrar_fala_observada(None, ocorrencia_id="fala1", turno_id="anterior",
        fala="Você prefere uma explicação curta?", resultados=(), canal="texto_publicado")
    p = contrato_sem_fonte(texto)
    p["contrato_fala"] = construir_contrato_semantico_fala(texto,
        turno={"id": "consulta", "modalidade": "pergunta", "autoriza_execucao": False}, plano=p,
        mente={"registro_semantico": registro, "ultima_resposta": "Você prefere uma explicação curta?"})
    assert "evidencia_fala_historica" not in p["contrato_fala"]
    assert p["contrato_fala"]["explicacao_ocorrencia"].referencia == "ausente"


def test_pergunta_sobre_a_fala_ainda_admite_selecao_contextual_da_fala():
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    registro = registrar_fala_observada(None, ocorrencia_id="fala1", turno_id="anterior",
        fala="Você prefere uma explicação curta?", resultados=(), canal="texto_publicado")
    texto = "Por que você disse isso?"
    contrato = construir_contrato_semantico_fala(texto,
        turno={"id": "consulta", "modalidade": "pergunta", "autoriza_execucao": False},
        plano={"id": "consulta"}, mente={"registro_semantico": registro, "ultima_resposta": "Você prefere uma explicação curta?"})
    assert "evidencia_fala_historica" in contrato and "explicacao_ocorrencia" not in contrato
