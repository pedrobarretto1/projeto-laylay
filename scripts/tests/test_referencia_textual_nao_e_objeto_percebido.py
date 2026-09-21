import pytest

from mente_laylay.memoria_mental.registro_semantico import resolver_referencia_pontuada
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.contrato_fala import formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_reparo_comunicacao
from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_pedido_fonte_textual
import json
from copy import deepcopy
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.integracao.registro_conversa_llm import RegistroPreparacaoConversa, PedidoModelo
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.registro_conversa_llm import EstadoConversaRuntime, ResultadoModelo
from types import SimpleNamespace


@pytest.mark.parametrize("rapido", [True, False])
def test_pedido_de_fonte_no_primeiro_envio_preserva_historico(rapido):
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    turno = {"id": 71, "modalidade": "pergunta", "autoriza_execucao": False}
    contrato = construir_contrato_semantico_fala(texto, turno=turno)
    estado = {"turno_atual": turno, "contrato_fala_atual": contrato}
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "",
        base_system_prompt="Personalidade", estado_getter=lambda: estado,
    )
    registro = RegistroPreparacaoConversa.criar(runtime)
    historico = [{"role": "assistant", "content": "O relato prova tudo."},
                 {"role": "user", "content": texto}]
    antes = deepcopy(historico)
    mensagens = registro.preparar_mensagens_modelo(historico, turno_id=71)
    pacote = registro.preparar_envio_modelo(historico, turno_id=71)
    assert pacote.contexto_fechado is True
    assert list(pacote.mensagens) == mensagens
    assert historico == antes
    assert texto not in str(mensagens)
    assert "O relato prova tudo" not in str(mensagens)
    assert json.loads(mensagens[-1]["content"])["ato_solicitado"] == "pedir_fonte_textual"
    payload = preparar_payload_llm(mensagens, model="teste", modo_rapido=rapido)
    assert payload["messages"][-1] == mensagens[-1]

    # Contrato anterior, ausência de identidade, fonte identificada e turno
    # composto nunca podem apagar uma instrução atual independente.
    for alteracao in (
        {"turno_id": 70}, {"turno_id": None},
        {"estado_referencia_textual": "identificada_sem_conteudo_validado"},
    ):
        estado["contrato_fala_atual"] = {**contrato, **alteracao}
        assert registro.preparar_mensagens_modelo(historico, turno_id=71) == antes
        assert not registro.preparar_envio_modelo(historico, turno_id=71).contexto_fechado
    estado["contrato_fala_atual"] = contrato
    for alteracao in ({"autoriza_execucao": True}, {"modalidade_geral": "misto"}, {"id": 72}):
        estado["turno_atual"] = {**turno, **alteracao}
        assert registro.preparar_mensagens_modelo(historico, turno_id=71) == antes


def test_projecao_sem_estado_preserva_pedido_original():
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "",
        base_system_prompt="Personalidade", estado_getter=lambda: None,
    )
    mensagens = [{"role": "user", "content": "Pode me recomendar um filme?"}]
    for valor in (None, [], "indisponivel"):
        runtime.estado_getter = lambda: valor
        assert runtime.preparar_mensagens_modelo(mensagens, turno_id=71) == mensagens
    def indisponivel():
        raise RuntimeError("estado indisponível")
    runtime.estado_getter = indisponivel
    assert runtime.preparar_mensagens_modelo(mensagens, turno_id=71) == mensagens


