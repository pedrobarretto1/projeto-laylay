from __future__ import annotations

import hashlib
import json

import pytest

from mente_laylay.neural.triagem_prospectiva_operacional import (
    preparar_triagem,
)


def _fila(tmp_path):
    itens = [
        {
            "id": "a",
            "texto": "liga a luz",
            "destinacao": "revisao_pendente",
            "registro_origem": {"sessao_conversa_ts": 1.0},
        },
        {
            "id": "b",
            "texto": "liga a luz",
            "destinacao": "revisao_pendente",
            "registro_origem": {"sessao_conversa_ts": 2.0},
        },
        {
            "id": "c",
            "texto": "tenta de novo",
            "destinacao": "revisao_pendente",
            "registro_origem": {"sessao_conversa_ts": 2.0},
        },
        {
            "id": "d",
            "texto": "caso de teste",
            "destinacao": "teste_declarado",
            "registro_origem": {"sessao_conversa_ts": 3.0},
        },
    ]
    caminho = tmp_path / "fila.jsonl"
    bruto = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
        for item in itens
    )
    caminho.write_text(bruto, encoding="utf-8")
    resumo = {
        "fila_sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
        "destinacoes": {"revisao_pendente": 3, "teste_declarado": 1},
        "dados_prontos": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
    }
    resumo_path = tmp_path / "resumo.json"
    resumo_path.write_text(json.dumps(resumo), encoding="utf-8")
    return caminho, resumo_path


def _manifesto(fila):
    return {
        "versao": 1,
        "fonte_fila_sha256": hashlib.sha256(fila.read_bytes()).hexdigest(),
        "origem_decisao": "curadoria_ia",
        "revisao_humana": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
        "decisoes": [
            {
                "indice_fila": 1,
                "status": "candidato_literal",
                "motivo": "iot literal",
                "intent_proposta": "IOT_CONTROL",
                "action_proposta": "on",
            },
            {
                "indice_fila": 2,
                "status": "candidato_literal",
                "motivo": "iot literal repetido",
                "intent_proposta": "IOT_CONTROL",
                "action_proposta": "on",
            },
            {
                "indice_fila": 3,
                "status": "contextual",
                "motivo": "depende do turno anterior",
            },
        ],
    }


def test_triagem_cobre_pendentes_sem_promover_autoridade(tmp_path):
    fila, resumo = _fila(tmp_path)
    relatorio = preparar_triagem(fila, resumo, _manifesto(fila))

    assert relatorio["resumo"]["total_pendentes"] == 3
    assert relatorio["resumo"]["status"] == {
        "candidato_literal": 2,
        "contextual": 1,
    }
    assert relatorio["contrato"] == {
        "uso": "fila_revisao_operacional",
        "revisao_humana": False,
        "dados_prontos_para_treino": False,
        "treino_permitido": False,
        "autoriza_execucao": False,
        "autoriza_promocao": False,
    }


def test_textos_repetidos_compartilham_grupo_e_nao_viram_independentes(tmp_path):
    fila, resumo = _fila(tmp_path)
    relatorio = preparar_triagem(fila, resumo, _manifesto(fila))
    candidatos = [
        item for item in relatorio["itens"]
        if item["status"] == "candidato_literal"
    ]

    assert candidatos[0]["grupo_texto"] == candidatos[1]["grupo_texto"]
    assert relatorio["resumo"]["textos_distintos_pendentes"] == 2
    assert relatorio["resumo"]["eventos_repetidos"] == 1
    assert relatorio["resumo"]["candidatos_literais_eventos"] == 2
    assert relatorio["resumo"]["candidatos_literais_textos_distintos"] == 1
    assert relatorio["resumo"]["candidatos_literais_eventos_repetidos"] == 1


@pytest.mark.parametrize("mutacao", ["faltando", "duplicado", "extra"])
def test_manifesto_precisa_cobrir_pendentes_exatamente_uma_vez(tmp_path, mutacao):
    fila, resumo = _fila(tmp_path)
    manifesto = _manifesto(fila)
    if mutacao == "faltando":
        manifesto["decisoes"].pop()
    elif mutacao == "duplicado":
        manifesto["decisoes"].append(dict(manifesto["decisoes"][0]))
    else:
        manifesto["decisoes"].append({
            "indice_fila": 4,
            "status": "fora_perfil",
            "motivo": "nao deveria entrar",
        })

    with pytest.raises(ValueError, match="cobrir"):
        preparar_triagem(fila, resumo, manifesto)


def test_candidato_literal_exige_variante_do_catalogo(tmp_path):
    fila, resumo = _fila(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["decisoes"][0]["action_proposta"] = "explode"

    with pytest.raises(ValueError, match="variante"):
        preparar_triagem(fila, resumo, manifesto)


@pytest.mark.parametrize("campo", [
    "revisao_humana",
    "treino_permitido",
    "autoriza_execucao",
    "autoriza_promocao",
])
def test_manifesto_nao_pode_conceder_autoridade(tmp_path, campo):
    fila, resumo = _fila(tmp_path)
    manifesto = _manifesto(fila)
    manifesto[campo] = True

    with pytest.raises(ValueError, match="autoridade|revisao"):
        preparar_triagem(fila, resumo, manifesto)


def test_hash_da_fila_e_vinculo_obrigatorio(tmp_path):
    fila, resumo = _fila(tmp_path)
    fila.write_text(fila.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA"):
        preparar_triagem(fila, resumo, _manifesto(fila))


def test_manifesto_precisa_declarar_sha_da_fila_de_origem(tmp_path):
    fila, resumo = _fila(tmp_path)
    manifesto = _manifesto(fila)
    manifesto["fonte_fila_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="manifesto.*SHA"):
        preparar_triagem(fila, resumo, manifesto)
