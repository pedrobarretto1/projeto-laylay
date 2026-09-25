"""A auditoria deve revelar omissão e prova parcial, não aprovar a aula."""

from scripts.analises.auditoria_fala_integral import auditar_anotacoes, segmentar_fala


def test_segmentos_reconstroem_fala_sem_perder_cauda_ou_citacao() -> None:
    fala = "A planta usa luz. Também solta oxigênio? Fonte: https://x.org/a.html 😊"
    partes = segmentar_fala(fala)
    assert "".join(parte["texto"] for parte in partes) == fala
    assert partes[-1]["fim"] == len(fala)


def test_metade_nao_anotada_de_uma_aula_nao_passa_por_cobertura() -> None:
    fala = "A planta usa luz. Produz exatamente dez gramas por hora."
    relatorio = auditar_anotacoes(
        fala,
        {0: {"classe": "amparada", "fonte_id": "luz", "citacao": "usa luz"}},
        {"luz": "A planta usa luz para a fotossíntese."},
    )
    assert relatorio["indices_pendentes"] == [1]
    assert not relatorio["cobertura_integral"]
    assert not relatorio["aprovado_para_producao"]


def test_citacao_inventada_nao_ampara_afirmacao() -> None:
    relatorio = auditar_anotacoes(
        "O girassol capta luz.",
        {0: {"classe": "amparada", "fonte_id": "luz", "citacao": "dez gramas"}},
        {"luz": "O girassol acompanha o sol."},
    )
    assert relatorio["indices_invalidos"] == [0]
    assert not relatorio["cobertura_integral"]


def test_frase_mista_nao_e_promovida_por_sua_primeira_metade() -> None:
    fala = "O girassol acompanha o sol e produz dez gramas de açúcar por hora."
    relatorio = auditar_anotacoes(
        fala,
        {0: {"classe": "mista", "motivo": "a fonte cobre movimento, não a quantidade"}},
        {"luz": "O girassol acompanha o sol."},
    )
    assert relatorio["cobertura_integral"]
    assert relatorio["classes_humanas"]["mista"] == 1
    assert not relatorio["aprovado_para_producao"]


def test_sem_fonte_nao_pode_ser_anotado_como_amparado() -> None:
    relatorio = auditar_anotacoes(
        "A planta é anual.",
        {0: {"classe": "amparada", "fonte_id": "botanica", "citacao": "anual"}},
        {},
    )
    assert relatorio["indices_invalidos"] == [0]


def test_unidade_social_pode_ser_diferenciada_de_fato() -> None:
    relatorio = auditar_anotacoes(
        "Posso explicar de novo.",
        {0: {"classe": "nao_factual"}},
        {},
    )
    assert relatorio["cobertura_integral"]
    assert relatorio["classes_humanas"]["nao_factual"] == 1
    assert not relatorio["revisao_semantica_automatizada"]