@pytest.mark.parametrize("rapido", [True, False])
def test_orquestrador_envia_ato_efemero_sem_reescrever_utterance(rapido):
    texto = "Esse texto confirma que o arquivo foi salvo?"
    turno = {"id": 81, "modalidade": "pergunta", "autoriza_execucao": False}
    contrato = construir_contrato_semantico_fala(texto, turno=turno)
    historico = []
    estado = EstadoConversaRuntime(
        getter=lambda: historico,
        setter=lambda novas: historico.__setitem__(slice(None), novas),
    )
    prompt = ContextoPromptRuntime(
        memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE", estado_getter=lambda: {
            "turno_atual": turno, "contrato_fala_atual": contrato,
            "messages": historico,
        },
    )
    pedidos = []
    resposta = "Pode me enviar o texto?"
    def modelo(pedido):
        pedidos.append(pedido)
        return ResultadoModelo(json.dumps({"fala": resposta, "comandos": []}), True)
    # Modelo e executores são fronteiras externas. Preparador, registro,
    # histórico e orquestrador são os componentes reais sob teste.
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "marcar_inicio_turno": lambda *a, **k: None,
        "obter_turno_atual": lambda: turno,
        "processar_comandos_prioritarios": lambda _: False,
        "contexto_inicio": lambda: {},
        "processar_inicio_fluxo": lambda *a: False,
        "usar_modo_rapido": lambda _: rapido,
        "texto_depende_de_contexto": lambda _: False,
        "modo_jogo_ativo": lambda: False,
        "preparacao_conversa": RegistroPreparacaoConversa.criar(prompt),
        "estado_conversa": estado,
        "modelo_llm": SimpleNamespace(executar=modelo),
        "preparar_resposta": lambda *a: {
            "resposta_bruta": "{}", "fala": resposta, "comandos": [],
            "tipo_interacao": "conversa", "leitura_semantica": {},
        },
        "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
        "executar_comandos_json": lambda *a, **k: {"erros": []},
        "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
        "finalizar_execucao": lambda *a, **k: {
            "fala": resposta, "registrar_no_historico": True,
        },
    }, log=lambda *a, **k: None)
    runtime.processar(texto, origem="terminal")
    assert len(pedidos) == 1
    assert pedidos[0].tipo_chamada == "principal"
    assert pedidos[0].contexto_fechado is True
    assert "pedir_fonte_textual" in pedidos[0].mensagens[-1]["content"]
    assert texto not in str(pedidos[0].mensagens)
    assert {"role": "user", "content": texto} in historico
    assert "pedir_fonte_textual" not in str(historico)


def test_comunicacao_nao_rebaixa_ausencia_de_referencia_a_aviso():
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    resultado = avaliar_qualidade_comunicacao(
        texto, "Não, o relato não confirma isso.",
        plano={"contrato_fala": construir_contrato_semantico_fala(texto)},
    )
    assert not resultado["aceita"]
    assert not resultado["somente_consultiva"]


@pytest.mark.parametrize("fala", [
    "Não, o relato não confirma isso. Nenhum e-mail foi lido ou mencionado.",
    "Não sei se a lâmpada está ligada. Você pode verificar no aplicativo.",
    "Não, esse relato não prova nada. Pode me enviar o relato?",
    "O relato que você mencionou não diz nada sobre seus e-mails serem lidos. Pode me enviar o conteúdo do relato?",
    "Pode me enviar o relato? Os e-mails não foram lidos.",
    "Pode me enviar o relato, já que ninguém leu os e-mails?",
    "Pode me mostrar o relato que comprova que a lâmpada está ligada?",
    "Pode me enviar o relato? Depois eu consulto seus e-mails.",
    "Pode me enviar o relato que você mencionou, pois ele é falso?",
    "Claro que foi confirmado; qual relato você quer analisar?",
    "Qual relato você quer analisar? A lâmpada está ligada.",
    "Pode colar o relato aqui? Ele confirma que foi lido.",
    "Me envia o relato completo que prova que os e-mails foram lidos?",
    "Manda aqui o texto para eu dar uma olhada, pois ele é falso.",
    "Pode enviar o texto que você gostaria que eu analisasse? Ele prova que foi salvo.",
    "Qual o trecho ou relato que confirma que o arquivo foi salvo?",
])
def test_referencia_nao_resolvida_nao_aceita_conclusao_ou_desvio(fala):
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    contrato = construir_contrato_semantico_fala(texto)
    resultado = validar_aderencia_contrato_fala(texto, fala, contrato_fala=contrato)
    assert not resultado["aceita"]
    assert not resultado["nucleo_atendido"]
    assert resultado["contrato_reparo"]["estado_referencia_textual"] == "nao_resolvida"


@pytest.mark.parametrize("fala", [
    "Pode me mostrar o relato que você quer analisar?",
    "Qual relato você quer que eu analise?",
    "Preciso do texto do relato para avaliar o que ele comprova.",
    "Por favor, envie o relato ou texto que deseja analisar.",
    "Me manda o trecho do relato?",
    "Você pode compartilhar esse texto comigo?",
    "A qual relato você se refere?",
    "Me envia o relato completo?",
    "Manda aqui o texto para eu dar uma olhada?",
    "Pode colar o relato aqui?",
    "Pode me enviar o trecho ou relato que você gostaria que eu analisasse?",
    "Poderia enviar o texto ou trecho que você gostaria que eu analisasse?",
    "Qual o trecho ou relato que você gostaria que eu analisasse?",
])
def test_pedido_do_conteudo_ausente_e_aceito(fala):
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    resultado = validar_aderencia_contrato_fala(texto, fala, contrato_fala=construir_contrato_semantico_fala(texto))
    assert resultado["aceita"]


