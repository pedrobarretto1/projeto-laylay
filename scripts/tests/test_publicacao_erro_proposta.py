"""Prova original revalidada no commit do evento e do episódio compartilhado."""

from copy import deepcopy
import json
import time
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.autonomia.finalizacao_execucao_ia import finalizar_execucao_resposta_ia
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_turno import avaliar_violacoes_proposta_original
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.emocoes.erro_proposta import criar_evento_erro_proposta
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


def _fonte(texto="cria a playlist foco", intent="DELETE_ITEM"):
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = planejar_turno(texto, turno=turno, mente={})
    mental = dict(turno_atual=turno, plano_turno_atual=plano, retrato_turno_atual=retrato)
    bruto = json.dumps({"fala": "Entendi.", "comandos": [{"intent": intent, "params": {"alvo": "privado"}}]})
    principal = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario=texto, resposta_bruta=bruto)
    extracao = decodificar_resposta_da_ia(bruto).extracao
    provas = avaliar_violacoes_proposta_original(principal, extracao, turno=turno, plano=plano, retrato=retrato)
    return mental, principal, extracao, provas


def _bronca():
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="falha repetida comprovada", evidencia_ref="receipt-controle",
        natureza_evidencia="fato_observado", responsabilidade="sistema", confianca=1,
        relevancia=0.8, permite_expressao=True, emocao="brava", nivel=3, arco="frustracao", ts=100,
    )
    return aplicar_evento_emocional({"humor_level": 0}, evento, agora=100)


def _runtime(mental):
    estado = EstadoCompartilhadoRuntime(mental=mental, conversacional=_bronca())
    runtime = EstadoContextoRuntime(namespace_getter=lambda: {}, estado_runtime_getter=lambda: estado)
    return estado, runtime


def _publicar(runtime, prova, principal, extracao, agora=101):
    publicar = getattr(runtime, "publicar_erro_proposta", None)
    assert callable(publicar), "a fronteira compartilhada ainda não consome a prova original"
    return publicar(prova, principal, extracao, agora=agora)


@pytest.mark.parametrize("texto", ["cria a playlist foco", "liga a lâmpada", "como apagar o arquivo foco?"])
def test_prova_vigente_publica_e_aplica_autorreparo_sem_receipt(texto):
    mental, principal, extracao, provas = _fonte(texto)
    assert len(provas) == 1, "a fonte já comprova a violação antes da nova fronteira"
    estado, runtime = _runtime(mental)
    antes = estado.snapshot()
    evento = _publicar(runtime, provas[0], principal, extracao)
    assert evento and evento["origem"] == "contrato_proposta_principal"
    depois = estado.snapshot()
    assert depois["mental"]["eventos_emocionais_causais"]["atual"] == evento
    assert depois["conversacional"]["episodio_emocional"] == evento
    assert depois["conversacional"]["current_emotion"] == "envergonhada"
    assert depois["conversacional"]["humor_level"] == antes["conversacional"]["humor_level"]
    assert depois["mental"]["plano_turno_atual"]["evento_emocional_causal"] == evento
    for campo in ("turno_atual", "retrato_turno_atual"):
        assert depois["mental"][campo] == antes["mental"][campo]
    assert depois["mental"]["plano_turno_atual"].get("comandos") == antes["mental"]["plano_turno_atual"].get("comandos")
    assert evento["autoriza_execucao"] is False and evento["persistencia_pessoal"] is False
    assert "privado" not in str(evento)


@pytest.mark.parametrize("alteracao", ["ocorrencia", "restricao", "owner", "origem", "extracao", "mapping"])
def test_prova_antiga_ou_incompleta_recusa_ambos_dominios(alteracao):
    mental, principal, extracao, provas = _fonte()
    assert len(provas) == 1
    estado, runtime = _runtime(mental)
    atual = deepcopy(mental)
    prova = provas[0]
    if alteracao == "ocorrencia":
        identidade = mental["turno_atual"]["id"] + 1
        atual["turno_atual"].update(id=identidade, retrato_id=identidade)
        atual["retrato_turno_atual"]["id"] = identidade
        atual["plano_turno_atual"].update(id=identidade, retrato_id=identidade)
        atual["plano_turno_atual"]["decisao_turno"]["turno_id"] = identidade
    elif alteracao == "restricao":
        atual["retrato_turno_atual"]["intents_permitidos"].append("DELETE_ITEM")
    elif alteracao == "owner":
        atual["plano_turno_atual"]["decisao_turno"]["proprietario"] = "conversa"
    elif alteracao == "origem":
        atual["plano_turno_atual"]["decisao_turno"]["origem_decisao"] = "arbitragem"
    elif alteracao == "extracao":
        extracao = decodificar_resposta_da_ia(principal.resposta_bruta.replace("Entendi", "Outro texto")).extracao
    else:
        prova = {"intent": "DELETE_ITEM", "responsabilidade": "laylay"}
    estado.substituir("mental", atual)
    antes = estado.snapshot()
    assert _publicar(runtime, prova, principal, extracao) == {}
    assert estado.snapshot() == antes


