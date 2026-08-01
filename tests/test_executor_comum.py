from __future__ import annotations

from mente_laylay.autonomia.executor_comum import falar_ctx, relatar_falha_ctx


def test_falar_ctx_repassa_fala_emocao_e_nivel_sem_alterar() -> None:
    chamadas: list[tuple] = []

    falar_ctx(
        {"falar_com_lipsync": lambda *args: chamadas.append(args)},
        "Pronto, Pedro.",
        "feliz",
        3,
    )

    assert chamadas == [("Pronto, Pedro.", "feliz", 3)]


def test_falar_ctx_sem_canal_de_voz_e_inofensivo() -> None:
    falar_ctx({}, "Isso não deve falhar.")
    falar_ctx({"falar_com_lipsync": None}, "Nem isso.")


def test_relatar_falha_ctx_vincula_dominio_fase_e_turno_sem_conteudo() -> None:
    eventos: list[tuple] = []
    erro = RuntimeError("conteúdo privado")

    registrado = relatar_falha_ctx(
        {
            "_registrar_falha_tecnica": (
                lambda *args, **kwargs: eventos.append((args, kwargs))
            ),
            "turno_atual": {"id": "turno-42", "texto": "não deve sair"},
        },
        "executor",
        "falha_teste",
        erro=erro,
        dominio="arquivos",
        fase="execucao",
    )

    assert registrado is True
    assert eventos[0][0] == ("executor", "falha_teste")
    assert eventos[0][1]["erro"] is erro
    assert eventos[0][1]["dominio"] == "arquivos"
    assert eventos[0][1]["fase"] == "execucao"
    assert eventos[0][1]["turno_id"] == "turno-42"
    assert "não deve sair" not in repr(eventos)


def test_relatar_falha_ctx_nao_substitui_falha_original_se_relator_quebrar() -> None:
    def relator_quebrado(*_args, **_kwargs):
        raise RuntimeError("telemetria indisponível")

    assert relatar_falha_ctx(
        {"_registrar_falha_tecnica": relator_quebrado},
        "executor",
        "falha_teste",
    ) is False
