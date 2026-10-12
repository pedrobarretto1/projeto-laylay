"""Glitch observa resultado atual do executor, sem criar permissão ou receipt."""
import asyncio
import importlib
from types import SimpleNamespace

import pytest

from mente_laylay.memoria_mental.atividade_operacional_runtime import (
    AtividadeOperacionalRuntime, criar_atividade_operacional_runtime,
    projetar_falha_operacional,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def criar_owner():
    mente = criar_estado_compartilhado_runtime()
    relogio = SimpleNamespace(agora=10.0)
    owner = criar_atividade_operacional_runtime(estado=mente, monotonic=lambda: relogio.agora)
    return owner, mente, relogio


def falha(**campos):
    dados = dict(intent="VOLUME", status="falha_execucao", origem="executor",
                 executou=False, confirmado=False)
    dados.update(campos)
    return ResultadoAcao(**dados)


def test_receipt_negativo_do_executor_publica_falha_transitoria_preservando_resultado():
    owner, mente, _ = criar_owner()
    resultado = falha()
    assert owner.executar(lambda: resultado) is resultado
    estado = mente.mental["atividade_operacional"]
    assert estado.get("falha_id") == 1, "resultado negativo atual não alcançou o sinal visual"
    assert estado["falha_monotonic"] == 10.0
    assert estado["ativos"] == 0
    assert estado["autoriza_execucao"] is False and estado["confirma_efeito"] is False
    assert "falha_execucao" not in str(estado)


@pytest.mark.parametrize("resultado", [
    False, None, True,
    {"comandos": [{"intent": "VOLUME", "ok": False}], "fase": "planejado"},
    {"ok": False},
    {"executou": False, "confirmado": False},
    {"ok": False, "status": "intent_nao_elegivel"},
    {"ok": False, "status": "aguardando_confirmacao"},
    {"ok": False, "status": "bloqueado_por_seguranca"},
    {"ok": False, "status": "falha_execucao", "origem": "politica"},
    falha(origem="politica"),
    falha(status="aguardando_confirmacao"),
    falha(status="alvo_ambiguo"),
    falha(status="acao_invalida"),
    falha(status="cancelado"),
    falha(status="solicitacao_recusada"),
    falha(status="bloqueado_por_seguranca"),
    falha(status="intent_nao_reconhecida"),
    falha(status="tratado_sem_receipt", executou=None, confirmado=None),
    falha(status="comando_enviado", executou=True, confirmado=None),
    falha(status="ja_aberto_focado", executou=False, confirmado=True),
    falha(status="volume_ajustado", executou=True, confirmado=True),
])
def test_recusa_pendencia_bool_e_ausencia_de_receipt_nao_criam_glitch(resultado):
    owner, _, _ = criar_owner()
    assert owner.executar(lambda: resultado) is resultado
    assert owner.retrato().get("falha_id", 0) == 0


def test_wrapper_de_executor_com_dict_explicitamente_negativo_reusa_sinal():
    owner, _, _ = criar_owner()
    resultado = {"ok": False, "confirmado": False, "status": "falha_confirmacao_midia"}
    assert owner.executar(lambda: resultado) is resultado
    assert owner.retrato().get("falha_id") == 1


def test_excecao_reentrante_publica_uma_falha_e_preserva_a_excecao():
    owner, _, _ = criar_owner()
    original = RuntimeError("detalhe pessoal que não deve ir à tela")
    def executar():
        raise original
    with pytest.raises(RuntimeError) as observado:
        owner.executar(lambda: owner.executar(executar))
    assert observado.value is original
    assert owner.retrato().get("falha_id") == 1
    assert owner.retrato()["ativos"] == 0
    assert "pessoal" not in str(owner.retrato())


def test_cancelamento_assincrono_nao_e_falha_operacional():
    owner, _, _ = criar_owner()
    async def cenario():
        async def cancelar():
            raise asyncio.CancelledError()
        with pytest.raises(asyncio.CancelledError):
            await owner.executar_assincrono(cancelar)
    asyncio.run(cenario())
    assert owner.retrato().get("falha_id", 0) == 0
    assert owner.retrato()["ativos"] == 0


def test_publicacao_visual_falha_preserva_receipt_negativo():
    def quebrar(*_args, **_kwargs):
        raise OSError("diagnóstico indisponível")
    owner = AtividadeOperacionalRuntime(publicar=quebrar, relatar_falha=quebrar)
    resultado = falha()
    assert owner.executar(lambda: resultado) is resultado
    assert owner.retrato().get("falha_id") == 1


def test_falha_recente_expira_e_nao_restabelece_receipt_antigo():
    owner, _, relogio = criar_owner()
    receipt = falha(id_solicitacao="ocorrencia-a")
    assert owner.observar_resultado(receipt)
    assert projetar_falha_operacional(owner.retrato(), agora=10) == (1, 10.0)
    assert projetar_falha_operacional(owner.retrato(), agora=12) == (1, 10.0)
    assert projetar_falha_operacional(owner.retrato(), agora=12.01) is None
    assert projetar_falha_operacional(owner.retrato(), agora=9.99) is None
    relogio.agora = 50
    assert not owner.observar_resultado(receipt)
    assert owner.retrato()["falha_monotonic"] == 10.0
    assert projetar_falha_operacional(owner.retrato(), agora=50) is None
    assert owner.observar_resultado(falha(id_solicitacao="ocorrencia-b"))
    assert projetar_falha_operacional(owner.retrato(), agora=50) == (2, 50.0)


@pytest.mark.parametrize("estado", [
    None,
    {"falha_id": 1, "falha_monotonic": 10},
    {"origem": "plano", "falha_id": 1, "falha_monotonic": 10},
    {"origem": "atividade_operacional_observada", "falha_id": True, "falha_monotonic": 10},
    {"origem": "atividade_operacional_observada", "falha_id": "1", "falha_monotonic": 10},
    {"origem": "atividade_operacional_observada", "falha_id": 1, "falha_monotonic": float("inf")},
    {"origem": "atividade_operacional_observada", "falha_id": 1, "falha_monotonic": float("nan")},
    {"origem": "atividade_operacional_observada", "falha_id": 1, "falha_monotonic": True},
    {"origem": "atividade_operacional_observada", "falha_id": 0, "falha_monotonic": 10},
])
def test_projecao_recusa_estado_nao_certificado_ou_timestamp_invalido(estado):
    assert projetar_falha_operacional(estado, agora=10) is None


def test_resultado_dict_fora_de_callback_nao_e_receipt_publicado():
    owner, _, _ = criar_owner()
    assert not owner.observar_resultado({"ok": False, "status": "falha_execucao"})
    assert owner.retrato()["falha_id"] == 0


def test_resultado_derivado_de_receipt_interno_nao_duplica_falha():
    owner, _, _ = criar_owner()
    def executor():
        owner.observar_resultado(falha(id_solicitacao="unica"))
        return {"ok": False, "confirmado": False, "status": "falha_confirmacao_midia"}
    assert owner.executar(executor)["ok"] is False
    assert owner.retrato()["falha_id"] == 1


@pytest.mark.parametrize("publicacao", [False, "receipt aceito"])
def test_ciclo_preserva_publicacao_e_observa_apenas_receipt_aceito(monkeypatch, publicacao):
    from mente_laylay.autonomia import coordenador_intencao
    owner, _, _ = criar_owner()
    ciclo = coordenador_intencao.CicloComandosRuntime(
        namespace_getter=lambda: {},
        contexto_intencao_runtime=SimpleNamespace(montar=lambda: {
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: publicacao,
        }),
        atividade_operacional=owner,
    )
    def executor(_pedido, _texto, contexto):
        assert contexto["_registrar_resultado_execucao"](falha()) is publicacao
        return False
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    assert ciclo.executar_intencao({"intent": "VOLUME"}, "pedido") is False
    assert owner.retrato()["falha_id"] == (0 if publicacao is False else 1)


def test_composicao_instalada_observa_receipt_do_executor_audio(monkeypatch, tmp_path):
    from mente_laylay.integracao import instancia_unica
    adquirir = instancia_unica.adquirir_instancia_unica
    monkeypatch.setattr(instancia_unica, "adquirir_instancia_unica",
                        lambda _: adquirir(tmp_path / "composicao_falha_visual"))
    root = importlib.import_module("laylay")
    # Só a porta externa de áudio e sua saída de voz são substituídas.
    monkeypatch.setitem(root._contexto_intencao_runtime._servicos_estaticos,
                        "ajustar_volume_sistema", lambda _valor: False)
    monkeypatch.setitem(root._contexto_intencao_runtime._servicos_estaticos,
                        "obter_volume_sistema", lambda: None)
    pedido = {"intent": "VOLUME", "params": {"nivel_volume": 42, "_execucao_silenciosa": True}}
    anterior = root._atividade_operacional_runtime.retrato().get("falha_id", 0)
    assert root.executar_intencao(pedido, "deixe o volume em 42 por cento") is True
    tratamento = pedido.get("_laylay_tratamento_operacional", {})
    assert tratamento.get("resultado_publicado") is True, "RED deve atingir o receipt real"
    assert tratamento.get("status") == "falha_execucao"
    assert tratamento.get("confirmado") is False
    retrato = root._estado_compartilhado_runtime.obter_copia("mental", "atividade_operacional", {})
    assert retrato.get("falha_id") == anterior + 1, "receipt aceito não foi observado pelo owner visual"
    assert root._rosto_oled_runtime.atividade_getter() == retrato
