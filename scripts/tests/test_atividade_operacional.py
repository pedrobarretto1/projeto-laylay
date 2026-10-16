"""Atividade transitória observada, independente de propostas e receipts."""
from concurrent.futures import ThreadPoolExecutor
import importlib
from threading import Event
import asyncio
from types import SimpleNamespace

import pytest

from mente_laylay.memoria_mental.atividade_operacional_runtime import (
    AtividadeOperacionalRuntime, criar_atividade_operacional_runtime,
    projetar_atividade_operacional, projetar_envio_operacional,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime


def criar_owner():
    mente = criar_estado_compartilhado_runtime()
    relogio = SimpleNamespace(agora=10.0)
    owner = criar_atividade_operacional_runtime(estado=mente, monotonic=lambda: relogio.agora)
    return owner, mente, relogio


def test_envio_sem_observacao_tem_identidade_propria_sem_confirmar_efeito():
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    owner, mente, clock = criar_owner()
    receipt = ResultadoAcao(intent="MEDIA_CONTROL", origem="executor", id_solicitacao="envio-1",
                            status="midia_play", ok=True, executou=True, confirmado=None)
    with owner.escopo():
        assert owner.observar_resultado(receipt)
        assert owner.retrato()["envio_id"] == 0
    assert owner.retrato()["envio_id"] == 1 and owner.retrato()["sucesso_id"] == 0
    assert projetar_envio_operacional(mente.mental["atividade_operacional"], agora=clock.agora)
    assert not owner.observar_resultado(receipt)
    assert receipt.confirmado is None
    assert not projetar_envio_operacional(owner.retrato(), agora=clock.agora + 3.1)


@pytest.mark.parametrize("dados", [
    {"origem": "modelo"}, {"id_solicitacao": ""}, {"executou": False},
    {"ok": False}, {"intent": "INVENTADO"}, {"status": "cancelado"},
    {"intent": "CORPO_MOVER"}, {"status": "bloqueado_sem_autorizacao"},
])
def test_proposta_recusa_falha_ou_ack_motor_nao_e_envio_operacional(dados):
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    owner, _, _ = criar_owner()
    base = dict(intent="MEDIA_CONTROL", origem="executor", id_solicitacao="nao-envio",
                status="midia_play", ok=True, executou=True, confirmado=None)
    base.update(dados)
    owner.observar_resultado(ResultadoAcao(**base))
    assert not owner.retrato()["envio_id"]


def test_falha_parcial_impede_sinal_de_envio_do_lote():
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    owner, _, _ = criar_owner()
    with owner.escopo():
        owner.observar_resultado(ResultadoAcao(intent="MEDIA_CONTROL", origem="executor", id_solicitacao="e",
            status="midia_play", ok=True, executou=True, confirmado=None))
        owner.observar_resultado(ResultadoAcao(intent="VOLUME", origem="executor", id_solicitacao="f",
            status="falha_execucao", ok=False, executou=False, confirmado=False))
    assert owner.retrato()["falha_id"] == 1 and owner.retrato()["envio_id"] == 0


def test_lote_com_efeito_confirmado_e_envio_nao_comemora_sucesso_total():
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    owner, _, _ = criar_owner()
    with owner.escopo():
        owner.observar_resultado(ResultadoAcao(intent="VOLUME", origem="executor", id_solicitacao="volume",
            status="volume_ajustado", ok=True, executou=True, confirmado=True))
        owner.observar_resultado(ResultadoAcao(intent="MEDIA_CONTROL", origem="executor", id_solicitacao="midia",
            status="midia_play", ok=True, executou=True, confirmado=None))
    assert owner.retrato()["envio_id"] == 1 and owner.retrato()["sucesso_id"] == 0


def test_escopo_usa_mesmo_estado_compartilhado_sem_promover_receipt_e_pulso_expira():
    owner, mente, relogio = criar_owner()
    assert not projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=10)
    with owner.escopo():
        assert mente.mental["atividade_operacional"]["ativos"] == 1
        assert projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=100)
    assert mente.mental["atividade_operacional"]["ativos"] == 0
    assert projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=10.7)
    assert not projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=10.9)
    assert not projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=9)


@pytest.mark.parametrize("estado", [
    {"current_emotion": "brava", "is_speaking": True},
    {"activity": "executing", "visual_activity": "executing"},
    {"comandos": [{"intent": "APP_OPEN"}], "fase": "planejado"},
    {"ativos": 1},
    {"origem": "atividade_operacional_observada", "ativos": False},
    {"origem": "atividade_operacional_observada", "ativos": 0, "ultimo_inicio_monotonic": float("nan")},
])
def test_proposta_emocao_e_estado_nao_observado_nao_criam_atividade(estado):
    assert not projetar_atividade_operacional(estado, agora=10)


