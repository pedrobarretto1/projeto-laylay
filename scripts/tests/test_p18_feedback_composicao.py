"""P18: ligação instalada no root escreve no SQLite real e isolado."""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_root_instalado_encaminha_feedback_da_emissao_com_proveniencia(tmp_path):
    codigo = textwrap.dedent(r'''
        import json, os, sys, time
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_P18_MEMORIA_TESTE"])
        iniciar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: iniciar(
            self, str(pasta / Path(caminho or "laylay_memoria.sqlite").name))
        iniciar_resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: iniciar_resumo(
            self, pasta_memoria=str(pasta / "resumo"), **k)
        iniciar_pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: iniciar_pessoas(
            self, caminho=pasta / "pessoas.json", **k)
        iniciar_central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: iniciar_central(
            self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
            str(ident) + ".p18-feedback-" + str(os.getpid()), **k)
        import laylay as root
        estado = root._estado_compartilhado_runtime
        diretor = root._diretor_presenca_runtime
        agora = [time.time()]
        diretor.clock = lambda: agora[0]
        fala_instalada = root._resposta_ia_runtime._contexto_getter()["observar_feedback_presenca"]
        assert fala_instalada == diretor.observar_resposta
        publicar_feedback = root._ponte_iniciativa_aplicacao_runtime._publicar_evento_emocional_feedback
        assert publicar_feedback.func == root._estado_contexto_runtime.publicar_evento_emocional_causal
        assert publicar_feedback.keywords == {"vincular_plano":False, "ocorrencia_unica":True}
        autoridade = {"id": "turno-de-controle", "autoriza_execucao": False}
        estado.atualizar_campos("mental", turno_atual=autoridade)
        def concluir(id_entrega, entregue=True, dominio="jogo"):
            diretor._registrar_resultado_entrega(
                id_entrega=id_entrega, entregue=entregue, motivo="entregue" if entregue else "falha_audio",
                fala="A dica observada.", registro_proposta={
                    "ts": agora[0], "dominio": dominio, "categoria": "dica", "chave": "dica_observada",
                    "origem": "observador_jogo"}, ao_concluir_fonte=None)
        concluir("p18-sem-entrega", False)
        assert fala_instalada("boa dica, isso ajudou") == {}
        assert root.MEMORIA_SQLITE.listar_hipoteses_aprendizado(limit=30) == []
        concluir("p18-entrega-aceita")
        assert fala_instalada("boa dica, isso ajudou")["resultado"] == "aceita"
        assert fala_instalada("boa dica, isso ajudou") == {}
        concluir("p18-entrega-corrigida", dominio="rotina")
        assert fala_instalada("essa dica está errada")["resultado"] == "correcao"
        concluir("p18-entrega-silencio")
        agora[0] += 599
        assert diretor.registrar_silencio_pendente() == {}
        agora[0] += 1
        assert diretor.registrar_silencio_pendente()["resultado"] == "silencio"
        assert diretor.registrar_silencio_pendente() == {}
        hipoteses = [h for h in root.MEMORIA_SQLITE.listar_hipoteses_aprendizado(limit=30)
                     if h["tipo"] == "feedback_contextual"]
        eventos = [e for h in hipoteses for e in root.MEMORIA_SQLITE.listar_eventos_aprendizado(h["chave"])]
        autoridade_preservada = estado.mental["turno_atual"] == autoridade
        from types import SimpleNamespace
        from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
        ctx_instalado = root._resposta_ia_runtime._contexto()
        assert ctx_instalado["registrar_feedback_emissao_turno"] == root._adaptadores_aplicacao_runtime.registrar_feedback_emissao_turno
        central = root._central_notificacoes_runtime
        assert central.registrar_entrega_cb == diretor.registrar_entrega_observada
        agendar_real = central.agendar_fala_cb
        assert agendar_real == root._agendar_fala_proativa
        agendadas = []
        central.agendar_fala_cb = lambda *a, **k: agendadas.append((a, k)) or True
        central.time_cb = lambda: agora[0]
        central.ingerir([{"id":"p18-root-aviso", "origem":"sistema", "titulo":"Aviso de controle"}])
        assert len(agendadas) == 1
        assert estado.mental["turno_atual"] == autoridade
        assert estado.mental["eventos_emocionais_causais"]["atual"]["origem"] == "central_notificacoes"
        agendadas[0][1]["ao_concluir"](True, "entregue")
        entrega_aviso = estado.mental["presenca_contextual"]["ultima_emissao"]["id_entrega"]
        agora[0] += 3
        chamadas = []
        def modelo(_pedido):
            chamadas.append("modelo")
            return ResultadoModelo(json.dumps({"fala":"Entendi a correção.", "comandos":[],
                                               "leitura_turno":["correcao"]}), True)
        def finalizar(*_args):
            chamadas.append("finalizacao")
            return {"fala":"Entendi a correção.", "registrar_no_historico":True}
        def dispatch(_ctx, _texto, comandos, *_args):
            assert comandos == [], "feedback não autoriza efeito externo"
            chamadas.append("dispatch")
            return {"erros":[]}
        chaves = ("marcar_inicio_turno", "obter_turno_atual", "observar_feedback_presenca",
                  "registrar_feedback_emissao_turno", "estado_conversa", "registrar_mente_curta",
                  "preparar_resposta", "validar_comandos_planejados", "atualizar_plano_turno",
                  "registrar_leitura_semantica_principal", "registrar_leitura_proposta",
                  "atualizar_plano_proposta", "atualizar_plano_ocorrencia")
        ctx = {k:ctx_instalado[k] for k in chaves}
        ctx.update(usar_modo_rapido=lambda _texto:False,
                   preparacao_conversa=SimpleNamespace(preparar_pacote=lambda _texto:PacotePrompt(())),
                   modelo_llm=SimpleNamespace(executar=modelo),
                   contexto_dispatch_runtime=SimpleNamespace(montar=lambda:{}), executar_comandos_json=dispatch,
                   contexto_finalizacao_runtime=SimpleNamespace(montar=lambda:{}), finalizar_execucao=finalizar)
        runtime = root._resposta_ia_runtime
        getter = runtime._contexto_getter
        try:
            runtime._contexto_getter = lambda:ctx
            assert runtime.processar("na verdade não é isso", origem="p18_composicao") is not False
        finally:
            runtime._contexto_getter = getter
        finais = [h for h in root.MEMORIA_SQLITE.listar_hipoteses_aprendizado(limit=30)
                  if h["tipo"] == "feedback_contextual"]
        eventos_finais = [e for h in finais for e in root.MEMORIA_SQLITE.listar_eventos_aprendizado(h["chave"])]
        assert len(eventos_finais) == 4, "mesma correção não pode virar também feedback genérico"
        assert chamadas == ["modelo", "dispatch", "finalizacao"]
        ultimo = estado.mental["turno_atual"]
        assert ultimo["feedback_emissao_observado"]["turno_id"] == ultimo["id"]
        assert ultimo["autoriza_execucao"] is False
        causas_feedback = [e for e in estado.mental["eventos_emocionais_causais"]["historico"]
                           if e.get("origem") == "feedback_comunicativo"]
        assert len(causas_feedback) == 4
        causa_aviso = [e for e in causas_feedback if e["proveniencia"]["id_entrega"] == entrega_aviso]
        assert len(causa_aviso) == 1 and causa_aviso[0]["tipo_feedback"] == "correcao"
        assert all(e["permite_expressao"] is False and e["autoriza_execucao"] is False for e in causas_feedback)
        fluxo = dict(chamadas=chamadas, entrega=entrega_aviso,
                     eventos=len(eventos_finais), marca=ultimo["feedback_emissao_observado"],
                     causas=len(causas_feedback))
        # Agora as conexões instaladas agendam de verdade no owner de voz.
        # Somente relógio/timer e saída física ficam controlados.
        voz = root._voz_runtime
        timers = []
        class TimerControlado:
            def __init__(self, intervalo, callback):
                self.intervalo, self.callback = intervalo, callback
                timers.append(self)
            def start(self): pass
            def is_alive(self): return True
            def cancel(self): pass
        voz.timer_factory = TimerControlado
        voz.iniciar_worker = lambda:None
        voz.iniciar_turno_resposta()
        voz.sincronizar_chave_turno_resposta()
        central.agendar_fala_cb = agendar_real
        central.ingerir([{"id":"p18-aviso-concorrente", "origem":"sistema", "titulo":"Segundo aviso"}])
        assert len(voz.proativa_buffer) == 1
        assert voz.falar("A resposta confirmada do usuário.", "calma", 1) is True
        assert voz.falar("A resposta final confirmada do usuário.", "calma", 1) is True
        assert voz.fila.qsize() == 1
        assert len(voz.proativa_buffer) == 1, "aviso adiado não pode atravessar a resposta"
        assert central.diagnostico()["pendentes"] == 1, "fila não é receipt"
        voz.finalizar_turno_resposta()
        fluxo.update(fila_usuario=voz.fila.qsize(), avisos_adiados=len(voz.proativa_buffer), timers=len(timers))
        saida = dict(hipoteses=hipoteses, eventos=eventos,
                     autoridade_preservada=autoridade_preservada, fluxo_notificacao=fluxo,
                     emissao=estado.mental["presenca_contextual"]["ultima_emissao"],
                     porta_instalada=root._ponte_iniciativa_aplicacao_runtime._registrar_feedback_compartilhado
                     == root._adaptadores_aplicacao_runtime.registrar_feedback_contextual,
                     banco=root.MEMORIA_SQLITE.db_path)
        sys.__stdout__.write("P18_COMPOSICAO " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_P18_MEMORIA_TESTE=str(tmp_path),
                 GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ", LAYLAY_IOT_MODO="simulado"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4500:]
    dados = next(json.loads(l.removeprefix("P18_COMPOSICAO "))
                 for l in processo.stdout.splitlines() if l.startswith("P18_COMPOSICAO "))
    assert dados["porta_instalada"] and dados["autoridade_preservada"]
    assert Path(dados["banco"]).parent == tmp_path
    assert len(dados["eventos"]) == 3
    assert {e["valor"]["evento"] for e in dados["eventos"]} == {"aceitacao", "correcao", "silencio"}
    assert {e["contexto"]["proveniencia"]["id_entrega"] for e in dados["eventos"]} == {
        "p18-entrega-aceita", "p18-entrega-corrigida", "p18-entrega-silencio"}
    assert all(e["confirmado_usuario"] is False for e in dados["eventos"])
    assert all(h["status"] == "candidata" for h in dados["hipoteses"])
    assert all(e["contexto"]["origem_feedback"] == "presenca" for e in dados["eventos"])
    assert dados["fluxo_notificacao"]["eventos"] == 4
    assert dados["fluxo_notificacao"]["entrega"].startswith("notificacao:")
    assert dados["fluxo_notificacao"]["fila_usuario"] == dados["fluxo_notificacao"]["avisos_adiados"] == 1
