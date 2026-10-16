"""Projeção do MPU: rotação relativa não é localização nem prova de colo."""
from __future__ import annotations

ESTADOS_IMU = {"PRONTA", "CALIBRANDO", "AUSENTE", "AGUARDANDO", "EXPIRADA", "ERRO_I2C"}
MANUSEIOS = {"ESTAVEL", "INCLINADA", "TOMBADA", "MOVIMENTO_BRUSCO", "POSSIVEL_LEVANTAMENTO", "DESCONHECIDO"}
FASES_MANUSEIO = {"TRANQUILA", "CURIOSA", "DESCONFIADA", "SUSTO", "RESMUNGO", "DESORIENTADA", "RECOMPONDO", "DESCONHECIDA"}


def interpretar_imu(linha: str, sequencia: int) -> dict:
    p = linha.split()
    if (len(p) not in {13, 14, 18} or p[:4] != ["IMU", "1", str(sequencia), "104"]
            or p[4] not in ESTADOS_IMU or p[6] not in {"0", "1"} or p[12] not in MANUSEIOS):
        raise ValueError("imu_nao_correlacionada")
    idade, roll, pitch, yaw, gz, norma = (int(p[i]) for i in (5, 7, 8, 9, 10, 11))
    if (not 0 <= idade <= 4294967295 or abs(roll) > 36000 or abs(pitch) > 18000
            or abs(yaw) > 2147483647 or abs(gz) > 60000 or not 0 <= norma <= 8000
            or (p[4] == "PRONTA" and (p[6] != "1" or idade > 75))
            or (p[4] != "PRONTA" and p[12] != "DESCONHECIDO")):
        raise ValueError("imu_incoerente")
    valida = p[4] == "PRONTA"
    identidade = int(p[13]) if len(p) >= 14 else 104
    if valida and identidade not in {104, 152}:
        raise ValueError("imu_identidade_nao_suportada")
    episodio = {}
    if len(p) == 18:
        evento, idade_fase, repeticoes = map(int,p[15:18])
        if (p[14] not in FASES_MANUSEIO or not 0 <= evento <= 4294967295
                or not 0 <= idade_fase <= 4294967295 or not 0 <= repeticoes <= 3
                or (not valida and p[14] != "DESCONHECIDA")):
            raise ValueError("episodio_manuseio_invalido")
        episodio = {"fase_manuseio": p[14], "evento_manuseio": evento,
                    "idade_fase_ms": idade_fase, "repeticoes_manuseio": repeticoes}
    return {**episodio, "estado": p[4], "idade_ms": idade, "calibrada": p[6] == "1",
            "modelo": "ICM20689_compativel" if identidade == 152 else "MPU6050" if identidade == 104 else "nao_identificada",
            "roll_graus": roll / 100 if valida else None,
            "pitch_graus": pitch / 100 if valida else None,
            "yaw_relativo_graus": yaw / 100 if valida else None,
            "velocidade_graus_s": gz / 100 if valida else None,
            "aceleracao_norma_g": norma / 1000 if valida else None,
            "manuseio": p[12], "origem": "imu_esp", "autoriza_execucao": False,
            "prova_deslocamento": False}
