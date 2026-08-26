from __future__ import annotations

from mente_laylay.cognicao import composicao_turno


def test_composicao_turno_filtra_e_congela_servicos(monkeypatch) -> None:
    capturas = []
    estado_runtime = object()
    normalizador_original = lambda texto: texto  # noqa: E731
    servicos = {
        "_estado_compartilhado_runtime": estado_runtime,
        "_normalizar_texto_com_apelidos": normalizador_original,
        "SEGREDO_FORA_DO_TURNO": "não reter",
    }

    def substituir(nome, retorno):
        def chamada(namespace_getter, *args, **kwargs):
            capturas.append((nome, namespace_getter(), args, kwargs))
            return retorno
        monkeypatch.setattr(composicao_turno, nome, chamada)

    substituir("iniciar_planejamento_turno", {"inicio": True})
    substituir("atualizar_planejamento_turno", {"fase": "executado"})
    substituir("verificar_fala_do_turno", {"fala": "oi"})
    substituir("registrar_leitura_semantica_principal", {"valida": True})

    runtime = composicao_turno.ComposicaoTurnoRuntime(servicos=servicos)
    servicos["_normalizar_texto_com_apelidos"] = lambda _texto: "mudou"
    servicos["novo_servico"] = object()

    assert runtime.iniciar("oi", origem="terminal") == {"inicio": True}
    assert runtime.atualizar("executado", comandos=[{"intent": "TESTE"}]) == {
        "fase": "executado"
    }
    assert runtime.verificar_fala("oi", origem="teste") == {"fala": "oi"}
    assert runtime.registrar_leitura_semantica("oi", {"valida": True}) == {
        "valida": True
    }

    for _, snapshot, _, _ in capturas:
        assert snapshot["_estado_compartilhado_runtime"] is estado_runtime
        assert snapshot["_normalizar_texto_com_apelidos"] is normalizador_original
        assert "SEGREDO_FORA_DO_TURNO" not in snapshot
        assert "novo_servico" not in snapshot
    assert "SEGREDO_FORA_DO_TURNO" not in runtime.servicos_registrados
    chamada_inicio = next(item for item in capturas if item[0] == "iniciar_planejamento_turno")
    assert chamada_inicio[3]["origem"] == "terminal"


def test_composicao_turno_encaminha_argumentos_sem_alterar_contrato(monkeypatch) -> None:
    recebidos = {}

    def atualizar(_namespace_getter, fase, *, comandos, erros, fala):
        recebidos.update(fase=fase, comandos=comandos, erros=erros, fala=fala)
        return recebidos

    def verificar(_namespace_getter, fala, *, origem):
        return {"fala": fala, "origem": origem}

    monkeypatch.setattr(composicao_turno, "atualizar_planejamento_turno", atualizar)
    monkeypatch.setattr(composicao_turno, "verificar_fala_do_turno", verificar)
    runtime = composicao_turno.ComposicaoTurnoRuntime(servicos={})

    assert runtime.atualizar(
        "resposta_planejada", comandos=(1,), erros=("erro",), fala="pronto",
    ) == {
        "fase": "resposta_planejada",
        "comandos": (1,),
        "erros": ("erro",),
        "fala": "pronto",
    }
    assert runtime.verificar_fala("pronto", origem="ia_final") == {
        "fala": "pronto",
        "origem": "ia_final",
    }
