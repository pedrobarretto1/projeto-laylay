"""Composição instalada com efeitos/modelo/voz isolados, não sessão main."""
import pytest

from scripts.analises.sonda_escopo_propostas_mistas import coletar


@pytest.fixture(scope="module")
def escopo_instalado():
    return coletar()


def test_composicao_instala_validador_e_dispatcher_com_a_mesma_mente(escopo_instalado):
    assert all(escopo_instalado["instalacao"].values())
    assert escopo_instalado["fontes_estaveis"]
    assert escopo_instalado["efeitos_externos_executados"] is False


@pytest.mark.parametrize("indice", range(10))
def test_admissao_e_porta_executor_conservam_escopo_exato(escopo_instalado, indice):
    resultado = escopo_instalado["resultados"][indice]
    assert resultado["falhas"] == []
    assert resultado["proposta_vinculada"] is True
    assert resultado["ocorrencia_vinculada"] is True
    assert resultado["recebidos_porta_executor"] == resultado["caso"]["esperados"]
    if indice < 6:
        assert resultado["validacao"]["atos_autorizados_vinculados"] == [0]
        assert len(resultado["validacao"]["rejeitados"]) == 1


@pytest.mark.parametrize("indice", range(3))
def test_pipeline_instalado_publica_so_pedido_valido_e_chega_a_conclusao(escopo_instalado, indice):
    resultado = escopo_instalado["pipelines_instalados"][indice]
    assert resultado["falhas"] == []
    # A API externa processar() retorna None por contrato. Conclusão se prova
    # pela publicação/porta de fala, não por um bool artificial no harness.
    assert resultado["plano"]["fase"] == "falha_execucao"
    assert len(resultado["recebidos"]) == 1
    assert len(resultado["plano"]["comandos"]) == 1
    assert resultado["falas_porta_isolada"]
    assert all(c["confirmado"] is not True for c in resultado["plano"]["comandos"])


@pytest.mark.parametrize("ident", ["conector_app_midia", "conector_volume_app", "conector_pedido_negado", "conector_pergunta"])
def test_conector_inicial_no_caminho_instalado_de_atos_e_dispatcher(escopo_instalado, ident):
    r = escopo_instalado
    caso = next(c for c in r["resultados"] if c["caso"]["id"] == ident)
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    assert caso["falhas"] == []
    assert caso["validacao"]["comandos"] == caso["caso"]["esperados"]
    assert caso["recebidos_porta_executor"] == caso["caso"]["esperados"]
    assert not r["efeitos_externos_executados"]


@pytest.mark.parametrize("ident", ["revisao_ambigua_observada", "cancelamento_observado", "schema_bloqueado_instalado"])
def test_pipeline_bloqueado_registra_compreensao_sem_executar_proposta(escopo_instalado, ident):
    resultado = next(r for r in escopo_instalado["pipelines_instalados"] if r["id"] == ident)
    assert resultado["turno"]["leitura_semantica_principal"]["valida"] is True
    assert resultado["turno"]["autoriza_execucao"] is False
    assert resultado["turno"]["veto_execucao_operacional"] is True
    assert resultado["plano"]["requer_execucao"] is False
    assert resultado["plano"]["decisao_turno"]["permite_acao"] is False
    assert resultado["recebidos"] == resultado["plano"]["comandos"] == []
    assert resultado["falas_porta_isolada"]
    assert resultado["falhas"] == []


def test_pipeline_com_fontes_vinculadas_nao_empresta_autoridade_ao_ato_negado(escopo_instalado):
    resultado = next(r for r in escopo_instalado["pipelines_instalados"] if r["id"] == "schema_fontes_mistas_instalado")
    assert resultado["pedidos_http"] == [{"formato": "json_schema", "max_tokens": 1024}]
    assert len(resultado["turno"]["leitura_semantica_principal"]["atos"]) == 2
    assert [c["intent"] for c in resultado["recebidos"]] == ["APP_OPEN"]
    assert resultado["falhas"] == [] and resultado["falas_porta_isolada"]
    assert all(c["confirmado"] is not True for c in resultado["plano"]["comandos"])


