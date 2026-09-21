from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from mente_laylay.neural.dataset import validar_exemplo
from mente_laylay.neural.revisao_contextual import (
    preparar_revisao_contextual, escrever_revisao_contextual,
)
from mente_laylay.autonomia.pre_fluxo_contextual import _extrair_alvo_consulta_app
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao


RAIZ = Path(__file__).resolve().parents[1]
FONTE = RAIZ / "mente_laylay/neural/datasets/candidatos/list_windows_onda_v2.jsonl"
REVISAO = RAIZ / "mente_laylay/neural/datasets/revisoes/list_windows_contexto_v1.json"
REVISAO_V2 = REVISAO.with_name("list_windows_contexto_v2.json")


def _insumos():
    return FONTE.read_bytes(), json.loads(REVISAO.read_text(encoding="utf-8"))


def test_revisao_ampliada_preserva_historico_e_separa_dezenove_ambiguidades():
    fonte, anterior = _insumos()
    revisao = json.loads(REVISAO_V2.read_text(encoding="utf-8"))
    resultado = preparar_revisao_contextual(fonte, revisao)
    decisoes = {d["indice"]: d for d in revisao["decisoes"]}
    for decisao in anterior["decisoes"]:
        assert decisoes[decisao["indice"]] == decisao
    esperados = {74, 80, 82, 85, 93, 97, 103, 105, 109, 116, 177, 178, 179,
                 370, 371, 372, 373, 374, 375}
    assert set(decisoes) == esperados
    assert resultado["total_revisados"] == 19
    assert resultado["total_nao_revisados"] == 686
    originais = [json.loads(x) for x in fonte.decode("utf-8").splitlines()]
    assert resultado["nao_revisados"] == [x for i, x in enumerate(originais) if i not in esperados]
    for pendente in resultado["pendentes"]:
        assert pendente["exemplo_historico"] == originais[pendente["indice_fonte"]]
        assert pendente["treino_permitido"] is pendente["autoriza_execucao"] is False
        with pytest.raises(ValueError):
            validar_exemplo(pendente, intents_permitidas={"LIST_WINDOWS"})


@pytest.mark.parametrize("indice", [177, 178, 179])
def test_capacidade_ambigua_nao_vira_recusa_nem_autorizacao(indice):
    resultado = preparar_revisao_contextual(
        FONTE.read_bytes(), json.loads(REVISAO_V2.read_text(encoding="utf-8")),
    )
    item = next(p for p in resultado["pendentes"] if p["indice_fonte"] == indice)
    assert item["fatores_textuais"] == {"dominio_app": True}
    assert item["rotulos_indeterminados"]["extension_factors.ato_consulta"] is None
    assert "extension_factors.dominio_app" not in item["rotulos_indeterminados"]
    assert item["exemplo_historico"]["extension_factors"]["ato_consulta"] is False


@pytest.mark.parametrize("indice", [74, 80, 82, 85, 93, 97, 103, 105, 109, 116])
def test_nome_ambiguo_preserva_consulta_sem_inventar_dominio(indice):
    resultado = preparar_revisao_contextual(
        FONTE.read_bytes(), json.loads(REVISAO_V2.read_text(encoding="utf-8")),
    )
    item = next(p for p in resultado["pendentes"] if p["indice_fonte"] == indice)
    assert item["fatores_textuais"] == {"ato_consulta": True}
    assert item["rotulos_indeterminados"]["extension_factors.dominio_app"] is None
    assert "extension_factors.ato_consulta" not in item["rotulos_indeterminados"]


def test_publicacao_ampliada_nao_modifica_fonte_ou_revisao_anterior(tmp_path):
    caminhos = [FONTE, REVISAO, REVISAO_V2]
    antes = [p.read_bytes() for p in caminhos]
    resumo = escrever_revisao_contextual(FONTE, REVISAO_V2, tmp_path / "ampliada.json")
    assert resumo["total_revisados"] == 19
    assert [p.read_bytes() for p in caminhos] == antes


def test_seis_pronomes_ficam_indeterminados_e_nao_viram_negativos():
    fonte, revisao = _insumos()
    resultado = preparar_revisao_contextual(fonte, revisao)
    assert resultado["total_fonte"] == 705
    assert resultado["total_revisados"] == 6
    assert resultado["total_nao_revisados"] == 699
    originais = [json.loads(x) for x in fonte.decode("utf-8").splitlines()]
    suspensos = {x["indice_fonte"] for x in resultado["pendentes"]}
    assert resultado["nao_revisados"] == [x for i, x in enumerate(originais) if i not in suspensos]
    for item in resultado["pendentes"]:
        assert item["status"] == "requer_contexto"
        assert item["fatores_textuais"] == {"ato_consulta": True}
        assert item["rotulos_indeterminados"]["extension_factors.dominio_app"] is None
        assert "intent" not in item
        assert item["exemplo_historico"] == originais[item["indice_fonte"]]
        assert item["treino_permitido"] is item["autoriza_execucao"] is False
        with pytest.raises(ValueError):
            validar_exemplo(item, intents_permitidas={"LIST_WINDOWS"})


