"""Schema negociado atravessa a porta existente; formato não prova efeito."""
import inspect
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
from mente_laylay.integracao.registro_conversa_llm import PedidoModelo, ResultadoModelo
from mente_laylay.integracao.preparador_requisicao_llm import PreparadorRequisicaoLLMRuntime
from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
from mente_laylay.integracao.llm_http import compactar_payload_llm_local


def contrato():
    def validar(dados):
        if set(dados) != {"leitura_turno"} or type(dados["leitura_turno"]) is not list:
            raise ValueError("formato do owner recusado")
    return ContratoSaidaEstruturada("teste_principal", "[TESTE]", {
        "type": "object", "properties": {"leitura_turno": {"type": "array", "items": {"type": "string"}}},
        "required": ["leitura_turno"], "additionalProperties": False}, validar)


def preparador():
    return PreparadorRequisicaoLLMRuntime(model="qwen3:4b-instruct", endpoint_local_getter=lambda: True,
        resumo_do_dia_getter=lambda: "", data_atual_getter=lambda: "", normalizar_texto=lambda t: t,
        mapear_pastas=lambda *_: {}, contexto_logs_getter=lambda: [],
        contexto_navegador_relevante=lambda *_: False, contexto_sistema_getter=lambda: {},
        obter_contexto_paginas=lambda: {}, resumo_mente_integrada=lambda *_: "", log=lambda *_: None)


def pedido_tipado():
    assert "contrato_saida" in inspect.signature(PedidoModelo).parameters, "primeira fronteira: pedido perde negociação de formato"
    return PedidoModelo.criar([{"role": "user", "content": "abre Calculadora"}],
        contrato_saida=contrato(), reserva_saida_tokens=1024, max_tokens=1024, contexto_fechado=True)


def test_schema_e_reserva_negociados_chegam_ao_payload_e_sobrevivem_compactacao():
    pedido = pedido_tipado()
    payload = preparador().preparar(pedido).payload
    assert payload["response_format"] == pedido.contrato_saida.response_format
    assert payload["max_tokens"] == 1024
    compacto = compactar_payload_llm_local(payload)
    assert compacto["response_format"] == payload["response_format"]
    assert compacto["max_tokens"] == 1024


@pytest.mark.parametrize("bruto", ['{"leitura_turno":[]}', '{ "leitura_turno" : ["pedido_acao"] }'])
def test_owner_valida_documento_sem_publicar_marcador_no_envelope_principal(bruto):
    runtime = ServicoModeloLLMRuntime(preparador=preparador(),
        cliente=SimpleNamespace(executar=lambda _: ResultadoModelo(bruto, True)))
    resultado = runtime.executar(pedido_tipado())
    assert resultado.sucesso is True
    assert json.loads(resultado.texto) == json.loads(bruto)
    assert "[TESTE]" not in resultado.texto


@pytest.mark.parametrize("bruto", [
    'prefixo {"leitura_turno":[]}', '{"leitura_turno":[],"leitura_turno":[]}',
    '{"leitura_turno":false}', '{"leitura_turno":[],"confirmado":true}',
    '{"leitura_turno":[NaN]}', '{"leitura_turno":[',
])
def test_resposta_que_ignora_schema_nao_chega_ao_decoder_como_sucesso(bruto):
    runtime = ServicoModeloLLMRuntime(preparador=preparador(),
        cliente=SimpleNamespace(executar=lambda _: ResultadoModelo(bruto, True)))
    resultado = runtime.executar(pedido_tipado())
    assert resultado.sucesso is False
    assert resultado.texto == ""
    assert resultado.rota == "contrato_saida_invalido"


def test_falha_de_transporte_nao_entrega_payload_ao_decoder_negociado():
    runtime = ServicoModeloLLMRuntime(preparador=preparador(), cliente=SimpleNamespace(
        executar=lambda _: ResultadoModelo('{"leitura_turno":["pedido_acao"]}', False, rota="falha_transporte")))
    resultado = runtime.executar(pedido_tipado())
    assert resultado.sucesso is False
    assert resultado.texto == ""
    assert resultado.rota == "falha_transporte"


