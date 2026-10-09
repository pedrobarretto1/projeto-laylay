"""P18: root instalado usa cognição/Diretor/porteiro reais e uma fila local."""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import pytest


@pytest.mark.parametrize("foco", ["legado", "efeito", "natural", "rotulo", "autoral-invalida", "sequencia"],
                         ids=["ponte-legada", "foco-do-efeito", "reacao-autoral", "ocr-isolado", "sem-falso-efeito", "acao-temporal"])
def test_root_instalado_materializa_evento_jogo_com_uma_fila_e_zero_modelo(tmp_path, foco):
    codigo = textwrap.dedent(r'''
        import json, os, sys
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
            str(ident) + ".p18-compositor-" + str(os.getpid()), **k)
        import laylay as root
        estado = root._estado_compartilhado_runtime
        diretor = root._diretor_presenca_runtime
        voz = root._voz_runtime
        # Estado de entrada controlado; os owners cognitivos e de voz são os
        # mesmos instalados no root. O teste não simula captura ou som físico.
        root._modo_jogo_runtime._ativo = True
        estado.atualizar_campos("mental", presenca_contextual={}, iniciativa_autonoma={},
            oportunidades_cooperativas={}, plano_turno_atual={}, turno_atual={},
            ultima_entrada_ts=0.0)
        estado.atualizar_campos("conversacional", is_speaking=False, audio_playing=False,
            modo_chat=False, conversa_ativa=False)
        root._motor_iniciativa_runtime.configurar_dominio(
            "jogo", "sugestao", confirmacao_explicita=True, origem="controle_p18")
        chamadas = {"modelo": 0, "prompt": 0}
        def bloquear_modelo(*_a, **_k):
            chamadas["modelo"] += 1
            raise AssertionError("materialização de jogo não pode chamar modelo")
        def bloquear_prompt(*_a, **_k):
            chamadas["prompt"] += 1
            raise AssertionError("materialização de jogo não pode preparar prompt")
        type(root._resposta_evento_runtime.modelo_llm).executar = bloquear_modelo
        type(root._resposta_evento_runtime.preparacao_prompt).preparar_pacote = bloquear_prompt
        assert root._resposta_evento_runtime.agendar_fala_proativa == voz.agendar_fala_proativa
        assert voz.avaliar_proatividade_cb == root._porteiro_proatividade_runtime.avaliar
        timers = []
        class TimerSemEntrega:
            def __init__(self, intervalo, callback):
                self.intervalo, self.callback = intervalo, callback
                timers.append(self)
            def start(self): pass
            def is_alive(self): return True
            def cancel(self): pass
        voz.timer_factory = TimerSemEntrega
        evento = {
            "origem": "observador_presenca_jogo", "dominio": "jogo",
            "categoria": "celebracao", "chave": "ponte-observada-p18",
            "confianca": 0.97, "utilidade": 90, "momento_seguro": True,
            "motivo": "Companhia a partir da ponte observada.",
            "evidencias": ["A ponte suspensa liga as duas encostas.", "duas encostas visíveis"],
        }
        caso = os.environ["LAYLAY_P21_CASO"]
        if caso == "efeito":
            evento["evidencias"] = ["texto exato visível: ROCCA BLAU", "Um feixe azul vertical."]
            evento["foco_evidencia"] = evento["evidencias"][1]
        if caso in {"natural", "rotulo", "autoral-invalida", "sequencia"}:
            from mente_laylay.percepcao.visao_jogo.presenca_visual import extrair_presenca_visual
            fonte = "texto exato visível: -FLORESTA." if caso == "rotulo" else "Monstro de pedra com olhos azuis."
            fala_autoral = ("Esse monstro de pedra tem uma cara de poucos amigos." if caso == "natural"
                           else "Fechei o jogo e apaguei o monstro de pedra.")
            if caso == "sequencia":
                fonte = "Um feixe azul se expandiu ao redor do personagem."
                fala_autoral = "Esse feixe azul tomou conta de tudo!"
            resposta_visual = "PRESENCA_JOGO_JSON: " + json.dumps({
                "relevante": True, "categoria": "curiosidade", "momento_seguro": True,
                "confianca": .97, "fala": "Fechei o jogo e apaguei os arquivos.",
                "motivo": "Detalhe observado.", "evidencias": [fonte], "foco_evidencia": fonte,
                "proposta_reacao": {"fala": fala_autoral, "foco_evidencia": fonte,
                                    "trecho_ancora": "feixe azul" if caso == "sequencia" else "monstro de pedra", "humor": True},
            })
            _, proposta = extrair_presenca_visual(resposta_visual)
            assert root._visao_jogo_servico.processar_sugestao_proativa == root._coordenador_visao_jogo_runtime.processar_sugestao_proativa
            if caso == "sequencia":
                from scripts.tests.test_observador_presenca_jogo import _quadro_inicial_e_final
                from mente_laylay.percepcao.imagens_multimodais import desempacotar_imagens
                quadros = _quadro_inicial_e_final()
                restante = iter(quadros)
                contexto = {"ativo": True, "processo": "Megabonk.exe", "titulo": "Megabonk", "pid": 1, "hwnd": 7}
                observador, visao = root._observador_presenca_jogo_runtime, root._visao_jogo_servico
                assert observador.executar_visao.__self__ is visao
                observador.contexto_jogo = lambda: contexto
                observador.jogo_chave_atual = lambda _: "megabonk"
                observador.permitido = lambda: True
                observador.visao_ocupada = lambda: False
                observador.sleep = lambda _: None
                observador.capturar = lambda _: next(restante)
                visao.contexto_jogo = lambda: contexto
                visao.confirmar_contexto = lambda c: c
                class ThreadImediata:
                    def __init__(self, target, **_): self.target = target
                    def start(self): self.target()
                visao.thread_factory = ThreadImediata
                leituras = []
                def analisar(pacote, prompt):
                    assert [i["data"] for i in desempacotar_imagens(pacote)] == quadros
                    assert "SEQUÊNCIA TEMPORAL" in prompt and "não faça catálogo de objetos" in prompt
                    leituras.append(True)
                    return resposta_visual
                visao.analisar_imagem = analisar
                assert observador.verificar_uma_vez()
                assert len(leituras) == observador._analises == 1
            else:
                root._visao_jogo_servico.processar_sugestao_proativa(proposta, {"chave": "controle-naturalidade"}, {})
            resultado = dict(estado.mental["presenca_contextual"]["ultima_decisao"])
        else:
            resultado = diretor.considerar(evento)
        diagnostico = root._diagnostico_mente_runtime.snapshot()["estado_emocional_causal"]
        assert "intensidade" in diagnostico and "emocao_expressavel" in diagnostico
        assert diagnostico["autoriza_execucao"] is False
        primeira_fila = [dict(i) for i in voz.proativa_buffer]
        if caso in {"natural", "rotulo", "autoral-invalida", "sequencia"}:
            if caso == "sequencia":
                from mente_laylay.percepcao.visao_jogo.sessao_jogo import identificar_jogo
                identidade = identificar_jogo(contexto)
            else:
                identidade = {"chave": "controle-naturalidade"}
            root._visao_jogo_servico.processar_sugestao_proativa(proposta, identidade, {})
            repetida = dict(estado.mental["presenca_contextual"]["ultima_decisao"])
        else:
            repetida = diretor.considerar(evento)
        saida = dict(chamadas=chamadas, resultado=resultado, repetida=repetida,
            fila_tamanho=len(voz.proativa_buffer), primeira_fila_tamanho=len(primeira_fila),
            texto=primeira_fila[0]["texto"] if primeira_fila else "",
            tipo=primeira_fila[0]["tipo"] if primeira_fila else "",
            callbacks=bool(primeira_fila and callable(primeira_fila[0]["ao_concluir"])),
            diagnostico=diagnostico,
            timers=len(timers),
            emissao=estado.mental["presenca_contextual"]["ultima_emissao"],
            autoridade=estado.mental["turno_atual"].get("autoriza_execucao"))
        if os.environ.get("LAYLAY_P21_JOGO_DIR"):
            pasta_prova = Path(os.environ["LAYLAY_P21_JOGO_DIR"])
            pasta_prova.mkdir(parents=True, exist_ok=True)
            (pasta_prova / ("composicao_" + caso + ".json")).write_text(
                json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.__stdout__.write("P18_COMPOSITOR " + json.dumps(saida, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_P18_MEMORIA_TESTE=str(tmp_path),
                 LAYLAY_P21_CASO=foco,
                 GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ", LAYLAY_IOT_MODO="simulado"),
        capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert processo.returncode == 0, processo.stderr[-4500:]
    dados = next(json.loads(l.removeprefix("P18_COMPOSITOR "))
                 for l in processo.stdout.splitlines() if l.startswith("P18_COMPOSITOR "))
    assert dados["chamadas"] == {"modelo": 0, "prompt": 0}
    assert dados["resultado"]["status"] == "proposta_cognitiva"
    if foco in {"rotulo", "autoral-invalida"}:
        if foco == "rotulo":
            assert dados["resultado"]["contrato_fala"]["evidencias_factuais"] == ["texto exato visível: -FLORESTA."]
            assert dados["resultado"]["contrato_fala"]["ancora_factual_completa"] == ""
        else:
            assert dados["resultado"]["contrato_fala"]["reacao_validada"] == {}
        assert dados["resultado"]["proposta_comunicativa"]["status"] == "fala_vazia"
        assert dados["primeira_fila_tamanho"] == dados["fila_tamanho"] == dados["timers"] == 0
        assert dados["texto"] == "" and dados["emissao"] == {}
        assert dados["autoridade"] is False
        return
    assert dados["resultado"]["proposta_comunicativa"]["status"] == "agendada"
    assert dados["primeira_fila_tamanho"] == dados["fila_tamanho"] == dados["timers"] == 1
    esperado = {"legado": "A ponte suspensa liga as duas encostas.",
                "efeito": "Um feixe azul vertical.",
                "natural": "Esse monstro de pedra tem uma cara de poucos amigos.",
                "sequencia": "Esse feixe azul tomou conta de tudo!"}[foco]
    assert esperado in dados["texto"]
    assert "Na tela:" not in dados["texto"]
    if foco == "natural":
        assert dados["texto"] == esperado
        assert dados["resultado"]["contrato_fala"]["ancora_factual_completa"] == "Monstro de pedra com olhos azuis."
        assert dados["resultado"]["contrato_fala"]["reacao_validada"]["fala"] == esperado
        assert "Fechei" not in dados["texto"] and "apaguei" not in dados["texto"]
    if foco == "efeito":
        assert "ROCCA BLAU" not in dados["texto"] and "orbital" not in dados["texto"]
    assert dados["tipo"] == "presenca_jogo"
    assert dados["callbacks"] is True
    assert dados["repetida"]["status"] == "bloqueada"
    assert dados["emissao"] == {}
    assert dados["autoridade"] is False
