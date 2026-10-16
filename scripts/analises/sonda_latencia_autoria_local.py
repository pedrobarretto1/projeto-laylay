"""Replay diagnóstico de autoria local, sem main, execução, publicação ou voz.

Compara o payload HTTP arquivado com a mesma chamada aquecida. A rota nativa
fornece métricas de carregamento/prompt/geração, mas não é o transporte instalado.
O timeout de 60s é SOMENTE observacional; o limite da produção não é alterado.
Não descarrega modelos nem altera keep_alive, parâmetros ou configuração.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
from scripts.analises.sonda_execucao_contextual_windows import verificar_sessao


def preparar_replay(dados: dict, selecao: dict) -> tuple[str, dict]:
    """Recusa modelo/rota divergentes e dados não pertencentes à autoria arquivada."""
    transportes = dados.get("transportes_autoria") or []
    if len(transportes) != 1 or dados.get("autoria") != "real":
        raise ValueError("Artefato não contém uma única autoria real.")
    registro = transportes[0]
    url, payload = registro.get("url"), registro.get("payload")
    if (url != selecao["LAYLAY_LLM_BASE_URL"].rstrip("/") + "/chat/completions"
            or not isinstance(payload, dict) or payload.get("model") != selecao["LAYLAY_LLM_MODEL"]):
        raise ValueError("Modelo/rota arquivados divergem da seleção local.")
    if set(payload) != {"model", "messages", "max_tokens", "temperature"}:
        raise ValueError("Payload fora do contrato de replay sem ferramentas.")
    mensagens = payload["messages"]
    if (not isinstance(mensagens, list) or len(mensagens) != 2
            or [m.get("role") for m in mensagens] != ["system", "user"]
            or any(not isinstance(m.get("content"), str) for m in mensagens)):
        raise ValueError("Mensagens fora do contrato de autoria.")
    contrato = json.loads(mensagens[1]["content"])
    receipts = [r for passo in dados.get("chamadas", []) for r in passo.get("receipts", [])]
    if (not receipts or len(receipts) != len(contrato.get("resultados", []))
            or [r.get("id_solicitacao") for r in receipts]
               != [r.get("id_solicitacao") for r in contrato["resultados"]]):
        raise ValueError("Receipts arquivados não cobrem a autoria.")
    return url, deepcopy(payload)


def conferir_redacao(dados: dict, texto: str) -> dict:
    """Revalida evidência HISTÓRICA; não admite/persiste receipts no turno atual."""
    from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    resultados = [normalizar_resultado_acao(r) for p in dados["chamadas"] for r in p["receipts"]]
    return asdict(personalizar_confirmacao_composta_llm(resultados,
        dados["fala_canonica_esperada"], enviar_mensagem=lambda *_a, **_k: texto))


def coletar(dados: dict, selecao: dict) -> dict:
    import requests
    url, payload = preparar_replay(dados, selecao)
    partes = urlsplit(url)
    base = f"{partes.scheme}://{partes.netloc}"
    transportes, medidas = [], []
    def sem_redirect(sessao, method, endereco, *args, **kwargs):
        kwargs["allow_redirects"] = False
        return requests.sessions.Session.request(sessao, method, endereco, *args, **kwargs)
    http = criar_guarda_http_local(selecao, transportes, sem_redirect)
    with requests.Session() as sessao:
        def estado():
            verificar_sessao()
            r = sessao.get(base + "/api/ps", timeout=3, allow_redirects=False)
            r.raise_for_status()
            return r.json()
        versao = sessao.get(base + "/api/version", timeout=3, allow_redirects=False).json()
        nativo = {"model": payload["model"], "messages": payload["messages"], "stream": False,
            "options": {"num_predict": payload["max_tokens"], "temperature": payload["temperature"]}}
        for nome, endereco, corpo, limite in (
            ("compativel_observacional", url, payload, 60),
            ("nativo_metricas", base + "/api/chat", nativo, 60),
            ("compativel_8s_1", url, payload, 8),
            ("compativel_8s_2", url, payload, 8),
        ):
            medida = {"caso": nome, "timeout_s": limite, "ps_antes": estado()}
            inicio = time.monotonic()
            try:
                r = http(sessao, "POST", endereco, json=corpo, timeout=limite)
                r.raise_for_status()
                resposta = r.json()
                texto = (resposta.get("message", {}).get("content", "") if nome == "nativo_metricas"
                         else resposta["choices"][0]["message"].get("content", ""))
                medida.update(resposta=resposta, redacao=conferir_redacao(dados, texto))
            except Exception as erro:
                medida["erro_tipo"] = type(erro).__name__
            medida.update(segundos=round(time.monotonic() - inicio, 3), ps_depois=estado())
            medidas.append(medida)
            print(json.dumps({k:medida[k] for k in ("caso", "segundos")}, ensure_ascii=False), flush=True)
    return {"versao": versao, "medidas": medidas, "transportes": transportes,
        "executor_chamado": False, "publicacao_atual": False, "audio_fisico": False,
        "configuracao_alterada": False, "modelo_descarregado_pela_sonda": False,
        "composicao_instalada_validada": False}


def coletar_autoria_instalada(dados: dict, selecao: dict) -> dict:
    """Executado apenas no processo diagnóstico, sem iniciar main/efeitos/saídas."""
    import requests
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    preparar_replay(dados, selecao)
    verificar_sessao()
    transportes, pedidos = [], []
    original_http = requests.sessions.Session.request
    def sem_redirect(sessao, method, url, *a, **k):
        k["allow_redirects"] = False
        return original_http(sessao, method, url, *a, **k)
    http = criar_guarda_http_local(selecao, transportes, sem_redirect)
    os.environ.update(PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
        LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
        LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
        LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
        LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
    with tempfile.TemporaryDirectory(prefix="laylay_autoria_sem_efeitos_") as pasta:
        root = preparar_instalacao_isolada(Path(pasta), requisicao_http=http)
        # Reutiliza o pré-aquecimento existente; não cria política nova de startup.
        preaquecer = root._runtime_llm_portatil.preaquecer()
        cliente = root._cliente_llm_runtime.servico.cliente
        executar_original = cliente.executar
        def executar_observando(pedido):
            pedidos.append(asdict(pedido))
            return executar_original(pedido)
        cliente.executar = executar_observando
        orcamento = cliente.orcamento_turno
        orcamento.iniciar_turno("turno-20261013", classe="normal", ainda_atual_cb=lambda: True)
        resultados = [normalizar_resultado_acao(r) for p in dados["chamadas"] for r in p["receipts"]]
        inicio = time.monotonic()
        redacao = personalizar_confirmacao_composta_llm(resultados, dados["fala_canonica_esperada"],
            enviar_mensagem=root._registro_modelo_llm_runtime.enviar)
        duracao = round(time.monotonic() - inicio, 3)
        diagnostico = orcamento.diagnostico()
        orcamento.finalizar_turno()
    return {"preaquecimento_existente": preaquecer, "pedidos": pedidos,
        "transportes": transportes, "segundos": duracao, "redacao": asdict(redacao),
        "orcamento": diagnostico, "executor_chamado": False, "publicacao_atual": False,
        "receipts_historicos_revalidados_somente_para_redacao": True,
        "main_iniciado": False, "audio_fisico": False, "configuracao_alterada": False,
        "composicao_autoria_instalada": True, "composicao_execucao_instalada": False}


def coletar_corrida_startup(dados: dict, selecao: dict) -> dict:
    """Primeiro turno instalado e aquecedor real, sem prioridade/efeito/fala.

