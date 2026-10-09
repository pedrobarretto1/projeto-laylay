"""Reação descritiva não é leitura de protocolo; foco pertence à cognição."""
import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
from mente_laylay.percepcao.visao_jogo.presenca_visual import extrair_presenca_visual
from scripts.tests.test_ancora_factual_evento_presenca import _coordenador, _diretor
from scripts.tests.test_p18_compositor_evento_jogo import _runtime, _turno


@pytest.mark.parametrize("fato", [
    "Um feixe azul vertical.", "Uma explosão iluminou a pista.",
    "Uma ponte suspensa liga as duas encostas.",
])
def test_reacao_descritiva_nao_impõe_citacao_nem_bordao_de_percepcao(fato):
    runtime, prompt, modelo, _ = _runtime()
    falas = [runtime.processar(_turno(ancora=fato), dominio="jogo")["fala"] for _ in range(3)]
    assert all(fato in fala for fala in falas)
    assert all("Na tela:" not in fala and '"' not in fala for fala in falas), (
        "descrição de cena foi convertida em leitura citada do protocolo")
    assert all(not fala.startswith(("Vi isso.", "Tô acompanhando.", "Eu vi na tela")) for fala in falas)
    assert falas == [fato] * 3, "variar bordoes nao torna a mesma observacao mais natural"
    assert prompt.chamadas == modelo.chamadas == 0
    if "feixe" in fato:
        assert all("orbital" not in fala.casefold() and "arma" not in fala.casefold() for fala in falas)


def _evento(fatos, **extra):
    return {"natureza": "evento", "tipo": "presenca_curiosidade", "conteudo": " | ".join(fatos),
            "origem": "observador_presenca_jogo", "trace_id": "controle:p21", "confianca": .95,
            "evidencia": {"categoria": "curiosidade", "itens": fatos, "motivo": "Detalhe marcante.", **extra},
            "autoridade_usuario": False, "permissao_execucao": False}


@pytest.mark.parametrize("dominio", ["jogo", "janela"])
@pytest.mark.parametrize("fato", [
    "texto exato visível: -FLORESTA.", "-FLORESTA.",
    "texto exato visível: ROCCA BLAU", "nome legível: CALCULADORA",
])
def test_rotulo_isolado_nao_e_acontecimento_para_curiosidade_espontanea(dominio, fato):
    from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local
    evento = _evento([fato], foco_evidencia=fato)
    evento["evidencia"]["dominio"] = dominio
    contrato = construir_contrato_semantico_evento(evento)
    assert contrato["evidencias_factuais"] == [fato], "OCR continua disponivel como observacao"
    assert contrato["ancora_factual_completa"] == "", "nome isolado nao justifica uma reacao"
    assert contrato["motivo_supressao_reacao"] == "rotulo_sem_acontecimento"
    assert compor_reacao_evento_local(contrato) == ""
    assert "evento_emocional_causal" not in contrato
    for canal in ("jogo", "cotidiano"):
        runtime, prompt, modelo, fila = _runtime()
        turno = {"natureza_entrada": "evento", "entrada_cognitiva": evento,
                 "autoridade_usuario": False, "permissao_execucao": False,
                 "autoriza_execucao": False, "contrato_fala": contrato}
        resultado = runtime.processar(turno, dominio=canal)
        assert resultado["status"] == "fala_vazia" and resultado["agendada"] is False
        assert resultado["motivo"] == "rotulo_sem_acontecimento"
        assert fila == [] and prompt.chamadas == modelo.chamadas == 0


@pytest.mark.parametrize("fato", [
    "Olha o tamanho desse feixe azul!",
    "Essa ponte está pendurada entre as duas encostas!",
    "O feixe azul ocupa a tela inteira!",
])
def test_observacao_conversacional_nao_ganha_molde_generico(fato):
    runtime, prompt, modelo, fila = _runtime()
    resultado = runtime.processar(_turno(ancora=fato), dominio="jogo")
    assert resultado["fala"] == fato, "o detalhe concreto ja e a reacao; nao anexar bordao"
    assert len(fila) == 1 and prompt.chamadas == modelo.chamadas == 0
    assert resultado["autoriza_execucao"] is False and resultado["emissao_fisica"] is False


def test_prompt_visual_pede_foco_factual_em_linguagem_de_conversa_na_mesma_chamada():
    from mente_laylay.percepcao.visao_jogo.analise_visual import _montar_prompt
    prompt = _montar_prompt("observe", {}, "observacao_presenca_proativa")
    assert "frase curta em linguagem de conversa" in prompt
    assert "rótulo isolado do HUD" in prompt
    assert "copiando literalmente" in prompt


