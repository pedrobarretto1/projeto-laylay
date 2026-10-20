"""Declaração da autora conserva proveniência; não certifica proposições."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from copy import deepcopy
from dataclasses import asdict, FrozenInstanceError

import pytest

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal


def _capturar(itens=None, *, fala="A origem tem uma cópia. A estratégia é adequada.", extras=None):
    from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
    itens = itens if itens is not None else [
        {"texto": "A origem tem uma cópia.", "fontes": ["alegacao:100"]},
        {"texto": "A estratégia é adequada.", "fontes": ["fonte:ausente"]}]
    dados = {"fala": fala, "comandos": [], "suporte_proposicoes": itens, **(extras or {})}
    principal = ContratoPropostaPrincipal("turno", "Consulta de teste?", json.dumps(dados, ensure_ascii=False), True)
    return capturar_suporte_autoria(principal, fontes_no_contexto=("alegacao:100",))


def test_ancora_cobertura_e_fonte_existente_nao_certificam_apoio_ou_verdade():
    suporte = _capturar()
    dados = suporte.declaracao.como_dict()
    assert dados["estado"] == "revisao_semantica_pendente" and dados["cobertura_textual"] is True
    assert dados["proposicoes"][0]["fontes_no_contexto"] == ["alegacao:100"]
    assert dados["proposicoes"][1]["fontes_ausentes"] == ["fonte:ausente"]
    assert suporte.semantica_verificada is False and suporte.prova_implicacao is False
    assert suporte.autoriza_execucao is False
    with pytest.raises(FrozenInstanceError):
        suporte.turno_id = "outro"
    dados["proposicoes"][0]["fontes"].append("adulterada")
    assert suporte.declaracao.como_dict()["proposicoes"][0]["fontes"] == ["alegacao:100"]


@pytest.mark.parametrize("itens", [[], [{"texto": "Não consta.", "fontes": []}],
    [{"texto": "A origem tem uma cópia.", "fontes": []}],
    [{"texto": "A estratégia é adequada.", "fontes": []}, {"texto": "A origem tem uma cópia.", "fontes": []}],
    [{"texto": "A origem tem uma cópia.", "fontes": [], "validado": True}],
    [{"texto": "A origem tem uma cópia.", "fontes": ["alegacao:100", "alegacao:100"]}],
    [{"texto": "A origem tem uma cópia.", "fontes": [True]}]])
def test_proposta_parcial_malformada_fora_da_ordem_ou_autoaprovada_fica_invalida(itens):
    dados = _capturar(itens).declaracao.como_dict()
    assert dados["estado"] == "declaracao_invalida"
    assert not dados["proposicoes"] and dados["cobertura_textual"] is False


def test_trecho_repetido_nao_ganha_identidade_por_proximidade():
    dados = _capturar([{"texto": "A origem tem uma cópia.", "fontes": []}],
        fala="A origem tem uma cópia. A origem tem uma cópia.").declaracao.como_dict()
    assert dados["estado"] == "declaracao_invalida"


def test_envelope_duplicado_e_objeto_proposto_nao_criam_fonte_do_host():
    from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
    principal = ContratoPropostaPrincipal("turno", "Consulta?",
        '{"fala":"A origem tem cópia.","suporte_proposicoes":[],"suporte_proposicoes":[]}', True)
    assert capturar_suporte_autoria(principal).declaracao.como_dict()["estado"] == "declaracao_invalida"
    assert capturar_suporte_autoria(asdict(principal)) is None
    sem_campo = ContratoPropostaPrincipal("turno", "Consulta?", '{"fala":"A origem tem cópia."}', True)
    assert capturar_suporte_autoria(sem_campo) is None


@pytest.mark.parametrize("divergencia", ["nenhuma", "fala", "turno", "json"])
def test_registro_conserva_pendencia_e_nao_materializa_fontes_ou_efeitos(divergencia):
    from mente_laylay.memoria_mental.registro_semantico import registrar_interacao_semantica
    suporte = _capturar()
    fala, turno = suporte.fala_original, suporte.turno_id
    if divergencia == "fala":
        fala = "A resposta foi corrigida antes de ser publicada."
    elif divergencia == "turno":
        turno = "outro"
    elif divergencia == "json":
        suporte = asdict(suporte)
    r = registrar_interacao_semantica(None, texto_usuario="Consulta de teste?", resposta_laylay=fala,
        fonte_resposta="contexto_global", suporte_autoria=suporte, turno_id=turno, agora=100)
    declaracao = r["declaracoes_suporte_autoria"][-1]
    assert declaracao["estado"] == ("revisao_semantica_pendente" if divergencia == "nenhuma" else "declaracao_nao_vinculada")
    assert declaracao["semantica_verificada"] is False and declaracao["autoriza_execucao"] is False
    assert all(not i["fonte"] and i["status"] != "confirmado_por_fonte" for i in r["alegacoes"] if i["autor"] == "laylay")
    repetido = registrar_interacao_semantica(r, texto_usuario="Consulta de teste?", resposta_laylay=fala,
        fonte_resposta="contexto_global", suporte_autoria=suporte, turno_id=turno, agora=101)
    assert repetido["declaracoes_suporte_autoria"] == r["declaracoes_suporte_autoria"]


def test_declaracao_pendente_nao_ganha_memoria_duravel_na_renovacao():
    from mente_laylay.memoria_mental.registro_semantico import registrar_interacao_semantica, renovar_registro_semantico_sessao
    suporte = _capturar()
    r = registrar_interacao_semantica(None, texto_usuario=suporte.texto_usuario,
        resposta_laylay=suporte.fala_original, suporte_autoria=suporte, turno_id=suporte.turno_id, agora=100)
    assert r["declaracoes_suporte_autoria"]
    assert renovar_registro_semantico_sessao(r, agora=101)["declaracoes_suporte_autoria"] == []


@pytest.fixture(scope="module")
def autoria_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("declaracao_suporte_instalada")
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        assert not os.environ.get("LAYLAY_SONDA_ESCOPO_BASELINE")
        root = preparar_instalacao_isolada(Path(os.environ["LAYLAY_AUTORIA_MEMORIA_TESTE"]))
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        modelo_instalado = RegistroModeloLLM.executar
        def descrever_pedido(pedido):
            dados = {f.name: getattr(pedido, f.name) for f in dataclasses.fields(pedido) if f.name != "contrato_saida"}
            dados["contrato_saida"] = pedido.contrato_saida.response_format if pedido.contrato_saida else None
            return dados
        root._voz_runtime.falar = lambda *_a, **_k: False
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError("USB proibido"))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError("TCP proibido"))
        estado = root._estado_compartilhado_runtime
        runtime = root._resposta_ia_runtime
        contexto_original = runtime._contexto_getter
        textos, casos = [], []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, partes in (("arquivo", ["O arquivo alfa tem uma cópia.", "A estratégia de restauração é adequada."]),
                                ("iot", ["A tomada da sala tem proteção elétrica.", "A estratégia de alimentação é adequada."])):
            for modo in (False, True):
                estado.substituir("mental", criar_estado_mental_inicial())
                estado.atualizar_campos("memoria_conversa", messages=[])
                fala = " ".join(partes)
                proposta = [{"texto": partes[0], "fontes": ["fonte_de_contexto_simulada"]},
                            {"texto": partes[1], "fontes": ["alegacao:inexistente"]}]
                bruto = json.dumps({"fala": fala, "comandos": [], "suporte_proposicoes": proposta}, ensure_ascii=False)
                modelos, efeitos = [], []
                def gerar(self, pedido):
                    modelos.append(descrever_pedido(pedido))
                    return ResultadoModelo(bruto, True)
                RegistroModeloLLM.executar = gerar
                contexto = contexto_original()
                marcar = contexto["marcar_inicio_turno"]
                def inicio(*a, **k):
                    resultado = marcar(*a, **k)
                    estado.atualizar_campos("mental", fundamentacao_factual_turno={"confiavel": True,
                        "fonte": "fonte_de_contexto_simulada"})
                    return resultado
                contexto["marcar_inicio_turno"] = inicio
                contexto["usar_modo_rapido"] = lambda _t: modo
                def impedir_efeito(pedido, texto):
                    efeitos.append(pedido)
                    raise AssertionError("Autoria não autoriza efeito externo.")
                contexto["contexto_dispatch_runtime"] = SimpleNamespace(montar=lambda: {"executar_intencao": impedir_efeito})
                runtime._contexto_getter = lambda: contexto
                inicio_textos = len(textos)
                runtime.processar("Quais informações você tem sobre esse exemplo?", origem="teste_declaracao_suporte")
                caso = {"dominio": dominio, "modo": "rapido" if modo else "normal", "fala": fala,
                    "partes": partes, "proposta": proposta, "bruto": bruto, "modelos": modelos, "efeitos": efeitos,
                    "textos": textos[inicio_textos:], "mental": estado.retrato_dominio("mental")}
                if os.environ.get("LAYLAY_AUTORIA_QWEN_REAL") == "1" and modo == (dominio == "iot"):
                    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                    selecao, transportes, modelos_reais = selecao_local(), [], []
                    requests.sessions.Session.request = criar_guarda_http_local(selecao, transportes, http_original)
                    estado.substituir("mental", criar_estado_mental_inicial())
                    estado.atualizar_campos("memoria_conversa", messages=[])
                    def gerar_real(self, pedido):
                        resultado = modelo_instalado(self, pedido)
                        modelos_reais.append({"pedido": descrever_pedido(pedido), "resultado": dataclasses.asdict(resultado)})
                        return resultado
                    RegistroModeloLLM.executar = gerar_real
                    pergunta_real = ("Neste exemplo fictício, responda exatamente com estas duas frases: " + fala
                        + " No JSON da resposta, inclua também suporte_proposicoes com estes dados declarados, "
                        "sem afirmar que foram verificados: " + json.dumps(proposta, ensure_ascii=False))
                    inicio_textos = len(textos)
                    runtime.processar(pergunta_real, origem="teste_autoria_qwen_real")
                    caso["real"] = {"selecao": selecao, "modelos": modelos_reais, "transportes": transportes,
                        "textos": textos[inicio_textos:], "mental": estado.retrato_dominio("mental")}
                casos.append(caso)
        runtime._contexto_getter = contexto_original
        sys.__stdout__.write("AUTORIA_INSTALADA " + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + "\n")
    ''')
    processo = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_AUTORIA_MEMORIA_TESTE=str(pasta)),
        capture_output=True, text=True, encoding="utf-8",
        timeout=180 if os.environ.get("LAYLAY_AUTORIA_QWEN_REAL") == "1" else 60)
    assert processo.returncode == 0, processo.stdout[-2000:] + processo.stderr[-5000:]
    dados = json.loads(next(l.removeprefix("AUTORIA_INSTALADA ") for l in processo.stdout.splitlines() if l.startswith("AUTORIA_INSTALADA ")))
    if caminho := os.environ.get("LAYLAY_EVIDENCIA_AUTORIA"):
        with Path(caminho).open("x", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize("indice", range(4))
def test_composicao_conserva_declaracao_sem_transformar_proposta_em_fato(autoria_instalada, indice):
    caso = autoria_instalada[indice]
    assert caso["modelos"] and len(caso["textos"]) == 1 and caso["textos"] != [caso["fala"]]
    plano = caso["mental"]["plano_turno_atual"]
    assert "suporte_autoria_proposto" in plano
    registro = caso["mental"]["registro_semantico"]
    declaracao = registro["declaracoes_suporte_autoria"][-1]
    assert declaracao["cobertura_textual"] is False
    assert declaracao["semantica_verificada"] is False
    assert declaracao["estado"] == "declaracao_nao_vinculada"
    original = json.loads(plano["suporte_autoria_proposto"]["declaracao"]["_dados_json"])
    assert original["estado"] == "revisao_semantica_pendente" and original["cobertura_textual"] is True
    assert [p["texto"] for p in original["proposicoes"]] == caso["partes"]
    assert [p["fontes"] for p in original["proposicoes"]] == [p["fontes"] for p in caso["proposta"]]
    alegacoes = {a["texto"]: a for a in registro["alegacoes"] if a["autor"] == "laylay"}
    for parte in caso["partes"]:
        assert parte not in alegacoes
    assert not caso["efeitos"] and not plano.get("comandos")


@pytest.mark.skipif(os.environ.get("LAYLAY_AUTORIA_QWEN_REAL") != "1", reason="Inferência local real opcional.")
@pytest.mark.parametrize("indice", [0, 3])
def test_qwen_real_conserva_proposta_sem_emprestar_suporte_a_fala_substituta(autoria_instalada, indice):
    real = autoria_instalada[indice]["real"]
    assert real["modelos"] and real["transportes"]
    assert all(t["status"] == 200 for t in real["transportes"])
    assert len(real["textos"]) == 1
    # A emissão pode ser substituída pelo juiz instalado. O suporte pertence
    # à emissão original, não ganha o texto da contingência como nova âncora.
    suporte = real["mental"]["plano_turno_atual"]["suporte_autoria_proposto"]
    proposta = json.loads(suporte["declaracao"]["_dados_json"])
    assert proposta["estado"] == "revisao_semantica_pendente" and proposta["cobertura_textual"] is True
    assert [p["fontes"] for p in proposta["proposicoes"]] == [p["fontes"] for p in autoria_instalada[indice]["proposta"]]
    registro = real["mental"]["registro_semantico"]
    assert registro["declaracoes_suporte_autoria"]
    d = registro["declaracoes_suporte_autoria"][-1]
    mesma_fala = suporte["fala_original"] == real["textos"][0]
    assert d["estado"] == ("revisao_semantica_pendente" if mesma_fala else "declaracao_nao_vinculada")
    assert d["cobertura_textual"] is mesma_fala
    if not mesma_fala:
        assert not d["proposicoes"]
    assert d["semantica_verificada"] is False and d["prova_implicacao"] is False
    assert all(a["status"] != "confirmado_por_fonte" for a in registro["alegacoes"] if a["autor"] == "laylay")
