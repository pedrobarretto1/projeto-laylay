"""Protocolo diagnóstico: validade, sequência e distância ausente são explícitas."""
import pytest
from scripts.diagnosticar_sensores_usb import interpretar_linha_distancia

LINHA = "DIST 1 27 FRENTE 48 VALIDA 120 41 0 BORDA 49 VALIDA 105 86 0"


def test_dois_enderecos_tem_distancia_e_idade_independentes():
    r = interpretar_linha_distancia(LINHA, 27)
    assert r["frente"]["mm"] == 120 and r["borda"]["mm"] == 105
    assert r["frente"]["idade_ms"] == 41 and r["borda"]["idade_ms"] == 86


@pytest.mark.parametrize("estado", ["INVALIDA", "EXPIRADA", "AUSENTE", "ERRO_I2C", "AGUARDANDO"])
def test_ausencia_de_medida_nao_e_caminho_livre(estado):
    r = interpretar_linha_distancia(LINHA.replace("VALIDA 120 41 0", f"{estado} -1 41 255"), 27)
    assert r["frente"]["mm"] is None and r["borda"]["mm"] == 105


@pytest.mark.parametrize("linha", [LINHA.replace("DIST 1 27", "DIST 1 26"),
    LINHA.replace("FRENTE 48", "FRENTE 49"), LINHA + " extra",
    LINHA.replace("120 41 0", "120 301 0"), LINHA.replace("120 41 0", "120 41 2"),
    LINHA.replace("120 41 0", "-1 41 0"), LINHA.replace("VALIDA 120", "INVALIDA 120")])
def test_dado_incoerente_ou_nao_correlacionado_e_rejeitado(linha):
    with pytest.raises(ValueError):
        interpretar_linha_distancia(linha, 27)
