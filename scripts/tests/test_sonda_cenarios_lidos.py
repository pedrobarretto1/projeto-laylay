"""Cenário exige relação e proveniência, não só palavra parecida."""

from scripts.analises.sonda_cenarios_lidos import (
    blocos_com_secao,
    candidatos_causais,
    contrastes_observacionais,
)


def _bloco(texto: str, indice: int = 0, *, url: str = "https://escola.example/circuitos", secao: str = "Série") -> dict:
    return {"texto": texto, "indice": indice, "url": url, "secao": secao}


def test_cenario_causal_explicito_da_mesma_frase_e_candidato() -> None:
    frase = (
        "Num circuito em série, se uma lâmpada abre o circuito, a corrente para "
        "porque o caminho único foi interrompido; por isso a outra apaga."
    )
    assert candidatos_causais([_bloco(frase)], "circuito em série") == [{
        "tipo": "causal", "texto_fonte": frase,
        "url": "https://escola.example/circuitos", "secao": "Série", "indice": 0,
        "mecanismo_textual": True, "verdade_externa_verificada": False,
    }]


def test_editorial_pergunta_e_dominio_paralelo_nao_viram_cenario_de_serie() -> None:
    blocos = [
        _bloco("Veja exemplos de circuito em série em nosso próximo artigo.", 0),
        _bloco("O que acontece se uma lâmpada queimar em um circuito em série?", 1),
        _bloco("Num circuito paralelo, se uma lâmpada queima, as outras seguem acesas; por isso recomendamos esse modelo.", 2),
    ]
    assert candidatos_causais(blocos, "circuito em série") == []


def test_cenario_sem_url_ou_secao_nao_tem_proveniencia_suficiente() -> None:
    frase = (
        "Num circuito em série, se uma lâmpada abre o circuito, a corrente para "
        "porque o caminho único foi interrompido; por isso a outra apaga."
    )
    assert candidatos_causais([_bloco(frase, url="")], "circuito em série") == []
    assert candidatos_causais([_bloco(frase, secao="")], "circuito em série") == []


def test_contraste_observacional_exige_mesmo_objeto_pagina_e_secao() -> None:
    a = _bloco("Na planta baixa, a janela da sala revela sua posição e largura.", 0,
               url="https://escola.example/arquitetura", secao="Representações")
    b = _bloco("No corte vertical, a janela da sala revela sua altura em relação ao piso.", 1,
               url="https://escola.example/arquitetura", secao="Representações")
    esperado = [{
        "tipo": "observacional", "texto_a": a["texto"], "texto_b": b["texto"],
        "url": a["url"], "secao": a["secao"], "objeto": "janela da sala",
        "indices": (0, 1),
        "verdade_externa_verificada": False,
    }]
    assert contrastes_observacionais([a, b], "janela da sala", "planta baixa", "corte vertical") == esperado
    assert contrastes_observacionais(
        [a, {**b, "url": "https://outro.example/arquitetura"}],
        "janela da sala", "planta baixa", "corte vertical",
    ) == []
    assert contrastes_observacionais(
        [a, {**b, "secao": "Outra seção"}],
        "janela da sala", "planta baixa", "corte vertical",
    ) == []


def test_legenda_e_contraste_sem_objeto_compartilhado_nao_passam() -> None:
    blocos = [
        _bloco("Exemplo de planta baixa.", 0),
        _bloco("No corte vertical, a janela da sala revela sua altura em relação ao piso.", 1),
    ]
    assert contrastes_observacionais(blocos, "janela da sala", "planta baixa", "corte vertical") == []


def test_parser_preserva_url_secao_e_ordem_sem_unir_artigos() -> None:
    html = (
        "<nav><p>Outra janela aparece no menu lateral.</p></nav>"
        "<h2>Representações da casa</h2>"
        "<p>Na planta baixa, a janela da sala revela sua posição e largura.</p>"
        "<p>No corte vertical, a janela da sala revela sua altura em relação ao piso.</p>"
        "<h2>Outra seção</h2>"
        "<p>A fachada mostra a mesma janela vista de fora da casa.</p>"
    )
    blocos = blocos_com_secao(html, "https://escola.example/arquitetura")
    assert [(item["indice"], item["secao"]) for item in blocos] == [
        (0, "Representações da casa"),
        (1, "Representações da casa"),
        (2, "Outra seção"),
    ]
    assert contrastes_observacionais(
        blocos, "janela da sala", "planta baixa", "corte vertical",
    )[0]["url"] == "https://escola.example/arquitetura"


def test_subsecoes_irmas_ligam_a_mesma_janela_sob_o_mesmo_titulo_pai() -> None:
    html = (
        "<h2>Uma janela, dois desenhos</h2>"
        "<h3>Planta baixa</h3>"
        "<p>Na planta baixa, a janela da sala revela sua largura e posição.</p>"
        "<h3>Fachada</h3>"
        "<p>Na fachada, a mesma janela revela sua altura vista da rua.</p>"
    )
    blocos = blocos_com_secao(html, "https://escola.example/arquitetura")
    assert [b["secao_pai"] for b in blocos] == ["Uma janela, dois desenhos"] * 2
    assert contrastes_observacionais(
        blocos, "janela da sala", "planta baixa", "fachada",
    ) == [{
        "tipo": "observacional",
        "texto_a": blocos[0]["texto"], "texto_b": blocos[1]["texto"],
        "url": "https://escola.example/arquitetura",
        "secao": "Uma janela, dois desenhos", "objeto": "janela da sala",
        "indices": (0, 1), "verdade_externa_verificada": False,
    }]


def test_anafora_nao_une_janela_de_outro_capitulo() -> None:
    html = (
        "<h2>Primeiro projeto</h2><h3>Planta baixa</h3>"
        "<p>Na planta baixa, a janela da sala revela sua largura e posição.</p>"
        "<h2>Segundo projeto</h2><h3>Fachada</h3>"
        "<p>Na fachada, a mesma janela revela sua altura vista da rua.</p>"
    )
    blocos = blocos_com_secao(html, "https://escola.example/arquitetura")
    assert contrastes_observacionais(
        blocos, "janela da sala", "planta baixa", "fachada",
    ) == []


def test_titulo_de_subsecao_repetido_nao_une_capitulos_diferentes() -> None:
    html = (
        "<h2>Primeiro projeto</h2><h3>Representações</h3>"
        "<p>Na planta baixa, a janela da sala revela sua largura e posição.</p>"
        "<h2>Segundo projeto</h2><h3>Representações</h3>"
        "<p>Na fachada, a mesma janela revela sua altura vista da rua.</p>"
    )
    blocos = blocos_com_secao(html, "https://escola.example/arquitetura")
    assert contrastes_observacionais(
        blocos, "janela da sala", "planta baixa", "fachada",
    ) == []


def test_titulo_de_capitulo_repetido_continua_sendo_outro_span() -> None:
    html = (
        "<h2>Representações</h2>"
        "<p>Na planta baixa, a janela da sala revela sua largura e posição.</p>"
        "<h2>Representações</h2>"
        "<p>Na fachada, a mesma janela revela sua altura vista da rua.</p>"
    )
    blocos = blocos_com_secao(html, "https://escola.example/arquitetura")
    assert blocos[0]["secao_pai"] == blocos[1]["secao_pai"]
    assert blocos[0]["secao_pai_id"] != blocos[1]["secao_pai_id"]
    assert contrastes_observacionais(
        blocos, "janela da sala", "planta baixa", "fachada",
    ) == []
