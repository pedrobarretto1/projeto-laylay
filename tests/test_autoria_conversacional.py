from mente_laylay.personalidade.autoria_conversacional import criar_fala_autoral
from mente_laylay.autonomia.processamento_resposta_ia import (
    preparar_resposta_para_execucao,
)
from mente_laylay.personalidade.variacao_fala import (
    escolher_variacao,
    resetar_variacoes_para_testes,
)


def test_variacao_local_nao_repete_antes_de_esgotar_conjunto() -> None:
    resetar_variacoes_para_testes()
    opcoes = ["uma", "duas", "três"]

    escolhidas = [escolher_variacao(opcoes) for _ in range(3)]

    assert len(set(escolhidas)) == 3


def test_variacao_local_respeita_fala_recente() -> None:
    resetar_variacoes_para_testes()

    assert escolher_variacao(["repete", "muda"], evitar=["repete"]) == "muda"


def test_autoria_conversacional_entrega_fala_criada_pela_llm() -> None:
    def modelo(*_args, **_kwargs):
        return '{"fala":"Você chegou distribuindo caos de graça hoje, né?","comandos":[]}'

    resultado = criar_fala_autoral(
        "boiola",
        "Do nada? Se era provocação, capricha sem apelar pra isso.",
        enviar_mensagem=modelo,
        mensagens=[{"role": "assistant", "content": "Outra fala."}],
    )

    assert resultado.usada_llm is True
    assert resultado.fala == "Você chegou distribuindo caos de graça hoje, né?"


def test_autoria_conversacional_aceita_fala_pura_sem_envelope_json() -> None:
    def modelo(*_args, **_kwargs):
        return "Você quer romance leve ou daqueles que deixam um estrago bonito?"

    resultado = criar_fala_autoral(
        "quero um filme de romance",
        "Você prefere um romance leve ou dramático?",
        enviar_mensagem=modelo,
    )

    assert resultado.usada_llm is True
    assert resultado.fala == (
        "Você quer romance leve ou daqueles que deixam um estrago bonito?"
    )


def test_autoria_conversacional_nunca_aceita_comando() -> None:
    def modelo(*_args, **_kwargs):
        return '{"fala":"Tá bom.","comandos":[{"acao":"open_app","alvo":"opera"}]}'

    resultado = criar_fala_autoral(
        "boiola",
        "Fala segura.",
        enviar_mensagem=modelo,
    )

    assert resultado.usada_llm is False
    assert resultado.fala == "Fala segura."
    assert resultado.motivo_fallback == "comando_na_fala_conversacional"


def test_autoria_conversacional_nao_repete_fala_recente() -> None:
    def modelo(*_args, **_kwargs):
        return '{"fala":"Essa eu já disse.","comandos":[]}'

    resultado = criar_fala_autoral(
        "teste",
        "Fala segura.",
        enviar_mensagem=modelo,
        mensagens=[{"role": "assistant", "content": "Essa eu já disse."}],
    )

    assert resultado.usada_llm is False
    assert resultado.motivo_fallback == "fala_recente_repetida"


def test_fluxo_real_prefere_autoria_da_laylay_ao_bordao_local() -> None:
    chamadas = []

    def modelo(*_args, **_kwargs):
        chamadas.append(1)
        if len(chamadas) == 1:
            return '{"fala":"Tá.","comandos":[]}'
        return (
            '{"fala":"Você acordou escolhendo o caos hoje, né? Melhora essa '
            'provocação.","comandos":[]}'
        )

    resultado = preparar_resposta_para_execucao(
        "boiola",
        '{"fala":"Entendi.","comandos":[]}',
        enviar_mensagem_cb=modelo,
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_comunicacao={"mensagens": []},
        log=lambda *_args: None,
    )

    assert len(chamadas) == 2
    assert resultado["fala"] == (
        "Você acordou escolhendo o caos hoje, né? Melhora essa provocação."
    )
    assert "do nada" not in resultado["fala"].casefold()


def test_fluxo_real_nao_registra_modelo_sem_callback_quando_reparo_ja_falhou() -> None:
    logs: list[str] = []

    def modelo(*_args, **_kwargs):
        return "__LAYLAY_LLM_INDISPONIVEL__"

    resultado = preparar_resposta_para_execucao(
        "boiola",
        '{"fala":"Entendi.","comandos":[]}',
        enviar_mensagem_cb=modelo,
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_comunicacao={"mensagens": []},
        log=logs.append,
    )

    assert resultado["fala"]
    assert not any("modelo_sem_callback" in item for item in logs)
    assert any("reparo_modelo_indisponivel" in item for item in logs)
