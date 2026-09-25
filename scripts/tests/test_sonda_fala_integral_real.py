"""A revisão da fala completa deve falhar fechada em omissão e recibo falso."""

from scripts.analises.sonda_fala_integral_real import (
    conferir_saida,
    pontuar,
    pontuar_veto_lexical,
)


def _caso(rotulos: tuple[str, ...], fontes: dict[str, str] | None = None) -> dict:
    return {"nome": "controle", "partes": [{"texto": "frase"}] * len(rotulos),
            "rotulos": rotulos, "fontes": fontes or {}}


def test_todos_os_indices_inclusive_dez_devem_estar_presentes() -> None:
    caso = _caso(("social",) * 12)
    itens = [{"indice": i, "classe": "nao_factual"} for i in range(12)]
    assert conferir_saida({"partes": itens}, caso)["valida"]
    assert not conferir_saida({"partes": itens[:-1]}, caso)["valida"]
    assert not conferir_saida({"partes": itens[:-1] + [itens[0]]}, caso)["valida"]


def test_citacao_ou_fonte_inventada_nao_aprova() -> None:
    caso = _caso(("sustentada",), {"F1": "O girassol jovem acompanha o sol durante o dia."})
    item = {"indice": 0, "classe": "sustentada", "fonte_id": "F1",
            "citacao": "O girassol jovem acompanha o sol"}
    assert conferir_saida({"partes": [item]}, caso)["valida"]
    assert not conferir_saida({"partes": [{**item, "citacao": "dez quilos por hora"}]}, caso)["valida"]
    assert not conferir_saida({"partes": [{**item, "fonte_id": "F2"}]}, caso)["valida"]


def test_mista_e_calculo_sem_recibo_nao_sao_aprovados() -> None:
    caso = _caso(("mista", "local"))
    resposta = {"observado": {"valida": True, "motivo": "", "partes": [
        {"indice": 0, "classe": "sem_prova"},
        {"indice": 1, "classe": "calculo"},
    ]}, "segundos": 1.0}
    placar = pontuar(caso, resposta)
    assert placar["falso_aceite"] == []
    assert placar["falso_bloqueio"] == [1]
    assert placar["propostas_locais_sem_recibo"] == [1]


def test_citacao_de_regra_geral_nao_prova_conta_local() -> None:
    caso = _caso(("local",), {"F1": "Divisão é repartir em partes iguais."})
    resposta = {"observado": {"valida": True, "motivo": "", "partes": [
        {"indice": 0, "classe": "sustentada", "fonte_id": "F1",
         "citacao": "Divisão é repartir em partes iguais."},
    ]}, "segundos": 1.0}
    placar = pontuar(caso, resposta)
    assert placar["falso_bloqueio"] == []
    assert placar["propostas_locais_sem_recibo"] == [0]


def test_conta_real_e_verificada_mas_nao_aprova_outra_afirmacao_na_frase() -> None:
    caso = _caso(("local", "mista"))
    caso["partes"] = [
        {"texto": "12 dividido por 3 é igual a 4."},
        {"texto": "12 / 3 = 4 e a caixa pesa 8 kg."},
    ]
    resposta = {"observado": {"valida": True, "motivo": "", "partes": [
        {"indice": 0, "classe": "calculo"},
        {"indice": 1, "classe": "sem_prova"},
    ]}, "segundos": 1.0}
    placar = pontuar(caso, resposta)
    assert placar["contas_explicitas_conferidas"] == [0, 1]
    assert placar["falso_bloqueio"] == [0]
    assert placar["falso_aceite"] == []


def test_saida_incompleta_nao_vira_acerto_por_falta_de_itens() -> None:
    caso = _caso(("sustentada", "sem_prova"))
    resposta = {"observado": {"valida": False, "motivo": "cobertura", "partes": []},
                "segundos": 1.0}
    placar = pontuar(caso, resposta)
    assert not placar["saida_valida"]
    assert placar["falso_bloqueio"] == [0]


def test_veto_apenas_rebaixa_proposta_e_expoe_falso_bloqueio() -> None:
    caso = _caso(("mista", "sustentada"), {"F1": "Girassóis jovens acompanham o sol."})
    caso["partes"] = [
        {"texto": "Girassóis jovens acompanham o sol e liberam dez litros de água."},
        {"texto": "Girassóis jovens seguem o sol."},
    ]
    resultado = {"observado": {"valida": True, "motivo": "", "partes": [
        {"indice": 0, "classe": "sustentada", "fonte_id": "F1",
         "citacao": "Girassóis jovens acompanham o sol."},
        {"indice": 1, "classe": "sustentada", "fonte_id": "F1",
         "citacao": "Girassóis jovens acompanham o sol."},
    ]}, "segundos": 1.0}
    assert pontuar(caso, resultado)["falso_aceite"] == [0]
    placar = pontuar_veto_lexical(caso, resultado)
    assert placar["falso_aceite"] == []
    assert placar["falso_bloqueio"] == [1]
    assert set(placar["vetos"]) == {0, 1}
