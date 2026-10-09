"""Procedência semântica no preparador e publicador instalados por laylay.py.

O subprocesso mantém o runtime, o preparador, a extração semântica, o
validador e o publicador transacional reais. Transporte do modelo, retorno
do reparo JSON, persistência, execução externa e fala são portas isoladas.
Nenhum receipt desta sonda representa um efeito físico.
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
def procedencia_composicao() -> dict:
    codigo = textwrap.dedent(r'''
        import json
        import os
        import sys
        from types import SimpleNamespace
        from mente_laylay.integracao import instancia_unica

        adquirir_real = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir_real(
            str(identificador) + ".sonda-procedencia-semantica-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.autonomia import processamento_resposta_ia as processamento
        from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
        from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo

        estado = root._estado_compartilhado_runtime
        composicao = root._composicao_turno_runtime
        composicao._servicos["_coleta_entradas_neurais"] = None
        contexto = root._resposta_ia_runtime._contexto()
        preparar_instalado = contexto["preparar_resposta"]
        publicar_instalado = contexto["registrar_leitura_proposta"]
        validar_instalado = contexto["validar_comandos_planejados"]
        root.MEMORIA_SQLITE = None
        root._registrar_autocorrecao_virtual = lambda *_args, **_kwargs: None
        root._memoria_conversa_get = lambda _chave, padrao=None: padrao
        logs = []
        root.print = lambda *args, **_kwargs: logs.append(" ".join(str(item) for item in args))
        texto = "antes eu estava triste, mas agora estou aliviado"
        reparada = json.dumps({
            "fala": "Que bom que agora você está aliviado.", "comandos": [],
            "leitura_turno": ["relato"],
            "leitura_emocional": {
                "estado_usuario": "tristeza", "intensidade": 2,
                "causa_expressa": "antes eu estava triste",
                "trecho_evidencia": "eu estava triste", "confianca": 0.95,
            },
        }, ensure_ascii=False)

        resultados = {"instalacao": {
            "runtime_root": root._resposta_ia_runtime is not None,
            "preparador": callable(preparar_instalado),
            "publisher_owner": getattr(publicar_instalado, "__self__", None) is composicao,
            "validador_original": callable(getattr(validar_instalado, "validar_proposta_original", None)),
        }, "casos": {}}
        for modo in ("nenhum", "ausente", "alivio", "sem_reparo", "obsoleta"):
            dados = {"fala": "Que bom que agora você está aliviado.", "comandos": []}
            if modo != "ausente":
                dados["leitura_turno"] = ["relato"]
                dados["leitura_emocional"] = {
                    "estado_usuario": "nenhum", "intensidade": 0,
                    "causa_expressa": "", "trecho_evidencia": "", "confianca": 0.0,
                }
            if modo in ("alivio", "sem_reparo"):
                dados["leitura_emocional"] = {
                    "estado_usuario": "alivio", "intensidade": 1,
                    "causa_expressa": "agora estou aliviado",
                    "trecho_evidencia": "agora estou aliviado", "confianca": 0.95,
                }
            original = json.dumps(dados, ensure_ascii=False)
            chamadas = []
            preparadas = []
            snapshot_novo = []
            evento_antes = []
            logs.clear()

            def emitir(pedido):
                chamadas.append(pedido.tipo_chamada)
                return ResultadoModelo(original, True)

            modelo_isolado = SimpleNamespace(
                executar=emitir, diagnostico=lambda: {"disponivel": True},
            )
            root._registro_modelo_llm_runtime = modelo_isolado

            def reparar(_texto, bruto, _enviar):
                assert bruto == original, "reparo recebe a emissão principal capturada"
                if modo == "sem_reparo":
                    return None
                chamadas.append("retorno_reparo_json")
                if modo == "obsoleta":
                    root._iniciar_planejamento_turno(texto, origem="sonda_semantica_concorrente")
                    snapshot_novo.append(estado.snapshot())
                return reparada

            def preparar(entrada, bruto):
                evento_antes.append(estado.obter_copia("mental", "plano_turno_atual").get("evento_emocional_causal"))
                resultado = preparar_instalado(entrada, bruto)
                preparadas.append(resultado)
                return resultado

            def dispatch(_ctx, _texto, comandos, *_args):
                chamadas.append("dispatch")
                assert comandos == [], "o relato não autoriza efeitos externos"
                return {"erros": []}

            def finalizar(*_args):
                chamadas.append("finalizacao")
                return {"fala": "Que bom que agora você está aliviado."}

            ctx = {
                "marcar_inicio_turno": root._iniciar_planejamento_turno,
                "obter_turno_atual": contexto["obter_turno_atual"],
                "usar_modo_rapido": lambda _texto: False,
                "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
                "modelo_llm": modelo_isolado,
                "preparar_resposta": preparar,
                "validar_comandos_planejados": validar_instalado,
                "atualizar_plano_turno": contexto["atualizar_plano_turno"],
                "atualizar_plano_proposta": contexto["atualizar_plano_proposta"],
                "registrar_leitura_semantica_principal": contexto["registrar_leitura_semantica_principal"],
                "registrar_leitura_proposta": publicar_instalado,
                "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
                "executar_comandos_json": dispatch,
                "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
                "finalizar_execucao": finalizar,
            }
            runtime = root._resposta_ia_runtime
            getter_real = runtime._contexto_getter
            corretor_real = processamento.corrigir_saida_malformada_da_ia
            try:
                runtime._contexto_getter = lambda: ctx
                processamento.corrigir_saida_malformada_da_ia = reparar
                tratado = runtime.processar(texto, origem="sonda_procedencia_semantica")
            finally:
                runtime._contexto_getter = getter_real
                processamento.corrigir_saida_malformada_da_ia = corretor_real
            preparada = preparadas[0] if preparadas else {}
            plano = estado.obter_copia("mental", "plano_turno_atual")
            turno = estado.obter_copia("mental", "turno_atual")
            resultados["casos"][modo] = {
                "tratado": tratado, "chamadas": chamadas,
                "original_extraida": processamento.extrair_leitura_semantica_da_ia(original, texto),
                "principal_preparada": preparada.get("leitura_semantica"),
                "reparo_preparado": preparada.get("leitura_semantica_reparada"),
                "fala_preparada": preparada.get("fala"),
                "principal_publicada": turno.get("leitura_semantica_principal"),
                "evento_antes": evento_antes[0] if evento_antes else None,
                "evento_final": plano.get("evento_emocional_causal"),
                "fase": plano.get("fase"), "autoriza": turno.get("autoriza_execucao"),
                "snapshot_novo_preservado": bool(snapshot_novo and estado.snapshot() == snapshot_novo[-1]),
                "logs": logs[-20:],
            }

        turno = root._iniciar_planejamento_turno(texto, origem="sonda_injecao_leitura")
        principal = ContratoPropostaPrincipal(
            turno_id=turno["id"], texto_usuario=texto,
            resposta_bruta=json.dumps({"fala": "Entendi.", "comandos": []}),
        )
        leitura_forjada = processamento.extrair_leitura_semantica_da_ia(reparada, texto)
        antes = estado.snapshot()
        publicada = publicar_instalado(texto, leitura_forjada, principal)
        resultados["injecao"] = {
            "forjada_validada": leitura_forjada.get("valida"),
            "recusada": publicada == {}, "snapshot_preservado": estado.snapshot() == antes,
        }
        sys.__stdout__.write("PROCEDENCIA_SEMANTICA_COMPOSICAO " + json.dumps(resultados, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True,
        text=True, encoding="utf-8", timeout=60,
    )
    assert processo.returncode == 0, processo.stderr[-4000:]
    linhas = [
        linha.removeprefix("PROCEDENCIA_SEMANTICA_COMPOSICAO ")
        for linha in processo.stdout.splitlines()
        if linha.startswith("PROCEDENCIA_SEMANTICA_COMPOSICAO ")
    ]
    assert len(linhas) == 1, "a composição precisa publicar a evidência semântica"
    return json.loads(linhas[0])


def test_composicao_preserva_owners_semanticos_instalados(procedencia_composicao: dict) -> None:
    assert all(procedencia_composicao["instalacao"].values())


@pytest.mark.parametrize("modo", ("nenhum", "ausente", "alivio"))
def test_preparador_instalado_conserva_original_e_separa_leitura_do_reparo(
    procedencia_composicao: dict, modo: str,
) -> None:
    caso = procedencia_composicao["casos"][modo]
    assert caso["chamadas"][0] == "principal"
    assert caso["principal_preparada"] == caso["original_extraida"], "primeira fronteira: leitura do reparo não substitui a original"
    assert caso["reparo_preparado"]["origem"] == "resposta_reparada"
    assert caso["reparo_preparado"]["leitura_emocional"]["estado_usuario"] == "tristeza"
    assert caso["fala_preparada"] == "Que bom que agora você está aliviado."


@pytest.mark.parametrize("modo", ("nenhum", "ausente"))
def test_runtime_instalado_nao_cria_evento_do_reparo_e_conclui_resposta(
    procedencia_composicao: dict, modo: str,
) -> None:
    caso = procedencia_composicao["casos"][modo]
    assert caso["chamadas"] == ["principal", "retorno_reparo_json", "dispatch", "finalizacao"]
    publicada = caso["principal_publicada"] or {}
    emocional = publicada.get("leitura_emocional") or {}
    assert emocional.get("valida") is not True
    assert caso["evento_final"] == caso["evento_antes"], "reparo não produz evento semântico principal"
    assert caso["autoriza"] is False
    assert caso["fase"] == "executado"


def test_runtime_instalado_publica_leitura_original_valida_apesar_de_reparo_divergente(
    procedencia_composicao: dict,
) -> None:
    caso = procedencia_composicao["casos"]["alivio"]
    assert caso["principal_publicada"]["origem"] == "llm_principal"
    assert caso["principal_publicada"]["leitura_emocional"]["estado_usuario"] == "alivio"
    assert caso["principal_publicada"]["somente_observacao"] is True
    assert caso["autoriza"] is False
    assert caso["chamadas"] == ["principal", "retorno_reparo_json", "dispatch", "finalizacao"]


@pytest.mark.parametrize("modo", ("alivio", "sem_reparo"))
def test_runtime_nao_promove_tristeza_passada_ao_evento_atual(
    procedencia_composicao: dict, modo: str,
) -> None:
    caso = procedencia_composicao["casos"][modo]
    assert caso["evento_antes"] is None, "primeira fronteira: tristeza passada não recebe o verbo estou de outra oração"
    assert caso["principal_publicada"]["leitura_emocional"]["estado_usuario"] == "alivio"
    evento = caso["evento_final"]
    assert evento["origem"] == "leitura_semantica_principal"
    assert evento["causa"] == "agora estou aliviado"
    assert evento["sensibilidade"] == "sensivel"
    assert evento["permite_expressao"] is False
    assert evento["autoriza_execucao"] is False
    assert caso["autoriza"] is False
    assert caso["fase"] == "executado"


def test_preparador_instalado_sem_reparo_preserva_original_sem_inventar_diagnostico(
    procedencia_composicao: dict,
) -> None:
    caso = procedencia_composicao["casos"]["sem_reparo"]
    assert caso["principal_preparada"] == caso["original_extraida"]
    assert not caso["reparo_preparado"]
    assert caso["chamadas"] == ["principal", "dispatch", "finalizacao"]


def test_runtime_instalado_recusa_ocorrencia_substituida_durante_reparo(
    procedencia_composicao: dict,
) -> None:
    caso = procedencia_composicao["casos"]["obsoleta"]
    assert caso["chamadas"] == ["principal", "retorno_reparo_json"]
    assert caso["snapshot_novo_preservado"]


def test_publicador_instalado_recusa_leitura_valida_ausente_da_emissao_original(
    procedencia_composicao: dict,
) -> None:
    caso = procedencia_composicao["injecao"]
    assert caso["forjada_validada"] is True, "a normalização textual deve alcançar a fronteira de procedência"
    assert caso["recusada"], "mesmo frame e rótulo principal não provam origem da leitura"
    assert caso["snapshot_preservado"]
