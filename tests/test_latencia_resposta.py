from __future__ import annotations

import json
import threading
import time

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.integracao.llm_http import (
    FALHA_LLM_INDISPONIVEL,
    FALHA_LLM_TIMEOUT,
    RespostaLLMFallback,
    compactar_payload_llm_local,
    executar_chat_llm,
    post_chat_llm,
)
import requests
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.cognicao.pesquisa_contextual import PesquisaContextualRuntime
from mente_laylay.cognicao.orquestrador_turno_runtime import registrar_metrica_opcional
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.autonomia.fluxos_conversa import usar_modo_rapido_conversa
from mente_laylay.cognicao.referencias_linguagem import texto_tem_referencia_contextual
from mente_laylay.personalidade.proporcao_resposta import limite_tokens_resposta


class _MemoriaFalsa:
    def salvar_aprendizados_semanticos(self, itens):
        return list(itens or [])


def test_equacao_compacta_nao_usa_prompt_rapido() -> None:
    rapido = usar_modo_rapido_conversa(
        "3(2x-5)-4(x+1)=2(3x-7)+9",
        normalizar_texto=lambda texto: texto.casefold(),
    )

    assert rapido is False


def test_nao_entendi_preserva_contexto_com_prompt_completo() -> None:
    rapido = usar_modo_rapido_conversa(
        "não entendi",
        normalizar_texto=lambda texto: texto.casefold(),
    )

    assert rapido is False


def test_qualquer_fala_semanticamente_dependente_evitar_prompt_rapido() -> None:
    chamadas = []
    rapido = usar_modo_rapido_conversa(
        "pode explicar por outro ângulo?",
        normalizar_texto=lambda texto: texto.casefold(),
        texto_depende_de_contexto=lambda texto: chamadas.append(texto) or True,
    )

    assert rapido is False
    assert chamadas == ["pode explicar por outro ângulo?"]


def test_reparo_discursivo_e_contextual_sem_depender_do_assunto() -> None:
    for texto in ("não entendi", "como assim?", "explica isso melhor", "mais devagar"):
        assert texto_tem_referencia_contextual(texto) is True


def test_fala_curta_dependente_recebe_espaco_para_resposta_completa() -> None:
    assert limite_tokens_resposta("como assim?", depende_contexto=True) == 512


def _payload(mensagens, resumo_cb):
    return preparar_payload_llm(
        mensagens,
        model="teste",
        resumo_mente_integrada=resumo_cb,
    )


def test_prompt_rapido_limita_saida_sem_reduzir_resposta_complexa() -> None:
    mensagens = [
        {"role": "system", "content": "Responda em JSON."},
        {"role": "user", "content": "oi lay"},
    ]

    rapido = preparar_payload_llm(
        mensagens, model="teste", max_tokens=640, modo_rapido=True,
    )
    completo = preparar_payload_llm(
        mensagens, model="teste", max_tokens=640, modo_rapido=False,
        endpoint_local=True,
    )

    assert rapido["max_tokens"] == 128
    assert completo["max_tokens"] == 640


def test_compactacao_local_preserva_contrato_e_continuidade_recente() -> None:
    principal = (
        "Você é Laylay. "
        + "P" * 4900
        + " FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON"
    )
    payload = preparar_payload_llm(
        [
            {"role": "system", "content": principal},
            {"role": "user", "content": "Você prefere rock ou metal?"},
            {"role": "assistant", "content": "Eu prefiro rock."},
            {"role": "user", "content": "Por quê?"},
            {
                "role": "assistant",
                "content": "Porque ele passeia por mais climas sem perder a força.",
            },
            {
                "role": "user",
                "content": "Agora explica isso de um jeito simples.",
            },
        ],
        model="teste",
        max_tokens=640,
        endpoint_local=True,
        resumo_do_dia="R" * 7000,
        resumo_mente_integrada=lambda _texto: (
            "--- MENTE INTEGRADA ---\n"
            + ("regra auxiliar sem relação\n" * 180)
            + "Turno atual: modalidade=pergunta | autoriza_execucao=False\n"
            + "Contexto selecionado pelo filtro: ultima_fala[conversa]: "
            + "Eu prefiro rock porque ele passeia por mais climas.\n"
            + ("cauda sem relação\n" * 180)
        ),
    )

    compacto = compactar_payload_llm_local(payload)
    conteudos = [item["content"] for item in compacto["messages"]]

    assert conteudos[0].startswith("Você é Laylay")
    assert "FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON" in conteudos[0]
    assert "Você prefere rock ou metal?" in conteudos
    assert "Eu prefiro rock." in conteudos
    assert "Por quê?" in conteudos
    assert "Porque ele passeia por mais climas sem perder a força." in conteudos
    assert conteudos[-1] == "Agora explica isso de um jeito simples."
    assert any(
        "Contexto selecionado pelo filtro" in conteudo
        and "prefiro rock" in conteudo
        for conteudo in conteudos
    )
    assert sum(len(item) for item in conteudos) <= 12000