def test_reentrancia_nao_apaga_acao_externa_ao_encerrar_a_interna():
    owner, mente, relogio = criar_owner()
    with owner.escopo():
        with owner.escopo():
            assert mente.mental["atividade_operacional"]["ativos"] == 2
        relogio.agora = 50
        assert mente.mental["atividade_operacional"]["ativos"] == 1
        assert projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=50)
    assert not projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=50)


def test_escopos_concorrentes_independentes_sobrevivem_ao_primeiro_fim():
    owner, mente, _ = criar_owner()
    primeiro, segundo, liberar_primeiro, liberar_segundo = (Event() for _ in range(4))

    def operar(entrou, liberar):
        with owner.escopo():
            entrou.set()
            assert liberar.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(operar, primeiro, liberar_primeiro)
        b = pool.submit(operar, segundo, liberar_segundo)
        try:
            assert primeiro.wait(timeout=5) and segundo.wait(timeout=5)
            assert mente.mental["atividade_operacional"]["ativos"] == 2
            liberar_primeiro.set()
            a.result(timeout=5)
            assert mente.mental["atividade_operacional"]["ativos"] == 1
        finally:
            liberar_primeiro.set()
            liberar_segundo.set()
            a.result(timeout=5)
            b.result(timeout=5)
    assert mente.mental["atividade_operacional"]["ativos"] == 0


def test_falha_visual_e_diagnostica_nao_muda_retorno_ou_excecao_operacional():
    def falhar(*_args, **_kwargs):
        raise OSError("falha na saída visual")
    owner = AtividadeOperacionalRuntime(publicar=falhar, relatar_falha=falhar)
    assert owner.executar(lambda: "receipt preservado") == "receipt preservado"
    erro_real = RuntimeError("executor falhou")
    def executor():
        raise erro_real
    with pytest.raises(RuntimeError) as observado:
        owner.executar(executor)
    assert observado.value is erro_real
    assert owner.retrato()["ativos"] == 0


def test_corrotina_mantem_escopo_durante_await_e_fecha_ao_cancelar():
    owner, mente, _ = criar_owner()
    async def cenario():
        entrou, liberar = asyncio.Event(), asyncio.Event()
        async def executor():
            entrou.set()
            await liberar.wait()
        tarefa = asyncio.create_task(owner.executar_assincrono(executor))
        await asyncio.wait_for(entrou.wait(), timeout=2)
        assert mente.mental["atividade_operacional"]["ativos"] == 1
        tarefa.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarefa
        assert mente.mental["atividade_operacional"]["ativos"] == 0
    asyncio.run(cenario())


def test_composicao_instalada_publica_atividade_durante_despacho_e_encerra(monkeypatch, tmp_path):
    from mente_laylay.integracao import instancia_unica
    from mente_laylay.autonomia import coordenador_intencao
    adquirir = instancia_unica.adquirir_instancia_unica
    monkeypatch.setattr(instancia_unica, "adquirir_instancia_unica",
                        lambda _: adquirir(tmp_path / "composicao_atividade"))
    root = importlib.import_module("laylay")
    assert root._composicao_ciclo_comandos_runtime.ciclo.atividade_operacional is root._atividade_operacional_runtime
    entrou, liberar = Event(), Event()

    def despacho_controlado(*_args):
        entrou.set()
        assert liberar.wait(timeout=5)
        return False

    # Somente o efeito externo é substituído; composição, ciclo e mente são reais.
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", despacho_controlado)
    with ThreadPoolExecutor(max_workers=1) as pool:
        futuro = pool.submit(root.executar_intencao, {"intent": "VOLUME", "params": {}},
                             "pedido sem texto publicado no periférico")
        try:
            assert entrou.wait(timeout=5), "o teste deve alcançar o despacho real"
            retrato = root._estado_compartilhado_runtime.obter_copia(
                "mental", "atividade_operacional", {},
            )
            assert retrato.get("ativos") == 1, "despacho em andamento não foi observado pela mente"
            assert root._rosto_oled_runtime.atividade_getter() == retrato
            assert projetar_atividade_operacional(root._rosto_oled_runtime.atividade_getter())
            assert retrato.get("autoriza_execucao") is False
            assert retrato.get("confirma_efeito") is False
            assert "pedido" not in str(retrato)
        finally:
            liberar.set()
            assert futuro.result(timeout=5) is False
    assert root._estado_compartilhado_runtime.obter_copia(
        "mental", "atividade_operacional", {},
    )["ativos"] == 0
    assert root._rosto_oled_runtime.atividade_getter() == root._atividade_operacional_runtime.retrato()


