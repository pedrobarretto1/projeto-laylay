"""P1-E RED — aceite da fila não é prova de entrega da fala de presença."""

from __future__ import annotations

from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo


def _turno_evento(evento: dict[str, Any]) -> dict[str, Any]:
    contrato = {
        "funcao": "reacao_evento",
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoriza_execucao": False,
        "roteiro_concreto": {
            "estrategia": "reacao_evento",
            "autoriza_execucao": False,
        },
    }
    return {
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
        "contrato_fala": contrato,
    }


def _runtime_cognitivo() -> tuple[
    DiretorPresencaRuntime,
    dict[str, Any],
    list[Any],
    list[tuple[bool, str]],
    list[float],
]:
    estado: dict[str, Any] = {}
    conclusoes: list[Any] = []
    callback_fonte: list[tuple[bool, str]] = []
    agora = [1000.0]

    def materializar(turno: dict[str, Any], **contexto: Any) -> dict[str, Any]:
        assert turno["autoriza_execucao"] is False
        contexto["ao_materializar_fala"]("Essa tentativa cobrou caro, hein?")
        conclusoes.append(contexto["ao_concluir"])
        return {
            "status": "agendada",
            "fala": "Essa tentativa cobrou caro, hein?",
            "agendada": True,
            "emissao_fisica": False,
            "autoriza_execucao": False,
            "comandos_descartados": 0,
        }

    runtime = DiretorPresencaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {
            "modo_jogo_ativo": True,
            "turno_ativo": False,
            "is_speaking": False,
            "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=lambda evento: _turno_evento(dict(evento)),
        processar_proposta_comunicativa=materializar,
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )
    resultado = runtime.considerar({
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "confianca": 0.96,
        "momento_seguro": True,
        "motivo": "o jogador morreu depois de errar o salto",
        "evidencias": ["morte do jogador", "salto tentado"],
        "chave": "morte-salto-recibo",
        "ao_concluir": lambda entregue, motivo: callback_fonte.append(
            (bool(entregue), str(motivo))
        ),
    })
    assert resultado["status"] == "proposta_cognitiva"
    assert resultado["proposta_comunicativa"]["agendada"] is True
    return runtime, estado, conclusoes, callback_fonte, agora


def test_red_p1e_fila_aceita_nao_cria_emissao_antes_do_callback_final() -> None:
    runtime, estado, conclusoes, callback_fonte, _agora = _runtime_cognitivo()

    assert len(conclusoes) == 1
    assert estado["contadores"]["emitidas"] == 0
    assert estado["ultima_emissao"] == {}
    assert runtime.observar_resposta("boa, gostei dessa") == {}
    assert callback_fonte == []


def test_red_p1e_entrega_confirmada_cria_alvo_real_para_feedback_uma_vez() -> None:
    runtime, estado, conclusoes, callback_fonte, agora = _runtime_cognitivo()
    agora[0] = 1025.0

    conclusoes[0](True, "entregue")

    assert estado["contadores"]["emitidas"] == 1
    assert estado["ultima_emissao"]["fala"] == "Essa tentativa cobrou caro, hein?"
    assert estado["ultima_emissao"]["categoria"] == "celebracao"
    assert estado["ultima_emissao"]["ts"] == 1025.0
    assert estado["ultima_emissao"]["feedback_registrado"] is False
    assert estado["ultima_proposta_cognitiva"]["resultado_entrega"] == {
        "entregue": True,
        "motivo": "entregue",
        "ts": 1025.0,
    }
    assert callback_fonte == [(True, "entregue")]

    assert runtime.observar_resposta("boa, gostei dessa") == {
        "resultado": "aceita",
        "categoria": "celebracao",
    }
    conclusoes[0](True, "entregue")
    assert estado["contadores"]["emitidas"] == 1
    assert callback_fonte == [(True, "entregue")]


def test_red_p1e_falha_de_entrega_nao_vira_emissao_nem_alvo_de_feedback() -> None:
    runtime, estado, conclusoes, callback_fonte, agora = _runtime_cognitivo()
    agora[0] = 1030.0

    conclusoes[0](False, "falha_entrega")

    assert estado["contadores"]["emitidas"] == 0
    assert estado["ultima_emissao"] == {}
    assert estado["ultima_proposta_cognitiva"]["resultado_entrega"] == {
        "entregue": False,
        "motivo": "falha_entrega",
        "ts": 1030.0,
    }
    assert runtime.observar_resposta("boa, gostei dessa") == {}
    assert callback_fonte == [(False, "falha_entrega")]


class _PromptEvento:
    def preparar_pacote(self, texto: str) -> PacotePrompt:
        assert texto == ""
        return PacotePrompt(mensagens=(
            {"role": "system", "content": "Personalidade canônica."},
        ))


class _ModeloEvento:
    def executar(self, _pedido: Any) -> ResultadoModelo:
        return ResultadoModelo(
            texto='{"fala":"Essa tentativa cobrou caro, hein?","comandos":[]}',
            sucesso=True,
            rota="teste",
        )


def test_red_p1e_porteiro_sincrono_fecha_recibo_sem_corrida_de_estado() -> None:
    estado: dict[str, Any] = {}
    callback_fonte: list[tuple[bool, str]] = []

    def rejeitar_no_porteiro(
        _tipo: str,
        _fala: str,
        _emocao: str,
        _nivel: int,
        **opcoes: Any,
    ) -> bool:
        opcoes["ao_concluir"](False, "politica_descartou")
        return False

    resposta = RespostaEventoRuntime(
        preparacao_prompt=_PromptEvento(),
        modelo_llm=_ModeloEvento(),
        agendar_fala_proativa=rejeitar_no_porteiro,
        limpar_texto_fala=lambda texto: texto,
        log=lambda _texto: None,
    )
    runtime = DiretorPresencaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {
            "modo_jogo_ativo": True,
            "turno_ativo": False,
            "is_speaking": False,
            "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=lambda evento: _turno_evento(dict(evento)),
        processar_proposta_comunicativa=resposta.processar,
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "confianca": 0.96,
        "momento_seguro": True,
        "motivo": "o jogador morreu depois de errar o salto",
        "evidencias": ["morte do jogador", "salto tentado"],
        "chave": "morte-salto-rejeicao-sincrona",
        "ao_concluir": lambda entregue, motivo: callback_fonte.append(
            (bool(entregue), str(motivo))
        ),
    })

    assert resultado["proposta_comunicativa"]["status"] == "bloqueada_porteiro"
    assert estado["ultima_proposta_cognitiva"]["resultado_entrega"] == {
        "entregue": False,
        "motivo": "politica_descartou",
        "ts": 1000.0,
    }
    assert estado["contadores"]["emitidas"] == 0
    assert estado["ultima_emissao"] == {}
    assert callback_fonte == [(False, "politica_descartou")]
