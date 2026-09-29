"""Congelamento e contratos da comparação, sem chamadas a modelo."""

import pytest

from scripts.analises import sonda_produtor_criterios_v5 as painel
from scripts.analises.sonda_produtor_criterios_v1 import conferir_proposta
from scripts.analises.sonda_produtor_criterios_v2 import medir_caso


CASOS, REVISAO = painel.carregar_painel()


def test_novo_painel_tem_cinco_positivos_revisados_sem_liberacao():
    assert sum(r["estado"] == "criterio_candidato" for r in REVISAO.values()) == 5
    for caso in CASOS:
        revisao = REVISAO[caso["id"]]
        if revisao["estado"] != "criterio_candidato":
            continue
        resultado = conferir_proposta(caso, revisao, {**revisao, "motivo": ""})
        assert resultado["alinhado_revisao"] is True, caso["id"]
        assert resultado["aprovado_para_producao"] is False


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["id"])
def test_caminho_segmentado_mantem_guardas_com_proponente_controlado(caso):
    revisao = REVISAO[caso["id"]]
    chamadas = []

    def consultar(_sistema, entrada, _formato, **kwargs):
        chamadas.append(entrada)
        if len(chamadas) == 1:
            return {"estado": "fonte_candidata", "motivo": "", "fonte_id": "criterio"}
        # Copiar slots do positivo equivalente também nos negativos: não
        # permitir que erro repetido no proponente burle as guardas reais.
        equivalente = next(r for r in REVISAO.values()
                           if r.get("referente_id") == caso["medida"]["referente_id"])
        return {k: equivalente[k] for k in
                ("referente_id", "atributo", "operador", "limiar", "unidade")}

    resultado = medir_caso(caso, revisao, consulta=consultar,
                           exigir_condicao_unica=True, normalizacao_segmentada=True)
    if revisao["estado"] == "criterio_candidato":
        assert len(chamadas) == 2
        assert resultado["afericao_final"]["alinhado_revisao"] is True
        assert resultado["afericao_final"]["aprovado_para_producao"] is False
    elif caso["id"] == "ESTUFA_OUTRO_SUJEITO":
        assert resultado["afericao_final"]["grafo_estado"] == "sujeito_efeito_pendente"
        assert resultado["afericao_final"]["alinhado_revisao"] is False
    else:
        assert len(chamadas) == 1
        assert resultado["normalizacao"] == "nao_executada"


def test_loader_nao_adapta_revisao_a_resposta_do_modelo(tmp_path, monkeypatch):
    caminho = tmp_path / "revisao.json"
    caminho.write_bytes(painel.REVISAO.read_bytes() + b" ")
    monkeypatch.setattr(painel, "REVISAO", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        painel.carregar_painel()
