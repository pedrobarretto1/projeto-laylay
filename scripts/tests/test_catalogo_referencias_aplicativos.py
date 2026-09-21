"""Referência cadastrada seleciona documentação, nunca autoridade ou efeito."""
import ast
from copy import deepcopy
from pathlib import Path

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime


def mapa_da_composicao():
    """Executa a declaração e a factory reais sem iniciar serviços externos."""
    arvore = ast.parse(Path("laylay.py").read_text(encoding="utf-8-sig"))
    atribuicoes = {
        alvo.id: no for no in arvore.body if isinstance(no, ast.Assign)
        for alvo in no.targets if isinstance(alvo, ast.Name)
    }
    class Saude:
        def snapshot(self):
            return {}
    namespace = {"_criar_mapa_habilidades_runtime": MapaHabilidadesRuntime,
                 "_saude_mente_runtime": Saude()}
    # A factory precede APPS_MAP na produção: o acesso deve continuar tardio.
    for nome in ("_mapa_habilidades_runtime", "APPS_MAP"):
        modulo = ast.Module(body=[atribuicoes[nome]], type_ignores=[])
        exec(compile(modulo, "laylay.py", "exec"), namespace)
    return namespace["_mapa_habilidades_runtime"]


@pytest.mark.parametrize("nome", ["calculadora", "Krita", "Visual Studio Code", "notepad++"])
def test_composicao_recupera_documentacao_por_nome_configurado(nome):
    texto = f"como eu poderia abrir {nome}?"
    turno = classificar_modalidade_turno(texto)
    antes = deepcopy(turno)
    mapa = mapa_da_composicao()
    assert "sistema" in mapa.dominios_relevantes(texto, turno=turno)
    evidencia = mapa.evidencia_conversacional(texto, turno=turno)
    assert "sistema" in evidencia["documentacao_capacidades"]
    assert evidencia["autoriza_execucao"] is False
    assert turno == antes and turno["autoriza_execucao"] is False


def test_referencias_sao_vivas_sem_copiar_catalogo_nem_alterar_disponibilidade():
    apps = {"editor aurora": "aurora"}
    mapa = MapaHabilidadesRuntime(apps_getter=lambda: apps,
        operacional_getter=lambda: {"dominios": {"sistema": {"estado": "indisponivel"}}})
    assert "sistema" in mapa.dominios_relevantes("como abrir editor aurora?")
    assert mapa.snapshot()["dominios"]["sistema"]["estado"] == "indisponivel"
    apps.clear()
    assert "sistema" not in mapa.dominios_relevantes("como abrir editor aurora?")
    apps["editor boreal"] = "boreal"
    assert "sistema" in mapa.dominios_relevantes("como abrir editor boreal?")


@pytest.mark.parametrize("texto", ["como abrir discorde?", "como abrir kritaria?", "como abrir desconhecido?"])
def test_fragmentos_e_nomes_desconhecidos_nao_inventam_referencia(texto):
    mapa = MapaHabilidadesRuntime(apps_getter=lambda: {"discord": "discord", "krita": "krita"})
    assert "sistema" not in mapa.dominios_relevantes(texto)


def test_falha_da_fonte_nao_remove_recuperacao_existente():
    def indisponivel():
        raise RuntimeError("sem catálogo")
    mapa = MapaHabilidadesRuntime(apps_getter=indisponivel)
    assert "sistema" in mapa.dominios_relevantes("como ajustar o volume?")
    assert "arquivos" in mapa.dominios_relevantes("como criar um arquivo?")
    assert "sistema" not in mapa.dominios_relevantes("como abrir calculadora?")
