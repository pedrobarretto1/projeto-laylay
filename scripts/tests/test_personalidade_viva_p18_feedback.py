"""P18: feedback de emissão entregue atravessa a porta de aprendizado comum.

RED histórico em resultados_testes/p18_feedback_emissao: aceitação e recusa
chegam ao coordenador/rede, mas não ao MotorAprendizado. Base:
90a2fb8698541119f523c0a22fa4de0187cbaf92, main, root da worktree.

A prova começa no receipt externo de entrega: componentes compartilhados e
SQLite temporária são reais; ligações relevantes vêm do AST atual do root.
Não importa laylay, não chama modelo/áudio e não inicia serviços. Não certifica
cognição anterior, autoria ou som físico.
"""

from __future__ import annotations

import ast
import os
import sqlite3
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.coordenador_oportunidades import CoordenadorOportunidadesRuntime
from mente_laylay.autonomia.diretor_presenca import criar_diretor_presenca_runtime
from mente_laylay.autonomia.motor_iniciativa import MotorIniciativaRuntime
from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.autonomia.resposta_evento_runtime import RespostaEventoRuntime
from mente_laylay.autonomia.servicos_background import GerenciadorServicosBackground
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.integracao.ponte_iniciativa_aplicacao import criar_ponte_iniciativa_aplicacao_runtime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
from mente_laylay.memoria_mental.rede_associativa import RedeAssociativaRuntime


RAIZ = Path(__file__).resolve().parents[2]


