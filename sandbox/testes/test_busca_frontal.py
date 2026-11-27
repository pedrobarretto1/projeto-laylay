from pathlib import Path

import pytest

from sandbox.__main__ import Bancada
from sandbox.bancada import Cena


@pytest.mark.parametrize("frente_apos_giro,lado_esperado", [(45, -1), (75, 1), (110, 1)])
def test_busca_reavalia_distancia_e_retorna_de_espera_com_frente_na_histerese(
    tmp_path, frente_apos_giro, lado_esperado,
):
    bancada = Bancada(Path("firmware/rosto_laylay").resolve(), tmp_path)
    try:
        assert bancada.firmware, bancada.log_build
        with bancada.lock:
            consultar = bancada.firmware.consultar
            consultar("P HELLO 1 01234567")
            seq = 0
            fases = []
            pulsos = []
            frente = 45
            voltando = False
            for quadro in range(650):
                if quadro % 10 == 0:
                    seq += 1
                    consultar(f"P FACE 1 01234567 {seq} 0 1 0 3500")
                    consultar(f"P SENTRY 1 01234567 {seq} 1 1200")
                pwm = next(linha.split()[1:3] for linha in consultar(
                    f"S 20 {frente} 0 0 0 1 0 0 0") if linha.startswith("E "))
                esquerda, direita = map(int, pwm)
                _, _, _, _, _, incidente, _, risco, fase, *_ = next(
                    linha.split() for linha in consultar("P GUARD 1 1") if linha.startswith("R GUARD "))
                assert not (esquerda > 0 and direita > 0), (fase, frente)
                if fase == "BUSCANDO" and esquerda * direita < 0 and (not fases or fases[-1] != fase):
                    pulsos.append((int(incidente), 1 if esquerda > 0 else -1))
                    frente = frente_apos_giro
                if fase == "BUSCANDO" and esquerda == direita == 0:
                    continue
                if not fases or fases[-1] != fase:
                    fases.append(fase)
                if fase == "ESPERA_BUSCA":
                    frente = 110
                if pulsos and int(incidente) > pulsos[0][0] and fase == "BUSCANDO" and esquerda * direita < 0:
                    voltando = True
                    consultar("P STOP")
                    break
            assert len(pulsos) >= 2, (fases, pulsos, risco)
            assert pulsos[1][1] == pulsos[0][1] * lado_esperado, pulsos
            assert "ESPERA_BUSCA" in fases, fases
            assert voltando, (fases, pulsos, risco)
            for quadro in range(260):
                if quadro % 10 == 0:
                    seq += 1
                    consultar(f"P FACE 1 01234567 {seq} 0 1 0 3500")
                    consultar(f"P SENTRY 1 01234567 {seq} 0 1200")
                assert any(linha.startswith("E 0 0 ") for linha in consultar("S 20 45 0 0 0 1 0 0 0"))
    finally:
        bancada.fechar()


def test_pausa_por_obstaculo_continua_expressiva_na_faixa_de_histerese(tmp_path):
    bancada = Bancada(Path("firmware/rosto_laylay").resolve(), tmp_path)
    try:
        assert bancada.firmware, bancada.log_build
        with bancada.lock:
            consultar = bancada.firmware.consultar
            consultar("P HELLO 1 01234567")
            espera = 0
            seq = 0
            quadros_oled = set()
            for quadro in range(420):
                if quadro % 10 == 0:
                    seq += 1
                    consultar(f"P FACE 1 01234567 {seq} 0 1 0 3500")
                    consultar(f"P SENTRY 1 01234567 {seq} 1 1200")
                frente = 110 if espera else 45
                amostras = consultar(f"S 20 {frente} 0 0 0 1 0 0 0")
                guard = next(linha.split() for linha in consultar("P GUARD 1 1") if linha.startswith("R GUARD "))
                if guard[8] != "ESPERA_BUSCA":
                    continue
                espera += 1
                assert any(linha.startswith("E 0 0 ") for linha in amostras)
                if espera in {50, 145, 175}:
                    assert guard[7] == "NENHUM"
                    assert guard[11] == "IRRITADA", guard
                    quadros_oled.update(linha for linha in consultar("O") if linha.startswith("O "))
                if espera == 175:
                    break
            assert espera == 175
            assert len(quadros_oled) > 1
            incidentes = set()
            for quadro in range(2400):
                if quadro % 8 == 0:
                    seq += 1
                    consultar(f"P FACE 1 01234567 {seq} 0 1 0 3500")
                    consultar(f"P SENTRY 1 01234567 {seq} 1 1200")
                amostras = consultar("S 50 110 0 0 0 1 0 0 0")
                esquerda, direita = next(tuple(map(int, linha.split()[1:3]))
                    for linha in amostras if linha.startswith("E "))
                assert not (esquerda > 0 and direita > 0)
                if quadro % 8 == 0:
                    guard = next(linha.split() for linha in consultar("P GUARD 1 1") if linha.startswith("R GUARD "))
                    incidentes.add(guard[5])
            assert len(incidentes) > 1
            for quadro in range(100):
                if quadro % 10 == 0:
                    seq += 1
                    consultar(f"P FACE 1 01234567 {seq} 0 1 0 3500")
                    consultar(f"P SENTRY 1 01234567 {seq} 1 1200")
                consultar("S 20 350 0 0 0 1 0 0 0")
            guard = next(linha.split() for linha in consultar("P GUARD 1 1") if linha.startswith("R GUARD "))
            assert guard[7:9] == ["NENHUM", "PRONTA"]
            assert guard[11] == "NENHUMA"
    finally:
        bancada.fechar()


def test_corpo_reavalia_depois_de_falhar_no_canto_da_arena(tmp_path):
    bancada = Bancada(Path("firmware/rosto_laylay").resolve(), tmp_path)
    try:
        assert bancada.firmware, bancada.log_build
        with bancada.lock:
            consultar = bancada.firmware.consultar
            consultar("P HELLO 1 01234567")
            cena = Cena()
            esquerda = direita = seq = 0
            esperou = False
            retomou = False
            for quadro in range(660):
                if quadro == 120:
                    cena.atualizar({"reset": True, "corpo": {"x": 12, "y": 14, "yaw": 0}})
                if quadro % 10 == 0:
                    seq += 1
                    consultar(f"P FACE 1 01234567 {seq} 0 1 0 3500")
                    consultar(f"P SENTRY 1 01234567 {seq} {int(quadro >= 125)} 1200")
                amostras = " ".join(f"{v:.5f}" for v in cena.passo(.02, esquerda, direita))
                frente = cena.sensor_frontal()
                leitura = consultar(f"S 20 {frente or -1} 0 {amostras}")
                esquerda, direita = next(tuple(map(int, linha.split()[1:3]))
                    for linha in leitura if linha.startswith("E "))
                fase = next(linha.split()[8] for linha in consultar("P GUARD 1 1") if linha.startswith("R GUARD "))
                if fase == "ESPERA_BUSCA":
                    esperou = True
                    assert esquerda == direita == 0
                if esperou and fase == "SEGUINDO":
                    retomou = True
                if retomou and cena.corpo.y >= 20:
                    break
            assert esperou and retomou, (esperou, retomou, fase)
            assert cena.corpo.y >= 20
    finally:
        bancada.fechar()
