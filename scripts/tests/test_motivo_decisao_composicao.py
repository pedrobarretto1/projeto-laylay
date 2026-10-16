"""Decisão anterior ao efeito pela composição instalada, com serial simulado.

Nenhum corpo físico, conta, voz ou rede é acionado. O histórico cooperativo,
decisor, experiência e prompt são os owners que laylay.py conecta.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def decisao_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("motivo_decisao_instalada")
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_DECISAO_MEMORIA_TESTE"])
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "laylay.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".decisao-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
        from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
        from mente_laylay.cognicao.modelo_corporal import formatar_realidade_corporal
        from scripts.tests.test_corpo_transporte_oled import EspCorpo
        from scripts.tests.test_rosto_oled import estado_emocional
        executar_modelo_original = RegistroModeloLLM.executar
        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
        for nome in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime", "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            root._composicao_turno_runtime._servicos[nome] = None
        estado = root._estado_compartilhado_runtime
        corpo, rosto = root._corpo_motor_runtime, root._rosto_oled_runtime
        esp = EspCorpo()
        # O owner/transporte/handshake são os instalados. Somente a porta física
        # é substituída; nenhum USB/TCP real pode ser aberto neste processo.
        rosto._config_wifi_path = None
        rosto._config_wifi = None
        rosto.porta = "SERIAL_SIMULADO"
        rosto.autodetectar = False
        rosto.abrir_serial = lambda _: esp
        rosto.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError("TCP externo proibido"))
        corpo.companhia.perfil_corporal = "bancada"
        corpo.companhia._automatica_ao_iniciar = False
        corpo.companhia._ativacao_pendente = False
        corpo.companhia.prioridade_interacao_getter = lambda: False
        corpo.companhia._aguardar_gesto = lambda ms, validar: validar()
        root._voz_runtime.falar = lambda *_a, **_k: False
        saida = {"owners": {
            "transporte": corpo.transporte is rosto,
            "estado": corpo.estado is estado and corpo.experiencias.estado is estado,
            "coordenador": corpo.companhia.coordenador is root._orquestrador_cooperativo_runtime,
            "quadro": corpo.companhia.coordenador.quadro is root._quadro_cooperacao_runtime,
            "aprendizado": corpo.experiencias.aprendizado is root._motor_aprendizado_runtime,
        }, "casos": {}}
        original_iniciar = corpo.experiencias.iniciar
        iniciar_capturas = []
        def iniciar(**campos):
            antes = estado.obter_copia("mental", "intencao_corporal", {})
            ocorrencia = original_iniciar(**campos)
            argumentos = {k: v.como_dict() if hasattr(v, "como_dict") else v for k, v in campos.items()}
            iniciar_capturas.append({"decisao": antes, "argumentos": argumentos, "ocorrencia": ocorrencia.copy()})
            return ocorrencia
        corpo.experiencias.iniciar = iniciar
        original_mover = rosto.mover_corpo
        antes_motor = []
        def mover(*args, **kwargs):
            antes_motor.append({"decisao": estado.obter_copia("mental", "intencao_corporal", {}),
                "ocorrencia": iniciar_capturas[-1]["ocorrencia"],
                "quadro": root._quadro_cooperacao_runtime.snapshot()})
            return original_mover(*args, **kwargs)
        rosto.mover_corpo = mover
        try:
            root._iniciar_planejamento_turno("ative modo companhia na bancada", origem="teste_decisao")
            assert rosto.sincronizar(), rosto.diagnostico()
            texto = "ative modo companhia na bancada"
            ativacao = corpo.executar("CORPO_COMPANHIA", {"acao": "ativar"},
                autorizacao=classificar_modalidade_turno(texto))
            assert ativacao["ok"], ativacao
            estado.substituir("conversacional", estado_emocional("alegre"))
            assert rosto.sincronizar()
            retorno = corpo.companhia.processar()
            assert retorno.get("ok"), retorno
            capturada = iniciar_capturas[-1]
            experiencia = estado.obter_copia("mental", "experiencia_corporal", {})
            chave = f"corpo_execucao:{experiencia['perfil']}:{experiencia['nome']}:{experiencia['variante']}"
            aprendido = root._motor_aprendizado_runtime.memoria.listar_eventos_aprendizado(chave)
            historico_cooperativo = root._quadro_cooperacao_runtime.snapshot()
            quantidade_motores = len([f for f in esp.enviados if f.startswith("MOTOR ")])
            corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1))
            modelo = corpo.modelo_para_mente()
            pergunta = "Por que você fez esse gesto?"
            root._iniciar_planejamento_turno(pergunta, origem="teste_recuperacao_motivo")
            normal = root._contexto_prompt_runtime.preparar_pacote(pergunta)
            rapido = root._contexto_prompt_runtime.preparar_instrucao_rapida(pergunta)
            saida["casos"]["gesto_causal"] = {"captura_inicio": capturada,
                "antes_motor": list(antes_motor), "retorno": retorno, "experiencia": experiencia,
                "aprendido": aprendido,
                "experiencia_depois": estado.obter_copia("mental", "experiencia_corporal", {}),
                "quadro": historico_cooperativo, "modelo": modelo,
                "projecao": formatar_realidade_corporal(modelo),
                "normal": normal.prompt_sistema, "rapido": rapido,
                "plano_consulta": estado.obter_copia("mental", "plano_turno_atual", {}),
                "motores_antes_consulta": quantidade_motores,
                "motores_depois_consulta": len([f for f in esp.enviados if f.startswith("MOTOR ")])}
            if os.environ.get("LAYLAY_COLETAR_EXPLICACAO_IMPLICITA") == "1":
                consultas = []
                for texto_consulta in (
                    "Por que você fez esse gesto?",
                    "Por que você reagiu daquele jeito?",
                    "O que te levou a fazer isso?",
                    "Por que você apagou esse arquivo?",
                    "Por que você desligou essa tomada?",
                    "Qual foi o motivo da sua decisão?",
                ):
                    root._iniciar_planejamento_turno(texto_consulta, origem="teste_obrigacao_explicativa")
                    antes = estado.obter_copia("mental", "plano_turno_atual", {})
                    fonte = corpo.experiencias.recuperar_explicacao(texto_consulta, turno=antes)
                    candidata = "A escolha veio de uma rotina agendada anteriormente."
                    preparada = root._resposta_ia_runtime._contexto()["preparar_resposta"](texto_consulta,
                        json.dumps({"fala": candidata, "comandos": []}))
                    consultas.append({"texto": texto_consulta, "fonte_owner": fonte,
                        "candidata": candidata, "plano": antes, "preparada": preparada,
                        "guarda_final": root._verificar_fala_do_turno(candidata, origem="ia")})
                saida["consultas_implicitas"] = consultas
                from types import SimpleNamespace
                runtime = root._resposta_ia_runtime
                contexto_original = runtime._contexto_getter
                textos_publicados, turnos = [], []
                def receber_texto_implicito(texto, *_a, **_k):
                    textos_publicados.append(texto)
                    return True
                root._orquestrador_fala_runtime.registrar_observador_texto_final(receber_texto_implicito)
                try:
                    for texto_consulta in ("Por que você reagiu daquele jeito?",
                                           "Por que você apagou esse arquivo?",
                                           "Por que você desligou essa tomada?"):
                        for modo in (False, True):
                            modelos, executores = [], []
                            def gerar_implicita(self, pedido):
                                modelos.append(dataclasses.asdict(pedido))
                                return ResultadoModelo(json.dumps({"fala": "A escolha veio de uma rotina agendada anteriormente.",
                                    "comandos": [], "tipo_interacao": "pergunta"}), True)
                            RegistroModeloLLM.executar = gerar_implicita
                            contexto = contexto_original()
                            contexto["usar_modo_rapido"] = lambda _t: modo
                            def impedir_efeito_implicito(pedido, texto):
                                executores.append(pedido)
                                raise AssertionError("Explicação não admite execução externa.")
                            contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito_implicito})
                            runtime._contexto_getter = lambda: contexto
                            inicio_textos = len(textos_publicados)
                            motores_antes = len([f for f in esp.enviados if f.startswith("MOTOR ")])
                            runtime.processar(texto_consulta, origem="teste_explicacao_implicita_completa")
                            turnos.append({"modo": "rapido" if modo else "normal", "texto": texto_consulta,
                                "textos": textos_publicados[inicio_textos:], "modelos": modelos, "executores": executores,
                                "motores_antes": motores_antes,
                                "motores_depois": len([f for f in esp.enviados if f.startswith("MOTOR ")]),
                                "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                finally:
                    runtime._contexto_getter = contexto_original
                    RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                saida["turnos_implicitos"] = turnos
                root._iniciar_planejamento_turno(pergunta, origem="restabelecer_consulta_literal")
            if os.environ.get("LAYLAY_COLETAR_REVISAO_CAUSA") == "1":
                revisoes = []
                preparar_instalado = root._resposta_ia_runtime._contexto()["preparar_resposta"]
                for candidata in ("A escolha desse gesto veio de uma rotina agendada anteriormente.",
                                  "Escolhi esse gesto porque o servidor pediu."):
                    chamadas = []
                    def modelo_reparo(self, pedido):
                        chamadas.append(dataclasses.asdict(pedido))
                        return ResultadoModelo(json.dumps({"fala": candidata, "comandos": []}), True)
                    RegistroModeloLLM.executar = modelo_reparo
                    bruto = json.dumps({"fala": "Porque eu vi você com o olho no meio do ecrã.", "comandos": []})
                    preparada = preparar_instalado(pergunta, bruto)
                    guarda_final = root._verificar_fala_do_turno(candidata, origem="ia")
                    revisoes.append({"candidata": candidata, "preparada": preparada, "chamadas": chamadas,
                        "guarda_final": guarda_final,
                        "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                saida["revisoes_controladas"] = revisoes
                from types import SimpleNamespace
                textos_publicados = []
                def receber_texto(texto, *_a, **_k):
                    textos_publicados.append(texto)
                    return True
                root._orquestrador_fala_runtime.registrar_observador_texto_final(receber_texto)
                runtime = root._resposta_ia_runtime
                contexto_original = runtime._contexto_getter
                turnos = []
                try:
                    for modo in (False, True):
                        modelos, executores = [], []
                        def gerar(self, pedido):
                            modelos.append(dataclasses.asdict(pedido))
                            return ResultadoModelo(json.dumps({"fala": "A escolha desse gesto veio de uma rotina agendada anteriormente.",
                                "comandos": [], "tipo_interacao": "pergunta"}), True)
                        RegistroModeloLLM.executar = gerar
                        contexto = contexto_original()
                        contexto["usar_modo_rapido"] = lambda _t: modo
                        def impedir_efeito(pedido, texto):
                            executores.append(pedido)
                            raise AssertionError("Consulta histórica não admite execução externa.")
                        contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito})
                        runtime._contexto_getter = lambda: contexto
                        inicio_textos = len(textos_publicados)
                        motores_antes = len([f for f in esp.enviados if f.startswith("MOTOR ")])
                        runtime.processar(pergunta, origem="teste_revisao_completa")
                        turnos.append({"modo": "rapido" if modo else "normal", "textos": textos_publicados[inicio_textos:],
                            "modelos": modelos, "executores": executores,
                            "motores_antes": motores_antes,
                            "motores_depois": len([f for f in esp.enviados if f.startswith("MOTOR ")]),
                            "mental": estado.retrato_dominio("mental")})
                finally:
                    runtime._contexto_getter = contexto_original
                    RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                saida["turnos_revisao"] = turnos
            if os.environ.get("LAYLAY_DECISAO_QWEN_REAL") == "1":
                if os.environ.get("LAYLAY_COLETAR_EXPLICACAO_IMPLICITA") == "1":
                    pergunta = "Por que você reagiu daquele jeito?"
                from copy import deepcopy
                from dataclasses import asdict
                from types import SimpleNamespace
                import requests
                from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                selecao, transportes = selecao_local(), []
                requests.sessions.Session.request = criar_guarda_http_local(
                    selecao, transportes, requests.sessions.Session.request)
                RegistroModeloLLM.executar = executar_modelo_original
                runtime = root._resposta_ia_runtime
                contexto_original = runtime._contexto_getter
                log_original, logs = runtime._log, []
                runtime._log = logs.append
                instalado = runtime._contexto()
                chaves = ("marcar_inicio_turno", "obter_turno_atual", "texto_depende_de_contexto",
                    "preparacao_conversa", "estado_conversa", "preparar_resposta",
                    "validar_comandos_planejados", "atualizar_plano_proposta",
                    "proposta_principal_vigente", "executar_comandos_json",
                    "iniciar_orcamento_llm_turno", "configurar_orcamento_llm_turno", "finalizar_orcamento_llm_turno")
                geracoes = []
                try:
                    for modo in (False, True):
                        modelos, preparados, executores, finais = [], [], [], []
                        inicio_http = len(transportes)
                        def modelo_real(pedido):
                            resultado = instalado["modelo_llm"].executar(pedido)
                            modelos.append({"resultado": asdict(resultado)})
                            return resultado
                        def preparar(texto, bruto):
                            resultado = instalado["preparar_resposta"](texto, bruto)
                            preparados.append(deepcopy(resultado))
                            return resultado
                        def executar(pedido, texto):
                            executores.append(deepcopy(pedido))
                            return False
                        def finalizar(ctx, comandos, erros, fala, *flags):
                            finais.append({"fala": fala, "comandos": deepcopy(comandos), "erros": list(erros)})
                            return {"registrar_no_historico": False}
                        contexto = {k: instalado[k] for k in chaves if k in instalado}
                        contexto.update(usar_modo_rapido=lambda _texto: modo,
                            modelo_llm=SimpleNamespace(executar=modelo_real), preparar_resposta=preparar,
                            contexto_dispatch_runtime=SimpleNamespace(montar=lambda: {"executar_intencao": executar}),
                            contexto_finalizacao_runtime=SimpleNamespace(montar=lambda: {}), finalizar_execucao=finalizar)
                        runtime._contexto_getter = lambda: contexto
                        runtime.processar(pergunta, origem="sonda_decisao_real")
                        geracoes.append({"modo": "rapido" if modo else "normal", "modelos": modelos,
                            "preparados": preparados, "porta_executor": executores, "finais_isolados": finais,
                            "http": deepcopy(transportes[inicio_http:])})
                finally:
                    runtime._contexto_getter = contexto_original
                    runtime._log = log_original
                    RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                saida["qwen_real"] = {"selecao": selecao, "geracoes": geracoes, "logs": logs}
            # Uma recusa elétrica posterior não muda por que o gesto foi
            # escolhido. É outra ocorrência sob a mesma concessão simulada.
            root._iniciar_planejamento_turno("que dia triste", origem="teste_falha_decisao")
            estado.substituir("conversacional", estado_emocional("alegre"))
            corpo.companhia.revogar("fim_caso_anterior")
            assert rosto.sincronizar()
            assert corpo.executar("CORPO_COMPANHIA", {"acao": "ativar"},
                autorizacao=classificar_modalidade_turno(texto))["ok"]
            estado.substituir("conversacional", estado_emocional("triste"))
            assert rosto.sincronizar()
            esp.mack = False
            retorno_falha = corpo.companhia.processar()
            assert retorno_falha.get("ok") is False, retorno_falha
            falha = estado.obter_copia("mental", "experiencia_corporal", {})
            assert falha["id"] != experiencia["id"], retorno_falha
            saida["casos"]["falha_eletrica"] = {"captura_inicio": iniciar_capturas[-1],
                "experiencia": falha, "retorno": retorno_falha,
                "quadro": root._quadro_cooperacao_runtime.snapshot()}
            if os.environ.get("LAYLAY_COLETAR_REVISAO_CAUSA") == "1":
                consultas = []
                for texto_consulta in (f"Por que você fez esse gesto {falha['id']}?",
                                       "Por que você fez esse gesto?",
                                       "Por que você fez esse gesto 00000000000000000000000000000000?"):
                    root._iniciar_planejamento_turno(texto_consulta, origem="teste_limite_explicacao")
                    resultado = root._resposta_ia_runtime._contexto()["preparar_resposta"](texto_consulta,
                        json.dumps({"fala": "Foi porque uma rotina antiga pediu.", "comandos": []}))
                    consultas.append({"texto": texto_consulta, "preparada": resultado,
                        "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                saida["consultas_limites"] = consultas
        finally:
            rosto.encerrar()
        sys.__stdout__.write("DECISAO_INSTALADA " + json.dumps(saida, ensure_ascii=False,
            default=dataclasses.asdict) + "\n")
    ''')
    processo = subprocess.run([sys.executable, "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_DECISAO_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8",
        timeout=180 if os.environ.get("LAYLAY_DECISAO_QWEN_REAL") == "1" else 60)
    assert processo.returncode == 0, processo.stdout[-1500:] + processo.stderr[-5000:]
    dados = json.loads(next(linha.removeprefix("DECISAO_INSTALADA ")
        for linha in processo.stdout.splitlines() if linha.startswith("DECISAO_INSTALADA ")))
    evidencia = os.environ.get("LAYLAY_EVIDENCIA_DECISAO")
    if evidencia:
        with Path(evidencia).open("x", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return dados


def test_decisao_anterior_e_receipts_separados_na_composicao_instalada(decisao_instalada):
    assert all(decisao_instalada["owners"].values())
    caso = decisao_instalada["casos"]["gesto_causal"]
    captura = caso["captura_inicio"]
    assert captura["decisao"]["motivo"] == "mudanca_emocional_causal"
    assert caso["antes_motor"], "Não chegou à fronteira anterior ao efeito."
    assert caso["experiencia"]["intencao_id"] == captura["decisao"]["id"]
    assert caso["experiencia"] == caso["experiencia_depois"]
    assert caso["motores_antes_consulta"] == caso["motores_depois_consulta"]
    assert caso["experiencia"]["prova_deslocamento"] is False


def test_ocorrencia_conserva_motivo_original_antes_do_efeito(decisao_instalada):
    caso = decisao_instalada["casos"]["gesto_causal"]
    fonte = caso["captura_inicio"]["ocorrencia"].get("decisao_origem")
    assert fonte, "Primeira fronteira: decisão existe antes do efeito, mas sua ocorrência guarda apenas ID."
    assert fonte["motivo"] == caso["captura_inicio"]["decisao"]["motivo"]
    assert fonte["autoriza_execucao"] is False
    assert caso["aprendido"][0]["contexto"]["experiencia"]["decisao_origem"] == fonte
    assert all(c["ocorrencia"]["decisao_origem"] == fonte for c in caso["antes_motor"])


def test_falha_eletrica_preserva_decisao_sem_fabricar_confirmacao(decisao_instalada):
    caso = decisao_instalada["casos"]["falha_eletrica"]
    e = caso["experiencia"]
    assert e["decisao_origem"]["motivo"] == "mudanca_emocional_causal"
    assert e["decisao_origem"] == caso["captura_inicio"]["ocorrencia"]["decisao_origem"]
    assert e["motivo"] != e["decisao_origem"]["motivo"]
    assert not e["confirmado"] and not e["prova_deslocamento"] and not e["autoriza_execucao"]
    assert caso["quadro"]["planos_recentes"][-1]["estado"] != "confirmado"


def test_fonte_e_contrato_cabem_inteiros_no_transporte_local(decisao_instalada):
    from mente_laylay.cognicao.modelo_corporal import formatar_modelo_corporal
    from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
    from mente_laylay.integracao.llm_http import compactar_payload_llm_local
    modelo = decisao_instalada["casos"]["gesto_causal"]["modelo"]
    instrucao = formatar_modelo_corporal(modelo)
    assert len(instrucao) <= 3800, "A fonte nova não pode expulsar regras de saída do transporte."
    payload = preparar_payload_llm([{"role": "system", "content": instrucao},
        {"role": "user", "content": "por que fez esse gesto?"}], model="qwen3:4b-instruct",
        max_tokens=256, endpoint_local=True, contexto_fechado=True)
    assert instrucao in compactar_payload_llm_local(payload)["messages"][-2]["content"]


def test_geracao_opcional_real_alcanca_http_sem_executar_propostas(decisao_instalada):
    if "qwen_real" not in decisao_instalada:
        pytest.skip("Sonda opcional exige LAYLAY_DECISAO_QWEN_REAL=1.")
    dados = decisao_instalada["qwen_real"]
    assert len(dados["geracoes"]) == 2
    for geracao in dados["geracoes"]:
        assert geracao["modelos"] and geracao["modelos"][0]["resultado"]["sucesso"], dados["logs"]
        assert any(r.get("status") == 200 for r in geracao["http"]), dados["logs"]
        assert any("mudanca_emocional_causal" in json.dumps(r["payload"], ensure_ascii=False)
                   for r in geracao["http"])
        assert not geracao["porta_executor"]


@pytest.mark.parametrize("rota", ["normal", "rapido"])
def test_consulta_recupera_motivo_anterior_sem_emprestar_decisao_atual(rota, decisao_instalada):
    caso = decisao_instalada["casos"]["gesto_causal"]
    assert caso["experiencia"]["intencao_id"] != caso["modelo"]["intencao_em_curso"]["id"]
    assert "mudanca_emocional_causal" in caso[rota], "Motivo do gesto antigo não é recuperável após outra decisão."
