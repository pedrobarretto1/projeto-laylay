from __future__ import annotations

import threading

from mente_laylay.personalidade.orquestrador_fala_runtime import (
    OrquestradorFalaRuntime,
)


class _Estado:
    mental = {}

    def substituir(self, _nome, valor):
        self.mental = dict(valor)


def test_interacao_preserva_briefing_e_salva_so_depois_da_entrega() -> None:
    chamadas = []
    callback_adiado = []
    salvos = []

    def agendar(tipo, texto, emocao, nivel, **kwargs):
        chamadas.append((tipo, texto, dict(kwargs)))
        if kwargs.get("forcar_inicio"):
            kwargs["ao_concluir"](False, "interacao_iniciada")
        else:
            callback_adiado.append(kwargs["ao_concluir"])
        return True

    runtime = OrquestradorFalaRuntime(servicos_iniciais={
        "_threading": threading,
        "_agendar_fala_proativa": agendar,
        "_estado_compartilhado_runtime": _Estado(),
        "print": lambda *_args: None,
    })

    resultado = runtime.entregar_fala_inicial_confirmada(
        "briefing", "Seu resumo do dia.",
        adiar_se_interacao=True,
        ao_entrega_adiada=lambda: salvos.append(True),
        detalhar=True,
    )

    assert resultado == {"entregue": False, "pendente": True}
    assert salvos == []
    assert chamadas[1][2]["preservar_ate_entrega"] is True

    callback_adiado[0](True, "entregue")
    assert salvos == [True]
