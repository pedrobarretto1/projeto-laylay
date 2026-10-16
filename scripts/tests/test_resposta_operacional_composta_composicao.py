"""Portas e apresentação instaladas em laylay.py, com efeitos isolados.

O processo importa a composição real sem iniciar a aplicação. Executor externo,
modelo e TTS usam portas controladas; não há comprovação física ou de áudio.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def composicao_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("composta_instalada")
    codigo = textwrap.dedent(r'''
        import json, os, sys
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_COMPOSTA_MEMORIA_TESTE"])
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "laylay.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".composta-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
        from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
        from mente_laylay.autonomia.finalizacao_execucao_ia import finalizar_execucao_resposta_ia
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        orquestrador = root._orquestrador_fala_runtime
        ciclo = root._ciclo_comandos_runtime
        contexto = root._contexto_intencao_runtime
        registro = root._registro_servicos_aplicacao_runtime.snapshot()
        ctx = contexto.montar()
        dispatch_ctx = root._contexto_dispatcher_runtime.montar()
        saida = {"owners": {
            "registro_lote": registro.get("_agrupar_resultados_operacionais").__self__ is orquestrador,
            "contexto_lote": ctx.get("_agrupar_resultados_operacionais").__self__ is orquestrador,
            "contexto_acumulo": ctx.get("_acumular_resultado_operacional").__self__ is orquestrador,
            "dispatcher_lote": dispatch_ctx.get("_agrupar_resultados_operacionais").__self__ is orquestrador,
            "fala": root.falar_com_lipsync.__self__ is orquestrador,
            "ciclo": root._composicao_ciclo_comandos_runtime.ciclo is ciclo,
            # A origem agora é capturada na porta antes do efeito. A fachada
            # não é o callback global nu, mas continua no mesmo owner.
            "publicador": (
                ctx["_vincular_registro_resultado_execucao"].__self__ is root._adaptadores_aplicacao_runtime
                and ctx["_registrar_resultado_execucao"] is not root._registrar_resultado_execucao
                and ctx["_registrar_resultado_execucao"].__wrapped__ == root._registrar_resultado_execucao
            ),
        }, "casos": {}}
        # A publicação de receipt e o estado continuam sendo os instalados.
        # Apenas serviços de aprendizagem persistente são desligados na porta.
        ns_adaptadores = dict(root._adaptadores_aplicacao_runtime._ns())
        for nome in ("_especialista_neural_comandos_runtime", "_motor_aprendizado_runtime", "_mapa_habilidades_runtime", "_rede_associativa_runtime"):
            ns_adaptadores[nome] = None
        root._adaptadores_aplicacao_runtime._namespace_getter = lambda: ns_adaptadores
        for nome in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime", "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            root._composicao_turno_runtime._servicos[nome] = None
        caso = None
        orquestrador.registrar_observador_texto_final(lambda texto, *_a, **_k: caso["textos"].append(texto))
        root._voz_runtime.falar = lambda texto, *_a, **_k: caso["falas"].append(texto) or True
        def modelar(self, pedido):
            dados = json.loads(pedido.mensagens[1]["content"])
            caso["autorias"].append(dados)
            if caso.get("autoria_indisponivel"):
                return ResultadoModelo("", False)
            if caso.get("autoria_repetida"):
                trechos = [r["fato_verificado"].rstrip(".") for r in dados["resultados"]]
                caso["resposta_autoral"] = {"fala": " e ".join(trechos) + ".", "trechos": trechos}
                return ResultadoModelo(json.dumps(caso["resposta_autoral"], ensure_ascii=False), True)
            assert len(dados["resultados"]) == 2
            luz = "Liguei a lâmpada do quarto"
            piano = "não consegui abrir a playlist piano" if caso["falha"] else "abri a playlist piano"
            resposta = {"fala": luz + " e " + piano + ".", "trechos": [{"indice": 0, "trecho": luz}, {"indice": 1, "trecho": piano}]}
            return ResultadoModelo(json.dumps(resposta, ensure_ascii=False), True)
        RegistroModeloLLM.executar = modelar
        ciclo._servicos_estaticos["detectar_intencao_deterministica"] = lambda texto: {"intent": "IOT_CONTROL" if "luz" in texto else "PLAYLIST_PLAY", "params": {"alvo": "lâmpada do quarto" if "luz" in texto else "piano"}}
        def efeito_isolado(resultado, texto, ctx_exec=None):
            alvo = resultado["params"]["alvo"]
            status = "ligado" if alvo != "piano" else ("falha_execucao" if caso["falha"] else "playlist_aberta")
            ok = status != "falha_execucao"
            adaptador = AdaptadorResultadoOperacional(resultado, resultado["params"], texto, "pc_a",
                contexto.montar() if ctx_exec is None else ctx_exec)
            adaptador.marcar_resultado(status, ok, confirmado=ok)
            adaptador.falar_por_status(status, "Lâmpada ligada. Pronta pra brilhar." if alvo != "piano" else "Já puxei piano pra tocar.", alvo=alvo)
            return ok
        ciclo.executar_intencao = efeito_isolado
        # A composição nova usa também a porta observada: substituir só o
        # bool legado não isola sua folha externa. O coordenador/publicador
        # permanecem reais, inclusive o coletor por invocação.
        from mente_laylay.autonomia import coordenador_intencao
        coordenador_intencao.executar_intencao = efeito_isolado
        for caminho in ("cadeia", "dispatcher"):
            for falha in (False, True):
                nome = caminho + ("_parcial" if falha else "_sucesso")
                caso = {"falha": falha, "falas": [], "textos": [], "autorias": []}
                texto = "liga a luz e coloca a playlist piano"
                root._iniciar_planejamento_turno(texto, origem="teste_composta_instalada")
                if caminho == "cadeia":
                    caso["tratado"] = root.processar_comandos_em_cadeia(texto)
                else:
                    comandos = [{"intent": "IOT_CONTROL", "params": {"alvo": "lâmpada do quarto"}}, {"intent": "PLAYLIST_PLAY", "params": {"alvo": "piano", "nome_playlist": "piano"}}]
                    dispatch_ctx = root._contexto_dispatcher_runtime.montar()
                    dispatch_ctx["executar_intencao"] = efeito_isolado
                    resultado = executar_comandos_json(dispatch_ctx, texto, comandos, "", "comando", False, False, False)
                    final_ctx = root._contexto_finalizacao_runtime.montar()
                    final_ctx["resposta_operacional_composta"] = resultado
                    final = finalizar_execucao_resposta_ia(final_ctx, comandos, resultado["erros"], "", False, True, False)
                    caso["final"] = final
                    caso["tratado"] = resultado["resposta_composta_publicada"]
                plano = root._estado_compartilhado_runtime.obter_copia("mental", "plano_turno_atual")
                caso["receipts"] = plano["comandos"]
                saida["casos"][nome] = caso
        # Router/adaptador/executor/publicador e agrupador instalados; somente
        # a API que moveria janelas é substituída. Não simular falar_por_status.
        from mente_laylay.autonomia.roteador_intencao import executar_intencao
        caso = {"falha": False, "falas": [], "textos": [], "autorias": [],
                "autoria_indisponivel": True, "efeitos": [], "publicacoes": []}
        root._iniciar_planejamento_turno(
            "coloca a Calculadora à esquerda e coloca a Calculadora à direita e coloca a Calculadora à esquerda",
            origem="teste_fala_direta_instalada")
        ctx_real = contexto.montar()
        def organizar(esquerda, direita):
            caso["efeitos"].append([esquerda, direita])
            return {"ok": True, "executou": True, "confirmado": True,
                    "status": "layout_confirmado", "nome_esquerda": esquerda, "nome_direita": direita}
        publicar = ctx_real["_registrar_resultado_execucao"]
        def observar(receipt, *args, **kwargs):
            aceito = publicar(receipt, *args, **kwargs)
            if aceito is not False:
                caso["publicacoes"].append(receipt.como_dict())
            return aceito
        ctx_real = {**ctx_real, "organizar_janelas_robusto": organizar,
                    "_registrar_resultado_execucao": observar}
        with ctx_real["_agrupar_resultados_operacionais"](texto_usuario="esquerda, direita, esquerda",
                enviar_mensagem=ctx_real["enviar_mensagem"]) as lote:
            for i, lado in enumerate(("left", "right", "left")):
                executar_intencao({"intent": "ORGANIZAR_DESKTOP", "params": {lado: "Calculadora"},
                    "id_solicitacao": f"layout-direto-{i}"}, "pedido autorizado", ctx_real)
            caso["receipts_no_lote"] = [r.como_dict() for r in lote.resultados]
            caso["avisos_no_lote"] = list(lote.avisos)
        saida["casos"]["fala_direta_repetida"] = caso
        # Mesmas portas instaladas, agora com três trechos e duas ocorrências
        # literais iguais; a autora é controlada, não substitui o verificador.
        caso = {"falha": False, "falas": [], "textos": [], "autorias": [], "autoria_repetida": True}
        root._iniciar_planejamento_turno("liga a lâmpada e desliga a lâmpada e liga a lâmpada",
            origem="teste_ocorrencias_autoria_instalada")
        ctx_autoria = contexto.montar()
        with ctx_autoria["_agrupar_resultados_operacionais"](texto_usuario="liga, desliga, liga",
                enviar_mensagem=ctx_autoria["enviar_mensagem"]) as lote:
            for i, status in enumerate(("ligado", "desligado", "ligado")):
                adapter = AdaptadorResultadoOperacional({"intent": "IOT_CONTROL", "id_solicitacao": f"autoria-{i}"},
                    {"alvo": "lâmpada", "acao": "ligar" if status == "ligado" else "desligar"},
                    "pedido da fixture", "pc_a", ctx_autoria)
                adapter.marcar_resultado(status, True, confirmado=True,
                    evidencia_confirmacao="fixture sintética, sem efeito físico")
                adapter.falar_texto_da_invocacao("Liguei a lâmpada." if status == "ligado" else "Desliguei a lâmpada.")
            caso["receipts_no_lote"] = [r.como_dict() for r in lote.resultados]
        saida["casos"]["autoria_ocorrencias_iguais"] = caso
        sys.__stdout__.write("COMPOSTA_INSTALADA " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_COMPOSTA_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert processo.returncode == 0, processo.stderr[-5000:]
    linha = next(x.removeprefix("COMPOSTA_INSTALADA ") for x in processo.stdout.splitlines() if x.startswith("COMPOSTA_INSTALADA "))
    return json.loads(linha)


def test_portas_do_composition_root_instalam_o_mesmo_owner(composicao_instalada):
    assert all(composicao_instalada["owners"].values())


def test_receipts_de_fala_direta_instalada_nao_viram_avisos_deduplicados(composicao_instalada):
    caso = composicao_instalada["casos"]["fala_direta_repetida"]
    assert len(caso["efeitos"]) == len(caso["publicacoes"]) == 3
    assert len(caso["receipts_no_lote"]) == 3, "vínculo some antes da autoria/direção"
    assert not caso["avisos_no_lote"]
    assert caso["textos"] == caso["falas"] and len(caso["textos"]) == 1
    assert caso["falas"][0].count("Calculadora na esquerda") == 2
    assert caso["falas"][0].rfind("Calculadora na esquerda") > caso["falas"][0].find("Calculadora na direita")


def test_autoria_instalada_aceita_trechos_repetidos_sem_recorrer_a_contingencia(composicao_instalada):
    caso = composicao_instalada["casos"]["autoria_ocorrencias_iguais"]
    assert len(caso["receipts_no_lote"]) == 3
    assert len({r["id_solicitacao"] for r in caso["receipts_no_lote"]}) == 3
    assert len(caso["autorias"]) == 1
    assert caso["autorias"][0]["resultados"][0]["fato_verificado"] == caso["autorias"][0]["resultados"][2]["fato_verificado"]
    assert "; " not in caso["resposta_autoral"]["fala"]
    # O sinal usada_llm também é provado no contrato local; aqui a fala exata
    # da autora controlada difere da contingência factual (conectivo/ponto).
    assert caso["textos"] == caso["falas"] == [caso["resposta_autoral"]["fala"]]


@pytest.mark.parametrize("caminho", ["cadeia", "dispatcher"])
@pytest.mark.parametrize("falha", [False, True])
def test_composicao_publica_receipts_separados_e_uma_resposta(caminho, falha, composicao_instalada):
    caso = composicao_instalada["casos"][caminho + ("_parcial" if falha else "_sucesso")]
    assert caso["tratado"]
    assert len(caso["receipts"]) == 2
    assert len({x["id_solicitacao"] for x in caso["receipts"]}) == 2
    assert caso["receipts"][0]["confirmado"] is True
    assert caso["receipts"][1]["confirmado"] is not falha
    assert len(caso["autorias"]) == len(caso["textos"]) == len(caso["falas"]) == 1
    assert caso["textos"] == caso["falas"]
    if falha:
        assert "não consegui abrir a playlist piano" in caso["falas"][0]
    else:
        assert caso["falas"] == ["Liguei a lâmpada do quarto e abri a playlist piano."]
