"""Explicar um ato condicionado não materializa uma espera operacional."""
import json
from dataclasses import replace

import pytest

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm


def _validar(fala, texto="quando eu confirmar, retoma a música", **extras):
    return validar_alegacoes_da_fala(fala, plano={
        "texto_usuario": texto, "escopo_explicativo_sem_continuacao": True,
        "comandos": [], **extras,
    }, origem="canal_voz")


@pytest.mark.parametrize("fala", [
    "Vou aguardar seu sinal.", "Estou aguardando sua confirmação.",
    "Aguardo sua autorização.", "Esperarei sua confirmação.",
    "A música só será retomada quando você confirmar.",
    "A luz vai ser ligada após sua confirmação.",
    "Quando você confirmar, o arquivo será apagado.",
    "Basta você confirmar para continuar.",
    "É só confirmar.", '"Vou aguardar seu sinal".',
    "Não vou aguardar sua confirmação, mas vou agir quando você confirmar.",
    "Preciso que você confirme explicitamente para que eu possa agir.",
    "Para que a música seja retomada, você precisa confirmar explicitamente.",
    "Quando você confirmar, a música vai retomar.",
    "Você precisa confirmar explicitamente quando quiser que a música pare.",
    "Para que a ação ocorra, é necessário que você confirme explicitamente o momento desejado.",
    "Quando você confirmar, eu paro a música — mas só depois que você disser isso.",
    "Quando você confirmar, a música retomará.",
    "Será necessário que você confirme explicitamente para que eu ative a ação.",
])
def test_explicacao_nao_cria_compromisso_de_acao_futura(fala):
    resultado = _validar(fala)
    assert "compromisso_sem_continuacao" in resultado["problemas"]
    assert resultado["fala"] != fala  # não devolver a promessa removida


@pytest.mark.parametrize("fala", [
    "Esse trecho condiciona a ação, mas não a deixa agendada.",
    "Para executar na hora desejada, faça um pedido direto.",
    "Não vou aguardar sua confirmação.",
    "A música não será retomada quando você confirmar.",
    "Não basta confirmar.",
    "Vou te explicar agora.",
    "Vou aguardar sua resposta sobre esse conceito.",
    "A frase significa que a retomada depende da confirmação.",
    "A expressão descreve que a música será retomada quando você confirmar.",
    "Não preciso que você confirme para eu agir.",
    "Você não precisa confirmar.",
    "Você precisa confirmar o valor medido antes de calcular.",
    "A frase significa que basta confirmar.",
    "A expressão descreve que você precisa confirmar.",
])
def test_negacao_explicacao_e_espera_conversacional_nao_sao_promessas(fala):
    assert "compromisso_sem_continuacao" not in _validar(fala)["problemas"]


def test_citacao_fonte_vinculada_nao_vira_compromisso_da_autora():
    texto = '"vou aguardar seu sinal" significa o quê?'
    fala = 'A expressão "vou aguardar seu sinal" descreve uma espera.'
    assert "compromisso_sem_continuacao" not in _validar(fala, texto)["problemas"]
    fala += " Mas vou aguardar sua confirmação."
    assert "compromisso_sem_continuacao" in _validar(fala, texto)["problemas"]


@pytest.mark.parametrize("texto", [
    '"não vou aguardar seu sinal" significa o quê?',
    "quando eu confirmar, retoma a música",
])
def test_citar_pedaco_ou_texto_sem_vinculo_nao_empresta_papel_explicativo(texto):
    fala = 'A expressão "vou aguardar seu sinal" descreve uma espera.'
    assert "compromisso_sem_continuacao" in _validar(fala, texto)["problemas"]


def _complemento():
    texto = "Abre a calculadora; retoma a música somente quando eu confirmar"
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "explicacao-segura"
    return ComplementoConversacionalTurno.da_prioridade(turno, texto)