def _porta_externa_indisponivel(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("a prova de feedback não pode chamar modelo, áudio ou persistência do usuário")


def _executar_atribuicao_root(arvore: ast.Module, nome: str, namespace: dict[str, Any]) -> None:
    candidatos = [
        no for no in arvore.body
        if isinstance(no, ast.Assign)
        and any(isinstance(alvo, ast.Name) and alvo.id == nome for alvo in no.targets)
    ]
    assert len(candidatos) == 1, f"composição root ambígua para {nome}"
    trecho = ast.Module(body=candidatos, type_ignores=[])
    exec(compile(trecho, str(RAIZ / "laylay.py"), "exec"), namespace)


def _montar_composicao(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    agora = [1000.0]
    estado = EstadoCompartilhadoRuntime(mental={}, conversacional={}, percepcao={})
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria,
        contexto_getter=lambda: {"periodo": "noite", "atividade": "jogo"},
        log=lambda *_args: None,
    )
    contexto = {
        "modo_jogo_ativo": True, "turno_ativo": False,
        "is_speaking": False, "ultima_entrada_ts": 0.0,
    }

    def getter(chave: str):
        return lambda: dict(estado.mental.get(chave) or {})

    def setter(chave: str):
        return lambda valor: estado.atualizar_campos("mental", **{chave: dict(valor)})

    iniciativa = MotorIniciativaRuntime(
        estado_get=getter("iniciativa"), estado_set=setter("iniciativa"),
        contexto_getter=lambda: contexto, modo="sugestao",
        clock=lambda: agora[0], log=lambda *_args: None,
    )
    iniciativa.configurar_dominio("jogo", "sugestao", confirmacao_explicita=True)
    coordenador = CoordenadorOportunidadesRuntime(
        encaminhar=iniciativa.registrar,
        estado_get=getter("oportunidades"), estado_set=setter("oportunidades"),
        contexto_getter=lambda: contexto, clock=lambda: agora[0], log=lambda *_args: None,
    )
    porteiro = PorteiroProatividadeRuntime(contexto_getter=lambda: contexto, agora=lambda: agora[0])
    rede = RedeAssociativaRuntime(
        db_path=memoria.db_path, contexto_getter=lambda: {"atividade": "jogo"},
        modo="ativo", log=lambda *_args: None,
    )
    supervisor = GerenciadorServicosBackground(log=lambda *_args: None)
    # Estas dependências são reais, mas o teste começa após a entrega e não as chama.
    turnos = ComposicaoTurnoRuntime(servicos={"_estado_compartilhado_runtime": estado})
    resposta_evento = RespostaEventoRuntime(
        preparacao_prompt=None, modelo_llm=None,
        agendar_fala_proativa=_porta_externa_indisponivel, log=lambda *_args: None,
    )
    falhas: list[tuple[Any, ...]] = []
    namespace = {
        "os": os, "partial": partial, "print": lambda *_args: None,
        "_estado_compartilhado_runtime": estado,
        "_motor_aprendizado_runtime": motor,
        "_motor_iniciativa_runtime": iniciativa,
        "_porteiro_proatividade_runtime": porteiro,
        "_coordenador_oportunidades_runtime": coordenador,
        "_rede_associativa_runtime": rede,
        "_criar_ponte_iniciativa_aplicacao_runtime": criar_ponte_iniciativa_aplicacao_runtime,
        "_criar_diretor_presenca_runtime_mente": criar_diretor_presenca_runtime,
        "_percepcao_get": lambda chave, padrao=None: estado.percepcao.get(chave, padrao),
        "_conversa_estado_get": lambda chave, padrao=None: estado.conversacional.get(chave, padrao),
        "_modo_jogo_runtime": SimpleNamespace(ativo=True),
        "_prioridade_interacao_usuario_runtime": SimpleNamespace(ativa=lambda: False),
        "_registro_visao_jogo_leitura_runtime": None,
        "identificar_jogo": lambda _contexto: {},
        "salvar_memoria": lambda: None,
        "falar_com_lipsync": _porta_externa_indisponivel,
        "_composicao_turno_runtime": turnos,
        "_resposta_evento_runtime": resposta_evento,
        "_observabilidade_mente_runtime": SimpleNamespace(
            relatar_falha=lambda *args, **_kwargs: falhas.append(args),
        ),
        "_recomendar_playlist_real_para_presenca": _porta_externa_indisponivel,
        "_servicos_background_runtime": supervisor,
    }
    namespace["_estado_contexto_runtime"] = EstadoContextoRuntime(
        namespace_getter=lambda: namespace, estado_runtime_getter=lambda: estado,
    )
    namespace["_adaptadores_aplicacao_runtime"] = AdaptadoresAplicacaoRuntime(lambda: namespace)
    arvore = ast.parse((RAIZ / "laylay.py").read_text(encoding="utf-8"))
    _executar_atribuicao_root(arvore, "_ponte_iniciativa_aplicacao_runtime", namespace)
    monkeypatch.setattr(namespace["_ponte_iniciativa_aplicacao_runtime"], "_clock", lambda: agora[0])
    conexoes = [
        no for no in arvore.body
        if isinstance(no, ast.Expr) and isinstance(no.value, ast.Call)
        and isinstance(no.value.func, ast.Attribute) and no.value.func.attr == "conectar"
        and isinstance(no.value.func.value, ast.Name)
        and no.value.func.value.id == "_ponte_iniciativa_aplicacao_runtime"
    ]
    assert len(conexoes) == 1, "a ponte deve ter uma única conexão no root"
    exec(compile(ast.Module(body=conexoes, type_ignores=[]), str(RAIZ / "laylay.py"), "exec"), namespace)
    conexoes_aprendizado = [
        no for no in arvore.body
        if isinstance(no, ast.Expr) and isinstance(no.value, ast.Call)
        and isinstance(no.value.func, ast.Attribute) and no.value.func.attr == "conectar_aprendizado"
        and isinstance(no.value.func.value, ast.Name)
        and no.value.func.value.id == "_ponte_iniciativa_aplicacao_runtime"
    ]
    assert len(conexoes_aprendizado) <= 1, "a porta compartilhada não pode ser conectada duas vezes"
    if conexoes_aprendizado:
        exec(compile(ast.Module(body=conexoes_aprendizado, type_ignores=[]), str(RAIZ / "laylay.py"), "exec"), namespace)
    _executar_atribuicao_root(arvore, "_registrar_feedback_proatividade", namespace)
    namespace["_contexto_motor_iniciativa"] = namespace["_ponte_iniciativa_aplicacao_runtime"].contexto
    namespace["_registrar_oportunidade_iniciativa"] = coordenador.registrar
    _executar_atribuicao_root(arvore, "_diretor_presenca_runtime", namespace)
    diretor = namespace["_diretor_presenca_runtime"]
    monkeypatch.setattr(diretor, "clock", lambda: agora[0])
    return SimpleNamespace(
        diretor=diretor, memoria=memoria, motor=motor, estado=estado,
        coordenador=coordenador, rede=rede, agora=agora, falhas=falhas,
        ponte=namespace["_ponte_iniciativa_aplicacao_runtime"],
        adaptadores=namespace["_adaptadores_aplicacao_runtime"],
        estado_contexto=namespace["_estado_contexto_runtime"],
    )


def _receber_receipt_entrega(composicao: SimpleNamespace, entregue: bool) -> None:
    decisao = composicao.coordenador.registrar({
        "origem": "observador_jogo", "tipo": "presenca_dica", "dominio": "jogo",
        "chave": "presenca:jogo:dica:salto_observado", "confianca": 0.96,
        "utilidade": 84, "risco": "baixo", "momento_seguro": True,
        "executavel": False, "validade_s": 120.0,
    })
    assert decisao["decisao"] == "sugerir", "oportunidade deve atravessar governança real"
    composicao.diretor._registrar_resultado_entrega(
        id_entrega="presenca:jogo:dica:salto_observado:1000.0",
        entregue=entregue, motivo="entregue" if entregue else "falha_audio",
        fala="Esse salto pede um pouco mais de impulso.",
        registro_proposta={
            "ts": 1000.0, "dominio": "jogo", "categoria": "dica",
            "chave": "salto_observado", "origem": "observador_jogo",
        },
        ao_concluir_fonte=None,
    )


def _feedbacks_compartilhados(composicao: SimpleNamespace) -> list[dict[str, Any]]:
    return [
        item for item in composicao.memoria.listar_hipoteses_aprendizado(limit=100)
        if item["tipo"] == "feedback_contextual" and item["escopo"] != "controle_sqlite"
    ]


def test_controle_motor_real_persiste_feedback_sem_configuracao_adicional(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    hipotese = composicao.motor.registrar_feedback_contextual(
        tipo="aceitacao", aceito=True, resultado="boa dica", origem="controle_sqlite", alvo="dica",
    )
    assert hipotese is not None
    assert hipotese["evidencias_positivas"] == 1
    assert composicao.memoria.listar_eventos_aprendizado(hipotese["chave"])[0]["sinal"] > 0


@pytest.mark.parametrize(
    ("texto", "resultado", "aceito"),
    (("boa dica, isso ajudou", "aceita", True), ("não precisa comentar", "recusa", False),
     ("essa dica está errada", "correcao", None)),
    ids=("aceitacao", "recusa", "correcao"),
)
def test_feedback_de_emissao_confirmada_chega_ao_motor_compartilhado(
    tmp_path, monkeypatch, texto, resultado, aceito,
) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    emissao = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]
    assert emissao["id_entrega"] == "presenca:jogo:dica:salto_observado:1000.0"
    assert emissao["feedback_registrado"] is False

    observado = composicao.diretor.observar_resposta(texto)
    assert observado == {"resultado": resultado, "categoria": "dica"}
    assert composicao.falhas == [], "falha de callback não pode mascarar a fronteira de encaminhamento"
    assert composicao.coordenador.snapshot()["contadores"]["feedbacks"] == 1
    assert composicao.rede.processar_pendentes() == 1
    assert composicao.rede.diagnostico()["metricas"]["feedbacks"] == 1
    assert composicao.rede.diagnostico()["metricas"]["falhas"] == 0

    compartilhados = _feedbacks_compartilhados(composicao)
    assert len(compartilhados) == 1, (
        "RED P18: entrega e classificação foram confirmadas; coordenador e rede processaram "
        f"{resultado}, mas nenhum feedback alcançou MotorAprendizadoRuntime/SQLite compartilhado"
    )
    assert compartilhados[0]["valor"]["aceito"] is aceito
    eventos = composicao.memoria.listar_eventos_aprendizado(compartilhados[0]["chave"])
    assert len(eventos) == 1
    assert eventos[0]["evidencia"] == texto
    assert eventos[0]["contexto"]["proveniencia"] == {
        **_evento_feedback(composicao), "contexto_humor": emissao["contexto_humor"],
    }
    assert "fala" not in eventos[0]["contexto"]["proveniencia"]
    sinal = 0.45 if resultado == "aceita" else -0.45 if resultado == "recusa" else -0.35
    assert eventos[0]["sinal"] == pytest.approx(sinal)
    presenca = composicao.estado.mental["presenca_contextual"]
    assert presenca["ultima_emissao"]["aprendizado_compartilhado"] == {
        "status": "registrado", "id_evento": emissao["id_entrega"],
    }
    assert presenca["contadores"]["feedbacks_compartilhados"] == 1


def _evento_feedback(composicao: SimpleNamespace) -> dict[str, Any]:
    emissao = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]
    return {
        "id_entrega": emissao["id_entrega"], "dominio": emissao["dominio"],
        "origem_produtor": emissao["origem"], "categoria": emissao["categoria"],
        "alvo": emissao["chave"], "entrega_ts": emissao["ts"],
        "observado_ts": composicao.agora[0], "entregue": True,
    }


