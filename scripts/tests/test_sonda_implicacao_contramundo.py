"""O portão de sonda não pode aceitar recibos inexistentes ou incompletos."""

from scripts.analises.sonda_implicacao_contramundo import (
    INSTRUCAO, aprovar_seletivamente, medir_portao_seletivo, validar_saida,
)


def test_instrucao_tenta_falsificar_antes_de_aprovar() -> None:
    assert "fonte verdadeira e a alegação falsa" in INSTRUCAO
    assert "sustente o começo" in INSTRUCAO
    assert "ambas verdadeiras" in INSTRUCAO


def test_recibo_literal_e_necessario_mas_nao_e_prova_semantica() -> None:
    fonte = "A planta baixa mostra a casa vista de cima."
    localizado = validar_saida({"classe": "sustentada", "trecho_literal": fonte}, fonte)
    assert localizado["classe"] == "sustentada"
    assert localizado["prova_localizada"] is True
    assert localizado["trecho_bruto"] == fonte
    assert validar_saida({"classe": "sustentada", "trecho_literal": "vista de baixo"}, fonte)["classe"] == "invalida"
    assert validar_saida({"classe": "sem_prova", "trecho_literal": fonte}, fonte)["classe"] == "invalida"
    assert validar_saida({"classe": "sem_prova", "trecho_literal": ""}, fonte)["classe"] == "sem_prova"
    assert validar_saida({"classe": "aprovada", "trecho_literal": fonte}, fonte)["classe"] == "invalida"


def test_portao_seletivo_so_aprova_sustentacao_com_citacao_localizada() -> None:
    assert aprovar_seletivamente({"classe": "sustentada", "prova_localizada": True})
    for classe in ("contradita", "sem_prova", "invalida"):
        assert not aprovar_seletivamente({"classe": classe, "prova_localizada": True})
    assert not aprovar_seletivamente({"classe": "sustentada", "prova_localizada": False})


def test_medicao_separa_cobertura_de_falso_suporte() -> None:
    casos = (
        ("D-ok", "f", "definicao", "correta", "sustentada"),
        ("E-falso", "f", "exemplo", "extra", "sem_prova"),
    )
    def julgar(alegacao: str, _fonte: str) -> dict:
        return {"classe": "sustentada", "prova_localizada": True,
                "latencia_s": 0.1}
    relatorio = medir_portao_seletivo(casos, {"f": {"texto": "fonte"}}, julgador=julgar)
    assert relatorio["grupos"]["definicao"] == {"aceitos_corretos": 1, "sustentados": 1}
    assert relatorio["falsos_suportes"] == ["E-falso"]
    assert relatorio["aprovado_para_producao"] is False