def test_pedido_ordinario_preserva_teto_existente_e_nao_adquire_schema():
    pedido = PedidoModelo.criar([{"role": "user", "content": "oi"}], max_tokens=1024)
    payload = preparador().preparar(pedido).payload
    assert payload["max_tokens"] == 640
    assert payload.get("response_format", {}).get("type") != "json_schema"


def envelope():
    from scripts.tests.test_interpretacao_operacional_por_ato import proposta_ato
    texto = "abre o aplicativo Calculadora"
    ato = proposta_ato(texto, texto)
    ato["interpretacao"].pop("intervalo")
    return texto, {"fala": "Vou verificar o pedido.", "emocao": "calma", "nivel_emocao": 1,
        "tipo_interacao": "conversa", "leitura_turno": [ato], "comandos": [], "aprendizados": [],
        "leitura_emocional": {"estado_usuario": "nenhum", "intensidade": 0, "causa_expressa": "",
            "trecho_evidencia": "", "natureza_evidencia": "inferencia", "hipotetica": False,
            "alvo": "estado_geral", "confianca": 0.0}}


def test_envelope_tipado_preserva_conversa_e_leitura_sem_conceder_efeito():
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_da_ia
    texto, dados = envelope()
    # Fixture usada com destino vazio, não com target artificial de execução.
    dados["leitura_turno"][0]["interpretacao"]["destino"] = ""
    antes = deepcopy(dados)
    owner = criar_contrato_saida_interpretacao_principal(texto)
    assert owner.decodificar_json(json.dumps(dados)) == dados == antes
    leitura = extrair_leitura_semantica_da_ia(json.dumps(dados), texto)
    proposta = leitura["atos"][0]["interpretacao"]
    assert proposta["autoriza_execucao"] is proposta["comprova_efeito"] is False
    assert proposta["estado"] == "proposta_nao_validada_semanticamente"


@pytest.mark.parametrize("caminho,valor", [
    (("confirmado",), True), (("nivel_emocao",), True), (("aprendizados",), False),
    (("leitura_emocional", "confianca"), True), (("leitura_emocional", "hipotetica"), "false"),
    (("leitura_turno",), ["pedido_acao"]),
    (("leitura_turno", 0, "interpretacao", "texto_original"), "abre o aplicativo Opera"),
    (("leitura_turno", 0, "interpretacao", "autoriza_execucao"), True),
    (("leitura_turno", 0, "interpretacao", "dependencias"), [0]),
    (("leitura_turno", 0, "interpretacao", "parametros"), []),
    (("comandos",), [{"tipo": "pedido_acao", "interpretacao": {}}]),
    (("comandos",), [{"intent": "APP_OPEN", "params": {}, "confirmado": True}]),
])
def test_owner_recusa_coercao_fonte_falsa_e_campos_de_autoridade(caminho, valor):
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    texto, dados = envelope()
    destino = dados
    for chave in caminho[:-1]:
        destino = destino[chave]
    destino[caminho[-1]] = valor
    with pytest.raises(ValueError):
        criar_contrato_saida_interpretacao_principal(texto).decodificar_json(json.dumps(dados))


@pytest.mark.parametrize("tipo", [PedidoModelo])
@pytest.mark.parametrize("falso", [True, {}, "json_schema"])
def test_negociacao_de_saida_nao_vem_de_metadados_da_fala(tipo, falso):
    with pytest.raises(TypeError, match="codec do host"):
        tipo.criar([], contrato_saida=falso)


@pytest.mark.parametrize("texto", [
    "abre o aplicativo Calculadora e pausa a música",
    "Abre o site Example.test/A e desliga o ventilador",
    "Abre\t o aplicativo\nCalculadora e pausa a música",
    'abre o arquivo "A e B.txt" e pausa a música',
])
def test_segmentacao_canonica_publica_fontes_literais_sem_criar_autoridade(texto):
    import mente_laylay.cognicao.modalidade_turno as modulo
    publicar = getattr(modulo, "fontes_textuais_dos_segmentos", None)
    assert callable(publicar), "primeira fronteira: segmentos canônicos não oferecem vínculo literal ao produtor"
    turno = modulo.classificar_modalidade_turno(texto)
    antes = deepcopy(turno)
    fontes = publicar(texto, turno["segmentos"])
    assert len(fontes) == 2
    for fonte in fontes:
        dados = fonte.como_dict()
        assert texto[slice(*dados["intervalo"])] == dados["texto_original"]
        assert dados["autoriza_execucao"] is False and dados["comprova_efeito"] is False
    assert turno == antes


