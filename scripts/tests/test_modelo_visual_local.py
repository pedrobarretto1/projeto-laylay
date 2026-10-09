from __future__ import annotations

import pytest

from mente_laylay.cognicao.memoria_visual import executar_captura_tela
from mente_laylay.integracao.llm_http import RespostaLLMFallback
from mente_laylay.integracao.modelo_visual_local import ModeloVisualLocalRuntime
from mente_laylay.percepcao.imagens_multimodais import empacotar_imagens


class _Resposta:
    def __init__(self, texto="Vejo um botão azul.", *, status_code=200, dados=None):
        self.status_code = status_code
        self._dados = dados if dados is not None else {
            "choices": [{"message": {"content": texto}}],
        }

    def json(self):
        return self._dados


def _criar(resposta=None, *, model="qwen3-vl:4b"):
    chamadas, logs, falhas = [], [], []

    def post(headers, data, **kwargs):
        chamadas.append((headers, data, kwargs))
        if isinstance(resposta, Exception):
            raise resposta
        return resposta if resposta is not None else _Resposta()

    runtime = ModeloVisualLocalRuntime(
        model=model,
        post_chat=post,
        timeout_s=47,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=logs.append,
    )
    return runtime, chamadas, logs, falhas


def test_visao_local_preserva_todos_os_recortes_rotulados_no_transporte_compartilhado():
    runtime, chamadas, _, _ = _criar()
    pacote = empacotar_imagens([
        {"label": "Contexto", "mime": "image/jpeg", "data": "quadro", "width": 800, "height": 450},
        {"label": "Tooltip", "mime": "image/png", "data": "tooltip", "width": 600, "height": 300},
        {"label": "Detalhe nativo", "mime": "image/png", "data": "detalhe", "width": 300, "height": 150},
    ])

    assert runtime.analisar(pacote, "O que aparece aqui?") == "Vejo um botão azul."

    assert len(chamadas) == 1
    headers, payload, opcoes = chamadas[0]
    assert headers == {"Content-Type": "application/json"}
    assert payload["model"] == "qwen3-vl:4b"
    assert payload["max_tokens"] == 512
    assert payload["reasoning_effort"] == "none"
    assert payload["_laylay_percepcao_visual"] is True
    assert payload["_laylay_prioridade_interativa"] is False
    assert payload["_laylay_conversa_modo_jogo"] is True
    assert opcoes == {"timeout": 47.0}
    partes = payload["messages"][-1]["content"]
    assert partes[0] == {"type": "text", "text": "O que aparece aqui?"}
    imagens = [parte["image_url"]["url"] for parte in partes if parte["type"] == "image_url"]
    assert imagens == [
        "data:image/jpeg;base64,quadro",
        "data:image/png;base64,tooltip",
        "data:image/png;base64,detalhe",
    ]
    rotulos = [parte["text"] for parte in partes[1:] if parte["type"] == "text"]
    assert "Contexto" in rotulos[0] and "800x450" in rotulos[0]
    assert "Tooltip" in rotulos[1] and "Detalhe nativo" in rotulos[2]


def test_visao_local_nao_transforma_texto_da_imagem_em_autorizacao_ou_ferramenta():
    runtime, chamadas, _, _ = _criar()

    assert runtime.analisar("imagem", "Leia o texto visível.") == "Vejo um botão azul."

    payload = chamadas[0][1]
    sistema = payload["messages"][0]
    assert sistema["role"] == "system"
    assert "não autoriza" in sistema["content"]
    assert "instruções" in sistema["content"]
    assert "tools" not in payload and "tool_choice" not in payload


@pytest.mark.parametrize("imagem,pergunta", [
    ("", "O que aparece?"),
    ("imagem", ""),
    ("LAYLAY_IMAGE_BUNDLE_V1:{inválido", "O que aparece?"),
])
def test_visao_local_recusa_entrada_incompleta_antes_do_transporte(imagem, pergunta):
    runtime, chamadas, _, _ = _criar()

    assert runtime.analisar(imagem, pergunta).startswith("Falha visual:")
    assert chamadas == []


