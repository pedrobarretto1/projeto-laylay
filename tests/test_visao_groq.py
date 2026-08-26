from __future__ import annotations

from types import SimpleNamespace

from mente_laylay.cognicao.memoria_visual import analisar_com_groq
from mente_laylay.percepcao.imagens_multimodais import empacotar_imagens


class _CompletionsFake:
    def __init__(self, resultado=None, erro=None):
        self.resultado = resultado
        self.erro = erro
        self.chamadas = []

    def create(self, **kwargs):
        self.chamadas.append(kwargs)
        if self.erro is not None:
            raise self.erro
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.resultado))]
        )


def _fabrica(completions):
    clientes = []

    def criar(**kwargs):
        cliente = SimpleNamespace(
            chat=SimpleNamespace(completions=completions),
            kwargs=kwargs,
        )
        clientes.append(cliente)
        return cliente

    return criar, clientes


def test_groq_visual_usa_modelo_e_contrato_multimodal_atual():
    completions = _CompletionsFake(resultado="O item aumenta dano de fogo.")
    fabrica, clientes = _fabrica(completions)
    resposta = analisar_com_groq(
        "imagem-base64",
        "esse item é bom?",
        "chave-teste",
        "qwen/qwen3.6-27b",
        client_factory=fabrica,
        log=lambda *_: None,
    )
    assert resposta == "O item aumenta dano de fogo."
    assert clientes[0].kwargs == {"api_key": "chave-teste"}
    chamada = completions.chamadas[0]
    assert chamada["model"] == "qwen/qwen3.6-27b"
    assert chamada["max_completion_tokens"] == 512
    assert chamada["reasoning_effort"] == "none"
    assert chamada["temperature"] == 0.7
    assert chamada["top_p"] == 0.8
    assert "max_tokens" not in chamada
    imagem = chamada["messages"][0]["content"][1]
    assert imagem["image_url"]["url"] == "data:image/jpeg;base64,imagem-base64"


def test_groq_visual_envia_recortes_separados_com_rotulos():
    completions = _CompletionsFake(resultado="Nome e atributos lidos.")
    fabrica, _clientes = _fabrica(completions)
    pacote = empacotar_imagens([
        {"label": "Quadro geral", "data": "geral", "width": 1920, "height": 810},
        {"label": "Tooltip nativo", "data": "tooltip", "width": 1400, "height": 1000},
    ])
    resposta = analisar_com_groq(
        pacote, "Leia literalmente.", "chave", "qwen/qwen3.6-27b",
        client_factory=fabrica, temperature=0.05, log=lambda *_: None,
    )
    assert resposta == "Nome e atributos lidos."
    chamada = completions.chamadas[0]
    conteudo = chamada["messages"][0]["content"]
    imagens = [item for item in conteudo if item["type"] == "image_url"]
    rotulos = [item["text"] for item in conteudo if item["type"] == "text"][1:]
    assert len(imagens) == 2
    assert imagens[0]["image_url"]["url"].endswith(",geral")
    assert imagens[1]["image_url"]["url"].endswith(",tooltip")
    assert any("1920x810" in rotulo for rotulo in rotulos)
    assert chamada["temperature"] == 0.05


def test_groq_visual_reserva_detalhe_para_confirmacao_e_reduz_tpm():
    completions = _CompletionsFake(resultado="Leitura inicial.")
    fabrica, _clientes = _fabrica(completions)
    logs = []
    pacote = empacotar_imagens([
        {"label": "Quadro geral", "data": "geral", "width": 1280, "height": 540},
        {"label": "Tooltip amplo", "data": "regiao", "width": 1200, "height": 900},
        {"label": "Detalhe nativo", "data": "detalhe", "width": 900, "height": 900},
    ])

    assert analisar_com_groq(
        pacote, "Leia o item.", "chave", "qwen/qwen3.6-27b",
        client_factory=fabrica, log=logs.append,
    ) == "Leitura inicial."

    conteudo = completions.chamadas[0]["messages"][0]["content"]
    urls = [
        item["image_url"]["url"]
        for item in conteudo if item["type"] == "image_url"
    ]
    assert len(urls) == 2
    assert urls[0].endswith(",geral")
    assert urls[1].endswith(",regiao")
    assert all(not url.endswith(",detalhe") for url in urls)
    assert any("pacote otimizado" in item for item in logs)


def test_groq_visual_explica_modelo_desativado_sem_vazar_chave():
    completions = _CompletionsFake(
        erro=RuntimeError(
            "400 model_decommissioned meta-llama scout Authorization Bearer gsk_segredo123"
        )
    )
    fabrica, _clientes = _fabrica(completions)
    logs = []
    resposta = analisar_com_groq(
        "imagem",
        "pergunta",
        "gsk_segredo123",
        "modelo-antigo",
        client_factory=fabrica,
        log=logs.append,
    )
    assert resposta == "Falha visual: o modelo configurado foi desativado pela Groq."
    assert len(completions.chamadas) == 1
    assert logs and "categoria=modelo_desativado" in logs[0]
    assert "gsk_segredo123" not in logs[0]


def test_groq_visual_repete_somente_falha_transitoria():
    completions = _CompletionsFake(erro=RuntimeError("429 rate limit"))
    fabrica, _clientes = _fabrica(completions)
    esperas = []
    resposta = analisar_com_groq(
        "imagem",
        "pergunta",
        "chave",
        "qwen/qwen3.6-27b",
        client_factory=fabrica,
        sleep_fn=esperas.append,
        log=lambda *_: None,
    )
    assert resposta == "Falha visual: a Groq atingiu o limite temporário."
    assert len(completions.chamadas) == 3
    assert esperas == [4, 8]


def test_groq_visual_usa_http_quando_sdk_nao_esta_disponivel():
    chamadas = []

    class _RespostaHttp:
        status_code = 200
        text = ""

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "Vejo um item raro."}}]}

    def post(url, **kwargs):
        chamadas.append((url, kwargs))
        return _RespostaHttp()

    resposta = analisar_com_groq(
        "imagem",
        "esse item é bom?",
        "chave-http",
        "qwen/qwen3.6-27b",
        requests_post=post,
        forcar_http=True,
        log=lambda *_: None,
    )
    assert resposta == "Vejo um item raro."
    assert chamadas[0][0] == "https://api.groq.com/openai/v1/chat/completions"
    assert chamadas[0][1]["headers"]["Authorization"] == "Bearer chave-http"
    assert chamadas[0][1]["json"]["model"] == "qwen/qwen3.6-27b"
    assert chamadas[0][1]["timeout"] == 35


def test_groq_visual_respeita_orcamento_curto_do_modo_jogo():
    chamadas = []
    esperas = []

    def post(_url, **kwargs):
        chamadas.append(kwargs)
        raise TimeoutError("tempo esgotado")

    resposta = analisar_com_groq(
        "imagem",
        "pode ver essa bota aqui?",
        "chave-http",
        "qwen/qwen3.6-27b",
        requests_post=post,
        forcar_http=True,
        max_tentativas=1,
        timeout_s=12,
        retry_delay_s=0.6,
        sleep_fn=esperas.append,
        log=lambda *_: None,
    )
    assert resposta.startswith("Falha visual:")
    assert len(chamadas) == 1
    assert chamadas[0]["timeout"] == 12
    assert esperas == []
