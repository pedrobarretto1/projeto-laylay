"""Veto independente da dependência/POS do parser, sem aprovar partições."""

import pytest

from scripts.analises import veto_superficie_sujeito_composto as modulo
from scripts.analises.gerar_indice_portilexicon_condicional import extrair_indice
from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.veto_superficie_sujeito_composto import (
    conferir_numero_condicao_curta,
    sinal_plural_sujeito_composto,
    verificar_sujeito_composto_superficial,
)


def _verificar(fonte):
    trechos = gerar_candidatos({"fonte": fonte})["candidatos"]
    assert len(trechos) == 3
    return verificar_sujeito_composto_superficial(fonte, *trechos)


def test_texto_veta_sujeito_composto_sem_receber_parser():
    for fonte in (
        "Se o aplicativo registrar a foto e a câmera e o drone pararem, "
        "a tarefa pausa.",
        "Se o robô detectar a fumaça e o sensor e a sirene falharem, "
        "o painel avisa.",
        "Se o sistema registrar o log e o usuário e o cliente confirmarem, "
        "a tarefa termina.",
    ):
        resultado = _verificar(fonte)
        assert resultado["estado"] == "sujeito_composto_possivel"
        assert resultado["autoriza_efeito"] is False


def test_sem_veto_nao_significa_que_objeto_foi_comprovado():
    for fonte in (
        "Se o robô localizar a peça e a etiqueta e a esteira parar, "
        "o painel avisa.",
        "Se o sensor salvar foto e vídeo e os servidores reiniciarem, "
        "o aviso aparece.",
    ):
        resultado = _verificar(fonte)
        assert resultado["estado"] == "sem_veto_superficial"
        assert resultado["aprovado_para_producao"] is False
        assert resultado["autoriza_efeito"] is False


def test_flexoes_plurais_de_tempo_diferente_mantem_o_veto():
    for verbo in ("pararem", "pararam", "paravam", "parassem"):
        fonte = ("Se o aplicativo registrar a foto e a câmera e o drone "
                 f"{verbo}, a tarefa pausa.")
        assert _verificar(fonte)["estado"] == "sujeito_composto_possivel"


def test_flexoes_singulares_nao_autorizam_nem_criam_veto_plural():
    for verbo in ("parar", "parou", "parava", "parasse"):
        fonte = ("Se o robô localizar a peça e a etiqueta e a esteira "
                 f"{verbo}, o painel avisa.")
        resultado = _verificar(fonte)
        assert resultado["estado"] == "sem_veto_superficial"
        assert resultado["aprovado_para_producao"] is False


def test_veto_pode_perder_cobertura_em_objeto_com_condicao_plural():
    fonte = ("Se o robô localizar a peça e a etiqueta e os sensores "
             "dispararem, o painel avisa.")
    resultado = _verificar(fonte)
    assert resultado["estado"] == "sujeito_composto_possivel"
    assert resultado["aprovado_para_producao"] is False


def test_offset_invalido_nao_gera_ausencia_de_veto_confiavel():
    fonte = ("Se o robô localizar a peça e a etiqueta e a esteira parar, "
             "o painel avisa.")
    trechos = gerar_candidatos({"fonte": fonte})["candidatos"]
    adulterado = {**trechos[1], "inicio": trechos[1]["inicio"] + 1}
    resultado = verificar_sujeito_composto_superficial(
        fonte, trechos[0], adulterado, trechos[2],
    )
    assert resultado["estado"] == "entrada_invalida"
    assert resultado["aprovado_para_producao"] is False


def test_sinal_plural_cobre_sujeitos_compostos_literais_em_dominios_distintos():
    for trecho, verbo in (
        ("o técnico e a coordenadora entrarem", "entrarem"),
        ("a câmera e o drone pararem", "pararem"),
        ("o autor e a tradutora concordarem", "concordarem"),
        ("a artista e os músicos saírem", "saírem"),
    ):
        sinal = sinal_plural_sujeito_composto(trecho)
        assert sinal["estado"] == "indicio_plural_explicito"
        assert sinal["marcador_verbal"] == verbo
        assert sinal["aprovado_para_producao"] is False
        assert sinal["autoriza_efeito"] is False


def test_sinal_plural_nao_inventa_cobertura_fora_da_estrutura_curta():
    for trecho in (
        "o técnico e a coordenadora entrar",
        "a coordenadora entrarem",
        "o técnico experiente e a coordenadora entrarem",
        "o técnico e a coordenadora entrarem, depois",
        "o técnico e a coordenadora entrarem ou saírem",
    ):
        sinal = sinal_plural_sujeito_composto(trecho)
        assert sinal["estado"] == "sem_sinal_plural_confiavel"
        assert sinal["aprovado_para_producao"] is False


def test_morfologia_independente_cobre_irregular_sem_aceitar_sufixo_inventado():
    # A fonte lexical mostra que "forem" é plural; a antiga expectativa de
    # ausência de sinal, baseada apenas no sufixo, não era o contrato correto.
    irregular = sinal_plural_sujeito_composto(
        "o técnico e a coordenadora forem",
    )
    assert irregular["estado"] == "indicio_plural_explicito"
    assert irregular["marcador_verbal"] == "forem"

    inventado = sinal_plural_sujeito_composto(
        "o técnico e a coordenadora trubarem",
    )
    assert inventado["estado"] == "sem_sinal_plural_confiavel"
    assert inventado["autoriza_efeito"] is False


def test_indice_morfologico_distingue_convergencia_e_divergencia_de_numero():
    exemplos = {
        "o técnico e a coordenadora entrarem": "numero_convergente",
        "o técnico e a coordenadora forem": "numero_convergente",
        "o alicate e a aprendiz chegar": "numero_divergente",
        "a coordenadora entrarem": "numero_divergente",
        "a aprendiz chegar": "numero_convergente",
        "os motoristas pararem": "numero_convergente",
        "o técnico e a coordenadora trubarem": "sem_analise",
        "o técnico experiente e a coordenadora entrarem": "sem_analise",
    }
    for trecho, esperado in exemplos.items():
        resultado = conferir_numero_condicao_curta(trecho)
        assert resultado["estado"] == esperado, trecho
        assert resultado["aprovado_para_producao"] is False
        assert resultado["autoriza_efeito"] is False


def test_indice_ausente_ou_corrompido_nao_vira_sinal_gramatical(
    monkeypatch, tmp_path,
):
    ausente = tmp_path / "ausente.tsv"
    monkeypatch.setattr(modulo, "_CAMINHO_INDICE_MORFOLOGICO", ausente)
    for caminho in (ausente, tmp_path / "corrompido.tsv"):
        if caminho != ausente:
            caminho.write_text("entrarem\tP\n", encoding="utf-8")
            monkeypatch.setattr(modulo, "_CAMINHO_INDICE_MORFOLOGICO",
                                caminho)
        resultado = conferir_numero_condicao_curta(
            "o técnico e a coordenadora entrarem",
        )
        assert resultado["estado"] == "recurso_morfologico_indisponivel"
        assert resultado["autoriza_efeito"] is False


def test_gerador_rejeita_fonte_externa_nao_congelada():
    with pytest.raises(ValueError, match="hash congelado"):
        extrair_indice(b"forma\tlema\tNumber=Plur")
