from copy import deepcopy
import hashlib

import pytest

from mente_laylay.neural.validar_coleta_runtime import validar


def base():
    texto = "Não abra o Opera."
    comandos = (texto,)
    planos = [{"indice": 0, "comando": texto, "plano": {"id": 123, "texto_usuario": texto, "comandos": []}}]
    registros = [{"tipo": "entrada_prospectiva", "planejamento": "concluido", "turno_id": 123,
        "entrada": {"texto": texto, "truncado": False, "caracteres_originais": len(texto),
            "sha256_original": hashlib.sha256(texto.encode()).hexdigest()},
        "origem_declarada": "roteiro_teste", "teste_declarado": True,
        "origem_humana_certificada": False, "apto_treino": False, "treino_permitido": False,
        "autoriza_execucao": False, "autoriza_promocao": False, "anotacao": None,
        "particao": None, "origem_rotulo": "pendente", "conversa_id": "teste", "sessao_conversa_ts": 10.0,
        "contexto_anterior": {"turno_id": None, "autoriza_execucao": False, "mensagens": []}}]
    return comandos, planos, registros, {"concluido_transporte": True, "respondidos": 1}


def test_green_limitado_a_coleta_sem_revisao_humana():
    a = base(); antes = deepcopy(a)
    r = validar(*a)
    assert a == antes and r["coleta_runtime_green"] is True
    assert r["amostras_humanas"] == 0 and r["qualidade_conversa_certificada"] is False


@pytest.mark.parametrize("falha", ["ausente", "duplicada", "texto", "hash", "truncado", "origem", "humano", "treino", "comando", "contexto", "system", "sessao", "incompleto"])
def test_evidencia_insuficiente_nao_fica_verde(falha):
    comandos, planos, rs, resumo = base()
    r = rs[0]
    if falha == "ausente": rs = []
    if falha == "duplicada": rs.append(deepcopy(r))
    if falha == "texto": r["entrada"]["texto"] = "outro"
    if falha == "hash": r["entrada"]["sha256_original"] = "outro"
    if falha == "truncado": r["entrada"]["truncado"] = True
    if falha == "origem": r["origem_declarada"] = "terminal"
    if falha == "humano": r["origem_humana_certificada"] = True
    if falha == "treino": r["apto_treino"] = True
    if falha == "comando": planos[0]["plano"]["comandos"] = [{"intent": "APP_OPEN"}]
    if falha == "contexto": r["contexto_anterior"]["turno_id"] = 999
    if falha == "system": r["contexto_anterior"]["mensagens"] = [{"papel": "system"}]
    if falha == "sessao": r["sessao_conversa_ts"] = None
    if falha == "incompleto": resumo["concluido_transporte"] = False
    with pytest.raises(ValueError): validar(comandos, planos, rs, resumo)
