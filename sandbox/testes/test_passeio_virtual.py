from pathlib import Path
from threading import Thread
import math
import time

import pytest

from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
from mente_laylay.especialistas.corpo_motor_runtime import criar_corpo_motor_runtime
from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from sandbox.__main__ import Bancada, ClienteCorpo, ServidorCorpo, ambiente_laylay_virtual
from sandbox.laylay_virtual import perfil_passeio_virtual


@pytest.fixture
def passeio_da_bancada():
    with perfil_passeio_virtual(ambiente_laylay_virtual(8766, b"\x20" * 32)):
        yield


def test_perfil_virtual_nao_herda_nem_altera_montagem_fisica(tmp_path):
    caminho = tmp_path / "configuracao.env"
    original = "LAYLAY_CORPO_PERFIL=rodas_suspensas\n"
    caminho.write_text(original, encoding="utf-8")
    configuracao = ConfiguracaoAplicacaoRuntime(raiz=tmp_path)
    assert configuracao.perfil_corporal() == "rodas_suspensas"
    with pytest.raises(ValueError, match="canal virtual"):
        with perfil_passeio_virtual({}):
            pytest.fail("O perfil foi aplicado fora da bancada")
    with perfil_passeio_virtual(ambiente_laylay_virtual(8766, bytes(32))):
        assert configuracao.perfil_corporal() == "bancada"
    assert configuracao.perfil_corporal() == "rodas_suspensas"
    assert caminho.read_text(encoding="utf-8") == original


def test_passeio_em_area_livre_desloca_o_corpo_virtual_e_preserva_stop(tmp_path, monkeypatch, passeio_da_bancada):
    bancada = Bancada(Path("firmware/rosto_laylay").resolve(), tmp_path)
    servidor = ServidorCorpo(("127.0.0.1", 0), ClienteCorpo)
    servidor.bancada = bancada
    Thread(target=servidor.serve_forever, daemon=True).start()
    for chave, valor in ambiente_laylay_virtual(servidor.server_address[1], bancada.token).items():
        if chave.startswith("LAYLAY_"):
            monkeypatch.setenv(chave, valor)
    estado = criar_estado_compartilhado_runtime()

    def procurar_placa():
        raise AssertionError("O passeio virtual tentou descobrir hardware")

    transporte = criar_composicao_rosto_oled_runtime(
        estado=estado, listar_portas=procurar_placa,
        observabilidade=type("Obs", (), {"relatar_falha": lambda *_args, **_kw: None})(),
        busca_obstaculos_getter=lambda sessao: companhia.autorizar_busca_obstaculos(sessao),
    )
    agora = [time.monotonic()]
    atencao = [False]
    (tmp_path / "configuracao.env").write_text("LAYLAY_CORPO_PERFIL=rodas_suspensas\n", encoding="utf-8")
    configuracao = ConfiguracaoAplicacaoRuntime(raiz=tmp_path)
    corpo = criar_corpo_motor_runtime(
        transporte=transporte, estado=estado, monotonic=lambda: agora[0],
        companhia_bancada_ao_iniciar=configuracao.companhia_bancada_ao_iniciar(),
        passeio_bancada_ao_iniciar=configuracao.passeio_bancada_ao_iniciar(),
        perfil_corporal=configuracao.perfil_corporal(),
        prioridade_interacao_getter=lambda: atencao[0],
    )
    companhia = corpo.companhia
    companhia.coordenador = OrquestradorCooperativoRuntime(
        quadro=QuadroCooperacaoRuntime(modo="ativo", log=lambda _: None),
        clipboard_snapshot=lambda: {}, clipboard_getter=lambda: "",
        executar_intencao=lambda *_: False, resolver_caminho=lambda s: s,
        falar=lambda *_: None, log=lambda _: None,
    )
    companhia.coordenador.governanca.registrar_autorizador_escopo("corpo_companhia", companhia.autorizar_escopo)
    try:
        assert bancada.firmware, bancada.log_build
        limite = time.monotonic() + 5
        while time.monotonic() < limite:
            assert transporte.sincronizar()
            if transporte.diagnostico()["imu"].get("estado") == "PRONTA":
                break
            time.sleep(.08)
        assert transporte.diagnostico()["imu"]["estado"] == "PRONTA"
        assert transporte.diagnostico()["transporte"] == "simulado"
        assert companhia.processar()["passeio_ativado"]
        assert not companhia.processar()["ok"]
        y_antes = bancada.cena.corpo.y
        agora[0] += 8.1
        passeio = companhia.processar()
        assert passeio["ok"], passeio
        deslocamento = y_antes - bancada.cena.corpo.y
        assert deslocamento > 11, deslocamento
        x, y, yaw = bancada.cena.corpo.x, bancada.cena.corpo.y, bancada.cena.corpo.yaw
        agora[0] += 10
        assert companhia.processar()["em_repouso"]
        agora[0] += 14
        with bancada.lock:
            obstaculo_anterior = {"x": bancada.cena.obstaculo.x, "y": bancada.cena.obstaculo.y}
            angulo = math.radians(yaw)
            bancada.cena.atualizar({"obstaculo": {"x": x + 32 * math.sin(angulo),
                                                  "y": y - 32 * math.cos(angulo)}})
        time.sleep(.3)
        assert transporte.sincronizar()
        frente = transporte.diagnostico()["sensores"]["leituras"]["frente"]
        assert 120 < frente["mm"] < 220, frente
        sem_espaco = companhia.processar()
        assert sem_espaco["em_repouso"] and not sem_espaco["movimento_executado"], sem_espaco
        with bancada.lock:
            bancada.cena.atualizar({"obstaculo": obstaculo_anterior})
        time.sleep(.3)
        assert transporte.sincronizar()
        curva = companhia.processar()
        assert curva["ok"], curva
        assert math.hypot(bancada.cena.corpo.x - x, bancada.cena.corpo.y - y) > 5
        assert abs((bancada.cena.corpo.yaw - yaw + 180) % 360 - 180) > 5
        agora[0] += 24
        assert companhia.processar()["em_repouso"]
        atencao[0] = True
        agora[0] += 120
        assert transporte.sincronizar()
        espera = companhia.processar()
        assert espera["em_observacao"] and not espera["movimento_executado"], espera
        assert bancada.retrato()["firmware"]["pwm_esq"] == bancada.retrato()["firmware"]["pwm_dir"] == 0
        assert companhia.diagnostico()["ativa"]
        atencao[0] = False
        assert transporte.sincronizar()
        retomada = companhia.processar()
        assert retomada["ok"], retomada
        assert corpo.executar("CORPO_PARAR", {})["ok"]
        agora[0] += 120
        assert not companhia.processar()["ok"]
        assert not companhia.diagnostico()["ativa"]
        assert bancada.retrato()["firmware"]["pwm_esq"] == bancada.retrato()["firmware"]["pwm_dir"] == 0
    finally:
        transporte.encerrar()
        servidor.shutdown()
        servidor.server_close()
        bancada.fechar()