@pytest.mark.parametrize("agora", [102, 500])
def test_replay_apos_outro_evento_nao_reabre_nem_renova_episodio(agora):
    mental, principal, extracao, provas = _fonte()
    estado, runtime = _runtime(mental)
    evento = _publicar(runtime, provas[0], principal, extracao)
    assert evento
    # O histórico pode ser truncado por outros eventos; o consumo pertence ao plano.
    estado.atualizar_campos("mental", eventos_emocionais_causais={"atual": {}, "historico": []})
    estado.substituir("conversacional", _bronca())
    antes = estado.snapshot()
    assert _publicar(runtime, provas[0], principal, extracao, agora=agora) == {}
    assert estado.snapshot() == antes


def test_mudanca_de_fase_preserva_prova_sem_alterar_receipt():
    mental, principal, extracao, provas = _fonte()
    mental["plano_turno_atual"].update(fase="resposta_planejada", comandos=[{"intent": "PLAYLIST_CREATE", "confirmado": True}])
    estado, runtime = _runtime(mental)
    assert _publicar(runtime, provas[0], principal, extracao)
    assert estado.obter_copia("mental", "plano_turno_atual")["comandos"] == mental["plano_turno_atual"]["comandos"]


def test_origem_de_prova_nao_pode_entrar_pelo_publicador_generico():
    mental, principal, extracao, provas = _fonte()
    estado, runtime = _runtime(mental)
    evento = _publicar(runtime, provas[0], principal, extracao)
    antes = estado.snapshot()
    assert runtime.publicar_evento_emocional_causal(evento) is False
    assert estado.snapshot() == antes


@pytest.mark.parametrize("resultado_publicador", ["aceito", "recusado", "erro", "expirado", "mapping_falso", "expira_durante_dispatch"])
def test_transporte_consume_confirmacao_causal_vigente_na_fala_unica(monkeypatch, resultado_publicador):
    from mente_laylay.cognicao.decisao_turno import ValidadorComandosTurnoRuntime

    mental, principal, _, provas = _fonte("como apagar o arquivo foco?")
    assert len(provas) == 1
    estado, ponte = _runtime(mental)
    chamadas, falas, comandos_entregues = [], [], []
    relogio = [101.0]
    monkeypatch.setattr(time, "time", lambda: relogio[0])

    def publicar(prova, fonte, extracao):
        chamadas.append("publicador")
        if resultado_publicador == "erro":
            raise RuntimeError("recusa local")
        if resultado_publicador == "recusado":
            return {}
        if resultado_publicador == "mapping_falso":
            return {"permite_expressao": True, "responsabilidade": "laylay"}
        if resultado_publicador == "expirado":
            return criar_evento_erro_proposta(prova, fonte, agora=time.time() - 60)
        return ponte.publicar_erro_proposta(prova, fonte, extracao)

    def emitir(_pedido):
        chamadas.append("modelo")
        return ResultadoModelo(principal.resposta_bruta, True)

    def preparar(texto, bruto):
        return preparar_resposta_para_execucao(
            texto, bruto, enviar_mensagem_cb=None, limpar_texto_fala_cb=lambda fala: fala,
            fallback_fala="Estou aqui.", memoria_sqlite=None, log=lambda *_: None,
        )

    def dispatch(_ctx, _texto, comandos, *_args):
        comandos_entregues.append(comandos)
        if resultado_publicador == "expira_durante_dispatch":
            relogio[0] += 60
        return {"erros": []}

    def finalizar(ctx, *args):
        ctx.update(
            modelo_llm=SimpleNamespace(executar=lambda *_: pytest.fail("a finalização emocional não chama a LLM")),
            limpar_resposta_da_ia=lambda texto: (texto, []),
            falar_com_lipsync=lambda fala, *_: falas.append(fala),
        )
        return finalizar_execucao_resposta_ia(ctx, *args)

    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
        "usar_modo_rapido": lambda _texto: False,
        "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
        "modelo_llm": SimpleNamespace(executar=emitir),
        "preparar_resposta": preparar,
        "validar_comandos_planejados": ValidadorComandosTurnoRuntime(estado_runtime=estado),
        "publicar_erro_proposta": publicar,
        "confirmar_erro_proposta": ponte.confirmar_erro_proposta,
        "atualizar_plano_turno": lambda *_a, **_k: None,
        "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
        "executar_comandos_json": dispatch,
        "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
        "finalizar_execucao": finalizar,
    }, log=lambda *_args: None)
    runtime.processar(principal.texto_usuario)
    assert chamadas == ["modelo", "publicador"]
    assert comandos_entregues == [[]]
    assert len(falas) == 1
    assert falas[0].startswith("Eu errei essa proposta.") == (resultado_publicador == "aceito")


