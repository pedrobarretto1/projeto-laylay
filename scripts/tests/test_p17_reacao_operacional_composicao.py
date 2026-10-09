"""P17 pela composição instalada: publicação, avaliação e autoria do mesmo receipt.

Receipts aqui são entradas controladas; a prova de efeito externo pertence ao
executor no runtime e não é afirmada por esta integração.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_reacao_instalada_distingue_redundancia_de_falha_do_sistema(tmp_path: Path) -> None:
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
            str(identificador) + ".p17-reacao-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional

        ctx = root._contexto_intencao_runtime.montar()
        instalacao = {
            "registrador": ctx["_registrar_resultado_execucao"] == root._registrar_resultado_execucao,
            "avaliador": ctx["_avaliar_evento_emocional_operacional"] is root._avaliar_evento_emocional_operacional,
        }
        prompts = []
        entregas = []
        def modelo(mensagens, **kwargs):
            contrato = json.loads(mensagens[1]["content"])
            prompts.append({
                "regra": mensagens[0]["content"],
                "contrato": contrato,
                "tipo": kwargs.get("_tipo_chamada"),
            })
            if (
                contrato["intent"] == "APP_OPEN"
                and contrato["reacao_causal"].get("intensidade") == "alta"
            ):
                return "__LAYLAY_LLM_TIMEOUT__"
            return contrato["fala_segura"]
        ctx["enviar_mensagem"] = modelo
        ctx["_falar_resultado_operacional"] = lambda *args: entregas.append(args)
        ctx["falar_com_lipsync"] = lambda *args: entregas.append(args)
        saida = {"instalacao": instalacao, "casos": {}}
        for intent, alvo, status, executou, confirmado in (
            ("APP_OPEN", "Calculadora", "ja_aberto_focado", False, True),
            ("CREATE_FILE", "anotações.txt", "falha_execucao", False, False),
        ):
            casos = []
            for indice in range(4):
                texto = ("abre a Calculadora" if intent == "APP_OPEN"
                         else "escreva em anotações.txt")
                root._iniciar_planejamento_turno(texto, origem="teste_p17_composicao")
                pedido = {"intent": intent, "id_solicitacao": f"p17-{intent}-{indice}"}
                adaptador = AdaptadorResultadoOperacional(
                    pedido, {"alvo": alvo}, texto, "pc_a", ctx,
                )
                adaptador.marcar_resultado(status, executou, confirmado=confirmado)
                antes = len(prompts)
                antes_entregas = len(entregas)
                fala = (f"{alvo} já estava como pedido; não repeti a ação."
                        if confirmado else f"Não consegui concluir a ação em {alvo}.")
                adaptador.falar_por_status(
                    status, fala, alvo=alvo, executou=executou,
                    confirmado=confirmado,
                )
                avaliacao = root._avaliador_eventos_emocionais_runtime.diagnostico()["ultima"]
                casos.append({
                    "receipt": root._estado_compartilhado_runtime.obter_copia(
                        "mental", "plano_turno_atual",
                    ).get("comandos", [])[-1],
                    "avaliacao": avaliacao,
                    "regra": prompts[antes]["regra"] if len(prompts) > antes else "",
                    "falou": len(entregas) > antes_entregas,
                    "fala": entregas[-1][1] if len(entregas) > antes_entregas else "",
                    "emocao_fala": entregas[-1][2] if len(entregas) > antes_entregas else "",
                    "nivel_fala": entregas[-1][3] if len(entregas) > antes_entregas else 0,
                })
            saida["casos"][intent] = casos
        sys.__stdout__.write("P17_COMPOSICAO " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_SONDA_SQLITE=str(tmp_path)),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4000:]
    saida = next(
        json.loads(linha.removeprefix("P17_COMPOSICAO "))
        for linha in processo.stdout.splitlines()
        if linha.startswith("P17_COMPOSICAO ")
    )
    assert all(saida["instalacao"].values())
    for intent, casos in saida["casos"].items():
        assert len(casos) == 4
        for caso in casos:
            assert caso["receipt"]["origem"] == "executor"
            assert caso["receipt"]["id_solicitacao"] == caso["avaliacao"]["evidencia_ref"]
            assert caso["avaliacao"]["autoriza_execucao"] is False
            assert caso["falou"] is True
        assert casos[-1]["avaliacao"]["emocao"] == "brava"
        regra = casos[-1]["regra"]
        assert bool("recusar o retrabalho redundante" in regra) is (intent == "APP_OPEN")
    assert saida["casos"]["APP_OPEN"][-1]["receipt"]["executou"] is False
    assert saida["casos"]["APP_OPEN"][-1]["emocao_fala"] == "brava"
    assert saida["casos"]["APP_OPEN"][-1]["nivel_fala"] == 3
    assert "não repeti" in saida["casos"]["APP_OPEN"][-1]["fala"]
    assert saida["casos"]["CREATE_FILE"][-1]["receipt"]["confirmado"] is False
