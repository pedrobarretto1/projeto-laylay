from __future__ import annotations

from types import SimpleNamespace

import pytest

import mente_laylay.autonomia.adaptador_resultado as modulo_adaptador
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import _motivo_contrato_invalido


@pytest.mark.parametrize(
    ("texto", "comando"),
    (
        (
            "Pesquisa por documentação oficial do Python.",
            {"intent": "SEARCH", "params": {"query": "documentação oficial do Python"}},
        ),
        (
            "O que você consegue identificar?",
            {"intent": "VISION_QUERY", "params": {}},
        ),
    ),
)
def test_leitura_explicita_chega_ao_executor_antes_da_conversa(
    texto: str,
    comando: dict,
) -> None:
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple] = []
    estado = SimpleNamespace(mental={})
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "detectar_intencao_deterministica": lambda recebido: (
                comando if recebido == texto else None
            ),
            "executar_intencao": lambda detectado, original: (
                execucoes.append((detectado, original)) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
            "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
                AssertionError("a leitura explícita não pode cair na conversa/LLM")
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(texto) is True
    assert execucoes == [(comando, texto)]
    assert registros[0][1]["origem"] == "prioritario_leitura_deterministica"


def test_barreira_de_leitura_nao_promove_outro_intent() -> None:
    estado = SimpleNamespace(mental={})
    resolucoes: list[tuple[str, str]] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "APP_OPEN",
                "params": {"nome_app": "Opera"},
            },
            "resolver_comando_natural": lambda texto, origem: (
                resolucoes.append((texto, origem)) or (None, "")
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("eu estava falando do Opera") is False
    assert resolucoes == [
        ("eu estava falando do Opera", "prioritario-linguagem-natural"),
    ]


def test_consulta_de_capacidade_preserva_negacao_de_execucao() -> None:
    fala = (
        "Consigo abrir programas e organizar janelas visíveis, sim. "
        "Como você só perguntou, não abri nem movi nada."
    )

    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"comandos": [], "requer_execucao": False},
        origem="canal_voz",
    )

    assert resultado["fala"] == fala
    assert resultado["problemas"] == []


@pytest.mark.parametrize(
    ("texto", "trecho"),
    [
        ("Talvez fosse legal abrir o Spotify.", "possibilidade"),
        ("Talvez eu apague o roteiro correcao.txt depois.", "possibilidade"),
        ("Não abra o Spotify.", "não executei"),
        ("Não apague o roteiro correcao.txt.", "não executei"),
    ],
)
def test_mencao_operacional_sem_autorizacao_recebe_ack_local(
    texto: str,
    trecho: str,
) -> None:
    falas: list[str] = []
    runtime = ComandosImediatosRuntime(namespace_getter=lambda: {
        "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
    }, loop_getter=lambda: None)

    assert runtime.processar_prioritarios(texto) is True
    assert len(falas) == 1
    assert trecho in falas[0].casefold()


def test_consulta_nomeada_usa_caminho_exato_do_arquivo_recente(tmp_path) -> None:
    arquivo = tmp_path / "carlos" / "roteiro correcao.txt"
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": arquivo.name,
            "caminho": str(arquivo),
        },
    }

    assert detectar_intencao_arquivos(
        "Onde o roteiro correcao.txt fica?",
        params_cb=lambda **kwargs: kwargs,
        estado_mental=estado,
        normalizar_texto=lambda valor: str(valor).casefold(),
    ) == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "roteiro correcao.txt",
            "referencia_caminho": str(arquivo),
            "alvo": "roteiro correcao.txt",
        },
    }


def test_playlist_ja_preenchida_nao_recebe_fala_de_dispositivo_desligado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    falas: list[str] = []
    monkeypatch.setattr(
        modulo_adaptador,
        "fala_por_estado_acao",
        lambda *_args, **_kwargs: "fallback que não deve vencer",
    )
    adaptador = AdaptadorResultadoOperacional(
        {"intent": "PLAYLIST_ADD"},
        {"playlist": "roteiro teste"},
        "tenta de novo",
        "pc_a",
        {"falar_com_lipsync": lambda fala, *_args: falas.append(fala)},
    )

    adaptador.falar_por_status(
        "playlist_musica_ja_existia",
        "A faixa já estava na playlist.",
        alvo="roteiro teste",
    )

    assert falas == [
        "A faixa já estava na playlist roteiro teste; mantive uma só cópia.",
    ]
    assert "desligado" not in falas[0].casefold()


def test_consulta_de_caminho_rejeita_ordem_aleatoria_anexada_pela_autoria() -> None:
    resultado = ResultadoAcao(
        intent="FILE_SEARCH",
        status="caminho_encontrado",
        alvo="roteiro correcao.txt",
        executou=True,
        confirmado=True,
    )

    motivo = _motivo_contrato_invalido(
        (
            "O arquivo roteiro correcao.txt fica em Downloads. "
            "Não fale, não chame, só deixe o arquivo lá e vá embora."
        ),
        resultado=resultado,
        classe="sucesso",
        status_declarado="caminho_encontrado",
        alvo_declarado="roteiro correcao.txt",
    )

    assert motivo == "instrucao_alheia_ao_resultado"