def test_metadata_conversa_conserva_restricao_existente_sem_apagar_leitura_por_ato(escopo_instalado):
    resultado = next(r for r in escopo_instalado["pipelines_instalados"] if r["id"] == "schema_fontes_conversa_instalado")
    assert resultado["recebidos"] == [] and resultado["falhas"] == []
    assert len(resultado["turno"]["leitura_semantica_principal"]["atos"]) == 2
    assert resultado["falas_porta_isolada"]


@pytest.mark.parametrize("ident", [
    "vocabulario_volume_app", "vocabulario_app_volume",
    "vocabulario_ajuste_iot_app",
    "vocabulario_negacao_volume", "vocabulario_capacidade_volume", "vocabulario_condicao_iot",
])
def test_vocabulario_compartilhado_chega_ao_validador_instalado_sem_emprestar_permissao(escopo_instalado, ident):
    resultado = next(r for r in escopo_instalado["resultados"] if r["caso"]["id"] == ident)
    assert resultado["falhas"] == []
    assert resultado["proposta_vinculada"] and resultado["ocorrencia_vinculada"]
    assert resultado["recebidos_porta_executor"] == resultado["caso"]["esperados"]


@pytest.mark.parametrize("ident", [
    "vocabulario_volume_app", "vocabulario_app_volume", "vocabulario_ajuste_iot_app",
])
def test_classificacao_instalada_e_resolucao_por_ato_preservam_os_dois_pedidos(escopo_instalado, ident):
    resultado = next(r for r in escopo_instalado["resultados"] if r["caso"]["id"] == ident)
    assert resultado["turno"]["autoriza_execucao"] is True
    assert len(resultado["turno"]["segmentos"]) == 2
    assert all(s["autoriza_execucao"] is True for s in resultado["turno"]["segmentos"])
    assert len(resultado["resolucoes_canonicas_autorizadas"]) == 2


def test_pipeline_volume_app_sem_prototipo_conclui_sem_anunciar_efeitos_falsos(escopo_instalado):
    resultado = next(r for r in escopo_instalado["pipelines_instalados"] if r["id"] == "vocabulario_volume_app")
    assert len(resultado["turno"]["segmentos"]) == 2
    assert [c["intent"] for c in resultado["recebidos"]] == ["VOLUME", "APP_OPEN"]
    assert len(resultado["plano"]["comandos"]) == 2
    assert all(c["confirmado"] is not True for c in resultado["plano"]["comandos"])
    assert resultado["plano"]["fase"] == "falha_execucao"
    assert resultado["pedidos_http"] == []
    assert resultado["falhas"] == []
    assert len(resultado["falas_porta_isolada"]) == 1


@pytest.mark.parametrize("ident", [
    "conjunto_iot_app_invertido", "conjunto_parametro_inventado", "conjunto_alvo_inventado",
    "conjunto_proposta_duplicada", "conjunto_ordem_repetida",
])
def test_admissao_instalada_do_conjunto_exige_ato_exato_e_nao_so_intent_permitido(escopo_instalado, ident):
    resultado = next(r for r in escopo_instalado["resultados"] if r["caso"]["id"] == ident)
    assert resultado["falhas"] == []
    assert resultado["validacao"]["comandos"] == resultado["caso"]["esperados"]
    assert resultado["recebidos_porta_executor"] == resultado["caso"]["esperados"]
    assert resultado["validacao"]["atos_autorizados_vinculados"] == [0, 1]


