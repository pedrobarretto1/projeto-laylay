"""P21: diagnóstico e publicação textual pelo root, em uma sequência causal.

Entradas causais são controladas; memória isolada e voz silenciosa. Não é
prova de geração semântica real, som físico ou efeito de executor externo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("contexto", ["terminal", "chat"])
def test_transicoes_instaladas_preservam_causa_resultado_e_uma_publicacao(tmp_path: Path, contexto: str):
    codigo = textwrap.dedent(r'''
        import hashlib, json, os, sys, time
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
        from mente_laylay.integracao import instancia_unica
        pasta = Path(os.environ["LAYLAY_P21_MEMORIA"])
        sql = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, db_path=None: sql(self, str(pasta / "memoria.sqlite"))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
        central = CentralNotificacoesRuntime.__init__
        CentralNotificacoesRuntime.__init__ = lambda self, arquivo_estado, **k: central(self, str(pasta / "central.json"), **k)
        mutex = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: mutex(str(ident) + ".p21-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        from mente_laylay.memoria_mental.formatacao_diagnostico import formatar_diagnostico_terminal
        estado = root._estado_compartilhado_runtime
        voz = root._voz_runtime
        chamadas = []
        def bloquear_modelo(*a, **k):
            chamadas.append(k)
            raise AssertionError("diagnóstico e projeção não chamam modelo")
        RegistroModeloLLM.executar = bloquear_modelo
        voz.definir_modo_silencioso(True)
        textos = []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda texto, emocao, nivel, **k: textos.append([texto, emocao, nivel]))
        contexto = os.environ["LAYLAY_P21_CONTEXTO"]
        root._atualizar_estado_modo_chat(contexto == "chat")
        turno = root._iniciar_planejamento_turno("vamos conversar", origem="terminal")
        plano_original = estado.obter_copia("mental", "plano_turno_atual", {})
        assert not plano_original["requer_execucao"], "controle: conversa não autoriza executor"
        def publicar(ref, emocao, nivel, responsabilidade):
            evento = criar_evento_emocional_causal(
                origem="resultado_operacional", causa="causa controlada de transição",
                evidencia_ref=ref, natureza_evidencia="fato_observado", confianca=.97,
                relevancia=.95, responsabilidade=responsabilidade, intensidade=nivel,
                permite_expressao=True, emocao=emocao, nivel=nivel, ts=time.time())
            assert root._estado_contexto_runtime.publicar_evento_emocional_causal(evento, vincular_plano=False)
            aplicado = root._definir_emocao_conversacional(emocao, nivel, evento["causa"])
            return evento, aplicado
        forte, aplicado = publicar("p21:forte", "brava", 3, "usuario")
        assert aplicado
        fraco, aplicado = publicar("p21:fraco", "surpresa", 1, "sistema")
        assert not aplicado, "controle: evento fraco não substitui episódio forte"
        assert estado.mental["eventos_emocionais_causais"]["atual"] == fraco
        assert estado.conversacional["episodio_emocional"] == forte
        antes = json.loads(json.dumps(dict(estado.conversacional)))
        diagnostico = root._diagnostico_mente_runtime.snapshot()
        retrato = diagnostico["estado_emocional_causal"]
        ref_forte = "causa:" + hashlib.sha256(forte["evidencia_ref"].encode()).hexdigest()[:16]
        ref_fraco = "causa:" + hashlib.sha256(fraco["evidencia_ref"].encode()).hexdigest()[:16]
        assert retrato["emocao_expressavel"] == "brava"
        assert retrato["causa_ref"] == ref_forte, "primeira fronteira: causa exibida não pertence ao episódio selecionado"
        assert retrato["evento_observado_ref"] == ref_fraco
        assert retrato["fonte_causa"] == "episodio_expressavel"
        assert estado.conversacional == antes and estado.mental["plano_turno_atual"] == plano_original
        root.falar_com_lipsync("Continuamos a conversa.")
        assert len(textos) == 1 and textos[0][1:] == ["brava", 3]
        assert voz.fila.empty(), "modo silencioso publica texto sem fila de áudio"
        antes_expiracao = json.loads(json.dumps(dict(estado.conversacional)))
        # Expiração controlada pelo relógio; não editar a validade do episódio.
        tempo_real = time.time
        try:
            time.time = lambda: tempo_real() + 500
            expirado = root._diagnostico_mente_runtime.snapshot()["estado_emocional_causal"]
        finally:
            time.time = tempo_real
        assert expirado["emocao_expressavel"] == "calma"
        assert expirado["decisao_expressao"] == "expressao_contida"
        assert expirado["supressao"] == "evento_fora_da_validade"
        assert estado.conversacional == antes_expiracao, "diagnóstico não renova nem encerra estado como efeito colateral"
        # Evento observado elegível sem episódio aplicado não é expressão atual.
        root._acalmar_emocao_conversacional("encerramento controlado")
        neutro = root._diagnostico_mente_runtime.snapshot()["estado_emocional_causal"]
        assert neutro["emocao_expressavel"] == "calma"
        assert neutro["supressao"] == "episodio_nao_expressavel"
        assert neutro["fonte_causa"] == "ultimo_evento_observado"
        assert estado.mental["plano_turno_atual"] == plano_original
        assert not chamadas and all(not r["autoriza_execucao"] for r in (retrato, expirado, neutro))
        texto_diag = formatar_diagnostico_terminal(diagnostico)
        assert "causa controlada" not in texto_diag
        saida = {"origem_entrada":turno["origem_entrada"], "contexto":contexto,
                 "chat_ativo":bool(estado.conversacional["modo_chat"]),
                 "ativo":retrato, "expirado":expirado, "neutro":neutro,
                 "publicacoes":len(textos), "modelo":len(chamadas), "plano_preservado":True}
        sys.__stdout__.write("P21_TRANSICOES " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-B", "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_P21_MEMORIA=str(tmp_path),
                 LAYLAY_P21_CONTEXTO=contexto, GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ",
                 LAYLAY_IOT_MODO="simulado", LAYLAY_MICROFONE_ATIVO="0", LAYLAY_AVATAR_ATIVO="0",
                 LAYLAY_MASCOT_ENABLED="0", LAYLAY_PRESENCA="0", LAYLAY_BRIEFING_INICIAL="0"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4000:] + processo.stdout[-1200:]
    dados = next(json.loads(l.removeprefix("P21_TRANSICOES ")) for l in processo.stdout.splitlines()
                 if l.startswith("P21_TRANSICOES "))
    assert dados["origem_entrada"] == "terminal"
    assert dados["contexto"] == contexto and dados["chat_ativo"] is (contexto == "chat")
    assert dados["publicacoes"] == 1 and dados["modelo"] == 0 and dados["plano_preservado"]
    pasta_evidencia = os.environ.get("LAYLAY_P21_TRANSICOES_DIR")
    if pasta_evidencia:
        Path(pasta_evidencia, f"transicoes_{contexto}.json").write_text(
            json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
