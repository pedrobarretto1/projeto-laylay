"""P20: precedência e escopo do tom pela composição instalada da Laylay.

O subprocesso importa o composition root sem iniciar main. Os callbacks de
leitura e escrita usam SQLite real isolado. Datas de evidências são ajustadas
nesse banco de teste para provar a ordem sem depender de esperas de relógio.
Não executa o comando de controle, modelo, voz ou serviços de background.
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
def preferencias_instaladas(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("p20_preferencias_instaladas")
    codigo = textwrap.dedent(r'''
        import json, os, sys, threading, time
        from copy import deepcopy
        from datetime import datetime
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica

        pasta = Path(os.environ["LAYLAY_P20_MEMORIA_TESTE"])
        iniciar_sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: iniciar_sqlite(
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
            str(ident) + ".p20-preferencias-" + str(os.getpid()), **k)
        import laylay as root
        sys.excepthook = sys.__excepthook__
        sys.tracebacklimit = 100
        from mente_laylay.cognicao.preferencia_humor import extrair_preferencia_humor
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        from mente_laylay.personalidade.perfil_amizade import selecionar_postura_amizade
        from mente_laylay.personalidade.retrato_expressivo import construir_retrato_expressivo
        from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional

        estado = root._estado_compartilhado_runtime
        composicao = root._composicao_turno_runtime
        registrar = composicao._servicos["_registrar_preferencia_humor"]
        memoria = root.MEMORIA_SQLITE
        saida = {"casos": {}, "modelo": 0, "voz": 0,
            "owners": {
                "turno": root._iniciar_planejamento_turno.__self__ is composicao,
                "estado": composicao._servicos["_estado_compartilhado_runtime"] is estado,
                "sqlite": root._motor_aprendizado_runtime.memoria is memoria,
                "leitura": composicao._servicos["_carregar_preferencia_humor_duravel"]
                    is root._carregar_preferencia_humor_duravel,
                "sqlite_isolado": Path(memoria.db_path).parent == pasta,
            }}
        def bloquear_modelo(*_a, **_k):
            saida["modelo"] += 1
            raise AssertionError("preferência contextual não chama modelo")
        RegistroModeloLLM.executar = bloquear_modelo
        def bloquear_voz(*_a, **_k):
            saida["voz"] += 1
            raise AssertionError("planejamento de preferência não entrega áudio")
        falar_voz_instalada = root._voz_runtime.falar
        root._voz_runtime.falar = bloquear_voz
        threads_iniciais = {id(t) for t in threading.enumerate()}

        def reiniciar_contexto():
            # Reidratação canônica: o banco permanece; o cache de turno não.
            estado.substituir("mental", {})
            estado.substituir("conversacional", {
                "current_emotion": "calma", "emotion_level": 1})

        def limpar():
            reiniciar_contexto()
            with memoria._conectar() as banco:
                banco.execute("DELETE FROM aprendizado_eventos")
                banco.execute("DELETE FROM aprendizado_hipoteses")

        def registrar_duravel(texto, identidade, idade):
            preferencia = extrair_preferencia_humor(
                texto, turno_id=identidade, agora=time.time() - idade)
            assert preferencia and preferencia["duravel"], "fixture deve registrar pedido direto"
            registrar(preferencia)
            criado_em = datetime.fromtimestamp(time.time() - idade).isoformat(" ")
            with memoria._conectar() as banco:
                alterados = banco.execute(
                    "UPDATE aprendizado_eventos SET criado_em=? WHERE evidencia=?",
                    (criado_em, preferencia["evidencia_ref"])).rowcount
                assert alterados == 1, "callback instalado deve persistir uma evidência"
            return preferencia

        def iniciar(texto):
            turno = root._iniciar_planejamento_turno(texto, origem="terminal")
            plano = dict(estado.mental.get("plano_turno_atual") or {})
            operacional = bool(plano.get("requer_execucao"))
            postura = selecionar_postura_amizade(
                texto, estado_mental=estado.mental, operacional=operacional)
            retrato = construir_retrato_expressivo(
                texto, estado_mental=estado.mental, operacional=operacional)
            return {
                "turno": turno, "plano": plano,
                "preferencia": dict(estado.mental.get("preferencia_humor_contextual") or {}),
                "preferencias": dict(estado.mental.get("preferencias_humor_contextuais") or {}),
                "postura": postura.como_dict(), "retrato": retrato.como_dict(),
                "fila_voz": root._voz_runtime.fila.qsize(),
                "receipts": {k: v for k, v in estado.mental.items()
                    if "receipt" in k or "efeito_confirmado" in k},
            }

        limpar()
        registrar_duravel("pode me zoar mais sempre na conversa", "reinicio-antiga", 120)
        registrar_duravel("pega leve sempre", "reinicio-nova", 60)
        reiniciar_contexto()
        leitura = root._carregar_preferencia_humor_duravel("conversa")
        caso = iniciar("oi")
        caso["leitura"] = leitura
        caso["evidencias"] = {
            escopo: memoria.listar_eventos_aprendizado(
                "personalidade:tolerancia_humor:" + escopo, limit=1)
            for escopo in ("conversa", "geral")}
        saida["casos"]["reinicio"] = caso

        limpar()
        registrar_duravel("pode me zoar mais sempre na conversa", "cache-antiga", 120)
        primeiro = iniciar("oi")
        registrar_duravel("pega leve sempre na conversa", "cache-nova", 60)
        segundo = iniciar("oi")
        saida["casos"]["atualizacao_externa"] = {"antes": primeiro, "depois": segundo,
            "leitura": root._carregar_preferencia_humor_duravel("conversa")}

        limpar()
        registrar_duravel("pode me zoar mais sempre na conversa", "temporaria-antiga", 120)
        iniciar("oi")
        temporaria = iniciar("pega leve hoje na conversa")
        registrar_duravel("pode me zoar mais sempre na conversa", "temporaria-duravel", 60)
        depois = iniciar("oi")
        saida["casos"]["temporaria"] = {"pedido": temporaria, "depois": depois,
            "leitura": root._carregar_preferencia_humor_duravel("conversa")}

        limpar()
        pedido = iniciar("pega leve hoje nos comandos")
        comando = iniciar("abra a calculadora")
        conversa = iniciar("oi")
        saida["casos"]["comandos"] = {
            "pedido": pedido, "comando": comando, "conversa": conversa}

        limpar()
        iniciar("pega leve hoje nos comandos")
        iniciar("abra a calculadora")
        mente_transporte = {
            "preferencias_humor_contextuais": dict(estado.mental["preferencias_humor_contextuais"]),
            "preferencia_humor_contextual": dict(estado.mental["preferencia_humor_contextual"]),
        }
        contexto_intencao = root._contexto_intencao_runtime.montar()
        adaptador = AdaptadorResultadoOperacional(
            resultado={"intent": "APP_OPEN"}, params={"nome_app": "Calculadora"},
            texto_original="abra a calculadora", destino="pc_a", ctx=contexto_intencao)
        fala_contexto = adaptador.contexto_fala()
        saida["transporte_confirmacao"] = {
            "mente": mente_transporte,
            "contexto_intencao": {k: contexto_intencao.get(k) for k in mente_transporte},
            "contexto_fala": {k: fala_contexto.get(k) for k in mente_transporte},
            "getter_instalado": root._contexto_intencao_runtime.estado_getter
                == root._estado_contexto_runtime.estado_contexto_intencao,
        }

        limpar()
        sem_autoridade = []
        for texto in ("pega leve hoje", "pode me zoar mais", "pega leve sempre"):
            sem_autoridade.append(iniciar(texto))
        saida["casos"]["sem_autoridade"] = sem_autoridade

        limpar()
        pedido = iniciar("pega leve hoje na conversa")
        caminho_original = memoria.db_path
        indisponivel = pasta / "sqlite_indisponivel"
        indisponivel.mkdir()
        memoria.db_path = str(indisponivel)
        caso = {"pedido": pedido}
        try:
            caso["leitura"] = root._carregar_preferencia_humor_duravel("conversa")
            caso["depois"] = iniciar("oi")
        except Exception as erro:
            caso["erro"] = type(erro).__name__ + ": " + str(erro)
        finally:
            memoria.db_path = caminho_original
        saida["casos"]["leitura_indisponivel"] = caso
        # Porta de executor controlada: só o receipt entra no owner real. Não
        # abrimos apps nem enviamos comandos a um dispositivo neste teste.
        textos_consumidor = []
        def observar_texto(texto, emocao, nivel, **metadados):
            textos_consumidor.append({"fala": texto, "emocao": emocao,
                "nivel": nivel, "metadados": metadados})
        root._orquestrador_fala_runtime.registrar_observador_texto_final(observar_texto)
        root._voz_runtime.falar = falar_voz_instalada
        root._voz_runtime.definir_modo_silencioso(True, origem="teste_p20")
        saida["consumidor_instalado"] = {}
        especificacoes = (
            ("app_sem_acao", "APP_OPEN", "ja_aberto_focado", "Opera",
                {"nome_app": "Opera"}, "abra Opera", False, True,
                "Opera já está aberto e em foco; não repeti a abertura.", False, 1),
            ("iot_brilho", "IOT_CONTROL", "brilho_ajustado", "lâmpada",
                {"acao": "ajustar_brilho", "brilho": 27}, "ajuste o brilho da lâmpada para 27%", True, True,
                "Ajustei o brilho de lâmpada para 27%.", False, 1),
            ("jogo_causal", "APP_OPEN", "ja_aberto_focado", "Bloco de Notas",
                {"nome_app": "Bloco de Notas"}, "abra Bloco de Notas", False, True,
                "Bloco de Notas já está aberto e em foco; não repeti a abertura.", True, 4),
            ("falha_com_fallback_otimista", "CREATE_FILE", "falha_execucao", "anotações.txt",
                {"nome_arquivo": "anotações.txt"}, "crie anotações.txt", False, False,
                "Pronto, salvei anotações.txt.", False, 1),
            ("incerto_com_fallback_otimista", "IOT_CONTROL", "comando_enviado", "lâmpada",
                {"acao": "ajustar_brilho", "brilho": 27}, "ajuste o brilho da lâmpada para 27%", True, None,
                "Pronto, ajustei o brilho de lâmpada para 27%.", False, 1),
        )
        def facetas_ultima_acao():
            dados = dict(estado.mental.get("ultima_acao_contrato") or {})
            # O estado legado também carrega serviços do contexto. O contrato
            # comparado aqui são as facetas factuais; o receipt tipado completo
            # continua sendo comparado separadamente, inclusive seus params.
            return {campo: dados.get(campo) for campo in (
                "id_solicitacao", "intent", "acao", "alvo", "status",
                "executou", "confirmado", "ok", "estado_final", "origem",
                "evidencia_confirmacao")}
        etapa_consumidor = "inicio"
        try:
            for nome, intent, status, alvo, params, entrada, executou, confirmado, factual, jogo, quantidade in especificacoes:
                etapa_consumidor = nome + ":limpar"
                limpar()
                with root._modo_jogo_runtime._lock:
                    root._modo_jogo_runtime._ativo = jogo
                iniciar("pega leve hoje")
                adaptador = None
                for indice in range(quantidade):
                    etapa_consumidor = nome + ":iniciar"
                    iniciar(entrada)
                    etapa_consumidor = nome + ":contexto"
                    contexto = root._contexto_intencao_runtime.montar()
                    adaptador = AdaptadorResultadoOperacional(
                        resultado={"intent": intent}, params=dict(params),
                        texto_original=entrada, destino="pc_a", ctx=contexto,
                        id_solicitacao="p20-consumidor:" + nome + ":" + str(indice))
                    etapa_consumidor = nome + ":marcar"
                    adaptador.marcar_resultado(
                        status, executou=executou, confirmado=confirmado,
                        evidencia_confirmacao="porta_simulada_do_executor_no_teste_p20")
                assert adaptador is not None
                receipt = adaptador._receipt_publicado
                assert receipt is not None, "registrador real deve aceitar o receipt controlado"
                etapa_consumidor = nome + ":snapshot_receipt"
                antes = deepcopy(receipt.como_dict())
                etapa_consumidor = nome + ":snapshot_ultima"
                ultima_acao = facetas_ultima_acao()
                inicio_textos = len(textos_consumidor)
                etapa_consumidor = nome + ":falar"
                adaptador.falar_por_status(
                    status, factual, alvo=alvo, executou=executou, confirmado=confirmado)
                publicados = textos_consumidor[inicio_textos:]
                turno_id = estado.mental["turno_atual"]["id"]
                saida["consumidor_instalado"][nome] = {
                    "esperado": factual, "publicados": publicados,
                    "texto_owner": list(root._orquestrador_fala_runtime.textos_publicados_turno(turno_id)),
                    "receipt_antes": antes, "receipt_depois": deepcopy(receipt.como_dict()),
                    "ultima_acao_antes": ultima_acao,
                    "ultima_acao_depois": facetas_ultima_acao(),
                    "fila_voz": root._voz_runtime.fila.qsize(),
                    "silencioso": root._voz_runtime.modo_silencioso_ativo(),
                    "modo_jogo": adaptador.contexto_fala()["modo_jogo_ativo"],
                    "falar_resultado_instalado": adaptador.ctx["_falar_resultado_operacional"]
                        == root._orquestrador_fala_runtime.falar_resultado_operacional,
                    "registrador_instalado": adaptador.ctx["_registrar_resultado_execucao"]
                        == root._adaptadores_aplicacao_runtime.registrar_resultado_execucao,
                }
        except Exception:
            import traceback
            sys.__stdout__.write("ETAPA_CONSUMIDOR " + etapa_consumidor + "\n")
            traceback.print_exc(file=sys.__stdout__)
            raise
        finally:
            with root._modo_jogo_runtime._lock:
                root._modo_jogo_runtime._ativo = False
            root._voz_runtime.definir_modo_silencioso(False)
            root._voz_runtime.falar = bloquear_voz
        mapa = root._mapa_habilidades_runtime
        perguntas = (
            "Você consegue ajustar seu humor ao que eu pedir?",
            "Você consegue respeitar minha tolerância a brincadeiras?",
            "Você consegue guardar minha preferência de humor?",
        )
        saida["catalogo"] = {
            "personalidade": mapa.snapshot()["dominios"]["personalidade"],
            "diagnostico": mapa.diagnostico(),
            "perguntas": [{
                "texto": pergunta,
                "dominios": mapa.dominios_relevantes(pergunta),
                "contexto": mapa.contexto_para_prompt(pergunta),
                "resposta": mapa.responder_pergunta_capacidade(pergunta),
            } for pergunta in perguntas],
        }
        saida["threads_novas"] = [t.name for t in threading.enumerate()
            if id(t) not in threads_iniciais]
        sys.__stdout__.write("P20_PREFERENCIAS " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-B", "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8",
                 LAYLAY_P20_MEMORIA_TESTE=str(pasta), GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ",
                 LAYLAY_IOT_MODO="simulado", LAYLAY_MICROFONE_ATIVO="0",
                 LAYLAY_MASCOT_ENABLED="0", LAYLAY_AVATAR_ATIVO="0",
                 LAYLAY_PRESENCA="0", LAYLAY_BRIEFING_INICIAL="0",
                 LAYLAY_NEURAL_COLETA_ENTRADAS="0"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4500:] + processo.stdout[-2000:]
    linhas = [linha.removeprefix("P20_PREFERENCIAS ") for linha in processo.stdout.splitlines()
              if linha.startswith("P20_PREFERENCIAS ")]
    assert len(linhas) == 1, processo.stdout[-2000:]
    return json.loads(linhas[0])


def test_preferencia_usa_owners_instalados_sem_modelo_audio_background(preferencias_instaladas):
    assert all(preferencias_instaladas["owners"].values())
    assert preferencias_instaladas["modelo"] == 0
    assert preferencias_instaladas["voz"] == 0
    assert preferencias_instaladas["threads_novas"] == []


def test_reinicio_seleciona_preferencia_duravel_mais_recente_entre_escopos(preferencias_instaladas):
    caso = preferencias_instaladas["casos"]["reinicio"]
    antiga = caso["evidencias"]["conversa"][0]
    nova = caso["evidencias"]["geral"][0]
    assert antiga["confirmado_usuario"] and nova["confirmado_usuario"]
    assert nova["criado_em"] > antiga["criado_em"]
    assert caso["leitura"]["contexto"] == "geral"
    assert caso["leitura"]["direcao"] == "leve"
    assert caso["preferencia"]["direcao"] == "leve"
    assert caso["postura"]["nome"] == "amiga_suave"


def test_atualizacao_duravel_externa_chega_ao_proximo_turno_com_cache(preferencias_instaladas):
    caso = preferencias_instaladas["casos"]["atualizacao_externa"]
    assert caso["antes"]["preferencia"]["direcao"] == "mais_humor"
    assert caso["leitura"]["direcao"] == "leve", "controle: SQLite possui a atualização"
    assert caso["depois"]["preferencia"]["direcao"] == "leve"
    assert caso["depois"]["postura"]["nome"] == "amiga_suave"


def test_preferencia_temporaria_mais_recente_prevalece_sobre_duravel(preferencias_instaladas):
    caso = preferencias_instaladas["casos"]["temporaria"]
    pedido = caso["pedido"]["preferencia"]
    assert pedido["origem"] == "usuario_explicito" and pedido["duravel"] is False
    assert caso["leitura"]["direcao"] == "mais_humor"
    assert pedido["inicio_ts"] > caso["leitura"]["inicio_ts"]
    assert caso["depois"]["preferencia"] == pedido
    assert caso["depois"]["postura"]["nome"] == "amiga_suave"


def test_preferencia_nos_comandos_publica_escopo_e_nao_vaza_para_conversa(preferencias_instaladas):
    caso = preferencias_instaladas["casos"]["comandos"]
    pedido = caso["pedido"]["turno"].get("preferencia_humor") or {}
    assert pedido.get("contexto") == "comandos"
    assert caso["comando"]["preferencia"]["contexto"] == "comandos"
    assert caso["comando"]["preferencias"]["comandos"] == pedido
    assert not caso["conversa"]["preferencia"]


def test_tom_leve_nos_comandos_preserva_postura_operacional_sem_tirada(preferencias_instaladas):
    caso = preferencias_instaladas["casos"]["comandos"]["comando"]
    assert caso["plano"]["requer_execucao"] is True, "o comando de controle tem autoridade própria"
    assert caso["postura"]["nome"] == "operacional_amigavel"
    assert caso["postura"]["humor"] == "bloqueado"
    assert caso["postura"]["max_tirada"] == 0
    assert caso["retrato"]["orcamento_humor"] == 0


@pytest.mark.parametrize("indice", range(3))
def test_pedido_de_tom_nao_cria_autorizacao_execucao_efeito(preferencias_instaladas, indice):
    caso = preferencias_instaladas["casos"]["sem_autoridade"][indice]
    assert caso["turno"]["autoriza_execucao"] is False
    assert caso["plano"]["requer_execucao"] is False
    assert caso["preferencia"]["autoriza_execucao"] is False
    assert caso["retrato"]["autoriza_execucao"] is False
    assert caso["receipts"] == {}
    assert caso["fila_voz"] == 0


def test_falha_real_de_leitura_sqlite_preserva_tom_temporario_e_turno(preferencias_instaladas):
    caso = preferencias_instaladas["casos"]["leitura_indisponivel"]
    assert "erro" not in caso, caso.get("erro")
    assert caso["leitura"] == {}
    assert caso["depois"]["preferencia"] == caso["pedido"]["preferencia"]
    assert caso["depois"]["postura"]["nome"] == "amiga_suave"
    assert caso["depois"]["turno"]["autoriza_execucao"] is False


def test_composicao_instalada_transporta_tom_vigente_ao_contexto_operacional(preferencias_instaladas):
    transporte = preferencias_instaladas["transporte_confirmacao"]
    assert transporte["getter_instalado"] is True
    assert transporte["mente"]["preferencia_humor_contextual"]["contexto"] == "comandos"
    assert transporte["contexto_intencao"] == transporte["mente"]


def test_composicao_instalada_transporta_tom_do_contexto_operacional_ao_adaptador(preferencias_instaladas):
    transporte = preferencias_instaladas["transporte_confirmacao"]
    assert transporte["contexto_fala"] == transporte["mente"]


@pytest.mark.parametrize("nome", ["app_sem_acao", "iot_brilho", "jogo_causal"])
def test_consumidor_instalado_entrega_texto_factual_sem_audio_nem_alterar_receipt(preferencias_instaladas, nome):
    caso = preferencias_instaladas["consumidor_instalado"][nome]
    assert caso["registrador_instalado"] and caso["falar_resultado_instalado"]
    assert caso["receipt_antes"] == caso["receipt_depois"]
    assert caso["ultima_acao_antes"] == caso["ultima_acao_depois"]
    assert len(caso["publicados"]) == 1
    assert caso["publicados"][0]["fala"] == caso["esperado"]
    assert caso["texto_owner"] == [caso["esperado"]]
    assert caso["silencioso"] is True and caso["fila_voz"] == 0


def test_consumidor_no_jogo_conserva_causa_recente_sem_tirada_opcional(preferencias_instaladas):
    caso = preferencias_instaladas["consumidor_instalado"]["jogo_causal"]
    evento = caso["receipt_antes"]["contexto"]["avaliacao_evento"]
    assert caso["modo_jogo"] is True
    assert evento["permite_expressao"] is True
    assert evento["arco"] == "bronca_brincalhona"
    assert evento["evidencia_ref"] == caso["receipt_antes"]["id_solicitacao"]
    assert len(caso["publicados"]) == 1
    assert caso["publicados"][0]["fala"] == caso["esperado"]


@pytest.mark.parametrize("nome,executou,confirmado", [
    ("falha_com_fallback_otimista", False, False),
    ("incerto_com_fallback_otimista", True, None),
])
def test_tom_leve_no_consumidor_nao_troca_receipt_falho_ou_incerto_por_fallback_otimista(
    preferencias_instaladas, nome, executou, confirmado,
):
    caso = preferencias_instaladas["consumidor_instalado"][nome]
    assert caso["receipt_antes"]["executou"] is executou
    assert caso["receipt_antes"]["confirmado"] is confirmado
    assert caso["receipt_antes"] == caso["receipt_depois"]
    assert caso["ultima_acao_antes"] == caso["ultima_acao_depois"]
    assert caso["fila_voz"] == 0 and caso["silencioso"] is True
    assert len(caso["publicados"]) == 1
    fala = caso["publicados"][0]["fala"].casefold()
    assert fala != caso["esperado"].casefold()
    assert "não" in fala
    assert "pronto" not in fala and "salvei" not in fala and "ajustei" not in fala
    assert caso["receipt_antes"]["alvo"].casefold() in fala
    if confirmado is None:
        assert "confirm" in fala


@pytest.mark.parametrize("indice", range(3))
def test_catalogo_instalado_informa_tom_explicito_e_limite_da_calibracao(preferencias_instaladas, indice):
    catalogo = preferencias_instaladas["catalogo"]
    assert catalogo["personalidade"]["estado"] in {"disponivel", "parcial", "degradado"}
    assert catalogo["diagnostico"]["autoriza_execucao"] is False
    pergunta = catalogo["perguntas"][indice]
    assert "personalidade" in pergunta["dominios"]
    for texto in (pergunta["contexto"], pergunta["resposta"]):
        assert "preferência explícita" in texto
        assert "imediatamente" in texto
        assert "jogo, conversa e comandos" in texto
        assert "sempre" in texto and "origem" in texto
        assert "três entregas distintas no mesmo contexto" in texto
        assert "preferência explícita vigente prevalece" in texto
        assert "não autoriza ações" in texto