@pytest.mark.parametrize("defeito", ["fonte", "indice", "duplicata", "texto", "autoridade", "treino", "campos", "fatores", "contradicao"])
def test_revisao_invalida_aborta_sem_saida(tmp_path, defeito):
    fonte, revisao = _insumos()
    if defeito == "fonte":
        fonte += b"\n"
    elif defeito == "indice":
        revisao["decisoes"][0]["indice"] = 9999
    elif defeito == "duplicata":
        revisao["decisoes"].append(deepcopy(revisao["decisoes"][0]))
    elif defeito == "texto":
        revisao["decisoes"][0]["texto_sha256"] = "0" * 64
    elif defeito == "autoridade":
        revisao["autoriza_execucao"] = True
    elif defeito == "treino":
        revisao["treino_permitido"] = True
    elif defeito == "campos":
        revisao["decisoes"][0]["campos_dependentes"] = []
    elif defeito == "fatores":
        revisao["decisoes"][0]["fatores_textuais"]["ato_consulta"] = "sim"
    else:
        revisao["decisoes"][0]["fatores_textuais"]["dominio_app"] = True
    with pytest.raises(ValueError):
        preparar_revisao_contextual(fonte, revisao)
    assert list(tmp_path.iterdir()) == []


def test_publicacao_preserva_fonte_e_nao_sobrescreve_relatorio(tmp_path):
    antes = FONTE.read_bytes(), REVISAO.read_bytes()
    saida = tmp_path / "revisao.json"
    resumo = escrever_revisao_contextual(FONTE, REVISAO, saida)
    assert resumo["total_revisados"] == 6
    assert resumo["treino_permitido"] is False
    gravado = saida.read_bytes()
    with pytest.raises(FileExistsError):
        escrever_revisao_contextual(FONTE, REVISAO, saida)
    assert saida.read_bytes() == gravado
    assert (FONTE.read_bytes(), REVISAO.read_bytes()) == antes


@pytest.mark.parametrize("dominio", ["volume", "musica", "aplicativos", "arquivos"])
def test_revisao_generica_nao_inventa_dominio_a_partir_de_pronome(dominio):
    bateria = json.loads((RAIZ / "tests/fixtures/neural/bateria_linguistica_v1.json").read_text(encoding="utf-8"))
    caso = next(x for x in bateria["casos"] if x["id"] == f"{dominio}:referencia_sem_contexto")
    fonte = json.dumps({"text": caso["text"]}, ensure_ascii=False).encode("utf-8")
    revisao = {
        "versao": 1, "origem": "REVISAO_MANUAL",
        "fonte_sha256": hashlib.sha256(fonte).hexdigest(),
        "treino_permitido": False, "autoriza_execucao": False,
        "decisoes": [{
            "indice": 0, "texto_sha256": hashlib.sha256(caso["text"].encode("utf-8")).hexdigest(),
            "motivo": "referência sem contexto", "campos_dependentes": ["domain", "params.alvo"],
            "fatores_textuais": {},
        }],
    }
    saida = preparar_revisao_contextual(fonte, revisao)
    assert saida["nao_revisados"] == []
    assert saida["pendentes"][0]["rotulos_indeterminados"] == {"domain": None, "params.alvo": None}


@pytest.mark.parametrize("app", ["vlc", "opera"])
def test_referencia_e_resolvida_pelo_estado_canonico_nao_pela_neural(app):
    estado = registrar_resultado_execucao(
        {}, resultado={
            "intent": "LIST_WINDOWS", "params": {"alvo": app},
            "status": "estado_app_consultado", "executou": True, "confirmado": True,
        }, texto=f"O {app} está aberto?", executou=True,
        origem="consulta_sistema_local", status="estado_app_consultado",
    )
    assert estado["ultimo_app_janela"] == app
    assert _extrair_alvo_consulta_app({"mente_integrada_estado": estado}, "Ele continua aberto?") == app
    assert _extrair_alvo_consulta_app({"mente_integrada_estado": {}}, "Ele continua aberto?") == ""
    assert _extrair_alvo_consulta_app({"mente_integrada_estado": estado}, "Não confira se ele continua aberto.") == ""