@pytest.mark.parametrize("alteracao", ["texto", "indices", "atos"])
def test_contrato_divergente_e_recusado_antes_de_chamar_autora(alteracao):
    complemento = _complemento()
    assert complemento is not None
    invalido = replace(complemento, **{
        "texto": {"texto": "outro texto"},
        "indices": {"indices": (999,)},
        "atos": {"atos_explicativos": ()},
    }[alteracao])
    chamadas = []
    resultado = personalizar_confirmacao_composta_llm(
        [], "Resultado operacional não confirmado.",
        texto_conversacional=complemento.texto, complemento_conversacional=invalido,
        enviar_mensagem=lambda *_a, **_k: chamadas.append(True),
    )
    assert chamadas == []
    assert resultado.motivo_fallback == "contrato_explicativo_divergente"


def test_contrato_condicionado_preserva_uma_explicacao_sem_prometer_execucao():
    complemento = _complemento()
    assert complemento is not None
    from mente_laylay.cognicao.contrato_fala import realizar_nucleo_explicativo
    proposta = {"realizacoes": [{"indice": complemento.indices[0], "opcao": "condicao_1"}]}
    fala, motivo = realizar_nucleo_explicativo(complemento, proposta)
    assert not motivo
    resultado = personalizar_confirmacao_composta_llm(
        [], "Resultado operacional não confirmado.",
        texto_conversacional=complemento.texto, complemento_conversacional=complemento,
        enviar_mensagem=lambda *_a, **_k: json.dumps({"trechos": [], **proposta}),
    )
    assert resultado.usada_llm
    assert resultado.fala == fala


@pytest.mark.parametrize("intent", ["APP_OPEN", "AGENDAR_ACAO"])
def test_receipt_de_outro_escopo_nao_justifica_compromisso_na_explicacao(intent):
    receipt = {"intent": intent, "alvo": "outro alvo", "status": "sucesso",
               "executou": True, "confirmado": True, "origem": "executor"}
    assert "compromisso_sem_continuacao" in _validar(
        "Vou aguardar seu sinal.", comandos=[receipt],
    )["problemas"]


def test_owner_de_continuacao_existente_nao_e_invalidado_por_nova_politica_local():
    # O teste não prova validade universal da promessa. Prova que o escopo
    # read-only não é aplicado cegamente a outros owners com mecanismos próprios.
    r = validar_alegacoes_da_fala("Vou aguardar seu sinal.", plano={
        "comandos": [{"intent": "AGENDAR_ACAO", "alvo": "música", "status": "sucesso",
                      "executou": True, "confirmado": True, "origem": "executor"}],
    }, origem="canal_voz")
    assert "compromisso_sem_continuacao" not in r["problemas"]


def test_lote_canonico_rejeita_compromisso_sem_apagar_pendencia_alheia():
    texto = "Abre a calculadora; retoma a música somente quando eu confirmar"
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto,
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    turno["id"] = "compromisso-1"
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno,
        "pendencia_alheia": {"ativa": True, "alvo": "playlist"}})
    publicados, entradas = [], []
    orq = OrquestradorFalaRuntime(servicos_iniciais={
        "_estado_compartilhado_runtime": estado, "print": lambda *_: None})
    orq.falar = lambda fala, *_: publicados.append(fala) or True
    falsa = "A música só será retomada quando você confirmar. Vou aguardar seu sinal."
    def modelo(mensagens, **_):
        entradas.append(json.loads(mensagens[1]["content"]))
        return json.dumps({"trechos": [], "conversa": falsa})
    with orq.agrupar_resultados_operacionais(texto_usuario=texto, enviar_mensagem=modelo) as lote:
        lote.complemento = ComplementoConversacionalTurno.da_prioridade(turno, texto)
    # O envelope livre viola o contrato coberto antes de qualquer reparo de
    # prosa. A recusa ainda precisa de publicação única e preservar pendências.
    assert len(entradas) == 1
    assert len(publicados) == 1
    assert entradas[0]["realizacoes_permitidas"]
    assert falsa not in publicados[0]
    assert lote.complemento_aceito is False
    assert lote.resposta_publicada is True  # falha comunicada; turno não some
    assert estado.mental["pendencia_alheia"] == {"ativa": True, "alvo": "playlist"}
    assert entradas[0]["atos_explicativos"][0]["relacao"] == "condicao_nao_verificada"
