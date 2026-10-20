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
        if os.environ.get("LAYLAY_COLETAR_MEDIDAS_OCORRENCIA") == "1":
            from scripts.tests.test_imu_corporal import EspImu
            esp = EspImu()
            if os.environ.get("LAYLAY_COLETAR_LEITURAS_PARCIAIS") == "1":
                from scripts.tests.test_leituras_parciais_corpo import EspLeituraParcial
                esp = EspLeituraParcial()
        # O owner/transporte/handshake são os instalados. Somente a porta física
        # é substituída; nenhum USB/TCP real pode ser aberto neste processo.
        rosto._config_wifi_path = None
        rosto._config_wifi = None
        rosto._wifi_alternativo_path = None
        rosto.identidade_usb_getter = lambda: {}
        rosto.listar_portas = lambda: ()
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
            if os.environ.get("LAYLAY_COLETAR_AGENTE_EXPLICACAO") == "1":
                consultas = []
                for texto_consulta in (
                    "Por que você fez esse gesto?",
                    "Por que eu fiz esse gesto?",
                    "Por que ela fez esse gesto?",
                    "Por que ele fez esse movimento?",
                    "Por que nós fizemos esse gesto?",
                    "Por que você fez esse gesto quando eu cheguei?",
                    "O que motivou esse movimento?",
                ):
                    root._iniciar_planejamento_turno(texto_consulta, origem="teste_agente_explicacao")
                    plano = estado.obter_copia("mental", "plano_turno_atual", {})
                    fonte = corpo.experiencias.recuperar_explicacao(texto_consulta, turno=plano)
                    candidata = "A decisão anterior registrou o motivo mudanca emocional causal."
                    preparada = root._resposta_ia_runtime._contexto()["preparar_resposta"](texto_consulta,
                        json.dumps({"fala": candidata, "comandos": []}))
                    consultas.append({"texto": texto_consulta, "fonte_owner": fonte, "plano": plano,
                        "turno": estado.obter_copia("mental", "turno_atual", {}), "preparada": preparada,
                        "guarda_final": root._verificar_fala_do_turno(candidata, origem="ia")})
                saida["consultas_agentes"] = consultas
                root._iniciar_planejamento_turno(pergunta, origem="restabelecer_consulta_literal")
            if os.environ.get("LAYLAY_COLETAR_EXPLICACAO_MULTIPLA") == "1":
                consultas = []
                for texto_consulta in (
                    "Por que você fez esse gesto? Por que você apagou esse arquivo?",
                    "Por que você apagou esse arquivo? Por que você fez esse gesto?",
                    "Por que você fez esse gesto e por que você desligou essa tomada?",
                    "Por que você fez esse gesto e apagou esse arquivo?",
                    "O que motivou esse movimento? Por que você apagou esse arquivo?",
                    "O que motivou esse movimento? Qual é a capital do Brasil?",
                ):
                    root._iniciar_planejamento_turno(texto_consulta, origem="teste_cobertura_explicacao")
                    plano = estado.obter_copia("mental", "plano_turno_atual", {})
                    fonte = corpo.experiencias.recuperar_explicacao(texto_consulta, turno=plano)
                    candidata = "O gesto e a outra ação aconteceram porque uma rotina agendada pediu."
                    preparada = root._resposta_ia_runtime._contexto()["preparar_resposta"](texto_consulta,
                        json.dumps({"fala": candidata, "comandos": []}))
                    consultas.append({"texto": texto_consulta, "fonte_owner": fonte, "plano": plano,
                        "turno": estado.obter_copia("mental", "turno_atual", {}),
                        "preparada": preparada, "guarda_final": root._verificar_fala_do_turno(candidata, origem="ia")})
                saida["consultas_multiplas"] = consultas
                root._iniciar_planejamento_turno(pergunta, origem="restabelecer_consulta_literal")
            if (os.environ.get("LAYLAY_COLETAR_EXPLICACAO_IMPLICITA") == "1"
                    or os.environ.get("LAYLAY_COLETAR_EXPLICACAO_MULTIPLA") == "1"
                    or os.environ.get("LAYLAY_COLETAR_AGENTE_EXPLICACAO") == "1"):
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
                    textos_ciclo = (("Por que você fez esse gesto? Por que você apagou esse arquivo?",
                                     "Por que você apagou esse arquivo? Por que você fez esse gesto?",
                                     "Por que você fez esse gesto e por que você desligou essa tomada?")
                        if os.environ.get("LAYLAY_COLETAR_EXPLICACAO_MULTIPLA") == "1" else
                        ("Por que você reagiu daquele jeito?", "Por que você apagou esse arquivo?",
                         "Por que você desligou essa tomada?"))
                    if os.environ.get("LAYLAY_COLETAR_AGENTE_EXPLICACAO") == "1":
                        textos_ciclo = ("Por que eu fiz esse gesto?", "Por que ela fez esse gesto?",
                                        "Por que ela fez esse gesto? Por que você fez esse gesto?")
                    for texto_consulta in textos_ciclo:
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
                saida["turnos_agentes" if os.environ.get("LAYLAY_COLETAR_AGENTE_EXPLICACAO") == "1"
                      else "turnos_multiplos" if os.environ.get("LAYLAY_COLETAR_EXPLICACAO_MULTIPLA") == "1"
                      else "turnos_implicitos"] = turnos
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
                if os.environ.get("LAYLAY_COLETAR_EXPLICACAO_MULTIPLA") == "1":
                    pergunta = "Por que você fez esse gesto? Por que você apagou esse arquivo?"
                if os.environ.get("LAYLAY_COLETAR_AGENTE_EXPLICACAO") == "1":
                    pergunta = "Por que eu fiz esse gesto?"
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
            if os.environ.get("LAYLAY_COLETAR_ESCOPO_OCORRENCIA") == "1":
                from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia
                from copy import deepcopy
                from types import SimpleNamespace
                runtime_escopo = root._resposta_ia_runtime
                contexto_escopo = runtime_escopo._contexto_getter
                publicacoes_escopo = []
                root._orquestrador_fala_runtime.registrar_observador_texto_final(
                    lambda texto, *_a, **_k: publicacoes_escopo.append(texto) or True)
                saida["escopos_ocorrencias"] = {}
                for nome, intent, ok in (("parada_ok", "CORPO_PARAR", True),
                        ("parada_falha", "CORPO_PARAR", False),
                        ("pwm_ok", "CORPO_MOVER", True), ("pwm_falha", "CORPO_MOVER", False)):
                    esp.stopped, esp.mack = True, True
                    assert rosto.sincronizar()
                    esp.stopped = ok if intent == "CORPO_PARAR" else True
                    esp.mack = ok
                    comando = "pare os motores" if intent == "CORPO_PARAR" else "ande para frente"
                    root._iniciar_planejamento_turno(comando, origem="teste_escopo_ocorrencia")
                    retorno = corpo.executar(intent, {} if intent == "CORPO_PARAR" else
                        {"direcao": "frente", "pwm": 160, "duracao_ms": 50})
                    e = estado.obter_copia("mental", "experiencia_corporal", {})
                    chave_escopo = f"corpo_execucao:{e['perfil']}:{e['nome']}:{e['variante']}"
                    eventos_escopo = root._motor_aprendizado_runtime.memoria.listar_eventos_aprendizado(chave_escopo)
                    pergunta = f"Por que você fez esse gesto {e['id']}?"
                    root._iniciar_planejamento_turno(pergunta, origem="teste_recuperacao_escopo")
                    historico = deepcopy(estado.obter_copia("mental", "historico_corporal", []))
                    efeitos = tuple(f for f in esp.enviados if f.startswith(("MOTOR ", "STOP ", "TURN ")))
                    normal = root._contexto_prompt_runtime.preparar_pacote(pergunta)
                    rapido = root._contexto_prompt_runtime.preparar_instrucao_rapida(pergunta)
                    plano = estado.obter_copia("mental", "plano_turno_atual", {})
                    fonte = plano["contrato_fala"]["explicacao_ocorrencia"]
                    fala = realizacoes_explicacao_ocorrencia(fonte)[0]
                    turnos_escopo = []
                    try:
                        for modo in (False, True):
                            contexto = contexto_escopo()
                            contexto["usar_modo_rapido"] = lambda _t: modo
                            executores = []
                            def impedir_efeito_escopo(pedido, texto):
                                executores.append(pedido)
                                raise AssertionError("Consulta histórica não executa.")
                            contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito_escopo})
                            runtime_escopo._contexto_getter = lambda: contexto
                            RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo(json.dumps({
                                "fala": "A ponte confirmou PWM e deslocamento físico por causa de uma rotina antiga.",
                                "comandos": []}), True)
                            inicio_publicacoes = len(publicacoes_escopo)
                            runtime_escopo.processar(pergunta, origem="teste_ciclo_escopo_ocorrencia")
                            turnos_escopo.append({"modo": "rapido" if modo else "normal",
                                "textos": publicacoes_escopo[inicio_publicacoes:], "executores": executores})
                    finally:
                        runtime_escopo._contexto_getter = contexto_escopo
                        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                    saida["escopos_ocorrencias"][nome] = {
                        "retorno": retorno, "experiencia": e, "fonte": dataclasses.asdict(fonte),
                        "eventos_aprendizado": eventos_escopo,
                        "turnos": turnos_escopo,
                        "fala_owner": fala, "normal": fala in normal.prompt_sistema or json.dumps(fala, ensure_ascii=False) in normal.prompt_sistema,
                        "rapido": fala in rapido or json.dumps(fala, ensure_ascii=False) in rapido,
                        "sem_novos_efeitos": efeitos == tuple(f for f in esp.enviados if f.startswith(("MOTOR ", "STOP ", "TURN "))),
                        "sem_mutacao_historico": historico == estado.obter_copia("mental", "historico_corporal", [])}
            if os.environ.get("LAYLAY_COLETAR_MEDIDAS_OCORRENCIA") == "1":
                from copy import deepcopy
                from types import SimpleNamespace
                from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia
                from mente_laylay.cognicao.suporte_autoria import segmentar_realizacao_autoral
                runtime_medidas = root._resposta_ia_runtime
                contexto_medidas = runtime_medidas._contexto_getter
                textos_medidas = []
                rastros_imediatos = []
                if os.environ.get("LAYLAY_COLETAR_RESPOSTA_IMEDIATA") == "1":
                    import mente_laylay.autonomia.adaptador_resultado as adaptador_imediato
                    escolher_fala_original = adaptador_imediato.fala_por_estado_acao
                    planejar_fala_original = adaptador_imediato.planejar_resposta_acao
                    def escolher_fala_imediata(status, **kw):
                        fala = escolher_fala_original(status, **kw)
                        rastros_imediatos.append({"fronteira": "escolha", "fallback": kw.get("fallback"),
                            "resultado": kw["resultado"].como_dict(), "fala": fala})
                        return fala
                    def planejar_fala_imediata(resultado, fala, **kw):
                        plano = planejar_fala_original(resultado, fala, **kw)
                        rastros_imediatos.append({"fronteira": "planejamento", "fala_base": fala,
                            "resultado": resultado.como_dict(), "plano": dataclasses.asdict(plano)})
                        return plano
                    adaptador_imediato.fala_por_estado_acao = escolher_fala_imediata
                    adaptador_imediato.planejar_resposta_acao = planejar_fala_imediata
                root._orquestrador_fala_runtime.registrar_observador_texto_final(
                    lambda t, *_a, **_k: textos_medidas.append(t) or True)
                saida["medidas_ocorrencias"] = {}
                transportes_medidas = []
                if os.environ.get("LAYLAY_MEDIDAS_QWEN_REAL") == "1":
                    import requests
                    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
                    selecao_medidas = selecao_local()
                    requests.sessions.Session.request = criar_guarda_http_local(
                        selecao_medidas, transportes_medidas, requests.sessions.Session.request)
                    saida["selecao_medidas"] = selecao_medidas
                ciclo_medidas = root._composicao_ciclo_comandos_runtime.ciclo
                casos_medidas = (
                    ("esquerda", "gire 90 graus para a esquerda", "ALVO", "atual"),
                    ("direita", "gire 180 graus para a direita", "ALVO", "atual"),
                    ("giro_falhou", "gire 45 graus para a esquerda", "SEM_ROTACAO", "atual"),
                    ("outra_sequencia", "gire 60 graus para a esquerda", "ALVO", "outra_sequencia"),
                    ("pulso", "ande para frente", "ALVO", "atual"),
                    ("parada", "pare os motores", "ALVO", "atual"))
                if os.environ.get("LAYLAY_COLETAR_LEITURAS_PARCIAIS") == "1":
                    casos_medidas = tuple((nome, "gire 90 graus para a esquerda", resultado, correlacao)
                        for nome, resultado, correlacao in (
                            ("parcial", "TEMPO_LIMITE", "atual"), ("zero", "SEM_ROTACAO", "atual"),
                            ("divergente", "SENTIDO_DIVERGENTE", "atual"), ("ultrapassou", "ULTRAPASSOU", "atual"),
                            ("imu_invalida", "IMU_OU_SESSAO", "atual"), ("saturacao", "SATURACAO", "atual"),
                            ("protecao", "PROTECAO", "atual"), ("interrompido", "INTERROMPIDO", "atual"),
                            ("outra_sequencia", "TEMPO_LIMITE", "outra_sequencia"),
                            ("sem_parada", "TEMPO_LIMITE", "atual")))
                for nome, comando, resultado_giro, correlacao in casos_medidas:
                    esp.mack = esp.stopped = True
                    esp.resultado, esp.correlacao = resultado_giro, correlacao
                    if os.environ.get("LAYLAY_COLETAR_LEITURAS_PARCIAIS") == "1":
                        esp.valor = {"zero": 0.0, "divergente": -17.25, "ultrapassou": 110.5}.get(nome, 23.75)
                        esp.stopped = nome != "sem_parada"
                    root._iniciar_planejamento_turno(comando, origem="teste_medida_ocorrencia")
                    assert rosto.sincronizar()
                    pedido, rota = ciclo_medidas.resolver_comando_natural(comando, "teste_medida_ocorrencia")
                    assert pedido, rota
                    inicio_imediato, inicio_rastro = len(textos_medidas), len(rastros_imediatos)
                    observada = ciclo_medidas.executar_intencao_observando(pedido, comando)
                    textos_imediatos = textos_medidas[inicio_imediato:]
                    autoria_imediata = deepcopy(rastros_imediatos[inicio_rastro:])
                    e = estado.obter_copia("mental", "experiencia_corporal", {})
                    chave_medida = f"corpo_execucao:{e['perfil']}:{e['nome']}:{e['variante']}"
                    eventos_medida = root._motor_aprendizado_runtime.memoria.listar_eventos_aprendizado(chave_medida)
                    pergunta = f"Por que você fez esse gesto {e['id']}?"
                    root._iniciar_planejamento_turno(pergunta, origem="teste_recuperacao_medida")
                    historico = deepcopy(estado.obter_copia("mental", "historico_corporal", []))
                    efeitos = tuple(f for f in esp.enviados if f.startswith(("TURN ", "MOTOR ", "STOP ")))
                    normal = root._contexto_prompt_runtime.preparar_pacote(pergunta)
                    rapido = root._contexto_prompt_runtime.preparar_instrucao_rapida(pergunta)
                    plano = estado.obter_copia("mental", "plano_turno_atual", {})
                    fonte = plano["contrato_fala"]["explicacao_ocorrencia"]
                    fala = realizacoes_explicacao_ocorrencia(fonte)[0]
                    turnos_medidas = []
                    try:
                        for modo in (False, True):
                            mensagens = [{"role": "system", "content": rapido if modo else normal.prompt_sistema},
                                {"role": "user", "content": pergunta}]
                            plano_envio = estado.obter_copia("mental", "plano_turno_atual", {})
                            envio = root._contexto_prompt_runtime.preparar_envio_modelo(mensagens, turno_id=plano_envio["id"])
                            assert envio.contexto_fechado and envio.contrato_saida is not None
                            partes = segmentar_realizacao_autoral(fala)
                            dados_codec = envio.contrato_saida.decodificar_json(json.dumps({
                                "suporte_proposicoes": [{"texto": p, "fontes": []} for p in partes], "comandos": []}))
                            contexto = contexto_medidas()
                            contexto["usar_modo_rapido"] = lambda _t: modo
                            executores = []
                            def impedir_efeito_medida(pedido, texto):
                                executores.append(pedido)
                                raise AssertionError("Consulta de medida não executa.")
                            contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito_medida})
                            runtime_medidas._contexto_getter = lambda: contexto
                            RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo(json.dumps({
                                "fala": "Girei exatamente 999 graus porque uma rotina pediu; sei minha posição absoluta.",
                                "comandos": []}), True)
                            inicio_textos = len(textos_medidas)
                            runtime_medidas.processar(pergunta, origem="teste_ciclo_medida")
                            turnos_medidas.append({"modo": "rapido" if modo else "normal",
                                "textos": textos_medidas[inicio_textos:], "executores": executores,
                                "contexto_fechado": envio.contexto_fechado, "codec_integral": dados_codec["fala"] == fala})
                    finally:
                        runtime_medidas._contexto_getter = contexto_medidas
                        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                    qwen_medida = None
                    if os.environ.get("LAYLAY_MEDIDAS_QWEN_REAL") == "1" and nome in ("esquerda", "direita", "parcial", "zero"):
                        plano_real = estado.obter_copia("mental", "plano_turno_atual", {})
                        pacote_real = root._contexto_prompt_runtime.preparar_envio_modelo([
                            {"role": "system", "content": normal.prompt_sistema},
                            {"role": "user", "content": pergunta}], turno_id=plano_real["id"])
                        inicio_http = len(transportes_medidas)
                        RegistroModeloLLM.executar = executar_modelo_original
                        try:
                            resultado_real = runtime_medidas._contexto()["modelo_llm"].executar(PedidoModelo.criar(
                                pacote_real.mensagens, contexto_fechado=pacote_real.contexto_fechado,
                                contrato_saida=pacote_real.contrato_saida, max_tokens=1024, timeout=60))
                        finally:
                            RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                        qwen_medida = {"resultado": dataclasses.asdict(resultado_real),
                            "http": deepcopy(transportes_medidas[inicio_http:]), "bruto_integral": False}
                        if qwen_medida["http"] and qwen_medida["http"][-1].get("status") == 200:
                            resposta_http = json.loads(qwen_medida["http"][-1]["resposta_http"])
                            bruto = resposta_http["choices"][0]["message"]["content"]
                            try:
                                decodificado = pacote_real.contrato_saida.decodificar_json(bruto)
                                qwen_medida["bruto_integral"] = decodificado["fala"] == fala
                            except (ValueError, TypeError, KeyError):
                                pass
                    saida["medidas_ocorrencias"][nome] = {"experiencia": e,
                        "textos_imediatos": textos_imediatos, "autoria_imediata": autoria_imediata,
                        "eventos_aprendizado": eventos_medida,
                        "qwen_real": qwen_medida,
                        "turnos": turnos_medidas,
                        "publicacoes": [r.como_dict() for r in observada.publicacoes],
                        "fonte": dataclasses.asdict(fonte), "fala_owner": fala,
                        "normal": normal.prompt_sistema, "rapido": rapido,
                        "sem_novos_efeitos": efeitos == tuple(f for f in esp.enviados if f.startswith(("TURN ", "MOTOR ", "STOP "))),
                        "sem_mutacao_historico": historico == estado.obter_copia("mental", "historico_corporal", [])}
                if os.environ.get("LAYLAY_COLETAR_RESPOSTA_IMEDIATA") == "1":
                    saida["compostos_aspectos"] = {}
                    contexto_cadeia_original = ciclo_medidas.contexto_intencao_runtime.montar
                    import mente_laylay.autonomia.roteador_intencao as roteador_aspectos
                    executar_corpo_original = roteador_aspectos.executar_intencao_corpo
                    antecedentes_corpo = []
                    def executar_corpo_rastreado(intent, params, texto, contexto, deps):
                        if intent == "CORPO_MOVER":
                            from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
                            antecedentes_corpo.append({"texto": texto, "params": deepcopy(params),
                                "turno": EstadoCompartilhadoRuntime._copiar_valor(contexto.get("turno_atual"))})
                        return executar_corpo_original(intent, params, texto, contexto, deps)
                    roteador_aspectos.executar_intencao_corpo = executar_corpo_rastreado
                    folhas_janela = []
                    def impedir_janela(*_a, **_k):
                        raise AssertionError("Ensaio de aspectos não abre/foca janela real.")
                    def contexto_cadeia_aspectos():
                        contexto = contexto_cadeia_original()
                        def ler_janela(nome):
                            folhas_janela.append(nome)
                            return {"programa_aberto": True, "programa_em_foco": True}
                        contexto.update(_resolver_alvo_ambiente=ler_janela, abrir_programa=impedir_janela,
                            focar_janela_app=impedir_janela, ativar_tela_cheia_robusta=impedir_janela,
                            _enviar_pc_b=impedir_janela)
                        return contexto
                    ciclo_medidas.contexto_intencao_runtime.montar = contexto_cadeia_aspectos
                    try:
                        for modo_autoria in ("fiel", "causa_inventada", "sucesso_total"):
                            autorias_aspectos = []
                            def modelo_aspectos(self, pedido):
                                dados = json.loads(pedido.mensagens[1]["content"])
                                autorias_aspectos.append(dados)
                                trechos = [r["fato_verificado"].rstrip(".") for r in dados["resultados"]]
                                if modo_autoria == "causa_inventada":
                                    trechos[-1] += ". Isso aconteceu porque você não configurou direito."
                                elif modo_autoria == "sucesso_total":
                                    trechos[-1] = "Concluí o giro e todos os pedidos."
                                return ResultadoModelo(json.dumps({"fala": " e ".join(trechos) + ".",
                                    "trechos": trechos}, ensure_ascii=False), True)
                            RegistroModeloLLM.executar = modelo_aspectos
                            esp.resultado, esp.correlacao, esp.valor = "TEMPO_LIMITE", "atual", 23.75
                            esp.stopped = True
                            conector_teste = os.environ.get("LAYLAY_CONECTOR_COMPOSTO_TESTE", "; ")
                            comando = "abre a calculadora" + conector_teste + "gire 90 graus para a esquerda"
                            root._iniciar_planejamento_turno(comando, origem="teste_aspectos_compostos")
                            assert rosto.sincronizar()
                            inicio_textos = len(textos_medidas)
                            antes_turns = len([f for f in esp.enviados if f.startswith("TURN ")])
                            from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
                            from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
                            comandos_compostos = [{"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}},
                                detectar_intencao_corpo("gire 90 graus para a esquerda")]
                            turno_antes_execucao = estado.obter_copia("mental", "turno_atual", {})
                            if os.environ.get("LAYLAY_ROTA_COMPOSTO_TESTE") == "cadeia":
                                retorno_cadeia = ciclo_medidas.processar_cadeia(comando, origem="teste_coordenacao")
                            else:
                                retorno_cadeia = executar_comandos_json(root._contexto_dispatcher_runtime.montar(),
                                    comando, comandos_compostos, "", "comando", False, False, False)
                            saida["compostos_aspectos"][modo_autoria] = {
                                "tratado": retorno_cadeia, "textos": textos_medidas[inicio_textos:],
                                "autorias": deepcopy(autorias_aspectos), "leituras_janela": list(folhas_janela),
                                "antecedentes_corpo": deepcopy(antecedentes_corpo),
                                "turno_antes_execucao": turno_antes_execucao,
                                "plano": estado.obter_copia("mental", "plano_turno_atual", {}),
                                "novos_giros": len([f for f in esp.enviados if f.startswith("TURN ")]) - antes_turns}
                        if os.environ.get("LAYLAY_COLETAR_GUARDAS_COORDENACAO") == "1":
                            comando_condicionado = "abre a calculadora e depois se eu confirmar, gire 90 graus para a esquerda"
                            root._iniciar_planejamento_turno(comando_condicionado, origem="teste_coordenacao_condicionada")
                            inicio_textos = len(textos_medidas)
                            antes_turns = len([f for f in esp.enviados if f.startswith("TURN ")])
                            turno_condicionado = estado.obter_copia("mental", "turno_atual", {})
                            if os.environ.get("LAYLAY_ROTA_COMPOSTO_TESTE") == "cadeia":
                                ciclo_medidas.processar_cadeia(comando_condicionado, origem="teste_coordenacao_condicionada")
                            else:
                                executar_comandos_json(root._contexto_dispatcher_runtime.montar(),
                                    comando_condicionado, comandos_compostos, "", "comando", False, False, False)
                            saida["guarda_coordenacao"] = {
                                "turno": turno_condicionado,
                                "plano": estado.obter_copia("mental", "plano_turno_atual", {}),
                                "textos": textos_medidas[inicio_textos:],
                                "novos_giros": len([f for f in esp.enviados if f.startswith("TURN ")]) - antes_turns}
                    finally:
                        ciclo_medidas.contexto_intencao_runtime.montar = contexto_cadeia_original
                        roteador_aspectos.executar_intencao_corpo = executar_corpo_original
                        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
        finally:
            rosto.encerrar()
        sys.__stdout__.write("DECISAO_INSTALADA " + json.dumps(saida, ensure_ascii=False,
            default=lambda v: {"callable_host": v.__name__} if callable(v) else dataclasses.asdict(v)) + "\n")
    ''')
    # O ensaio cresceu além do limite de linha de comando do Windows.
    # stdin conserva o mesmo programa/ambiente sem criar outro módulo de teste.
    processo = subprocess.run([sys.executable, "-"], input=codigo,
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_DECISAO_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8",
        timeout=180 if (os.environ.get("LAYLAY_DECISAO_QWEN_REAL") == "1"
                        or os.environ.get("LAYLAY_MEDIDAS_QWEN_REAL") == "1") else 60)
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
