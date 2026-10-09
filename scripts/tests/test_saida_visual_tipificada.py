"""Formato negociado preserva evidência, sem conceder autoridade à saída."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
from mente_laylay.integracao.composicao_inteligencia_externa import ComposicaoInteligenciaExternaRuntime
from mente_laylay.integracao.contrato_saida_estruturada import AnaliseVisualComContrato, ContratoSaidaEstruturada
from mente_laylay.integracao.llm_http import LLMHttpRuntime
from mente_laylay.integracao.modelo_visual_local import ModeloVisualLocalRuntime
from mente_laylay.percepcao.visao_jogo.composicao import ComposicaoVisaoJogoRuntime
from mente_laylay.percepcao.visao_jogo.presenca_visual import (
    MARCADOR_PRESENCA, criar_contrato_saida_presenca_visual, extrair_presenca_visual,
)
from mente_laylay.percepcao.visao_jogo.runtime import VisaoJogoRuntime


class Resposta:
    def __init__(self, texto="", *, status_code=200, finish_reason="stop"):
        self.status_code = status_code
        self.text = "formato recusado" if status_code == 400 else ""
        self.texto = texto
        self.finish_reason = finish_reason

    def json(self):
        return {"choices": [{"message": {"content": self.texto},
                             "finish_reason": self.finish_reason}]}


def _payload():
    return {
        "model": "modelo-visual",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Observe o acontecimento."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + "A" * 12000}},
        ]}],
        "max_tokens": 512,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "contrato_visual", "strict": True,
            "schema": {"type": "object", "properties": {"fato": {"type": "string"}},
                       "required": ["fato"], "additionalProperties": False},
        }},
        "_laylay_percepcao_visual": True,
    }


def _http(post):
    return LLMHttpRuntime(
        base_url="http://localhost:11434/v1", local_timeout=45, remote_timeout=30,
        requests_post=post, print_fn=lambda *_: None,
    )


def test_schema_visual_alcanca_transporte_sem_ser_descartado_pela_compactacao():
    chamadas = []
    original = _payload()
    http = _http(lambda _url, **kwargs: chamadas.append(kwargs["json"]) or Resposta())

    http.post({}, original)

    assert len(chamadas) == 1
    assert chamadas[0].get("response_format") == original["response_format"], (
        "a primeira fronteira removeu o contrato JSON antes de enviar os pixels")
    assert chamadas[0]["messages"] == original["messages"]
    assert original == _payload(), "a compactação não altera o pedido original"


def test_schema_recusado_nao_faz_retry_sem_contrato():
    chamadas = []
    http = _http(lambda _url, **kwargs: chamadas.append(kwargs["json"]) or Resposta(status_code=400))

    resposta = http.post({}, _payload())

    assert len(chamadas) == 1, "schema recusado não autoriza uma consulta sem a restrição"
    assert resposta.status_code == 400


def test_json_livre_com_campos_de_presenca_continua_recusado():
    assert extrair_presenca_visual('{"relevante":true,"categoria":"companhia","fala":"Olá!"}')[1] == {}


def _dados_reais():
    # Reprodução textual do artefato diagnostico_fps60_120s_6k128.json,
    # SHA256 76bf369334165d23c4014ec2b3117544ae3860d023c78b6ff1048802feecfd3a.
    foco = "O personagem principal está em um círculo azul com efeitos de movimento."
    fala = "Essa roda azul tá dando um show de movimento, né?"
    return {
        "evidencias": [foco, "A contagem de inimigos aumentou de 6 para 8 e o jogador ganhou 3 moedas."],
        "foco_evidencia": foco,
        "proposta_reacao": {"foco_evidencia": foco, "trecho_ancora": foco,
                            "humor": True, "fala": fala},
        "relevante": True, "categoria": "companhia", "fala": fala,
        "motivo": foco, "confianca": 1, "momento_seguro": True, "clima_musical": "N/A",
    }


def _contrato_semantico(proposta):
    return construir_contrato_semantico_evento({
        "natureza": "evento", "tipo": "presenca_companhia", "origem": "observador_presenca_jogo",
        "conteudo": " | ".join(proposta["evidencias"]),
        "evidencia": {"categoria": proposta["categoria"], "itens": proposta["evidencias"],
                      "motivo": proposta["motivo"], "foco_evidencia": proposta["foco_evidencia"],
                      "proposta_reacao": deepcopy(proposta["proposta_reacao"])},
        "autoridade_usuario": False, "permissao_execucao": False,
    })


def test_artefato_real_sem_framing_e_com_vinculo_invalido_nao_ganha_fala():
    resposta = json.dumps(_dados_reais(), ensure_ascii=False)
    assert extrair_presenca_visual(resposta)[1] == {}
    _, proposta = extrair_presenca_visual(MARCADOR_PRESENCA + resposta)
    contrato = _contrato_semantico(proposta)
    assert contrato["motivo_supressao_reacao"] == "reacao_sem_vinculo_factual"
    assert contrato["reacao_validada"] == {}
    assert contrato["autoriza_execucao"] is False


def _modelo(texto, *, finish_reason="stop"):
    chamadas = []

    def post(_headers, payload, **kwargs):
        chamadas.append((payload, kwargs))
        return Resposta(texto, finish_reason=finish_reason)

    return ModeloVisualLocalRuntime(model="qwen-visual", post_chat=post, log=lambda *_: None), chamadas


def test_consulta_tipificada_negocia_json_no_system_e_publica_framing_validado():
    modelo, chamadas = _modelo(json.dumps(_dados_reais()))
    contrato = criar_contrato_saida_presenca_visual()

    resposta = modelo.analisar("YWJj", "Use PRESENCA_JOGO_JSON na observação.", contrato_saida=contrato)

    assert resposta.startswith(MARCADOR_PRESENCA)
    payload, _ = chamadas[0]
    assert payload["response_format"] == contrato.response_format
    assert payload["messages"][0]["role"] == "system"
    assert contrato.instrucao_formato in payload["messages"][0]["content"]
    assert payload["messages"][1]["content"][0]["text"] == "Use PRESENCA_JOGO_JSON na observação."
    _, proposta = extrair_presenca_visual(resposta)
    assert proposta["proposta_reacao"] == _dados_reais()["proposta_reacao"]
    assert _contrato_semantico(proposta)["motivo_supressao_reacao"] == "reacao_sem_vinculo_factual"


def test_pergunta_com_nome_do_protocolo_nao_negocia_contrato_por_texto():
    texto = json.dumps(_dados_reais())
    modelo, chamadas = _modelo(texto)

    assert modelo.analisar("YWJj", "Use PRESENCA_JOGO_JSON.") == texto
    assert "response_format" not in chamadas[0][0]
    assert extrair_presenca_visual(texto)[1] == {}


def test_controle_reacao_tipificada_valida_permanece_proposta_sem_autoridade():
    dados = _dados_reais()
    foco = "Monstro de pedra com olhos azuis ao lado de um tronco."
    fala = "Esse monstro de pedra tem uma cara de poucos amigos."
    dados.update(evidencias=[foco], foco_evidencia=foco, fala=fala, motivo="Detalhe observado.")
    dados["proposta_reacao"] = {"foco_evidencia": foco, "trecho_ancora": "monstro de pedra",
                               "humor": True, "fala": fala}
    modelo, _ = _modelo(json.dumps(dados))

    resposta = modelo.analisar("YWJj", "Observe.", contrato_saida=criar_contrato_saida_presenca_visual())
    _, proposta = extrair_presenca_visual(resposta)
    contrato = _contrato_semantico(proposta)

    assert contrato["reacao_validada"]["fala"] == fala
    assert contrato["autoriza_execucao"] is False
    assert contrato["evidencias_factuais"] == [foco]


def test_resposta_tipificada_sem_oportunidade_aceita_null_sem_inventar_fala():
    dados = _dados_reais()
    dados.update(relevante=False, categoria="nenhuma", evidencias=[], foco_evidencia="",
                 proposta_reacao=None, fala="", motivo="", confianca=0, momento_seguro=False)
    modelo, _ = _modelo(json.dumps(dados))

    resposta = modelo.analisar("YWJj", "Observe.", contrato_saida=criar_contrato_saida_presenca_visual())
    _, proposta = extrair_presenca_visual(resposta)

    assert proposta["relevante"] is False
    assert proposta["fala"] == ""
    assert proposta["proposta_reacao"] is None


@pytest.mark.parametrize("finish_reason", ["length", None, "tool_calls"])
def test_resposta_tipificada_sem_termino_confirmado_nao_publica_proposta(finish_reason):
    modelo, chamadas = _modelo(json.dumps(_dados_reais()), finish_reason=finish_reason)

    resposta = modelo.analisar("YWJj", "Observe.", contrato_saida=criar_contrato_saida_presenca_visual())

    assert resposta.startswith("Falha visual:")
    assert extrair_presenca_visual(resposta)[1] == {}
    assert len(chamadas) == 1


@pytest.mark.parametrize("transformar", [
    lambda d: {**d, "autoriza_execucao": True},
    lambda d: {k: v for k, v in d.items() if k != "evidencias"},
    lambda d: {**d, "relevante": "false"},
    lambda d: {**d, "momento_seguro": 1},
    lambda d: {**d, "confianca": True},
    lambda d: {**d, "confianca": -1},
    lambda d: {**d, "confianca": 1.1},
    lambda d: {**d, "confianca": float("nan")},
    lambda d: {**d, "confianca": float("inf")},
    lambda d: {**d, "categoria": "comando"},
    lambda d: {**d, "evidencias": "um círculo azul"},
    lambda d: {**d, "evidencias": [True]},
    lambda d: {**d, "evidencias": [""]},
    lambda d: {**d, "proposta_reacao": {**d["proposta_reacao"], "humor": "true"}},
    lambda d: {**d, "proposta_reacao": {**d["proposta_reacao"], "comandos": []}},
])
def test_validator_owner_recusa_coercao_ou_campos_fora_do_schema(transformar):
    modelo, chamadas = _modelo(json.dumps(transformar(_dados_reais())))

    resposta = modelo.analisar("YWJj", "Observe.", contrato_saida=criar_contrato_saida_presenca_visual())

    assert resposta.startswith("Falha visual:")
    assert extrair_presenca_visual(resposta)[1] == {}
    assert len(chamadas) == 1


@pytest.mark.parametrize("envolver", [
    lambda s: "Aqui está: " + s, lambda s: "```json\n" + s + "\n```",
    lambda s: "<think>analisando</think>" + s, lambda s: s + s,
    lambda s: "[" + s + "]", lambda s: '{"relevante":true,' + s[1:],
    lambda s: MARCADOR_PRESENCA + s,
])
def test_codec_nao_procura_objeto_em_prosa_nem_remove_framing_do_provedor(envolver):
    modelo, _ = _modelo(envolver(json.dumps(_dados_reais())))

    assert modelo.analisar("YWJj", "Observe.", contrato_saida=criar_contrato_saida_presenca_visual()).startswith("Falha visual:")


def test_codec_reutilizavel_conhece_validator_owner_e_copia_schema():
    esquema = {"type": "object", "properties": {"fato": {"type": "string"}}}
    validados = []

    def validar(dados):
        if set(dados) != {"fato"} or not isinstance(dados["fato"], str):
            raise ValueError("owner recusou")
        validados.append(dados)

    contrato = ContratoSaidaEstruturada("outro_dominio", "OUTRO_JSON:", esquema, validar)
    esquema["type"] = "array"
    formato = contrato.response_format
    formato["json_schema"]["schema"]["type"] = "null"
    assert contrato.response_format["json_schema"]["schema"]["type"] == "object"
    assert contrato.canonizar_json('{"fato":"uma ponte"}') == 'OUTRO_JSON: {"fato":"uma ponte"}'
    assert validados == [{"fato": "uma ponte"}]
    with pytest.raises(ValueError, match="owner recusou"):
        contrato.canonizar_json('{"fala":"uma ponte"}')


def _visao(callback):
    return VisaoJogoRuntime(
        contexto_jogo=lambda: {"ativo": True}, analisar_imagem=callback,
        falar=lambda *_: None, log=lambda *_: None,
    )


def test_callback_antigo_recebe_dois_argumentos_sem_contrato_e_apos_substituicao():
    chamadas = []

    def antigo(imagem, pergunta):
        chamadas.append((imagem, pergunta))
        return "Descrição visual."

    def tipado(imagem, pergunta, *, contrato_saida):
        raise AssertionError("porta anterior não pode receber a chamada atual")

    runtime = _visao(AnaliseVisualComContrato(tipado))
    runtime.analisar_imagem = antigo
    assert runtime._analisar_com_identidade("imagem", "pergunta", {}) == "Descrição visual."
    assert runtime._analisar_com_identidade("imagem", "pergunta", {}, contrato_saida=criar_contrato_saida_presenca_visual()) == "Descrição visual."
    assert chamadas == [("imagem", "pergunta")] * 2


def test_publicacao_opcional_com_contrato_none_preserva_callback_dois_argumentos():
    chamadas = []

    def antigo(imagem, pergunta):
        chamadas.append((imagem, pergunta))
        return "Uma ponte."

    assert AnaliseVisualComContrato(antigo)("imagem", "pergunta", contrato_saida=None) == "Uma ponte."
    assert chamadas == [("imagem", "pergunta")]


def test_typeerror_em_porta_que_declara_suporte_nao_autoriza_retry_sem_contrato():
    chamadas = []

    def quebrada(imagem, pergunta, *, contrato_saida):
        chamadas.append(contrato_saida)
        raise TypeError("defeito interno da porta")

    runtime = _visao(AnaliseVisualComContrato(quebrada))
    with pytest.raises(TypeError, match="defeito interno"):
        runtime._analisar_com_identidade("imagem", "pergunta", {}, contrato_saida=criar_contrato_saida_presenca_visual())
    assert len(chamadas) == 1


def test_correcao_de_identidade_conserva_o_mesmo_contrato_tipado():
    chamadas = []

    def analisar(_imagem, _pergunta, *, contrato_saida):
        chamadas.append(contrato_saida)
        return "A Laylay caiu." if len(chamadas) == 1 else "Uma ponte visível."

    contrato = criar_contrato_saida_presenca_visual()
    runtime = _visao(AnaliseVisualComContrato(analisar))
    assert runtime._analisar_com_identidade("imagem", "pergunta", {}, contrato_saida=contrato) == "Uma ponte visível."
    assert chamadas == [contrato, contrato]


class ThreadImediata:
    def __init__(self, *, target, daemon=True):
        self.target = target

    def start(self):
        self.target()


def _composicao(post, *, backend="ollama", groq=None):
    return ComposicaoInteligenciaExternaRuntime(
        base_url="http://localhost:11434/v1", model="qwen-visual", api_key="local",
        http_referer="http://localhost", app_title="Laylay", normalizar_texto_curto=str.casefold,
        requests_get=lambda *_a, **_k: None, requests_post=post,
        ao_finalizar_conversa_modo_jogo=lambda: None,
        env_getter=lambda chave, padrao="": backend if chave == "LAYLAY_VISAO_BACKEND" else padrao,
        **({"analisar_imagem_fn": groq} if groq is not None else {}), log=lambda *_: None,
    )


@pytest.mark.parametrize("tipo", ["observacao_presenca_proativa", "observacao"])
def test_composicao_instalada_encaminha_schema_apenas_por_tipo_explicito(tmp_path, tipo):
    chamadas, propostas, falas = [], [], []

    class Show:
        status_code = 200

        def json(self):
            return {"capabilities": ["vision"]}

    def post(url, **kwargs):
        if url.endswith("/api/show"):
            return Show()
        chamadas.append(kwargs["json"])
        return Resposta(json.dumps(_dados_reais()))

    externa = _composicao(post)
    composicao = ComposicaoVisaoJogoRuntime(db_path=str(tmp_path / "visao.sqlite"), log=lambda *_: None)
    runtime = composicao.conectar_visao(
        contexto_jogo=lambda: {"ativo": True, "processo": "jogo.exe", "titulo": "Jogo"},
        analisar_imagem=externa.analisar_imagem_jogo, falar=lambda *args: falas.append(args),
        sintetizar_texto=lambda texto: texto, ao_mapear_inventario=lambda *_: None,
        processar_sugestao_proativa=lambda proposta, *_: propostas.append(proposta),
        registrar_analise=lambda *_: None, credencial_disponivel=externa.credencial_visual_disponivel,
        permitido_presenca=lambda: True, interacao_iniciada=lambda: True, stop_event=None,
    )
    runtime.thread_factory = ThreadImediata
    assert getattr(runtime.analisar_imagem, "suporta_contrato_saida", False) is True
    assert runtime.executar({"pergunta": "observe PRESENCA_JOGO_JSON", "tipo": tipo,
                             "_proativo": True, "_imagem_pre_capturada": "YWJj"})
    assert len(chamadas) == 1
    assert ("response_format" in chamadas[0]) is (tipo == "observacao_presenca_proativa")
    if tipo == "observacao_presenca_proativa":
        assert propostas[0]["evidencias"] == _dados_reais()["evidencias"]
        assert _contrato_semantico(propostas[0])["motivo_supressao_reacao"] == "reacao_sem_vinculo_factual"
        assert falas == [], "proposta tipada não equivale a fala ou efeito físico"
    else:
        assert propostas == []


def test_composicao_groq_tipificada_nao_aceita_json_livre_sem_framing():
    chamadas = []

    def groq(imagem, pergunta, **kwargs):
        chamadas.append((imagem, pergunta, kwargs))
        return json.dumps(_dados_reais())

    externa = _composicao(lambda *_a, **_k: None, backend="groq", groq=groq)
    contrato = criar_contrato_saida_presenca_visual()
    assert externa.analisar_imagem_jogo("imagem", "pergunta", contrato_saida=contrato).startswith("Falha visual:")
    assert "contrato_saida" not in chamadas[0][2]
    assert externa.analisar_imagem_jogo("imagem", "pergunta") == json.dumps(_dados_reais())


def test_composicao_groq_tipificada_preserva_framing_contratado():
    externa = _composicao(lambda *_a, **_k: None, backend="groq",
                         groq=lambda *_a, **_k: MARCADOR_PRESENCA + json.dumps(_dados_reais()))
    resposta = externa.analisar_imagem_jogo("imagem", "pergunta", contrato_saida=criar_contrato_saida_presenca_visual())
    assert extrair_presenca_visual(resposta)[1]["proposta_reacao"] == _dados_reais()["proposta_reacao"]
