"""Coleta finita da presença instalada; não injeta cenas, decisões ou receipts."""

from __future__ import annotations

import argparse
import base64
import contextlib
from datetime import datetime
import functools
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time


RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segundos", type=int, default=180)
    parser.add_argument("--guardar-capturas", action="store_true",
                        help="Preserva os quadros analisados para conferir a evidência visual.")
    parser.add_argument("--amostra-inicial", action="store_true",
                        help="Coleta um único par assim que o modo jogo estiver pronto, sem aguardar a cadência normal.")
    argumentos = parser.parse_args()
    duracao = max(40, min(300, argumentos.segundos))
    pasta = RAIZ / "resultados_testes" / (
        "p18_jogo_real_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    pasta.mkdir(parents=True, exist_ok=False)
    banco = pasta / "memoria" / "laylay_memoria.sqlite"
    banco.parent.mkdir()
    origem = RAIZ / "memoria" / "laylay_memoria.sqlite"
    if origem.exists():
        with sqlite3.connect(origem.resolve().as_uri() + "?mode=ro", uri=True) as entrada:
            with sqlite3.connect(banco) as saida:
                entrada.backup(saida)
    baseline = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=RAIZ).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True, cwd=RAIZ).strip(),
        "status": subprocess.check_output(["git", "status", "--short"], text=True, cwd=RAIZ),
        "sonda_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fontes_sha256": {str(c): hashlib.sha256((RAIZ / c).read_bytes()).hexdigest()
            for c in map(Path, ("laylay.py", "mente_laylay/autonomia/resposta_evento_runtime.py",
                "mente_laylay/integracao/composicao_inteligencia_externa.py",
                "mente_laylay/percepcao/visao_jogo/runtime.py",
                "mente_laylay/percepcao/visao_jogo/analise_visual.py",
                "mente_laylay/percepcao/visao_jogo/coordenador.py",
                "mente_laylay/percepcao/visao_jogo/presenca_visual.py",
                "mente_laylay/percepcao/visao_jogo/observador_presenca.py",
                "mente_laylay/percepcao/imagens_multimodais.py",
                "mente_laylay/especialistas/mapa_habilidades.py",
                "mente_laylay/autonomia/diretor_presenca.py",
                "mente_laylay/cognicao/contrato_fala.py",
                "mente_laylay/personalidade/compositor_evento_local.py"))},
        "duracao_s": duracao,
        "amostragem": "um par antecipado; gates reais preservados" if argumentos.amostra_inicial else "cadencia normal do runtime",
        "isolamento": "copia SQLite; resumo/pessoas proprios; demais servicos e jogo reais",
        "restricoes": "microfone, terminal, avatar, briefing e IoT fisico desativados; gates de jogo/presenca preservados",
    }
    (pasta / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P18_JOGO_COLETA:", pasta, flush=True)
    os.environ.update({
        "GMAIL_USER": " ", "GMAIL_APP_PASSWORD": " ",
        "LAYLAY_IOT_MODO": "simulado", "IOT_CONTROLE_FISICO_AUTORIZADO": "NAO",
        "LAYLAY_TERMINAL_2": "0", "LAYLAY_MICROFONE_ATIVO": "0",
        "LAYLAY_BRIEFING_INICIAL": "0", "LAYLAY_FALAS_INICIAIS": "0",
        "LAYLAY_MASCOT_ENABLED": "0", "LAYLAY_AVATAR_ATIVO": "0",
        "PYTHONIOENCODING": "utf-8",
    })
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
    from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
    iniciar_sqlite = MemoriaSQLite.__init__
    MemoriaSQLite.__init__ = lambda self, db_path=None: iniciar_sqlite(self, str(banco))
    iniciar_resumo = MemoriaLaylay.__init__
    MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: iniciar_resumo(
        self, pasta_memoria=str(pasta / "resumo"), **k)
    iniciar_pessoas = MemoriaPessoasRuntime.__init__
    MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: iniciar_pessoas(
        self, caminho=pasta / "pessoas.json", **k)
    from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
    iniciar_central = CentralNotificacoesRuntime.__init__
    CentralNotificacoesRuntime.__init__ = lambda self, arquivo_estado, **k: iniciar_central(
        self, str(pasta / "central.json"), **k)
    trava = threading.RLock()
    parada = threading.Event()

    def registrar(etapa: str, **dados) -> None:
        with trava:
            with (pasta / "observacoes.jsonl").open("a", encoding="utf-8") as arq:
                arq.write(json.dumps(dict(etapa=etapa, ts=time.time(), **dados), ensure_ascii=False, default=str) + "\n")

    def observar(owner, nome, projetar_entrada, projetar_saida=lambda retorno: retorno):
        original = getattr(owner, nome)
        @functools.wraps(original)
        def chamada(*args, **kwargs):
            registrar(nome + "_entrada", dados=projetar_entrada(args, kwargs))
            try:
                retorno = original(*args, **kwargs)
            except BaseException as erro:
                registrar(nome + "_erro", tipo=type(erro).__name__)
                raise
            registrar(nome + "_retorno", dados=projetar_saida(retorno))
            return retorno
        setattr(owner, nome, chamada)

    capturas = 0
    def registrar_captura(imagem):
        nonlocal capturas
        dados = {"bytes": len(imagem or ""),
                 "sha256": hashlib.sha256(str(imagem or "").encode()).hexdigest()}
        if argumentos.guardar_capturas and imagem:
            try:
                binario = base64.b64decode(str(imagem).split(",", 1)[-1], validate=True)
                capturas += 1
                extensao = ".png" if binario.startswith(b"\x89PNG") else ".jpg"
                quadro = pasta / (f"captura_{capturas:02d}" + extensao)
                quadro.write_bytes(binario)
                dados.update(arquivo=quadro.name, imagem_sha256=hashlib.sha256(binario).hexdigest())
            except (ValueError, TypeError) as erro:
                dados["erro_preservacao"] = type(erro).__name__
        return dados

    with (pasta / "runtime.log").open("w", encoding="utf-8", buffering=1) as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            if argumentos.amostra_inicial:
                from mente_laylay.percepcao.visao_jogo.observador_presenca import ObservadorPresencaJogoRuntime
                def executar_amostra_inicial(observador):
                    # Apenas o disparo deste controle é antecipado. Captura,
                    # alvo, orçamento, relevância e entrega mantêm seus owners.
                    while not observador.stop_event.wait(0.5):
                        with observador._lock:
                            if observador._analises >= 1:
                                return
                        observador.verificar_uma_vez()
                ObservadorPresencaJogoRuntime.executar = executar_amostra_inicial
            import laylay as root
            visao = root._visao_jogo_servico
            diretor = root._diretor_presenca_runtime
            observar(root._observador_presenca_jogo_runtime, "capturar", lambda a, k: {"ativo": bool(a[0].get("ativo"))},
                     registrar_captura)
            observar(visao, "analisar_imagem", lambda a, k: {
                "chamada_visual": True,
                "prompt_sha256": hashlib.sha256(str(a[1] if len(a) > 1 else "").encode()).hexdigest(),
                "prompt_caracteres": len(str(a[1] if len(a) > 1 else "")),
            },
                     lambda r: str(r or "")[:6000])
            observar(visao, "processar_sugestao_proativa", lambda a, k: {"sugestao": a[0], "identidade": a[1]})
            observar(diretor, "considerar", lambda a, k: a[0])
            observar(diretor, "_registrar_resultado_entrega", lambda a, k: k)
            observar(root._resposta_evento_runtime, "processar", lambda a, k: {"turno": a[0], "contexto": {n:v for n,v in k.items() if not callable(v)}})
            observar(type(root._resposta_evento_runtime.modelo_llm), "executar", lambda a, k: {"tipo": str(getattr(a[1], "tipo_chamada", ""))},
                     lambda r: {"sucesso": bool(getattr(r, "sucesso", False)), "texto": str(getattr(r, "texto", ""))[:1800]})
            manter = root._inicializacao_runtime.manter_ativo
            prazo = time.monotonic() + duracao
            def manter_finito(**kwargs):
                anterior = kwargs.get("deve_encerrar")
                kwargs["deve_encerrar"] = lambda: time.monotonic() >= prazo or bool(callable(anterior) and anterior())
                return manter(**kwargs)
            root._inicializacao_runtime.manter_ativo = manter_finito

            def amostrar():
                while not parada.is_set():
                    try:
                        observador = root._observador_presenca_jogo_runtime
                        contexto = root._modo_jogo_runtime.contexto_atual()
                        estado = root._estado_compartilhado_runtime
                        presenca = dict(estado.mental.get("presenca_contextual") or {})
                        registrar("snapshot", contexto_jogo=contexto,
                            visao=root._registro_visao_jogo_leitura_runtime.diagnostico(),
                            observador={"habilitado": observador.habilitado, "permitido": observador.permitido(),
                                "ocupado": observador.visao_ocupada(), "analises": observador._analises,
                                "intervalo_s": observador.intervalo_s},
                            presenca={nome:presenca.get(nome) for nome in ("configuracao", "contadores", "ultima_decisao", "ultima_emissao")},
                            servicos=root._servicos_background_runtime.ativos(),
                            voz={nome: estado.conversacional.get(nome) for nome in ("is_speaking", "audio_playing", "current_emotion", "emotion_level")},
                            analises=[{n:v for n,v in item.items() if n in ("ts", "tipo", "sugestao", "resposta")}
                                      for item in visao._ultimas_analises.values()])
                    except Exception as erro:
                        registrar("erro_observacao", tipo=type(erro).__name__, detalhe=str(erro))
                    parada.wait(5)
            watcher = threading.Thread(target=amostrar, daemon=True)
            watcher.start()
            try:
                sys.argv = [str(RAIZ / "laylay.py")]
                root.main()
            finally:
                parada.set()
                watcher.join(timeout=6)
                registrar("coleta_concluida", banco=str(banco), audicao_fisica="nao_aferida")
    print("P18_JOGO_FINAL:", pasta, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