def test_pipeline_brilho_app_conserva_duas_operacoes_e_uma_conclusao_sem_confirmacao_falsa(escopo_instalado):
    resultado = next(r for r in escopo_instalado["pipelines_instalados"] if r["id"] == "vocabulario_ajuste_iot_app")
    assert len(resultado["turno"]["segmentos"]) == 2
    assert [c["intent"] for c in resultado["recebidos"]] == ["IOT_CONTROL", "APP_OPEN"]
    assert len(resultado["plano"]["comandos"]) == 2
    assert all(c["confirmado"] is not True for c in resultado["plano"]["comandos"])
    assert resultado["plano"]["fase"] == "falha_execucao"
    assert resultado["pedidos_http"] == []
    assert resultado["falhas"] == [] and len(resultado["falas_porta_isolada"]) == 1


@pytest.mark.parametrize("ident", [
    "janela_posicao", "janela_foco", "iot_cor", "controle_deixa", "controle_literal",
])
def test_composicao_conserva_dependencia_do_operando_sem_tratar_pronome_como_nome(escopo_instalado, ident):
    resultado = next(r for r in escopo_instalado["referencias_operando_instaladas"] if r["id"] == ident)
    assert resultado["falhas"] == []
    assert resultado["segmentos"][1]["depende_contexto"] is resultado["dependencia_esperada"]
    if resultado["dependencia_esperada"]:
        assert resultado["validacao"]["comandos"] == []
        assert all(a["indice"] != 1 for a in resultado["validacao"]["escopo_operacional_por_ato"])
    else:
        assert resultado["validacao"]["comandos"] == [resultado["candidato_segundo_sem_receipt"]]


def test_controle_literal_instalado_compara_mesma_fonte_original_nas_duas_portas(escopo_instalado):
    caso = next(r for r in escopo_instalado["referencias_operando_instaladas"] if r["id"] == "controle_literal")
    fonte = caso["fonte_segundo"]
    assert caso["texto"][slice(*fonte["intervalo"])] == fonte["texto_original"]
    assert fonte["texto_original"] == 'toca a música "Ela à Esquerda"'
    assert caso["candidato_segundo_sem_receipt"]["params"]["query"] == "Ela à Esquerda"
    assert caso["validacao"]["comandos"] == [caso["candidato_segundo_sem_receipt"]]


@pytest.mark.parametrize("ident", ["abertura_confirmada", "abertura_falhou", "abertura_incerta"])
def test_cadeia_instalada_so_resolve_dependencia_depois_do_receipt_e_nao_de_app_antigo(escopo_instalado, ident):
    resultado = next(r for r in escopo_instalado["cadeias_referenciais_instaladas"] if r["id"] == ident)
    assert resultado["falhas"] == [] and resultado["tratado"] is True
    assert resultado["efeitos_fisicos_executados"] is False
    assert resultado["chamadas_porta"][0]["intent"] == "APP_OPEN"
    if ident == "abertura_confirmada":
        assert resultado["receipts_sinteticos"][0]["confirmado"] is True
        assert len(resultado["chamadas_porta"]) == 2
        segundo = resultado["chamadas_porta"][1]
        assert segundo["intent"] == "ORGANIZAR_DESKTOP"
        assert segundo["params"]["left"].casefold() == "calculadora"
    else:
        assert resultado["receipts_sinteticos"][0]["confirmado"] is not True
        assert len(resultado["chamadas_porta"]) == 1
        assert resultado["falas_porta_isolada"]


def test_pipeline_principal_nao_omite_ato_contextual_que_nao_materializou(escopo_instalado):
    resultado = next(r for r in escopo_instalado["pipelines_instalados"] if r["id"] == "dependencia_principal_nao_materializada")
    assert len(resultado["turno"]["segmentos"]) == 2
    assert [c["intent"] for c in resultado["recebidos"]] == ["APP_OPEN"]
    assert any("etapa contextual não materializada" in erro and "coloca ela à esquerda" in erro
               for erro in resultado["plano"]["erros"])
    assert resultado["plano"]["fase"] == "falha_execucao"
    assert resultado["falhas"] == [] and len(resultado["falas_porta_isolada"]) == 1
