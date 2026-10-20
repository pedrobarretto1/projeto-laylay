"""C5: revisão identifica a alegação antes de alterar seu estado de confiança."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta
from mente_laylay.memoria_mental.registro_semantico import (
    atualizar_registro_turno, contestar_alegacao_recente, corrigir_alegacao_recente,
    registrar_alegacao, registrar_interacao_semantica, resumo_registro_semantico_para_prompt,
    renovar_registro_semantico_sessao,
)


ANTIGA = "O arquivo alfa tem uma cópia de segurança."
RECENTE = "A tomada da sala tem proteção elétrica."


def _registro():
    registro = registrar_alegacao(None, ANTIGA, autor="laylay", fonte="fonte_de_teste", agora=100)
    return registrar_alegacao(registro, RECENTE, autor="laylay", fonte="outra_fonte_de_teste", agora=101)


@pytest.mark.parametrize("alvo,outro", [(ANTIGA, RECENTE), (RECENTE, ANTIGA)])
@pytest.mark.parametrize("aspas", [('"', '"'), ('“', '”')])
def test_contestacao_literal_seleciona_a_alegacao_e_preserva_a_vizinha(alvo, outro, aspas):
    original = _registro()
    registro = contestar_alegacao_recente(original, f'De onde você tirou {aspas[0]}{alvo}{aspas[1]}?', agora=102)
    itens = {item["texto"]: item for item in registro["alegacoes"]}
    assert itens[alvo]["status"] == "contestado"
    assert itens[outro]["status"] == "confirmado_por_fonte"
    assert original == _registro(), "A entrada histórica não pode ser modificada por alias."
    resumo = resumo_registro_semantico_para_prompt(registro, agora=103)
    utilizaveis = resumo.split("informações_utilizáveis=", 1)[1].split("alegações_bloqueadas=", 1)[0]
    assert outro in utilizaveis and alvo not in utilizaveis


@pytest.mark.parametrize("cita", ['"Outra frase que não consta no registro."', f'"{ANTIGA}" e "{RECENTE}"'])
def test_referencia_nao_resolvida_nao_contesta_a_ultima_por_aproximacao(cita):
    original = _registro()
    registro = contestar_alegacao_recente(original, f'De onde você tirou {cita}?', agora=102)
    assert registro["alegacoes"] == original["alegacoes"]


def test_repetir_contestacao_na_mesma_cadeia_nao_caminha_para_alegacoes_anteriores():
    registro = contestar_alegacao_recente(_registro(), "tem certeza disso?", agora=102)
    registro = registrar_interacao_semantica(registro, texto_usuario="tem certeza disso?", agora=102)
    assert [item["status"] for item in registro["alegacoes"]] == ["confirmado_por_fonte", "contestado"]


def test_correcao_dirigida_pode_revisar_a_alegacao_ja_contestada():
    texto = f'Não, a afirmação "{ANTIGA}" está errada.'
    registro = contestar_alegacao_recente(_registro(), f'De onde você tirou "{ANTIGA}"?', agora=102)
    registro = corrigir_alegacao_recente(registro, texto, agora=103)
    assert registro["alegacoes"][0]["status"] == "corrigido"
    assert registro["alegacoes"][1]["status"] == "confirmado_por_fonte"
    assert registro["correcoes"][-1]["alegacao_corrigida_id"] == registro["alegacoes"][0]["id"]
    assert registro["alegacoes"][0]["texto"] == ANTIGA


def test_revisao_por_id_nao_depende_da_recencia():
    registro = _registro()
    alvo_id = registro["alegacoes"][0]["id"]
    registro = contestar_alegacao_recente(registro, f'De onde você tirou a alegação {alvo_id}?', agora=102)
    assert [item["status"] for item in registro["alegacoes"]] == ["contestado", "confirmado_por_fonte"]


def test_citacao_duplicada_exige_identidade_em_vez_de_escolher_a_mais_recente():
    registro = registrar_alegacao(_registro(), ANTIGA, autor="laylay", fonte="fonte_repetida", agora=300)
    anterior = deepcopy(registro["alegacoes"])
    registro = contestar_alegacao_recente(registro, f'De onde você tirou "{ANTIGA}"?', agora=301)
    assert registro["alegacoes"] == anterior


def test_marcador_dentro_de_citacao_nao_e_feedback_do_usuario():
    registro = _registro()
    novo = contestar_alegacao_recente(registro, 'Traduza "tem certeza disso?" para inglês.', agora=102)
    assert novo["alegacoes"] == registro["alegacoes"]


def test_projecao_contextual_nao_tem_outro_seletor_de_ultima_resposta():
    estado = registrar_mente_curta({"registro_semantico": _registro(), "ultima_resposta": RECENTE},
        texto_usuario=f'De onde você tirou "{ANTIGA}"?')
    assert estado["alegacao_contestada"]["texto"] == ANTIGA
    assert estado["alegacao_contestada"]["alegacao_id"] == estado["registro_semantico"]["alegacoes"][0]["id"]


def test_correcao_pelo_turno_e_contestacao_pela_memoria_nao_revisam_alvos_diferentes():
    texto = f'De onde você tirou "{ANTIGA}"?'
    registro = atualizar_registro_turno(_registro(), texto, retrato={}, funcao="correcao", agora=102)
    registro = registrar_interacao_semantica(registro, texto_usuario=texto, agora=103)
    assert registro["alegacoes"][1]["status"] == "confirmado_por_fonte"


def test_revisao_conserva_original_e_idempotencia_sem_promover_alternativa_a_fonte():
    original = _registro()
    texto = f'De onde você tirou "{ANTIGA}"?'
    registro = contestar_alegacao_recente(original, texto, agora=102)
    assert registro["alegacoes"][0]["status"] == "contestado"
    revisao = registro["revisoes_alegacoes"][-1]
    assert revisao["anterior"] == original["alegacoes"][0]
    assert revisao["autoriza_execucao"] is False
    repetido = contestar_alegacao_recente(registro, texto, agora=103)
    assert repetido["revisoes_alegacoes"] == registro["revisoes_alegacoes"]
    assert all(item["autor"] == "laylay" for item in repetido["alegacoes"])
    renovado = renovar_registro_semantico_sessao(repetido, agora=104)
    assert renovado["revisoes_alegacoes"] == repetido["revisoes_alegacoes"]
    assert renovado["revisao_alegacao_atual"] == {}


def test_referencia_inexistente_fica_explicita_sem_revisar_qualquer_outra_fonte():
    original = _registro()
    registro = contestar_alegacao_recente(original, "De onde você tirou a alegação alegacao:999?", agora=102)
    assert registro["alegacoes"] == original["alegacoes"]
    assert registro["revisao_alegacao_atual"]["referencia"] == "ausente"
    assert "peça qual afirmação" in resumo_registro_semantico_para_prompt(registro, agora=103)


@pytest.mark.parametrize("cita", ["'Não consta no registro.'", '«Não consta no registro.»', '""'])
def test_delimitador_nao_resolvido_nao_vira_referencia_implicita(cita):
    original = _registro()
    registro = contestar_alegacao_recente(original, f'De onde você tirou {cita}?', agora=102)
    assert registro["alegacoes"] == original["alegacoes"]


def test_revisao_textual_nao_reescreve_receipts_fala_observada_ou_efeitos():
    estado = {"registro_semantico": _registro(), "ultima_resposta": RECENTE,
        "ultima_acao_contrato": {"id_solicitacao": "receipt-original", "confirmado": True},
        "efeitos_reversiveis": [{"id": "efeito-original"}],
        "plano_turno_atual": {"comandos": []}}
    original = deepcopy(estado)
    novo = registrar_mente_curta(estado, texto_usuario=f'De onde você tirou "{ANTIGA}"?')
    assert novo["registro_semantico"]["alegacoes"][0]["status"] == "contestado"
    for chave in ("ultima_acao_contrato", "efeitos_reversiveis", "plano_turno_atual"):
        assert novo[chave] == original[chave]


@pytest.fixture(scope="module")
def revisao_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("revisao_dirigida_instalada")
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_REVISAO_MEMORIA_TESTE"])
        sqlite = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "laylay.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: central(self, str(pasta / "central.json"), **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".revisao-" + str(os.getpid()), **k)
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
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: textos.append(texto) or True)
        casos = []
        for alvo, outra in (("O arquivo alfa tem uma cópia de segurança.", "A tomada da sala tem proteção elétrica."),
                            ("A tomada da sala tem proteção elétrica.", "O arquivo alfa tem uma cópia de segurança.")):
            estado.substituir("mental", criar_estado_mental_inicial())
            for indice, fala in enumerate((alvo, outra)):
                entrada = "Vamos conversar sobre esse assunto " + str(indice)
                root._iniciar_planejamento_turno(entrada, origem="teste_revisao")
                assert root.falar_com_lipsync(fala)
                root._registrar_mente_curta(entrada, fala)
            antes = estado.retrato_dominio("mental")
            texto = 'De onde você tirou "' + alvo + '"?'
            root._iniciar_planejamento_turno(texto, origem="teste_revisao_dirigida")
            turno = estado.retrato_dominio("mental")
            root._registrar_mente_curta(texto, "Vou verificar essa afirmação.")
            depois = estado.retrato_dominio("mental")
            consulta = "Quais afirmações continuam confiáveis?"
            root._iniciar_planejamento_turno(consulta, origem="teste_revisao_posterior")
            normal = root._contexto_prompt_runtime.preparar_pacote(consulta).prompt_sistema
            rapido = root._contexto_prompt_runtime.preparar_instrucao_rapida(consulta)
            posteriores = []
            ciclos_revisao = []
            geracoes_reais = []
            if os.environ.get("LAYLAY_COLETAR_JULGAMENTO_REVISAO") == "1":
                alvo_id = next(a["id"] for a in depois["registro_semantico"]["alegacoes"] if a["texto"] == alvo)
                for consulta_revisada in ('Você mantém a alegação ' + alvo_id + '?',
                                         'Você mantém a afirmação "' + alvo + '"?'):
                    root._iniciar_planejamento_turno(consulta_revisada, origem="teste_julgamento_revisao")
                    plano_revisado = estado.obter_copia("mental", "plano_turno_atual", {})
                    preparada = root._resposta_ia_runtime._contexto()["preparar_resposta"](
                        consulta_revisada, json.dumps({"fala": alvo, "comandos": []}))
                    posteriores.append({"texto": consulta_revisada, "plano": plano_revisado,
                        "guarda": root._verificar_fala_do_turno(alvo, origem="ia"), "preparada": preparada})
                from types import SimpleNamespace
                runtime = root._resposta_ia_runtime
                contexto_original = runtime._contexto_getter
                try:
                    for modo in (False, True):
                        modelos, efeitos = [], []
                        def gerar_reafirmacao(self, pedido):
                            modelos.append(dataclasses.asdict(pedido))
                            return ResultadoModelo(json.dumps({"fala": alvo, "comandos": [],
                                "tipo_interacao": "pergunta"}), True)
                        RegistroModeloLLM.executar = gerar_reafirmacao
                        contexto = contexto_original()
                        contexto["usar_modo_rapido"] = lambda _t: modo
                        def impedir_efeito(pedido, texto):
                            efeitos.append(pedido)
                            raise AssertionError("Revisão não autoriza efeito externo.")
                        contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito})
                        runtime._contexto_getter = lambda: contexto
                        inicio = len(textos)
                        runtime.processar('Você mantém a alegação ' + alvo_id + '?', origem="teste_ciclo_revisao")
                        ciclos_revisao.append({"modo": "rapido" if modo else "normal", "modelos": modelos,
                            "efeitos": efeitos, "textos": textos[inicio:],
                            "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                finally:
                    runtime._contexto_getter = contexto_original
                    RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
                if os.environ.get("LAYLAY_REVISAO_QWEN_REAL") == "1":
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
                        runtime.processar('Você mantém a alegação ' + alvo_id + '?', origem="teste_revisao_qwen_real")
                        geracoes_reais.append({"modo": "rapido" if modo else "normal", "selecao": selecao,
                            "modelos": modelos, "transportes": transportes, "textos": textos[inicio:],
                            "plano": estado.obter_copia("mental", "plano_turno_atual", {})})
                    finally:
                        runtime._contexto_getter = contexto_original
                        requests.sessions.Session.request = http_original
                        RegistroModeloLLM.executar = lambda *_a, **_k: ResultadoModelo("", False)
            casos.append({"alvo": alvo, "outra": outra, "antes": antes, "turno": turno,
                "depois": depois, "normal": normal, "rapido": rapido,
                "posteriores": posteriores, "ciclos_revisao": ciclos_revisao, "geracoes_reais": geracoes_reais,
                "plano_posterior": estado.obter_copia("mental", "plano_turno_atual", {})})
        sys.__stdout__.write("REVISAO_INSTALADA " + json.dumps(casos, ensure_ascii=False,
            default=lambda v: {"callable_host": v.__name__} if callable(v) else dataclasses.asdict(v)) + "\n")
    ''')
    processo = subprocess.run([sys.executable, "-c", codigo],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ,
        PYTHONIOENCODING="utf-8", LAYLAY_REVISAO_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8",
        timeout=180 if os.environ.get("LAYLAY_REVISAO_QWEN_REAL") == "1" else 60)
    assert processo.returncode == 0, processo.stdout[-2000:] + processo.stderr[-5000:]
    casos = json.loads(next(linha.removeprefix("REVISAO_INSTALADA ") for linha in processo.stdout.splitlines()
                            if linha.startswith("REVISAO_INSTALADA ")))
    if caminho := os.environ.get("LAYLAY_EVIDENCIA_REVISAO"):
        with Path(caminho).open("x", encoding="utf-8") as arquivo:
            json.dump(casos, arquivo, ensure_ascii=False, indent=2)
    return casos


@pytest.mark.parametrize("indice", [0, 1])
def test_composicao_instalada_revisa_a_fonte_citada_e_a_consulta_posterior(revisao_instalada, indice):
    caso = revisao_instalada[indice]
    antigas = caso["antes"]["registro_semantico"]["alegacoes"]
    assert any(item["texto"] == caso["alvo"] for item in antigas)
    itens = {item["texto"]: item for item in caso["turno"]["registro_semantico"]["alegacoes"]}
    assert itens[caso["alvo"]]["status"] in {"contestado", "corrigido"}
    assert itens[caso["outra"]]["status"] == "incerto"
    depois = {item["texto"]: item for item in caso["depois"]["registro_semantico"]["alegacoes"]}
    assert depois[caso["outra"]]["status"] == "incerto"
    assert caso["depois"]["alegacao_contestada"]["texto"] == caso["alvo"]
    assert not caso["plano_posterior"].get("comandos")


@pytest.mark.parametrize("indice", [0, 1])
@pytest.mark.parametrize("rota", ["normal", "rapido"])
def test_revisao_identificada_chega_a_autoria_posterior(revisao_instalada, indice, rota):
    caso = revisao_instalada[indice]
    # O contrato é a identidade revisada, não a presença de um resumo inteiro.
    if "alegações_bloqueadas=" in caso[rota]:
        bloco = caso[rota].split("alegações_bloqueadas=", 1)[1].split("Relatos e memórias", 1)[0]
    else:
        assert "ALEGAÇÃO CONTESTADA:" in caso[rota]
        bloco = caso[rota].split("ALEGAÇÃO CONTESTADA:", 1)[1].split("\n", 1)[0]
    assert caso["alvo"] in bloco
    assert caso["outra"] not in bloco
