"""A selecao nao autoriza a normalizacao a trocar fonte nem publicar fala."""

import pytest

from scripts.analises import sonda_produtor_criterios_v2 as sonda
from scripts.analises.sonda_produtor_criterios_v1 import conferir_proposta


CASOS, REVISAO = sonda.carregar_painel()
POR_ID = {caso["id"]: caso for caso in CASOS}
NORMALIZADOS = (
    "referente_id", "atributo", "operador", "limiar", "unidade",
    "direcao_implicacao", "citacao_condicao",
)


def test_segmentacao_preserva_offsets_direcao_e_nao_usa_revisao():
    fonte = "O motor é lento apenas se a latência do motor ficar acima de 12 ms."
    partes = sonda.preparar_normalizacao_segmentada(fonte, "lento")
    assert partes["estado"] == "segmentos_literais_revisao_pendente"
    assert partes["direcao"]["direcao"] == "condicoes_necessarias"
    for campo in ("condicao", "efeito"):
        trecho = partes[campo]
        assert fonte[trecho["inicio"]:trecho["fim"]] == trecho["citacao"]
    assert partes["condicao"]["citacao"] == "a latência do motor ficar acima de 12 ms"
    assert partes["efeito"]["citacao"] == "O motor é lento"
    assert partes["autoriza_efeito"] is False


@pytest.mark.parametrize("fonte", [
    "Se a carga cair, o alarme de bateria fraca toca.",
    "Se a carga cair, a bateria não é fraca.",
    "Se a carga cair e a tensão diminuir, a bateria é fraca.",
    "A bateria fraca marcou 5 V.",
    "Quando a carga cair, a bateria é fraca.",
])
def test_segmentacao_inconclusiva_nao_pede_slots_ao_modelo(fonte):
    from copy import deepcopy
    caso = deepcopy(POR_ID["MOTOR_CRITERIO_INSTAVEL"])
    caso["rotulo_alvo"] = "fraca"
    caso["fontes"][-1]["texto"] = fonte
    chamadas = []

    def consulta(*args, **kwargs):
        chamadas.append(args)
        return _selecao("criterio")

    resultado = sonda.medir_caso(caso, {}, consulta=consulta,
                                 normalizacao_segmentada=True)
    assert len(chamadas) == 1
    assert resultado["normalizacao"] == "nao_executada"
    assert resultado["segmentacao"]["estado"] == "segmentacao_pendente"


@pytest.mark.parametrize("extra", [None, "fonte_id", "citacao_condicao", "direcao_implicacao"])
def test_slots_nao_podem_sobrescrever_campos_do_host(extra):
    caso = POR_ID["MOTOR_CRITERIO_INSTAVEL"]
    chamadas = []
    slots = {campo: REVISAO[caso["id"]][campo] for campo in
             ("referente_id", "atributo", "operador", "limiar", "unidade")}

    def consulta(_sistema, entrada, formato, **kwargs):
        chamadas.append(entrada)
        if len(chamadas) == 1:
            return _selecao("criterio")
        assert set(formato["required"]) == set(slots)
        assert set(formato["properties"]) == set(slots)
        assert "medida" not in entrada
        assert entrada["condicao_literal"]["citacao"] not in {"", entrada["fonte_integral"]}
        return slots if extra is None else {**slots, extra: "inventado"}

    resultado = sonda.medir_caso(caso, REVISAO[caso["id"]], consulta=consulta,
                                 normalizacao_segmentada=True)
    assert len(chamadas) == 2
    if extra is not None:
        assert resultado["afericao_final"]["estado"] == "normalizacao_invalida"
    else:
        assert resultado["proposta"]["direcao_implicacao"] == "condicoes_suficientes"
        assert resultado["proposta"]["citacao_condicao"] == (
            "a vibração do motor ficar acima de 5 mm/s"
        )
        assert resultado["afericao_final"]["grafo_estado"] == (
            "condicao_numerica_satisfeita_relacao_pendente"
        )
        # A revisão antiga não inclui o artigo. Não a reescrever nem relaxar
        # a comparação exata para inflar o placar deste replay diagnóstico.
        assert resultado["afericao_final"]["alinhado_revisao"] is False
    assert resultado["afericao_final"]["aprovado_para_producao"] is False


