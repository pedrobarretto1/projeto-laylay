"""Coleta finita P19 com composição, voz e avatar reais e memória isolada.

As causas são estímulos controlados. Receipts de software não confirmam som
audível nem percepção visual; essas observações ficam separadas no relatório.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--espera-visual", type=float, default=8.0)
    args = parser.parse_args()
    pasta = args.saida.resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, valor in {
        "GMAIL_USER": " ", "GMAIL_APP_PASSWORD": " ",
        "LAYLAY_IOT_MODO": "simulado", "LAYLAY_MICROFONE_ATIVO": "0",
        "LAYLAY_PRESENCA": "0", "LAYLAY_BRIEFING_INICIAL": "0",
    }.items():
        os.environ[nome] = valor
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
    from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
    from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
    from mente_laylay.integracao import instancia_unica

    iniciar_sqlite = MemoriaSQLite.__init__
    MemoriaSQLite.__init__ = lambda self, caminho=None: iniciar_sqlite(
        self, str(pasta / Path(caminho or "laylay_memoria.sqlite").name))
    iniciar_resumo = MemoriaLaylay.__init__
    MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: iniciar_resumo(
        self, pasta_memoria=str(pasta / "resumo"), **k)
    iniciar_pessoas = MemoriaPessoasRuntime.__init__
    MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: iniciar_pessoas(
        self, caminho=pasta / "pessoas.json", **k)
    iniciar_central = CentralNotificacoesRuntime.__init__
    CentralNotificacoesRuntime.__init__ = lambda self, caminho, **k: iniciar_central(
        self, str(pasta / "central.json"), **k)
    adquirir = instancia_unica.adquirir_instancia_unica
    instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
        str(ident) + ".p19-real-" + str(os.getpid()), **k)
    import laylay as root
    from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
    from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM

    estado = root._estado_compartilhado_runtime
    voz = root._voz_runtime
    avatar = root._avatar_runtime
    inicio = time.monotonic()
    prazo = inicio + 60.0
    relatorio = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ,
                                        text=True).strip(),
        "pid": os.getpid(), "audio_pedido": args.audio,
        "audio_fisico_confirmado": False, "pixels_inspecionados": False,
        "causas": "estimulos_controlados", "modelo": 0,
        "textos": [], "metricas": [], "amostras": [], "frases": [],
        "hashes": {},
    }
    for nome in (
        "laylay.py", "mente_laylay/personalidade/retrato_entrega.py",
        "mente_laylay/personalidade/orquestrador_fala_runtime.py",
        "mente_laylay/personalidade/voz_runtime.py",
        "mente_laylay/integracao/estado_contexto_runtime.py",
        "mente_laylay/integracao/politicas_composicao.py",
        "mente_laylay/personalidade/avatar_runtime.py", "cliente/avatar_laylay.py",
        "mente_laylay/memoria_mental/diagnostico_mente.py",
        "mente_laylay/memoria_mental/formatacao_diagnostico.py",
    ):
        relatorio["hashes"][nome] = hashlib.sha256((RAIZ / nome).read_bytes()).hexdigest()

    def bloquear_modelo(*_a, **_k):
        relatorio["modelo"] += 1
        raise AssertionError("a coleta de expressão não chama modelo")
    RegistroModeloLLM.executar = bloquear_modelo
    root._orquestrador_fala_runtime.registrar_observador_texto_final(
        lambda texto, emocao, nivel, **dados: relatorio["textos"].append(
            {"texto": texto, "emocao": emocao, "nivel": nivel, **dados}) or True)
    metrica_original = voz.registrar_metrica_cb
    def metrica(nome, ms, ok, **dados):
        relatorio["metricas"].append({"nome": nome, "ms": ms, "ok": bool(ok)})
        if callable(metrica_original):
            metrica_original(nome, ms, ok, **dados)
    voz.registrar_metrica_cb = metrica
    popen_original = avatar.popen
    def abrir_avatar(comando, **dados):
        comando = list(comando)
        comando[comando.index("--state-file") + 1] = str(pasta / "avatar_estado.json")
        return popen_original(comando, **dados)
    avatar.popen = abrir_avatar
    env_original = avatar.env_getter
    avatar.env_getter = lambda nome, padrao: {
        "LAYLAY_MASCOT_ENABLED": "1", "LAYLAY_AVATAR_ATIVO": "1",
    }.get(nome, env_original(nome, padrao))

    def publicar(ref: str, emocao: str, nivel: int) -> None:
        evento = criar_evento_emocional_causal(
            origem="resultado_operacional", causa="estímulo controlado de sincronização",
            evidencia_ref=ref, natureza_evidencia="fato_observado", confianca=.97,
            permite_expressao=True, emocao=emocao, nivel=nivel,
            intensidade=nivel, ts=time.time())
        assert root._estado_contexto_runtime.publicar_evento_emocional_causal(evento)
        assert root._definir_emocao_conversacional(emocao, nivel, evento["causa"])

    def amostrar(fase: str) -> None:
        visual = root._estado_visual_laylay()
        retrato = estado.obter_copia("conversacional", "retrato_entrega_fala", {})
        relatorio["amostras"].append({
            "t": round(time.monotonic() - inicio, 3), "fase": fase,
            "visual": visual, "retrato": retrato,
            "episodio": estado.obter_copia("conversacional", "episodio_emocional", {}),
            "diagnostico_emocional": root._diagnostico_mente_runtime.snapshot()["estado_emocional_causal"],
        })
        (pasta / "estado_atual.json").write_text(json.dumps(
            {"fase": fase, "visual": visual, "pid_avatar": getattr(avatar._processo, "pid", None)},
            ensure_ascii=False, indent=2), encoding="utf-8")

    def espera_visual(fase: str) -> None:
        fim = min(prazo, time.monotonic() + max(0.0, min(12.0, args.espera_visual)))
        while time.monotonic() < fim:
            amostrar(fase)
            time.sleep(.10)

    def falar(turno: str, texto: str, troca: bool = False) -> None:
        estado.atualizar_campos("mental", ultima_entrada_ts=time.time(),
            turno_atual={"id": turno}, plano_turno_atual={
                "id": turno, "requer_execucao": False, "texto_usuario": "teste de expressão"})
        assert root.falar_com_lipsync(texto)
        concluida = threading.Event()
        # Espera pelo owner real sem substituir TTS, player ou reprodução.
        iniciou = False
        trocou = False
        while time.monotonic() < prazo:
            if estado.obter("conversacional", "audio_playing", False):
                iniciou = True
                if troca and not trocou:
                    publicar("p19:real:B", "brava", 3)
                    trocou = True
            amostrar(turno)
            if iniciou and not estado.obter("conversacional", "is_speaking", False):
                concluida.set()
                break
            if not iniciou and voz.fila.empty() and voz._pedido_turno_pendente is None:
                break
            time.sleep(.05)
        relatorio["frases"].append({"turno": turno, "audio_iniciou": iniciou,
            "concluida": concluida.is_set(), "trocou_episodio_durante_audio": trocou})

    try:
        assert avatar.iniciar(), "avatar real não iniciou"
        publicar("p19:real:A", "irritada", 1)
        espera_visual("A_nivel_1")
        if args.audio:
            falar("p19:real:entrega_A", "Primeira fala. Vou manter este tom até terminar a resposta.", True)
        else:
            publicar("p19:real:B", "brava", 3)
        espera_visual("B_nivel_3")
        if args.audio:
            falar("p19:real:entrega_B", "Segunda fala. Agora uso a intensidade da nova entrega.")
        root._acalmar_emocao_conversacional("fim da coleta controlada")
        espera_visual("final_neutro")
        relatorio["retrato_liberado"] = not bool(
            estado.obter("conversacional", "retrato_entrega_fala", {}))
    except Exception as erro:
        relatorio["erro"] = f"{type(erro).__name__}: {erro}"
    finally:
        voz.interrupt_event.set()
        voz.encerrar(timeout_s=2.0)
        avatar.parar()
        relatorio["duracao_s"] = round(time.monotonic() - inicio, 3)
        (pasta / "relatorio.json").write_text(json.dumps(
            relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P19_REAL", json.dumps({"saida": str(pasta), "erro": relatorio.get("erro"),
        "frases": relatorio["frases"], "duracao_s": relatorio["duracao_s"]}, ensure_ascii=False))
    return 1 if relatorio.get("erro") else 0


if __name__ == "__main__":
    raise SystemExit(main())
