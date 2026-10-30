"""Saída autoral principal exige declaração; forma não certifica apoio."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("texto", ["Quais informações você tem sobre esse exemplo?", "abre o aplicativo Calculadora"])
def test_envio_principal_negocia_suporte_sem_depender_de_pedido_na_fala(texto):
    from scripts.tests.test_interpretacao_operacional_por_ato import _prompt_para_turno
    runtime, estado = _prompt_para_turno(texto)
    mensagens = [{"role": "user", "content": texto}]
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=estado["turno_atual"]["id"])
    assert pacote.contrato_saida is not None, "primeira fronteira: autoria sem contrato obrigatório"
    esquema = pacote.contrato_saida.response_format["json_schema"]["schema"]
    assert "suporte_proposicoes" in esquema["required"], "primeira fronteira: schema admite omissão de suporte"
    assert mensagens == [{"role": "user", "content": texto}]


@pytest.mark.parametrize("estrategia", ["explicacao_capacidades", "negacao_operacional_sem_efeito", "analise_evidencia_textual"])
def test_projecoes_fechadas_preservam_obrigacao_de_suporte(estrategia):
    from scripts.tests.test_interpretacao_operacional_por_ato import _prompt_para_turno
    texto = "Quais informações você tem?"
    runtime, estado = _prompt_para_turno(texto)
    turno = estado["turno_atual"]
    turno.update(autoriza_execucao=False, modalidade_geral="recusa" if estrategia.startswith("negacao") else "pergunta")
    estado["contrato_fala_atual"] = {"turno_id": turno["id"], "roteiro_concreto": {"estrategia": estrategia},
        "documentacao_capacidades": "Catálogo de teste.", "estado_referencia_textual": "nao_resolvida"}
    pacote = runtime.preparar_envio_modelo([{"role": "user", "content": texto}], turno_id=turno["id"])
    assert pacote.contexto_fechado is True
    assert "suporte_proposicoes" in pacote.contrato_saida.response_format["json_schema"]["schema"]["required"]


@pytest.mark.parametrize("tipo,interativa,autoral", [
    ("reparo_comunicacao", True, True), ("reparo_json", False, True),
    ("reparo_factual", True, True), ("autoria_operacional", True, True),
    ("presenca_evento", False, True), ("continuacao", True, True),
    ("continuacao", False, False), ("interpretacao", True, False), ("auxiliar", False, False)])
def test_recuperacao_nao_contorna_contrato_e_interpretacao_interna_mantem_protocolo(tipo, interativa, autoral):
    from scripts.tests.test_saida_tipificada_principal import preparador
    from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo, ResultadoModelo
    vistos = []
    def responder(requisicao):
        vistos.append(dict(requisicao.payload))
        return ResultadoModelo('{"fala":"Proposta sem apoio declarado.","comandos":[]}', True)
    servico = ServicoModeloLLMRuntime(preparador=preparador(), cliente=SimpleNamespace(executar=responder))
    resultado = servico.executar(PedidoModelo.criar([{"role": "user", "content": "Consulta de teste?"}],
        tipo_chamada=tipo, prioridade_interativa=interativa))
    assert resultado.sucesso is (not autoral)
    if autoral:
        from mente_laylay.cognicao.estado_tecnico_llm import categoria_estado_tecnico_llm
        assert categoria_estado_tecnico_llm(resultado.texto) == 'contrato_saida_invalido'
        assert resultado.rota == "contrato_saida_invalido" and 'Proposta sem apoio' not in resultado.texto
        assert "suporte_proposicoes" in vistos[0]["response_format"]["json_schema"]["schema"]["required"]


@pytest.mark.parametrize("mudanca", ["ausente", "parcial", "autoaprovada", "referencia_invalida", "repetida"])
def test_owner_recusa_declaracao_incompleta_sem_reparar_por_proximidade(mudanca):
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    # O teste desta fronteira oferece a referência; caso contrário o codec
    # recusaria pelo inventário antes de alcançar a mutação que queremos testar.
    codec = exigir_suporte_no_pacote_autoral(PacotePrompt(()),
        referencias_disponiveis=("fonte:presente",)).contrato_saida
    d = {"suporte_proposicoes": [
        {"texto": "Uma hipótese.", "fontes": [], "sem_fonte": "nao_utilizada"},
        {"texto": "Uma conclusão.", "fontes": ["fonte:presente"]}]}
    if mudanca == "ausente":
        d.pop("suporte_proposicoes")
    elif mudanca == "parcial":
        d["suporte_proposicoes"][0].pop("fontes")
    elif mudanca == "autoaprovada":
        d["suporte_proposicoes"][0]["semantica_verificada"] = True
    elif mudanca == "referencia_invalida":
        d["suporte_proposicoes"][0]["fontes"] = [False]
    else:
        d["suporte_proposicoes"][1]["texto"] = "Uma hipótese."
    with pytest.raises(ValueError):
        codec.decodificar_json(json.dumps(d))


def test_extensao_preserva_validator_operacional_e_nao_autoaprova_suporte():
    from scripts.tests.test_saida_tipificada_principal import envelope
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    texto, d = envelope()
    base = criar_contrato_saida_interpretacao_principal(texto)
    original = base.response_format
    codec = exigir_suporte_no_pacote_autoral(PacotePrompt((), contrato_saida=base),
        referencias_disponiveis=("fonte:presente",)).contrato_saida
    d["suporte_proposicoes"] = [{"texto": d["fala"], "fontes": ["fonte:presente"]}]
    original_fala = d.pop("fala")
    assert codec.decodificar_json(json.dumps(d)) == {**d, "fala": original_fala}
    assert base.response_format == original
    d["comandos"] = [{"intent": "APP_OPEN", "params": {}, "confirmado": True}]
    with pytest.raises(ValueError):
        codec.decodificar_json(json.dumps(d))


def test_fala_e_projetada_das_unidades_autorais_sem_copia_independente():
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    codec = exigir_suporte_no_pacote_autoral(PacotePrompt(()),
        referencias_disponiveis=("fonte:existente",)).contrato_saida
    esquema = codec.response_format["json_schema"]["schema"]
    assert esquema["additionalProperties"] is False and "fala" not in esquema["properties"]
    dados = {"suporte_proposicoes": [{"texto": "Uma hipótese.", "fontes": [], "sem_fonte": "nao_utilizada"},
                                    {"texto": "Uma conclusão.", "fontes": ["fonte:existente"]}]}
    esperado = json.loads(json.dumps(dados))
    saida = codec.decodificar_json(json.dumps(dados))
    assert saida["fala"] == "Uma hipótese. Uma conclusão."
    assert saida["suporte_proposicoes"] == esperado["suporte_proposicoes"]
    with pytest.raises(ValueError):
        codec.decodificar_json(json.dumps({**dados, "fala": "Uma versão diferente."}))


@pytest.fixture(scope="module")
def emissao_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("emissao_suporte_instalada")
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        assert not os.environ.get("LAYLAY_SONDA_ESCOPO_BASELINE")
        root = preparar_instalacao_isolada(Path(os.environ["LAYLAY_EMISSAO_MEMORIA_TESTE"]))
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        original_http = ClienteLLMRuntime.executar
        root._voz_runtime.falar = lambda *_a, **_k: False
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError("USB proibido"))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError("TCP proibido"))
        estado, runtime = root._estado_compartilhado_runtime, root._resposta_ia_runtime
        contexto_original = runtime._contexto_getter
        textos, casos = [], []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, partes in (("arquivo", ["O arquivo alfa tem uma cópia.", "A estratégia de restauração é adequada."]),
                                ("iot", ["A tomada da sala tem proteção elétrica.", "A estratégia de alimentação é adequada."])):
            fala = " ".join(partes)
            for modo in (False, True):
                for variante in ("presente", "ausente", "malformada", "reparo_valido"):
                    estado.substituir("mental", criar_estado_mental_inicial())
                    estado.atualizar_campos("memoria_conversa", messages=[])
                    enviados, efeitos = [], []
                    dados = {"comandos": []}
                    if variante not in {"ausente", "reparo_valido"}:
                        dados["suporte_proposicoes"] = [{"texto": parte,
                            "fontes": ["alegacao:inexistente"] if variante == "presente" else [True]} for parte in partes]
                    def gerar(self, requisicao):
                        enviados.append({"tipo": requisicao.tipo_chamada, "payload": dict(requisicao.payload)})
                        resposta = dados
                        if variante == "reparo_valido" and requisicao.tipo_chamada == "reparo_json":
                            resposta = {"comandos": [], "suporte_proposicoes": [
                                {"texto": parte, "fontes": ["alegacao:inexistente"]} for parte in partes]}
                        return ResultadoModelo(json.dumps(resposta, ensure_ascii=False), True)
                    ClienteLLMRuntime.executar = gerar
                    contexto = contexto_original()
                    marcar = contexto["marcar_inicio_turno"]
                    def inicio_turno(*a, **k):
                        r = marcar(*a, **k)
                        base={"confiavel": True, "fonte": "fonte_contextual_simulada"}
                        if variante in {"presente", "reparo_valido"}:
                            # A referência interna é OFERECIDA pela fixture,
                            # mas continua sem prova externa. O teste alcança
                            # a revisão posterior sem burlar o codec anterior.
                            base.update(resumo="Referência interna em cenário simulado, sem prova externa.",
                                fontes=[{"url":"alegacao:inexistente","trecho":"Hipótese interna sem prova externa."}])
                        estado.atualizar_campos("mental", fundamentacao_factual_turno=base)
                        plano=estado.obter_copia("mental","plano_turno_atual",{})
                        plano["fundamentacao_factual"]=dict(base)
                        estado.atualizar_campos("mental",plano_turno_atual=plano)
                        return r
                    contexto["marcar_inicio_turno"] = inicio_turno
                    contexto["usar_modo_rapido"] = lambda _t: modo
                    def impedir(*a, **k):
                        efeitos.append(True)
                        raise AssertionError("Declaração não autoriza execução")
                    contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir})
                    runtime._contexto_getter = lambda: contexto
                    inicio = len(textos)
                    runtime.processar("Quais informações você tem sobre esse exemplo?", origem="teste_emissao_suporte")
                    caso = {"dominio": dominio, "modo": modo, "variante": variante, "fala": fala,
                            "enviados": enviados, "efeitos": efeitos, "textos": textos[inicio:],
                            "mental": estado.retrato_dominio("mental")}
                    if os.environ.get("LAYLAY_EMISSAO_QWEN_REAL") == "1" and variante == "presente" and modo == (dominio == "iot"):
                        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                        selecao, transportes = selecao_local(), []
                        requests.sessions.Session.request = criar_guarda_http_local(selecao, transportes, http_original)
                        ClienteLLMRuntime.executar = original_http
                        estado.substituir("mental", criar_estado_mental_inicial())
                        estado.atualizar_campos("memoria_conversa", messages=[])
                        inicio = len(textos)
                        runtime.processar("Como você explicaria a diferença entre uma hipótese e uma confirmação?",
                                          origem="teste_emissao_qwen_real")
                        caso["real"] = {"selecao": selecao, "transportes": transportes, "textos": textos[inicio:],
                                        "mental": estado.retrato_dominio("mental")}
                    casos.append(caso)
        sys.__stdout__.write("EMISSAO_INSTALADA " + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + "\n")
    ''')
    p = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_EMISSAO_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-5000:]
    dados = json.loads(next(l.removeprefix("EMISSAO_INSTALADA ") for l in p.stdout.splitlines() if l.startswith("EMISSAO_INSTALADA ")))
    if destino := os.environ.get("LAYLAY_EVIDENCIA_EMISSAO"):
        with Path(destino).open("x", encoding="utf-8") as out:
            json.dump(dados, out, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize("indice", range(16))
def test_composicao_exige_declaracao_antes_de_admitir_autoria(emissao_instalada, indice):
    c = emissao_instalada[indice]
    principal = next(e for e in c["enviados"] if e["tipo"] == "principal")
    formato = principal["payload"].get("response_format", {})
    assert formato.get("type") == "json_schema", "primeira fronteira: envio instalado não negocia suporte"
    assert "suporte_proposicoes" in formato["json_schema"]["schema"]["required"]
    assert c["textos"], "turno consumido precisa de conclusão observável"
    if c["variante"] == "presente":
        # Declaração formal continua preservada; a nova revisão não autoriza
        # publicar suas fontes internas inexistentes como apoio factual.
        assert len(c["textos"]) == 1 and c["textos"] != [c["fala"]]
        suporte = c["mental"]["plano_turno_atual"]["suporte_autoria_proposto"]
        assert json.loads(suporte["declaracao"]["_dados_json"])["estado"] == "revisao_semantica_pendente"
        d = c["mental"]["registro_semantico"]["declaracoes_suporte_autoria"][-1]
        assert d["estado"] == "declaracao_nao_vinculada" and d["semantica_verificada"] is False
        assert c["mental"]["plano_turno_atual"]["ultima_verificacao"]["revisao_suporte_autoria"]["proposicoes"]
    elif c["variante"] != "reparo_valido":
        assert c["fala"] not in c["textos"], "autoria sem cobertura não pode reaparecer como sucesso"
    else:
        # A principal sem suporte recebe um reparo de formato, ainda sujeito
        # à mesma revisão. A referência interna oferecida não vira prova.
        assert [e['tipo'] for e in c['enviados']] == ['principal', 'reparo_json']
        assert len(c["textos"]) == 1 and c["fala"] not in c["textos"][0]
        plano = c["mental"]["plano_turno_atual"]
        assert plano['autoria_revisada_proposta']
        assert plano['ultima_verificacao']['revisao_suporte_autoria']['proposicoes']
    assert not c["efeitos"]
    assert all(a["status"] != "confirmado_por_fonte" for a in c["mental"]["registro_semantico"]["alegacoes"] if a["autor"] == "laylay")


@pytest.mark.skipif(os.environ.get("LAYLAY_EMISSAO_QWEN_REAL") != "1", reason="Inferência local opcional")
@pytest.mark.parametrize("indice", [0, 12])
def test_qwen_real_emite_suporte_sem_pedido_explicito_na_utterance(emissao_instalada, indice):
    r = emissao_instalada[indice]["real"]
    assert r["transportes"] and all(t["status"] == 200 for t in r["transportes"])
    assert len(r["textos"]) == 1
    suporte = r["mental"]["plano_turno_atual"]["suporte_autoria_proposto"]
    d = json.loads(suporte["declaracao"]["_dados_json"])
    assert d["estado"] == "revisao_semantica_pendente" and d["cobertura_textual"] is True
    assert suporte["semantica_verificada"] is suporte["autoriza_execucao"] is False
    assert r["mental"]["registro_semantico"]["declaracoes_suporte_autoria"][-1]["estado"] == "revisao_semantica_pendente"
