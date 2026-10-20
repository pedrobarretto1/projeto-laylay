"""Referência proposta não dispensa revisão do conteúdo por unidade."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from dataclasses import asdict, FrozenInstanceError

import pytest


def _plano(texto="A avaliação depende de confirmação.", *, referencias=None, trecho=None):
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    url = "https://fonte.test/registro"
    proposta = {"fala": texto, "suporte_proposicoes": [{"texto": texto, "fontes": [url] if referencias is None else referencias}]}
    suporte = capturar_suporte_autoria(ContratoPropostaPrincipal("t", "Consulta?", json.dumps(proposta), True))
    fundamento = montar_fundamentacao("", {"ok": True, "confianca": .9, "resumo": trecho or texto,
        "fonte": "rota_da_pesquisa", "fontes": [{"url": url, "trecho": trecho or texto}]}, agora=1000)
    return {"id": "t", "texto_usuario": "Consulta?", "suporte_autoria_proposto": suporte,
            "fundamentacao_factual": fundamento}


@pytest.mark.parametrize("caso,esperado", [
    ("literal", "literal_integral_na_fonte"), ("parafrase", "apoio_semantico_pendente"),
    ("parcial", "trecho_parcial_sem_implicacao"), ("oposta", "apoio_semantico_pendente"),
    ("ausente", "fonte_nao_resolvida"), ("agregada", "fonte_sem_conteudo_individual"),
    ("interna", "referencia_interna_sem_prova_externa"), ("duplicada", "fonte_ambigua"),
    ("expirada", "fonte_fora_validade"), ("sem_conteudo", "fonte_sem_conteudo_conferivel"),
    ("nao_admitida", "fonte_nao_admissivel")])
def test_revisao_separa_origem_literalidade_e_implicacao_sem_rotulo_autoaprovado(caso, esperado):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    texto = "A avaliação depende de confirmação."
    trecho = {"parafrase": "É necessário confirmar antes de avaliar.",
              "parcial": texto + " Isto só vale no cenário simulado.",
              "oposta": "O registro rejeita essa avaliação."}.get(caso)
    refs = {"ausente": ["https://fonte.test/ausente"], "agregada": ["rota_da_pesquisa"],
            "interna": ["alegacao:100"]}.get(caso)
    plano = _plano(texto, referencias=refs, trecho=trecho)
    f = plano["fundamentacao_factual"]
    if caso == "duplicada":
        f["fontes"].append(dict(f["fontes"][0]))
    elif caso == "expirada":
        f.update(requer_evidencia_recente=True, evidencia_expira_em=999)
    elif caso == "sem_conteudo":
        f["fontes"][0]["trecho"] = False
    elif caso == "nao_admitida":
        f["confiavel"] = False
    revisao = revisar_suporte_autoria(texto, plano=plano, agora=1001)
    d = revisao.como_dict()
    assert d["proposicoes"][0]["estado"] == esperado
    assert d["semantica_verificada"] is d["prova_implicacao"] is d["autoriza_execucao"] is False
    assert d["pode_confirmar_fato_externo"] is False
    assert revisao.aplicar_limite is True and revisao.fala_realizada != texto
    if caso == "literal":
        assert "«" + texto + "»" in revisao.fala_realizada
        with pytest.raises(FrozenInstanceError):
            revisao.prova_implicacao = True
        d["fontes_lidas"][0]["trecho"] = "adulterado"
        assert revisao.como_dict()["fontes_lidas"][0]["trecho"] == texto


@pytest.mark.parametrize("contexto", [False, True])
def test_ausencia_de_referencia_nao_certifica_fato_e_contexto_nao_completa_citacao(contexto):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano(referencias=[])
    if not contexto:
        plano["fundamentacao_factual"] = {}
    r = revisar_suporte_autoria(plano["suporte_autoria_proposto"].fala_original, plano=plano, agora=1001)
    assert r.aplicar_limite is contexto
    assert r.como_dict()["proposicoes"][0]["estado"] == "sem_fontes_declaradas"
    assert r.prova_implicacao is False


def test_fonte_literal_nao_aprova_segunda_referencia_irrelevante():
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano(referencias=["https://fonte.test/registro", "https://fonte.test/outra"])
    plano["fundamentacao_factual"]["fontes"].append({"url": "https://fonte.test/outra", "trecho": "Outro assunto foi registrado."})
    r = revisar_suporte_autoria(plano["suporte_autoria_proposto"].fala_original, plano=plano, agora=1001)
    unidade = r.como_dict()["proposicoes"][0]
    assert [f["estado"] for f in unidade["fontes"]] == ["literal_integral_na_fonte", "apoio_semantico_pendente"]
    assert unidade["estado"] == "apoio_semantico_pendente"


@pytest.mark.parametrize("divergencia", ["json", "turno", "consulta", "fala"])
def test_julgamento_nao_empresta_autoria_ou_fontes_de_outra_ocorrencia(divergencia):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano()
    fala = plano["suporte_autoria_proposto"].fala_original
    if divergencia == "json":
        plano["suporte_autoria_proposto"] = asdict(plano["suporte_autoria_proposto"])
    elif divergencia == "turno":
        plano["id"] = "outro"
    elif divergencia == "consulta":
        plano["texto_usuario"] = "Outra consulta?"
    else:
        fala = "O executor registrou um resultado diferente."
    r = revisar_suporte_autoria(fala, plano=plano, agora=1001)
    if divergencia == "json":
        assert r is None
    else:
        assert r.como_dict()["estado"] in {"autoria_de_outra_ocorrencia", "fala_nao_vinculada"}
        assert r.prova_implicacao is False


def test_realizacao_limitada_e_idempotente_sem_apagar_qualificador_da_fonte():
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano(texto="A avaliação só é válida após confirmação independente.")
    r = revisar_suporte_autoria(plano["suporte_autoria_proposto"].fala_original, plano=plano, agora=1001)
    assert "só é válida após confirmação independente" in r.fala_realizada
    outra = revisar_suporte_autoria(r.fala_realizada, plano=plano, agora=1001)
    assert outra.como_dict() == r.como_dict() and outra.fala_realizada == r.fala_realizada


@pytest.fixture(scope="module")
def revisao_fontes_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("revisao_fontes_instalada")
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        assert not os.environ.get("LAYLAY_SONDA_ESCOPO_BASELINE")
        root = preparar_instalacao_isolada(Path(os.environ["LAYLAY_REVISAO_FONTES_MEMORIA"]))
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
        cliente_original = ClienteLLMRuntime.executar
        root._voz_runtime.falar = lambda *_a, **_k: False
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError("USB proibido"))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError("TCP proibido"))
        estado, runtime = root._estado_compartilhado_runtime, root._resposta_ia_runtime
        contexto_original = runtime._contexto_getter
        textos, casos = [], []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, partes in (("arquivo", ["O arquivo alfa tem uma cópia.", "A estratégia de restauração é adequada."]),
                                ("iot", ["A tomada da sala tem proteção elétrica.", "A estratégia de alimentação é adequada."])):
            for modo in (False, True):
                for variante in ("literal", "irrelevante", "parcial", "ausente"):
                    estado.substituir("mental", criar_estado_mental_inicial())
                    estado.atualizar_campos("memoria_conversa", messages=[])
                    urls = ["https://fonte.test/" + dominio + "/a", "https://fonte.test/" + dominio + "/b"]
                    conteudos = list(partes)
                    if variante == "irrelevante":
                        conteudos[1] = "O registro foi consultado durante a tarde."
                    elif variante == "parcial":
                        conteudos[1] += " Essa afirmação vale apenas no cenário simulado, após validação."
                    fontes = [{"url": u, "trecho": t, "titulo": "Registro simulado", "alvo": dominio} for u, t in zip(urls, conteudos)]
                    fundamento = montar_fundamentacao("", {"ok": True, "confianca": .9,
                        "resumo": " ".join(conteudos), "fonte": "pesquisa_simulada", "fontes": fontes})
                    referencias = [urls[0], urls[1] if variante != "ausente" else "https://fonte.test/inexistente"]
                    dados = {"comandos": [], "suporte_proposicoes": [{"texto": p, "fontes": [f]} for p, f in zip(partes, referencias)]}
                    enviados, efeitos = [], []
                    def gerar(self, requisicao):
                        enviados.append({"tipo": requisicao.tipo_chamada, "payload": dict(requisicao.payload)})
                        return ResultadoModelo(json.dumps(dados, ensure_ascii=False), True)
                    ClienteLLMRuntime.executar = gerar
                    contexto = contexto_original()
                    marcar = contexto["marcar_inicio_turno"]
                    def inicio_turno(*a, **k):
                        r = marcar(*a, **k)
                        mental = estado.retrato_dominio("mental")
                        plano = dict(mental["plano_turno_atual"])
                        plano["fundamentacao_factual"] = fundamento
                        estado.atualizar_campos("mental", fundamentacao_factual_turno=fundamento, plano_turno_atual=plano)
                        return r
                    contexto["marcar_inicio_turno"] = inicio_turno
                    contexto["usar_modo_rapido"] = lambda _t: modo
                    def impedir(*a, **k):
                        efeitos.append(True)
                        raise AssertionError("Revisão não autoriza efeito")
                    contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir})
                    runtime._contexto_getter = lambda: contexto
                    inicio = len(textos)
                    runtime.processar("Quais informações você tem sobre esse exemplo?", origem="teste_revisao_fontes")
                    caso = {"dominio": dominio, "modo": modo, "variante": variante, "partes": partes,
                            "fundamento": fundamento, "enviados": enviados, "efeitos": efeitos,
                            "textos": textos[inicio:], "mental": estado.retrato_dominio("mental")}
                    if os.environ.get("LAYLAY_REVISAO_FONTES_QWEN_REAL") == "1" and variante == "irrelevante" and modo == (dominio == "iot"):
                        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                        selecao, transportes = selecao_local(), []
                        requests.sessions.Session.request = criar_guarda_http_local(selecao, transportes, http_original)
                        ClienteLLMRuntime.executar = cliente_original
                        estado.substituir("mental", criar_estado_mental_inicial())
                        estado.atualizar_campos("memoria_conversa", messages=[])
                        # Porta corporal fora do recorte: o contexto diário
                        # completo excedeu os 4096 tokens locais neste ensaio.
                        # Fonte, preparação, codec, juiz e publicação permanecem
                        # instalados; não se altera configuração ou orçamento.
                        corpo_prompt = root._composicao_contextos_ia_runtime.modelo_corporal_getter
                        root._composicao_contextos_ia_runtime.modelo_corporal_getter = None
                        inicio = len(textos)
                        try:
                            runtime.processar("O que podemos concluir sobre o exemplo disponível?", origem="teste_revisao_fontes_qwen")
                        finally:
                            root._composicao_contextos_ia_runtime.modelo_corporal_getter = corpo_prompt
                        caso["real"] = {"selecao": selecao, "transportes": transportes, "textos": textos[inicio:],
                                        "mental": estado.retrato_dominio("mental")}
                    casos.append(caso)
        sys.__stdout__.write("REVISAO_FONTES_INSTALADA " + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + "\n")
    ''')
    p = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_REVISAO_FONTES_MEMORIA=str(pasta)),
        capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-5000:]
    dados = json.loads(next(l.removeprefix("REVISAO_FONTES_INSTALADA ") for l in p.stdout.splitlines() if l.startswith("REVISAO_FONTES_INSTALADA ")))
    if destino := os.environ.get("LAYLAY_EVIDENCIA_REVISAO_FONTES"):
        with Path(destino).open("x", encoding="utf-8") as out:
            json.dump(dados, out, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize("indice", range(16))
def test_composicao_revisa_conteudo_citado_antes_de_publicar_como_conclusao(revisao_fontes_instalada, indice):
    c = revisao_fontes_instalada[indice]
    plano = c["mental"]["plano_turno_atual"]
    assert "suporte_autoria_proposto" in plano
    assert plano["fundamentacao_factual"]["fontes"] == c["fundamento"]["fontes"]
    declarada = json.loads(plano["suporte_autoria_proposto"]["declaracao"]["_dados_json"])
    if c["variante"] == "ausente":
        # Agora a autoria recusa o ID fora do inventário antes da revisão.
        assert declarada["estado"] == "declaracao_ausente" and not declarada["proposicoes"]
        assert len(c["textos"]) == 1 and not any(t in c["textos"][0] for t in c["partes"])
        assert not c["efeitos"]
        assert all(a["status"] != "confirmado_por_fonte" for a in c["mental"]["registro_semantico"]["alegacoes"] if a["autor"] == "laylay")
        return
    assert declarada["proposicoes"][0]["fontes_no_contexto"] == [c["fundamento"]["fontes"][0]["url"]], "inventário não pode declarar ausente uma URL preservada"
    revisao = plano["ultima_verificacao"].get("revisao_suporte_autoria")
    assert revisao, "primeira fronteira: juiz não consome a declaração nem o conteúdo por fonte"
    assert len(revisao["proposicoes"]) == 2
    assert revisao["semantica_verificada"] is revisao["prova_implicacao"] is revisao["autoriza_execucao"] is False
    assert revisao["proposicoes"][0]["estado"] == "literal_integral_na_fonte"
    esperado = {"literal": "literal_integral_na_fonte", "irrelevante": "apoio_semantico_pendente",
                "parcial": "trecho_parcial_sem_implicacao", "ausente": "fonte_nao_resolvida"}[c["variante"]]
    assert revisao["proposicoes"][1]["estado"] == esperado
    assert len(c["textos"]) == 1 and c["textos"][0] != " ".join(c["partes"])
    assert c["partes"][0] in c["textos"][0]
    if c["variante"] != "literal":
        assert c["partes"][1] not in c["textos"][0]
    assert not c["efeitos"]
    assert all(a["status"] != "confirmado_por_fonte" for a in c["mental"]["registro_semantico"]["alegacoes"] if a["autor"] == "laylay")


@pytest.mark.skipif(os.environ.get("LAYLAY_REVISAO_FONTES_QWEN_REAL") != "1", reason="Inferência local opcional")
@pytest.mark.parametrize("indice", [1, 13])
def test_qwen_real_nao_autoaprova_relacao_entre_proposta_e_fonte(revisao_fontes_instalada, indice):
    r = revisao_fontes_instalada[indice]["real"]
    assert r["transportes"] and all(t.get("status") == 200 for t in r["transportes"])
    verificacao = r["mental"]["plano_turno_atual"]["ultima_verificacao"]
    revisao = verificacao["revisao_suporte_autoria"]
    assert revisao["proposicoes"] and len(r["textos"]) == 1
    assert revisao["estado"] == "revisao_limitada"
    assert verificacao["aceita"] is True and r["textos"] == [verificacao["fala"]]
    for unidade in revisao["proposicoes"]:
        if unidade["estado"] != "literal_integral_na_fonte":
            assert unidade["texto"] not in r["textos"][0]
    assert revisao["semantica_verificada"] is revisao["prova_implicacao"] is False
