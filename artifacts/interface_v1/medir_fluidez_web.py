"""Compara o renderer WebEngine com fixtures declaradas, sem executar habilidades.

Uso: python artifacts/interface_v1/medir_fluidez_web.py --output antes.json
     python artifacts/interface_v1/medir_fluidez_web.py --platform windows --output depois.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--platform", choices=("offscreen", "windows"), default="offscreen")
    parser.add_argument("--sources-dir", "--assets", type=Path, help="Mede uma cópia congelada dos assets, sem alterar a worktree")
    parser.add_argument("--warmup-ms", type=int, default=350)
    args = parser.parse_args()
    os.environ["QT_QPA_PLATFORM"] = args.platform
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"
    os.environ.pop("LAYLAY_REDUZIR_MOVIMENTO", None)
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    from PySide6.QtCore import QSettings
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import cliente.terminal_laylay_2 as terminal
    from cliente.terminal_2.interface_web_v1 import JanelaInterfaceWebV1

    assets = args.sources_dir.resolve() if args.sources_dir else root / "cliente/terminal_2/web_v1"
    saved = Path(tempfile.mkdtemp(prefix="laylay-fluidez-fontes-"))
    hashes = {}
    for name in ("index.html", "interface.js", "paginas.js"):
        hashes[name] = hashlib.sha256((assets / name).read_bytes()).hexdigest()
        shutil.copy2(assets / name, saved / name)
    terminal.QSettings = lambda *_: QSettings(str(saved / "ui.ini"), QSettings.IniFormat)
    app = QApplication.instance() or QApplication([])
    worker = terminal.PonteWorker("127.0.0.1", 1, "benchmark-sem-conexao")
    window = JanelaInterfaceWebV1(worker, root, diretorio_web=assets)

    def wait(condition, seconds=30):
        end = time.monotonic() + seconds
        while not condition() and time.monotonic() < end:
            QTest.qWait(10)
        if not condition():
            raise RuntimeError("Timeout na composição do benchmark")

    def js(code):
        value = []
        window.web.page().runJavaScript(code, value.append)
        wait(lambda: bool(value))
        return value[0]

    report = {"platform": args.platform, "dados": "fixtures declaradas; nenhuma habilidade executada", "fontes_sha256": hashes, "fontes_congeladas": str(saved), "warmup_ms": args.warmup_ms, "cenarios": []}
    try:
        window.show()
        wait(lambda: js("!!window.LaylayInterface?.views.dev"))
        js("""window.longTasks=[];try{new PerformanceObserver(l=>longTasks.push(...l.getEntries().map(e=>({duration:e.duration,startTime:e.startTime})))).observe({type:'longtask',buffered:true})}catch(e){};
          // As leituras de playlist deste benchmark usam somente a fixture abaixo.
          LaylayInterface.request=async()=>'';LaylayInterface.receiveEvent({type:'conexao',connected:true});
        """)
        for scene in ("chat200", "dev160", "playlist125"):
            messages = [{"id": "msg:"+str(i), "role": "assistant" if i % 2 else "user", "text": "Mensagem para medir a projeção de uma conversa longa. " * 3, "status": "responded"} for i in range(200)]
            events = [{"id": "dev:"+str(i), "timestamp": 1700000000+i, "category": "SYSTEM", "depth": "normal", "level": "info", "message": "Observação periódica do processo de teste."} for i in range(160)]
            dashboard = {"generated_at": 1700000000, "system": {"cpu_percent": {"value": 20, "observed_at": 1700000000, "freshness": "fresh"}}, "music": {"video_id": "abcdefghijk", "title": "Faixa de teste", "state": "playing", "freshness": "fresh", "controls_available": True, "catalog_available": True, "catalog": [{"name": "Benchmark", "count": 125}], "queue": []}}
            snapshot = {"type": "snapshot", "messages": messages, "dashboard": dashboard, "state": {"activity": "idle"}, "dev_console": {"events": events}}
            js("LaylayInterface.receiveEvent(" + json.dumps(snapshot) + ")")
            page = "chat" if scene == "chat200" else "dev" if scene == "dev160" else "music"
            js("LaylayInterface.goPage(" + json.dumps(page) + ")")
            QTest.qWait(80)
            if scene == "playlist125":
                js("document.querySelector('[data-tp-action=playlist-open]').click()")
                rows = [{"video_id": f"track{i:06d}", "title": f"Faixa {i+1} para teste", "channel": "Canal de teste", "duration_seconds": 180} for i in range(125)]
                js("LaylayInterface.receiveEvent(" + json.dumps({"type": "playlist_result", "id": "fixture", "operation": "detail", "playlist": "Benchmark", "result": {"ok": True, "revision": "fixture", "items": rows, "total": 125}}) + ")")
                QTest.qWait(80)
            # O paint/layout inicial pertence ao carregamento da cena, não ao burst observado.
            QTest.qWait(args.warmup_ms)
            js("""window.perfSample={start_time:performance.now(),templates:0,handler_ms:0,raf_costs:[],frame_gaps:[],input_ms:[],before_nodes:document.querySelectorAll('*').length};
              window.originalCreate=document.createElement.bind(document);document.createElement=function(name,...args){if(name==='template')perfSample.templates++;return originalCreate(name,...args)};
              window.originalRAF=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=function(callback){return originalRAF(time=>{const start=performance.now();callback(time);perfSample.raf_costs.push(performance.now()-start)})};
              window.frameActive=true;window.lastFrame=0;function sampleFrame(time){if(lastFrame)perfSample.frame_gaps.push(time-lastFrame);lastFrame=time;if(frameActive)originalRAF(sampleFrame)}originalRAF(sampleFrame);
              longTasks=[];
            """)
            start = time.monotonic()
            for burst in range(6):
                js("""(() => {const start=performance.now();for(let i=0;i<12;i++){
                  LaylayInterface.receiveEvent({type:'music_meter',video_id:'abcdefghijk',observed_at:Date.now()/1000,levels:[.2,.4,.3]});
                  LaylayInterface.receiveEvent({type:'dev_events',events:[{id:'burst:"""+str(burst)+""":'+i,category:'SYSTEM',depth:'normal',level:'info',message:'Amostra de desempenho'}]});
                  LaylayInterface.receiveEvent({type:'state',activity:'idle',activity_label:'Pronta'});
                }perfSample.handler_ms+=performance.now()-start;
                const input=document.querySelector('#composer-input,[data-tp-input=devCommand],[data-tp-input=trackQuery]');
                if(input){const before=performance.now();input.value='Texto digitado sem perder foco';input.dispatchEvent(new Event('input',{bubbles:true}));originalRAF(()=>perfSample.input_ms.push(performance.now()-before));}
                })()""")
                QTest.qWait(50)
            QTest.qWait(100)
            sample = json.loads(js("frameActive=false;JSON.stringify({...perfSample,long_tasks:longTasks.filter(e=>e.startTime>=perfSample.start_time)})"))
            sample.update(cenario=scene, elapsed_ms=round((time.monotonic()-start)*1000, 2))
            js("document.createElement=originalCreate;window.requestAnimationFrame=originalRAF")
            sample["navigation"] = json.loads(js("""JSON.stringify((()=>{const before=performance.now();LaylayInterface.goPage('home');const middle=performance.now();LaylayInterface.goPage('"""+page+"""');return {home_ms:middle-before,return_ms:performance.now()-middle}})())"""))
            report["cenarios"].append(sample)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        for scene in report["cenarios"]:
            print(scene["cenario"], "templates=", scene["templates"], "handler_ms=", round(scene["handler_ms"], 1), "max_raf_ms=", round(max(scene["raf_costs"], default=0), 1), "long_tasks=", len(scene["long_tasks"]))
        print(args.output.resolve())
    finally:
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
