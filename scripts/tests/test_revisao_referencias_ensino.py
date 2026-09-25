"""O painel é cego; contexto sintético não se torna prova automática."""

from scripts.analises.revisao_referencias_ensino import (
    carregar_painel, diagnosticar, validar_revisao,
)


def test_painel_congelado_nao_traz_gabarito() -> None:
    casos = carregar_painel()
    assert len(casos) == 10
    assert len({item["id"] for item in casos}) == 10
    assert all("esperado" not in item and "rotulo" not in item
               and "revisao" not in item for item in casos)


def test_contexto_nao_se_transforma_em_prova_automatica() -> None:
    casos = {item["id"]: item for item in carregar_painel()}
    sem_contexto = diagnosticar(casos["REF-01"])
    unico_sensor = diagnosticar(casos["REF-05"])
    dois_sensores = diagnosticar(casos["REF-06"])
    assert sem_contexto["estado"] == "qualificador_ausente"
    assert unico_sensor["estado"] == "qualificador_ausente"
    assert dois_sensores["estado"] == "qualificador_ausente"
    assert unico_sensor["contexto_verificado"] is False
    assert all(item["aprovado_para_compor"] is False
               for item in (sem_contexto, unico_sensor, dois_sensores))


def test_revisao_exige_todos_os_ids_e_rotulos_validos() -> None:
    casos = carregar_painel()
    revisoes = [{"id": item["id"], "referente": "indeterminado",
                 "leitura": "indeterminada",
                 "evidencia": "15%" if "15%" in item["exemplo"] else "3°C",
                 "justificativa": "O referente não está demonstrado."}
                for item in casos]
    assert validar_revisao(revisoes)["valida"] is True
    assert validar_revisao(revisoes)["aprovado_para_treino"] is False
    assert validar_revisao(revisoes[:-1])["valida"] is False
    revisoes[0] = {**revisoes[0], "referente": "adivinhado"}
    assert validar_revisao(revisoes)["valida"] is False
    revisoes[0] = {**revisoes[0], "referente": ["mesmo"]}
    assert validar_revisao(revisoes)["valida"] is False


def test_citacao_de_revisao_tem_que_estar_no_caso() -> None:
    revisoes = [{"id": item["id"], "referente": "indeterminado",
                 "leitura": "indeterminada",
                 "evidencia": "15%" if "15%" in item["exemplo"] else "3°C",
                 "justificativa": "A frase não identifica a grandeza."}
                for item in carregar_painel()]
    revisoes[0]["evidencia"] = "umidade oceânica inventada"
    assert validar_revisao(revisoes)["motivo"] == "evidencia_sem_origem"
