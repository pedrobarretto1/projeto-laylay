"""Admissão da interpretação auxiliar preserva a decisão e o prazo principal.

Sem Qwen, rede, executores, persistência pessoal ou voz. O relógio controlado
mede a consequência da admissão; não estima desempenho do modelo real.
"""
from copy import deepcopy

import pytest

from mente_laylay.autonomia.porteiro_acoes import (
    texto_social_curto, texto_tem_comando_explicito,
)
from mente_laylay.autonomia.pre_fluxo_contextual import texto_deve_evitar_llm_de_comando
from mente_laylay.cognicao.interpretacao_intencao import InterpretacaoIntencaoRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.integracao.orcamento_llm_turno import OrcamentoLLMTurnoRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


PERGUNTAS = [
    "voltando à conversa, quem vai levar o livro azul?",
    "qual é mesmo o nome do jogo que eu e o Leo estamos montando?",
    "qual era o nome da pessoa?",
    "voltando ao assunto, onde combinamos de nos encontrar?",
]


class Relogio:
    agora = 100.0

    def __call__(self):
        return self.agora


def _compor(texto, *, resultado='{"intent":"NONE","params":{}}', custo=11.198):
    turno = classificar_modalidade_turno(
        texto, normalizar_texto=normalizar_texto,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    turno.update(id="turno-contextual", texto=texto)
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno})
    estado_contexto = EstadoContextoRuntime(
        estado_runtime_getter=lambda: estado,
        namespace_getter=lambda: {
            "_texto_tem_comando_explicito": texto_tem_comando_explicito,
            "_texto_expresso_melhor_no_deterministico": lambda _t: False,
        },
    )
    mapa = MapaHabilidadesRuntime()
    relogio = Relogio()
    orcamento = OrcamentoLLMTurnoRuntime(monotonic=relogio)
    orcamento.iniciar_turno("turno-contextual")
    chamadas = []

    def enviar(mensagens, **opcoes):
        decisao = orcamento.autorizar_chamada(
            tipo_chamada=opcoes.get("_tipo_chamada", "principal"),
        )
        assert decisao.permitida
        chamadas.append({"opcoes": opcoes, "mensagens": deepcopy(mensagens),
                         "timeout_s": decisao.timeout_s})
        relogio.agora += custo
        orcamento.concluir_chamada(decisao, sucesso=True)
        return resultado

    contexto = {
        "estado": {"mente_integrada_estado": estado.retrato_dominio("mental")},
        "normalizar_texto": normalizar_texto,
        "texto_social_curto": texto_social_curto,
        "texto_conversa_casual_sem_acao": estado_contexto.texto_conversa_casual_sem_acao,
        "texto_conversa_contextual_sem_comando": estado_contexto.texto_conversa_contextual_sem_comando,
        "texto_tem_comando_explicito": texto_tem_comando_explicito,
        "texto_parece_consulta_operacional": mapa.parece_consulta_operacional,
        "contexto_mental_ativo": lambda: True,
        "enviar_mensagem": enviar,
    }
    runtime = InterpretacaoIntencaoRuntime(contexto_getter=lambda: contexto, log=lambda *_a: None)
    return runtime, turno, chamadas, orcamento, estado


@pytest.mark.parametrize("texto", PERGUNTAS)
def test_conversa_canonica_nao_admite_interpretacao_operacional_auxiliar(texto):
    runtime, turno, chamadas, orcamento, estado = _compor(texto)
    antes = estado.snapshot()
    assert turno["autoriza_execucao"] is False
    assert runtime.tentar_ai_primeiro(texto) is None
    assert chamadas == [], "primeira RED: decisão sem ação perdida na admissão auxiliar"
    assert estado.snapshot() == antes
    principal = orcamento.autorizar_chamada(tipo_chamada="principal")
    assert principal.permitida
    assert principal.timeout_s == 20.0, "auxiliar dispensável consumiu o prazo da autoria"


def test_porteiro_reconhece_misto_de_conversa_e_pergunta_sem_ato_operacional():
    texto = PERGUNTAS[0]
    _, turno, _, _, _ = _compor(texto)
    assert turno["modalidade_geral"] == "misto"
    assert not any(s.get("autoriza_execucao") for s in turno["segmentos"])
    assert texto_deve_evitar_llm_de_comando({"mente_integrada_estado": {"turno_atual": turno}}, texto)


