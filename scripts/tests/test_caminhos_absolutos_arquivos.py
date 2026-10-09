"""Identidade de caminho literal antes de referências e busca por basename."""

from __future__ import annotations

import os

import pytest

from mente_laylay.arquivos.arquivos_sistema import resolver_caminho
from mente_laylay.arquivos.contexto_execucao import resolver_referencia_arquivo_contextual
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.memoria_mental.continuidade_contexto import registrar_estrutura_arquivo_recente
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime


ALVO = r"C:\Users\pbarr\Downloads\pasta organizada\projeto lay\p16 teste\prova.txt"
ANTIGO = r"C:\Users\pbarr\Downloads\outro alvo\prova.txt"


def _estado() -> dict:
    return registrar_estrutura_arquivo_recente({}, {
        "tipo": "arquivo", "caminho": ANTIGO, "arquivo_nome": "prova.txt",
    })


def _detectar(texto: str, estado: dict | None = None) -> dict | None:
    return detectar_intencao_arquivos(
        texto, params_cb=lambda **params: params, estado_mental=estado or {},
    )


@pytest.mark.parametrize("aspas", ["", '"', "'", "“"])
@pytest.mark.parametrize("prefixo,intent,campo", [
    ("Leia ", "FILE_READ", "caminho"),
    ("Abra ", "FILE_OPEN_RESULT", "caminho"),
    ("apaga o arquivo ", "DELETE_ITEM", "alvo"),
])
def test_caminho_literal_nao_herda_outro_arquivo_de_mesmo_basename(
    aspas: str, prefixo: str, intent: str, campo: str,
) -> None:
    fechado = "”" if aspas == "“" else aspas
    resultado = _detectar(prefixo + aspas + ALVO + fechado, _estado())
    assert resultado is not None
    assert resultado["intent"] == intent
    assert resultado["params"][campo] == ALVO, "primeira fronteira: identidade literal precede basename recente"
    assert resultado["params"].get("referencia_contextual") is not True


@pytest.mark.parametrize("alvo", [ALVO, ALVO[:-4] + ".md", ALVO[:-4]])
@pytest.mark.parametrize("prefixo,intent", [("Leia ", "FILE_READ"), ("Abra ", "FILE_OPEN_RESULT")])
def test_leitura_e_abertura_de_caminho_literal_independem_de_antecedente(
    alvo: str, prefixo: str, intent: str,
) -> None:
    resultado = _detectar(prefixo + alvo)
    assert resultado is not None, "pedido com caminho exato não depende de índice ou memória"
    assert resultado["intent"] == intent
    assert resultado["params"]["caminho"] == alvo


@pytest.mark.parametrize("prefixo", [
    "Escreva Conteúdo preservado no arquivo ",
    "Escreva Conteúdo preservado dentro do arquivo ",
    "Acrescente Conteúdo preservado no arquivo ",
    "Acrescente Conteúdo preservado dentro do arquivo ",
])
@pytest.mark.parametrize("envolver", [False, True])
def test_escrita_e_append_separam_conteudo_do_caminho_absoluto(prefixo: str, envolver: bool) -> None:
    argumento = '"' + ALVO + '"' if envolver else ALVO
    resultado = _detectar(prefixo + argumento, _estado())
    assert resultado is not None
    assert resultado["intent"] == "CREATE_FILE"
    assert resultado["params"]["alvo"] == ALVO
    assert resultado["params"]["conteudo"] == "Conteúdo preservado"
    assert resultado["params"]["editar_existente"] is True
    assert resultado["params"].get("modo_escrita", "overwrite") == (
        "append" if prefixo.startswith("Acrescente") else "overwrite"
    )


@pytest.mark.parametrize("envolver", [False, True])
def test_conteudo_entre_aspas_nao_e_moldura_de_linha_na_escrita(envolver: bool) -> None:
    argumento = '"' + ALVO + '"' if envolver else ALVO
    resultado = _detectar(f'Acrescente "LINHA ADICIONAL" no arquivo {argumento}')
    assert resultado["params"]["conteudo"] == "LINHA ADICIONAL"


def test_linha_sem_aspas_continua_sendo_moldura_natural_do_append() -> None:
    resultado = _detectar(f'Acrescente a linha ADICIONAL no arquivo "{ALVO}"')
    assert resultado["params"]["conteudo"] == "ADICIONAL"