def test_ciclo_sem_turno_observa_excecao_e_preserva_erro_original(monkeypatch):
    from mente_laylay.autonomia import coordenador_intencao
    owner, mente, _ = criar_owner()
    ciclo = coordenador_intencao.CicloComandosRuntime(
        namespace_getter=lambda: {}, contexto_intencao_runtime=SimpleNamespace(montar=lambda: {}),
        atividade_operacional=owner,
    )
    original = RuntimeError("efeito externo falhou")
    def executor(*_args):
        assert mente.mental["atividade_operacional"]["ativos"] == 1
        raise original
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    with pytest.raises(RuntimeError) as erro:
        ciclo.executar_intencao({"intent": "VOLUME"}, "sem turno")
    assert erro.value is original
    assert mente.mental["atividade_operacional"]["ativos"] == 0


def test_cache_do_ciclo_nao_dispara_outra_animacao_apos_mesmo_despacho(monkeypatch):
    from mente_laylay.autonomia import coordenador_intencao
    owner, mente, relogio = criar_owner()
    ciclo = coordenador_intencao.CicloComandosRuntime(
        namespace_getter=lambda: {},
        contexto_intencao_runtime=SimpleNamespace(montar=lambda: {"turno_atual": {"id": "t1"}}),
        atividade_operacional=owner,
    )
    chamadas = []
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", lambda *_: chamadas.append(True) or True)
    assert ciclo.executar_intencao({"intent": "VOLUME", "params": {}}, "ajuste")
    inicio_original = mente.mental["atividade_operacional"]["ultimo_inicio_monotonic"]
    relogio.agora += 5
    assert ciclo.executar_intencao({"intent": "VOLUME", "params": {}}, "ajuste")
    assert chamadas == [True]
    assert mente.mental["atividade_operacional"]["ultimo_inicio_monotonic"] == inicio_original
    assert not projetar_atividade_operacional(mente.mental["atividade_operacional"], agora=relogio.agora)


def test_bypasses_instalados_de_resumo_e_saida_audio_reusam_owner(monkeypatch):
    root = importlib.import_module("laylay")
    owner, mente = root._atividade_operacional_runtime, root._estado_compartilhado_runtime
    assert root.resumir_pagina_ou_video.func.__self__ is root._resumo_conteudo_runtime
    assert root.resumir_pagina_ou_video.keywords["executar_assincrono"].__self__ is owner
    resultado = {"executou": False, "confirmado": False}
    def selecionar(_referencia):
        assert mente.mental["atividade_operacional"]["ativos"] == 1
        return resultado
    monkeypatch.setattr(root._saidas_audio_runtime, "selecionar", selecionar)
    assert root._desktop_bridge_runtime.executar_acao_painel(
        "audio_output_select", {"device_ref": "a" * 16},
    ) is resultado
    assert mente.mental["atividade_operacional"]["ativos"] == 0


def test_autonomia_instalada_reusa_owner_sem_alterar_receipt_ou_governanca(monkeypatch):
    root = importlib.import_module("laylay")
    owner, mente = root._atividade_operacional_runtime, root._estado_compartilhado_runtime
    assert root._executar_acao_autonoma_segura.func.__self__ is owner
    assert root._executar_acao_autonoma_segura.args[0].__self__ is root._executor_acoes_autonomas_runtime
    assert root._desfazer_acao_autonoma_segura.func.__self__ is owner
    assert root._desfazer_acao_autonoma_segura.args[0].__self__ is root._executor_acoes_autonomas_runtime
    def controlar(_acao):
        assert mente.mental["atividade_operacional"]["ativos"] == 1
        assert root._rosto_oled_runtime.atividade_getter() == owner.retrato()
        return False
    monkeypatch.setattr(root._executor_acoes_autonomas_runtime, "controlar_midia", controlar)
    resultado = root._executar_acao_autonoma_segura({
        "intent": "MEDIA_CONTROL", "params": {"acao": "pause"},
    })
    assert resultado["ok"] is False and resultado["confirmado"] is False
    assert mente.mental["atividade_operacional"]["ativos"] == 0
