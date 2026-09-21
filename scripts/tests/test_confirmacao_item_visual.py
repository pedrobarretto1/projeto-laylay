from __future__ import annotations

from mente_laylay.percepcao.visao_jogo.confirmacao_item import (
    precisa_confirmar_item,
    reconciliar_leituras_item,
)


def _item(**updates):
    base = {
        "nome": "Tempest March", "base": "Embossed Boots",
        "categoria": "Boots", "raridade": "Rare",
        "atributos": ["15% increased Movement Speed"],
        "termos_pesquisa": ["Embossed Boots"], "confianca": 0.7,
    }
    base.update(updates)
    return base


def test_confirmacao_so_ocorre_quando_existe_recorte_separado() -> None:
    assert precisa_confirmar_item(_item(), multiplas_imagens=True) is True
    assert precisa_confirmar_item(_item(), multiplas_imagens=False) is False
    assert precisa_confirmar_item(_item(confianca=0.9), multiplas_imagens=True) is False


def test_duas_leituras_equivalentes_elevam_confianca() -> None:
    item, diagnostico = reconciliar_leituras_item(
        _item(confianca=0.7),
        _item(nome="Tempest  March", confianca=0.82),
    )
    assert diagnostico["status"] == "confirmada"
    assert item["nome"] == "Tempest March"
    assert item["confianca"] >= 0.78


def test_conflito_de_nome_ou_base_bloqueia_confianca_para_pesquisa() -> None:
    item, diagnostico = reconciliar_leituras_item(
        _item(),
        _item(nome="Storm Treads", base="Silk Slippers", confianca=0.8),
    )
    assert diagnostico["status"] == "conflito"
    assert set(diagnostico["conflitos"]) >= {"nome", "base"}
    assert item["nome"] == ""
    assert item["base"] == ""
    assert item["confianca"] <= 0.44


def test_recorte_recupera_leitura_ausente_sem_fingir_confirmacao() -> None:
    item, diagnostico = reconciliar_leituras_item({}, _item(confianca=0.91))
    assert diagnostico["status"] == "recuperada_por_recorte"
    assert item["base"] == "Embossed Boots"
    assert item["confianca"] == 0.52