def _selecao(fonte_id):
    return {"estado": "fonte_candidata", "motivo": "", "fonte_id": fonte_id}


def _abstencao(motivo):
    return {"estado": "abster", "motivo": motivo, "fonte_id": ""}


def _normalizacao(id_caso):
    return {campo: REVISAO[id_caso][campo] for campo in NORMALIZADOS}


def test_painel_historico_preserva_revisao_sem_mascarar_vinculo_ausente():
    assert len(CASOS) == 9
    assert set(POR_ID) == set(REVISAO)
    for caso in CASOS:
        revisao = REVISAO[caso["id"]]
        proposta = (
            {"estado": "criterio_candidato", "motivo": "",
             "fonte_id": revisao["fonte_id"], **_normalizacao(caso["id"])}
            if revisao["estado"] == "criterio_candidato" else
            {"estado": "abster", "motivo": revisao["motivo"],
             **{campo: "" for campo in ("fonte_id", *NORMALIZADOS)}}
        )
        afericao = conferir_proposta(caso, revisao, proposta)
        if caso["id"] == "VOLUME_CRITERIO_BAIXO":
            # "volume do reservatório" não tem alias explícito "volume".
            # Não editar o painel congelado para adaptar-se à nova guarda.
            assert afericao["alinhado_revisao"] is False
            assert afericao["estado"] == "grafo_rejeitou_proposta"
            assert afericao["grafo_estado"] == "sujeito_efeito_pendente"
        else:
            assert afericao["alinhado_revisao"] is True
        assert afericao["aprovado_para_producao"] is False


def test_citacao_integral_ancora_numero_sem_aprovar_semantica():
    for id_caso in ("MOTOR_CRITERIO_INSTAVEL", "TESTE_CRITERIO_CONTAGEM"):
        caso = POR_ID[id_caso]
        revisao = REVISAO[id_caso]
        fonte = next(item["texto"] for item in caso["fontes"]
                     if item["id"] == revisao["fonte_id"])
        proposta = {
            "estado": "criterio_candidato", "motivo": "",
            **_normalizacao(id_caso), "fonte_id": revisao["fonte_id"],
            "citacao_condicao": fonte,
        }
        resultado = conferir_proposta(caso, revisao, proposta)
        assert resultado["grafo_estado"] == (
            "condicao_numerica_satisfeita_relacao_pendente"
        )
        assert resultado["estado"] == "proposta_divergente"
        assert resultado["aprovado_para_producao"] is False


def test_guarda_separa_fonte_de_acao_criterio_e_referente_ambiguo():
    assert sonda.conferir_selecao(
        POR_ID["VOLUME_REGRA_ALARME"], _selecao("alarme"),
    )["estado"] == "rotulo_sem_ancora_literal"
    assert sonda.conferir_selecao(
        POR_ID["MOTOR_CRITERIO_INSTAVEL"], _selecao("criterio"),
    )["estado"] == "fonte_literal_candidata_revisao_pendente"
    assert sonda.conferir_selecao(
        POR_ID["PNEUS_REFERENTE_ABERTO"], _selecao("criterio"),
    )["estado"] == "referente_indeterminado"


def test_primeira_etapa_oferece_so_fontes_com_rotulo_literal():
    caso = POR_ID["MOTOR_CRITERIO_INSTAVEL"]
    observado = {}

    def consultar(_sistema, entrada, formato, **_kwargs):
        observado["entrada"] = entrada
        observado["formato"] = formato
        return _abstencao("outro_indeterminado")

    sonda.medir_caso(caso, REVISAO[caso["id"]], consulta=consultar)
    assert observado["entrada"]["fontes_com_rotulo_literal"] == ["criterio"]
    assert observado["formato"]["properties"]["fonte_id"]["enum"] == [
        "", "criterio",
    ]
    assert "revisao" not in observado["entrada"]


def test_selecao_apenas_literal_nao_e_prova_semantica():
    caso = POR_ID["TESTE_APENAS_SE"]
    resultado = sonda.confrontar_selecao(
        caso, REVISAO[caso["id"]], _selecao("criterio"),
    )
    assert resultado["estado_revisao"] == "selecao_alinhada"
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


