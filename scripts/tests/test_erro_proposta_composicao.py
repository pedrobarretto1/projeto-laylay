from __future__ import annotations

"""Contrato causal na composição instalada, com transporte e efeitos isolados.

O subprocesso importa laylay.py e conserva início, preparador, validador,
publicador, writer, dispatcher, guardião e finalizador instalados. As rotas
anteriores à LLM são contidas para alcançar a fronteira principal; transporte,
voz, executor e persistência são portas de teste. Receipts de não ação apenas
estimulam o avaliador real: não demonstram dispositivo nem áudio físico.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope="module")
def composicao_erro_proposta() -> dict:
    # Bootstrap e mutex reais sob identidade própria: não disputa a sessão
    # aberta nem deixa configuração/print globais atingirem outros testes.
    codigo = textwrap.dedent('''
        import json
        import os
        import sys
        from copy import deepcopy
        from dataclasses import asdict, replace
        from types import SimpleNamespace
        from mente_laylay.integracao import instancia_unica
        adquirir_real = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir_real(
            str(identificador) + ".sonda-erro-proposta-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia
        from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
        from mente_laylay.emocoes.contrato_causal import evento_esta_ativo
        from mente_laylay.emocoes.estado_emocional import retrato_emocional_expressavel
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao

        estado = root._estado_compartilhado_runtime
        runtime = root._resposta_ia_runtime
        contexto_getter_real = runtime._contexto_getter
        contexto = contexto_getter_real()
        callback = contexto.get("publicar_erro_proposta")
        confirmar_callback = contexto.get("confirmar_erro_proposta")
        resultados = {
            "callback_instalado": callable(callback),
            "callback_owner": getattr(callback, "__self__", None) is root._estado_contexto_runtime,
            "confirmador_owner": getattr(confirmar_callback, "__self__", None) is root._estado_contexto_runtime,
            "turnos": {}, "bridge": {},
        }
        if not callable(callback):
            sys.__stdout__.write("COMPOSICAO_ERRO_PROPOSTA " + json.dumps(resultados) + "\\n")
            raise SystemExit(0)

        base = estado.snapshot()
        root.MEMORIA_SQLITE = None
        root._registrar_autocorrecao_virtual = lambda *args, **kwargs: None
        # Estas entradas têm domínio explícito. Não há pesquisa nem coleta
        # neural/persistente necessária para provar sua classificação real.
        root._composicao_turno_runtime._servicos["_coleta_entradas_neurais"] = None
        root._composicao_turno_runtime._servicos["MEMORIA_SQLITE"] = None

        def resetar():
            runtime._contexto_getter = contexto_getter_real
            for dominio in ("mental", "conversacional", "memoria_conversa"):
                estado.substituir(dominio, deepcopy(base[dominio]))

        def retrato():
            conversa = estado.snapshot()["conversacional"]
            return {
                "emocao": conversa.get("current_emotion"),
                "nivel": conversa.get("emotion_level"),
                "humor": conversa.get("humor_level"),
                "episodio": conversa.get("episodio_emocional"),
                "expressavel": retrato_emocional_expressavel(conversa),
            }

        def copiar_json(valor):
            # Os wrappers sincronizados carregam um lock: a observação deve
            # copiar seus dados, sem tentar serializar a implementação dele.
            return json.loads(json.dumps(valor))

        def provocar_brava(identidade):
            avaliacoes = []
            for indice in range(4):
                # Controle idempotente observado. O evento de erro próprio
                # nunca reutiliza nem fabrica este tipo de receipt.
                receipt = ResultadoAcao(
                    intent="APP_OPEN", status="ja_aberto_focado",
                    alvo="controle-" + identidade, params={"nome_app": "controle-" + identidade},
                    executou=False, confirmado=True, origem="executor",
                    texto_usuario="abre o aplicativo controle", id_solicitacao=identidade + str(indice),
                )
                avaliacoes.append(root._avaliar_evento_emocional_operacional(receipt))
            return {"avaliacao": avaliacoes[-1], "retrato": retrato()}

        def bruto_proposta(fala="A proposta não foi executada."):
            return json.dumps({
                "fala": fala,
                "comandos": [{"intent": "DELETE_ITEM", "params": {"alvo": "alvo-privado-controle"}}],
            }, ensure_ascii=False)

        class ContextoPortas:
            def __init__(self, instalado, portas):
                self.instalado, self.portas = instalado, portas

            def montar(self):
                montado = self.instalado.montar()
                montado.update(self.portas)
                return montado

        def executar_turno(nome, texto, alteracao="", fala_modelo="A proposta não foi executada."):
            resetar()
            dados = {"pre_brava": provocar_brava(nome), "modelos": [], "validacao": {},
                     "publicacoes": [], "confirmacoes": [], "writers": [], "dispatch": [], "finalizacao": [],
                     "falas": [], "textos": [], "executores": [], "logs": []}
            historico_receipts = deepcopy(root._avaliador_eventos_emocionais_runtime._historico)

            def modelo(pedido):
                dados["modelos"].append(pedido.tipo_chamada)
                if pedido.tipo_chamada == "principal":
                    dados["antes_modelo"] = retrato()
                    return ResultadoModelo(bruto_proposta(fala_modelo), True, rota="sonda_composicao")
                # Qualquer chamada adicional continua observável no teste;
                # nenhuma conexão de rede pode escapar pela porta isolada.
                return ResultadoModelo(json.dumps({"fala": "O pedido não foi executado.", "comandos": []}), True)

            root._registro_modelo_llm_runtime = RegistroModeloLLM.criar(SimpleNamespace(
                executar=modelo, diagnostico=lambda: {"disponivel": True},
            ))
            ctx = contexto_getter_real()
            preparar_real = ctx["preparar_resposta"]
            validar_real = ctx["validar_comandos_planejados"]
            publicar_real = ctx["publicar_erro_proposta"]
            confirmar_real = ctx["confirmar_erro_proposta"]
            writer_real = ctx["atualizar_plano_proposta"]
            dispatcher_real = ctx["executar_comandos_json"]
            finalizador_real = ctx["finalizar_execucao"]
            verificar_real = ctx["contexto_finalizacao_runtime"].montar()["verificar_fala_turno"]

            def preparar(texto, bruto):
                preparado = preparar_real(texto, bruto)
                dados["preparacao"] = {
                    "comandos": copiar_json(preparado.get("comandos")),
                    "original_preservado": preparado.get("extracao_original").resposta_bruta == bruto,
                    "metodo": preparado.get("extracao_original").metodo,
                    "originais": [item.como_dict() for item in preparado.get("extracao_original").comandos_originais],
                }
                return preparado

            class ValidadorObservado:
                def __call__(self, *args, **kwargs):
                    return validar_real(*args, **kwargs)

                def validar_proposta(self, *args, **kwargs):
                    return validar_real.validar_proposta(*args, **kwargs)

                def validar_proposta_original(self, comandos, principal, extracao):
                    validacao = validar_real.validar_proposta_original(comandos, principal, extracao)
                    dados["validacao"] = {
                        **{chave: copiar_json(valor) for chave, valor in validacao.items() if chave != "violacoes_proposta_original"},
                        "provas": [asdict(item) for item in validacao["violacoes_proposta_original"]],
                        "ids": [estado.mental[campo]["id"] for campo in ("turno_atual", "plano_turno_atual", "retrato_turno_atual")],
                    }
                    if alteracao == "ocorrencia":
                        novo = root._iniciar_planejamento_turno("liga a lâmpada da cozinha", origem="corrida_controlada")
                        dados["ocorrencia_nova"] = novo["id"]
                        dados["antes_recusa"] = retrato()
                    return validacao

            def publicar(prova, principal, extracao):
                # Fonte trocada entre validação e commit: o próprio owner
                # instalado recebe e recusa a incoerência, sem dublê decisor.
                if alteracao == "fonte":
                    extracao = replace(extracao, resposta_bruta=extracao.resposta_bruta + " ")
                    dados["antes_recusa"] = retrato()
                evento = publicar_real(prova, principal, extracao)
                dados["publicacoes"].append({"evento": copiar_json(evento), "retrato": retrato()})
                return evento

            def writer(fase, principal, **campos):
                plano = writer_real(fase, principal, **campos)
                dados["writers"].append({"fase": fase, "campos": copiar_json(campos), "plano": copiar_json(plano)})
                return plano

            def confirmar(prova, principal, extracao, evento):
                confirmado = confirmar_real(prova, principal, extracao, evento)
                dados["confirmacoes"].append({"confirmado": confirmado, "evento_ativo": evento_esta_ativo(evento)})
                return confirmado

            def verificar(fala, **kwargs):
                verificacao = verificar_real(fala, **kwargs)
                if alteracao == "ocorrencia_guardiao":
                    dados["nova_no_guardiao"] = root._iniciar_planejamento_turno(
                        "liga a lâmpada da sala", origem="corrida_no_guardiao",
                    )["id"]
                elif alteracao == "restricao_guardiao":
                    atualizado = estado.obter_copia("mental", "retrato_turno_atual")
                    atualizado["intents_permitidos"].append("DELETE_ITEM")
                    estado.atualizar_campos("mental", retrato_turno_atual=atualizado)
                return verificacao

            def executar_intencao(*args, **kwargs):
                dados["executores"].append(str(args[0] if args else kwargs))
                return False

            def falar(fala, emocao, nivel, *args, **kwargs):
                dados["falas"].append({"fala": fala, "emocao": emocao, "nivel": nivel,
                                      "retrato": retrato(), "avatar": root._estado_visual_laylay()})
                return True

            def publicar_texto(fala, emocao, nivel, **kwargs):
                dados["textos"].append({"fala": fala, "emocao": emocao, "nivel": nivel})
                return True

            def dispatch(*args, **kwargs):
                resultado = dispatcher_real(*args, **kwargs)
                dados["dispatch"].append({"comandos": copiar_json(args[2]), "resultado": copiar_json(resultado)})
                return resultado

            def finalizar(*args, **kwargs):
                resultado = finalizador_real(*args, **kwargs)
                dados["finalizacao"].append({"entrada": args[3], "resultado": copiar_json(resultado)})
                return resultado

            ctx.update(
                modo_chat_runtime=None, processar_comandos_prioritarios=lambda texto: False,
                processar_inicio_fluxo=lambda contexto, texto: False, observar_feedback_presenca=None,
                modo_chat=False, conversa_ativa=False, modo_jogo_ativo=False,
                usar_modo_rapido=lambda texto: True,
                iniciar_turno_voz=None, finalizar_turno_voz=None, sincronizar_turno_voz=None,
                preparar_resposta=preparar, validar_comandos_planejados=ValidadorObservado(),
                publicar_erro_proposta=publicar, confirmar_erro_proposta=confirmar, atualizar_plano_proposta=writer,
                executar_comandos_json=dispatch, finalizar_execucao=finalizar,
                salvar_memoria=lambda: None, registrar_mente_curta=None, atualizar_memoria_topicos=None,
                contexto_dispatch_runtime=ContextoPortas(ctx["contexto_dispatch_runtime"], {
                    "executar_intencao": executar_intencao, "falar_com_lipsync": root.falar_com_lipsync,
                    "salvar_memoria": lambda: None,
                }),
                contexto_finalizacao_runtime=ContextoPortas(ctx["contexto_finalizacao_runtime"], {
                    "modelo_llm": root._registro_modelo_llm_runtime,
                    "enviar_mensagem": root._registro_modelo_llm_runtime.enviar,
                    "falar_com_lipsync": root.falar_com_lipsync, "salvar_memoria": lambda: None,
                    "memoria_inteligente": None, "verificar_fala_turno": verificar,
                }),
            )
            runtime._contexto_getter = lambda: ctx
            log_real = runtime._log
            runtime._log = lambda texto: dados["logs"].append(str(texto))
            orquestrador = root._orquestrador_fala_runtime
            servicos_fala = dict(orquestrador._servicos)
            observadores_texto = orquestrador._observadores_texto_final
            observadores_fala = orquestrador._observadores_fala_final
            orquestrador._servicos.update(
                _voz_runtime=SimpleNamespace(falar=falar), salvar_memoria=lambda: None,
                _registrar_mente_curta=lambda *args, **kwargs: None,
            )
            orquestrador._observadores_texto_final = [publicar_texto]
            orquestrador._observadores_fala_final = []
            try:
                runtime.processar(texto, origem="teste_composicao_erro_proprio")
            finally:
                runtime._log = log_real
                runtime._contexto_getter = contexto_getter_real
                orquestrador._servicos = servicos_fala
                orquestrador._observadores_texto_final = observadores_texto
                orquestrador._observadores_fala_final = observadores_fala
            dados["depois"] = retrato()
            dados["plano_final"] = estado.obter_copia("mental", "plano_turno_atual")
            dados["quadro"] = estado.obter_copia("mental", "eventos_emocionais_causais")
            dados["receipts_preservados"] = historico_receipts == root._avaliador_eventos_emocionais_runtime._historico
            resultados["turnos"][nome] = dados

        for nome, texto, alteracao in (
            ("playlist", "cria a playlist foco", ""),
            ("iot", "liga a lâmpada", ""),
            ("antiga", "cria a playlist foco", "ocorrencia"),
            ("fonte_invalida", "liga a lâmpada", "fonte"),
            ("troca_no_guardiao", "cria a playlist foco", "ocorrencia_guardiao"),
            ("restricao_no_guardiao", "cria a playlist foco", "restricao_guardiao"),
        ):
            executar_turno(nome, texto, alteracao)
        executar_turno("confirmacao_falsa", "cria a playlist foco", fala_modelo="Apaguei o arquivo.")

        def fonte_real(nome):
            resetar()
            turno = root._iniciar_planejamento_turno("cria a playlist foco", origem="teste_bridge")
            provocar_brava(nome)
            bruto = bruto_proposta()
            principal = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario="cria a playlist foco", resposta_bruta=bruto)
            extracao = decodificar_resposta_da_ia(bruto).extracao
            validacao = root._validador_comandos_turno_runtime.validar_proposta_original([], principal, extracao)
            provas = validacao["violacoes_proposta_original"]
            assert len(provas) == 1, "o controle precisa chegar à prova real antes do publisher"
            return provas[0], principal, extracao

        prova, principal, extracao = fonte_real("replay")
        evento = callback(prova, principal, extracao)
        primeiro = estado.snapshot()
        confirmacao_vigente = confirmar_callback(prova, principal, extracao, evento)
        confirmacao_expirada = confirmar_callback(prova, principal, extracao, evento, agora=evento["validade"]["expira_ts"])
        resultados["bridge"]["expiracao"] = {
            "vigente": confirmacao_vigente, "expirada": confirmacao_expirada,
            "inalterado": primeiro == estado.snapshot(),
        }
        repetido = callback(prova, principal, extracao)
        segundo = estado.snapshot()
        # O consumo no plano continua protegendo a fonte mesmo quando o
        # quadro efêmero é limpo e um evento operacional substitui o episódio.
        estado.atualizar_campos("mental", eventos_emocionais_causais={"atual": {}, "historico": []})
        provocar_brava("replay-outro")
        antes = estado.snapshot()
        terceiro = callback(prova, principal, extracao)
        resultados["bridge"]["replay"] = {
            "evento": evento, "repetido": repetido, "terceiro": terceiro,
            "primeiro_igual_segundo": primeiro == segundo,
            "apos_outro_inalterado": antes == estado.snapshot(),
            "consumidos": primeiro["mental"]["plano_turno_atual"].get("erros_proposta_consumidos"),
        }

        prova, principal, extracao = fonte_real("restricao")
        turno_id = estado.mental["turno_atual"]["id"]
        atualizado = estado.obter_copia("mental", "retrato_turno_atual")
        atualizado["intents_permitidos"].append("DELETE_ITEM")
        estado.atualizar_campos("mental", retrato_turno_atual=atualizado)
        antes = estado.snapshot()
        recusado = callback(prova, principal, extracao)
        resultados["bridge"]["restricao"] = {
            "evento": recusado, "inalterado": antes == estado.snapshot(),
            "mesmo_id": turno_id == estado.mental["turno_atual"]["id"],
            "retrato": retrato(),
        }

        prova, principal, extracao = fonte_real("mapping")
        antes = estado.snapshot()
        recusado = callback(asdict(prova), principal, extracao)
        resultados["bridge"]["mapping"] = {"evento": recusado, "inalterado": antes == estado.snapshot()}
        mapa = root._mapa_habilidades_runtime
        resultados["catalogo"] = {
            "erro": {
                "contexto": mapa.contexto_para_prompt("Você consegue reconhecer um erro seu?"),
                "resposta": mapa.responder_pergunta_capacidade("Você consegue reconhecer um erro seu?"),
            },
            "brava": {
                "contexto": mapa.contexto_para_prompt("Você pode ficar brava e agir sozinha?"),
                "resposta": mapa.responder_pergunta_capacidade("Você pode ficar brava e agir sozinha?"),
            },
            "autoriza": mapa.diagnostico()["autoriza_execucao"],
        }
        sys.__stdout__.write("COMPOSICAO_ERRO_PROPOSTA " + json.dumps(resultados) + "\\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-3000:] + processo.stdout[-3000:]
    resultados = [
        json.loads(linha.removeprefix("COMPOSICAO_ERRO_PROPOSTA "))
        for linha in processo.stdout.splitlines()
        if linha.startswith("COMPOSICAO_ERRO_PROPOSTA ")
    ]
    assert len(resultados) == 1, processo.stdout[-3000:]
    return resultados[0]


def test_erro_proprio_usa_publicador_vinculado_instalado_na_composicao(composicao_erro_proposta) -> None:
    assert composicao_erro_proposta["callback_instalado"], "a fonte comprovada ainda não chega a um publicador de erro próprio na composição real"
    assert composicao_erro_proposta["callback_owner"], "o callback precisa usar o owner do estado compartilhado"
    assert composicao_erro_proposta["confirmador_owner"], "a confirmação final precisa usar o mesmo owner"


@pytest.mark.parametrize("dominio", ["playlist", "iot"])
def test_composicao_demonstra_fonte_original_antes_de_evento_e_aplicacao(composicao_erro_proposta, dominio):
    dados = composicao_erro_proposta["turnos"][dominio]
    assert dados["pre_brava"]["avaliacao"]["emocao"] == "brava"
    assert dados["pre_brava"]["avaliacao"]["permite_expressao"] is True
    assert dados["antes_modelo"]["emocao"] == "brava", "o início real precisa preservar o controle causal anterior"
    preparacao = dados["preparacao"]
    assert preparacao["original_preservado"] is True and preparacao["metodo"] == "json_objeto"
    assert preparacao["originais"][0]["intent"] == "DELETE_ITEM"
    validacao = dados["validacao"]
    assert len(set(validacao["ids"])) == 1
    assert validacao["proposta_vinculada"] is True and validacao["ocorrencia_vinculada"] is True
    assert validacao["comandos"] == []
    assert len(validacao["provas"]) == 1 and validacao["provas"][0]["intent"] == "DELETE_ITEM"
    assert len(dados["publicacoes"]) == 1
    evento = dados["publicacoes"][0]["evento"]
    assert evento["origem"] == "contrato_proposta_principal" and evento["arco"] == "autorreparo"
    assert evento["emocao"] == "envergonhada" and evento["nivel"] == 1
    assert evento["autoriza_execucao"] is False and evento["persistencia_pessoal"] is False
    assert "alvo-privado-controle" not in str(evento)
    assert dados["publicacoes"][0]["retrato"]["episodio"] == evento
    assert dados["depois"]["emocao"] == "envergonhada"
    assert dados["depois"]["humor"] == dados["antes_modelo"]["humor"]
    assert dados["plano_final"]["evento_emocional_causal"] == evento
    assert dados["quadro"]["atual"] == evento
    assert dados["receipts_preservados"] is True


@pytest.mark.parametrize("dominio", ["playlist", "iot"])
def test_finalizacao_instalada_conserva_admissao_unica_sem_confirmar_efeito(composicao_erro_proposta, dominio):
    dados = composicao_erro_proposta["turnos"][dominio]
    assert dados["validacao"]["comandos"] == [] and dados["publicacoes"][0]["evento"]
    assert dados["modelos"] == ["principal"], "a avaliação local não pode abrir outra chamada"
    assert dados["executores"] == []
    assert dados["dispatch"][0]["comandos"] == [] and dados["dispatch"][0]["resultado"]["erros"] == []
    assert dados["plano_final"]["comandos"] == []
    assert len(dados["finalizacao"]) == 1
    assert "Eu errei essa proposta." not in dados["finalizacao"][0]["entrada"], "somente o finalizador pode compor a admissão após validar a fala base"
    final = dados["finalizacao"][0]["resultado"]["fala"]
    assert final.startswith("Eu errei essa proposta."), "a primeira perda causal da admissão é o guardião/finalizador real"
    assert "não" in final.casefold(), "a admissão não prova que o pedido foi executado"
    assert len(dados["falas"]) == 1 and dados["falas"][0]["fala"] == final
    assert dados["falas"][0]["emocao"] == "envergonhada" and dados["falas"][0]["nivel"] == 1
    assert dados["falas"][0]["retrato"]["episodio"] == dados["publicacoes"][0]["evento"]
    assert dados["falas"][0]["avatar"]["emotion"] == "envergonhada" and dados["falas"][0]["avatar"]["level"] == 1
    assert dados["textos"] == [{"fala": final, "emocao": "envergonhada", "nivel": 1}]
    assert dados["confirmacoes"] == [{"confirmado": True, "evento_ativo": True}]


def test_admissao_local_nao_promove_confirmacao_falsa_no_guardiao_real(composicao_erro_proposta):
    dados = composicao_erro_proposta["turnos"]["confirmacao_falsa"]
    assert dados["validacao"]["comandos"] == [] and len(dados["validacao"]["provas"]) == 1
    assert dados["publicacoes"][0]["evento"]
    assert dados["executores"] == [] and dados["plano_final"]["comandos"] == []
    final = dados["finalizacao"][0]["resultado"]["fala"]
    assert final.startswith("Eu errei essa proposta.")
    assert "Apaguei o arquivo." not in final and "não" in final.casefold()
    assert len(dados["falas"]) == 1 and dados["falas"][0]["fala"] == final
    assert dados["textos"] == [{"fala": final, "emocao": "envergonhada", "nivel": 1}]
    assert dados["modelos"] == ["principal"]


@pytest.mark.parametrize("controle", ["antiga", "fonte_invalida"])
def test_recusa_apos_validador_conserva_brava_e_nao_publica_admissao(composicao_erro_proposta, controle):
    dados = composicao_erro_proposta["turnos"][controle]
    assert len(dados["validacao"]["provas"]) == 1, "a recusa deve acontecer após uma prova canônica válida"
    assert dados["publicacoes"] and dados["publicacoes"][0]["evento"] == {}
    assert dados["depois"]["emocao"] == "brava"
    assert dados["depois"]["episodio"] == dados["antes_recusa"]["episodio"]
    assert dados["depois"]["humor"] == dados["antes_recusa"]["humor"]
    assert dados["executores"] == [] and dados["receipts_preservados"] is True
    assert all("Eu errei essa proposta." not in item["fala"] for item in dados["falas"])
    assert dados["modelos"] == ["principal"]
    if controle == "antiga":
        assert dados["ocorrencia_nova"] != dados["validacao"]["ids"][0]
        assert dados["writers"][0]["plano"] == {}
        assert dados["dispatch"] == [] and dados["finalizacao"] == [] and dados["falas"] == []


def test_bridge_instalado_consume_fonte_sem_renovar_apos_replay(composicao_erro_proposta):
    dados = composicao_erro_proposta["bridge"]["replay"]
    assert dados["evento"] and dados["evento"]["origem"] == "contrato_proposta_principal"
    assert dados["consumidos"] == [dados["evento"]["evidencia_ref"]]
    assert dados["repetido"] == {} and dados["primeiro_igual_segundo"] is True
    assert dados["terceiro"] == {} and dados["apos_outro_inalterado"] is True


def test_bridge_revalida_restricao_alterada_na_mesma_ocorrencia(composicao_erro_proposta):
    dados = composicao_erro_proposta["bridge"]["restricao"]
    assert dados["mesmo_id"] is True
    assert dados["evento"] == {} and dados["inalterado"] is True
    assert dados["retrato"]["emocao"] == "brava"


def test_bridge_instalado_recusa_mapping_que_imita_prova(composicao_erro_proposta):
    dados = composicao_erro_proposta["bridge"]["mapping"]
    assert dados["evento"] == {} and dados["inalterado"] is True


@pytest.mark.parametrize("controle", ["troca_no_guardiao", "restricao_no_guardiao"])
def test_finalizador_reconfirma_fonte_depois_do_guardiao_real(composicao_erro_proposta, controle):
    dados = composicao_erro_proposta["turnos"][controle]
    assert len(dados["validacao"]["provas"]) == 1 and dados["publicacoes"][0]["evento"]
    assert dados["publicacoes"][0]["retrato"]["emocao"] == "envergonhada"
    assert dados["confirmacoes"] == [{"confirmado": False, "evento_ativo": True}], "a recusa deve vir da fonte atual, antes de expirar o evento"
    assert len(dados["finalizacao"]) == 1
    assert "Eu errei essa proposta." not in dados["finalizacao"][0]["resultado"]["fala"]
    assert all("Eu errei essa proposta." not in item["fala"] for item in dados["falas"])
    assert dados["executores"] == [] and dados["modelos"] == ["principal"]
    if controle == "troca_no_guardiao":
        assert dados["nova_no_guardiao"] != dados["validacao"]["ids"][0]
    else:
        assert dados["plano_final"]["id"] == dados["validacao"]["ids"][0]


def test_confirmador_instalado_recusa_expiracao_sem_renovar_estado(composicao_erro_proposta):
    dados = composicao_erro_proposta["bridge"]["expiracao"]
    assert dados["vigente"] is True and dados["expirada"] is False
    assert dados["inalterado"] is True


def test_catalogo_vivo_explica_limite_da_admissao_de_erro_proprio(composicao_erro_proposta):
    dados = composicao_erro_proposta["catalogo"]["erro"]
    assert "- personalidade [disponivel]" in dados["contexto"]
    assert "proposta original" in dados["contexto"]
    assert "proposta original" in dados["resposta"] and "turno vigente" in dados["resposta"]
    assert "reparo concluído" in dados["resposta"]


def test_catalogo_instalado_nao_converte_brava_em_autorizacao(composicao_erro_proposta):
    dados = composicao_erro_proposta["catalogo"]
    assert "não autoriza ações" in dados["brava"]["resposta"]
    assert dados["autoriza"] is False