Não força modelo frio. Registra /api/ps antes e usa evento na admissão HTTP
para iniciar a mensagem quando a chamada de aquecimento está em andamento.
"""
    import requests
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    preparar_replay(dados, selecao)
    verificar_sessao()
    original_http = requests.sessions.Session.request
    base = selecao["LAYLAY_LLM_BASE_URL"].removesuffix("/v1")
    ps_antes = requests.get(base + "/api/ps", timeout=3, allow_redirects=False).json()
    transportes, eventos, casos = [], [], []
    caso = {}
    aquecimento_admitido = threading.Event()
    def sem_redirect(sessao, method, url, *a, **k):
        k["allow_redirects"] = False
        nome = threading.current_thread().name
        inicio = time.monotonic()
        eventos.append({"caso": caso.get("nome"), "thread": nome, "etapa": "admissao_http", "ts": inicio})
        if nome.startswith("Sonda-Preaquecimento-"):
            aquecimento_admitido.set()
        try:
            return original_http(sessao, method, url, *a, **k)
        finally:
            eventos.append({"caso": caso.get("nome"), "thread": nome, "etapa": "fim_http", "ts": time.monotonic()})
    http = criar_guarda_http_local(selecao, transportes, sem_redirect)
    os.environ.update(PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
        LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
        LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
        LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
        LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
    with tempfile.TemporaryDirectory(prefix="laylay_corrida_startup_") as pasta:
        root = preparar_instalacao_isolada(Path(pasta), requisicao_http=http)
        runtime = root._resposta_ia_runtime
        instalado = runtime._contexto()
        chaves = ("marcar_inicio_turno", "obter_turno_atual", "usar_modo_rapido",
            "texto_depende_de_contexto", "preparacao_conversa", "estado_conversa",
            "preparar_resposta", "validar_comandos_planejados", "atualizar_plano_proposta",
            "proposta_principal_vigente", "executar_comandos_json", "iniciar_orcamento_llm_turno",
            "configurar_orcamento_llm_turno", "finalizar_orcamento_llm_turno")
        def modelo(pedido):
            inicio = time.monotonic()
            resultado = instalado["modelo_llm"].executar(pedido)
            caso["modelos"].append({"pedido": asdict(pedido), "resultado": asdict(resultado),
                "segundos": round(time.monotonic()-inicio, 3)})
            return resultado
        def efeito_proibido(*_a, **_k):
            caso["efeitos_tentados"] += 1
            raise RuntimeError("Sonda de saudação não autoriza efeitos.")
        def concluir(_ctx, comandos, erros, fala, *_flags):
            caso["conclusoes"].append({"fala_planejada": fala, "comandos": deepcopy(comandos), "erros": list(erros)})
            return {"registrar_no_historico": False}
        ctx = {k: instalado[k] for k in chaves if k in instalado}
        ctx.update(modelo_llm=SimpleNamespace(executar=modelo),
            contexto_dispatch_runtime=SimpleNamespace(montar=lambda: {"executar_intencao": efeito_proibido}),
            contexto_finalizacao_runtime=SimpleNamespace(montar=lambda: {}), finalizar_execucao=concluir)
        runtime._contexto_getter = lambda: ctx
        for nome in ("durante", "antes", "apos"):
            verificar_sessao()
            caso = {"nome": nome, "modelos": [], "conclusoes": [], "efeitos_tentados": 0}
            ativo, terminou = threading.Event(), threading.Event()
            aquecimento_admitido.clear()
            if nome == "antes": ativo.set()
            def aquecer():
                try:
                    caso["preaquecimento"] = root._runtime_llm_portatil.preaquecer(interacao_ativa=ativo.is_set)
                finally:
                    terminou.set()
            inicio_http = len(transportes)
            root._servicos_background_runtime.iniciar("Sonda-Preaquecimento-" + nome, aquecer)
            if nome == "durante":
                if not aquecimento_admitido.wait(5):
                    raise RuntimeError("Não alcançou admissão HTTP do aquecimento.")
                caso["llm_em_andamento_durante_aquecimento"] = root._llm_http_runtime.requisicao_local_em_andamento
                caso["atividade_consumer_durante_aquecimento"] = root._modo_jogo_runtime.llm_em_andamento()
                caso["aquecimento_terminou_antes_da_entrada"] = terminou.is_set()
            elif not terminou.wait(35):
                raise RuntimeError("Aquecimento não terminou no recorte diagnóstico.")
            ativo.set()
            caso["entrada_ts"] = time.monotonic()
            runtime.processar("Bom dia, Laylay. Me responda com uma saudação curta.", origem="sonda_corrida_startup")
            caso["segundos_turno"] = round(time.monotonic()-caso["entrada_ts"], 3)
            if not terminou.wait(35):
                raise RuntimeError("Aquecimento ficou pendente após o turno.")
            caso["orcamento"] = root._cliente_llm_runtime.servico.cliente.orcamento_turno.diagnostico()
            caso["transportes"] = deepcopy(transportes[inicio_http:])
            caso["falhas"] = []
            if not caso["modelos"] or not all(m["resultado"]["sucesso"] for m in caso["modelos"]):
                caso["falhas"].append("geracao_principal_sem_sucesso")
            if len(caso["conclusoes"]) != 1 or not caso["conclusoes"][0]["fala_planejada"]:
                caso["falhas"].append("conclusao_ausente_ou_duplicada")
            if caso["efeitos_tentados"] or any(c["comandos"] or c["erros"] for c in caso["conclusoes"]):
                caso["falhas"].append("saudacao_com_efeito_ou_erro")
            casos.append(caso)
    return {"ps_antes": ps_antes, "casos": casos, "eventos": eventos,
        "falhas": [f for c in casos for f in c["falhas"]],
        "startup_background_instalado": True, "main_iniciado": False,
        "prioridade_retirada_na_sonda": True, "publicacao_atual": False, "audio_fisico": False,
        "configuracao_alterada": False, "modelo_descarregado_pela_sonda": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artefato", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--somente-instalada", action="store_true")
    modo.add_argument("--corrida-startup", action="store_true")
    args = parser.parse_args()
    if (args.saida.exists() or not args.saida.resolve().is_relative_to((RAIZ/"resultados_testes").resolve())
            or not args.artefato.resolve().is_relative_to((RAIZ/"resultados_testes").resolve())):
        parser.error("Usar fonte e destino novo dentro de resultados_testes.")
    dados = json.loads(args.artefato.read_text(encoding="utf-8"))
    selecao = selecao_local()
    preparar_replay(dados, selecao)
    verificar_sessao()
    fontes = ["configuracao.env", "mente_laylay/personalidade/confirmacao_llm.py",
        "mente_laylay/integracao/cliente_llm_runtime.py", "mente_laylay/integracao/orcamento_llm_turno.py",
        "mente_laylay/integracao/runtime_llm_portatil.py", "mente_laylay/integracao/llm_http.py",
        "mente_laylay/integracao/composicao_inteligencia_externa.py", "laylay.py"]
    hashes = lambda: {f: hashlib.sha256((RAIZ/f).read_bytes()).hexdigest() for f in fontes}
    antes = hashes()
    resultado = (coletar_corrida_startup(dados, selecao) if args.corrida_startup
                 else coletar_autoria_instalada(dados, selecao) if args.somente_instalada
                 else coletar(dados, selecao))
    depois = hashes()
    with args.saida.open("x", encoding="utf-8") as arquivo:
        json.dump({"head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], text=True),
            "artefato_origem": str(args.artefato), "selecao": selecao, **resultado,
            "hashes_antes": antes, "hashes_depois": depois, "fontes_estaveis": antes == depois},
            arquivo, ensure_ascii=False, indent=2)
    return int(antes != depois or bool(resultado.get("falhas")))


if __name__ == "__main__":
    raise SystemExit(main())
