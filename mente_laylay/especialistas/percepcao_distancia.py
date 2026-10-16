"""Receipts dos VL53L0X: medição factual, sem autoridade de movimento."""
from __future__ import annotations

FASES_REFLEXO = {"RECUANDO", "PAUSA", "GIRANDO", "VERIFICANDO", "SEGUINDO", "BUSCANDO", "CONFERINDO", "RECUO_MEDROSO", "ESPERA_MEDROSA"}
RISCOS = {"NENHUM", "BORDA", "BORDA_SEM_RETORNO", "FALHA_BORDA", "FALHA_FRENTE", "OBSTACULO", "MANUSEIO"}


def interpretar_linha_distancia(linha: str, sequencia: int) -> dict:
    p = linha.split()
    if (len(p) != 15 or p[:3] != ["DIST", "1", str(sequencia)]
        or p[3:5] != ["FRENTE", "48"] or p[9:11] != ["BORDA", "49"]):
        raise ValueError("resposta_distancia_nao_correlacionada")
    estados = {"VALIDA", "INVALIDA", "AUSENTE", "AGUARDANDO", "EXPIRADA", "ERRO_I2C"}
    resultado = {}
    for nome, indice in (("frente", 5), ("borda", 11)):
        estado, mm, idade, status = p[indice:indice+4]
        if estado not in estados:
            raise ValueError("estado_distancia_invalido")
        mm, idade, status = int(mm), int(idade), int(status)
        if not 0 <= idade <= 4294967295 or not 0 <= status <= 255:
            raise ValueError("campos_distancia_invalidos")
        if estado == "VALIDA" and not (0 < mm < 8190 and idade <= 300 and status == 0):
            raise ValueError("validade_distancia_incoerente")
        if estado != "VALIDA" and mm != -1:
            raise ValueError("distancia_invalida_publicada")
        resultado[nome] = {"estado": estado, "mm": mm if estado == "VALIDA" else None,
                            "idade_ms": idade, "status": status}
    return resultado


def interpretar_linha_protecao(linha: str, sequencia: int, sessao: str) -> dict:
    p = linha.split()
    fases = FASES_REFLEXO | {"PRONTA", "BLOQUEADA", "CONCLUIDA", "CANCELADA", "FALHA_PWM", "ESPERA_BUSCA"}
    if (len(p) not in {10,13} or p[:4] != ["GUARD", "1", str(sequencia), sessao]
        or p[6] not in RISCOS or p[7] not in fases or p[8:10] != ["130", "100"]
        or not all(v.isdecimal() and 0 <= int(v) <= 4294967295 for v in p[4:6])):
        raise ValueError("receipt_protecao_invalido")
    reacao, tentativa, vigia = "NENHUMA", 0, False
    if len(p)==13:
        if (p[10] not in {"NENHUMA","MEDO","PAVOR","IRRITADA","ALERTA"}
            or p[11] not in {"0","1","2","3","4"} or p[12] not in {"0","1"}):
            raise ValueError("receipt_alerta_invalido")
        reacao, tentativa, vigia = p[10], int(p[11]), p[12]=="1"
    return {"incidente_id": int(p[4]), "motor_origem_seq": int(p[5]),
            "risco": p[6], "fase": p[7], "reflexo_ativo": p[7] in FASES_REFLEXO,
            "reacao_expressiva": reacao.lower(), "tentativa_busca": tentativa, "vigia_ativa": vigia,
            "limite_borda_mm": 130, "limite_obstaculo_mm": 100,
            "origem": "executor_protecao_esp", "autoriza_execucao": False,
            "rotacao_medida": False, "cobertura": "frente_e_borda_dianteira"}
