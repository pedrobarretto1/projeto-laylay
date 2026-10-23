"""Conversa contínua instalada: texto/modelo reais, persistência isolada, sem efeitos.

Mantém prioridade, pré-fluxo, histórico, autoria e publicação entre os turnos.
O dispatcher externo é uma porta de recusa: propostas não viram efeitos.
Não comprova áudio nem altera a sessão pessoal que permanece aberta.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

HISTORICO = (
    "oi laylay, como voce ta?",
    "e o que voce esta fazendo?",
    "o que voce esta fazendo?",
    "o que voce ta fazendo?",
    "e como estao as coisas no computador?",
    "como assim?",
)

COTIDIANO = (
    "oi laylay, como voce ta?",
    "eu to bem, hoje tive uma aula puxada",
    "foi de matemática, fiquei cansado",
    "mas consegui terminar os exercícios",
    "o que você acha disso?",
    "como assim?",
    "mudando de assunto, vamos só conversar um pouco",
    "valeu por conversar comigo",
)


def salvar(caminho: Path, valor: object) -> None:
    caminho.write_text(json.dumps(valor, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def coletar(destino: Path, *, modelo_real: bool, entradas: tuple[str, ...] = HISTORICO,
            falhas_transporte: tuple[int, ...] = (), falhas_reparo: bool = False) -> dict:
    import requests
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local

    destino.mkdir(parents=True, exist_ok=False)
    fontes = list((RAIZ / "mente_laylay").rglob("*.py")) + [RAIZ / "laylay.py"]
    hashes = {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes}
    salvar(destino / "baseline.json", {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
        "fontes": hashes,
    })
    transportes: list[dict] = []
    selecao = selecao_local() if modelo_real else {}
    if modelo_real and (falhas_transporte or falhas_reparo):
        raise ValueError("não misturar geração real com injeção de falha")
    def timeout_controlado(*_a, **_k):
        raise requests.ReadTimeout("timeout injetado na porta HTTP da sonda")
    http = (criar_guarda_http_local(selecao, transportes, requests.sessions.Session.request) if modelo_real
            else timeout_controlado if falhas_transporte or falhas_reparo else None)
    memoria = destino / "memoria_isolada"
    memoria.mkdir()
    root = preparar_instalacao_isolada(memoria, requisicao_http=http)
    from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
    from mente_laylay.autonomia import coordenador_intencao

    # O histórico real da conversa fica ligado ao mesmo owner. Somente as
    # folhas externas são recusadas; o resolvedor e a prioridade permanecem.
    root._voz_runtime.falar = lambda *_a, **_k: False
    executores: list[dict] = []
    def recusar(resultado, texto, contexto):
        executores.append({"pedido": deepcopy(resultado), "texto": texto})
        return False
    coordenador_intencao.executar_intencao = recusar
    publicadas: list[str] = []
    root._orquestrador_fala_runtime.registrar_observador_texto_final(
        lambda fala, *_a, **_k: publicadas.append(str(fala)) or True)
    chamadas: list[dict] = []
    numero_turno = 0
    original_modelo = RegistroModeloLLM.executar
    def modelo(self, pedido):
        registro = {"pedido": asdict(pedido)}
        chamadas.append(registro)
        resposta = original_modelo(self, pedido) if (modelo_real or numero_turno in falhas_transporte
            or falhas_reparo and pedido.tipo_chamada == "reparo_comunicacao") else ResultadoModelo(
            json.dumps({"fala": "Estou acompanhando nossa conversa.", "comandos": []}), True)
        registro["resultado"] = asdict(resposta)
        return resposta
    RegistroModeloLLM.executar = modelo
    runtime = root._resposta_ia_runtime
    original_contexto = runtime._contexto_getter
    prioridades: list[dict] = []
    def contexto():
        ctx = original_contexto()
        original_prioridade = ctx.get("processar_comandos_prioritarios")
        if callable(original_prioridade):
            def prioridade(texto):
                resultado = original_prioridade(texto)
                prioridades.append({"texto": texto, "tratado": resultado})
                return resultado
            ctx["processar_comandos_prioritarios"] = prioridade
        return ctx
    runtime._contexto_getter = contexto
    resultados: list[dict] = []
    relatorio = {"modelo_real": modelo_real, "falhas_transporte": falhas_transporte, "falhas_reparo": falhas_reparo,
                 "selecao": selecao, "resultados": resultados,
                 "transportes": transportes, "efeitos_externos": False, "audio": False}
    for texto in entradas:
        numero_turno += 1
        ini = (len(publicadas), len(chamadas), len(executores), len(transportes), len(prioridades))
        antes = [dict(m) for m in root._memoria_conversa_get("messages", [])]
        inicio = time.monotonic()
        runtime.processar(texto, origem="sonda_conversa_continua")
        mental = root._estado_compartilhado_runtime.snapshot()["mental"]
        resultados.append({"texto": texto, "historico_antes": antes,
            "historico_depois": [dict(m) for m in root._memoria_conversa_get("messages", [])],
            "turno": mental.get("turno_atual"), "plano": mental.get("plano_turno_atual"),
            "contrato": mental.get("contrato_fala_atual"),
            "respostas": publicadas[ini[0]:], "modelos": chamadas[ini[1]:],
            "executores_recusados": executores[ini[2]:], "indices_http": [ini[3], len(transportes)],
            "prioridades": prioridades[ini[4]:], "segundos": round(time.monotonic()-inicio, 3)})
        salvar(destino / "conversa.json", relatorio)
        sys.__stdout__.write(json.dumps({"turno": len(resultados), "texto": texto,
            "respostas": resultados[-1]["respostas"],
            "prioridades": resultados[-1]["prioridades"],
            "executores": resultados[-1]["executores_recusados"],
            "http": [r.get("status") for r in transportes[ini[3]:]]}, ensure_ascii=False) + "\n")
        sys.__stdout__.flush()
    relatorio["fontes_alteradas_durante_coleta"] = [str(p.relative_to(RAIZ)) for p in fontes
        if hashlib.sha256(p.read_bytes()).hexdigest() != hashes[str(p.relative_to(RAIZ))]]
    salvar(destino / "conversa.json", relatorio)
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--modelo-real", action="store_true")
    parser.add_argument("--cenario", choices=("historico", "cotidiano"), default="historico")
    args = parser.parse_args()
    caminho = args.saida.resolve()
    if not caminho.is_relative_to((RAIZ / "resultados_testes").resolve()) or caminho.exists():
        parser.error("a saída precisa ser uma pasta nova dentro de resultados_testes")
    coletar(caminho, modelo_real=args.modelo_real,
            entradas=COTIDIANO if args.cenario == "cotidiano" else HISTORICO)
