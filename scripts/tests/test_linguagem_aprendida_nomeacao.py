"""Nomear uma entidade não ensina substituição lexical para falas futuras."""

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto


def criar_runtime(tmp_path):
    banco = MemoriaSQLite(str(tmp_path / "linguagem.sqlite"))
    falas = []
    runtime = LinguagemAprendidaRuntime(
        memoria_sqlite=banco, normalizar_texto=normalizar_texto,
        texto_social_curto=lambda _texto: False,
        falar=lambda fala, *_args: falas.append(fala), log=lambda *_args: None,
    )
    return runtime, banco, falas


@pytest.mark.parametrize("texto", [
    "Meu irmão se chama Esta.",
    "Minha irmã se chama Ana.",
    "Meu projeto se chama Aurora.",
    "O arquivo se chama Relatorio.",
])
def test_nomeacao_reflexiva_nao_autoriza_aprendizado_de_alias(tmp_path, texto):
    runtime, banco, falas = criar_runtime(tmp_path)
    assert runtime.extrair_apelido_ensinavel(texto) is None
    assert runtime.processar_aprendizado_imediato(texto) is False
    assert banco.listar_aprendizados_semanticos() == []
    assert falas == []


@pytest.mark.parametrize("texto,alias,alvo", [
    ("calc quer dizer calculadora", "calc", "calculadora"),
    ("calc chama calculadora", "calc", "calculadora"),
    ("apelido calc é calculadora", "calc", "calculadora"),
    ("quando eu falar calc é calculadora", "calc", "calculadora"),
])
def test_ensino_lexical_explicito_continua_persistindo_com_evidencia(tmp_path, texto, alias, alvo):
    runtime, banco, falas = criar_runtime(tmp_path)
    assert runtime.processar_aprendizado_imediato(texto) is True
    item = banco.listar_aprendizados_semanticos()[0]
    assert (item["gatilho"], item["valor"], item["evidencia"]) == (alias, alvo, texto)
    assert falas
    assert runtime.aplicar_apelidos("abre calc") == "abre calculadora"