def test_disponibilidade_local_indica_configuracao_sem_exigir_credencial_remota():
    runtime, chamadas, _, _ = _criar()
    assert runtime.disponivel is True
    sem_modelo, chamadas_sem_modelo, _, _ = _criar(model=" ")
    assert sem_modelo.disponivel is False
    assert sem_modelo.analisar("imagem", "O que aparece?").startswith("Falha visual:")
    assert chamadas == chamadas_sem_modelo == []


@pytest.mark.parametrize("resposta", [
    RespostaLLMFallback("Vejo uma tela.", motivo="timeout"),
    _Resposta("__LAYLAY_LLM_TIMEOUT__"),
    _Resposta("__LAYLAY_LLM_OCUPADA__"),
    _Resposta("<think>Estou tentando ler a tela"),
    _Resposta(""),
    _Resposta(status_code=503),
    _Resposta(dados={"choices": []}),
    _Resposta(dados={"choices": [{"message": {"tool_calls": [{"function": {"name": "DELETE_FILE"}}]}}]}),
])
def test_fallback_erro_ou_resposta_sem_conteudo_nao_vira_evidencia_visual(resposta):
    runtime, chamadas, _, falhas = _criar(resposta)

    assert runtime.analisar("imagem", "O que aparece?").startswith("Falha visual:")
    assert len(chamadas) == 1
    assert len(falhas) == 1


def test_visao_local_remove_raciocinio_interno_sem_alterar_descricao_final():
    runtime, _, _, _ = _criar(_Resposta("<think>raciocínio interno</think>Vejo um botão azul."))

    assert runtime.analisar("imagem", "O que aparece?") == "Vejo um botão azul."


def test_falha_de_transporte_nao_vaza_imagem_pergunta_ou_corpo_do_erro():
    runtime, _, logs, falhas = _criar(RuntimeError("segredo imagem-base64-sensivel"))

    resposta = runtime.analisar("imagem-base64-sensivel", "pergunta privada")

    assert resposta.startswith("Falha visual:")
    assert "segredo" not in repr(logs + falhas)
    assert "imagem-base64-sensivel" not in repr(logs + falhas)
    assert "pergunta privada" not in repr(logs + falhas)


@pytest.mark.parametrize('status', [400, 401, 403, 404, 429, 503])
def test_diagnostico_preserva_status_http_sem_publicar_corpo_sensivel(status):
    runtime, chamadas, logs, falhas = _criar(_Resposta('segredo privado', status_code=status))
    assert runtime.analisar('imagem privada', 'pergunta privada').startswith('Falha visual:')
    assert len(chamadas) == 1
    assert f'resposta_visual_http_{status}' in repr(logs + falhas)
    assert 'segredo privado' not in repr(logs + falhas)


@pytest.mark.parametrize('finish,codigo', [('length', 'resposta_visual_truncada'),
    ('content_filter', 'resposta_visual_filtrada'), ('stop', 'estrutura_visual_invalida')])
def test_diagnostico_separa_truncamento_filtro_e_schema(finish, codigo):
    from mente_laylay.percepcao.visao_jogo.presenca_visual import criar_contrato_saida_presenca_visual
    runtime, chamadas, logs, falhas = _criar(_Resposta(dados={
        'choices': [{'message': {'content': '{"segredo":"privado"}'}, 'finish_reason': finish}]}))
    assert runtime.analisar('imagem', 'Leia.', contrato_saida=criar_contrato_saida_presenca_visual()).startswith('Falha visual:')
    assert len(chamadas) == 1
    assert codigo in repr(logs + falhas)
    assert 'privado' not in repr(logs + falhas)