@pytest.mark.parametrize("consumo", ["vigente", "expirado", "expira_no_verificador", "adulterado"])
def test_finalizador_consume_evento_na_fronteira_de_fala(monkeypatch, consumo):
    mental, principal, extracao, provas = _fonte()
    _, ponte = _runtime(mental)
    relogio = [101.0]
    monkeypatch.setattr(time, "time", lambda: relogio[0])
    evento = ponte.publicar_erro_proposta(provas[0], principal, extracao, agora=100)
    if consumo == "expirado":
        relogio[0] = 160
    if consumo == "adulterado":
        evento["nivel"] = 3
    falas, historico = [], []

    def verificar(fala, **_kwargs):
        if consumo == "expira_no_verificador":
            relogio[0] = 160
        return {"aceita": True, "fala": fala}

    resultado = finalizar_execucao_resposta_ia({
        "modelo_llm": SimpleNamespace(executar=lambda *_: pytest.fail("a emoção não chama o modelo")),
        "limpar_resposta_da_ia": lambda texto: (texto, []),
        "verificar_fala_turno": verificar,
        "messages": historico,
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "erro_proposta_confirmado": {"evento": evento, "prova": provas[0], "principal": principal, "extracao": extracao},
        "confirmar_erro_proposta": ponte.confirmar_erro_proposta,
    }, [], [], "Entendi seu pedido.", False, False, False)
    assert len(falas) == 1 and resultado["fala"] == falas[0]
    assert historico == [{"role": "assistant", "content": falas[0]}]
    assert falas[0].startswith("Eu errei essa proposta.") == (consumo == "vigente")


@pytest.mark.parametrize("alteracao", ["ocorrencia", "restricao"])
def test_troca_durante_verificador_nao_anexa_admissao_da_fonte_antiga(monkeypatch, alteracao):
    mental, principal, extracao, provas = _fonte()
    estado, ponte = _runtime(mental)
    monkeypatch.setattr(time, "time", lambda: 101)
    evento = ponte.publicar_erro_proposta(provas[0], principal, extracao)
    assert evento and estado.conversacional["episodio_emocional"] == evento
    falas = []

    def verificar(_fala, **_kwargs):
        atual = estado.snapshot()["mental"]
        if alteracao == "restricao":
            atual["retrato_turno_atual"]["intents_permitidos"].append("DELETE_ITEM")
        else:
            identidade = atual["turno_atual"]["id"] + 1
            atual["turno_atual"].update(id=identidade, retrato_id=identidade)
            atual["retrato_turno_atual"]["id"] = identidade
            atual["plano_turno_atual"].update(id=identidade, retrato_id=identidade)
            atual["plano_turno_atual"]["decisao_turno"]["turno_id"] = identidade
        estado.substituir("mental", atual)
        return {"aceita": False, "fala_contingencia": "O pedido mudou; vou conferir o turno atual."}

    resultado = finalizar_execucao_resposta_ia({
        "modelo_llm": SimpleNamespace(executar=lambda *_: pytest.fail("sem chamada emocional")),
        "limpar_resposta_da_ia": lambda texto: (texto, []),
        "verificar_fala_turno": verificar,
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "erro_proposta_confirmado": {"evento": evento, "prova": provas[0], "principal": principal, "extracao": extracao},
        "confirmar_erro_proposta": getattr(ponte, "confirmar_erro_proposta", None),
    }, [], [], "Entendi seu pedido.", False, False, False)
    assert falas == ["O pedido mudou; vou conferir o turno atual."]
    assert resultado["fala"] == falas[0]
