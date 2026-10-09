"""Identidade e evidência por solicitação na composição instalada.

O subprocesso importa ``laylay`` sem chamar seu main. A mente, o validador,
o writer, o dispatcher, o adaptador operacional e o leitor são os objetos
de produção. Somente modelo, execução externa, voz e persistência são
portas isoladas. Receipts locais não comprovam efeito ou áudio físicos.
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
def correlacao_composicao(tmp_path_factory: pytest.TempPathFactory) -> dict:
    codigo = textwrap.dedent(r'''
        import json
        import os
        import sys
        from copy import deepcopy
        from types import SimpleNamespace
        from mente_laylay.integracao import instancia_unica
        from memoria_sqlite import MemoriaSQLite

        inicializar_sqlite = MemoriaSQLite.__init__
        def inicializar_sqlite_isolado(self, caminho, *args, **kwargs):
            return inicializar_sqlite(
                self, os.path.join(os.environ["LAYLAY_SONDA_SQLITE"], os.path.basename(caminho)),
                *args, **kwargs,
            )
        MemoriaSQLite.__init__ = inicializar_sqlite_isolado

        adquirir_real = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir_real(
            str(identificador) + ".sonda-solicitacao-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
        from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo

        estado = root._estado_compartilhado_runtime
        composicao = root._composicao_turno_runtime
        composicao._servicos["_coleta_entradas_neurais"] = None
        composicao._servicos["_especialista_neural_comandos_runtime"] = None
        composicao._servicos["_interpretador_semantico_runtime"] = None
        composicao._servicos["_pesquisa_contextual_runtime"] = None
        contexto = root._resposta_ia_runtime._contexto()
        validar = contexto["validar_comandos_planejados"]
        writer = contexto["atualizar_plano_proposta"]
        dispatcher = contexto["executar_comandos_json"]
        finalizar = contexto["finalizar_execucao"]
        registrar = root._registrar_resultado_execucao
        leitor = composicao.verificar_fala

        # Estes objetos instalados continuam responsáveis pelas mutações.
        # Suas portas de aprendizagem/persistência não participam da sonda.
        adaptadores = root._adaptadores_aplicacao_runtime
        namespace_registro = dict(adaptadores._ns())
        for porta in (
            "_especialista_neural_comandos_runtime", "_motor_aprendizado_runtime",
            "_mapa_habilidades_runtime", "_rede_associativa_runtime",
        ):
            namespace_registro[porta] = None
        namespace_getter_original = adaptadores._namespace_getter
        adaptadores._namespace_getter = lambda: namespace_registro

        resultados = {
            "instalacao": {
                "writer_owner": getattr(writer, "__self__", None) is composicao,
                "reader_owner": getattr(leitor, "__self__", None) is composicao,
                "registrador_owner": getattr(registrar, "__self__", None) is adaptadores,
                "mesma_mente": composicao._servicos["_estado_compartilhado_runtime"] is estado,
                "dispatcher_instalado": dispatcher is root._executar_comandos_json_mente,
                "finalizador_instalado": finalizar is root._finalizar_execucao_resposta_ia_mente,
                "runtime_instalado": contexto is not None,
            },
            "casos": {},
        }
        texto = "abre a Calculadora e o Bloco de Notas"

        try:
            for formato in ("flat", "canonico"):
                fonte = []
                for alvo in ("Calculadora", "Bloco de Notas"):
                    comando = (
                        {"acao": "open_app", "alvo": alvo}
                        if formato == "flat" else
                        {"intent": "APP_OPEN", "params": {"nome_app": alvo}}
                    )
                    comando.update(id_solicitacao="id-do-modelo", request_id="id-do-modelo")
                    fonte.append(comando)
                original = deepcopy(fonte)
                capturas = {"validacoes": [], "fases": {}, "pedidos": [], "receipts": [], "falas": [], "modelos": []}

                class ValidadorObservado:
                    def __call__(self, comandos):
                        return validar(comandos)
                    def validar_proposta(self, comandos, principal):
                        capturas["validacoes"].append(deepcopy(comandos))
                        return validar.validar_proposta(comandos, principal)
                    def validar_proposta_original(self, comandos, principal, extracao):
                        capturas["validacoes"].append(deepcopy(comandos))
                        return validar.validar_proposta_original(comandos, principal, extracao)

                def publicar(fase, principal, **campos):
                    capturas["fases"][fase] = deepcopy(campos.get("comandos") or [])
                    publicado = writer(fase, principal, **campos)
                    capturas["fases"][fase + ":publicado"] = json.loads(json.dumps(publicado.get("comandos") or []))
                    return publicado

                def registrar_local(receipt, *args, **kwargs):
                    capturas["receipts"].append(receipt.como_dict())
                    return registrar(receipt, *args, **kwargs)

                def executar_local(pedido, entrada):
                    capturas["pedidos"].append(deepcopy(pedido))
                    alvo = str(pedido.get("params", {}).get("nome_app") or "")
                    confirmado = alvo == "Calculadora"
                    adaptador = AdaptadorResultadoOperacional(
                        pedido, pedido.get("params") or {}, entrada, "pc_a",
                        {"_registrar_resultado_execucao": registrar_local},
                    )
                    adaptador.marcar_resultado(
                        "app_iniciado_focado" if confirmado else "falha_execucao",
                        executou=confirmado, confirmado=confirmado,
                        evidencia_confirmacao="receipt local da Calculadora" if confirmado else "",
                    )
                    return confirmado

                def modelo_principal(_pedido):
                    capturas["modelos"].append("principal")
                    return ResultadoModelo(json.dumps({"fala": "Vou verificar.", "comandos": fonte}), True)

                def modelo_finalizacao(_pedido):
                    capturas["modelos"].append("finalizacao")
                    return ResultadoModelo(json.dumps({
                        "fala": "Não consegui abrir o Bloco de Notas.", "comandos": [],
                    }), True)

                ctx = {
                    "marcar_inicio_turno": root._iniciar_planejamento_turno,
                    "obter_turno_atual": contexto["obter_turno_atual"],
                    "usar_modo_rapido": lambda _texto: False,
                    "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
                    "modelo_llm": SimpleNamespace(executar=modelo_principal),
                    "preparar_resposta": lambda _texto, bruto: json.loads(bruto),
                    "validar_comandos_planejados": ValidadorObservado(),
                    "atualizar_plano_proposta": publicar,
                    "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {"executar_intencao": executar_local}),
                    "executar_comandos_json": dispatcher,
                    "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {
                        "messages": [{"role": "user", "content": texto}],
                        "modelo_llm": SimpleNamespace(executar=modelo_finalizacao),
                        "limpar_resposta_da_ia": lambda bruto: (json.loads(bruto)["fala"], []),
                        "falar_com_lipsync": lambda fala, *_args: capturas["falas"].append(fala),
                        "verificar_fala_turno": leitor,
                    }),
                    "finalizar_execucao": finalizar,
                }
                runtime = root._resposta_ia_runtime
                contexto_getter_original = runtime._contexto_getter
                try:
                    runtime._contexto_getter = lambda: ctx
                    runtime.processar(texto, origem="teste_correlacao_instalada")
                finally:
                    runtime._contexto_getter = contexto_getter_original

                plano = estado.obter_copia("mental", "plano_turno_atual")
                primeira_republicacao = deepcopy(plano.get("comandos") or [])
                verificacao = leitor("Concluí tudo.", origem="ia_final")

                # Alias legítimo identifica a mesma ocorrência. Outro ID com
                # a mesma intent não pode completar-se com seu receipt.
                primeiro_id = (primeira_republicacao[0].get("id_solicitacao")
                               if primeira_republicacao else "")
                alias = composicao.atualizar("executado", comandos=[{
                    "request_id": primeiro_id, "intent": "APP_OPEN",
                }])
                outro = composicao.atualizar("executado", comandos=[{
                    "id_solicitacao": "outra-solicitacao", "intent": "APP_OPEN",
                    "params": {"nome_app": "Paint"},
                }])
                resultados["casos"][formato] = {
                    "fonte_preservada": fonte == original,
                    "fonte": original, "capturas": capturas,
                    "plano": plano, "verificacao": verificacao,
                    "alias": alias.get("comandos") or [], "outro": outro.get("comandos") or [],
                }
        finally:
            adaptadores._namespace_getter = namespace_getter_original
        sys.__stdout__.write("CORRELACAO_COMPOSICAO " + json.dumps(resultados, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8",
                 LAYLAY_SONDA_SQLITE=str(tmp_path_factory.mktemp("correlacao-sqlite"))), capture_output=True,
        text=True, encoding="utf-8", timeout=60,
    )
    assert processo.returncode == 0, processo.stderr[-3000:]
    linhas = [linha.removeprefix("CORRELACAO_COMPOSICAO ") for linha in processo.stdout.splitlines()
              if linha.startswith("CORRELACAO_COMPOSICAO ")]
    assert len(linhas) == 1, "a composição deve devolver a prova da cadeia observada"
    return json.loads(linhas[0])


def test_callbacks_da_correlacao_sao_os_instalados_pelo_root(correlacao_composicao: dict) -> None:
    assert all(correlacao_composicao["instalacao"].values())


@pytest.mark.parametrize("formato", ("flat", "canonico"))
def test_runtime_cria_identidades_apos_validacao_e_transporta_ate_receipt(
    correlacao_composicao: dict, formato: str,
) -> None:
    caso = correlacao_composicao["casos"][formato]
    capturas = caso["capturas"]
    assert capturas["validacoes"] == [caso["fonte"]], "o último validador vê a proposta sem identidade host"
    planejados = capturas["fases"]["resposta_planejada"]
    ids = [item.get("id_solicitacao") for item in planejados]
    assert len(ids) == 2 and len(set(ids)) == 2 and all(ids) and "id-do-modelo" not in ids, "o host identifica cada pedido depois da validação"
    assert caso["fonte_preservada"], "identificar a execução não deve modificar a proposta"
    assert len(capturas["pedidos"]) == 2, "ambas as solicitações devem alcançar a porta de execução canônica"
    assert [item.get("id_solicitacao") for item in capturas["pedidos"]] == ids
    assert all("request_id" not in item and "id_solicitacao" not in item["params"]
               and "request_id" not in item["params"] for item in capturas["pedidos"])
    assert [item["id_solicitacao"] for item in capturas["receipts"]] == ids
    assert capturas["modelos"].count("principal") == 1


@pytest.mark.parametrize("formato", ("flat", "canonico"))
def test_writer_instalado_preserva_resultados_distintos_da_mesma_intencao(
    correlacao_composicao: dict, formato: str,
) -> None:
    caso = correlacao_composicao["casos"][formato]
    receipts = caso["capturas"]["receipts"]
    assert len(receipts) == 2, "o adaptador real deve publicar uma conclusão para cada tentativa"
    assert [item["alvo"] for item in receipts] == ["Calculadora", "Bloco de Notas"]
    assert [item["confirmado"] for item in receipts] == [True, False]
    comandos = caso["plano"]["comandos"]
    assert len(comandos) == 2, "republicar o plano não pode colapsar a intent repetida"
    for comando, receipt in zip(comandos, receipts, strict=True):
        for campo in ("id_solicitacao", "alvo", "status", "executou", "confirmado", "origem", "evidencia_confirmacao"):
            assert comando[campo] == receipt[campo], f"{campo} deve vir da própria solicitação"
    assert caso["plano"]["fase"] == "falha_execucao"
    assert caso["capturas"]["falas"] == ["Não consegui abrir o Bloco de Notas."]
    assert "conclusao_total_com_plano_parcial" in caso["verificacao"]["problemas"]
    assert caso["verificacao"]["fala"] != "Concluí tudo."


@pytest.mark.parametrize("formato", ("flat", "canonico"))
def test_alias_da_mesma_solicitacao_preserva_receipt_e_outro_id_nao_herda_evidencia(
    correlacao_composicao: dict, formato: str,
) -> None:
    caso = correlacao_composicao["casos"][formato]
    comandos = caso["plano"]["comandos"]
    assert len(comandos) == 2, "controle precisa de ambas as ocorrências publicadas"
    assert caso["alias"] == comandos, "request_id da própria ocorrência conserva o receipt na posição"
    assert caso["outro"][:2] == comandos
    novo = caso["outro"][2]
    assert novo["id_solicitacao"] == "outra-solicitacao"
    assert novo["status"] == "" and novo["executou"] is None and novo["confirmado"] is None
    assert novo["evidencia_confirmacao"] in (None, "")