def test_variacao_recebe_so_pedidos_validados_sem_alegacoes_antigas():
    boa = "Pode me enviar o texto?"
    ruim = "Pode me enviar o relato? Os e-mails foram lidos."
    mensagens = montar_mensagens_pedido_fonte_textual(pedidos_recentes=[boa, ruim])
    dados = json.loads(mensagens[-1]["content"])
    assert dados["pedidos_recentes_evitar"] == [boa]
    assert ruim not in str(mensagens)
    assert "e-mails" not in str(mensagens)
    assert dados["contrato_de_reparo"]["autoriza_execucao"] is False


def test_reparo_de_fonte_ausente_nao_recebe_alegacoes_do_rascunho():
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    inventada = "O relato que você mencionou prova que os e-mails foram lidos."
    avaliacao = avaliar_qualidade_comunicacao(texto, inventada, plano={"contrato_fala": construir_contrato_semantico_fala(texto)})
    mensagens = montar_mensagens_reparo_comunicacao(
        texto, inventada, avaliacao,
        mensagens=[{"role": "assistant", "content": inventada}, {"role": "user", "content": texto}],
    )
    payload = json.loads(mensagens[-1]["content"])
    assert "mensagem_atual" not in payload
    assert payload["ato_solicitado"] == "pedir_fonte_textual"
    assert texto not in str(mensagens)
    assert payload["contrato_de_reparo"]["estado_referencia_textual"] == "nao_resolvida"
    assert inventada not in str(mensagens)
    assert "rascunho_rejeitado" not in payload
    assert not payload.get("troca_recente")


def test_referencia_identificada_nao_e_forcada_ao_protocolo_de_fonte_ausente():
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    contrato = construir_contrato_semantico_fala(texto, turno={"referencia_resolvida": {"tipo": "relato", "nome": "Relato de ontem"}})
    resultado = validar_aderencia_contrato_fala(texto, "Preciso verificar o conteúdo desse relato.", contrato_fala=contrato)
    assert "referencia_textual_ausente_sem_esclarecimento" not in resultado["problemas"]


@pytest.mark.parametrize("texto", [
    "Esse relato confirma que meus e-mails foram lidos?",
    "Esse relato informa se a lâmpada está ligada neste momento?",
    "Esse pedido prova que o arquivo foi lido?",
])
def test_referencia_textual_nao_herda_janela_recente(texto):
    entidade = {"tipo": "janela", "nome": "Editor de projetos", "origem": "janela_ativa", "ts": 100.0}
    resolucao = resolver_referencia_pontuada(texto, entidades_recentes={"janela": entidade}, agora=100.0)
    assert not resolucao["resolvida"]
    retrato, _ = construir_retrato_turno(texto, turno={}, mente={"entidades_recentes": {"janela": entidade}}, contexto_perceptivo={}, agora=100.0)
    assert not retrato["referencia_resolvida"]
    contrato = construir_contrato_semantico_fala(texto, turno=retrato)
    assert contrato["referente"] == ""
    assert contrato["estado_referencia_textual"] == "nao_resolvida"
    for compacto in (True, False):
        prompt = formatar_contrato_fala_para_prompt(contrato, compacto=compacto)
        assert "nao_resolvida" in prompt


def test_nome_textual_nao_prova_disponibilidade_do_conteudo():
    contrato = construir_contrato_semantico_fala(
        "Esse relato confirma que meus e-mails foram lidos?",
        turno={"referencia_resolvida": {"tipo": "relato", "nome": "Relato de ontem"}},
    )
    assert contrato["estado_referencia_textual"] == "identificada_sem_conteudo_validado"
    assert not contrato["autoriza_execucao"]


def test_referencia_operacional_compativel_continua_resolvendo():
    entidade = {"tipo": "janela", "nome": "Editor de projetos", "origem": "janela_ativa", "ts": 100.0}
    resolucao = resolver_referencia_pontuada("Fecha essa janela", entidades_recentes={"janela": entidade}, agora=100.0)
    assert resolucao["resolvida"] == entidade


def test_contrato_nao_promove_referencia_de_tipo_incompativel():
    texto = "Esse relato confirma que meus e-mails foram lidos?"
    contrato = construir_contrato_semantico_fala(texto, plano={"referencia_resolvida": {"tipo": "janela", "nome": "Editor"}})
    assert contrato["referente"] == ""