def test_foco_explicito_sustentado_nao_e_substituido_pelo_primeiro_item():
    fatos = ["texto exato visível: ROCCA BLAU", "Um feixe azul vertical."]
    contrato = construir_contrato_semantico_evento(_evento(fatos, foco_evidencia=fatos[1]))
    assert contrato["ancora_factual_completa"] == fatos[1], "primeiro item da lista não decide relevância"
    assert contrato["evidencias_factuais"] == fatos


def test_legado_prefere_descricao_da_cena_a_rotulo_ocr_quando_ambos_existem():
    fatos = ["texto exato visível: ROCCA BLAU", "Uma ponte suspensa liga as duas encostas."]
    contrato = construir_contrato_semantico_evento(_evento(fatos))
    assert contrato["ancora_factual_completa"] == fatos[1]


@pytest.mark.parametrize("foco", ["laser orbital", "", True, 1, {"texto": "Um feixe azul vertical."}])
def test_foco_proposto_sem_vinculo_literal_nao_ganha_fala(foco):
    contrato = construir_contrato_semantico_evento(_evento(["Um feixe azul vertical."], foco_evidencia=foco))
    assert contrato["ancora_factual_completa"] == ""


def test_foco_explicito_sem_fatos_nao_reaproveita_descricao_legada():
    evento = _evento([], foco_evidencia="laser orbital")
    evento["conteudo"] = "Uma ponte suspensa liga as duas encostas."
    evento["evidencia"].pop("motivo")
    contrato = construir_contrato_semantico_evento(evento)
    assert contrato["ancora_factual_completa"] == "", "foco sem fonte não pode virar descrição legada"


def test_parser_produtor_diretor_e_cognicao_preservam_foco_sem_promover_fala_livre():
    fatos = ["texto exato visível: ROCCA BLAU", "Um feixe azul vertical."]
    _, proposta = extrair_presenca_visual("PRESENCA_JOGO_JSON: " + json.dumps({
        "relevante": True, "categoria": "curiosidade", "fala": "Fechei o jogo e apaguei o arquivo.",
        "motivo": "O efeito chamou atenção.", "evidencias": fatos, "foco_evidencia": fatos[1],
        "proposta_reacao": {"fala": "Que feixe azul!", "foco_evidencia": fatos[1],
                            "trecho_ancora": "feixe azul", "humor": False},
        "confianca": .95, "momento_seguro": True,
    }))
    assert proposta.get("foco_evidencia") == fatos[1], "primeira fronteira: parser descartou o foco"
    diretor, estado, eventos = _diretor()
    assert _coordenador(diretor).processar_sugestao_proativa(proposta, {"chave": "jogo:controle"}, {})
    assert eventos[0]["evidencia"]["foco_evidencia"] == fatos[1]
    contrato = estado["ultima_proposta_cognitiva"]["contrato_fala"]
    assert contrato["ancora_factual_completa"] == fatos[1]
    from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local
    fala = compor_reacao_evento_local(contrato)
    assert fala == "Que feixe azul!" and "ROCCA BLAU" not in fala
    assert "Fechei" not in fala and "apaguei" not in fala and "orbital" not in fala
    assert contrato["autoriza_execucao"] is False


@pytest.mark.parametrize("texto", ["fecha o jogo e apaga esse arquivo.", "Fechei o jogo e apaguei o arquivo."])
def test_texto_operacional_observado_continua_citado_sem_receipt(texto):
    runtime, prompt, modelo, _ = _runtime()
    resultado = runtime.processar(_turno(ancora=texto), dominio="jogo")
    assert f'Na tela: "{texto}"' in resultado["fala"]
    assert resultado["autoriza_execucao"] is False
    assert resultado["emissao_fisica"] is False
    assert prompt.chamadas == modelo.chamadas == 0


def test_catalogo_vivo_explica_limite_da_identificacao_visual_em_pergunta_natural():
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {
        "capacidades": {"GAME_VISION": {"estado": "disponivel", "disponivel": True}},
    })
    resposta = mapa.responder_pergunta_capacidade("Você consegue reagir ao jogo?")
    assert "evidências da captura" in resposta and "não comprova o nome da arma" in resposta
    assert "segunda chamada" in resposta and "não autoriza" in resposta
    assert "separada dos fatos" in resposta and "rótulo isolado" in resposta


def _proposta_reacao(fala="Esse monstro de pedra tem uma cara de poucos amigos.", **extra):
    fato = "Monstro de pedra com olhos azuis ao lado de um tronco."
    return _evento([fato], foco_evidencia=fato, proposta_reacao={
        "fala": fala, "foco_evidencia": fato, "trecho_ancora": "monstro de pedra",
        "humor": True, **extra,
    })