@pytest.mark.parametrize("texto,intent,params", [
    ("pode colocar ele para mim ouvir", "MEDIA_CONTROL", {"acao": "play"}),
    ("abre esse aplicativo", "APP_OPEN", {"nome_app": "Calculadora"}),
    ("cria o arquivo notas.txt", "CREATE_FILE", {"alvo": "notas.txt"}),
    ("gosto de rock; pode colocar ele para mim ouvir", "MEDIA_CONTROL", {"acao": "play"}),
])
def test_ato_operacional_autorizado_preserva_interpretacao_auxiliar(texto, intent, params):
    import json
    runtime, turno, chamadas, _, _ = _compor(texto, resultado=json.dumps({"intent": intent, "params": params}))
    assert turno["autoriza_execucao"] is True
    leitura = runtime.tentar_ai_primeiro(texto)
    assert chamadas, "ação contextual legítima perdeu a interpretação"
    assert leitura and leitura["intent"] == intent


@pytest.mark.parametrize("modalidade", ["conversa", "pergunta", "deliberacao", "correcao", "reacao"])
def test_porteiro_existente_ja_veta_modalidade_sem_autoridade_quando_recebe_decisao(modalidade):
    turno = {"id": "atual", "modalidade": modalidade, "autoriza_execucao": False}
    assert texto_deve_evitar_llm_de_comando({"mente_integrada_estado": {"turno_atual": turno}}, "mesma fala")


def test_orcamento_existente_desconta_custo_auxiliar_sem_precisar_de_falha_ou_concorrencia():
    relogio = Relogio()
    orcamento = OrcamentoLLMTurnoRuntime(monotonic=relogio)
    orcamento.iniciar_turno("controle-serial")
    auxiliar = orcamento.autorizar_chamada(tipo_chamada="interpretacao")
    assert auxiliar.permitida and auxiliar.timeout_s == 20.0
    relogio.agora += 11.198
    orcamento.concluir_chamada(auxiliar, sucesso=True)
    principal = orcamento.autorizar_chamada(tipo_chamada="principal")
    assert principal.permitida and principal.timeout_s == 8.802
    assert orcamento.diagnostico()["circuito_aberto"] is False


def test_sem_decisao_canonica_interpretacao_de_pedido_eliptico_continua_disponivel():
    texto = "salva isso no arquivo"
    runtime, _, chamadas, _, _ = _compor(texto)
    contexto = runtime._contexto()
    contexto["estado"]["mente_integrada_estado"].clear()
    runtime.tentar_ai_primeiro(texto)
    assert chamadas, "ausência de decisão não equivale a veto canônico"


def test_decisao_de_outra_fala_nao_veta_interpretacao_do_pedido_atual():
    texto = "pode colocar ele para mim ouvir"
    runtime, _, chamadas, _, _ = _compor(texto)
    contexto = runtime._contexto()
    contexto["estado"]["mente_integrada_estado"]["turno_atual"] = {
        "id": "anterior", "texto": "qual era o nome da pessoa?",
        "modalidade": "pergunta", "autoriza_execucao": False,
    }
    runtime.tentar_ai_primeiro(texto)
    assert chamadas, "decisão de outra fala tornou-se veto do pedido atual"


@pytest.mark.parametrize("segmentos", [[], [{"modalidade": "conversa"}],
    [{"modalidade": "pergunta", "autoriza_execucao": False}, {"modalidade": "comando"}]])
def test_misto_sem_classificacao_completa_dos_atos_nao_inventa_veto(segmentos):
    turno = {"modalidade_geral": "misto", "autoriza_execucao": False, "segmentos": segmentos}
    assert not texto_deve_evitar_llm_de_comando(
        {"mente_integrada_estado": {"turno_atual": turno}}, "entrada ambígua",
    )


def test_esclarecimento_canonico_nao_tenta_resolver_ambiguidade_com_segunda_ia():
    turno = {"modalidade": "comando", "autoriza_execucao": False,
             "requer_esclarecimento": True}
    assert texto_deve_evitar_llm_de_comando(
        {"mente_integrada_estado": {"turno_atual": turno}}, "abre aquele",
    )
