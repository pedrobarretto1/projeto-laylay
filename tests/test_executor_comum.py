from __future__ import annotations

from mente_laylay.autonomia.executor_comum import falar_ctx


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
