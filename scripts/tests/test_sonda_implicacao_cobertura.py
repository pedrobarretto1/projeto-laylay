"""Cobertura exata impede que o revisor aprove somente a metade fácil."""

from scripts.analises.sonda_implicacao_cobertura import consolidar


FONTE = "O laço percorre os itens de uma lista na ordem em que aparecem."
ALEGA = "O laço percorre a lista em ordem e imprime os itens."
TRECHO = "percorre os itens de uma lista"


def _parte(original: str, classe: str, prova: str, proposicao: str | None = None) -> dict:
    return {"trecho_original": original, "proposicao": proposicao or original,
            "classe": classe, "trecho_literal": prova}


def test_reconstrucao_preserva_toda_a_alegacao_e_recusa_cauda_omitida() -> None:
    assert consolidar(ALEGA, [_parte("O laço percorre a lista em ordem", "sustentada", TRECHO)], FONTE)["classe"] == "invalida"
    assert consolidar(ALEGA, [
        _parte("O laço percorre a lista em ordem", "sustentada", TRECHO),
        _parte("e imprime os itens.", "sem_prova", ""),
    ], FONTE)["classe"] == "sem_prova"


def test_proposicao_nao_pode_apagar_palavra_de_conteudo_do_segmento() -> None:
    assert consolidar(ALEGA, [
        _parte(ALEGA, "sustentada", TRECHO, "O laço percorre a lista em ordem."),
    ], FONTE)["classe"] == "invalida"


def test_conjuncao_de_entidades_pode_ficar_em_uma_proposicao() -> None:
    alegacao = "R1 e R2 ficam no mesmo ramo."
    fonte = "R1 and R2 are in the same branch of a circuit."
    assert consolidar(alegacao, [_parte(alegacao, "sustentada", "same branch of a circuit")], fonte) == {
        "classe": "sustentada", "cobertura": True, "provas_localizadas": True,
    }


def test_recibo_com_trecho_inventado_e_reordenacao_falham_fechado() -> None:
    assert consolidar(ALEGA, [_parte(ALEGA, "sustentada", "imprime automaticamente")], FONTE)["classe"] == "invalida"
    assert consolidar(ALEGA, [
        _parte("e imprime os itens.", "sem_prova", ""),
        _parte("O laço percorre a lista em ordem", "sustentada", TRECHO),
    ], FONTE)["classe"] == "invalida"
