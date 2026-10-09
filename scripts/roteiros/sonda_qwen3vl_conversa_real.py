"""Conversa finita pelo composition root real; não fornece respostas ou receipts.

Usa a seleção persistida do Qwen3-VL Instruct. O loader lê as constantes por
AST, portanto o mesmo arquivo contém o roteiro e o inicializador da coleta.
"""

from __future__ import annotations

import contextlib
from datetime import datetime
import functools
import hashlib
import json
import os
from pathlib import Path
import runpy
import sqlite3
import subprocess
import sys
import threading
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests


COMANDOS = (
    "Oi, Laylay, tudo bem?",
    "O que é uma playlist?",
    "E como eu poderia organizar uma? Só quero a explicação.",
)
EXPECTATIVAS_SEMANTICAS = {
    1: {"sem_comando": True},
    2: {"sem_comando": True},
    3: {"sem_comando": True},
}
ATRASO_INICIAL_S = 0.0
TIMEOUT_RESPOSTA_S = 90.0
TIMEOUT_VOZ_S = 10.0
INTERVALO_ENTRE_COMANDOS_S = 0.25
PARAR_SEM_RESPOSTA = True
ENCERRAR_AO_FINAL = True
SILENCIAR_VOZ_DURANTE_TESTE = True
AGUARDAR_CONFIRMACAO_EXECUCAO = False

RAIZ = Path(__file__).resolve().parents[2]
MODELO_ESPERADO = "qwen3-vl:4b-instruct"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def _selecao_persistida() -> dict[str, str]:
    chaves = {"LAYLAY_LLM_BACKEND", "LAYLAY_LLM_BASE_URL", "LAYLAY_LLM_MODEL"}
    valores: dict[str, str] = {}
    with (RAIZ / "configuracao.env").open(encoding="utf-8-sig") as arquivo:
        for linha in arquivo:
            chave, separador, valor = linha.strip().partition("=")
            if separador and chave in chaves:
                valores[chave] = valor.strip().strip('"').strip("'")
    if valores.get("LAYLAY_LLM_MODEL", "").casefold() != MODELO_ESPERADO:
        raise RuntimeError("A seleção persistida ainda não é Qwen3-VL 4B Instruct.")
    if valores.get("LAYLAY_LLM_BACKEND", "").casefold() != "ollama":
        raise RuntimeError("A sonda exige o backend Ollama já selecionado na configuração.")
    partes = urlsplit(valores.get("LAYLAY_LLM_BASE_URL", ""))
    if (
        partes.scheme != "http" or partes.hostname not in {"localhost", "127.0.0.1", "::1"}
        or partes.username or partes.password or partes.query or partes.fragment
    ):
        raise RuntimeError("A seleção persistida não aponta para Ollama local.")
    for chave, valor in valores.items():
        if chave in os.environ and os.environ[chave] != valor:
            raise RuntimeError("Uma variável externa difere da seleção persistida; a sonda não a sobrescreve.")
    return valores


