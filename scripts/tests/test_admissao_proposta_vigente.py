"""Publicação aceita não autoriza iniciar outra etapa após troca do turno."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_turno import motivo_divergencia_ocorrencia_principal
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from scripts.tests.test_publicacao_ocorrencia_turno import _frame, _nova_ocorrencia, _servicos


@pytest.mark.parametrize("texto,comando", [
    ("abre a Calculadora", {"acao": "open_app", "alvo": "Calculadora"}),
    ("liga a lâmpada", {"acao": "ligar", "alvo": "lampada_quarto"}),
    ("abre o site", {"acao": "open_url", "alvo": "https://example.test"}),
])
@pytest.mark.parametrize("momento", ("controle", "montagem_dispatch", "entre_comandos", "montagem_finalizacao"))
def test_etapa_nao_inicia_quando_montagem_ou_comando_anterior_troca_ocorrencia(texto, comando, momento):
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    chamadas, publicacoes, novos = [], [], []

    def trocar():
        estado.substituir("mental", _nova_ocorrencia(original))
        novos.append(estado.snapshot())

    def vigente(principal):
        mental = estado.snapshot()["mental"]
        return not motivo_divergencia_ocorrencia_principal(principal,
            turno=mental.get("turno_atual"), plano=mental.get("plano_turno_atual"), retrato=mental.get("retrato_turno_atual"))

    def publicar(fase, principal, **campos):
        publicado = composicao.atualizar_proposta(fase, principal, **campos)
        publicacoes.append((fase, bool(publicado)))
        return publicado

    def executar(*_args):
        chamadas.append("executor")
        if momento == "entre_comandos" and chamadas.count("executor") == 1:
            trocar()
        return True

    def montar_dispatch():
        chamadas.append("montagem_dispatch")
        if momento == "montagem_dispatch":
            trocar()
        return {"executar_intencao": executar}

    def montar_finalizacao():
        chamadas.append("montagem_finalizacao")
        if momento == "montagem_finalizacao":
            trocar()
        return {}

    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
        "usar_modo_rapido": lambda *_: False,
        "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda *_: PacotePrompt(())),
        "modelo_llm": SimpleNamespace(executar=lambda *_: ResultadoModelo(json.dumps({"fala": "Vou verificar.", "comandos": [comando, deepcopy(comando)]}), True)),
        "preparar_resposta": lambda _texto, bruto: json.loads(bruto),
        "atualizar_plano_proposta": publicar,
        "proposta_principal_vigente": vigente,
        "contexto_dispatch_runtime": SimpleNamespace(montar=montar_dispatch),
        "executar_comandos_json": executar_comandos_json,
        "contexto_finalizacao_runtime": SimpleNamespace(montar=montar_finalizacao),
        "finalizar_execucao": lambda *_: chamadas.append("finalizacao") or {},
    }, log=lambda *_: None)
    runtime.processar(texto)
    assert publicacoes[0] == ("resposta_planejada", True), "primeira publicação era legítima, writer não é a primeira RED"
    esperados = {
        "controle": ["montagem_dispatch", "executor", "executor", "montagem_finalizacao", "finalizacao"],
        "montagem_dispatch": ["montagem_dispatch"],
        "entre_comandos": ["montagem_dispatch", "executor"],
        "montagem_finalizacao": ["montagem_dispatch", "executor", "executor", "montagem_finalizacao"],
    }
    assert chamadas == esperados[momento], "admissão deve recusar a próxima etapa da ocorrência antiga"
    if novos:
        assert estado.snapshot() == novos[-1]


@pytest.mark.parametrize("retorno", [False, None, {}, "sim", 1])
def test_dispatcher_recusa_guarda_que_nao_confirma_vigencia(retorno):
    efeitos = []
    resultado = executar_comandos_json({
        "proposta_principal_vigente": lambda: retorno,
        "executar_intencao": lambda *_: efeitos.append("canonico"),
        "_executar_comando_conteudo": lambda *_: efeitos.append("legado"),
    }, "abre a Calculadora", [{"acao": "open_app", "alvo": "Calculadora"}, {"acao": "acao_legada"}], "", "comando", False, False, False)
    assert efeitos == []
    assert resultado["erros"]


def test_dispatcher_falha_da_guarda_nao_inicia_executor():
    def falhar():
        raise RuntimeError("estado indisponível")
    efeitos = []
    resultado = executar_comandos_json({"proposta_principal_vigente": falhar,
        "executar_intencao": lambda *_: efeitos.append("executor")}, "abre a Calculadora",
        [{"acao": "open_app", "alvo": "Calculadora"}], "", "comando", False, False, False)
    assert efeitos == [] and resultado["erros"]


def test_composicao_confere_snapshot_sem_publicar_ou_conceder_autoridade():
    original = _frame("como abrir a Calculadora?")
    estado = EstadoCompartilhadoRuntime(mental=original)
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    conferir = getattr(composicao, "proposta_vigente", None)
    assert callable(conferir), "owner do turno deve expor conferência somente leitura"
    principal = ContratoPropostaPrincipal(turno_id=original["turno_atual"]["id"], texto_usuario="como abrir a Calculadora?", resposta_bruta="erro", sucesso_modelo=False)
    antes = estado.snapshot()
    assert conferir(principal) is True
    assert estado.snapshot() == antes
    assert estado.obter_copia("mental", "turno_atual")["autoriza_execucao"] is False
    estado.substituir("mental", _nova_ocorrencia(original))
    antes = estado.snapshot()
    assert conferir(principal) is False and conferir(None) is False
    assert estado.snapshot() == antes


@pytest.fixture(scope="module")
def admissao_instalada(tmp_path_factory):
    codigo = textwrap.dedent(r'''
        import json, os, sys
        from types import SimpleNamespace
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.integracao import instancia_unica
        inicializar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho, *a, **k: inicializar(
            self, os.path.join(os.environ["LAYLAY_ADMISSAO_SQLITE"], os.path.basename(caminho)), *a, **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **k: adquirir(
            str(identificador) + ".admissao-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
        composicao = root._composicao_turno_runtime
        for chave in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime",
                      "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            composicao._servicos[chave] = None
        contexto = root._resposta_ia_runtime._contexto()
        estado = root._estado_compartilhado_runtime
        conferir = contexto.get("proposta_principal_vigente")
        resultados = {"owner_instalado": getattr(conferir, "__self__", None) is composicao, "casos": {}}
        casos = (
            ("app", "abre a Calculadora", {"acao": "open_app", "alvo": "Calculadora"}),
            ("iot", "liga a lâmpada", {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}),
            ("navegador", "abre o site https://example.test", {"acao": "open_url", "alvo": "https://example.test"}),
        )
        for dominio, texto, comando in casos:
            # Duas invocações exigem duas ordens explícitas. A antiga fixture
            # emprestava uma ordem única a duas propostas iguais e mascarava
            # a guarda entre comandos. Manter duas admissões/efeitos esperados.
            texto = texto + "; " + texto
            for momento in ("controle", "montagem_dispatch", "entre_comandos", "montagem_finalizacao"):
                chamadas, publicacoes, novos, validacoes, escopos = [], [], [], [], []
                def trocar():
                    root._iniciar_planejamento_turno(texto, origem="intercalacao_admissao")
                    novos.append(estado.snapshot())
                def executar(*_args):
                    chamadas.append("executor")
                    if momento == "entre_comandos" and chamadas.count("executor") == 1:
                        trocar()
                    return True
                def montar_dispatch():
                    chamadas.append("montagem_dispatch")
                    if momento == "montagem_dispatch": trocar()
                    return {"executar_intencao": executar}
                def montar_finalizacao():
                    chamadas.append("montagem_finalizacao")
                    if momento == "montagem_finalizacao": trocar()
                    return {}
                def publicar(fase, principal, **campos):
                    publicado = contexto["atualizar_plano_proposta"](fase, principal, **campos)
                    publicacoes.append((fase, bool(publicado)))
                    return publicado
                validar = contexto["validar_comandos_planejados"]
                class ValidadorObservado:
                    def __call__(self, comandos): return validar(comandos)
                    def validar_proposta(self, comandos, principal):
                        return validar.validar_proposta(comandos, principal)
                    def validar_proposta_original(self, comandos, principal, extracao):
                        resultado = validar.validar_proposta_original(comandos, principal, extracao)
                        validacoes.append(len(resultado["comandos"]))
                        escopos.append(resultado.get("escopo_operacional_por_ato"))
                        return resultado
                ctx = {
                    "marcar_inicio_turno": root._iniciar_planejamento_turno,
                    "obter_turno_atual": contexto["obter_turno_atual"],
                    "usar_modo_rapido": lambda *_: False,
                    "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda *_: PacotePrompt(())),
                    "modelo_llm": SimpleNamespace(executar=lambda *_: ResultadoModelo(json.dumps({"fala": "Vou verificar.", "comandos": [comando, comando]}), True)),
                    "preparar_resposta": lambda _texto, bruto: json.loads(bruto),
                    "validar_comandos_planejados": ValidadorObservado(),
                    "atualizar_plano_proposta": publicar,
                    "contexto_dispatch_runtime": SimpleNamespace(montar=montar_dispatch),
                    "executar_comandos_json": contexto["executar_comandos_json"],
                    "contexto_finalizacao_runtime": SimpleNamespace(montar=montar_finalizacao),
                    "finalizar_execucao": lambda *_: chamadas.append("finalizacao") or {},
                }
                if callable(conferir): ctx["proposta_principal_vigente"] = conferir
                runtime = root._resposta_ia_runtime
                getter = runtime._contexto_getter
                try:
                    runtime._contexto_getter = lambda: ctx
                    runtime.processar(texto, origem="teste_admissao_instalada")
                finally:
                    runtime._contexto_getter = getter
                resultados["casos"][dominio + ":" + momento] = {
                    "chamadas": chamadas, "publicacoes": publicacoes, "validacoes": validacoes,
                    "novo_preservado": not novos or estado.snapshot() == novos[-1], "escopos": escopos,
                }
        sys.__stdout__.write("ADMISSAO_INSTALADA " + json.dumps(resultados) + "\n")
    ''')
    processo = subprocess.run([sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_ADMISSAO_SQLITE=str(tmp_path_factory.mktemp("admissao"))),
        capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert processo.returncode == 0, processo.stderr[-4000:]
    linhas = [linha.removeprefix("ADMISSAO_INSTALADA ") for linha in processo.stdout.splitlines() if linha.startswith("ADMISSAO_INSTALADA ")]
    assert len(linhas) == 1, processo.stdout[-4000:]
    return json.loads(linhas[0])


@pytest.mark.parametrize("dominio", ("app", "iot", "navegador"))
@pytest.mark.parametrize("momento", ("controle", "montagem_dispatch", "entre_comandos", "montagem_finalizacao"))
def test_runtime_instalado_confere_admissao_apos_montagem_e_entre_comandos(admissao_instalada, dominio, momento):
    assert admissao_instalada["owner_instalado"]
    caso = admissao_instalada["casos"][dominio + ":" + momento]
    assert caso["validacoes"] == [2], json.dumps(caso, ensure_ascii=False)
    assert caso["publicacoes"][0] == ["resposta_planejada", True]
    esperados = {
        "controle": ["montagem_dispatch", "executor", "executor", "montagem_finalizacao", "finalizacao"],
        "montagem_dispatch": ["montagem_dispatch"],
        "entre_comandos": ["montagem_dispatch", "executor"],
        "montagem_finalizacao": ["montagem_dispatch", "executor", "executor", "montagem_finalizacao"],
    }
    assert caso["chamadas"] == esperados[momento]
    assert caso["novo_preservado"]
