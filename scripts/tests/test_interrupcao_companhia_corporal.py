"""Cancelar uma expressão obsoleta não revoga a concessão da sessão."""
import pytest
from mente_laylay.especialistas.corpo_motor_runtime import CorpoMotorRuntime
from scripts.tests.test_companhia_corporal import montar, motores
from scripts.tests.test_presenca_corporal_v2 import EspPresenca
from scripts.tests.test_rosto_oled import estado_emocional


@pytest.mark.parametrize("fase", [0, 1, 2])
def test_mudanca_de_causa_no_inicio_da_expressao_nao_desativa_companhia(monkeypatch, fase):
    estado, esp, rosto, _, quadro, agora = montar(esp=EspPresenca())
    corpo = CorpoMotorRuntime(transporte=rosto, estado=estado, perfil_corporal="rodas_suspensas",
        companhia_bancada_ao_iniciar=True, monotonic=lambda: agora[0])
    # Mesma governança e executores reais; só o dispositivo é simulado.
    from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
    coordenador = OrquestradorCooperativoRuntime(quadro=quadro, clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "", executar_intencao=lambda *_: False, resolver_caminho=lambda s: s,
        falar=lambda *_: None, log=lambda _: None)
    corpo.companhia.coordenador = coordenador
    coordenador.governanca.registrar_autorizador_escopo("corpo_companhia", corpo.companhia.autorizar_escopo)
    assert corpo.companhia.processar()["ok"]
    estado.substituir("conversacional", estado_emocional("alegre"))
    assert rosto.sincronizar()
    expressar = rosto.expressar_gesto
    aconteceu = []
    def trocar_causa(estilo, etapa, *args, **kwargs):
        if etapa == fase and not aconteceu:
            aconteceu.append(True)
            estado.atualizar_campos("conversacional", current_emotion="calma")
        return expressar(estilo, etapa, *args, **kwargs)
    monkeypatch.setattr(rosto, "expressar_gesto", trocar_causa)
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    mover = rosto.mover_corpo
    monkeypatch.setattr(rosto, "mover_corpo", lambda e, d, ms, **kw: mover(e, d, 50, **kw))
    retorno = corpo.companhia.processar()
    assert aconteceu, "o ensaio deve alcançar a guarda real da expressão"
    assert not retorno["ok"]
    assert corpo.companhia.diagnostico()["ativa"], "causa substituída não é falha elétrica nem revogação do usuário"
    assert corpo.companhia.autorizar_busca_obstaculos(rosto.diagnostico()["sessao"])
    assert estado.obter_copia("mental", "experiencia_corporal", {})["resultado"] == "interrompida"
    if fase < 2:
        assert not motores(esp)
    assert not corpo.companhia.processar()["ok"], "não repetir a emoção antiga"
    rosto.encerrar()
