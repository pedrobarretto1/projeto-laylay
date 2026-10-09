import pytest

from mente_laylay.personalidade.autoria_conversacional import criar_fala_autoral
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
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


@pytest.mark.parametrize("fala", [
    "Você é um fracasso.",
    "Ninguém te aguenta.",
    "Sua inteligência é limitada.",
])
def test_autoria_conversacional_rejeita_ataque_pessoal(fala: str) -> None:
    resultado = criar_fala_autoral(
        "boiola", "Essa provocação passou do ponto.",
        enviar_mensagem=lambda *_args, **_kwargs: fala,
    )

    assert resultado.usada_llm is False
    assert resultado.motivo_fallback == "ataque_pessoal"
    assert resultado.fala == "Essa provocação passou do ponto."


@pytest.mark.parametrize("fala", [
    "Você é muito idiota.",
    "Você é completamente incapaz.",
    "Você é um fracassado.",
    "Você é uma pessoa inútil.",
    'A frase "você é um fracasso" é ofensiva, mas também é verdade.',
    'A expressão "você é um fracasso" é ofensiva, porém é verdadeira.',
    "Não acho que você é um fracasso. Você é incapaz.",
])
def test_ataque_explicito_ampliado_nao_e_aprovado_por_autoria_ou_qualidade(
    fala: str,
) -> None:
    autoria = criar_fala_autoral(
        "boa tarde", "Essa provocação passou do ponto.",
        enviar_mensagem=lambda *_args, **_kwargs: fala,
    )
    qualidade = avaliar_qualidade_comunicacao("boa tarde", fala)

    assert autoria.usada_llm is False
    assert autoria.motivo_fallback == "ataque_pessoal"
    assert qualidade["aceita"] is False
    assert "ataque_pessoal" in qualidade["problemas_bloqueantes"]


@pytest.mark.parametrize("fala", [
    "Você não é um fracasso.",
    "Não acho que você é um fracasso.",
    "Essa tentativa foi muito ruim.",
    'A frase "você é um fracasso" é ofensiva e não descreve a pessoa.',
    'A frase "você é um fracasso" é ofensiva, mas não é verdade.',
])
def test_critica_de_ato_mencao_critica_e_negacao_preservam_fala_legitima(
    fala: str,
) -> None:
    autoria = criar_fala_autoral(
        "boa tarde", "Essa tentativa passou do ponto.",
        enviar_mensagem=lambda *_args, **_kwargs: fala,
    )
    qualidade = avaliar_qualidade_comunicacao("boa tarde", fala)

    assert autoria.usada_llm is True
    assert autoria.fala == fala
    assert qualidade["aceita"] is True


def test_qualidade_comunicacao_bloqueia_ataque_pessoal_sem_bloquear_deboche_de_ato() -> None:
    ataque = avaliar_qualidade_comunicacao("boiola", "Você é um fracasso.")
    deboche = avaliar_qualidade_comunicacao(
        "boiola", "Você chegou distribuindo caos de graça hoje, né?",
    )

    assert ataque["aceita"] is False
    assert "ataque_pessoal" in ataque["problemas_bloqueantes"]
    assert deboche["aceita"] is True


def test_mencao_critica_de_ofensa_citada_nao_e_ataque_ao_usuario() -> None:
    fala = 'A frase "você é um fracasso" é ofensiva e não descreve a pessoa.'
    autoria = criar_fala_autoral(
        'O que significa "você é um fracasso"?', "É uma ofensa.",
        enviar_mensagem=lambda *_args, **_kwargs: fala,
    )
    qualidade = avaliar_qualidade_comunicacao(
        'O que significa "você é um fracasso"?', fala,
    )

    assert autoria.usada_llm is True
    assert qualidade["aceita"] is True


@pytest.mark.parametrize("fala", [
    '"Você é um fracasso."',
    'A frase "você é um fracasso" é verdade.',
    'A frase "você é um fracasso" é ofensiva. Você é incapaz.',
])
def test_ataque_pessoal_fora_de_citacao_critica_continua_bloqueado(fala: str) -> None:
    qualidade = avaliar_qualidade_comunicacao("boiola", fala)

    assert "ataque_pessoal" in qualidade["problemas_bloqueantes"]


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


@pytest.mark.parametrize("estado", [
    "__LAYLAY_LLM_OCUPADA__", "__LAYLAY_LLM_TIMEOUT__",
    "__LAYLAY_LLM_INDISPONIVEL__", "LAYLAY LLM OCUPADA.",
])
def test_autoria_distingue_estado_tecnico_de_fala_do_modelo(estado) -> None:
    resultado = criar_fala_autoral(
        "Estou perguntando sobre o documento, não sobre o aplicativo.",
        "Ainda não confirmei qual documento está aberto.",
        enviar_mensagem=lambda *_args, **_kwargs: estado,
    )

    assert resultado.usada_llm is False
    assert resultado.fala == "Ainda não confirmei qual documento está aberto."
    assert resultado.motivo_fallback == "estado_tecnico_llm"


@pytest.mark.parametrize("bruto", ["", "{}", '{"fala":""}', "Sim"])
def test_autoria_mantem_fala_invalida_para_conteudo_sem_fala_util(bruto) -> None:
    resultado = criar_fala_autoral(
        "Qual documento está aberto?", "Ainda não confirmei o documento.",
        enviar_mensagem=lambda *_args, **_kwargs: bruto,
    )
    assert resultado.usada_llm is False
    assert resultado.motivo_fallback == "fala_invalida"


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


def test_fluxo_real_nao_entrega_ataque_pessoal_da_autoria_final() -> None:
    chamadas = []

    def modelo(*_args, **_kwargs):
        chamadas.append(1)
        if len(chamadas) == 1:
            return '{"fala":"Tá.","comandos":[]}'
        return '{"fala":"Você é um fracasso.","comandos":[]}'

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
    assert resultado["fala"]
    assert "fracasso" not in resultado["fala"].casefold()


def test_fluxo_real_repara_ataque_pessoal_da_resposta_principal() -> None:
    chamadas = []

    def modelo(*_args, **_kwargs):
        chamadas.append(1)
        return '{"fala":"Essa provocação passou do ponto.","comandos":[]}'

    resultado = preparar_resposta_para_execucao(
        "boiola",
        '{"fala":"Você é um fracasso.","comandos":[]}',
        enviar_mensagem_cb=modelo,
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_comunicacao={"mensagens": []},
        log=lambda *_args: None,
    )

    assert len(chamadas) == 1
    assert resultado["fala"] == "Essa provocação passou do ponto."


@pytest.mark.parametrize("fala", [
    "Você é muito idiota.",
    'A frase "você é um fracasso" é ofensiva, mas também é verdade.',
])
def test_fluxo_composto_repara_ataque_intensificado_ou_citado_com_endosso(
    fala: str,
) -> None:
    import json

    chamadas = []

    def modelo(*_args, **_kwargs):
        chamadas.append(1)
        return '{"fala":"Essa provocação passou do ponto.","comandos":[]}'

    resultado = preparar_resposta_para_execucao(
        "boa tarde",
        json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=modelo,
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_comunicacao={"mensagens": []},
        log=lambda *_args: None,
    )

    assert len(chamadas) == 1
    assert resultado["fala"] == "Essa provocação passou do ponto."


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
