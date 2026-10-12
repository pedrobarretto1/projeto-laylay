"""RED de cobertura: prioridade de um ato não encerra todos os atos do turno.

As portas de efeito/modelo/entrega são isoladas; o RED é de roteamento, não
frequência do Qwen, efeito físico ou qualidade de uma resposta gerada.
"""
import json

import pytest

from scripts.analises.sonda_prioridade_turnos_mistos import coletar


@pytest.fixture(scope="module")
def prioridade_instalada():
    return coletar()


@pytest.fixture(scope="module")
def contraprova_retorno():
    return coletar(contraprova_retornar_nao_tratado=True)


def test_composicao_instalada_publica_contrato_explicativo_do_owner(prioridade_instalada):
    cobertos = []
    for resultado in prioridade_instalada["resultados"]:
        turno = resultado["turno"]
        for segmento in turno["segmentos"]:
            dados = segmento.get("contrato_explicativo")
            if not dados:
                continue
            assert segmento["autoriza_execucao"] is False
            assert dados["fonte"] == "interpretador_canonico"
            assert dados["autoriza_execucao"] is False
            if dados["relacao"] == "consulta_significado":
                inicio, fim = dados["intervalo_objeto"]
                assert dados["texto_ato"][inicio:fim] == dados["objeto_textual"]
            cobertos.append(dados["relacao"])
    assert "consulta_significado" in cobertos
    assert "condicao_nao_verificada" in cobertos


@pytest.fixture(scope="module")
def ablacao_instalada():
    return coletar(ablacao_projecao=True)


def test_ablacao_acrescenta_so_fatos_canonicos_sem_gold_no_pedido(ablacao_instalada):
    assert ablacao_instalada["fontes_estaveis"]
    assert not ablacao_instalada["efeitos_externos_executados"]
    grupos = {}
    for r in ablacao_instalada["resultados"]:
        assert len(r["recebidos"]) == len(r["modelos"]) == len(r["textos_publicados"]) == 1
        assert not r["reentrada_porta_operacional"]
        grupos.setdefault((r["caso"]["id"], r["caso"]["repeticao"]), {})[r["caso"]["variante"]] = r
    assert len(grupos) == 12
    for grupo in grupos.values():
        controle, projecao = grupo["controle"], grupo["intervencao"]
        mc, mp = controle["modelos"][0]["mensagens"], projecao["modelos"][0]["mensagens"]
        assert mc[0] == mp[0]
        dc, dp = json.loads(mc[1]["content"]), json.loads(mp[1]["content"])
        fatos = dp.pop("fatos_conversacionais")
        assert dp == dc
        assert "esperados" not in fatos and "propostos" not in fatos
        assert fatos["autoriza_execucao"] is False
        assert fatos["pendencia_criada_por_este_complemento"] is False
        assert fatos["pendencias_de_outros_fluxos"] == "nao_consultadas"
        assert fatos["capacidades"]["fonte"] == "catalogo_vivo"
        assert fatos["capacidades"]["autoriza_execucao"] is False
        assert fatos["capacidades"]["documentacao_turno_id"] == projecao["turno"]["id"]
        assert all(a["autoriza_execucao"] is False for a in fatos["atos_restantes"])
        assert [a["indice"] for a in fatos["atos_restantes"]] == [
            s["indice"] for s in projecao["turno"]["segmentos"] if not s["autoriza_execucao"]]


def test_ablacao_de_aviso_nao_remove_aviso_da_entrega_ou_altera_autoridade():
    relatorio = coletar(ablacao_avisos=True)
    assert relatorio["fontes_estaveis"]
    assert not relatorio["efeitos_externos_executados"]
    assert len(relatorio["resultados"]) == 24
    for r in relatorio["resultados"]:
        assert len(r["recebidos"]) == len(r["modelos"]) == len(r["textos_publicados"]) == 1
        assert not r["reentrada_porta_operacional"]
        modelo = r["modelos"][0]
        original = modelo["entrada_original"]
        enviado = json.loads(modelo["mensagens"][1]["content"])
        esperado = dict(original)
        if r["caso"]["variante"] == "intervencao":
            esperado.pop("avisos_obrigatorios")
        assert enviado == esperado
        assert enviado["resultados"] == []
        for aviso in original["avisos_obrigatorios"]:
            assert r["textos_publicados"][0].count(aviso) == 1


