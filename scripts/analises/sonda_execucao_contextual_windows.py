"""Prova opt-in: entrada instalada e efeitos reais, limitada à Calculadora.

Não inicia main, áudio, IoT ou corpo. Autoria real é opt-in e só usa Ollama local;
o principal continua controlado. Executores, contexto,
validação, publicação e prioridade instalada permanecem reais. Recusa uma
Calculadora/sessão Laylay preexistente e conserva a janela para inspeção visual.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def verificar_sessao() -> None:
    import psutil
    for processo in psutil.process_iter(["name", "cmdline"]):
        try:
            if str(processo.info["name"] or "").casefold() not in {"python.exe", "pythonw.exe"}:
                continue
            argumentos = processo.info["cmdline"] or []
            if any(Path(str(arg)).name.casefold() == "laylay.py" for arg in argumentos[1:]):
                raise RuntimeError("Laylay aberta; não interromper nem iniciar sonda concorrente.")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def observar_calculadora() -> list[dict]:
    """Leitura independente do receipt: HWND, PID e geometria do Windows."""
    import ctypes
    from ctypes import wintypes
    import psutil
    import pygetwindow as gw

    encontrados = []
    for janela in gw.getAllWindows():
        if str(janela.title or "").casefold() not in {"calculadora", "calculator"}:
            continue
        hwnd = int(janela._hWnd)
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            nome = psutil.Process(pid.value).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if nome.casefold() not in {"calculatorapp.exe", "calculator.exe", "applicationframehost.exe"}:
            continue
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError("Janela presente, geometria não observável.")
        encontrados.append({"hwnd": hwnd, "pid": pid.value, "processo": nome,
            "titulo": janela.title, "retangulo": [rect.left, rect.top, rect.right, rect.bottom]})
    return encontrados


def coletar_instalado(pasta: Path, *, caminho: str = "entrada", lado: str = "esquerda",
                      exigir_movimento: bool = False, alternar_lados: bool = False,
                      repetir_primeiro_lado: bool = False, autoria: str = "indisponivel") -> dict:
    from types import SimpleNamespace
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.autonomia import coordenador_intencao
    from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo

    if caminho not in {"entrada", "principal"} or lado not in {"esquerda", "direita"}:
        raise ValueError("Caminho/lado fora do escopo da sonda.")
    if repetir_primeiro_lado and not alternar_lados:
        raise ValueError("Repetição exige dois lados alternados antes do retorno.")
    if autoria not in {"indisponivel", "controlada", "real"} or autoria != "indisponivel" and caminho != "principal":
        raise ValueError("Autoria fora do escopo da porta principal.")
    lados = (["esquerda" if lado == "direita" else "direita"] if alternar_lados else []) + [lado]
    if repetir_primeiro_lado:
        lados.append(lados[0])
    texto_usuario = "abre o aplicativo Calculadora" + "".join(f" e coloca ela à {l}" for l in lados)
    verificar_sessao()
    if observar_calculadora():
        raise RuntimeError("Calculadora já aberta; sonda não altera janela preexistente.")
    transportes, selecao = [], {}
    http_local = None
    if autoria == "real":
        import requests
        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
        selecao = selecao_local()
        original_http = requests.sessions.Session.request
        def sem_redirect(sessao, method, url, *args, **kwargs):
            kwargs["allow_redirects"] = False
            return original_http(sessao, method, url, *args, **kwargs)
        http_local = criar_guarda_http_local(selecao, transportes, sem_redirect)
    root = preparar_instalacao_isolada(pasta, requisicao_http=http_local)
    falas, chamadas, modelos, receipts_apresentacao = [], [], [], []
    owner = root._orquestrador_fala_runtime
    # Isolamento das únicas saídas não sob teste; não é prova de áudio/modelo.
    owner._servicos["_voz_runtime"] = SimpleNamespace(falar=lambda *_a, **_k: True)
    owner._observadores_texto_final = [lambda texto, *_a, **_k: falas.append(texto) or True]
    owner._observadores_fala_final = []
    fonte = json.dumps({"fala": "Vou verificar o pedido.", "tipo_interacao": "comando",
        "comandos": [{"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}] + [
            {"intent": "ORGANIZAR_DESKTOP", "params": {"left" if l == "esquerda" else "right": "Notepad"}}
            for l in lados]})

    executar_modelo = root._cliente_llm_runtime.servico.cliente.executar
    def modelo_controlado(pedido):
        tipo = str(getattr(pedido, "tipo_chamada", ""))
        modelos.append(tipo)
        if tipo == "autoria_operacional" and autoria == "real":
            return executar_modelo(pedido)
        if tipo == "autoria_operacional" and autoria == "controlada":
            contrato = json.loads(pedido.payload["messages"][1]["content"])
            trechos = [r["fato_verificado"].rstrip(".") for r in contrato["resultados"]]
            return ResultadoModelo(json.dumps({"fala": " e ".join(trechos) + ".", "trechos": trechos}), True)
        return ResultadoModelo(fonte if tipo == "principal" else "", tipo == "principal")

    root._cliente_llm_runtime.servico.cliente.executar = modelo_controlado
    from mente_laylay.personalidade import orquestrador_fala_runtime as modulo_fala
    confirmar_original = modulo_fala.personalizar_confirmacao_composta_llm
    confirmacoes = []
    def confirmar_observando(*args, **kwargs):
        resultado = confirmar_original(*args, **kwargs)
        confirmacoes.append({"usada_llm": resultado.usada_llm, "motivo": resultado.motivo_fallback,
                             "fala": resultado.fala})
        return resultado
    modulo_fala.personalizar_confirmacao_composta_llm = confirmar_observando
    if caminho == "principal":
        # Contraprova declarada: a entrada normal foi consumida pela prioridade.
        # Retira SOMENTE essa porta no subprocesso para alcançar a composição
        # principal instalada; não equivale a main nem a seleção de rota real.
        contexto_original = root._resposta_ia_runtime._contexto_getter
        root._resposta_ia_runtime._contexto_getter = lambda: {
            **contexto_original(), "processar_comandos_prioritarios": None}
    original = coordenador_intencao.executar_intencao

    def executar_observando(pedido, texto, ctx):
        # Guarda diagnóstica ANTES de qualquer leaf: nunca executar Notepad,
        # volume ou outro domínio se o fluxo instalado divergir.
        intent, params = pedido.get("intent"), pedido.get("params") or {}
        posicao = len(chamadas)
        permitido = (posicao == 0 and intent == "APP_OPEN"
            and str(params.get("nome_app", "")).casefold() == "calculadora")
        if 1 <= posicao <= len(lados):
            parametro_lado = "left" if lados[posicao-1] == "esquerda" else "right"
            parametro_oposto = "right" if parametro_lado == "left" else "left"
            permitido = (intent == "ORGANIZAR_DESKTOP"
                and str(params.get(parametro_lado, "")).casefold() == "calculadora"
                and not params.get(parametro_oposto))
        if not permitido:
            raise RuntimeError("Efeito fora do escopo reversível autorizado para esta sonda.")
        passo = {"pedido": deepcopy(pedido), "texto": texto,
                 "antes": observar_calculadora(), "receipts": []}
        chamadas.append(passo)
        publicar = ctx.get("_registrar_resultado_execucao")
        if not callable(publicar):
            raise RuntimeError("Publicador instalado indisponível; não executar.")

        def publicar_observando(receipt, *args, **kwargs):
            retorno = publicar(receipt, *args, **kwargs)
            if retorno is not False:
                passo["receipts"].append(receipt.como_dict())
                receipts_apresentacao.append(deepcopy(receipt))
            return retorno

        retorno = original(pedido, texto, {**ctx, "_registrar_resultado_execucao": publicar_observando})
        passo.update(retorno_legado=bool(retorno), depois=observar_calculadora())
        return retorno

    coordenador_intencao.executar_intencao = executar_observando
    try:
        root._resposta_ia_runtime.processar(texto_usuario, origem="sonda_windows_contextual")
    finally:
        coordenador_intencao.executar_intencao = original
        modulo_fala.personalizar_confirmacao_composta_llm = confirmar_original
    plano = root._estado_compartilhado_runtime.obter_copia("mental", "plano_turno_atual")
    falhas = []
    if [p["pedido"]["intent"] for p in chamadas] != ["APP_OPEN"] + ["ORGANIZAR_DESKTOP"] * len(lados):
        falhas.append("sequencia_instalada_nao_executou_todos_os_atos")
    if len(falas) != 1:
        falhas.append("conclusao_instalada_nao_unica")
    from mente_laylay.personalidade.planejador_resposta import fala_factual_resultados_compostos
    fala_canonica = fala_factual_resultados_compostos(receipts_apresentacao)
    # O provider desta sonda não produz autoria. A contingência deve conservar
    # TODOS os receipts na ordem, inclusive dois fatos literalmente iguais.
    # Este controle não afirma qualidade semântica de uma futura fala da LLM.
    if autoria == "indisponivel" and falas != [fala_canonica]:
        falhas.append("contingencia_publicada_perdeu_receipt_ou_ordem")
    if autoria != "indisponivel" and (len(confirmacoes) != 1 or not confirmacoes[0]["usada_llm"]
            or falas != [confirmacoes[0]["fala"]]):
        falhas.append("autoria_composta_nao_aceita_ou_nao_publicada")
    if len(chamadas) == 1 + len(lados):
        for passo in chamadas:
            if len(passo["receipts"]) != 1 or passo["receipts"][0].get("confirmado") is not True:
                falhas.append("receipt_nao_confirmado")
        identidades = [p["depois"] for p in chamadas]
        if any(len(j) != 1 for j in identidades):
            falhas.append("janela_real_ausente_ou_ambigua")
        elif len({j[0]["hwnd"] for j in identidades}) != 1:
            falhas.append("identidade_real_da_janela_divergente")
        else:
            import ctypes
            from ctypes import wintypes
            area = wintypes.RECT()
            if not ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(area), 0):
                falhas.append("area_util_nao_observavel")
            for b, lado_executado in zip(chamadas[1:], lados) if area.right > area.left else ():
                metade = (area.right - area.left) // 2
                x = area.left if lado_executado == "esquerda" else area.left + metade
                esperado = [x, area.top, x + metade, area.bottom]
                observado = b["depois"][0]["retangulo"]
                if any(abs(x-y) > 32 for x, y in zip(esperado, observado)):
                    falhas.append("geometria_real_divergente")
                b["geometria_esperada"] = esperado
                b["movimento_observado"] = (len(b["antes"]) == 1
                    and b["antes"][0]["hwnd"] == b["depois"][0]["hwnd"]
                    and b["antes"][0]["retangulo"] != observado)
                # Em cadeia, a segunda posição DEVE comprovar movimento;
                # a primeira pode coincidir com uma geometria lembrada pelo SO.
                if exigir_movimento and (not alternar_lados or b is not chamadas[1]) and not b["movimento_observado"]:
                    falhas.append("sem_alteracao_geometrica_observada")
    if caminho == "principal" and ("principal" not in modelos or plano.get("fase") != "executado"):
        falhas.append("nao_alcancou_ou_nao_concluiu_a_porta_principal")
    return {"texto": texto_usuario, "caminho": caminho, "prioridade_removida_na_sonda": caminho == "principal",
            "chamadas": chamadas, "falas": falas, "plano": plano,
            "fala_canonica_esperada": fala_canonica,
            "autoria": autoria, "confirmacoes_autoria": confirmacoes,
            "selecao_local": selecao, "transportes_autoria": transportes,
            "tipos_chamadas_modelo_isolado": modelos, "falhas": falhas,
            "efeitos_windows_reais": True, "main_iniciado": False,
            "modelo_real_consultado": any(t.get("status") == 200 for t in transportes),
            "principal_modelo_real": False, "audio_fisico_validado": False,
            "janela_preservada_para_inspecao": observar_calculadora()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executar-windows", action="store_true", required=True)
    parser.add_argument("--caminho", choices=("entrada", "principal"), default="entrada")
    parser.add_argument("--lado", choices=("esquerda", "direita"), default="esquerda")
    parser.add_argument("--exigir-movimento", action="store_true")
    parser.add_argument("--alternar-lados", action="store_true")
    parser.add_argument("--repetir-primeiro-lado", action="store_true")
    parser.add_argument("--autoria", choices=("indisponivel", "controlada", "real"), default="indisponivel")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        parser.error("Artefato já existe; não sobrescrever.")
    if args.repetir_primeiro_lado and not args.alternar_lados:
        parser.error("Repetição exige --alternar-lados.")
    if args.autoria != "indisponivel" and args.caminho != "principal":
        parser.error("Autoria exige --caminho principal.")
    if args.autoria == "real":
        from scripts.analises.sonda_escopo_geracao_real import selecao_local
        selecao_local()  # recusa seleção externa antes de qualquer efeito
    verificar_sessao()
    if observar_calculadora():
        parser.error("Calculadora já aberta; preservá-la.")
    fontes = ["laylay.py", "mente_laylay/autonomia/coordenador_intencao.py",
        "mente_laylay/autonomia/resposta_ia_runtime.py", "mente_laylay/autonomia/dispatcher_comandos_json.py",
        "mente_laylay/autonomia/executor_janelas.py", "mente_laylay/percepcao/janelas_sistema.py",
        "mente_laylay/cognicao/decisao_turno.py", "mente_laylay/cognicao/materializacao_contextual.py",
        "mente_laylay/autonomia/composicao_ciclo_comandos.py",
        "mente_laylay/integracao/composicao_contextos_ia.py", "mente_laylay/cognicao/escopo_autorizacao.py",
        "mente_laylay/autonomia/adaptador_resultado.py", "mente_laylay/autonomia/roteador_intencao.py",
        "mente_laylay/personalidade/planejador_resposta.py", "mente_laylay/personalidade/confirmacao_llm.py",
        "mente_laylay/personalidade/orquestrador_fala_runtime.py", "mente_laylay/personalidade/diretor_fala.py",
        "configuracao.env", "scripts/analises/sonda_execucao_contextual_windows.py"]
    hashes = lambda: {f: hashlib.sha256((RAIZ/f).read_bytes()).hexdigest() for f in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
        "instante_utc": datetime.now(timezone.utc).isoformat()}
    with tempfile.TemporaryDirectory(prefix="laylay_windows_contextual_") as pasta:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        codigo = ("import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
            "from scripts.analises.sonda_execucao_contextual_windows import coletar_instalado; "
            "r=coletar_instalado(Path(sys.argv[2]),caminho=sys.argv[3],lado=sys.argv[4],"
            "exigir_movimento=sys.argv[5]=='1',alternar_lados=sys.argv[6]=='1',repetir_primeiro_lado=sys.argv[7]=='1',autoria=sys.argv[8]); "
            "sys.__stdout__.write('WINDOWS_JSON='+json.dumps(r,ensure_ascii=False)+'\\n')")
        processo = subprocess.run([sys.executable, "-c", codigo, str(RAIZ), pasta, args.caminho,
            args.lado, str(int(args.exigir_movimento)), str(int(args.alternar_lados)),
            str(int(args.repetir_primeiro_lado)), args.autoria], cwd=RAIZ,
            env=env, capture_output=True, text=True, encoding="utf-8", timeout=90)
    linhas = [l for l in processo.stdout.splitlines() if l.startswith("WINDOWS_JSON=")]
    resultado = json.loads(linhas[0].split("=", 1)[1]) if len(linhas) == 1 else {
        "falhas": ["sonda_nao_concluiu"], "erro": processo.stderr[-3000:],
        "efeitos_windows_reais": "resultado_desconhecido"}
    depois = hashes()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        json.dump({**base, **resultado, "exit_code_filho": processo.returncode,
            "hashes_antes": antes, "hashes_depois": depois, "fontes_estaveis": antes == depois},
            arquivo, ensure_ascii=False, indent=2)
    print(json.dumps({"artefato": str(args.saida), "falhas": resultado["falhas"],
        "fontes_estaveis": antes == depois}, ensure_ascii=False))
    return int(bool(resultado["falhas"]) or antes != depois or processo.returncode != 0)


if __name__ == "__main__":
    raise SystemExit(main())