def test_retrato_mental_ja_presente_nao_e_montado_nem_enviado_duas_vezes() -> None:
    chamadas = []
    mensagens = [
        {"role": "system", "content": "Base\n--- MENTE INTEGRADA ---\nAssunto atual: GTA 6"},
        {"role": "user", "content": "continua"},
    ]

    payload = _payload(mensagens, lambda texto: chamadas.append(texto) or "--- MENTE INTEGRADA ---\nDuplicada")

    conteudo = "\n".join(str(item.get("content") or "") for item in payload["messages"])
    assert conteudo.count("--- MENTE INTEGRADA ---") == 1
    assert chamadas == []


def test_retrato_mental_ainda_e_injetado_em_chamada_que_nao_o_possui() -> None:
    payload = _payload(
        [{"role": "system", "content": "Base"}, {"role": "user", "content": "oi"}],
        lambda _texto: "--- MENTE INTEGRADA ---\nPedro gosta de rock",
    )
    conteudo = "\n".join(str(item.get("content") or "") for item in payload["messages"])
    assert conteudo.count("--- MENTE INTEGRADA ---") == 1


def test_saida_conversacional_recuperavel_nao_faz_segunda_chamada_llm() -> None:
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "gosto muito de GTA 5",
        'Que memória boa. [fala]: "Isso marcou sua infância." [tipo_interacao]: conversa [comandos]: []',
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert resposta["fala"] == "Que memória boa."
    assert chamadas == []


def test_json_escapado_incompleto_entrega_fala_sem_reparo_ou_supressao() -> None:
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "oi lay, tudo bem?",
        r'{\"fala\":\"Oi, Pedro! Tudo bem aqui, só esperando você aparecer...',
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert resposta["fala"].startswith("Oi, Pedro!")
    assert resposta["suprimir_fala"] is False
    assert chamadas == []


def test_saida_com_acao_ambigua_preserva_autocorrecao_com_llm() -> None:
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "abre o site",
        "Vou abrir. open_url https://example.com",
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or '{"fala":"Vou abrir.","comandos":[]}',
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert resposta["fala"] == "Vou abrir."
    assert chamadas == [True]


