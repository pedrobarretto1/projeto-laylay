"""Fontes internas são relações declaradas, não prova de inferência ou verdade."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.memoria_mental.registro_semantico import (
    registrar_alegacao, contestar_alegacao_recente, recuperar_revisao_alegacao,
    resumo_registro_semantico_para_prompt,
    corrigir_alegacao_recente, renovar_registro_semantico_sessao,
)
from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao


def _cadeia():
    r = registrar_alegacao(None, "A origem tem uma cópia íntegra.", autor="laylay", fonte="fonte_externa_teste", agora=100)
    a = r["alegacoes"][-1]["id"]
    r = registrar_alegacao(r, "A estratégia de recuperação é adequada.", autor="laylay", fonte=a, agora=101)
    b = r["alegacoes"][-1]["id"]
    r = registrar_alegacao(r, "A avaliação final é favorável.", autor="laylay", fonte=b, agora=102)
    c = r["alegacoes"][-1]["id"]
    r = registrar_alegacao(r, "O inventário tem uma fonte independente.", autor="laylay", fonte="outra_fonte_externa", agora=103)
    return r, a, b, c


def test_identidade_de_alegacao_interna_nao_vira_fonte_externa_por_ser_string():
    r, a, b, c = _cadeia()
    item = next(i for i in r["alegacoes"] if i["id"] == b)
    assert item["fonte"] == a
    assert item["status"] != "confirmado_por_fonte"
    p = classificar_proveniencia_informacao({**item, "status": "confirmado_por_fonte", "confiavel": True}, contexto="registro_semantico")
    assert p["pode_sustentar_fato_externo"] is False


def test_registro_anterior_nao_reabilita_derivacao_so_pelo_rotulo_confirmado():
    r, a, b, c = _cadeia()
    for item in r["alegacoes"]:
        if item["id"] in {b, c}:
            item.update(status="confirmado_por_fonte", confianca=0.82)
    original = deepcopy(r)
    resumo = resumo_registro_semantico_para_prompt(r, agora=105)
    utilizaveis = resumo.split("informações_utilizáveis=", 1)[1].split("alegações_bloqueadas=", 1)[0]
    assert "estratégia de recuperação" not in utilizaveis and "avaliação final" not in utilizaveis
    assert r == original


@pytest.mark.parametrize("nivel", [1, 2])
def test_revisao_da_fonte_alcanca_dependente_sem_mudar_original_ou_fonte_independente(nivel):
    r, a, b, c = _cadeia()
    original = deepcopy(r)
    r = contestar_alegacao_recente(r, f'De onde você tirou a alegação {a}?', agora=104)
    alvo = b if nivel == 1 else c
    consulta = f'Você mantém a alegação {alvo}?'
    fonte = recuperar_revisao_alegacao(r, consulta, turno_id="consulta")
    assert fonte is not None
    assert fonte.status == "suporte_em_revisao"
    assert fonte.alegacao_id == alvo
    assert fonte.apoios_revisados == ((a, "contestado"),)
    assert r["alegacoes"][-1] == original["alegacoes"][-1]
    assert next(i for i in r["alegacoes"] if i["id"] == alvo) == next(i for i in original["alegacoes"] if i["id"] == alvo)
    resumo = resumo_registro_semantico_para_prompt(r, agora=105)
    utilizaveis = resumo.split("informações_utilizáveis=", 1)[1].split("alegações_bloqueadas=", 1)[0]
    assert "estratégia de recuperação" not in utilizaveis and "avaliação final" not in utilizaveis
    assert "fonte independente" in utilizaveis


def test_correcao_e_ramificacao_preservam_cada_identidade_e_receipts():
    r, a, b, c = _cadeia()
    r = registrar_alegacao(r, "A segunda avaliação é favorável.", autor="laylay", fonte=a, agora=104)
    outro_dependente = r["alegacoes"][-1]["id"]
    r["falas_observadas"] = [{"id": "fala-original", "resultados": [{"id_solicitacao": "receipt", "confirmado": True}]}]
    antes = deepcopy(r["falas_observadas"])
    r = corrigir_alegacao_recente(r, f'Corrijo a alegação {a}.', agora=105)
    for alvo in (b, c, outro_dependente):
        fonte = recuperar_revisao_alegacao(r, f'Você mantém a alegação {alvo}?', turno_id="consulta")
        assert fonte.status == "suporte_em_revisao" and fonte.apoios_revisados == ((a, "corrigido"),)
    assert r["falas_observadas"] == antes


@pytest.mark.parametrize("defeito", ["ausente", "ciclo", "identidade_duplicada"])
def test_suporte_interno_invalido_nao_e_trocado_por_uma_fonte_parecida(defeito):
    r, a, b, c = _cadeia()
    if defeito == "ausente":
        r["alegacoes"] = [i for i in r["alegacoes"] if i["id"] != a]
    elif defeito == "ciclo":
        r["alegacoes"][0]["fonte"] = c
    else:
        r["alegacoes"].append(deepcopy(r["alegacoes"][0]))
    fonte = recuperar_revisao_alegacao(r, f'Você mantém a alegação {c}?', turno_id="consulta")
    assert fonte is not None and fonte.status == "suporte_interno_invalido"
    assert not fonte.apoios_revisados


def test_proximidade_tema_e_conectivo_sem_fonte_nao_criam_dependencia():
    r, a, b, c = _cadeia()
    texto = "Portanto a origem tem uma estratégia adequada."
    r = registrar_alegacao(r, texto, autor="laylay", agora=104)
    independente = r["alegacoes"][-1]["id"]
    r = contestar_alegacao_recente(r, f'De onde você tirou a alegação {a}?', agora=105)
    assert recuperar_revisao_alegacao(r, f'Você mantém a alegação {independente}?', turno_id="consulta") is None


def test_derivacao_interna_nao_verificada_nao_ganha_retencao_duravel_de_fonte_externa():
    r, a, b, c = _cadeia()
    novo = renovar_registro_semantico_sessao(r, agora=105)
    assert not {b, c}.intersection(i["id"] for i in novo["alegacoes"])


def test_julgamento_compartilhado_consume_suporte_revisado_sem_negar_conclusao():
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
    from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
    from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
    r, a, b, c = _cadeia()
    r = contestar_alegacao_recente(r, f'De onde você tirou a alegação {a}?', agora=104)
    texto = f'Você mantém a alegação {c}?'
    turno = {**classificar_modalidade_turno(texto), "id": "consulta"}
    plano = {"id": "consulta", "texto_usuario": texto, "autoriza_execucao": False, "comandos": []}
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={"registro_semantico": r})
    for fala in ("A avaliação final é favorável.", "A avaliação final é desfavorável.", "A revisão prova que a estratégia falhou."):
        guardiao = validar_alegacoes_da_fala(fala, plano=plano)
        assert guardiao["problemas"] == ["revisao_alegacao_sem_cobertura"]
        assert guardiao["prova_semantica_livre"] is False and guardiao["autoriza_execucao"] is False
        assert "não prova que ela seja falsa" in guardiao["fala"]
        assert avaliar_qualidade_comunicacao(texto, fala, plano=plano)["problemas_bloqueantes"]
        assert validar_aderencia_contrato_fala(texto, fala, contrato_fala=plano["contrato_fala"], turno_id="consulta")["problemas"]
        assert not validar_alegacoes_da_fala(guardiao["fala"], plano=plano)["problemas"]


@pytest.fixture(scope="module")
def suporte_instalado(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("suporte_conclusoes_instalado")
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_SUPORTE_MEMORIA_TESTE"])
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "laylay.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".suporte-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        modelo_instalado = RegistroModeloLLM.executar
        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
        for nome in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime", "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            root._composicao_turno_runtime._servicos[nome] = None
        root._voz_runtime.falar = lambda *_a, **_k: False
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError("USB proibido"))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError("TCP proibido"))
        estado = root._estado_compartilhado_runtime
        textos = []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        casos = []
        for dominio, premissa, conclusao in (("arquivo", "O arquivo alfa tem uma cópia íntegra.", "A estratégia de recuperação é adequada."),
                                           ("iot", "A tomada da sala tem proteção elétrica.", "A estratégia de alimentação é adequada.")):
            estado.substituir("mental", criar_estado_mental_inicial())
            def publicar(entrada, fala, fonte):
                root._iniciar_planejamento_turno(entrada, origem="teste_suporte")
                # Entrada declarada na porta de fundamentação. Não representa
                # pesquisa/medição reais nem certifica a inferência da frase.
                estado.atualizar_campos("mental", fundamentacao_factual_turno={"confiavel": True, "fonte": fonte})
                assert root.falar_com_lipsync(fala)
                root._registrar_mente_curta(entrada, fala)
                return next(i["id"] for i in estado.obter_copia("mental", "registro_semantico", {})["alegacoes"] if i["texto"] == fala)
            a = publicar("Vamos conversar sobre a origem", premissa, "fonte_externa_simulada")
            b = publicar("Vamos conversar sobre a conclusão", conclusao, a)
            c = publicar("Vamos conversar sobre a avaliação", "A avaliação final é favorável.", b)
            independente = publicar("Vamos conversar sobre outro assunto", "O inventário tem uma fonte independente.", "outra_fonte_externa_simulada")
            antes = estado.retrato_dominio("mental")
            contestacao = 'De onde você tirou "' + premissa + '"?'
            root._iniciar_planejamento_turno(contestacao, origem="teste_revisar_premissa")
            root._registrar_mente_curta(contestacao, "Essa afirmação precisa ser verificada.")
            depois = estado.retrato_dominio("mental")
            consultas = []
            for alvo, fala in ((b, conclusao), (c, "A avaliação final é favorável.")):
                texto = 'Você mantém a alegação ' + alvo + '?'
                root._iniciar_planejamento_turno(texto, origem="teste_consulta_dependente")
                plano = estado.obter_copia("mental", "plano_turno_atual", {})
                consultas.append({"alvo": alvo, "fala": fala, "texto": texto, "plano": plano,
                    "guarda": root._verificar_fala_do_turno(fala, origem="ia"),
                    "preparada": root._resposta_ia_runtime._contexto()["preparar_resposta"](texto, json.dumps({"fala": fala, "comandos": []})),
                    "normal": root._contexto_prompt_runtime.preparar_pacote(texto).prompt_sistema,
                    "rapido": root._contexto_prompt_runtime.preparar_instrucao_rapida(texto)})
            from types import SimpleNamespace
            runtime = root._resposta_ia_runtime
            contexto_original = runtime._contexto_getter
            ciclos, reais = [], []
            try:
                for nivel, (alvo, fala) in enumerate(((b, conclusao), (c, "A avaliação final é favorável.")), 1):
                    for modo in (False, True):
                        modelos, efeitos = [], []
                        def gerar(self, pedido):
                            modelos.append(dataclasses.asdict(pedido))
                            return ResultadoModelo(json.dumps({"fala": fala, "comandos": [], "tipo_interacao": "pergunta"}), True)
                        RegistroModeloLLM.executar = gerar
                        contexto = contexto_original()
                        contexto["usar_modo_rapido"] = lambda _t: modo
                        def impedir_efeito(pedido, texto):
                            efeitos.append(pedido)
                            raise AssertionError("Consulta não autoriza efeito externo.")
                        contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito})
                        runtime._contexto_getter = lambda: contexto
                        inicio = len(textos)
                        runtime.processar('Você mantém a alegação ' + alvo + '?', origem="teste_suporte_ciclo")
                        ciclos.append({"nivel": nivel, "modo": "rapido" if modo else "normal", "modelos": modelos,
                            "efeitos": efeitos, "textos": textos[inicio:], "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                if os.environ.get("LAYLAY_SUPORTE_QWEN_REAL") == "1":
                    import requests
                    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                    selecao, transportes, modelos = selecao_local(), [], []
                    http_original = requests.sessions.Session.request
                    requests.sessions.Session.request = criar_guarda_http_local(selecao, transportes, http_original)
                    modo = bool(casos)
                    def gerar_real(self, pedido):
                        resultado = modelo_instalado(self, pedido)
                        modelos.append({"pedido": dataclasses.asdict(pedido), "resultado": dataclasses.asdict(resultado)})
                        return resultado
                    try:
                        RegistroModeloLLM.executar = gerar_real
                        contexto = contexto_original()
                        contexto["usar_modo_rapido"] = lambda _t: modo
                        contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito})
                        runtime._contexto_getter = lambda: contexto
                        inicio = len(textos)
                        runtime.processar('Você mantém a alegação ' + c + '?', origem="teste_suporte_qwen_real")
                        reais.append({"modo": "rapido" if modo else "normal", "selecao": selecao,
                            "modelos": modelos, "transportes": transportes, "textos": textos[inicio:],
                            "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                    finally:
                        requests.sessions.Session.request = http_original
            finally:
                runtime._contexto_getter = contexto_original
                RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
            casos.append({"dominio": dominio, "a": a, "b": b, "c": c, "independente": independente,
                "antes": antes, "depois": depois, "consultas": consultas, "ciclos": ciclos, "reais": reais})
        sys.__stdout__.write("SUPORTE_INSTALADO " + json.dumps(casos, ensure_ascii=False,
            default=lambda v: {"callable_host": v.__name__} if callable(v) else dataclasses.asdict(v)) + "\n")
    ''')
    processo = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_SUPORTE_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8",
        timeout=180 if os.environ.get("LAYLAY_SUPORTE_QWEN_REAL") == "1" else 60)
    assert processo.returncode == 0, processo.stdout[-2000:] + processo.stderr[-5000:]
    casos = json.loads(next(l.removeprefix("SUPORTE_INSTALADO ") for l in processo.stdout.splitlines() if l.startswith("SUPORTE_INSTALADO ")))
    if caminho := os.environ.get("LAYLAY_EVIDENCIA_SUPORTE"):
        with Path(caminho).open("x", encoding="utf-8") as arquivo:
            json.dump(casos, arquivo, ensure_ascii=False, indent=2)
    return casos


@pytest.mark.parametrize("indice", [0, 1])
@pytest.mark.parametrize("nivel", [0, 1])
def test_composicao_revisao_da_origem_bloqueia_reuso_da_conclusao_sem_apagar_vizinha(suporte_instalado, indice, nivel):
    caso = suporte_instalado[indice]
    posteriores = {i["id"]: i for i in caso["depois"]["registro_semantico"]["alegacoes"]}
    assert posteriores[caso["a"]]["status"] in {"contestado", "corrigido"}
    assert posteriores[caso["b"]]["fonte"] == caso["a"]
    assert posteriores[caso["c"]]["fonte"] == caso["b"]
    consulta = caso["consultas"][nivel]
    assert "revisao_alegacao" in consulta["plano"]["contrato_fala"]
    assert consulta["guarda"]["problemas"]
    assert "suporte" in consulta["guarda"]["fala"].casefold()
    assert consulta["preparada"]["fala"] == consulta["guarda"]["fala"]
    assert not consulta["preparada"].get("comandos")
    antes = next(i for i in caso["antes"]["registro_semantico"]["alegacoes"] if i["id"] == caso["independente"])
    assert posteriores[caso["independente"]] == antes


@pytest.mark.parametrize("indice", [0, 1])
@pytest.mark.parametrize("nivel", [1, 2])
@pytest.mark.parametrize("modo", ["normal", "rapido"])
def test_ciclo_instalado_nao_reafirma_conclusao_com_suporte_revisado(suporte_instalado, indice, nivel, modo):
    ciclo = next(c for c in suporte_instalado[indice]["ciclos"] if c["nivel"] == nivel and c["modo"] == modo)
    assert ciclo["modelos"] and len(ciclo["textos"]) == 1
    assert "suporte desta conclusão está em revisão" in ciclo["textos"][0]
    assert "não prova que ela seja falsa" in ciclo["textos"][0]
    assert not ciclo["efeitos"] and not ciclo["plano"].get("comandos")


@pytest.mark.skipif(os.environ.get("LAYLAY_SUPORTE_QWEN_REAL") != "1", reason="Inferência local real opcional.")
@pytest.mark.parametrize("indice", [0, 1])
def test_qwen_real_respeita_suporte_revisado_no_ciclo_instalado(suporte_instalado, indice):
    geracao = suporte_instalado[indice]["reais"][0]
    assert geracao["modelos"] and geracao["transportes"]
    assert all(t["status"] == 200 for t in geracao["transportes"])
    assert len(geracao["textos"]) == 1 and "suporte desta conclusão está em revisão" in geracao["textos"][0]
    assert not geracao["plano"].get("comandos")