def _repetir_envio(composicao: SimpleNamespace, **alteracoes: Any) -> dict[str, Any]:
    evento = _evento_feedback(composicao)
    evento["contexto_humor"] = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["contexto_humor"]
    evento["id_evento"] = evento["id_entrega"]
    evento.update(alteracoes)
    return composicao.ponte.registrar_feedback(
        "jogo", True, resultado="aceita", texto_feedback="boa dica, isso ajudou",
        evento_feedback=evento,
    )


def test_replay_da_mesma_emissao_nao_duplica_evidencia_compartilhada(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.diretor.observar_resposta("boa dica, isso ajudou")
    compartilhados = _feedbacks_compartilhados(composicao)
    assert len(compartilhados) == 1
    chave = compartilhados[0]["chave"]
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou") == {}
    retorno = _repetir_envio(composicao)
    assert retorno["aprendizado_compartilhado"]["status"] == "registrado"
    assert len(composicao.memoria.listar_eventos_aprendizado(chave)) == 1
    assert composicao.coordenador.snapshot()["contadores"]["feedbacks"] == 1
    assert composicao.estado.mental["presenca_contextual"]["contadores"]["feedbacks_compartilhados"] == 1


@pytest.mark.parametrize("alteracoes", (
    {"id_entrega": "outra_emissao", "id_evento": "outra_emissao"},
    {"id_evento": "identidade_divergente"},
    {"dominio": "cotidiano"},
    {"origem_produtor": "outra_fonte"},
    {"categoria": "musica"},
    {"alvo": "outro_salto"},
    {"entregue": False},
    {"observado_ts": 1001.0},
))
def test_ponte_rejeita_proveniencia_divergente_da_emissao_real(tmp_path, monkeypatch, alteracoes) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.diretor.observar_resposta("boa dica, isso ajudou")
    compartilhados = _feedbacks_compartilhados(composicao)
    assert len(compartilhados) == 1
    retorno = _repetir_envio(composicao, **alteracoes)
    assert retorno["aprendizado_compartilhado"]["status"] == "rejeitado"
    assert len(composicao.memoria.listar_eventos_aprendizado(compartilhados[0]["chave"])) == 1


def test_porta_sem_motor_nao_confirma_persistencia(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    adaptador_sem_motor = AdaptadoresAplicacaoRuntime(lambda: {})
    composicao.ponte.conectar_aprendizado(registrar_feedback=adaptador_sem_motor.registrar_feedback_contextual)
    _receber_receipt_entrega(composicao, True)
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou")["resultado"] == "aceita"
    presenca = composicao.estado.mental["presenca_contextual"]
    assert presenca["ultima_emissao"]["aprendizado_compartilhado"]["status"] == "sem_persistencia"
    assert presenca["contadores"].get("feedbacks_compartilhados", 0) == 0
    assert _feedbacks_compartilhados(composicao) == []
    assert composicao.coordenador.snapshot()["contadores"]["feedbacks"] == 1


def test_erro_sqlite_nao_confirma_persistencia_e_preserva_consumidores(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)

    def falhar_escrita(**_dados):
        raise sqlite3.OperationalError("armazenamento temporariamente indisponível")

    # Falha somente a porta externa de persistência; motor/adaptador continuam reais.
    monkeypatch.setattr(composicao.memoria, "registrar_evidencia_aprendizado", falhar_escrita)
    _receber_receipt_entrega(composicao, True)
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou")["resultado"] == "aceita"
    presenca = composicao.estado.mental["presenca_contextual"]
    assert presenca["ultima_emissao"]["aprendizado_compartilhado"]["status"] == "sem_persistencia"
    assert presenca["contadores"].get("feedbacks_compartilhados", 0) == 0
    assert _feedbacks_compartilhados(composicao) == []
    assert composicao.coordenador.snapshot()["contadores"]["feedbacks"] == 1
    assert composicao.rede.processar_pendentes() == 1


def test_diagnostico_tardio_nao_altera_emissao_nova(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    id_anterior = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["id_entrega"]
    composicao.diretor._registrar_resultado_entrega(
        id_entrega="nova_emissao", entregue=True, motivo="entregue",
        fala="Outra dica depois da primeira.",
        registro_proposta={"dominio": "jogo", "categoria": "dica", "chave": "outra", "origem": "observador_jogo"},
        ao_concluir_fonte=None,
    )
    antes = composicao.estado.snapshot()["mental"]["presenca_contextual"]
    composicao.diretor._registrar_resultado_feedback_compartilhado(
        id_anterior, {"aprendizado_compartilhado": {"status": "registrado", "id_evento": id_anterior}},
    )
    assert composicao.estado.snapshot()["mental"]["presenca_contextual"] == antes


def test_feedback_da_ocorrencia_confirmada_sobrevive_nova_entrega_durante_encaminhamento(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    id_anterior = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["id_entrega"]
    encaminhar = composicao.diretor.registrar_feedback

    def entregar_nova_antes_da_ponte(*args, **kwargs):
        composicao.diretor._registrar_resultado_entrega(
            id_entrega="nova_emissao", entregue=True, motivo="entregue",
            fala="Outra dica.", registro_proposta={
                "dominio": "jogo", "categoria": "dica", "chave": "outra", "origem": "observador_jogo"},
            ao_concluir_fonte=None,
        )
        return encaminhar(*args, **kwargs)

    monkeypatch.setattr(composicao.diretor, "registrar_feedback", entregar_nova_antes_da_ponte)
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou")["resultado"] == "aceita"
    compartilhados = _feedbacks_compartilhados(composicao)
    assert len(compartilhados) == 1, "feedback confirmado perdido após outra entrega"
    evento = composicao.memoria.listar_eventos_aprendizado(compartilhados[0]["chave"])[0]
    assert evento["contexto"]["proveniencia"]["id_entrega"] == id_anterior
    presenca = composicao.estado.mental["presenca_contextual"]
    assert presenca["ultima_emissao"]["id_entrega"] == "nova_emissao"
    assert presenca["ultima_emissao"]["feedback_registrado"] is False
    assert not presenca["ultima_emissao"].get("aprendizado_compartilhado")
    anterior = next(e for e in presenca["historico"] if e["id_entrega"] == id_anterior)
    assert anterior["feedback"] == "aceita"
    assert anterior["aprendizado_compartilhado"]["status"] == "registrado"
    assert presenca["contadores"]["feedbacks_compartilhados"] == 1


def test_falha_de_entrega_nao_cria_alvo_nem_feedback_compartilhado(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, False)
    assert composicao.estado.mental["presenca_contextual"]["ultima_emissao"] == {}
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou") == {}
    assert composicao.coordenador.snapshot()["contadores"]["feedbacks"] == 0
    assert composicao.rede.processar_pendentes() == 0
    assert _feedbacks_compartilhados(composicao) == []



def test_ausencia_de_entrega_nao_cria_feedback(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou") == {}
    assert composicao.diretor.registrar_silencio_pendente() == {}
    assert _feedbacks_compartilhados(composicao) == []


def test_silencio_antes_de_600_segundos_nao_alimenta_motor(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.agora[0] = 1599.99
    assert composicao.diretor.registrar_silencio_pendente() == {}
    assert _feedbacks_compartilhados(composicao) == []
    assert composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["feedback_registrado"] is False


def test_silencio_qualificado_apos_600_segundos_chega_ao_motor(tmp_path, monkeypatch) -> None:
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.agora[0] = 1600.0
    observado = composicao.diretor.registrar_silencio_pendente()
    assert observado == {"resultado": "silencio", "categoria": "dica"}
    assert composicao.falhas == []
    compartilhados = _feedbacks_compartilhados(composicao)
    assert len(compartilhados) == 1, "silêncio qualificado da emissão entregue deve atravessar a porta comum"
    assert compartilhados[0]["valor"]["aceito"] is None
    eventos = composicao.memoria.listar_eventos_aprendizado(compartilhados[0]["chave"])
    assert eventos[0]["sinal"] == pytest.approx(-0.10)
    assert composicao.diretor.registrar_silencio_pendente() == {}
    assert len(composicao.memoria.listar_eventos_aprendizado(compartilhados[0]["chave"])) == 1

