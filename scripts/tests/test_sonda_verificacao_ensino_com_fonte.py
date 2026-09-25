"""O gabarito experimental não deve confundir tema com prova da alegação."""

from scripts.analises.sonda_verificacao_ensino_com_fonte import (
    frases_fonte,
    resultado_rastreavel,
)
from scripts.analises.sonda_rascunho_didatico_ancorado import (
    auditar_publicacao,
    diagnosticar_citacoes,
)


def test_frases_fonte_preservam_texto_literal_e_url() -> None:
    fontes = [{"url": "https://exemplo.org/a", "trecho": (
        "A planta baixa representa a vista superior de uma edificação. "
        "A página também fala sobre arquitetura."
    )}]
    frases = frases_fonte(fontes)
    assert frases[0] == {
        "id": "E1",
        "url": "https://exemplo.org/a",
        "texto": "A planta baixa representa a vista superior de uma edificação.",
    }


def test_rotulo_correto_com_evidencia_errada_nao_passa() -> None:
    resultado = {
        "classe": "contradita", "id_evidencia": "E2",
        "evidencia": {"id": "E2", "texto": "A planta baixa é importante."},
    }
    assert not resultado_rastreavel(resultado, "contradita", ("E5",))
    assert resultado_rastreavel(
        {**resultado, "id_evidencia": "E5", "evidencia": {"id": "E5", "texto": "A vista é superior."}},
        "contradita", ("E5",),
    )


def test_sem_prova_exige_e0_sem_fonte_inventada() -> None:
    assert resultado_rastreavel(
        {"classe": "sem_prova", "id_evidencia": "E0", "evidencia": {}},
        "sem_prova", ("E0",),
    )
    assert not resultado_rastreavel(
        {"classe": "sem_prova", "id_evidencia": "E0", "evidencia": {"id": "E1"}},
        "sem_prova", ("E0",),
    )


def test_id_existente_na_definicao_nao_certifica_exemplo_sem_fonte() -> None:
    frases = [{"id": "E1", "texto": "A planta baixa representa a vista superior."}]
    diagnostico = diagnosticar_citacoes(
        {"definicao": "Vista superior.", "exemplo": "A casa é vista de baixo.",
         "ids_definicao": ["E1"], "ids_exemplo": []},
        frases,
    )
    assert diagnostico == {
        "ids_existentes": True,
        "definicao_com_id": True,
        "exemplo_com_id": False,
        "implicacao_verificada": False,
    }


def test_publicacao_extrativa_aceita_definicao_e_exemplo_literais() -> None:
    frases = [
        {"id": "E1", "texto": "As plantas anuais completam seu ciclo de vida em um ano."},
        {"id": "E2", "texto": "Petúnias são plantas anuais cultivadas em jardins."},
    ]
    gerado = {
        "definicao": frases[0]["texto"], "exemplo": frases[1]["texto"],
        "ids_definicao": ["E1"], "ids_exemplo": ["E2"],
    }
    assert auditar_publicacao(gerado, frases) == {
        "definicao_literal": True,
        "exemplo_literal": True,
        "publicavel": True,
    }


def test_id_valido_nao_autoriza_detalhe_inventado_no_exemplo() -> None:
    frases = [
        {"id": "E1", "texto": "As plantas anuais completam seu ciclo de vida em um ano."},
        {"id": "E2", "texto": "Petúnias são plantas anuais cultivadas em jardins."},
    ]
    gerado = {
        "definicao": frases[0]["texto"],
        "exemplo": "Petúnias são plantas anuais cultivadas em jardins e florescem em outubro.",
        "ids_definicao": ["E1"], "ids_exemplo": ["E2"],
    }
    assert auditar_publicacao(gerado, frases) == {
        "definicao_literal": True,
        "exemplo_literal": False,
        "publicavel": False,
    }
