"""Regressões integradas para nomes, extensão e repetição de arquivos."""

from __future__ import annotations

import os

import pytest

from mente_laylay.arquivos.nome_natural import (
    limpar_nome_arquivo_natural,
    nome_com_nova_extensao_textual,
)
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.arquivos.transacao_arquivos import executar_transacao_arquivo
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_contexto_unificado_precoce,
)
from mente_laylay.cognicao.esclarecimento_operacional import (
    detectar_esclarecimento_operacional,
    registrar_esclarecimento_operacional,
    resolver_esclarecimento_operacional,
)
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_semantica import (
    resolver_continuidade_semantica,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().replace("ã", "a").replace("á", "a")


def _estrutura_arquivo(caminho: str) -> dict:
    return {
        "arquivo_nome": os.path.basename(caminho),
        "caminho": caminho,
        "tipo": "arquivo",
        "tipo_arquivo": "texto",
    }


def test_resposta_exata_remove_moldura_e_respeita_extensao_markdown() -> None:
    pendencia = detectar_esclarecimento_operacional("cria um arquivo de texto")
    estado = registrar_esclarecimento_operacional({}, pendencia)

    resultado = resolver_esclarecimento_operacional(
        "um chamado teste laylay.md",
        estado,
    )

    assert resultado == {
        "tipo": "executar",
        "intencao": {
            "intent": "CREATE_FILE",
            "params": {
                "tipo_arquivo": "markdown",
                "alvo": "teste laylay.md",
                "origem": "esclarecimento_operacional",
            },
        },
    }


@pytest.mark.parametrize(
    ("fala", "esperado"),
    [
        ("um arquivo de texto chamado notas.txt", "notas.txt"),
        ("um de texto chamado carlos", "carlos"),
        ("o nome é ideias.md", "ideias.md"),
        ("Um Dia Qualquer.md", "Um Dia Qualquer.md"),
    ],
)
def test_nome_natural_remove_so_a_moldura_linguistica(
    fala: str,
    esperado: str,
) -> None:
    assert limpar_nome_arquivo_natural(fala) == esperado


@pytest.mark.parametrize(
    "fala",
    [
        "apaga o um chamado teste laylay.md",
        "apaga o um chamado teste laylay md",
    ],
)
def test_exclusao_preserva_nome_real_e_extensao(fala: str) -> None:
    resultado = detectar_intencao_arquivos(
        fala,
        params_cb=lambda **params: params,
        estado_mental={},
    )

    assert resultado is not None
    assert resultado["intent"] == "DELETE_ITEM"
    assert resultado["params"]["alvo"] == "teste laylay.md"


def test_mudanca_de_extensao_usa_referencia_exata_e_intent_canonico(tmp_path) -> None:
    origem = tmp_path / "teste laylay.txt"
    origem.write_text("# conteúdo", encoding="utf-8")

    decisao = resolver_continuidade_semantica(
        "muda o tipo dele de .txt para um .md",
        mente={"ultima_habilidade": "arquivos"},
        estrutura_arquivo=_estrutura_arquivo(str(origem)),
    )

    assert decisao.intent == "FILE_TRANSACTION"
    assert decisao.dominio == "arquivo"
    assert decisao.params == {
        "operacao": "renomear",
        "origem": str(origem),
        "novo_nome": "teste laylay.md",
    }
    assert decisao.confianca >= 0.90


@pytest.mark.parametrize(
    "fala",
    [
        "não muda o tipo dele para md",
        "como eu mudaria o tipo dele para md?",
        "se eu mudasse o tipo dele para md",
    ],
)
def test_negacao_e_hipotese_nao_autorizam_renomeacao(fala: str) -> None:
    decisao = resolver_continuidade_semantica(
        fala,
        mente={"ultima_habilidade": "arquivos"},
        estrutura_arquivo=_estrutura_arquivo("C:/Downloads/teste.txt"),
    )

    assert decisao.intent == ""
    assert decisao.operacao == "BLOQUEAR_SEM_AUTORIZACAO"


def test_transacao_renomeia_e_confere_o_estado_final(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS", str(tmp_path))
    origem = tmp_path / "teste.txt"
    destino = tmp_path / "teste.md"
    origem.write_text("conteúdo", encoding="utf-8")

    resultado = executar_transacao_arquivo({
        "operacao": "renomear",
        "origem": str(origem),
        "novo_nome": destino.name,
    })

    assert resultado.sucesso is True
    assert resultado.status == "renomeado"
    assert not origem.exists()
    assert destino.read_text(encoding="utf-8") == "conteúdo"

    repetido = executar_transacao_arquivo({
        "operacao": "renomear",
        "origem": str(destino),
        "novo_nome": destino.name,
    })
    assert repetido.sucesso is True
    assert repetido.status == "ja_com_mesmo_nome"


def test_extensao_executavel_fica_limitada_a_tipos_textuais_conhecidos() -> None:
    assert nome_com_nova_extensao_textual("nota.txt", ".md") == "nota.md"
    assert nome_com_nova_extensao_textual("nota.txt", ".exe") == ""
    assert nome_com_nova_extensao_textual("programa.exe", ".md") == ""


def test_falha_de_exclusao_pode_ser_retentada_sem_repetir_sucesso_ou_pendencia() -> None:
    base = {
        "ultima_acao_intent": "DELETE_ITEM",
        "ultima_acao_params": {"alvo": "teste laylay.md", "tipo": "arquivo"},
        "ultima_acao_ok": False,
        "ultima_acao_confirmada": False,
    }

    assert resolver_repeticao_ultima_acao(
        "tenta de novo",
        {**base, "ultima_acao_status": "falha_execucao"},
        _normalizar,
    ) == {
        "intent": "DELETE_ITEM",
        "params": {"alvo": "teste laylay.md", "tipo": "arquivo"},
    }
    assert resolver_repeticao_ultima_acao(
        "tenta de novo",
        {**base, "ultima_acao_status": "aguardando_confirmacao"},
        _normalizar,
    ) is None
    assert resolver_repeticao_ultima_acao(
        "tenta de novo",
        {
            **base,
            "ultima_acao_status": "movido_para_lixeira",
            "ultima_acao_ok": True,
            "ultima_acao_confirmada": True,
        },
        _normalizar,
    ) is None


def test_resultado_file_transaction_publica_contexto_temporario_canonico(tmp_path) -> None:
    origem = tmp_path / "teste.txt"
    destino = tmp_path / "teste.md"
    estado = registrar_resultado_execucao(
        {},
        ResultadoAcao(
            intent="FILE_TRANSACTION",
            status="renomeado",
            alvo=origem.name,
            params={
                "operacao": "renomear",
                "origem": str(origem),
                "novo_nome": destino.name,
            },
            executou=True,
            confirmado=True,
        ),
        "muda o tipo dele de .txt para um .md",
        True,
    )

    continuidade = estado["continuidade_geral"]
    assert continuidade["dominio_ativo"] == "arquivos"
    assert continuidade["dominios"]["arquivos"]["intent"] == "FILE_TRANSACTION"
    assert continuidade["dominios"]["arquivos"]["params"]["novo_nome"] == "teste.md"
    assert "memoria_persistente" not in estado


def test_fluxo_precoce_executa_pelo_porteiro_e_notifica_aprendizado(tmp_path) -> None:
    origem = tmp_path / "teste.txt"
    estrutura = _estrutura_arquivo(str(origem))
    executadas: list[dict] = []
    resultados: list[tuple] = []
    aprendizados: list[tuple] = []

    def resolver(texto: str) -> dict | None:
        return resolver_continuidade_semantica(
            texto,
            mente={"ultima_habilidade": "arquivos"},
            estrutura_arquivo=estrutura,
        ).para_intencao()

    tratado, etapa = processar_contexto_unificado_precoce(
        {
            "_resolver_comando_contextual_forcado": resolver,
            "executar_intencao": lambda intencao, _texto: executadas.append(intencao) or True,
            "_registrar_resultado_execucao": lambda *args, **kwargs: resultados.append((args, kwargs)),
            "_registrar_autoaprimoramento": lambda *args, **kwargs: aprendizados.append((args, kwargs)),
        },
        "muda o tipo dele de .txt para um .md",
    )

    assert tratado is True
    assert etapa == "continuidade_geral"
    assert executadas[0]["intent"] == "FILE_TRANSACTION"
    assert resultados
    assert aprendizados
    assert aprendizados[0][1]["contexto"] == "continuidade contextual de geral"


def test_mapa_vivo_explica_capacidade_limite_e_evidencia() -> None:
    mapa = MapaHabilidadesRuntime()

    assert mapa.consultar("FILE_TRANSACTION")["disponivel"] is True
    contexto = mapa.contexto_para_prompt("muda a extensão do arquivo")
    assert "- arquivos [disponivel]" in contexto
    assert "não uma conversão automática do conteúdo" in contexto

    resposta = mapa.responder_pergunta_capacidade(
        "você consegue mudar a extensão de um arquivo?",
    )
    assert "Consigo renomear" in resposta
    assert "não converte o conteúdo" in resposta
    assert "confere o caminho de origem e o novo nome" in resposta