def test_sonda_recusa_misturar_intervencoes_causais():
    with pytest.raises(ValueError, match="uma intervenção"):
        coletar(ablacao_projecao=True, ablacao_avisos=True)
    with pytest.raises(ValueError, match="não misturar"):
        coletar(ablacao_avisos=True, contraprova_retornar_nao_tratado=True)


def test_composicao_instalada_preserva_ato_anterior_a_condicao_posposta():
    relatorio = coletar(painel_pospostas=True)
    assert relatorio["fontes_estaveis"]
    assert all(relatorio["instalacao"].values())
    assert not relatorio["efeitos_externos_executados"]
    casos = [r for r in relatorio["resultados"] if r["caso"].get("auditar_escopo")]
    assert len(casos) == 4
    for r in casos:
        assert r["turno"]["autoriza_execucao"] is True, r["primeira_fronteira_red"]
        assert [s["autoriza_execucao"] for s in r["turno"]["segmentos"]] == [True, False]
        assert [{k: p[k] for k in ("intent", "params")} for p in r["recebidos"]] == r["caso"]["esperados"]
        assert len(r["modelos"]) == len(r["textos_publicados"]) == 1
        assert r["primeira_fronteira_red"] == ""
        assert not r["reentrada_porta_operacional"]


@pytest.mark.parametrize("opcoes", [
    {"modelo_real": True}, {"ablacao_projecao": True},
    {"contraprova_retornar_nao_tratado": True},
])
def test_painel_posposto_nao_mistura_prova_de_corte_com_outra_intervencao(opcoes):
    with pytest.raises(ValueError, match="painel de segmentação isolado"):
        coletar(painel_pospostas=True, **opcoes)


def test_compromisso_injetado_na_autoria_instalada_nao_chega_a_publicacao():
    relatorio = coletar(contraprova_compromisso=True)
    assert relatorio["fontes_estaveis"]
    assert all(relatorio["instalacao"].values())
    casos = [r for r in relatorio["resultados"] if r["compromisso_injetado"]]
    assert len(casos) == 3
    for r in casos:
        # Prosa livre no canal coberto viola o envelope antes da semântica;
        # não tentar reparar essa prosa como se fosse uma seleção válida.
        assert len(r["recebidos"]) == len(r["textos_publicados"]) == 1
        assert [m["tipo_chamada"] for m in r["modelos"]] == ["autoria_operacional"]
        assert r["compromisso_injetado"] not in r["textos_publicados"][0]
        assert r["plano"]["fase"] == "tratado_prioritario_parcial"
        assert r["primeira_fronteira_red"] == ""
    assert not relatorio["efeitos_externos_executados"]


def test_antiga_injecao_de_reparo_livre_nao_contorna_protocolo_condicional():
    relatorio = coletar(contraprova_reparo=True)
    assert all(relatorio["instalacao"].values()) and relatorio["fontes_estaveis"]
    casos = [r for r in relatorio["resultados"] if r["compromisso_injetado"]]
    assert len(casos) == 3
    for r in casos:
        assert len(r["recebidos"]) == len(r["textos_publicados"]) == 1
        assert [m["tipo_chamada"] for m in r["modelos"]] == ["autoria_operacional"]
        assert json.loads(r["modelos"][0]["mensagens"][1]["content"])["realizacoes_permitidas"]
        assert r["compromisso_injetado"] not in r["textos_publicados"][0]
        assert "Não consegui responder à parte conversacional" in r["textos_publicados"][0]
        assert r["plano"]["fase"] == "tratado_prioritario_parcial"
        assert r["primeira_fronteira_red"] == ""
        assert not r["reentrada_porta_operacional"]
    assert not relatorio["efeitos_externos_executados"]


def test_callbacks_prioritarios_vem_da_composicao_e_fontes_nao_mudaram(prioridade_instalada):
    assert all(prioridade_instalada["instalacao"].values())
    assert prioridade_instalada["fontes_estaveis"]
    assert prioridade_instalada["efeitos_externos_executados"] is False
    assert prioridade_instalada["modelo_real_consultado"] is False