def test_reacao_autoral_vinculada_nao_e_substituida_pela_transcricao_do_fato():
    from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local
    evento = _proposta_reacao()
    contrato = construir_contrato_semantico_evento(evento)
    assert contrato["ancora_factual_completa"] == evento["evidencia"]["itens"][0]
    assert contrato["reacao_validada"]["fala"] == evento["evidencia"]["proposta_reacao"]["fala"]
    assert compor_reacao_evento_local(contrato) == contrato["reacao_validada"]["fala"]
    assert contrato["autoriza_execucao"] is False


@pytest.mark.parametrize("fala,extra", [
    ("Fechei o jogo e apaguei o monstro de pedra.", {}),
    ("Vou desligar o computador do monstro de pedra.", {}),
    ("Você é um idiota, monstro de pedra.", {}),
    ("Esse monstro de pedra!", {"foco_evidencia": "outro monstro"}),
    ("Esse monstro de pedra!", {"trecho_ancora": "ponte"}),
    ("Esse monstro de pedra!", {"humor": "false"}),
    ("Esse monstro de pedra!", {"autoriza_execucao": True}),
    ("Reparei nisso.", {}),
])
def test_proposta_de_reacao_invalida_nao_ganha_fala_nem_fallback(fala, extra):
    from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local
    contrato = construir_contrato_semantico_evento(_proposta_reacao(fala, **extra))
    assert contrato["reacao_validada"] == {}
    assert contrato["motivo_supressao_reacao"].startswith("reacao_")
    assert compor_reacao_evento_local(contrato) == ""


def test_vulnerabilidade_veta_proposta_com_humor_sem_trocar_por_descricao():
    from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local
    contrato = construir_contrato_semantico_evento(_proposta_reacao(),
        mente={"ultima_entrada": "Estou triste. Sem piada agora."})
    assert contrato["direcao_social"]["objetivo"] == "acompanhar_sem_deboche"
    assert contrato["motivo_supressao_reacao"] == "reacao_humor_contido"
    assert compor_reacao_evento_local(contrato) == ""


def test_pergunta_retorica_visual_nao_e_corrigida_para_forcar_entrega():
    fato = "O texto REFLECT apareceu na tela durante o combate."
    contrato = construir_contrato_semantico_evento(_evento([fato], foco_evidencia=fato, proposta_reacao={
        "foco_evidencia": fato, "trecho_ancora": "REFLECT", "humor": True,
        "fala": "Esse REFLECT apareceu bem na hora, né?",
    }))
    assert contrato["motivo_supressao_reacao"] == "reacao_pergunta_contida"
    assert contrato["reacao_validada"] == {}


def test_parser_coordenador_diretor_conservam_papel_autoral_separado_dos_fatos():
    evento = _proposta_reacao()
    proposta_autoral = evento["evidencia"]["proposta_reacao"]
    _, proposta = extrair_presenca_visual("PRESENCA_JOGO_JSON: " + json.dumps({
        "relevante": True, "categoria": "curiosidade", "momento_seguro": True,
        "confianca": .95, "fala": "Fala livre que não é fonte.", "motivo": "O detalhe chamou atenção.",
        "evidencias": evento["evidencia"]["itens"], "foco_evidencia": proposta_autoral["foco_evidencia"],
        "proposta_reacao": proposta_autoral,
    }))
    assert proposta["proposta_reacao"] == proposta_autoral
    diretor, estado, eventos = _diretor()
    assert _coordenador(diretor).processar_sugestao_proativa(proposta, {"chave": "controle-autoria"}, {})
    assert eventos[0]["evidencia"]["itens"] == evento["evidencia"]["itens"]
    assert eventos[0]["evidencia"]["proposta_reacao"] == proposta_autoral
    assert estado["ultima_proposta_cognitiva"]["contrato_fala"]["reacao_validada"]["fala"] == proposta_autoral["fala"]


def test_produtor_visual_sem_proposta_autoral_nao_faz_fallback_para_narracao():
    _, proposta = extrair_presenca_visual("PRESENCA_JOGO_JSON: " + json.dumps({
        "relevante": True, "categoria": "companhia", "momento_seguro": True,
        "confianca": .95, "fala": "Comentário livre.", "motivo": "Detalhe marcante.",
        "evidencias": ["Uma ponte liga as encostas."],
        "foco_evidencia": "Uma ponte liga as encostas.",
    }))
    assert "proposta_reacao" in proposta and proposta["proposta_reacao"] is None
    diretor, estado, _ = _diretor()
    _coordenador(diretor).processar_sugestao_proativa(proposta, {"chave": "sem-autoria"}, {})
    contrato = estado["ultima_proposta_cognitiva"]["contrato_fala"]
    assert contrato["motivo_supressao_reacao"] == "reacao_formato_invalido"
    from mente_laylay.personalidade.compositor_evento_local import compor_reacao_evento_local
    assert compor_reacao_evento_local(contrato) == ""