def test_abstencao_nao_chama_normalizacao_mesmo_se_revisao_divergir(monkeypatch):
    caso = POR_ID["VOLUME_SEM_FAIXA"]
    chamadas = []

    def consultar(_sistema, entrada, _formato, **_kwargs):
        chamadas.append(entrada)
        return _abstencao("criterio_ausente")

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    revisao_trocada = {"estado": "criterio_candidato", "fonte_id": "leitura"}
    resultado = sonda.medir_caso(caso, revisao_trocada)
    assert len(chamadas) == 1
    assert "revisao" not in chamadas[0]
    assert resultado["normalizacao"] == "nao_executada"
    assert resultado["afericao_selecao"]["estado_revisao"] == "abstencao_divergente"


def test_normalizacao_recebe_fonte_integral_sem_poder_trocar_id(monkeypatch):
    caso = POR_ID["MOTOR_CRITERIO_INSTAVEL"]
    chamadas = []

    def consultar(_sistema, entrada, _formato, **_kwargs):
        chamadas.append(entrada)
        if len(chamadas) == 1:
            return _selecao("criterio")
        return _normalizacao(caso["id"])

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    resultado = sonda.medir_caso(caso, REVISAO[caso["id"]])
    assert len(chamadas) == 2
    assert chamadas[1]["fonte_id"] == "criterio"
    assert chamadas[1]["fonte_integral"] == caso["fontes"][1]["texto"]
    assert "revisao" not in chamadas[1]
    assert resultado["afericao_final"]["estado"] == (
        "proposta_alinhada_revisao_pendente"
    )
    assert resultado["afericao_final"]["aprovado_para_producao"] is False


def test_normalizacao_nao_pode_injetar_nova_fonte_id(monkeypatch):
    caso = POR_ID["MOTOR_CRITERIO_INSTAVEL"]
    chamadas = 0

    def consultar(_sistema, _entrada, _formato, **_kwargs):
        nonlocal chamadas
        chamadas += 1
        return (_selecao("criterio") if chamadas == 1 else
                {**_normalizacao(caso["id"]), "fonte_id": "leitura"})

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    resultado = sonda.medir_caso(caso, REVISAO[caso["id"]])
    assert chamadas == 2
    assert resultado["afericao_final"]["estado"] == "normalizacao_invalida"
    assert resultado["afericao_final"]["aprovado_para_producao"] is False


def test_fonte_ancorada_chama_etapa_2_sem_consultar_gabarito(monkeypatch):
    caso = POR_ID["MOTOR_CRITERIO_INSTAVEL"]
    chamadas = 0

    def consultar(_sistema, _entrada, _formato, **_kwargs):
        nonlocal chamadas
        chamadas += 1
        return (_selecao("criterio") if chamadas == 1 else
                _normalizacao(caso["id"]))

    monkeypatch.setattr(sonda, "_consultar_modelo", consultar)
    revisao_trocada = {"estado": "abster", "motivo": "criterio_ausente"}
    resultado = sonda.medir_caso(caso, revisao_trocada)
    assert chamadas == 2
    assert resultado["afericao_selecao"]["estado_revisao"] == "selecao_divergente"
    assert resultado["afericao_final"]["estado"] == "forcou_criterio_ausente"
    assert resultado["afericao_final"]["aprovado_para_producao"] is False


def test_consulta_injetada_reusa_mesmas_guardas_sem_trocar_decisao():
    caso = POR_ID["MOTOR_CRITERIO_INSTAVEL"]
    chamadas = []

    def consultar(_sistema, entrada, _formato, **_kwargs):
        chamadas.append(entrada)
        return (_selecao("criterio") if len(chamadas) == 1 else
                _normalizacao(caso["id"]))

    resultado = sonda.medir_caso(
        caso, REVISAO[caso["id"]], consulta=consultar,
    )
    assert len(chamadas) == 2
    assert resultado["afericao_selecao"]["estado_revisao"] == "selecao_alinhada"
    assert resultado["afericao_final"]["estado"] == (
        "proposta_alinhada_revisao_pendente"
    )
    assert resultado["afericao_final"]["aprovado_para_producao"] is False