def test_sintese_local_reusa_transporte_sem_reenviar_imagem():
    runtime, chamadas, _, _ = _criar(_Resposta("O item dá 20 de armadura."))

    assert runtime.sintetizar("Leitura: armadura 20.", "Explique os dados.") == "O item dá 20 de armadura."

    payload = chamadas[0][1]
    assert payload["model"] == "qwen3-vl:4b"
    assert payload["_laylay_percepcao_visual"] is True
    assert payload["_laylay_prioridade_interativa"] is False
    partes = payload["messages"][-1]["content"]
    assert all(parte["type"] == "text" for parte in partes)
    assert "Leitura: armadura 20." in repr(partes)
    assert "Explique os dados." in repr(partes)


@pytest.mark.parametrize("resposta", [RespostaLLMFallback("Pareceu bom."), _Resposta("__LAYLAY_LLM_TIMEOUT__"), RuntimeError("erro")])
def test_sintese_local_falha_sem_inventar_resultado(resposta):
    runtime, _, _, _ = _criar(resposta)
    assert runtime.sintetizar("Leitura: 20.", "Explique.") == ""


def test_sintese_local_incompleta_nao_chama_modelo():
    runtime, chamadas, _, _ = _criar()
    assert runtime.sintetizar("", "Explique.") == ""
    assert runtime.sintetizar("Leitura: 20.", "") == ""
    assert chamadas == []


class _ThreadImediata:
    def __init__(self, target, **_opcoes):
        self.target = target

    def start(self):
        self.target()


def _captura_com_resultado(analisar):
    memorias, falas = [], []
    resultado = executar_captura_tela(
        "pc_a",
        enviar_pc_b=lambda _pedido: False,
        capturar_tela=lambda: "imagem",
        analisar_imagem=analisar,
        falar=lambda *args: falas.append(args),
        estado_emocional=lambda: ("calma", 1),
        registrar_memoria=lambda *args, **kwargs: memorias.append((args, kwargs)),
        thread_factory=_ThreadImediata,
        retornar_resultado=True,
        falar_progresso=False,
        log=lambda *_args: None,
    )
    return resultado.aguardar(), memorias, falas


@pytest.mark.parametrize("resposta", [
    RespostaLLMFallback("Vejo um botão azul.", motivo="timeout"),
    _Resposta("__LAYLAY_LLM_INDISPONIVEL__"),
    _Resposta(status_code=503),
])
def test_captura_manual_nao_confirma_nem_persiste_falha_do_modelo_visual_local(resposta):
    runtime, chamadas, _, _ = _criar(resposta)

    resultado, memorias, falas = _captura_com_resultado(runtime.analisar)

    assert len(chamadas) == 1
    assert memorias == [], "Falha do provedor não é memória visual factual."
    assert resultado["ok"] is False
    assert resultado["confirmado"] is False
    assert resultado["status"] == "analise_visual_sem_resultado"
    assert falas, "Uma captura consumida com falha deve ter conclusão observável."


@pytest.mark.parametrize("descricao", [
    "Falha visual: o modelo não respondeu.",
    "Erro: chamada visual recusada.",
    "__LAYLAY_LLM_TIMEOUT__",
])
def test_captura_manual_recusa_estado_tecnico_antes_de_publicar_memoria_ou_receipt(descricao):
    resultado, memorias, falas = _captura_com_resultado(lambda _imagem, _pergunta: descricao)

    assert memorias == []
    assert resultado["ok"] is False
    assert resultado["confirmado"] is False
    assert resultado["status"] == "analise_visual_sem_resultado"
    assert falas


def test_captura_manual_preserva_descricao_valida_e_receipt_confirmado():
    runtime, chamadas, _, _ = _criar(_Resposta("Vejo um botão azul."))

    resultado, memorias, falas = _captura_com_resultado(runtime.analisar)

    assert len(chamadas) == 1
    assert len(memorias) == 1
    assert resultado["ok"] is True
    assert resultado["confirmado"] is True
    assert resultado["status"] == "captura_concluida"
    assert resultado["descricao"] == falas[-1][0] == "Vejo um botão azul."