@pytest.mark.parametrize("indice", range(6))
def test_prioridade_de_um_ato_nao_deve_encerrar_o_turno_misto(prioridade_instalada, indice):
    r = prioridade_instalada["resultados"][indice]
    assert r["turno"]["autoriza_execucao"] is True
    assert r["turno"]["texto_conversacional"]
    assert r["recebidos"]  # O RED alcança a fronteira, não é import ausente.
    assert len(r["recebidos"]) == 1
    assert r["recebidos"][0]["intent"] == r["caso"]["esperados"][0]["intent"]
    # Comparação diagnóstica dos campos do painel, não regra de autorização.
    normalizar = lambda p: {k: v.casefold() if isinstance(v, str) else v for k, v in p.items()}
    assert normalizar(r["recebidos"][0]["params"]) == normalizar(r["caso"]["esperados"][0]["params"])
    assert r["recebidos"][0]["texto_porta_executor"] != r["caso"]["texto"]
    assert r["continuacao_alcancada"], (
        "prioridade executou somente o recorte operacional e encerrou antes "
        "da continuação conversacional: " + r["caso"]["id"])
    assert len(r["modelos"]) == 1
    assert r["modelos"][0]["tipo_chamada"] == "autoria_operacional"
    assert len(r["falas_porta_isolada"]) == 1
    assert r["textos_publicados"] == r["falas_porta_isolada"]
    entrada = json.loads(r["modelos"][0]["mensagens"][1]["content"])
    if entrada.get("realizacoes_permitidas"):
        # Comparar a fonte/realização efetivamente adotada, não o antigo
        # marcador artificial de texto livre.
        fala = entrada["realizacoes_permitidas"][0]["opcoes"][0]["fala"]
        assert fala in r["falas_porta_isolada"][0]
    else:
        assert "Continuação conversacional capturada." in r["falas_porta_isolada"][0]
    assert not r["reentrada_porta_operacional"]
    assert r["plano"]["fase"] == "tratado_prioritario_misto"


@pytest.mark.parametrize("indice", [6, 7])
def test_consulta_ou_condicao_isolada_chega_a_conversa_sem_efeito(prioridade_instalada, indice):
    r = prioridade_instalada["resultados"][indice]
    assert not r["recebidos"]
    assert r["modelos"]
    assert r["conclusoes_isoladas"]


def test_falha_da_primeira_etapa_do_conjunto_interrompe_a_cadeia(prioridade_instalada):
    r = prioridade_instalada["resultados"][8]
    assert len(r["recebidos"]) == 1
    assert r["recebidos"][0]["intent"] == "APP_OPEN"
    assert not r["modelos"]
    assert r["falas_porta_isolada"]  # Falha de cadeia comunicada, não silêncio.


@pytest.mark.parametrize("indice", range(9, 15))
def test_ato_operacional_isolado_preserva_atalho_sem_nova_proposta(prioridade_instalada, indice):
    r = prioridade_instalada["resultados"][indice]
    assert len(r["recebidos"]) == 1
    assert r["recebidos"][0]["intent"] == r["caso"]["esperados"][0]["intent"]
    assert not r["modelos"]
    assert not r["continuacao_devida"]
    assert not r["primeira_fronteira_red"]


@pytest.mark.parametrize("indice", range(6))
def test_retornar_false_apos_prioridade_nao_e_solucao_de_cobertura(contraprova_retorno, indice):
    """Falsificação isolada: retomar o pipeline inteiro reenvia a operação.

    Não comprova dois efeitos: as duas portas recusam e não emitem receipt.
    Prova que chegar à LLM sozinho não é um critério suficiente de GREEN.
    """
    r = contraprova_retorno["resultados"][indice]
    assert contraprova_retorno["contraprova_retornar_nao_tratado"] is True
    assert contraprova_retorno["fontes_estaveis"]
    assert contraprova_retorno["efeitos_externos_executados"] is False
    assert r["continuacao_alcancada"]
    assert len(r["recebidos"]) == 2
    assert r["recebidos"][0]["intent"] == r["recebidos"][1]["intent"]
    assert r["recebidos"][0]["params"] == r["recebidos"][1]["params"]
    assert r["reentrada_porta_operacional"]
    assert r["primeira_fronteira_red"] == "continuacao_reentrou_porta_operacional"
