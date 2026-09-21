import time

import pytest

from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno


CORRECAO = "Estou perguntando sobre o documento, não sobre o aplicativo. Você conseguiu verificar qual documento está aberto?"
ANTERIOR = "O documento do Visual Studio Code está aberto?"


def contrato_correcao(texto=CORRECAO, *, anterior=ANTERIOR, idade=1):
    plano = {"texto_usuario": texto, "comandos": [], "requer_execucao": False,
             "atualidade_factual": {"classe": "estado_observavel", "depende_atualidade": True}}
    return construir_contrato_semantico_fala(
        texto, plano=plano, funcao_comunicativa=analisar_funcao_comunicativa(texto),
        mente={"ultima_entrada": anterior, "ultima_entrada_ts": time.time() - idade},
        falas_recentes=["Visual Studio Code está aberto.", "Spotify está aberto."],
    )


@pytest.mark.parametrize("texto", [CORRECAO,
    "Estou falando da janela, não do processo.",
    "Eu perguntei sobre a faixa, não sobre a playlist.",
])
def test_contraste_explicito_de_escopo_e_correcao_sem_autoridade(texto):
    assert analisar_funcao_comunicativa(texto)["funcao"] == "correcao"


def test_correcao_recupera_pergunta_do_usuario_sem_inventar_alvo_observado():
    contrato = contrato_correcao()
    assert contrato["texto_usuario_corrigido"] == ANTERIOR
    assert contrato["referente"] == ""
    assert contrato["autoriza_execucao"] is False
    for compacto in (False, True):
        assert ANTERIOR in formatar_contrato_fala_para_prompt(contrato, compacto=compacto)
    fala = "Não consegui verificar qual documento está aberto no Visual Studio Code."
    resultado = avaliar_qualidade_comunicacao(CORRECAO, fala, plano={"contrato_fala": contrato})
    assert resultado["aceita"] is True
    assert resultado["contrato_reparo"]["texto_usuario_corrigido"] == ANTERIOR


@pytest.mark.parametrize("idade", [241, -30, float("nan")])
def test_contexto_expirado_futuro_ou_invalido_nao_e_retornado(idade):
    contrato = contrato_correcao(idade=idade)
    assert contrato.get("texto_usuario_corrigido", "") == ""


def test_pergunta_independente_nao_herda_entidades_do_historico():
    texto = "O documento está aberto?"
    contrato = contrato_correcao(texto)
    assert contrato.get("texto_usuario_corrigido", "") == ""
    resultado = avaliar_qualidade_comunicacao(texto,
        "Não consegui verificar qual documento está aberto no Visual Studio Code.",
        plano={"contrato_fala": contrato})
    assert "estado_observavel_herdou_entidade_antiga" in resultado["problemas"]


def test_nome_presente_so_na_fala_da_laylay_continua_bloqueado():
    contrato = contrato_correcao()
    resultado = avaliar_qualidade_comunicacao(CORRECAO,
        "Não consegui verificar se o Spotify está aberto.", plano={"contrato_fala": contrato})
    assert "estado_observavel_herdou_entidade_antiga" in resultado["problemas"]


def test_contexto_da_correcao_nao_confirma_estado_do_documento():
    resultado = validar_alegacoes_da_fala("O documento está aberto.", plano={
        "texto_usuario": CORRECAO, "contrato_fala": contrato_correcao(), "comandos": [],
    })
    assert "estado_atual_sem_evidencia" in resultado["problemas"]


def test_verificacao_final_composta_preserva_correcao_sem_afirmar_efeito():
    fala = "Não consegui verificar qual documento está aberto no Visual Studio Code."
    plano = {"texto_usuario": CORRECAO, "contrato_fala": contrato_correcao(), "comandos": []}
    resultado = verificar_fala_turno(fala, plano=plano)
    assert resultado["aceita"] is True
    assert resultado["fala"] == fala
    assert plano["comandos"] == []
    assert plano["contrato_fala"]["referente"] == ""


def test_verificacao_final_composta_nao_libera_afirmacao_por_contexto():
    fala = "Não consegui verificar qual documento está aberto no Visual Studio Code, mas a janela está aberta."
    resultado = verificar_fala_turno(fala, plano={
        "texto_usuario": CORRECAO, "contrato_fala": contrato_correcao(), "comandos": [],
    })
    assert "estado_atual_sem_evidencia" in resultado["problemas"]
    assert resultado["fala"] != fala
