"""Diagnóstico local: captura o payload real sem alterar decisões ou respostas.

Artefatos podem conter contexto pessoal; ficam em resultados_testes, não publicar.
"""
from pathlib import Path
from datetime import datetime
import json
import os
import runpy
import sys
import threading
import argparse
from urllib.parse import urlsplit
import requests


def main() -> None:
    raiz = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roteiro", choices=(
        "roteiro_p0_leitura_sem_autorizacao.py", "roteiro_fonte_textual_ausente.py",
        "roteiro_neural_dialogo_controlado_50_v1.py",
        "roteiro_transformacao_conversacional.py",
        "roteiro_recomendacao_contextual.py",
        "roteiro_site_por_assunto.py",
        "roteiro_reparo_parcial_conversa.py",
        "roteiro_confirmacoes_recusas.py",
        "roteiro_recusas_autoria.py",
        "roteiro_explicacao_capacidades.py",
        "roteiro_iot_explicacoes.py",
    ), default="roteiro_p0_leitura_sem_autorizacao.py")
    parser.add_argument("--capturar-chrome", action="store_true",
                        help="Registra o retorno detalhado real, sem alterar o comando ou recibo")
    parser.add_argument("--capturar-preparacao", action="store_true",
                        help="Compara o pedido e o payload preparado com o envio HTTP real")
    parser.add_argument("--replay-captura", type=Path,
                        help="Reapresenta uma resposta HTTP gravada; NÃO é geração real nesse turno")
    parser.add_argument("--replay-texto",
                        help="Entrada exata com uma única resposta na captura; exige --replay-captura")
    parser.add_argument("--falhas-controladas", action="store_true",
                        help="Injeta timeout/conexão/ocupação uma vez em perguntas da sonda de capacidades; não são falhas espontâneas")
    parser.add_argument("--reparo-vazio", action="store_true",
                        help="Com replay, substitui o primeiro reparo desse pedido por {}; orçamento real permanece intacto")
    argumentos = parser.parse_args()
    if bool(argumentos.replay_captura) != bool(argumentos.replay_texto):
        parser.error("replay exige captura e texto juntos")
    if argumentos.reparo_vazio and not argumentos.replay_captura:
        parser.error("reparo vazio exige replay explícito")
    if argumentos.falhas_controladas and (argumentos.replay_captura or argumentos.roteiro != "roteiro_explicacao_capacidades.py"):
        parser.error("falhas controladas exigem roteiro de capacidades sem replay")
    replay_resposta = None
    if argumentos.replay_captura:
        origem_replay = argumentos.replay_captura.resolve(strict=True)
        if not origem_replay.is_relative_to((raiz / "resultados_testes").resolve()):
            parser.error("a captura de replay precisa estar em resultados_testes")
        candidatas, alvo_replay = [], False
        for linha in origem_replay.read_text(encoding="utf-8").splitlines():
            evento = json.loads(linha)
            if evento.get("etapa") == "envio":
                usuario = next((m.get("content") for m in reversed(evento["payload"]["messages"])
                                if m.get("role") == "user"), "")
                alvo_replay = usuario == argumentos.replay_texto
            elif evento.get("etapa") == "resposta" and alvo_replay:
                if evento.get("status") == 200:
                    candidatas.append(evento["texto"])
                alvo_replay = False
        if len(candidatas) != 1:
            parser.error("replay exige exatamente uma resposta HTTP 200 para a entrada")
        replay_resposta = candidatas[0]
        json.loads(replay_resposta)  # aborta captura inválida antes de abrir a Laylay
    roteiro = argumentos.roteiro
    pasta = raiz / "resultados_testes" / ("transporte_evidencia-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    pasta.mkdir(parents=True, exist_ok=False)
    for chave, valor in {
        "GMAIL_USER": " ", "GMAIL_APP_PASSWORD": " ",
        "LAYLAY_IOT_MODO": "simulado", "LAYLAY_TERMINAL_2": "0",
        "LAYLAY_MICROFONE_ATIVO": "0", "LAYLAY_BRIEFING_INICIAL": "0",
        "LAYLAY_FALAS_INICIAIS": "0", "LAYLAY_PRESENCA": "0",
        "LAYLAY_MODO_JOGO_AUTO": "0", "LAYLAY_LOG_VERBOSE": "1",
    }.items():
        os.environ[chave] = valor
    original = requests.post
    lock = threading.Lock()
    replay_usado = False
    reparo_vazio_usado = False
    falhas_pendentes = {
        "como eu poderia pausar a música?": "timeout",
        "como eu poderia retomar a música?": "conexao",
        "como eu poderia abrir a calculadora?": "ocupacao",
    } if argumentos.falhas_controladas else {}

    def observar(url, *args, **kwargs):
        nonlocal replay_usado, reparo_vazio_usado
        dados = kwargs.get("json")
        captura = isinstance(dados, dict) and "messages" in dados
        if captura and urlsplit(str(url)).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise RuntimeError("Sonda permitida somente com modelo local")
        if captura:
            with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps({"etapa": "envio", "payload": dados}, ensure_ascii=False) + "\n")
        usuario = next((m.get("content") for m in reversed(dados["messages"])
                        if m.get("role") == "user"), "") if captura else ""
        injetar_vazio = False
        if argumentos.reparo_vazio and replay_usado and not reparo_vazio_usado:
            try:
                pedido_reparo = json.loads(usuario)
            except (TypeError, ValueError):
                pedido_reparo = {}
            if (isinstance(pedido_reparo, dict)
                    and pedido_reparo.get("mensagem_atual") == argumentos.replay_texto
                    and pedido_reparo.get("contrato_de_reparo")):
                reparo_vazio_usado = injetar_vazio = True
                with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps({"etapa": "reparo_vazio_injetado", "geracao_real": False}) + "\n")
        with lock:
            falha_injetada = falhas_pendentes.pop(usuario, "")
            if falha_injetada:
                with (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps({"etapa": "falha_injetada", "categoria": falha_injetada,
                                              "texto_usuario": usuario, "espontanea": False}, ensure_ascii=False) + "\n")
        if falha_injetada == "timeout":
            raise requests.exceptions.ReadTimeout("Sonda F3: timeout controlado")
        if falha_injetada == "conexao":
            raise requests.exceptions.ConnectionError("Sonda F3: conexão controlada")
        if falha_injetada == "ocupacao":
            resposta = requests.Response()
            resposta.status_code = 200
            resposta._content = json.dumps({"choices": [{"message": {"content": "__LAYLAY_LLM_OCUPADA__"}}]}).encode("utf-8")
            resposta.encoding = "utf-8"
            return resposta
        usar_replay = False
        if replay_resposta and usuario == argumentos.replay_texto:
            with lock:
                if not replay_usado:
                    replay_usado, usar_replay = True, True
                    with (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                        arquivo.write(json.dumps({"etapa": "replay", "origem": str(origem_replay),
                                                  "texto_usuario": usuario,
                                                  "geracao_real": False}, ensure_ascii=False) + "\n")
        if injetar_vazio:
            resposta = requests.Response()
            resposta.status_code = 200
            resposta._content = json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode("utf-8")
            resposta.encoding = "utf-8"
        elif usar_replay:
            print("SONDA REPLAY: resposta gravada; demais fronteiras do runtime preservadas.", flush=True)
            resposta = requests.Response()
            resposta.status_code = 200
            resposta._content = replay_resposta.encode("utf-8")
            resposta.encoding = "utf-8"
        else:
            resposta = original(url, *args, **kwargs)
        if captura:
            with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps({"etapa": "resposta", "status": resposta.status_code, "texto": resposta.text}, ensure_ascii=False) + "\n")
        return resposta

    requests.post = observar
    from mente_laylay.integracao.preparador_requisicao_llm import PreparadorRequisicaoLLMRuntime
    preparar_original = PreparadorRequisicaoLLMRuntime.preparar

    def observar_preparacao(self, pedido):
        requisicao = preparar_original(self, pedido)
        with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps({
                "etapa": "preparacao", "tipo_chamada": pedido.tipo_chamada,
                "modo_rapido": pedido.modo_rapido,
                "mensagens_pedido": list(pedido.mensagens),
                "payload": dict(requisicao.payload),
            }, ensure_ascii=False) + "\n")
        return requisicao

    if argumentos.capturar_preparacao:
        PreparadorRequisicaoLLMRuntime.preparar = observar_preparacao
    from mente_laylay.integracao.chrome_comandos import ChromeComandosRuntime
    enviar_original = ChromeComandosRuntime.enviar_detalhado

    def observar_chrome(self, action=None, payload=None):
        retorno = enviar_original(self, action, payload)
        # O artefato é local e contém o recibo da mesma chamada, não uma
        # reconsulta ao último estado global após outra operação.
        with lock, (pasta / "recibos_chrome.jsonl").open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps({"action": action, "payload": payload,
                                      "retorno": retorno}, ensure_ascii=False) + "\n")
        return retorno

    if argumentos.capturar_chrome:
        ChromeComandosRuntime.enviar_detalhado = observar_chrome
    print("CAPTURA_LOCAL:", pasta, flush=True)
    sys.argv = [str(raiz / "laylay.py"), "--roteiro", str(raiz / "scripts" / "roteiros" / roteiro)]
    try:
        runpy.run_path(str(raiz / "laylay.py"), run_name="__main__")
    finally:
        requests.post = original
        PreparadorRequisicaoLLMRuntime.preparar = preparar_original
        ChromeComandosRuntime.enviar_detalhado = enviar_original


if __name__ == "__main__":
    main()
