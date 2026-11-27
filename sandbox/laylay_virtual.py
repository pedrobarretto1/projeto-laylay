"""Inicia a Laylay com a partitura de passeio da bancada."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import os
from pathlib import Path
import runpy
from typing import Any


def _espaco_medido_para_passear(diagnostico: Mapping[str, Any]) -> bool:
    sensores = diagnostico.get("sensores") or {}
    protecao = sensores.get("protecao") or {}
    frente = (sensores.get("leituras") or {}).get("frente") or {}
    imu = diagnostico.get("imu") or {}
    return (
        sensores.get("recente") is True and protecao.get("risco") == "NENHUM"
        and protecao.get("fase") in {"PRONTA", "CONCLUIDA"}
        and frente.get("estado") == "VALIDA" and type(frente.get("mm")) is int and frente["mm"] >= 220
        and type(frente.get("idade_ms")) is int and frente["idade_ms"] <= 150
        and imu.get("recente") is True and imu.get("manuseio") == "ESTAVEL"
        and imu.get("bloqueio_manuseio") is False
    )


@contextmanager
def perfil_passeio_virtual(ambiente: Mapping[str, str]) -> Iterator[None]:
    """Seleciona o perfil e os gestos no processo filho da bancada."""
    porta = ambiente.get("LAYLAY_CORPO_SIMULADOR_PORTA", "")
    chave = ambiente.get("LAYLAY_CORPO_SIMULADOR_SESSAO", "")
    if (ambiente.get("LAYLAY_ROSTO_PORTA") != "CORPO_VIRTUAL" or not porta.isdecimal()
            or not 0 < int(porta) <= 65535 or len(bytes.fromhex(chave)) != 32):
        raise ValueError("O perfil de passeio exige o canal virtual da bancada.")

    from mente_laylay.autonomia import companhia_corporal
    from mente_laylay.cognicao import decisao_corporal
    from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime

    gesto = companhia_corporal.GestoCorporal
    passeios_anteriores = companhia_corporal.PASSEIOS
    pausas_anteriores = companhia_corporal.PAUSAS_PASSEIO_S
    perfil_anterior = ConfiguracaoAplicacaoRuntime.perfil_corporal
    companhia = companhia_corporal.CompanhiaCorporalRuntime
    ritmo_anterior = companhia._ritmo_corporal
    decisao_anterior = decisao_corporal._decidir_ritmo

    def perfil_da_bancada(_configuracao: ConfiguracaoAplicacaoRuntime) -> str:
        return "bancada"

    def ritmo_da_bancada(self, concessao, diagnostico):
        ritmo = ritmo_anterior(self, concessao, diagnostico)
        if diagnostico.get("transporte") == "simulado" and self._canal_permitido(diagnostico):
            ritmo["espaco_medido_na_bancada"] = _espaco_medido_para_passear(diagnostico)
            if not ritmo["primeira_iniciativa"]:
                ritmo["pausa_original_s"] = pausas_anteriores[self._passeios % len(pausas_anteriores)]
        return ritmo

    def decidir_ritmo_da_bancada(ritmo, emocao, nivel, agora):
        # A cognição só chega aqui depois de avaliar o turno, as proteções e
        # o repouso agendado. O executor ainda exige a concessão e os receipts.
        if ritmo.get("espaco_medido_na_bancada") is True and ritmo.get("motor_ms_60s", 0) < 6000:
            return decisao_corporal.IntencaoCorporal("explorar", "passeio_virtual_com_espaco", 30,
                                                     emocao, nivel, True)
        if (ritmo.get("motor_ms_60s", 0) < 20000
                and ritmo.get("tempo_sem_gesto_s", 0) < ritmo.get("pausa_original_s", 0)):
            return decisao_corporal.IntencaoCorporal("descansar", "intervalo_normal_de_passeio", 30,
                                                     emocao, nivel)
        return decisao_anterior(ritmo, emocao, nivel, agora)

    ConfiguracaoAplicacaoRuntime.perfil_corporal = perfil_da_bancada
    companhia._ritmo_corporal = ritmo_da_bancada
    decisao_corporal._decidir_ritmo = decidir_ritmo_da_bancada
    companhia_corporal.PAUSAS_PASSEIO_S = (28, 18, 38, 24)
    companhia_corporal.PASSEIOS = (
        gesto("passeio_avanco", 80, ((100, 100, 440),) * 3 + ((-100, 100, 160),), 100),
        gesto("passeio_curva_direita", 80, ((200, 0, 340), (100, 100, 500)), 100),
        gesto("passeio_curva_esquerda", 80, ((0, 200, 340), (100, 100, 500)), 100),
        gesto("passeio_olhar", 80, ((-100, 100, 220), (100, -100, 120)), 120),
    )
    try:
        yield
    finally:
        ConfiguracaoAplicacaoRuntime.perfil_corporal = perfil_anterior
        companhia._ritmo_corporal = ritmo_anterior
        decisao_corporal._decidir_ritmo = decisao_anterior
        companhia_corporal.PAUSAS_PASSEIO_S = pausas_anteriores
        companhia_corporal.PASSEIOS = passeios_anteriores


if __name__ == "__main__":
    with perfil_passeio_virtual(os.environ):
        runpy.run_path(str(Path(__file__).resolve().parents[1] / "laylay.py"), run_name="__main__")
