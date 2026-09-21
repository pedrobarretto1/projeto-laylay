"""Ausência explícita de evidência não exige repetir uma frase de contingência."""

import json
import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno

REPARO_REAL_C3 = (
    "Não há evidência atual de que um documento do Visual Studio Code esteja aberto. "
    "A presença de uma janela aberta não garante que um documento específico esteja ativo ou visível. "
    "Para confirmar, seria necessário uma observação direta da interface atual do VS Code. "
    "Se quiser, posso te ajudar a verificar se há uma janela aberta com um projeto específico."
)


def plano_sem_leitura(texto):
    plano = {"texto_usuario": texto, "comandos": [], "requer_execucao": False,
             "atualidade_factual": {"classe": "estado_observavel", "depende_atualidade": True}}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, plano=plano)
    assert plano["contrato_fala"]["roteiro_concreto"]["estrategia"] == "estado_observavel_sem_evidencia"
    return plano


@pytest.mark.parametrize("texto,fala", [
    ("O documento do Visual Studio Code está aberto?",
     "Não há evidência atual de que um documento do Visual Studio Code esteja aberto."),
    ("A janela está aberta?", "Não tenho evidência suficiente para confirmar o estado da janela."),
    ("A lâmpada está ligada?", "Ainda não há confirmação atual do estado da lâmpada."),
    ("O processo está rodando?", "Sem evidência atual, não posso afirmar o estado do processo."),
    ("A música está tocando?", "Não consegui confirmar o estado da reprodução."),
])
def test_ausencia_de_evidencia_e_reconhecida_em_diferentes_dominios(texto, fala):
    resultado = avaliar_qualidade_comunicacao(texto, fala, plano=plano_sem_leitura(texto))
    assert "estado_observavel_sem_incerteza" not in resultado["problemas"]
    assert resultado["aceita"] is True


@pytest.mark.parametrize("fala", [
    "O documento está aberto.", "O documento não está aberto. A janela está vaga.",
    "Há evidência atual de que o documento está aberto.",
    "Não há erros no documento aberto.",
])
def test_afirmacoes_de_estado_nao_substituem_leitura_confirmada(fala):
    texto = "O documento do Visual Studio Code está aberto?"
    resultado = avaliar_qualidade_comunicacao(texto, fala, plano=plano_sem_leitura(texto))
    assert resultado["aceita"] is False
    assert "estado_observavel_sem_incerteza" in resultado["problemas"]


def test_incerteza_nao_libera_negacao_generica_da_capacidade():
    texto = "O documento está aberto?"
    resultado = avaliar_qualidade_comunicacao(
        texto, "Não há evidência atual. Não tenho acesso ao computador.",
        plano=plano_sem_leitura(texto),
    )
    assert resultado["aceita"] is False
    assert "estado_observavel_negou_habilidade" in resultado["problemas"]


def test_reparo_com_evidencia_ausente_nao_dispara_segunda_autoria():
    texto = "O documento do Visual Studio Code está aberto?"
    # Saída completa capturada na sonda 20260905-200631; não resumir a fixture
    # para esconder outra rejeição do mesmo reparo real.
    reparada = REPARO_REAL_C3
    chamadas = []

    def modelo(*_args, **kwargs):
        chamadas.append(kwargs["_tipo_chamada"])
        assert len(chamadas) == 1, "reparo válido não deve pedir outra autoria"
        return json.dumps({"fala": reparada, "comandos": []})

    resultado = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": "O documento não está aberto. A janela está vaga.", "comandos": []}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="Fallback de teste.", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano_sem_leitura(texto)},
        log=lambda *_args: None,
    )
    assert chamadas == ["reparo_comunicacao"]
    assert resultado["fala"] == reparada
    assert resultado["comandos"] == []


@pytest.mark.parametrize("fala", [
    "Falta uma observação atual sobre o estado do documento neste momento.",
    "Falta uma leitura atual para saber se o documento está aberto.",
    "Não há evidência atual de qual documento está aberto.",
    "Não posso afirmar se o documento está aberto sem evidência direta.",
    "Sem uma observação atual, não é possível afirmar se o documento está aberto.",
    "Ainda não consegui observar qual documento está aberto.",
])
def test_contrato_e_guardiao_preservam_a_mesma_ressalva_de_observacao(fala):
    texto = "O documento do Visual Studio Code está aberto?"
    plano = plano_sem_leitura(texto)
    qualidade = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert qualidade["aceita"] is True
    guardiao = validar_alegacoes_da_fala(fala, plano=plano)
    assert guardiao["problemas"] == []
    assert guardiao["fala"] == fala


@pytest.mark.parametrize("fala", [
    "Há uma observação atual e o documento está aberto.",
    "Não há falta de observação atual. O documento está aberto.",
    "A observação atual confirma que o documento está aberto.",
    "Não há evidência atual, mas o documento está aberto.",
])
def test_ressalva_nao_encobre_afirmacao_sem_leitura(fala):
    texto = "O documento está aberto?"
    resultado = validar_alegacoes_da_fala(fala, plano=plano_sem_leitura(texto))
    assert "estado_atual_sem_evidencia" in resultado["problemas"]


def test_formulacao_falta_observacao_chega_ao_verificador_final_sem_substituicao():
    texto = "O documento do Visual Studio Code está aberto?"
    fala = (
        "Falta uma observação atual sobre o estado do documento do Visual Studio Code neste momento. "
        "Não posso afirmar se está aberto ou não sem evidência direta."
    )
    plano = plano_sem_leitura(texto)
    assert avaliar_qualidade_comunicacao(texto, fala, plano=plano)["aceita"] is True
    resultado = verificar_fala_turno(fala, plano=plano)
    assert resultado["aceita"] is True
    assert resultado["fala"] == fala