def main() -> int:
    selecao = _selecao_persistida()
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica

    instancia = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not instancia.adquirida:
        print("SONDA_QWEN3VL não iniciada: a Laylay já tem uma sessão aberta.", flush=True)
        return 73
    instancia.liberar()

    origem = RAIZ / "memoria" / "laylay_memoria.sqlite"
    if not origem.is_file():
        raise RuntimeError("O SQLite original está ausente; não vou criar fatos para esta coleta.")
    pasta = RAIZ / "resultados_testes" / "troca_qwen3vl_20261007" / "runtime" / (
        "conversa_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    pasta.mkdir(parents=True, exist_ok=False)
    banco = pasta / "memoria" / "laylay_memoria.sqlite"
    banco.parent.mkdir()
    with sqlite3.connect(origem.resolve().as_uri() + "?mode=ro", uri=True) as entrada:
        with sqlite3.connect(banco) as saida:
            entrada.backup(saida)
    configuracao_sha256 = hashlib.sha256((RAIZ / "configuracao.env").read_bytes()).hexdigest()
    fontes = (
        "laylay.py", "mente_laylay/integracao/composicao_inteligencia_externa.py",
        "mente_laylay/integracao/modelo_visual_local.py",
        "mente_laylay/integracao/cliente_llm_runtime.py",
        "mente_laylay/integracao/preparador_requisicao_llm.py",
        "mente_laylay/integracao/roteiro_teste_conversa.py",
    )
    baseline = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "status": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
        "sonda_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "configuracao_sha256": configuracao_sha256,
        "selecao_persistida": selecao,
        "fontes_sha256": {nome: hashlib.sha256((RAIZ / nome).read_bytes()).hexdigest() for nome in fontes},
        "sqlite_copia_sha256": hashlib.sha256(banco.read_bytes()).hexdigest(),
        "entradas": list(COMANDOS),
        "escopo": "laylay.py --roteiro pelo root real; geração local e conclusão textual originais",
        "isolamento": "SQLite copiado read-only da origem; resumo, pessoas e central próprios da coleta",
        "restricoes": "voz silenciada; microfone, email, IoT físico, avatar, terminal e briefing desativados",
        "guarda": "bloqueia HTTP Groq e geração remota; não altera autorização, respostas, receipts ou gates",
        "limites": "não prova qualidade geral, visão, audição ou isolamento de toda persistência do runtime",
        "replay": False, "respostas_injetadas": False, "modelo_sobrescrito": False,
    }
    (pasta / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    trava = threading.RLock()
    transportes: list[dict[str, Any]] = []
    conclusoes: dict[int, dict[str, Any]] = {}
    bloqueios: list[str] = []
    restauracoes: list[tuple[Any, str, Any]] = []

    def registrar(nome: str, registro: dict[str, Any]) -> None:
        with trava, (pasta / nome).open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def substituir(owner: Any, nome: str, criar: Any) -> None:
        original = getattr(owner, nome)
        setattr(owner, nome, functools.wraps(original)(criar(original)))
        restauracoes.append((owner, nome, original))

    def observar_http(original: Any) -> Any:
        def chamar(sessao: Any, method: str, url: str, *args: Any, **opcoes: Any) -> Any:
            partes = urlsplit(str(url))
            local = partes.hostname in {"localhost", "127.0.0.1", "::1"}
            dados = opcoes.get("json")
            geracao = isinstance(dados, dict) and bool(dados.get("messages") or dados.get("prompt"))
            if partes.hostname == "api.groq.com" or (geracao and not local):
                with trava:
                    bloqueios.append("rota_remota_bloqueada")
                registrar("http.jsonl", {"etapa": "bloqueado", "destino": partes.hostname})
                raise RuntimeError("A sonda não autoriza envio de conversa para um provedor remoto.")
            modelo = str(dados.get("model") or "") if isinstance(dados, dict) else ""
            if geracao and modelo.casefold() != MODELO_ESPERADO:
                with trava:
                    bloqueios.append("modelo_divergente_bloqueado")
                registrar("http.jsonl", {"etapa": "bloqueado", "modelo": modelo})
                raise RuntimeError("A geração não selecionou o modelo persistido esperado.")
            inicio = time.monotonic()
            status = None
            erro_tipo = ""
            try:
                resposta = original(sessao, method, url, *args, **opcoes)
                status = int(resposta.status_code)
                return resposta
            except Exception as erro:
                erro_tipo = type(erro).__name__
                raise
            finally:
                if local:
                    registro = {
                        "metodo": str(method).upper(),
                        "url": urlunsplit((partes.scheme, partes.netloc, partes.path, "", "")),
                        "modelo": modelo, "status": status,
                        "duracao_s": round(time.monotonic() - inicio, 4),
                        "geracao": geracao, "erro_tipo": erro_tipo,
                    }
                    with trava:
                        transportes.append(registro)
                    registrar("http.jsonl", registro)
        return chamar

    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
    from mente_laylay.integracao.roteiro_teste_conversa import RoteiroTesteConversaRuntime
    from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
    from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay

    def observar_conclusao(original: Any) -> Any:
        def atualizar(runtime: Any, indice: int, **campos: Any) -> Any:
            retorno = original(runtime, indice, **campos)
            if str(campos.get("status") or "") in {
                "respondido", "sem_resposta", "erro_envio", "voz_nao_finalizada",
            }:
                with runtime._lock:
                    item = dict(runtime._estado["itens"][indice])
                registro = {
                    "indice": indice + 1, "entrada": item.get("comando"),
                    "status": item.get("status"), "resposta": item.get("resposta"),
                    "avaliacao": item.get("avaliacao"), "plano": item.get("plano"),
                    "voz_silenciada": item.get("voz_silenciada"),
                    "resultado_turno_concluido": item.get("resultado_turno_concluido"),
                }
                with trava:
                    conclusoes[indice] = registro
                registrar("conclusoes.jsonl", registro)
            return retorno
        return atualizar

    def observar_metrica(original: Any) -> Any:
        def medir(runtime: Any, componente: str, duracao_ms: float,
                  sucesso: bool = True, **contexto: Any) -> Any:
            retorno = original(runtime, componente, duracao_ms, sucesso, **contexto)
            registrar("metricas.jsonl", {
                "componente": str(componente), "duracao_ms": round(float(duracao_ms), 3),
                "sucesso": bool(sucesso),
                **{chave: contexto[chave] for chave in
                   ("turno_id", "rota", "fase", "tipo_chamada") if chave in contexto},
            })
            return retorno
        return medir

    ambiente = {
        "GMAIL_USER": " ", "GMAIL_APP_PASSWORD": " ",
        "LAYLAY_IOT_MODO": "simulado", "IOT_CONTROLE_FISICO_AUTORIZADO": "NAO",
        "LAYLAY_TERMINAL_2": "0", "LAYLAY_MICROFONE_ATIVO": "0",
        "LAYLAY_BRIEFING_INICIAL": "0", "LAYLAY_FALAS_INICIAIS": "0",
        "LAYLAY_PRESENCA": "0", "LAYLAY_MODO_JOGO_AUTO": "0",
        "LAYLAY_MASCOT_ENABLED": "0", "LAYLAY_AVATAR_ATIVO": "0",
        "PYTHONIOENCODING": "utf-8",
    }
    anteriores = {chave: os.environ.get(chave) for chave in ambiente}
    argumentos = sys.argv[:]
    codigo = 0
    inicio = time.monotonic()
    print("SONDA_QWEN3VL_COLETA:", pasta, flush=True)
    try:
        os.environ.update(ambiente)
        substituir(MemoriaSQLite, "__init__", lambda original: (
            lambda self, db_path=None: original(self, str(banco))
        ))
        substituir(MemoriaLaylay, "__init__", lambda original: (
            lambda self, *, pasta_memoria, **opcoes: original(self, pasta_memoria=str(pasta / "resumo"), **opcoes)
        ))
        substituir(MemoriaPessoasRuntime, "__init__", lambda original: (
            lambda self, *, caminho, **opcoes: original(self, caminho=pasta / "pessoas.json", **opcoes)
        ))
        substituir(CentralNotificacoesRuntime, "__init__", lambda original: (
            lambda self, arquivo_estado, **opcoes: original(self, str(pasta / "central.json"), **opcoes)
        ))
        substituir(requests.Session, "request", observar_http)
        substituir(ObservabilidadeMenteRuntime, "registrar_metrica", observar_metrica)
        substituir(RoteiroTesteConversaRuntime, "_atualizar_item", observar_conclusao)
        sys.argv = [str(RAIZ / "laylay.py"), "--roteiro", str(Path(__file__).resolve()),
                    "--resultado-raiz", str(pasta / "roteiro")]
        with (pasta / "runtime.log").open("w", encoding="utf-8", buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                runpy.run_path(str(RAIZ / "laylay.py"), run_name="__main__")
    except SystemExit as erro:
        codigo = int(erro.code or 0) if isinstance(erro.code, (int, type(None))) else 1
    except BaseException as erro:
        codigo = 1
        registrar("erros.jsonl", {"tipo": type(erro).__name__})
        raise
    finally:
        for owner, nome, original in reversed(restauracoes):
            setattr(owner, nome, original)
        sys.argv = argumentos
        for chave, valor in anteriores.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        configuracao_preservada = hashlib.sha256((RAIZ / "configuracao.env").read_bytes()).hexdigest() == configuracao_sha256
        geracoes = [item for item in transportes if item["geracao"]]
        turnos_ok = len(conclusoes) == len(COMANDOS) and all(
            item["status"] == "respondido" and bool(item["resposta"]) for item in conclusoes.values()
        )
        sem_comandos = bool(conclusoes) and all(
            int((item.get("avaliacao") or {}).get("quantidade_comandos") or 0) == 0
            and not (item.get("plano") or {}).get("comandos") for item in conclusoes.values()
        )
        completo = bool(codigo == 0 and turnos_ok and sem_comandos and geracoes and not bloqueios and configuracao_preservada)
        resumo = {
            "codigo_saida": codigo, "duracao_s": round(time.monotonic() - inicio, 3),
            "coleta": "CONCLUIDA" if completo else "INCOMPLETA_OU_RED",
            "turnos_observados": len(conclusoes), "sem_comandos_observados": sem_comandos,
            "geracoes_http_locais": len(geracoes), "bloqueios": bloqueios,
            "configuracao_preservada": configuracao_preservada,
            "qualidade_semantica": "requer revisão das conclusões originais",
            "visao": "não aferida por esta sonda", "voz": "silenciada; audição não aferida",
            "isolamento_total_persistencia": False,
        }
        (pasta / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
        print("SONDA_QWEN3VL_RESULTADO:", json.dumps(resumo, ensure_ascii=False), flush=True)
    return codigo or (0 if completo else 1)


if __name__ == "__main__":
    raise SystemExit(main())
