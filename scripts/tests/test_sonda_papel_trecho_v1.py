"""Papel proposto de uma ocorrência não é decisão/ausência/autoridade."""

from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_papel_trecho_v1 as sonda
from scripts.analises import sonda_selecao_literal_proposicao_v1 as literal
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


# Loader congelado é testado abaixo; fixtures ainda não consultam modelo.
CASOS = json.loads(sonda.ENTRADAS.read_text(encoding="utf-8"))["casos"]
OURO = json.loads(sonda.REVISAO.read_text(encoding="utf-8"))["casos"]


def caso(identificador):
    return next(c for c in CASOS if c["id"] == identificador)


def assert_inerte(r):
    assert all(r[k] is False for k in literal.contrato.BASE)
    assert not {"autoriza_execucao", "ausencia_verificada", "operacao_principal", "tratado", "referente_id"} & r.keys()


@pytest.mark.parametrize("id_caso", list(OURO))
def test_rotulo_alinhado_localmente_nao_e_interpretacao_certificada(id_caso):
    c = caso(id_caso)
    entrada = sonda.preparar_entrada(c)
    r = sonda.conferir_papel(c, entrada, {"papel": OURO[id_caso]})
    assert r["estado"] == "papel_proposto_revisao_pendente"
    assert r["entrada"] == entrada and r["entrada"] is not entrada
    assert sonda.aferir({"conferencia": r}, OURO[id_caso])["papel_alinhado_revisao_local"]
    assert_inerte(r)


def test_mesmo_conteudo_literal_tem_funcoes_diferentes_sem_parser_local():
    for par in (f"P{i:02}" for i in range(1, 7)):
        a, b = [c for c in CASOS if c["par"] == par]
        assert sonda.preparar_entrada(a)["foco"]["texto"] == sonda.preparar_entrada(b)["foco"]["texto"]
        assert OURO[a["id"]] != OURO[b["id"]]
        # A guarda admite qualquer rótulo tipado: não finge verificar papel.
        for c in (a, b):
            r = sonda.conferir_papel(c, sonda.preparar_entrada(c), {"papel": "nome_designacao"})
            assert r["estado"] == "papel_proposto_revisao_pendente"
            assert_inerte(r)


def test_nome_com_aparencia_de_comando_nao_bloqueia_proposta_por_lexico():
    c = caso("P05A")
    r = sonda.conferir_papel(c, sonda.preparar_entrada(c), {"papel": "operacao_mencionada"})
    assert r["estado"] == "papel_proposto_revisao_pendente"
    assert sonda.aferir({"conferencia": r}, OURO[c["id"]])["papel_alinhado_revisao_local"] is False
    assert_inerte(r)


def test_proposta_de_papel_nao_substitui_modalidade_nem_escreve_vigencia(monkeypatch):
    def proibida(*a, **k):
        raise AssertionError("papel não tem autoridade")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    r = sonda.medir_caso(caso("P03B"), consulta=lambda *a, **k: {"papel": "operacao_mencionada"})
    assert r["entrada"]["foco"]["texto"].startswith("não ")
    assert_inerte(r)


def test_modelo_recebe_fonte_integral_foco_autentico_sem_ouro_par_ou_id_caso():
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, deepcopy(entrada), formato, kwargs))
        assert set(entrada) == {"fonte", "aspas_sintaticas", "foco"}
        assert "P06" not in json.dumps(entrada) and "par" not in entrada
        assert "gabarito" not in entrada and "candidatos" not in entrada
        # Mutação do transporte injetado não pode mudar o envelope guardado.
        entrada["foco"]["texto"] = "falso"
        return {"papel": "operacao_mencionada"}
    c = caso("P06B")
    r = sonda.medir_caso(c, consulta=consulta)
    assert len(chamadas) == 1 and chamadas[0][0] == sonda.SISTEMA
    assert chamadas[0][1]["fonte"]["texto"] == c["texto"]
    assert set(chamadas[0][2]["properties"]) == {"papel"}
    assert chamadas[0][3]["modelo"] == "qwen3:4b-instruct"
    assert r["conferencia"]["estado"] == "papel_proposto_revisao_pendente"
    assert r["entrada"]["foco"]["texto"] == "gire a válvula"


def test_aspas_aninhadas_conservam_parentesco_e_contexto_exterior():
    c = caso("P06A")
    entrada = sonda.preparar_entrada(c)
    a, b = entrada["aspas_sintaticas"]["regioes_entre_aspas"]
    assert b["pai_id"] == a["id"] and entrada["foco"]["regiao_aspas_id"] == b["id"]
    assert "a peça chamada" in entrada["fonte"]["texto"]
    foco = entrada["foco"]
    assert entrada["fonte"]["texto"][foco["inicio"]:foco["fim"]] == foco["texto"]


