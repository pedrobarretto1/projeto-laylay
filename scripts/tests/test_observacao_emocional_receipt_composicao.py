"""Observação antes da fala, usando registrador/avaliador/mente instalados.

O subprocesso importa o composition root sem iniciar desktop. Os resultados
locais exercitam publicação; não comprovam efeitos nem áudio físicos.
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
def observacao_instalada(tmp_path_factory):
    codigo = textwrap.dedent(r'''
        import json
        import os
        import sys
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.integracao import instancia_unica

        inicializar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho, *a, **k: inicializar(
            self, os.path.join(os.environ["LAYLAY_SONDA_SQLITE"], os.path.basename(caminho)), *a, **k,
        )
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir(
            str(identificador) + ".observacao-receipt-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional

        estado = root._estado_compartilhado_runtime
        composicao = root._composicao_turno_runtime
        for nome in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime",
                     "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
            composicao._servicos[nome] = None
        namespace = dict(root._adaptadores_aplicacao_runtime._ns())
        for nome in ("_especialista_neural_comandos_runtime", "_motor_aprendizado_runtime",
                     "_mapa_habilidades_runtime", "_rede_associativa_runtime"):
            namespace[nome] = None
        root._adaptadores_aplicacao_runtime._namespace_getter = lambda: namespace
        ctx = root._contexto_intencao_runtime.montar()
        saida = {"instalacao": {
            "registrador": ctx["_registrar_resultado_execucao"] == root._registrar_resultado_execucao,
            "avaliador": ctx["_avaliar_evento_emocional_operacional"] is root._avaliar_evento_emocional_operacional,
            "estado": root._estado_contexto_runtime._estado() is estado,
        }, "casos": {}}
        ctx.pop("falar_com_lipsync", None)
        for intent, sucesso in (("CREATE_FILE", "conteudo_atualizado"), ("APP_OPEN", "app_iniciado_focado")):
            alvo = "controle-" + intent.lower()
            texto = "escreva no arquivo " + alvo if intent == "CREATE_FILE" else "abra o aplicativo " + alvo
            etapas = []
            for indice, status in enumerate(("falha_execucao", "falha_execucao", sucesso)):
                root._iniciar_planejamento_turno(texto, origem="teste_observacao_instalada")
                antes = root._avaliador_eventos_emocionais_runtime.diagnostico()["avaliados"]
                pedido = {"intent": intent, "id_solicitacao": intent + str(indice)}
                adaptador = AdaptadorResultadoOperacional(pedido, {"alvo": alvo}, texto, "pc_a", ctx)
                ok = indice == 2
                adaptador.marcar_resultado(status, ok, confirmado=ok)
                diagnostico = root._avaliador_eventos_emocionais_runtime.diagnostico()
                retrato = estado.snapshot()["conversacional"]
                plano = estado.obter_copia("mental", "plano_turno_atual")
                etapas.append({
                    "observacoes": diagnostico["avaliados"] - antes,
                    "avaliacao": diagnostico["ultima"],
                    "estado": {"emocao": retrato.get("current_emotion"), "episodio": retrato.get("episodio_emocional")},
                    "comandos": plano.get("comandos"),
                })
            saida["casos"][intent] = etapas
        sys.__stdout__.write("OBSERVACAO_RECEIPT " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8",
                 LAYLAY_SONDA_SQLITE=str(tmp_path_factory.mktemp("observacao-sqlite"))),
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert processo.returncode == 0, processo.stderr[-3000:]
    resultado = next(linha.removeprefix("OBSERVACAO_RECEIPT ") for linha in processo.stdout.splitlines()
                     if linha.startswith("OBSERVACAO_RECEIPT "))
    return json.loads(resultado)


def test_contexto_continua_usando_os_owners_instalados(observacao_instalada):
    assert all(observacao_instalada["instalacao"].values())


@pytest.mark.parametrize("intent", ["CREATE_FILE", "APP_OPEN"])
def test_publicacao_instalada_observa_sem_fala_e_transiciona_estado(observacao_instalada, intent):
    etapas = observacao_instalada["casos"][intent]
    assert [e["observacoes"] for e in etapas] == [1, 1, 1]
    assert [e["avaliacao"]["arco"] for e in etapas] == ["neutro", "irritacao_compartilhada", "alivio"]
    assert etapas[1]["estado"]["emocao"] == "irritada"
    assert etapas[2]["estado"]["emocao"] == "acalmando-se"
    for etapa in etapas:
        receipt = etapa["comandos"][0]
        assert receipt["origem"] == "executor"
        assert etapa["avaliacao"]["evidencia_ref"] == receipt["id_solicitacao"]
        assert etapa["avaliacao"]["autoriza_execucao"] is False