@pytest.mark.parametrize("pedido", [
    'Acrescente "LINHA ADICIONAL" dentro do arquivo prova.txt',
    'Acrescente "LINHA ADICIONAL" nele',
    'Acrescente "LINHA ADICIONAL"',
    "Acrescente 'texto literal' nele",
])
def test_literal_citado_tambem_e_preservado_na_continuidade(pedido: str) -> None:
    resultado = _detectar(pedido, _estado())
    assert resultado["params"]["alvo"] == ANTIGO
    assert resultado["params"]["conteudo"] == (
        "texto literal" if "texto literal" in pedido else "LINHA ADICIONAL"
    )


@pytest.mark.parametrize("texto", [
    ALVO,
    "Você consegue ler " + ALVO + "?",
    "Como eu escrevo texto no arquivo " + ALVO + "?",
    "Não leia " + ALVO,
    "Se eu pedir para abrir " + ALVO,
    "Leia \"" + ALVO,
    "Leia ”" + ALVO + "“",
    "Escreva teste no arquivo \"" + ALVO,
    "Abra \"" + ALVO + "'",
])
def test_mencao_negacao_e_aspas_incoerentes_nao_criam_rota_literal(texto: str) -> None:
    assert _detectar(texto, _estado()) is None


@pytest.mark.parametrize("prefixo,intent", [("Leia ", "FILE_READ"), ("Abra ", "FILE_OPEN_RESULT")])
def test_basename_e_pronome_preservam_continuidade_existente(prefixo: str, intent: str) -> None:
    por_nome = _detectar(prefixo + "prova.txt", _estado())
    por_pronome = _detectar(prefixo + "ele", _estado())
    assert por_nome["intent"] == por_pronome["intent"] == intent
    assert por_nome["params"]["caminho"] == por_pronome["params"]["caminho"] == ANTIGO


def test_resolvedor_existente_preserva_caminho_longo_e_aspas_pareadas() -> None:
    if os.name != "nt":
        pytest.skip("normalização nativa Windows")
    assert resolver_caminho(ALVO) == ALVO
    assert resolver_caminho('"' + ALVO + '"') == ALVO


def test_alias_txt_contextual_nao_substitui_diretorio_literal(tmp_path) -> None:
    recente = tmp_path / "outro alvo" / "prova"
    recente.parent.mkdir()
    recente.write_text("controle", encoding="utf-8")
    alvo = str(tmp_path / "pedido explicito" / "prova.txt")
    contexto = {
        "ultimo_arquivo_contextual": lambda: str(recente),
        "resolver_caminho": lambda valor: valor,
    }
    assert resolver_referencia_arquivo_contextual(contexto, alvo, "arquivo") == alvo
    assert resolver_referencia_arquivo_contextual(contexto, "prova.txt", "arquivo") == str(recente)


@pytest.mark.parametrize("intent", ["FILE_READ", "FILE_OPEN_RESULT", "CREATE_FILE"])
def test_catalogo_vivo_de_arquivos_informa_invocacao_por_caminho(intent: str) -> None:
    capacidade = MapaHabilidadesRuntime().snapshot()["capacidades"][intent]
    assert capacidade["disponivel"] is True
    assert "caminho" in " ".join(capacidade["invocacao_natural"])
    assert "raízes" in capacidade["limites"]


@pytest.mark.parametrize("verbo", ["ler", "escrever"])
def test_pergunta_natural_sobre_caminho_explicita_uso_e_limite_sem_agir(verbo: str) -> None:
    texto = f"Você consegue {verbo} um arquivo pelo caminho completo?"
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False
    resposta = MapaHabilidadesRuntime().responder_pergunta_capacidade(texto, turno=turno)
    assert "caminho" in resposta
    assert "pedido" in resposta
    assert _detectar(texto) is None


@pytest.mark.parametrize("verbo,intent", [("ler", "FILE_READ"), ("escrever", "CREATE_FILE")])
def test_pergunta_sobre_caminho_respeita_indisponibilidade_da_operacao(verbo: str, intent: str) -> None:
    mapa = MapaHabilidadesRuntime()
    mapa.registrar_resultado({"intent": intent, "status": "indisponivel", "executou": False})
    texto = f"Você consegue {verbo} um arquivo pelo caminho completo?"
    resposta = mapa.responder_pergunta_capacidade(texto, turno=classificar_modalidade_turno(texto))
    assert "indisponível" in resposta
    assert not resposta.startswith("Consigo")
