from copy import deepcopy
import json
from pathlib import Path

import pytest

from mente_laylay.neural.comparacao_linguistica import (
    comparar_pedidos, criar_preditor_neural, prever_python_sem_contexto,
)


def bateria(*rotulos):
    return {
        "treino_permitido": False, "autoriza_execucao": False,
        "casos": [
            {"id": str(i), "text": f"frase {i}", "autoriza_execucao": False,
             "contexto": None, "dominio_da_fatia": "teste", "fenomeno": "pedido",
             "esperado": {"pedido_operacional": valor, "requer_contexto": False}}
            for i, valor in enumerate(rotulos)
        ],
    }


def preditor(*valores):
    itens = iter(valores)
    return lambda texto: {"pedido_operacional": next(itens)}


def test_referencia_independente_distingue_ganhos_regressoes_e_erros_compartilhados():
    r = comparar_pedidos(
        bateria(True, True, False, False),
        python=preditor(True, False, True, False),
        neural=preditor(False, True, True, False),
    )
    assert r["pareado"] == {
        "regressao_neural": 1, "ganho_neural": 1, "ambos_erram": 1, "ambos_acertam": 1,
    }
    for nome in ("python", "neural"):
        assert r["metricas"][nome]["falsos_pedidos"] == 1
        assert r["metricas"][nome]["pedidos_perdidos"] == 1
        assert r["metricas"][nome]["taxa_acerto_total"] == .5


@pytest.mark.parametrize("retorno", [{}, {"pedido_operacional": "false"}, {"pedido_operacional": None}])
def test_saida_invalida_nao_vira_acerto_negativo(retorno):
    r = comparar_pedidos(bateria(False), python=preditor(False), neural=lambda texto: retorno)
    assert r["pareado"] == {"inconclusivo": 1}
    assert r["metricas"]["neural"]["falhas_inferencia"] == 1
    assert r["metricas"]["neural"]["taxa_acerto_total"] == 0


def test_excecao_nao_some_do_denominador_nem_interrompe_outro_preditor():
    def falha(texto):
        raise RuntimeError("não publicar detalhes privados")
    r = comparar_pedidos(bateria(False), python=falha, neural=preditor(False))
    assert r["casos"][0]["python"] == {"erro": "RuntimeError"}
    assert r["metricas"]["python"]["total"] == 1
    assert r["metricas"]["neural"]["acertos"] == 1


def test_contexto_nao_e_inventado_nem_rotulo_entregue_ao_modelo():
    b = bateria(True, True)
    b["casos"][1]["esperado"]["requer_contexto"] = True
    original = deepcopy(b)
    recebidos = []
    def prever(texto):
        recebidos.append(texto)
        return {"pedido_operacional": True}
    r = comparar_pedidos(b, python=prever, neural=prever)
    assert recebidos == ["frase 0", "frase 0"]
    assert r["excluidos"] == [{"id": "1", "motivo": "contexto_fora_do_escopo_v1"}]
    assert b == original
    assert r["promocao_permitida"] is False
    assert r["autoriza_execucao"] is False


@pytest.mark.parametrize("erro", ["id", "rotulo", "autoridade", "treino"])
def test_valida_bateria_inteira_antes_de_inferir(erro):
    b = bateria(True, False)
    if erro == "id":
        b["casos"][1]["id"] = "0"
    elif erro == "rotulo":
        del b["casos"][1]["esperado"]["pedido_operacional"]
    elif erro == "autoridade":
        b["casos"][1]["autoriza_execucao"] = True
    else:
        b["treino_permitido"] = True
    def nao_chamar(texto):
        pytest.fail("inferência antes da validação completa")
    with pytest.raises(ValueError):
        comparar_pedidos(b, python=nao_chamar, neural=nao_chamar)


@pytest.mark.parametrize("texto,esperado", [
    ("abaixa o volume", True), ("não abre o navegador", False),
    ("estou apenas escrevendo: abre o Opera", False),
])
def test_adaptador_reutiliza_classificador_real_sem_executor(texto, esperado):
    assert prever_python_sem_contexto(texto)["pedido_operacional"] is esperado


@pytest.mark.parametrize("negado,ood,esperado", [(False, False, True), (True, False, False), (False, True, False)])
def test_neural_expoe_head_separado_de_candidato_de_sombra(negado, ood, esperado):
    class Modelo:
        def prever(self, texto):
            return {"is_command": True, "negated": negado, "ood": ood}
    p = criar_preditor_neural(Modelo())("exemplo")
    assert p["pedido_operacional"] is esperado
    assert p["head_comando"] is True


def test_bateria_existente_preservada_com_exclusoes_explicitas():
    caminho = Path(__file__).parent / "fixtures/neural/bateria_linguistica_v1.json"
    b = json.loads(caminho.read_text(encoding="utf-8"))
    r = comparar_pedidos(b, python=prever_python_sem_contexto, neural=lambda t: {"pedido_operacional": False})
    assert r["total_bateria"] == 44
    assert len(r["excluidos"]) == 4
    assert r["metricas"]["python"]["total"] == 40
    assert len(r["fatias"]["dominio"]) == 4
