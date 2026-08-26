from mente_laylay.cognicao.investigacao_erro import (
    InvestigadorErroRuntime,
    extrair_consulta_erro,
)
from mente_laylay.especialistas.area_transferencia import AreaTransferenciaRuntime


class RespostaHTML:
    text = """
    <a class="result__a" href="https://exemplo.test/http500">Erro HTTP 500</a>
    <a class="result__snippet">Indica falha inesperada no servidor.</a>
    """

    def raise_for_status(self):
        return None


def test_consulta_de_erro_e_curta_e_descarta_descricao_inteira() -> None:
    consulta = extrair_consulta_erro(
        "ERRO 500: Falha interna do servidor. Detalhes longos sobre toda a solicitação."
    )
    assert consulta.casefold().startswith("erro 500")
    assert "detalhes longos" not in consulta.casefold()


def test_investigacao_pesquisa_e_sintetiza_sem_abrir_navegador() -> None:
    chamadas_web = []
    mensagens_llm = []
    opcoes_llm = []
    runtime = InvestigadorErroRuntime(
        requests_get=lambda *args, **kwargs: chamadas_web.append((args, kwargs)) or RespostaHTML(),
        enviar_mensagem=lambda mensagens, **kwargs: (
            mensagens_llm.append(mensagens),
            opcoes_llm.append(kwargs),
            "É um erro interno do servidor. Confira os logs e a conexão com as dependências.",
        )[-1],
        log=lambda *_args: None,
    )

    resultado = runtime.investigar("HTTP_500_INTERNAL_SERVER_ERROR")

    assert resultado["ok"] is True
    assert resultado["pesquisa_web"] is True
    assert "logs" in resultado["fala"]
    assert chamadas_web[0][0][0] == "https://html.duckduckgo.com/html/"
    assert "RESULTADOS DA PESQUISA" in mensagens_llm[0][1]["content"]
    assert opcoes_llm[0]["_prioridade_interativa"] is True
    assert opcoes_llm[0]["_permitir_conversa_modo_jogo"] is True
    assert resultado["sintese_llm"] is True


def test_estado_tecnico_da_llm_nunca_vira_fala_da_investigacao() -> None:
    runtime = InvestigadorErroRuntime(
        requests_get=lambda *_args, **_kwargs: RespostaHTML(),
        enviar_mensagem=lambda *_args, **_kwargs: "__LAYLAY_LLM_INDISPONIVEL__",
        limpar_resposta=lambda texto: texto.strip("_"),
        log=lambda *_args: None,
    )

    resultado = runtime.investigar("HTTP_500_INTERNAL_SERVER_ERROR")

    assert resultado["ok"] is True
    assert resultado["sintese_llm"] is False
    assert "LAYLAY_LLM" not in resultado["fala"]
    assert "falha inesperada no servidor" in resultado["fala"]


def test_area_transferencia_usa_investigacao_interna_para_erro() -> None:
    falas = []
    execucoes = []
    runtime = AreaTransferenciaRuntime(
        falar=lambda fala, *_args: falas.append(fala),
        leitor=lambda: "ValueError: invalid volume",
        investigar_erro=lambda _conteudo: {
            "ok": True,
            "fala": "O volume recebido é inválido; normalize o percentual antes de enviar.",
        },
        executar_intencao=lambda *_args: execucoes.append(True) or True,
        log=lambda *_args: None,
    )

    assert runtime.processar("pesquisa o erro que eu copiei") is True
    assert "normalize" in falas[-1]
    assert execucoes == []
