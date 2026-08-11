from __future__ import annotations

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.integracao.llm_http import (
    compactar_payload_llm_local,
    payload_precisa_compactar_llm_local,
)
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.integracao.preparador_requisicao_llm import (
    PreparadorRequisicaoLLMRuntime,
)
from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
from mente_laylay.personalidade.proporcao_resposta import limite_tokens_resposta


def _chars(payload: dict) -> int:
    return sum(
        len(str(item.get("content") or ""))
        for item in payload.get("messages", [])
        if isinstance(item, dict)
    )


def test_conversa_rapida_troca_prompt_completo_por_contrato_canonico_compacto() -> None:
    payload = preparar_payload_llm(
        [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": "Oi Lay, tudo bem com você?"},
        ],
        model="teste",
        max_tokens=640,
        modo_rapido=True,
    )
    sistema = payload["messages"][0]["content"]

    assert payload["max_tokens"] == 128
    assert _chars(payload) < 3000
    assert "Você é Laylay" in sistema
    assert "não autorizam ação" in sistema
    assert "Retorne somente JSON válido" in sistema
    assert "Playlists Disponíveis" not in sistema


def test_prompt_especializado_rapido_nao_e_substituido_pelo_prompt_da_personalidade() -> None:
    especializado = "Classifique a cor. Responda somente JSON válido."
    payload = preparar_payload_llm(
        [
            {"role": "system", "content": especializado},
            {"role": "user", "content": "roxo"},
        ],
        model="teste",
        modo_rapido=True,
    )

    assert payload["messages"][0]["content"] == especializado


def _preparador(contadores: dict[str, int], *, ativo: bool = True):
    def contar(nome: str, retorno):
        def callback(*_args, **_kwargs):
            contadores[nome] = contadores.get(nome, 0) + 1
            return retorno
        return callback

    return PreparadorRequisicaoLLMRuntime(
        model="teste",
        endpoint_local_getter=lambda: True,
        resumo_do_dia_getter=contar("resumo", "Resumo durável do dia."),
        data_atual_getter=lambda: "2026-08-10",
        normalizar_texto=lambda texto: texto.casefold(),
        mapear_pastas=contar("arquivos", "C:/projeto"),
        contexto_logs_getter=contar("logs", ["aba aberta"]),
        contexto_navegador_relevante=lambda texto: any(
            sinal in texto.casefold() for sinal in ("aba", "site", "página", "pagina")
        ),
        contexto_sistema_getter=contar("sistema", {"exe": "opera"}),
        obter_contexto_paginas=contar("pagina", "Conteúdo editorial da página."),
        resumo_mente_integrada=contar("mente", "--- MENTE INTEGRADA ---\nturno atual"),
        otimizacao_prompt_ativa=ativo,
        log=lambda *_args: None,
    )


def test_fontes_externas_nao_sao_consultadas_em_pergunta_comum() -> None:
    contadores: dict[str, int] = {}
    runtime = _preparador(contadores)

    runtime.preparar(PedidoModelo.criar([
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": "Você prefere rock ou metal?"},
    ]))

    assert contadores == {"mente": 1}


def test_contexto_da_pagina_e_resumo_diario_sao_consultados_sob_demanda() -> None:
    contadores: dict[str, int] = {}
    runtime = _preparador(contadores)

    requisicao = runtime.preparar(PedidoModelo.criar([
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": "O que aconteceu hoje e nesta página atual?"},
    ]))
    conteudo = "\n".join(item["content"] for item in requisicao.payload["messages"])

    assert contadores == {
        "logs": 1,
        "sistema": 1,
        "resumo": 1,
        "pagina": 1,
        "mente": 1,
    }
    assert "Resumo durável do dia" in conteudo
    assert "Conteúdo editorial da página" in conteudo


def test_chave_de_reversao_restaura_consulta_historica_das_fontes() -> None:
    contadores: dict[str, int] = {}
    runtime = _preparador(contadores, ativo=False)

    runtime.preparar(PedidoModelo.criar([
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": "Oi Lay"},
    ]))

    assert contadores["resumo"] == 1
    assert contadores["logs"] == 1
    assert contadores["sistema"] == 1
    assert contadores["pagina"] == 1


class _MemoriaLegada:
    def __init__(self) -> None:
        self.chamadas = 0

    def formatar_memoria_para_prompt(self, **_kwargs):
        self.chamadas += 1
        return "memória legada"


def _contexto_prompt(*, texto_mente: str, contadores: dict[str, int]):
    memoria = _MemoriaLegada()

    def playlists():
        contadores["playlists"] = contadores.get("playlists", 0) + 1
        return "Rock: 3 músicas"

    runtime = ContextoPromptRuntime(
        memoria_sqlite=memoria,
        resumo_mente_integrada=lambda _texto: texto_mente,
        formatar_playlists=playlists,
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt=BASE_SYSTEM_PROMPT,
        estado_getter=lambda: {
            "messages": [],
            "aba_titulo_atual": "História da China",
            "aba_url_atual": "https://pt.wikipedia.org",
        },
        otimizacao_prompt_ativa=True,
    )
    return runtime, memoria


def test_contexto_completo_poupa_playlist_aba_e_memoria_duplicada_quando_irrelevantes() -> None:
    contadores: dict[str, int] = {}
    runtime, memoria = _contexto_prompt(
        texto_mente="--- MENTE INTEGRADA ---\ncontexto selecionado",
        contadores=contadores,
    )

    _mensagens, prompt = runtime.preparar("Explique recursão de um jeito simples")

    assert contadores == {}
    assert memoria.chamadas == 0
    assert "História da China" not in prompt
    assert "Rock: 3 músicas" not in prompt
    assert runtime.diagnostico()["fontes_poupadas"] == {
        "aba": 1,
        "playlists": 1,
        "memoria_legada": 1,
    }


def test_contexto_musical_consulta_playlists_sem_abrir_memoria_legada() -> None:
    contadores: dict[str, int] = {}
    runtime, memoria = _contexto_prompt(
        texto_mente="--- MENTE INTEGRADA ---\ncontexto selecionado",
        contadores=contadores,
    )

    _mensagens, prompt = runtime.preparar("Quais playlists de rock você tem?")

    assert contadores == {"playlists": 1}
    assert memoria.chamadas == 0
    assert "Rock: 3 músicas" in prompt


def test_limites_de_saida_preservam_explicacao_e_matematica() -> None:
    assert limite_tokens_resposta("oi lay", modo_rapido=True) == 128
    assert limite_tokens_resposta("qual você prefere?") == 224
    assert limite_tokens_resposta("explique como isso funciona") == 512
    assert limite_tokens_resposta("resolva 3(2x-5)-4(x+1)=10") == 800


def test_compactacao_preventiva_e_proporcional_nao_reduz_saida_matematica() -> None:
    payload_curto = {
        "messages": [
            {"role": "system", "content": BASE_SYSTEM_PROMPT + "x" * 3000},
            {"role": "user", "content": "oi"},
        ],
        "max_tokens": 128,
    }
    assert payload_precisa_compactar_llm_local(payload_curto) is True
    compacto = compactar_payload_llm_local(payload_curto)
    assert _chars(compacto) <= 5000
    assert compacto["max_tokens"] == 128

    payload_matematica = dict(payload_curto, max_tokens=800)
    compacto_matematica = compactar_payload_llm_local(payload_matematica)
    assert compacto_matematica["max_tokens"] == 800
