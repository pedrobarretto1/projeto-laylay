"""P01: uma fonte pertinente não certifica a alegação nem o exemplo."""

from scripts.analises.contrato_unidades_ensino import (
    avaliar_unidade_ensino,
    extrair_contas_explicitas,
)
from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao


FONTES = {
    "arq": {
        "url": "https://escola.example/arquitetura",
        "trecho": "A planta baixa representa a casa vista de cima.",
    },
    "python": {
        "url": "https://docs.python.org/3/tutorial/controlflow.html",
        "trecho": "O for percorre os itens de uma sequência na ordem em que aparecem.",
    },
    "matematica": {
        "url": "https://escola.example/matematica",
        "trecho": "Por exemplo, 6 × 3 = 18.",
    },
}


def test_frase_observada_literalmente_tem_rastreio_mas_nao_verdade_universal() -> None:
    resultado = avaliar_unidade_ensino({
        "papel": "definicao", "fonte_id": "arq",
        "trecho": FONTES["arq"]["trecho"],
        "afirmacao": FONTES["arq"]["trecho"],
    }, FONTES)
    assert resultado["estado"] == "literal_rastreavel"
    assert resultado["implicacao_verificada"] is False
    assert resultado["fonte_id"] == "arq"


def test_planta_baixa_invertida_nao_herda_confianca_da_fonte() -> None:
    resultado = avaliar_unidade_ensino({
        "papel": "definicao", "fonte_id": "arq",
        "trecho": FONTES["arq"]["trecho"],
        "afirmacao": "A planta baixa representa a casa vista de baixo.",
        "verificado": True,
    }, FONTES)
    assert resultado["estado"] == "pendente_implicacao"
    assert resultado["implicacao_verificada"] is False


def test_afirmacao_composta_nao_e_provada_so_pelo_primeiro_pedaco() -> None:
    resultado = avaliar_unidade_ensino({
        "papel": "exemplo", "fonte_id": "python",
        "trecho": FONTES["python"]["trecho"],
        "afirmacao": (
            "O for percorre os itens de uma sequência na ordem em que aparecem "
            "e imprime tudo automaticamente."
        ),
    }, FONTES)
    assert resultado["estado"] == "pendente_implicacao"


def test_trecho_inventado_e_fonte_inexistente_nao_passam() -> None:
    proposta = {
        "papel": "exemplo", "fonte_id": "arq",
        "trecho": "A planta baixa mostra o telhado por baixo.",
        "afirmacao": "A planta baixa mostra o telhado por baixo.",
    }
    assert avaliar_unidade_ensino(proposta, FONTES)["estado"] == "trecho_nao_localizado"
    assert avaliar_unidade_ensino({**proposta, "fonte_id": "inexistente"}, FONTES)["estado"] == "fonte_nao_localizada"


def test_conta_extraida_exige_igualdade_matematica_correta() -> None:
    certa = avaliar_unidade_ensino({
        "papel": "exemplo", "fonte_id": "matematica",
        "trecho": "6 × 3 = 18", "afirmacao": "6 × 3 = 18",
    }, FONTES)
    errada = avaliar_unidade_ensino({
        "papel": "exemplo", "fonte_id": "matematica",
        "trecho": "6 × 3 = 18", "afirmacao": "6 × 3 = 19",
    }, FONTES)
    assert certa["estado"] == "calculo_conferido"
    assert certa["implicacao_verificada"] is True
    assert errada["estado"] == "pendente_implicacao"


def test_conta_errada_na_propria_pagina_nao_herda_verdade_da_fonte() -> None:
    fonte = {"erro": {
        "url": "https://escola.example/matematica",
        "trecho": "O exemplo informa 6 × 3 = 19.",
    }}
    resultado = avaliar_unidade_ensino({
        "papel": "exemplo", "fonte_id": "erro",
        "trecho": "6 × 3 = 19", "afirmacao": "6 × 3 = 19",
    }, fonte)
    assert resultado["estado"] == "calculo_incorreto"
    assert resultado["implicacao_verificada"] is False


def test_sem_papel_e_sem_url_nao_viram_evidencia_para_aula() -> None:
    proposta = {
        "papel": "exemplo", "fonte_id": "arq",
        "trecho": FONTES["arq"]["trecho"],
        "afirmacao": FONTES["arq"]["trecho"],
    }
    assert avaliar_unidade_ensino({**proposta, "papel": ""}, FONTES)["estado"] == "papel_invalido"
    sem_url = {"arq": {**FONTES["arq"], "url": ""}}
    assert avaliar_unidade_ensino(proposta, sem_url)["estado"] == "fonte_sem_url"


def test_confianca_da_pesquisa_real_nao_confirma_alegacao_invertida() -> None:
    frase = FONTES["arq"]["trecho"]
    fundamentacao = montar_fundamentacao("planta baixa", {
        "ok": True, "confianca": 0.72, "resumo": frase,
        "fonte": "web_multifonte", "fontes": [{**FONTES["arq"], "alvo": "planta baixa"}],
    }, agora=1000.0)
    assert fundamentacao["confiavel"] is True
    fonte = fundamentacao["fontes"][0]
    resultado = avaliar_unidade_ensino({
        "papel": "definicao", "fonte_id": "arq", "trecho": fonte["trecho"],
        "afirmacao": "A planta baixa representa a casa vista de baixo.",
    }, {"arq": fonte})
    assert resultado["estado"] == "pendente_implicacao"
    assert resultado["implicacao_verificada"] is False


def test_divisao_explicita_da_fala_real_e_conferida_fora_do_modelo() -> None:
    fala = "12 dividido por 3 é igual a 4. Mas aqui, 12 dividido por 3 = 4."
    contas = extrair_contas_explicitas(fala)
    assert len(contas) == 2
    assert [conta["estado"] for conta in contas] == ["calculo_conferido"] * 2
    assert [fala[conta["inicio"]:conta["fim"]] for conta in contas] == [
        "12 dividido por 3 é igual a 4", "12 dividido por 3 = 4",
    ]


def test_conta_errada_e_divisor_zero_nao_viram_recibo() -> None:
    contas = extrair_contas_explicitas("15 / 3 = 6; 12 dividido por 0 = 0")
    assert [conta["estado"] for conta in contas] == [
        "calculo_incorreto", "operacao_invalida",
    ]


def test_conta_certa_nao_aprova_cauda_extra_da_frase() -> None:
    fala = "12 / 3 = 4 e a caixa pesa 8 kg."
    contas = extrair_contas_explicitas(fala)
    assert len(contas) == 1
    assert contas[0]["estado"] == "calculo_conferido"
    assert fala[contas[0]["fim"]:] == " e a caixa pesa 8 kg."


def test_resultado_sem_operacao_explicita_permanece_pendente() -> None:
    assert extrair_contas_explicitas("Aí seria 5 por pessoa.") == []


def test_multiplicacao_e_espacos_na_divisao_usam_o_mesmo_contrato() -> None:
    contas = extrair_contas_explicitas("6 × 3 = 18; 12 dividido   por 3 = 4")
    assert [conta["estado"] for conta in contas] == ["calculo_conferido"] * 2
