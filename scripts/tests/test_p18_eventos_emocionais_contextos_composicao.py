"""P18: ocorrência causal atravessa os owners instalados no root real."""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_composicao_instalada_publica_causa_e_consumidor_preserva_validade(tmp_path):
    codigo = textwrap.dedent(r'''
        import json, os, sys, time
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_P18_MEMORIA_TESTE"])
        iniciar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: iniciar(
            self, str(pasta / Path(caminho or "laylay_memoria.sqlite").name))
        iniciar_resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: iniciar_resumo(
            self, pasta_memoria=str(pasta / "resumo"), **k)
        iniciar_pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: iniciar_pessoas(
            self, caminho=pasta / "pessoas.json", **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
            str(ident) + ".p18-causal-" + str(os.getpid()), **k)
        import laylay as root
        estado = root._estado_compartilhado_runtime
        from mente_laylay.emocoes.contrato_causal import evento_tem_causa_rastreavel
        import mente_laylay.cognicao.contrato_fala as contratos
        decidir = contratos._construir_direcao_social_evento
        decisoes = []
        def uma_decisao(*a, **k):
            resultado = decidir(*a, **k)
            decisoes.append(dict(resultado))
            return resultado
        contratos._construir_direcao_social_evento = uma_decisao
        causas = []
        for dominio in ("jogo", "rotina", "janela"):
            estado.atualizar_campos("mental", turno_atual={}, plano_turno_atual={}, ultima_entrada="")
            estado.substituir("conversacional", {"current_emotion":"calma", "emotion_level":1})
            evento = {"natureza":"evento", "origem":"observador_" + dominio,
                "tipo":"presenca_celebracao", "trace_id":"presenca:" + dominio + ":18",
                "conteudo":"Uma ponte foi observada.", "evidencia":{"itens":["Uma ponte foi observada."],
                "categoria":"celebracao", "dominio":dominio}, "confianca":0.97,
                "timestamp":time.time(), "autoridade_usuario":False, "permissao_execucao":False}
            turno = root._composicao_turno_runtime.iniciar(evento, origem="presenca")
            causal = turno.get("evento_emocional_causal")
            assert evento_tem_causa_rastreavel(causal), "evento instalado sem causa"
            assert estado.mental["eventos_emocionais_causais"]["atual"] == causal
            assert estado.conversacional["episodio_emocional"] == causal
            assert turno["contrato_fala"]["evento_emocional_causal"] == causal
            assert estado.mental["plano_turno_atual"]["evento_emocional_causal"] == causal
            causas.append(causal)
        assert len(decisoes) == 3, "cada evento deve ter uma decisão social"
        agendadas = []
        root._resposta_evento_runtime.agendar_fala_proativa = lambda *a, **k: agendadas.append(a) or True
        resultado = root._resposta_evento_runtime.processar(turno, dominio="jogo", emocao="brava", nivel=3)
        assert agendadas[0][2:4] == ("alegre", 2)
        turno["contrato_fala"]["evento_emocional_causal"]["validade"]["expira_ts"] = 1
        root._resposta_evento_runtime.processar(turno, dominio="jogo", emocao="brava", nivel=3)
        assert agendadas[1][2:4] == ("calma", 1)
        assert len(decisoes) == 3, "materializador não deve selecionar emoção novamente"
        sys.__stdout__.write("P18_CAUSAL " + json.dumps({"causas":causas,
            "decisoes":len(decisoes), "agendamentos":len(agendadas),
            "autoridade":resultado["autoriza_execucao"]}) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_P18_MEMORIA_TESTE=str(tmp_path),
                 GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ", LAYLAY_IOT_MODO="simulado"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4500:]
    dados = next(json.loads(l.removeprefix("P18_CAUSAL ")) for l in processo.stdout.splitlines()
                 if l.startswith("P18_CAUSAL "))
    assert dados["decisoes"] == len(dados["causas"]) == 3
    assert dados["agendamentos"] == 2
    assert dados["autoridade"] is False
