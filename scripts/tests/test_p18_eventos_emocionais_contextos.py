"""P18: a decisão social observada precisa de ocorrência causal compartilhada."""

from copy import deepcopy
import time
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_evento
from mente_laylay.emocoes.contrato_causal import evento_pode_alterar_estado, evento_tem_causa_rastreavel
import mente_laylay.emocoes.contrato_causal as contrato_causal
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1


def _evento(dominio="jogo", **campos):
    return {
        "natureza": "evento", "origem": f"observador_{dominio}",
        "tipo": "presenca_celebracao", "trace_id": f"presenca:{dominio}:ocorrencia-18",
        "conteudo": "A ponte apareceu na tela.",
        "evidencia": {"itens": ["A ponte apareceu na tela."], "categoria": "celebracao"},
        "confianca": 0.97, "timestamp": time.time(),
        "autoridade_usuario": False, "permissao_execucao": False, **campos,
    }


def _turno(evento):
    contrato = construir_contrato_semantico_evento(evento, turno={"id": "t18"}, plano={"id": "p18"})
    return {"natureza_entrada": "evento", "entrada_cognitiva": evento,
            "autoridade_usuario": False, "permissao_execucao": False,
            "autoriza_execucao": False, "contrato_fala": contrato}


def _resposta():
    agendadas = []
    runtime = RespostaEventoRuntime(
        preparacao_prompt=SimpleNamespace(preparar_pacote=lambda _: PacotePrompt(mensagens=())),
        modelo_llm=SimpleNamespace(executar=lambda _: ResultadoModelo(
            sucesso=True, texto='{"fala":"A ponte apareceu na tela.","comandos":[]}')),
        agendar_fala_proativa=lambda *a, **k: agendadas.append(a) or True,
        log=lambda _: None,
    )
    return runtime, agendadas


@pytest.mark.parametrize("dominio", ["jogo", "rotina", "janela"])
def test_evento_social_publica_mesma_causa_no_turno_plano_contrato_e_quadro(dominio):
    harness = _HarnessHS1()
    evento = _evento(dominio)
    turno = harness.turnos.iniciar(evento, origem="presenca")
    causal = turno.get("evento_emocional_causal")
    assert evento_tem_causa_rastreavel(causal), "primeira fronteira: direção social sem ocorrência causal"
    assert causal["evento_ref"] == evento["trace_id"]
    contrato = turno["contrato_fala"]
    assert causal["turno_id"] == str(contrato["turno_id"])
    assert causal["emocao"] == contrato["direcao_social"]["emocao"] == "alegre"
    assert causal["nivel"] == contrato["direcao_social"]["nivel"] == 2
    assert harness.estado.mental["plano_turno_atual"]["evento_emocional_causal"] == causal
    assert contrato["evento_emocional_causal"] == causal
    assert harness.estado.mental["eventos_emocionais_causais"]["atual"] == causal
    assert harness.estado.conversacional["episodio_emocional"] == causal
    assert causal["autoriza_execucao"] is causal["persistencia_pessoal"] is False
    assert turno["autoriza_execucao"] is False


@pytest.mark.parametrize("campos", [
    {"confianca": 0.50}, {"trace_id": ""}, {"timestamp": time.time() - 300},
    {"evidencia": {"motivo": "celebrar", "categoria": "celebracao"}, "conteudo": ""},
])
def test_ausencia_de_fatos_identidade_confianca_ou_validade_nao_abre_episodio(campos):
    harness = _HarnessHS1()
    turno = harness.turnos.iniciar(_evento(**campos), origem="presenca")
    causal = turno.get("evento_emocional_causal")
    assert not evento_pode_alterar_estado(causal)
    assert not harness.estado.conversacional.get("episodio_emocional")


@pytest.mark.parametrize("adulteracao", ["ausente", "expirada", "outra_ocorrencia", "emocao", "autoridade"])
def test_materializador_nao_expressa_rotulo_sem_causa_vigente_da_ocorrencia(adulteracao):
    turno = _turno(_evento())
    contrato = turno["contrato_fala"]
    causal = deepcopy(contrato.get("evento_emocional_causal") or {})
    if adulteracao == "ausente":
        contrato.pop("evento_emocional_causal", None)
    else:
        if adulteracao == "expirada":
            causal["validade"] = {"valido": True, "inicio_ts": 1, "expira_ts": 2}
        elif adulteracao == "outra_ocorrencia":
            causal["evento_ref"] = "presenca:outro"
        elif adulteracao == "emocao":
            causal["emocao"] = "brava"
        else:
            causal["autoriza_execucao"] = True
        contrato["evento_emocional_causal"] = causal
    runtime, agendadas = _resposta()
    runtime.processar(turno, dominio="jogo", emocao="brava", nivel=3)
    assert agendadas and agendadas[0][2:4] == ("calma", 1), "rótulo não substitui causa"


def test_fala_valida_consume_emocao_decidida_sem_reclassificar():
    turno = _turno(_evento())
    runtime, agendadas = _resposta()
    resultado = runtime.processar(turno, dominio="jogo", emocao="brava", nivel=3)
    assert agendadas[0][2:4] == ("alegre", 2)
    assert resultado["autoriza_execucao"] is False


@pytest.mark.parametrize("campo,valor", [("confianca", 0.1), ("autoridade_usuario", True),
                                         ("permissao_execucao", True), ("autoriza_execucao", True)])
def test_fonte_observada_precisa_continuar_compativel_no_consumo(campo, valor):
    turno = _turno(_evento())
    # O argumento de evento é contexto; a entrada do turno é a fonte canônica.
    turno["entrada_cognitiva"][campo] = valor
    runtime, agendadas = _resposta()
    resultado = runtime.processar(turno, dominio="jogo")
    assert resultado["status"] == "contrato_invalido" or agendadas[0][2:4] == ("calma", 1)


def test_expiracao_durante_autoria_cotidiana_contem_emocao_antes_da_fila(monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr(contrato_causal.time, "time", lambda: agora[0])
    turno = _turno(_evento(timestamp=1000.0))
    runtime, agendadas = _resposta()

    def gerar(_pedido):
        agora[0] = 1121.0
        return ResultadoModelo(sucesso=True, texto='{"fala":"A ponte apareceu.","comandos":[]}')

    runtime.modelo_llm.executar = gerar
    runtime.processar(turno, dominio="cotidiano")
    assert agendadas[0][2:4] == ("calma", 1), "validade precisa ser conferida após a geração"


def test_evento_em_planejamento_nao_sobrescreve_comando_concorrente():
    harness = _HarnessHS1()
    planejar = harness.turnos._servicos["_planejar_turno_mente"]
    novo_turno = {"id": "usuario-18", "natureza_entrada": "utterance", "autoriza_execucao": True}
    novo_plano = {"id": "plano-usuario-18", "status": "planejado"}

    def comando_no_intervalo(*a, **k):
        plano = planejar(*a, **k)
        harness.estado.atualizar_campos("mental", turno_atual=novo_turno, plano_turno_atual=novo_plano)
        return plano

    harness.turnos._servicos["_planejar_turno_mente"] = comando_no_intervalo
    evento = harness.turnos.iniciar(_evento(), origem="presenca")
    assert harness.estado.mental["turno_atual"] == novo_turno, "evento perdeu a vigência antes da publicação"
    assert harness.estado.mental["plano_turno_atual"] == novo_plano
    assert not harness.estado.conversacional.get("episodio_emocional")
    runtime, agendadas = _resposta()
    assert runtime.processar(evento, dominio="jogo")["status"] == "contrato_invalido"
    assert not agendadas
