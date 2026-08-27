"""P2-A RED — sombra observa; só autorização de jogo abre proposta de fala."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mente_laylay.autonomia.coordenador_oportunidades import (
    CoordenadorOportunidadesRuntime,
)
from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.motor_iniciativa import MotorIniciativaRuntime
from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    PonteIniciativaAplicacaoRuntime,
)
from mente_laylay.percepcao.ouvido_whisper import OuvidoWhisperRuntime


class _PromptEvento:
    def preparar_pacote(self, texto: str) -> PacotePrompt:
        assert texto == ""
        return PacotePrompt(mensagens=(
            {"role": "system", "content": "Personalidade canônica da Laylay."},
        ))


class _ModeloEvento:
    def __init__(self) -> None:
        self.chamadas = 0

    def executar(self, _pedido: Any) -> ResultadoModelo:
        self.chamadas += 1
        return ResultadoModelo(
            texto='{"fala":"Essa foi por pouco, hein?","comandos":[]}',
            sucesso=True,
            rota="teste_p2",
        )


def _turno_evento(evento: dict[str, Any]) -> dict[str, Any]:
    contrato = {
        "funcao": "reacao_evento",
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
    }
    return {
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
        "contrato_fala": contrato,
    }


def _evento_jogo(chave: str) -> dict[str, Any]:
    return {
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "confianca": 0.98,
        "momento_seguro": True,
        "motivo": "Pedro venceu a luta com pouca vida restante",
        "evidencias": ["vitória confirmada", "vida crítica visível"],
        "chave": chave,
        "validade_s": 8.0,
    }


def _pilha_p2(*, contexto_extra: dict[str, Any] | None = None) -> tuple[
    DiretorPresencaRuntime,
    MotorIniciativaRuntime,
    dict[str, Any],
    _ModeloEvento,
    list[tuple[Any, ...]],
]:
    agora = [1_000.0]
    estado_motor: dict[str, Any] = {}
    estado_coordenador: dict[str, Any] = {}
    estado_diretor: dict[str, Any] = {}
    agendamentos: list[tuple[Any, ...]] = []
    contexto = {
        "modo_jogo_ativo": True,
        "turno_ativo": False,
        "is_speaking": False,
        "usuario_falando": False,
        "ultima_entrada_ts": 0.0,
    }
    contexto.update(contexto_extra or {})

    motor = MotorIniciativaRuntime(
        estado_get=lambda: estado_motor,
        estado_set=lambda novo: estado_motor.clear() or estado_motor.update(novo),
        contexto_getter=lambda: contexto,
        modo="sombra",
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )
    coordenador = CoordenadorOportunidadesRuntime(
        encaminhar=motor.registrar,
        estado_get=lambda: estado_coordenador,
        estado_set=(
            lambda novo: estado_coordenador.clear()
            or estado_coordenador.update(novo)
        ),
        contexto_getter=lambda: contexto,
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )

    modelo = _ModeloEvento()
    resposta = RespostaEventoRuntime(
        preparacao_prompt=_PromptEvento(),
        modelo_llm=modelo,
        agendar_fala_proativa=lambda *args, **kwargs: (
            agendamentos.append((*args, kwargs)) or True
        ),
        limpar_texto_fala=lambda texto: texto,
        log=lambda _texto: None,
    )

    diretor = DiretorPresencaRuntime(
        estado_get=lambda: estado_diretor,
        estado_set=lambda novo: estado_diretor.clear() or estado_diretor.update(novo),
        contexto_getter=lambda: contexto,
        registrar_oportunidade=coordenador.registrar,
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=resposta.processar,
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )
    return diretor, motor, estado_motor, modelo, agendamentos


def test_red_p2_sombra_materializa_candidata_sem_agendar_fala_autonoma() -> None:
    diretor, _motor, estado_motor, modelo, agendamentos = _pilha_p2()

    resultado = diretor.considerar(_evento_jogo("vitoria-sombra"))

    assert str(estado_motor["ultima_decisao"]["decisao"]).startswith("sombra_")
    assert modelo.chamadas == 1
    assert resultado["status"] == "proposta_cognitiva"
    assert resultado["proposta_comunicativa"] == {
        "status": "suprimida_sombra",
        "fala": "Essa foi por pouco, hein?",
        "agendada": False,
        "emissao_fisica": False,
        "autoriza_execucao": False,
        "comandos_descartados": 0,
    }
    assert agendamentos == []


def test_red_p2_sugestao_explicita_de_jogo_abre_somente_proposta_sem_execucao() -> None:
    diretor, motor, estado_motor, modelo, agendamentos = _pilha_p2()
    liberacao = motor.configurar_dominio(
        "jogo",
        "sugestao",
        confirmacao_explicita=True,
        origem="laboratorio_p2",
    )

    resultado = diretor.considerar(_evento_jogo("vitoria-p2-autorizada"))

    assert liberacao == {
        "ok": True,
        "dominio": "jogo",
        "permissao": "sugestao",
        "modo": "sugestao",
    }
    assert estado_motor["ultima_decisao"]["decisao"] == "sugerir"
    assert resultado["status"] == "proposta_cognitiva"
    assert resultado["emissao_fisica"] is False
    assert resultado["contrato_fala"]["autoriza_execucao"] is False
    assert resultado["proposta_comunicativa"]["autoriza_execucao"] is False
    assert modelo.chamadas == 1
    assert len(agendamentos) == 1
    tipo, fala, emocao, nivel, opcoes = agendamentos[0]
    assert (tipo, fala, emocao, nivel) == (
        "presenca_jogo",
        "Essa foi por pouco, hein?",
        "animada",
        1,
    )
    assert callable(opcoes["ao_concluir"])


def test_red_p2_evento_vencido_morre_antes_da_cognicao_e_do_llm() -> None:
    diretor, motor, _estado_motor, modelo, agendamentos = _pilha_p2()
    motor.configurar_dominio(
        "jogo", "sugestao", confirmacao_explicita=True, origem="laboratorio_p2",
    )
    evento = _evento_jogo("vitoria-expirada")
    evento.update(timestamp=990.0, validade_s=8.0)

    resultado = diretor.considerar(evento)

    assert resultado == {
        "status": "bloqueada",
        "motivo": "evento_expirado",
        "categoria": "celebracao",
        "ts": 1_000.0,
    }
    assert modelo.chamadas == 0
    assert agendamentos == []


def test_red_p2_pedro_falando_bloqueia_antes_da_cognicao_e_do_llm() -> None:
    diretor, motor, _estado_motor, modelo, agendamentos = _pilha_p2(
        contexto_extra={"usuario_falando": True},
    )
    motor.configurar_dominio(
        "jogo", "sugestao", confirmacao_explicita=True, origem="laboratorio_p2",
    )

    resultado = diretor.considerar(_evento_jogo("vitoria-durante-fala-pedro"))

    assert resultado == {
        "status": "bloqueada",
        "motivo": "usuario_falando",
        "categoria": "celebracao",
        "ts": 1_000.0,
    }
    assert modelo.chamadas == 0
    assert agendamentos == []


def test_red_p2_tts_ativo_continua_bloqueando_antes_do_llm() -> None:
    diretor, motor, _estado_motor, modelo, agendamentos = _pilha_p2(
        contexto_extra={"is_speaking": True},
    )
    motor.configurar_dominio(
        "jogo", "sugestao", confirmacao_explicita=True, origem="laboratorio_p2",
    )

    resultado = diretor.considerar(_evento_jogo("vitoria-durante-tts"))

    assert resultado["status"] == "bloqueada"
    assert resultado["motivo"] == "fala_ou_turno_em_andamento"
    assert modelo.chamadas == 0
    assert agendamentos == []


def test_red_p2_evento_repetido_nao_gera_segunda_candidata() -> None:
    diretor, motor, _estado_motor, modelo, agendamentos = _pilha_p2()
    motor.configurar_dominio(
        "jogo", "sugestao", confirmacao_explicita=True, origem="laboratorio_p2",
    )
    evento = _evento_jogo("vitoria-repetida")

    primeira = diretor.considerar(evento)
    segunda = diretor.considerar(evento)

    assert primeira["status"] == "proposta_cognitiva"
    assert segunda["status"] == "bloqueada"
    assert segunda["motivo"] == "governanca"
    assert modelo.chamadas == 1
    assert len(agendamentos) == 1


def test_red_p2_cooldown_comeca_somente_apos_entrega_confirmada() -> None:
    diretor, motor, _estado_motor, modelo, agendamentos = _pilha_p2()
    motor.configurar_dominio(
        "jogo", "sugestao", confirmacao_explicita=True, origem="laboratorio_p2",
    )

    primeira = diretor.considerar(_evento_jogo("vitoria-entregue"))
    assert primeira["status"] == "proposta_cognitiva"
    assert len(agendamentos) == 1
    callback_entrega = agendamentos[0][4]["ao_concluir"]
    callback_entrega(True, "entregue")

    segunda = diretor.considerar(_evento_jogo("outra-vitoria-no-cooldown"))

    assert segunda == {
        "status": "bloqueada",
        "motivo": "cooldown_categoria",
        "categoria": "celebracao",
        "ts": 1_000.0,
    }
    assert modelo.chamadas == 1
    assert len(agendamentos) == 1


def test_red_p2_ponte_publica_estado_vad_do_usuario_no_contexto_real() -> None:
    ponte = PonteIniciativaAplicacaoRuntime(
        estado_mental_getter=lambda: {},
        percepcao_getter=lambda _chave, padrao: padrao,
        conversa_getter=lambda _chave, padrao: padrao,
        modo_jogo=SimpleNamespace(ativo=True),
        visao_leitura_getter=lambda: None,
        identificar_jogo=lambda _contexto: {},
        salvar_memoria=lambda: None,
        falar=lambda _texto, _emocao, _nivel: None,
        env_getter=lambda _nome, padrao: padrao,
        usuario_falando_getter=lambda: True,
        log=lambda _texto: None,
    )

    assert ponte.contexto()["usuario_falando"] is True


def test_red_p2_ouvido_expoe_estado_efemero_sem_expor_audio() -> None:
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _texto: None,
        esta_falando=lambda: False,
        log=lambda _texto: None,
    )

    assert ouvido.usuario_falando() is False
    assert not hasattr(ouvido, "audio_usuario_atual")


def test_red_p2_root_liga_ouvido_ao_contexto_canonico_de_iniciativa() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    conexao = ""
    for no in arvore.body:
        if not isinstance(no, ast.Expr) or not isinstance(no.value, ast.Call):
            continue
        funcao = no.value.func
        if (
            isinstance(funcao, ast.Attribute)
            and isinstance(funcao.value, ast.Name)
            and funcao.value.id == "_ponte_iniciativa_aplicacao_runtime"
            and funcao.attr == "conectar_usuario_falando"
        ):
            conexao = ast.unparse(no.value)
            break

    assert "_ouvido_whisper_runtime.usuario_falando" in conexao
