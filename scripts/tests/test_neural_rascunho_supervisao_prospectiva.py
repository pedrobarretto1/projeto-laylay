from __future__ import annotations

import hashlib
import json

import pytest

from mente_laylay.neural.rascunho_supervisao_prospectiva import (
    _grupo_entidade,
    preparar_rascunhos,
)


def _triagem(tmp_path):
    itens = [
        {
            "indice_fila": 10,
            "id_fonte": "a",
            "texto": "liga a luz",
            "grupo_texto": "g_liga",
            "status": "candidato_literal",
            "intent_proposta": "IOT_CONTROL",
            "action_proposta": "on",
            "origem_decisao": "curadoria_ia",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
        {
            "indice_fila": 11,
            "id_fonte": "b",
            "texto": "coloca o volume em 50",
            "grupo_texto": "g_volume",
            "status": "candidato_literal",
            "intent_proposta": "VOLUME",
            "action_proposta": "set",
            "origem_decisao": "curadoria_ia",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
        {
            "indice_fila": 12,
            "id_fonte": "c",
            "texto": "tenta de novo",
            "grupo_texto": "g_contexto",
            "status": "contextual",
            "origem_decisao": "curadoria_ia",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
    ]
    caminho = tmp_path / "fila_revisao.jsonl"
    serializado = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
        for item in itens
    )
    caminho.write_text(serializado, encoding="utf-8")
    return caminho


def _manifesto(fila):
    return {
        "versao": 1,
        "fonte_triagem_sha256": hashlib.sha256(fila.read_bytes()).hexdigest(),
        "origem_decisao": "curadoria_ia",
        "revisao_humana": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
        "propostas": [
            {
                "indice_fila": 10,
                "ato": "pedido",
                "ancora": "liga",
                "alvo": "luz",
            },
            {
                "indice_fila": 11,
                "ato": "pedido",
                "ancora": "coloca",
                "alvo": "volume",
                "parametro": {
                    "nome": "nivel_volume",
                    "valor": 50,
                    "unidade": "percentual",
                    "evidencia": "50",
                },
            },
        ],
    }


def test_rascunhos_usam_gold_proposto_sem_conceder_autoridade(tmp_path):
    fila = _triagem(tmp_path)
    r = preparar_rascunhos(fila, _manifesto(fila))

    assert r["resumo"]["total_candidatos"] == 2
    assert r["contrato"] == {
        "uso": "rascunho_curadoria_ia",
        "revisao_humana": False,
        "dados_prontos_para_treino": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
    }
    por_indice = {x["indice_fila"]: x for x in r["itens"]}
    assert por_indice[10]["exemplo_validacao"]["intent"] == "IOT_CONTROL"
    assert por_indice[10]["exemplo_validacao"]["action"] == "on"
    assert por_indice[10]["exemplo_validacao"]["diagnostico_operacional"]["atos"] == ["pedido"]
    assert por_indice[11]["exemplo_validacao"]["diagnostico_operacional"]["parametros"][0]["valor"] == 50


def test_grupo_entidade_independe_da_acao_para_o_mesmo_alvo():
    ligado = _grupo_entidade("IOT_CONTROL", "on", "luz")
    desligado = _grupo_entidade("IOT_CONTROL", "off", "luz")

    assert ligado == desligado


def test_alvo_canonico_controla_grupo_sem_alterar_literal(tmp_path):
    fila = _triagem(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["propostas"][0]["alvo_canonico"] = "lampada"

    r = preparar_rascunhos(fila, manifesto)
    por_indice = {x["indice_fila"]: x for x in r["itens"]}
    exemplo = por_indice[10]["exemplo_validacao"]

    assert exemplo["validation_entity_group"] == _grupo_entidade(
        "IOT_CONTROL", "on", "lampada"
    )
    assert (
        exemplo["diagnostico_operacional"]["ocorrencias"][0]["alvos"][0]["texto"]
        == "luz"
    )


def test_rascunho_preserva_grupo_texto_para_nao_vazar_repeticao(tmp_path):
    fila = _triagem(tmp_path)
    r = preparar_rascunhos(fila, _manifesto(fila))
    por_indice = {x["indice_fila"]: x for x in r["itens"]}

    assert por_indice[10]["exemplo_validacao"]["validation_group"] == "g_liga"
    assert por_indice[11]["exemplo_validacao"]["validation_group"] == "g_volume"


def test_manifesto_precisa_cobrir_todos_os_candidatos(tmp_path):
    fila = _triagem(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["propostas"].pop()

    with pytest.raises(ValueError, match="cobrir"):
        preparar_rascunhos(fila, manifesto)


def test_span_literal_ambiguo_e_rejeitado(tmp_path):
    fila = _triagem(tmp_path)
    itens = [json.loads(x) for x in fila.read_text(encoding="utf-8").splitlines()]
    itens[0]["texto"] = "liga a luz e liga outra luz"
    fila.write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in itens),
        encoding="utf-8",
    )
    manifesto = _manifesto(fila)

    with pytest.raises(ValueError, match="unic"):
        preparar_rascunhos(fila, manifesto)


def test_volume_set_exige_parametro_literal(tmp_path):
    fila = _triagem(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["propostas"][1].pop("parametro")

    with pytest.raises(ValueError, match="parametro"):
        preparar_rascunhos(fila, manifesto)


def test_manifesto_nao_pode_conceder_autoridade(tmp_path):
    fila = _triagem(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["treino_permitido"] = True

    with pytest.raises(ValueError, match="autoridade"):
        preparar_rascunhos(fila, manifesto)