def test_pergunta_com_resposta_adiada_e_refeita_no_mesmo_turno() -> None:
    chamadas = []

    def responder(*_args, **_kwargs):
        chamadas.append(True)
        return '{"fala":"Ela viu 20 casas, porque eram as mesmas na ida e na volta.","comandos":[]}'

    resposta = preparar_resposta_para_execucao(
        "Quantas casas ela viu no total?",
        '{"fala":"Vou pensar um pouco mais antes de responder.","comandos":[]}',
        enviar_mensagem_cb=responder,
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert chamadas == [True]
    assert resposta["fala"].startswith("Ela viu 20 casas")
    assert "vou pensar" not in resposta["fala"].casefold()


def test_equacao_com_promessa_de_calculo_e_concluida_sem_nova_entrada() -> None:
    chamadas = []

    def concluir(*_args, **_kwargs):
        chamadas.append(True)
        return json.dumps({
            "fala": (
                "Expandindo, o lado esquerdo vira 2x - 19 e o direito vira 6x - 5. "
                "Então 2x - 19 = 6x - 5, logo -14 = 4x. Portanto, x = -3,5."
            ),
            "comandos": [],
        }, ensure_ascii=False)

    resposta = preparar_resposta_para_execucao(
        "3(2x-5)-4(x+1)=2(3x-7)+9",
        (
            "Fala, mano! Vamos resolver essa equação juntos. Primeiro, vamos expandir tudo. "
            "Vou fazer o cálculo pra gente. Quer que eu mostre os passos também?"
        ),
        enviar_mensagem_cb=concluir,
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert chamadas == [True]
    assert resposta["fala"].endswith("Portanto, x = -3,5.")
    assert "quer que eu" not in resposta["fala"].casefold()


def test_equacao_ja_concluida_nao_dispara_continuacao_extra() -> None:
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "2x+4=10",
        '{"fala":"Subtraindo 4 e dividindo por 2, portanto x = 3.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert resposta["fala"].endswith("x = 3.")


def test_filtro_de_personalidade_nao_apaga_fala_natural_recuperada() -> None:
    fallback = "Não consegui encaixar isso direito. Me fala de outro jeito?"
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "ta tudo certo, e a sua?",
        '{"fala":"Tudo certo por aqui também. E gostei de saber que você está bem.","comandos":[]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala=fallback,
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert resposta["fala"].startswith("Tudo certo por aqui")
    assert resposta["fala"] != fallback
    assert chamadas == []


def test_fallback_interno_e_refeito_no_mesmo_turno_sem_pedir_repeticao() -> None:
    fallback = "Não consegui encaixar isso direito. Me fala de outro jeito?"
    chamadas = []

    def reparar(*_args, **_kwargs):
        chamadas.append(True)
        return '{"fala":"Por aqui também tá tudo certo. E gostei de saber que você tá bem.","comandos":[]}'

    resposta = preparar_resposta_para_execucao(
        "ta tudo certo, e a sua?",
        fallback,
        enviar_mensagem_cb=reparar,
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala=fallback,
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert chamadas == [True]
    assert "tudo certo" in resposta["fala"].casefold()
    assert "outro jeito" not in resposta["fala"].casefold()


def test_falha_do_reparo_mantem_turno_aberto_sem_inventar_resposta() -> None:
    fallback = "Não consegui encaixar isso direito. Me fala de outro jeito?"
    falhas = []
    resposta = preparar_resposta_para_execucao(
        "ta tudo certo, e a sua?",
        fallback,
        enviar_mensagem_cb=lambda *_args, **_kwargs: "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala=fallback,
        memoria_sqlite=_MemoriaFalsa(),
        registrar_falha_cb=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=lambda *_args: None,
    )

    assert "não quero responder pela metade" in resposta["fala"]
    assert resposta["suprimir_fala"] is False
    assert falhas == [(
        ("resposta_llm", "saida_nao_entregavel"),
        {
            "classe": "degradacao",
            "impacto": "turno",
            "fallback": "contingencia_conversacional",
        },
    )]


def test_reparo_de_fala_nunca_importa_comando_gerado_na_segunda_tentativa() -> None:
    fallback = "Não consegui encaixar isso direito. Me fala de outro jeito?"
    resposta = preparar_resposta_para_execucao(
        "ta tudo certo, e a sua?",
        fallback,
        enviar_mensagem_cb=lambda *_args, **_kwargs: (
            '{"fala":"Por aqui também está tudo certo.",'
            '"comandos":[{"acao":"open_url","alvo":"https://example.com"}]}'
        ),
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala=fallback,
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert resposta["fala"] == "Por aqui também está tudo certo."
    assert resposta["comandos"] == []


def test_continuacao_autonoma_nao_autoriza_comando_pratico() -> None:
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "abre o Chrome",
        '{"fala":"Vou fazer isso agora.","comandos":[{"acao":"open_app","alvo":"chrome"}]}',
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="Tô por aqui.",
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert resposta["comandos"]


def test_tarefa_secundaria_nao_espera_modelo_local_ocupado() -> None:
    lock = threading.Lock()
    lock.acquire()
    chamadas_http = []
    try:
        resposta, _ = post_chat_llm(
            {},
            {"messages": [{"role": "user", "content": "resuma em segundo plano"}]},
            base_url="http://127.0.0.1:11434/v1",
            local_timeout=120,
            remote_timeout=30,
            bad_request_until=0,
            lock=lock,
            requests_post=lambda *_args, **_kwargs: chamadas_http.append(True),
            print_fn=lambda *_args: None,
            prioridade_interativa=False,
        )
    finally:
        lock.release()

    assert chamadas_http == []
    assert resposta.status_code == 200


def test_timeout_local_nao_expoe_ollama_nem_cria_ciclo_de_repeticao() -> None:
    falhas = []

    def timeout(*_args, **_kwargs):
        raise requests.exceptions.ReadTimeout("demorou")

    resposta = executar_chat_llm(
        {"messages": []},
        post_chat=timeout,
        interpretar_payload=lambda _payload: "",
        api_key="teste",
        http_referer="http://localhost",
        app_title="Laylay",
        endpoint_local=True,
        log=lambda _mensagem: None,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )

    assert resposta == FALHA_LLM_TIMEOUT
    assert len(falhas) == 1
    args_falha, kwargs_falha = falhas[0]
    assert args_falha == ("llm_http", "timeout_resposta")
    assert isinstance(kwargs_falha.pop("erro"), requests.exceptions.ReadTimeout)
    assert kwargs_falha == {
        "classe": "degradacao",
        "impacto": "turno",
        "fallback": "contingencia_conversacional",
    }

    verificada = verificar_fala_turno(
        resposta,
        plano={
            "texto_usuario": "ver esse item",
            "ato_principal": "comando",
            "requer_execucao": True,
            "comandos": [],
        },
        origem="resposta_ia",
    )
    assert verificada["aceita"] is False
    assert verificada["fala"] == ""
    assert verificada["problemas"] == ["estado_tecnico_llm"]


def test_404_openrouter_identifica_modelo_indisponivel_sem_expor_payload() -> None:
    falhas = []
    logs = []

    class Resposta404:
        status_code = 404

        def raise_for_status(self):
            raise requests.exceptions.HTTPError("404 com corpo privado")

    resposta = executar_chat_llm(
        {"model": "qwen/modelo-antigo", "messages": [{"role": "user", "content": "segredo"}]},
        post_chat=lambda *_args, **_kwargs: Resposta404(),
        interpretar_payload=lambda _payload: "",
        api_key="chave-secreta",
        http_referer="http://localhost",
        app_title="Laylay",
        endpoint_local=False,
        log=logs.append,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
    )

    assert resposta == FALHA_LLM_INDISPONIVEL
    assert logs == [
        "Erro 404 na OpenRouter: o modelo qwen/modelo-antigo não existe ou está sem provedor ativo."
    ]
    assert "segredo" not in " ".join(logs)
    assert falhas == [(('llm_http', 'modelo_remoto_indisponivel'), {
        'classe': 'defeito', 'impacto': 'turno', 'fallback': 'troca_modelo_openrouter',
    })]


def test_fallback_contextual_do_transporte_e_classificado_uma_vez() -> None:
    falhas = []
    resposta_http = RespostaLLMFallback(
        '{"fala":"Tô aqui.","comandos":[]}',
        motivo="modelo_local_ocupado",
        classe="degradacao",
        impacto="turno",
        fallback="contingencia_conversacional",
    )

    resposta = executar_chat_llm(
        {"messages": []},
        post_chat=lambda *_args, **_kwargs: resposta_http,
        interpretar_payload=lambda payload: payload["choices"][0]["message"]["content"],
        api_key="teste",
        http_referer="http://localhost",
        app_title="Laylay",
        endpoint_local=True,
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=lambda *_args: None,
    )

    assert "Tô aqui" in resposta
    assert falhas == [(
        ("llm_http", "modelo_local_ocupado"),
        {
            "classe": "degradacao",
            "impacto": "turno",
            "fallback": "contingencia_conversacional",
        },
    )]


def test_verificador_substitui_horario_inventado_pelo_relogio_local(monkeypatch) -> None:
    monkeypatch.setattr(
        "mente_laylay.cognicao.plano_turno.responder_consulta_horario",
        lambda: "São 22h47 agora. Já é noite por aqui.",
    )

    verificada = verificar_fala_turno(
        "São 14h47, e o sol ainda está aparecendo.",
        plano={"texto_usuario": "que horas são?", "ato_principal": "pergunta"},
        origem="resposta_ia",
    )

    assert verificada["aceita"] is True
    assert verificada["fala"] == "São 22h47 agora. Já é noite por aqui."
    assert "horario_substituido_pelo_relogio_local" in verificada["problemas"]


def test_timeout_nao_vaza_estado_interno_e_mantem_turno_aberto() -> None:
    fallback = "Não consegui encaixar isso direito. Me fala de outro jeito?"
    chamadas = []
    resposta = preparar_resposta_para_execucao(
        "aqui estão meus atributos",
        FALHA_LLM_TIMEOUT,
        enviar_mensagem_cb=lambda *_args, **_kwargs: chamadas.append(True) or "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala=fallback,
        memoria_sqlite=_MemoriaFalsa(),
        log=lambda *_args: None,
    )

    assert chamadas == []
    assert "__LAYLAY" not in resposta["fala"]
    assert resposta["fala"] == "Entendi. Continua — eu tô acompanhando daqui."
    assert resposta["suprimir_fala"] is False


def test_timeout_mantem_detalhes_da_observacao_visual_recente() -> None:
    resposta = preparar_resposta_para_execucao(
        "minha casinha ta legal ne lay",
        FALHA_LLM_TIMEOUT,
        enviar_mensagem_cb=lambda *_args, **_kwargs: "{}",
        limpar_texto_fala_cb=lambda texto: texto,
        fallback_fala="fallback",
        memoria_sqlite=_MemoriaFalsa(),
        contexto_contingencia={
            "contexto_jogo_atual": {
                "ultima_observacao": (
                    "Que aconchego! Adorei a decoração com as camas amarelas "
                    "e a vista para a água."
                ),
            },
        },
        log=lambda *_args: None,
    )

    assert "camas amarelas" in resposta["fala"]
    assert "vista para a água" in resposta["fala"]
    assert "acompanhando daqui" not in resposta["fala"]


def test_pesquisa_em_background_nao_bloqueia_e_alimenta_cache() -> None:
    iniciou = threading.Event()
    liberar = threading.Event()

    class RespostaHTTP:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "query": {
                    "pages": {
                        "1": {"title": "GTA 6", "extract": "Jogo eletrônico em desenvolvimento."}
                    }
                }
            }

    def get_lento(*_args, **_kwargs):
        iniciou.set()
        liberar.wait(timeout=2)
        return RespostaHTTP()

    runtime = PesquisaContextualRuntime(requests_get=get_lento)
    inicio = time.perf_counter()
    assert runtime.precarregar_contexto_tema("GTA 6") is True
    duracao = time.perf_counter() - inicio

    assert duracao < 0.2
    assert iniciou.wait(timeout=1)
    assert runtime.precarregar_contexto_tema("GTA 6") is False
    liberar.set()
    limite = time.time() + 2
    while time.time() < limite and not runtime.obter_contexto_cache("GTA 6"):
        time.sleep(0.01)
    assert runtime.obter_contexto_cache("GTA 6")["ok"] is True


def test_pesquisa_interativa_lenta_respeita_orcamento_e_conclui_no_cache() -> None:
    iniciou = threading.Event()
    liberar = threading.Event()

    class RespostaHTTP:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "query": {
                    "pages": {
                        "1": {"title": "Path of Exile 2", "extract": "Um RPG de ação."}
                    }
                }
            }

    def get_lento(*_args, **_kwargs):
        iniciou.set()
        liberar.wait(timeout=2)
        return RespostaHTTP()

    runtime = PesquisaContextualRuntime(
        requests_get=get_lento,
        orcamento_interativo_s=0.02,
        log=lambda _mensagem: None,
    )
    inicio = time.perf_counter()
    resposta = runtime.pesquisar_contexto_tema("Path of Exile 2")
    duracao = time.perf_counter() - inicio

    assert duracao < 0.2
    assert resposta["pesquisa_pendente"] is True
    assert iniciou.is_set()

    liberar.set()
    limite = time.time() + 2
    while time.time() < limite and not runtime.obter_contexto_cache("Path of Exile 2"):
        time.sleep(0.01)
    assert runtime.obter_contexto_cache("Path of Exile 2")["ok"] is True


def test_telemetria_de_pesquisa_nao_depende_do_escopo_do_planejador() -> None:
    registros = []

    class Observabilidade:
        def registrar_metrica(self, *args):
            registros.append(args)

    registrar_metrica_opcional({}, "pesquisa_factual", 12.0, True)
    registrar_metrica_opcional(
        {"_observabilidade_mente_runtime": Observabilidade()},
        "pesquisa_factual",
        12.0,
        True,
    )

    assert registros == [("pesquisa_factual", 12.0, True)]
