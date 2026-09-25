"""Uma fonte literal e um tema comum não bastam para ligar exemplo à regra."""

from scripts.analises.contrato_vinculo_didatico import RelacaoAnotada, avaliar_vinculo
from scripts.analises.sonda_composicao_extrativa_ensino import casos_manuais_reais, compor_fala


FONTES = {
    "div_def": {"url": "https://exemplo.org/divisao", "trecho": (
        "Dividir é repartir objetos em partes iguais entre pessoas."
    )},
    "div_ex": {"url": "https://exemplo.org/exemplo", "trecho": (
        "Repartir 12 objetos entre 3 pessoas dá 4 objetos para cada pessoa."
    )},
    "div_inv": {"url": "https://exemplo.org/inversao", "trecho": (
        "Repartir 3 pessoas entre 12 objetos dá outro resultado."
    )},
    "luz_def": {"url": "https://exemplo.org/luz", "trecho": (
        "A luz é essencial para a fotossíntese das plantas."
    )},
    "luz_ex": {"url": "https://exemplo.org/girassol", "trecho": (
        "Girassóis jovens acompanham o percurso do sol."
    )},
    "flora_def": {"url": "https://exemplo.org/perene", "trecho": (
        "Perenes sensíveis ao frio são cultivadas como anuais em climas frios."
    )},
    "flora_ex": {"url": "https://exemplo.org/begonia", "trecho": (
        "Em climas frios, begônias perenes podem ser cultivadas como anuais."
    )},
}


def _relacao(fonte_id: str, papel: str, relacao: str,
             papeis: tuple[tuple[str, str], ...],
             condicoes: frozenset[str] = frozenset()) -> RelacaoAnotada:
    return RelacaoAnotada(fonte_id, FONTES[fonte_id]["trecho"], papel,
                          relacao, papeis, condicoes)


def test_exemplo_da_mesma_relacao_e_direcao_ainda_exige_revisao_independente() -> None:
    definicao = _relacao("div_def", "definicao", "repartir_igualmente",
                         (("quantidade", "objetos"), ("destino", "pessoas")),
                         frozenset({"partes_iguais"}))
    exemplo = _relacao("div_ex", "exemplo", "repartir_igualmente",
                       (("quantidade", "objetos"), ("destino", "pessoas")),
                       frozenset({"partes_iguais"}))
    observado = avaliar_vinculo(definicao, exemplo, FONTES)
    assert observado["estado"] == "estrutura_compativel_revisao_pendente"
    assert observado["aprovado_para_compor"] is False


def test_troca_de_papeis_eh_primeira_divergencia() -> None:
    definicao = _relacao("div_def", "definicao", "repartir_igualmente",
                         (("quantidade", "objetos"), ("destino", "pessoas")))
    inversao = _relacao("div_inv", "exemplo", "repartir_igualmente",
                        (("quantidade", "pessoas"), ("destino", "objetos")))
    assert avaliar_vinculo(definicao, inversao, FONTES)["estado"] == "direcao_ou_papeis_diferentes"


def test_assunto_luz_em_comum_nao_faz_exemplo_de_fotossintese() -> None:
    definicao = _relacao("luz_def", "definicao", "essencial_para_fotossintese",
                         (("agente", "luz"), ("processo", "fotossintese")))
    exemplo = _relacao("luz_ex", "exemplo", "acompanhar_percurso_do_sol",
                       (("agente", "girassol"), ("alvo", "sol")))
    assert avaliar_vinculo(definicao, exemplo, FONTES)["estado"] == "relacao_diferente"


def test_condicao_de_clima_nao_pode_desaparecer() -> None:
    definicao = _relacao("flora_def", "definicao", "cultivada_como_anual",
                         (("planta", "perene"), ("cultivo", "anual")),
                         frozenset({"clima_frio"}))
    exemplo = _relacao("flora_ex", "exemplo", "cultivada_como_anual",
                       (("planta", "perene"), ("cultivo", "anual")))
    assert avaliar_vinculo(definicao, exemplo, FONTES)["estado"] == "condicao_omitida"
    assert avaliar_vinculo(definicao, RelacaoAnotada(
        exemplo.fonte_id, exemplo.trecho, exemplo.papel, exemplo.relacao,
        exemplo.papeis, frozenset({"clima_frio"}),
    ), FONTES)["estado"] == "estrutura_compativel_revisao_pendente"


def test_relacao_anotada_sem_trecho_da_fonte_nao_e_receipt() -> None:
    definicao = _relacao("luz_def", "definicao", "fotossintese", ())
    inventado = RelacaoAnotada("luz_ex", "Girassóis fabricam luz por conta própria.",
                               "exemplo", "fotossintese", ())
    assert avaliar_vinculo(definicao, inventado, FONTES)["estado"] == "evidencia_literal_invalida"


def test_luz_real_composicao_rastreavel_nao_prova_vinculo_didatico() -> None:
    caso = casos_manuais_reais()["luz"]
    assert compor_fala(caso["propostas"], caso["fontes"], caso["pedido"])["estado"] == "forma_rastreavel"
    definicao, exemplo = (
        RelacaoAnotada(item["fonte_id"], item["trecho"], item["papel"],
                        relacao, papeis)
        for item, relacao, papeis in (
            (caso["propostas"][0], "luz_essencial_fotossintese",
             (("agente", "luz"), ("processo", "fotossintese"))),
            (caso["propostas"][1], "girassol_acompanha_sol",
             (("agente", "girassol_jovem"), ("alvo", "sol"))),
        )
    )
    assert avaliar_vinculo(definicao, exemplo, caso["fontes"])["estado"] == "relacao_diferente"


def test_floricultura_real_excecao_nao_e_exemplo_direto_da_definicao() -> None:
    caso = casos_manuais_reais()["floricultura"]
    assert compor_fala(caso["propostas"], caso["fontes"], caso["pedido"])["estado"] == "forma_rastreavel"
    definicao = RelacaoAnotada(
        caso["propostas"][0]["fonte_id"], caso["propostas"][0]["trecho"],
        "definicao", "ciclo_de_vida_anual", (("planta", "anual"),),
    )
    exemplo = RelacaoAnotada(
        caso["propostas"][2]["fonte_id"], caso["propostas"][2]["trecho"],
        "exemplo", "perene_cultivada_como_anual",
        (("planta", "perene"), ("cultivo", "anual")), frozenset({"clima_frio"}),
    )
    assert avaliar_vinculo(definicao, exemplo, caso["fontes"])["estado"] == "relacao_diferente"
