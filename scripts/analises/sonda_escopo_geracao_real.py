"""Geração local real em mensagens mistas; executor/finalização isolados.

Reutiliza o runtime RespostaIA instalado, prompt, pós-processador e validador.
Força a passagem pela LLM omitindo o atalho prioritário; não certifica main,
voz, efeitos externos nem a frequência de erros fora deste painel diagnóstico.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from urllib.parse import urlsplit

from scripts.analises.sonda_escopo_propostas_mistas import (
    RAIZ, painel, preparar_instalacao_isolada,
)


def serializar(valor):
    if is_dataclass(valor):
        return asdict(valor)
    raise TypeError(f"Tipo de artefato não suportado: {type(valor).__name__}")


def selecao_local() -> dict[str, str]:
    if os.environ.get("LAYLAY_SONDA_ESCOPO_BASELINE"):
        raise RuntimeError("A coleta real não admite substituição contrafactual do validador.")
    chaves = {"LAYLAY_LLM_BACKEND", "LAYLAY_LLM_BASE_URL", "LAYLAY_LLM_MODEL"}
    valores = {}
    for linha in (RAIZ / "configuracao.env").read_text(encoding="utf-8-sig").splitlines():
        chave, sep, valor = linha.strip().partition("=")
        if sep and chave in chaves:
            valores[chave] = valor.strip().strip('"').strip("'")
    url = urlsplit(valores.get("LAYLAY_LLM_BASE_URL", ""))
    if (valores.get("LAYLAY_LLM_BACKEND") != "ollama" or not valores.get("LAYLAY_LLM_MODEL")
            or url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1"}
            or url.username or url.password or url.query or url.fragment):
        raise RuntimeError("A sonda exige seleção persistida Ollama local sem credenciais na URL.")
    if any(k in os.environ and os.environ[k] != v for k, v in valores.items()):
        raise RuntimeError("Seleção externa divergente: não vou substituir o modelo escolhido.")
    return valores


def comparar_escopos(esperados: list[dict], comandos: list[dict]) -> dict:
    """Compara representações; não chama ausência de proposta de falso bloqueio."""
    from mente_laylay.cognicao.escopo_autorizacao import _identidade_operacional
    gold = [_identidade_operacional(c) for c in esperados]
    restantes = list(gold)
    indevidos = []
    for cmd in comandos:
        identidade = _identidade_operacional(cmd)
        if identidade is not None and identidade in restantes:
            restantes.remove(identidade)
        else:
            indevidos.append(deepcopy(cmd))
    ausentes = []
    for esperado, identidade in zip(esperados, gold):
        if identidade in restantes:
            ausentes.append(deepcopy(esperado))
            restantes.remove(identidade)
    return {"indevidos": indevidos, "ausentes": ausentes}


def criar_guarda_http_local(selecao: dict, transportes: list, original_http):
    """Aceita a assinatura requests (inclusive method/url por keyword)."""
    import requests

    def http_local(sessao, method, url, *args, **opcoes):
        partes = urlsplit(str(url))
        dados = opcoes.get("json")
        if (partes.scheme != "http" or partes.hostname not in {"localhost", "127.0.0.1", "::1"}
                or partes.port != urlsplit(selecao["LAYLAY_LLM_BASE_URL"]).port
                or partes.path not in {"/v1/chat/completions", "/api/chat"}
                or str(method).upper() != "POST" or not isinstance(dados, dict)
                or dados.get("model") != selecao["LAYLAY_LLM_MODEL"]
                or partes.username or partes.password or partes.query or partes.fragment):
            raise requests.RequestException("Rota fora da geração local autorizada para a sonda.")
        registro = {"url": str(url), "payload": deepcopy(dados)}
        transportes.append(registro)
        inicio = time.monotonic()
        try:
            retorno = original_http(sessao, method, url, *args, **opcoes)
            registro.update(status=retorno.status_code, resposta_http=retorno.text)
            return retorno
        except Exception as erro:
            registro["erro_tipo"] = type(erro).__name__
            raise
        finally:
            registro["segundos"] = round(time.monotonic() - inicio, 3)
    return http_local


def coletar_instalado_real(pasta: Path, selecao: dict, limite: int) -> dict:
    import requests
    transportes = []
    http_local = criar_guarda_http_local(selecao, transportes, requests.sessions.Session.request)

    root = preparar_instalacao_isolada(pasta, requisicao_http=http_local)
    runtime = root._resposta_ia_runtime
    original_ctx = runtime._contexto_getter
    instalado = runtime._contexto()
    validador = instalado["validar_comandos_planejados"]
    original_validar = validador._validar
    resultados = []
    # Sem callbacks prioritários, salvamento pessoal, presença, voz ou emoção.
    chaves = (
        "marcar_inicio_turno", "obter_turno_atual", "usar_modo_rapido",
        "texto_depende_de_contexto", "preparacao_conversa", "estado_conversa",
        "preparar_resposta", "validar_comandos_planejados", "atualizar_plano_proposta",
        "proposta_principal_vigente", "executar_comandos_json",
        "iniciar_orcamento_llm_turno", "configurar_orcamento_llm_turno",
        "finalizar_orcamento_llm_turno",
    )
    try:
        for caso in painel()[:min(limite, 9)]:
            modelos, preparadas, validacoes, recebidos, conclusoes = [], [], [], [], []
            inicio_http = len(transportes)
            inicio = time.monotonic()

            def modelo(pedido):
                resultado = instalado["modelo_llm"].executar(pedido)
                modelos.append({"pedido": asdict(pedido), "resultado": asdict(resultado)})
                return resultado

            def preparar(texto, bruto):
                preparada = instalado["preparar_resposta"](texto, bruto)
                preparadas.append(deepcopy(preparada))
                return preparada

            def validar(*a, **k):
                resultado = original_validar(*a, **k)
                validacoes.append(deepcopy(resultado))
                return resultado

            def capturar(pedido, texto):
                recebidos.append({"intent": pedido["intent"], "params": deepcopy(pedido["params"])})
                return False  # Não produz efeito, receipt ou sucesso.

            def concluir(ctx, comandos, erros, fala, *flags):
                conclusoes.append({"fala_planejada": fala, "comandos": deepcopy(comandos), "erros": list(erros)})
                return {"registrar_no_historico": False}  # Não publica nem fala.

            ctx = {k: instalado[k] for k in chaves if k in instalado}
            ctx.update(modelo_llm=SimpleNamespace(executar=modelo), preparar_resposta=preparar,
                contexto_dispatch_runtime=SimpleNamespace(montar=lambda: {"executar_intencao": capturar}),
                contexto_finalizacao_runtime=SimpleNamespace(montar=lambda: {}), finalizar_execucao=concluir)
            validador._validar = validar
            runtime._contexto_getter = lambda: ctx
            runtime.processar(caso["texto"], origem="sonda_escopo_geracao_real")
            mental = root._estado_compartilhado_runtime.snapshot()["mental"]
            preparada = preparadas[-1] if preparadas else {}
            validacao = validacoes[-1] if validacoes else {}
            propostos = list(preparada.get("comandos") or [])
            admitidos = list(validacao.get("comandos") or [])
            medida_proposta = comparar_escopos(caso["esperados"], propostos)
            medida_validacao = comparar_escopos(caso["esperados"], admitidos)
            identidades_propostas = comparar_escopos(caso["esperados"], propostos)["ausentes"]
            bloqueios_a_investigar = [c for c in medida_validacao["ausentes"] if c not in identidades_propostas]
            registros_http = deepcopy(transportes[inicio_http:])
            resultados.append({"caso": caso, "turno": mental.get("turno_atual"),
                "modelos": modelos, "preparadas": preparadas, "validacoes": validacoes,
                "recebidos_porta_executor": recebidos, "conclusoes_isoladas": conclusoes,
                "transportes": registros_http, "plano": mental.get("plano_turno_atual"),
                "medida_proposta_preparada": medida_proposta, "medida_validacao": medida_validacao,
                "bloqueios_de_proposta_equivalente_a_investigar": bloqueios_a_investigar,
                "medida_porta_executor": comparar_escopos(caso["esperados"], recebidos),
                "geracao_principal_sucesso": bool(modelos and modelos[0]["resultado"]["sucesso"]
                    and any(r.get("status") == 200 for r in registros_http)),
                "segundos": round(time.monotonic() - inicio, 3)})
            sys.__stdout__.write(f"CASO_REAL={caso['id']} concluido\n")
            sys.__stdout__.flush()
    finally:
        runtime._contexto_getter = original_ctx
        validador._validar = original_validar
    return {"resultados": resultados}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--limite", type=int, default=9, choices=range(1, 10))
    args = parser.parse_args()
    destino = args.saida.resolve()
    if not destino.is_relative_to((RAIZ / "resultados_testes").resolve()) or destino.exists():
        parser.error("usar destino novo dentro de resultados_testes")
    selecao = selecao_local()
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica
    instancia = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not instancia.adquirida:
        print("Laylay aberta: sonda não iniciada; nenhuma sessão interrompida.")
        return 73
    fontes = ["laylay.py", "scripts/analises/sonda_escopo_propostas_mistas.py", __file__,
        "mente_laylay/cognicao/escopo_autorizacao.py", "mente_laylay/cognicao/decisao_turno.py",
        "mente_laylay/cognicao/modalidade_turno.py", "mente_laylay/autonomia/resposta_ia_runtime.py",
        "mente_laylay/autonomia/contexto_resposta_ia.py", "mente_laylay/autonomia/processamento_resposta_ia.py",
        "mente_laylay/autonomia/dispatcher_comandos_json.py", "mente_laylay/autonomia/orquestrador_deterministico.py",
        "mente_laylay/integracao/preparador_requisicao_llm.py", "mente_laylay/integracao/cliente_llm_runtime.py",
        "mente_laylay/integracao/llm_http.py", "mente_laylay/integracao/preparacao_llm.py",
        "mente_laylay/personalidade/prompt_voz_unica.py", "mente_laylay/personalidade/perfil_amizade.py",
        "configuracao.env"]
    def hashes():
        return {str(Path(p).relative_to(RAIZ) if Path(p).is_absolute() else p):
                hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True)}
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="laylay_geracao_") as pasta:
            env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
                LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
                LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
                LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
                LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
            codigo = ("import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
                "from scripts.analises.sonda_escopo_geracao_real import coletar_instalado_real,serializar; "
                "r=coletar_instalado_real(Path(sys.argv[2]),json.loads(sys.argv[3]),int(sys.argv[4])); "
                "sys.__stdout__.write('GERACAO_JSON='+json.dumps(r,ensure_ascii=False,default=serializar)+'\\n')")
            processo = subprocess.run([sys.executable, "-c", codigo, str(RAIZ), pasta,
                json.dumps(selecao), str(args.limite)], cwd=RAIZ, env=env, capture_output=True,
                text=True, encoding="utf-8", timeout=900)
        linhas = [l for l in processo.stdout.splitlines() if l.startswith("GERACAO_JSON=")]
        if processo.returncode or len(linhas) != 1:
            raise RuntimeError("Sonda incompleta:\n" + processo.stderr[-2500:] + processo.stdout[-1000:])
        instalado = json.loads(linhas[0].split("=", 1)[1])
        depois = hashes()
        resultados = instalado["resultados"]
        relatorio = {**base, **instalado, "selecao_persistida": selecao,
            "instante_utc": datetime.now(timezone.utc).isoformat(), "hashes_antes": antes,
            "hashes_depois": depois, "fontes_estaveis": antes == depois,
            "resumo": {"casos": len(resultados),
                "geracoes_principais_sucesso": sum(r["geracao_principal_sucesso"] for r in resultados),
                "casos_com_propostas_divergentes": sum(bool(r["medida_proposta_preparada"]["indevidos"]) for r in resultados),
                "casos_com_admissoes_divergentes": sum(bool(r["medida_validacao"]["indevidos"]) for r in resultados),
                "casos_com_porta_executor_divergente": sum(bool(r["medida_porta_executor"]["indevidos"]) for r in resultados),
                "casos_com_pedidos_ausentes": sum(bool(r["medida_validacao"]["ausentes"]) for r in resultados),
                "casos_com_bloqueios_a_investigar": sum(bool(r["bloqueios_de_proposta_equivalente_a_investigar"]) for r in resultados)},
            "runtime_main_validado": False,
            "modelo_real_consultado": any(r.get("status") == 200 for c in resultados for r in c["transportes"]),
            "efeitos_externos_executados": False, "voz_validada": False, "holdout": False,
            "limite": "rota LLM forçada por omissão do atalho prioritário; contexto de coleta isolado, finalização não publicada",
            "stderr_subprocesso": processo.stderr}
        with destino.open("x", encoding="utf-8") as arquivo:
            json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
        print(json.dumps(relatorio["resumo"], ensure_ascii=False))
        print("Artefato:", destino)
        return int(not relatorio["fontes_estaveis"] or bool(relatorio["resumo"]["casos_com_admissoes_divergentes"])
            or relatorio["resumo"]["geracoes_principais_sucesso"] != len(resultados))
    finally:
        instancia.liberar()


if __name__ == "__main__":
    raise SystemExit(main())
