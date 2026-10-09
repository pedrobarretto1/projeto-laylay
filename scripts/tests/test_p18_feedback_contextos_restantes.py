"""Entrega de avisos e repetição usam o aprendizado comum, sem novo executor."""

from __future__ import annotations

import ast
import inspect
import os
from functools import partial
from pathlib import Path

import pytest

from mente_laylay.autonomia.central_notificacoes import criar_central_notificacoes_runtime
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from scripts.tests.test_personalidade_viva_p18_feedback import (
    RAIZ, _executar_atribuicao_root, _feedbacks_compartilhados,
    _montar_composicao, _receber_receipt_entrega,
)


def _central_instalada(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    filas = []
    contexto = EstadoContextoRuntime(
        namespace_getter=lambda: {}, estado_runtime_getter=lambda: composicao.estado,
    )
    namespace = {
        "os": os, "partial": partial, "_base_dir": str(tmp_path),
        "CENTRAL_NOTIFICACOES_ARQUIVO": "central.json",
        "_criar_central_notificacoes_runtime_mente": criar_central_notificacoes_runtime,
        "falar_com_lipsync": lambda *_a: pytest.fail("anúncio não usa fala direta"),
        "_agendar_fala_proativa": lambda *a, **k: filas.append((a, k)) or True,
        "_agendamentos_load": lambda: [],
        "_modo_jogo_runtime": type("Modo", (), {"ativo": False})(),
        "_conversa_estado_get": lambda _c, padrao=None: padrao,
        "_estado_compartilhado_runtime": composicao.estado,
        "_estado_contexto_runtime": contexto,
        "_diretor_presenca_runtime": composicao.diretor,
        "_motor_aprendizado_runtime": composicao.motor,
        "print": lambda *_a: None,
    }
    arvore = ast.parse((RAIZ / "laylay.py").read_text(encoding="utf-8"))
    _executar_atribuicao_root(arvore, "_central_notificacoes_runtime", namespace)
    central = namespace["_central_notificacoes_runtime"]
    central.time_cb = lambda: composicao.agora[0]
    return composicao, central, filas


@pytest.mark.parametrize("texto", ["de novo", "repete de novo", "tente outra vez"])
def test_repeticao_da_emissao_entregue_chega_ao_mesmo_motor(tmp_path, monkeypatch, texto):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.agora[0] += 5
    observado = composicao.diretor.observar_resposta(texto)
    assert observado.get("resultado") == "repeticao"
    registros = _feedbacks_compartilhados(composicao)
    assert len(registros) == 1
    eventos = composicao.memoria.listar_eventos_aprendizado(registros[0]["chave"])
    assert registros[0]["valor"]["evento"] == "repeticao"
    assert eventos[0]["sinal"] == -0.35
    assert composicao.diretor.observar_resposta(texto) == {}


@pytest.mark.parametrize("texto", [
    'A frase "repete de novo" é só um exemplo.',
    '"boa dica, isso ajudou"',
    "repete de novo e apaga o arquivo",
    "como eu diria boa dica, isso ajudou?",
])
def test_citacao_ou_comando_novo_nao_e_feedback_da_presenca(tmp_path, monkeypatch, texto):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    assert composicao.diretor.observar_resposta(texto) == {}
    assert _feedbacks_compartilhados(composicao) == []


@pytest.mark.parametrize("texto,resultado", [
    ("esse aviso ajudou", "aceita"), ("não precisa comentar", "recusa"),
    ("na verdade não é isso", "correcao"), ("de novo", "repeticao"),
])
def test_receipt_do_aviso_cria_vinculo_para_feedback_no_motor_comum(
    tmp_path, monkeypatch, texto, resultado,
):
    composicao, central, filas = _central_instalada(tmp_path, monkeypatch)
    central.ingerir([{"id": "aviso-testado", "origem": "sistema", "titulo": "Atualização disponível"}])
    assert len(filas) == 1
    assert composicao.estado.mental.get("presenca_contextual", {}).get("ultima_emissao", {}) == {}
    filas[0][1]["ao_concluir"](True, "entregue")
    emissao = composicao.estado.mental.get("presenca_contextual", {}).get("ultima_emissao", {})
    assert emissao.get("dominio") == "notificacoes", "receipt não alcançou o owner comum"
    assert emissao["entregue"] is True
    composicao.agora[0] += 5
    assert composicao.diretor.observar_resposta(texto)["resultado"] == resultado
    registros = _feedbacks_compartilhados(composicao)
    assert len(registros) == 1
    registro = composicao.memoria.listar_eventos_aprendizado(registros[0]["chave"])[0]
    assert registro["contexto"]["proveniencia"]["dominio"] == "notificacoes"
    assert registro["contexto"]["proveniencia"]["id_entrega"] == emissao["id_entrega"]
    assert registro["confirmado_usuario"] is False
    assert registros[0]["status"] == "candidata"


def test_falha_de_aviso_nao_cria_feedback_e_silencio_exige_entrega_e_600s(tmp_path, monkeypatch):
    composicao, central, filas = _central_instalada(tmp_path, monkeypatch)
    central.ingerir([{"id": "falha", "origem": "sistema", "titulo": "Aviso controlado"}])
    filas[0][1]["ao_concluir"](False, "falha_audio")
    assert composicao.estado.mental.get("presenca_contextual", {}).get("ultima_emissao", {}) == {}
    assert composicao.diretor.observar_resposta("esse aviso ajudou") == {}
    assert central.diagnostico()["pendentes"] == 1
    central.ingerir([{"id": "sucesso", "origem": "sistema", "titulo": "Outro aviso"}])
    filas[1][1]["ao_concluir"](True, "entregue")
    composicao.agora[0] += 599
    assert composicao.diretor.registrar_silencio_pendente() == {}
    composicao.agora[0] += 1
    assert composicao.diretor.registrar_silencio_pendente()["resultado"] == "silencio"
    assert len(_feedbacks_compartilhados(composicao)) == 1


def test_notificacao_preserva_plano_usuario_e_nao_inventa_irritacao(tmp_path, monkeypatch):
    composicao, central, filas = _central_instalada(tmp_path, monkeypatch)
    plano = {"id": "usuario-ativo", "autoriza_execucao": True}
    composicao.estado.atualizar_campos("mental", plano_turno_atual=plano)
    central.ingerir([{"id": "seguranca", "origem": "sistema", "categoria": "seguranca",
                    "titulo": "Novo acesso informado", "prioridade": "critica"}])
    assert filas[0][0][2:4] == ("calma", 1), "prioridade não é causa de irritação"
    evento = composicao.estado.mental["eventos_emocionais_causais"]["atual"]
    assert evento["origem"] == "central_notificacoes"
    assert evento["autoriza_execucao"] is False
    assert evento["permite_expressao"] is False
    assert composicao.estado.mental["plano_turno_atual"] == plano


def test_adaptador_legado_sem_receipt_nao_confirma_anuncio(tmp_path):
    central = criar_central_notificacoes_runtime(
        str(tmp_path / "central.json"), agendar_fala_cb=lambda *_a: True,
        time_cb=lambda: 1000.0, log=lambda *_a: None,
    )
    central.ingerir([{"id": "legado", "origem": "sistema", "titulo": "Aviso"}])
    assert central.diagnostico()["pendentes"] == 1


def test_observacao_textual_nao_conta_de_novo_feedback_da_mesma_entrada(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    texto = "na verdade não é isso"
    feedback = composicao.diretor.observar_resposta(texto)
    assert feedback["resultado"] == "correcao"
    composicao.estado.atualizar_campos("mental", turno_atual={"id": "entrada-1"})
    ns = composicao.adaptadores._ns()
    ns["_registrar_mente_curta_base"] = lambda *_a: None
    marcar = getattr(composicao.adaptadores, "registrar_feedback_emissao_turno", None)
    if callable(marcar):
        marcar(texto, feedback, "entrada-1")
    composicao.adaptadores.registrar_mente_curta(texto, "Entendi a correção.")
    assert len(_feedbacks_compartilhados(composicao)) == 1, "feedback entregue contou também como conversa genérica"


def test_novo_lote_apos_deduplicacao_tem_identidade_propria_de_entrega(tmp_path, monkeypatch):
    composicao, central, filas = _central_instalada(tmp_path, monkeypatch)
    aviso = {"id": "aviso-recorrente", "origem": "sistema", "titulo": "Aviso controlado"}
    central.ingerir([aviso])
    filas[0][1]["ao_concluir"](True, "entregue")
    primeira = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["id_entrega"]
    assert composicao.diretor.observar_resposta("esse aviso ajudou")["resultado"] == "aceita"
    composicao.agora[0] += 7 * 86400 + 1
    central.ingerir([aviso])
    assert len(filas) == 2, "novo lote precisa ter atravessado a ingestão"
    filas[1][1]["ao_concluir"](True, "entregue")
    segunda = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["id_entrega"]
    assert segunda != primeira, "IDs de fonte iguais não tornam duas entregas a mesma ocorrência"
    assert composicao.diretor.observar_resposta("esse aviso ajudou")["resultado"] == "aceita"
    eventos = [e for h in _feedbacks_compartilhados(composicao)
               for e in composicao.memoria.listar_eventos_aprendizado(h["chave"])]
    assert len(eventos) == 2
    assert {e["contexto"]["proveniencia"]["id_entrega"] for e in eventos} == {primeira, segunda}


@pytest.mark.parametrize("divergencia", ["entrada", "turno"])
def test_marca_de_feedback_nao_suprime_aprendizado_de_outra_entrada(tmp_path, monkeypatch, divergencia):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    texto = "na verdade não é isso"
    feedback = composicao.diretor.observar_resposta(texto)
    composicao.estado.atualizar_campos("mental", turno_atual={"id": "entrada-1"})
    composicao.adaptadores._ns()["_registrar_mente_curta_base"] = lambda *_a: None
    composicao.adaptadores.registrar_feedback_emissao_turno(texto, feedback, "entrada-1")
    if divergencia == "turno":
        turno = dict(composicao.estado.mental["turno_atual"], id="entrada-2")
        composicao.estado.atualizar_campos("mental", turno_atual=turno)
    else:
        texto = "você entendeu errado"
    composicao.adaptadores.registrar_mente_curta(texto, "Entendi.")
    assert len(_feedbacks_compartilhados(composicao)) == 2


def test_publicacao_de_ocorrencia_unica_nao_retrocede_quadro_em_replay(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    contexto = EstadoContextoRuntime(namespace_getter=lambda: {}, estado_runtime_getter=lambda: composicao.estado)
    def publicar(evento):
        extras = {"ocorrencia_unica": True} if "ocorrencia_unica" in inspect.signature(
            contexto.publicar_evento_emocional_causal).parameters else {}
        return contexto.publicar_evento_emocional_causal(evento, vincular_plano=False, **extras)
    def evento(ref):
        return criar_evento_emocional_causal(
            origem="controle_publicacao", causa="observação de entrega", evidencia_ref=ref,
            natureza_evidencia="fato_observado", responsabilidade="ambigua", confianca=1.0,
            relevancia=0.5, novidade=1.0, intensidade=0, permite_expressao=False,
            emocao="calma", nivel=1, ts=composicao.agora[0],
        )
    primeiro, segundo = evento("entrega:a"), evento("entrega:b")
    assert publicar(primeiro) is True
    assert publicar(segundo) is True
    antes = composicao.estado.snapshot()
    assert publicar(primeiro) is True, "mesma ocorrência válida continua idempotente"
    assert composicao.estado.snapshot() == antes, "replay não promove uma causa antiga a atual"
    adulterado = dict(primeiro, confianca=0.3)
    assert publicar(adulterado) is False, "identidade não confirma fonte diferente"
    assert composicao.estado.snapshot() == antes


def test_entrada_descartada_nao_consume_feedback_de_entrega(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    runtime = RespostaIARuntime(
        contexto_getter=lambda: {"observar_feedback_presenca": composicao.diretor.observar_resposta},
        log=lambda *_a: None,
    )
    assert runtime.processar("na verdade não é isso", ainda_atual_cb=lambda: False) is not False
    assert _feedbacks_compartilhados(composicao) == [], "entrada obsoleta não é feedback atual"
    assert composicao.diretor.observar_resposta("na verdade não é isso")["resultado"] == "correcao"
