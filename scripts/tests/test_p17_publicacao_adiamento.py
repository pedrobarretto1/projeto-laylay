"""RPV17-04: adiamento publicado não é receipt de um efeito executado."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time
from types import SimpleNamespace

import pytest

import mente_laylay.autonomia.roteador_intencao as roteador
from mente_laylay.autonomia.comandos_imediatos import _executar_intencao_com_contrato
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.integracao.avaliador_roteiro_teste import avaliar_turno_roteiro
from mente_laylay.integracao.roteiro_teste_conversa import RoteiroTesteConversaRuntime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


TEXTO = "alterna a repetição. É opcional."


def _componentes(monkeypatch):
    estado = EstadoCompartilhadoRuntime(mental={
        "turno_atual": {"id": "turno-oferta", "autoriza_execucao": True},
        "ultima_entrada": TEXTO,
        "plano_turno_atual": {
            "id": "turno-oferta", "texto_usuario": TEXTO,
            "fase": "planejado", "requer_execucao": True,
            "autoriza_execucao": True, "comandos": [], "erros": [],
        },
    })
    pendencias = PendenciaAcaoRuntime(
        estado_getter=lambda: estado.mental,
        estado_atualizar=lambda mutar: estado.atualizar("mental", mutar),
        log=lambda *_: None,
    )
    consumidores, bases, publicacoes, falas, despachos, correcoes = [], [], [], [], [], []
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_registrar_resultado_execucao_base": lambda *a, **k: bases.append((a, k)),
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_concluir_correcao_interpretacao_mente": lambda *a, **k: correcoes.append((a, k)) or {},
        "print": lambda *_: None,
    }
    for nome, metodo in (
        ("_especialista_neural_comandos_runtime", "observar_resultado"),
        ("_motor_aprendizado_runtime", "observar_resultado"),
        ("_mapa_habilidades_runtime", "registrar_resultado"),
        ("_rede_associativa_runtime", "observar_resultado"),
    ):
        namespace[nome] = SimpleNamespace(**{
            metodo: lambda *a, _nome=nome, **k: consumidores.append((_nome, a, k)),
        })
    registrador = AdaptadoresAplicacaoRuntime(lambda: namespace)

    def publicar(*args, **opcoes):
        assert falas == [], "pergunta foi emitida antes da conclusão canônica"
        assert pendencias.obter() is not None, "publicação não possui pendência criada"
        publicacoes.append((args, opcoes))
        return registrador.registrar_resultado_execucao(*args, **opcoes)

    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="repetição redundante observada",
        evidencia_ref="receipt-redundancia", natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=0.96, relevancia=0.95,
        novidade=0.2, intensidade=3, sensibilidade="normal", alvo="Calculadora",
        validade_s=45.0, permite_expressao=True, emocao="brava", nivel=3,
        arco="bronca_brincalhona", ts=time.time(),
    )
    contexto = {
        "_target_from_params": lambda *_: "pc_a",
        "_registrar_resultado_execucao": publicar,
        "_pendencia_acao_runtime": pendencias,
        "falar_com_lipsync": lambda *args: falas.append(args),
        "_avaliar_evento_emocional_operacional": lambda *_: pytest.fail("adiamento virou evento de efeito"),
        "registrar_resistencia_p17": lambda _ref: True,
        "episodio_emocional": evento, "current_emotion": "brava", "emotion_level": 3,
        "turno_atual": estado.obter_copia("mental", "turno_atual"),
    }
    for nome in (
        "janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
        "musical", "playlists", "cancelamentos", "integracoes",
    ):
        def despachar(*_args, _nome=nome, **_kwargs):
            despachos.append(_nome)
            return (ResultadoDespacho.concluido(False) if _nome == "integracoes"
                    else ResultadoDespacho.nao_tratado())
        monkeypatch.setattr(roteador, f"_executar_intencao_{nome}", despachar)
    return SimpleNamespace(**locals())


def test_oferta_publica_aguardo_da_mesma_ocorrencia_antes_de_liberar_roteiro(monkeypatch):
    c = _componentes(monkeypatch)
    autoridade = copy.deepcopy(c.contexto["turno_atual"])
    pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"},
              "id_solicitacao": "ocorrencia-oferta"}
    tratamento = _executar_intencao_com_contrato(
        {"executar_intencao": lambda p, t: roteador.executar_intencao(p, t, c.contexto),
         "_registrar_resultado_execucao": c.contexto["_registrar_resultado_execucao"]},
        pedido, TEXTO, origem="prioritario",
    )
    pendencia = c.pendencias.obter()
    assert pendencia and pendencia["status"] == "ativa"
    assert len(c.falas) == 1 and "?" in c.falas[0][0]
    plano = c.estado.obter_copia("mental", "plano_turno_atual")
    assert len(plano["comandos"]) == 1, "adiamento tratado não publicou sua conclusão no plano"
    comando = plano["comandos"][0]
    assert comando["id_solicitacao"] == pedido["id_solicitacao"]
    assert comando["status"] == "aguardando_confirmacao"
    assert comando["origem"] == "politica"
    assert comando["executou"] is False and comando["confirmado"] is False
    assert pendencia["id"] in comando["evidencia_confirmacao"]
    assert pendencia["metadados"]["id_solicitacao"] == comando["id_solicitacao"]
    assert len(c.publicacoes) == 1, "chamador republicou o adiamento como fallback"
    assert tratamento.resultado_publicado and not tratamento.sucesso_habilidade
    assert c.despachos == [] and c.consumidores == [] and c.correcoes == []
    assert c.contexto["turno_atual"] == autoridade
    terminal, motivo = RoteiroTesteConversaRuntime._resultado_turno_terminal(
        plano, comando=TEXTO, plano_id_anterior="turno-anterior",
    )
    assert terminal and motivo == "aguardando_confirmacao_usuario"
    avaliacao = avaliar_turno_roteiro(
        indice=5, comando=TEXTO, resposta=c.falas[0][0], plano=plano,
        respondeu=True, motivo_resultado=motivo,
        expectativa_local={"intents_any": ("MEDIA_CONTROL",),
                           "statuses_any": ("aguardando_confirmacao",), "confirmado": False},
    )
    assert avaliacao["erros_semanticos"] == []


@pytest.mark.parametrize("intent,params", [
    ("MEDIA_CONTROL", {"acao": "repeat_toggle"}),
    ("DELETE_ITEM", {"alvo": "anotacoes.txt"}),
])
def test_conclusao_de_aguardo_de_outro_owner_nao_alimenta_observadores_de_efeito(monkeypatch, intent, params):
    c = _componentes(monkeypatch)
    resultado = ResultadoAcao(
        intent=intent, params=params, status="aguardando_confirmacao",
        executou=False, confirmado=False, origem="politica", id_solicitacao="aguardo-tipado",
        evidencia_confirmacao="pendencia_acao_canonica:oferta-a",
    )
    c.registrador.registrar_resultado_execucao(resultado, TEXTO, False, origem="politica")
    assert c.estado.mental["plano_turno_atual"]["comandos"][0]["id_solicitacao"] == "aguardo-tipado"
    assert c.consumidores == [], "decisão de aguardo virou resultado de habilidade no aprendizado"
    assert c.correcoes == [], "aguardo encerrou correção sem receipt de efeito"
    assert len(c.bases) == 1


def test_receipt_real_de_falha_continua_alimentando_observadores(monkeypatch):
    c = _componentes(monkeypatch)
    resultado = ResultadoAcao(
        intent="MEDIA_CONTROL", params={"acao": "repeat_toggle"}, status="falha_execucao",
        executou=False, confirmado=False, origem="executor", id_solicitacao="efeito-falhou",
    )
    c.registrador.registrar_resultado_execucao(resultado, TEXTO, False, origem="executor")
    assert len(c.consumidores) == 4 and len(c.bases) == 1


def test_nome_do_owner_normalizado_nao_reclassifica_executor_como_politica(monkeypatch):
    c = _componentes(monkeypatch)
    resultado = ResultadoAcao(
        intent="MEDIA_CONTROL", params={"acao": "repeat_toggle"}, status="aguardando_confirmacao",
        executou=False, confirmado=False, origem="Executor", id_solicitacao="executor-pendente",
    )
    c.registrador.registrar_resultado_execucao(resultado, TEXTO, False, origem="Executor")
    assert len(c.consumidores) == 4, "grafia do owner alterou o contrato de efeito existente"


@pytest.mark.parametrize("falha", ["recusa", "excecao"])
def test_publicacao_rejeitada_nao_deixa_oferta_nem_pergunta_sobre_adiamento(monkeypatch, falha):
    c = _componentes(monkeypatch)

    def rejeitar(*_args, **_kwargs):
        if falha == "excecao":
            raise RuntimeError("publicador_indisponivel")
        return False

    c.contexto["_registrar_resultado_execucao"] = rejeitar
    roteador.executar_intencao(
        {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"}}, TEXTO, c.contexto,
    )
    assert c.pendencias.obter() is None, "falha de publicação deixou oferta sem conclusão"
    assert c.falas == []
    assert "integracoes" in c.despachos
    assert c.consumidores == [] and c.correcoes == []


def test_plano_terminal_vazio_continua_red_sem_conclusao_publicada():
    plano = {"id": "turno-oferta", "texto_usuario": TEXTO,
             "fase": "tratado_prioritario", "requer_execucao": True,
             "autoriza_execucao": True, "comandos": [], "erros": []}
    terminal, motivo = RoteiroTesteConversaRuntime._resultado_turno_terminal(
        plano, comando=TEXTO, plano_id_anterior="turno-anterior",
    )
    assert terminal and motivo == "execucao_nao_publicada"
    avaliacao = avaliar_turno_roteiro(
        indice=5, comando=TEXTO, resposta="Quer que eu altere mesmo assim?", plano=plano,
        respondeu=True, motivo_resultado=motivo, expectativa_local={"dominio": "musica"},
    )
    assert avaliacao["erros_semanticos"] == ["execucao_nao_publicada"]


def test_composicao_instalada_publica_aguardo_com_porta_canonica_sem_executar_main(tmp_path):
    codigo = textwrap.dedent(r'''
        import json, os, sys, time
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.integracao import instancia_unica
        iniciar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho, *a, **k: iniciar(
            self, os.path.join(os.environ["LAYLAY_SONDA_SQLITE"], os.path.basename(caminho)), *a, **k,
        )
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
            str(ident) + ".p17-publicacao-" + str(os.getpid()), **k,
        )
        import laylay as root
        import mente_laylay.autonomia.roteador_intencao as roteador
        from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
        from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
        texto = "alterna a repetição. É opcional."
        estado = root._estado_compartilhado_runtime
        evento = criar_evento_emocional_causal(
            origem="resultado_operacional", causa="repetição redundante observada",
            evidencia_ref="receipt-redundancia", natureza_evidencia="fato_observado",
            responsabilidade="usuario", confianca=0.96, relevancia=0.95,
            novidade=0.2, intensidade=3, sensibilidade="normal", alvo="Calculadora",
            validade_s=45.0, permite_expressao=True, emocao="brava", nivel=3,
            arco="bronca_brincalhona", ts=time.time(),
        )
        estado.atualizar_campos("conversacional", current_emotion="brava", emotion_level=3,
                               episodio_emocional=evento)
        root._iniciar_planejamento_turno(texto, origem="teste_publicacao_p17")
        ctx = root._contexto_intencao_runtime.montar()
        instalada = ctx["_registrar_resultado_execucao"] == root._registrar_resultado_execucao
        falas, despachos = [], []
        ctx["falar_com_lipsync"] = lambda *a: falas.append(a)
        ctx["_avaliar_evento_emocional_operacional"] = lambda *_: (_ for _ in ()).throw(
            AssertionError("adiamento alimentou avaliador emocional"))
        for nome in ("janelas", "navegador", "audio", "agenda", "informacoes", "sistema",
                     "musical", "playlists", "cancelamentos", "integracoes"):
            def executar(*a, _nome=nome, **k):
                despachos.append(_nome)
                return ResultadoDespacho.nao_tratado()
            setattr(roteador, "_executar_intencao_" + nome, executar)
        autoridade = estado.obter_copia("mental", "turno_atual")
        antes = root._avaliador_eventos_emocionais_runtime.diagnostico()
        pedido = {"intent": "MEDIA_CONTROL", "params": {"acao": "repeat_toggle"},
                  "id_solicitacao": "oferta-composicao"}
        retorno = roteador.executar_intencao(pedido, texto, ctx)
        saida = dict(instalada=instalada, retorno=retorno,
                     plano=estado.obter_copia("mental", "plano_turno_atual"),
                     pendencia=root._pendencia_acao_runtime.obter(), falas=falas, despachos=despachos,
                     autoridade_preservada=autoridade == estado.obter_copia("mental", "turno_atual"),
                     emocional_preservado=antes == root._avaliador_eventos_emocionais_runtime.diagnostico())
        sys.__stdout__.write("P17_PUBLICACAO " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_SONDA_SQLITE=str(tmp_path)),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4000:]
    saida = next(json.loads(l.removeprefix("P17_PUBLICACAO "))
                 for l in processo.stdout.splitlines() if l.startswith("P17_PUBLICACAO "))
    assert saida["instalada"] and saida["retorno"]
    assert saida["pendencia"] and len(saida["falas"]) == 1
    assert len(saida["plano"]["comandos"]) == 1, "root não transportou a conclusão do adiamento"
    comando = saida["plano"]["comandos"][0]
    assert comando["id_solicitacao"] == "oferta-composicao"
    assert comando["status"] == "aguardando_confirmacao" and comando["origem"] == "politica"
    assert comando["executou"] is False and comando["confirmado"] is False
    assert saida["pendencia"]["id"] in comando["evidencia_confirmacao"]
    assert saida["despachos"] == [] and saida["emocional_preservado"]
    assert saida["autoridade_preservada"]