def test_schema_vincula_fontes_do_host_e_recusa_ato_fundido_sem_enfraquecer_semantica():
    import mente_laylay.cognicao.modalidade_turno as modulo
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    assert "fontes" in inspect.signature(criar_contrato_saida_interpretacao_principal).parameters, "primeira fronteira: schema só limita formato, perde fontes canônicas"
    texto = "abre o aplicativo Calculadora e pausa a música"
    turno = modulo.classificar_modalidade_turno(texto)
    fontes = modulo.fontes_textuais_dos_segmentos(texto, turno["segmentos"])
    owner = criar_contrato_saida_interpretacao_principal(texto, fontes=fontes)
    _, dados = envelope()
    ato = dados["leitura_turno"][0]
    ato["conteudo"] = ato["interpretacao"]["texto_original"] = texto
    with pytest.raises(ValueError):
        owner.decodificar_json(json.dumps(dados))
    schema = owner.response_format["json_schema"]["schema"]["properties"]["leitura_turno"]
    assert schema["minItems"] == schema["maxItems"] == 2
    assert [r["properties"]["conteudo"]["const"] for r in schema["items"]["anyOf"]] == [f.como_dict()["texto_original"] for f in fontes]


@pytest.mark.parametrize("texto", [
    "abre o aplicativo Calculadora e pausa a música",
    "pausa a música; pausa a música",
])
def test_fontes_ordenadas_preservam_operacoes_independentes_e_repeticoes(texto):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_da_ia
    fontes = fontes_textuais_dos_segmentos(texto, classificar_modalidade_turno(texto)["segmentos"])
    assert len(fontes) == 2
    _, dados = envelope()
    dados["leitura_turno"] = []
    from scripts.tests.test_interpretacao_operacional_por_ato import proposta_ato
    for fonte in fontes:
        campos = fonte.como_dict()
        ato = proposta_ato(texto, campos["texto_original"])
        ato["interpretacao"]["intervalo"] = campos["intervalo"]
        dados["leitura_turno"].append(ato)
    owner = criar_contrato_saida_interpretacao_principal(texto, fontes=fontes)
    assert owner.decodificar_json(json.dumps(dados)) == dados
    leitura = extrair_leitura_semantica_da_ia(json.dumps(dados), texto)
    assert len(leitura["atos"]) == 2 and not leitura["problemas_interpretacao"]
    invertidos = deepcopy(dados)
    invertidos["leitura_turno"].reverse()
    with pytest.raises(ValueError):
        owner.decodificar_json(json.dumps(invertidos))
    schema = owner.response_format["json_schema"]["schema"]["properties"]["leitura_turno"]
    for ramo in schema["items"]["anyOf"]:
        # Const de fonte não vaza para strings semanticamente livres.
        assert "const" not in ramo["properties"]["interpretacao"]["properties"]["operacao"]


@pytest.mark.parametrize("segmentos", [[], [{"texto": "abre o Opera"}], [{"texto": "x" * 300}], [None]])
def test_fontes_ausentes_corrigidas_ou_truncadas_nao_recebem_vinculo_falso(segmentos):
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    assert fontes_textuais_dos_segmentos("abre o aplicativo Calculadora", segmentos) == ()


def test_retrato_colapsado_por_veto_nao_e_transformado_em_decomposicao_completa():
    from scripts.tests.test_coerencia_revisao_bloqueada import frame_bloqueado
    from scripts.tests.test_interpretacao_operacional_por_ato import _prompt_para_turno
    texto = "abre o aplicativo Calculadora; deixa ela à esquerda; não liga a luz"
    runtime, estado = _prompt_para_turno(texto)
    estado["turno_atual"] = frame_bloqueado(texto)["turno_atual"]
    antes = deepcopy(estado)
    pacote = runtime.preparar_envio_modelo([{"role": "user", "content": texto}],
        turno_id=estado["turno_atual"]["id"])
    leitura = pacote.contrato_saida.response_format["json_schema"]["schema"]["properties"]["leitura_turno"]
    assert leitura["minItems"] == 1 and "anyOf" not in leitura["items"]
    assert estado == antes and estado["turno_atual"]["autoriza_execucao"] is False