def test_foco_repetido_nao_perde_segunda_ocorrencia():
    c = {"id": "controle", "texto": 'O botão “abra o portão” repete a frase “abra o portão”.', "foco_id": "c2"}
    entrada = sonda.preparar_entrada(c)
    catalogo = literal.preparar_catalogo(c)
    assert entrada["foco"] == catalogo["candidatos"][2]
    assert entrada["foco"]["inicio"] > catalogo["candidatos"][1]["inicio"]


@pytest.mark.parametrize("proposta", [None, {}, {"papel": []}, {"papel": "comando_autorizado"},
                                       {"papel": "operacao_mencionada", "autoriza_efeito": True}])
def test_proposta_invalida_nao_publica_papel(proposta):
    c = caso("P01B")
    r = sonda.conferir_papel(c, sonda.preparar_entrada(c), proposta)
    assert r["papel_proposto"] is None and r["estado"] == "proposta_invalida"
    assert_inerte(r)


@pytest.mark.parametrize("valor", [0.0, False, "0", 1])
def test_envelope_com_tipo_ou_offset_adulterado_e_rejeitado(valor):
    c = {"id": "controle", "texto": "Não abra a janela.", "foco_id": "c0"}
    entrada = sonda.preparar_entrada(c)
    entrada["foco"]["inicio"] = valor
    r = sonda.conferir_papel(c, entrada, {"papel": "operacao_mencionada"})
    assert r["estado"] == "entrada_adulterada" and r["papel_proposto"] is None
    assert_inerte(r)


def test_contexto_adulterado_nao_mantem_papel_de_fonte_original():
    c = caso("P01A")
    entrada = sonda.preparar_entrada(c)
    entrada["fonte"]["texto"] = caso("P01B")["texto"]
    r = sonda.conferir_papel(c, entrada, {"papel": "operacao_mencionada"})
    assert r["estado"] == "entrada_adulterada" and r["papel_proposto"] is None


@pytest.mark.parametrize("foco", [None, "c99", "indeterminado", 1])
def test_foco_invalido_nunca_consulta_modelo(foco):
    c = {**caso("P01A"), "foco_id": foco}
    with pytest.raises(ValueError, match="foco_host_invalido"):
        sonda.medir_caso(c, consulta=lambda *a, **k: pytest.fail("não consultar"))


def test_aspas_incoerentes_nao_geram_foco_falso_ou_ausencia():
    c = {"id": "controle", "texto": 'O botão “abra o portão.', "foco_id": "c1"}
    with pytest.raises(ValueError):
        sonda.preparar_entrada(c)
    # Fonte integral ainda existe; papel segue só proposto e aspas incoerentes visíveis.
    c["foco_id"] = "c0"
    entrada = sonda.preparar_entrada(c)
    assert entrada["aspas_sintaticas"]["aspas_coerentes"] is False
    r = sonda.conferir_papel(c, entrada, {"papel": "indeterminado"})
    assert_inerte(r)


def test_resumo_exige_os_dois_contextos_sem_contar_erro_como_acerto():
    resultados = [{"id": c["id"], "afericao": {"saida_valida": True,
                  "papel_alinhado_revisao_local": c["id"] != "P01A"}} for c in CASOS]
    r = sonda.aferir_pares(CASOS, resultados, OURO)
    assert r["papeis_alinhados"] == 15 and r["pares_contextuais_completos"] == 5
    assert r["por_papel"]["nome_designacao"] == {"total": 6, "alinhados": 5}
    assert r["avalia_pipeline_completo"] is False
    assert_inerte(r)


@pytest.mark.parametrize("tipo", ["duplicado", "desconhecido", "faltante"])
def test_resumo_rejeita_cobertura_adulterada_sem_placar_parcial(tipo):
    resultados = [{"id": c["id"], "afericao": {"saida_valida": True,
                  "papel_alinhado_revisao_local": True}} for c in CASOS]
    if tipo == "duplicado":
        resultados.append(deepcopy(resultados[0]))
    elif tipo == "desconhecido":
        resultados[0]["id"] = "X99"
    else:
        resultados.pop()
    r = sonda.aferir_pares(CASOS, resultados, OURO)
    assert r["tipo"] == "resumo_invalido"
    assert "papeis_alinhados" not in r and "validos" not in r
    assert_inerte(r)


def test_painel_e_revisao_congelados_sem_modelo():
    casos, ouro = sonda.carregar_painel()
    assert casos == CASOS and ouro == OURO


def test_loader_rejeita_revisao_alterada_sem_recongelar(monkeypatch, tmp_path):
    revisao = tmp_path / "revisao.json"
    revisao.write_text('{"casos": {}}', encoding="utf-8")
    monkeypatch.setattr(sonda, "REVISAO", revisao)
    with pytest.raises(ValueError, match="apos congelamento"):
        sonda.carregar_painel()
