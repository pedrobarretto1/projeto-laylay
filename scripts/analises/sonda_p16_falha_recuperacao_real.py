"""Falha controlada de escrita no Windows, pelo loop e executor reais.

Cria somente um arquivo descartável próprio. Um handle compartilhável para
leitura impede escrita; o bloqueio só é liberado depois de duas falhas com
receipts distintos e barreiras de processamento/voz concluídas. Nenhum receipt
ou estado emocional é injetado. Preserva arquivo, logs e prova ao terminar.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


RAIZ = Path(__file__).resolve().parents[2]
INICIAL = "P16 ANTES DO TESTE\n"
NOVO = "P16 RECUPERADA"


def _ler_json(caminho: Path) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _ler_planos(diretorio: Path) -> list[dict]:
    try:
        return [json.loads(linha) for linha in (diretorio / "planos.jsonl").read_text(
            encoding="utf-8",
        ).splitlines() if linha.strip()]
    except (OSError, ValueError):
        return []


def _receipt(plano: dict, alvo: Path, status: str) -> dict:
    comandos = plano.get("comandos") or []
    if len(comandos) != 1:
        raise AssertionError("Cada turno precisa produzir somente a escrita autorizada.")
    receipt = comandos[0]
    assert receipt.get("intent") == "CREATE_FILE", receipt.get("intent")
    assert receipt.get("origem") == "executor", "a prova precisa vir do executor"
    assert receipt.get("status") == status, receipt.get("status")
    assert os.path.normcase(os.path.abspath(str(receipt.get("alvo") or ""))) == os.path.normcase(str(alvo))
    assert isinstance(receipt.get("id_solicitacao"), str) and receipt["id_solicitacao"]
    sucesso = status == "conteudo_atualizado"
    assert receipt.get("executou") is sucesso and receipt.get("confirmado") is sucesso
    return receipt


def _estado_causal(plano: dict, receipt: dict, emocao: str) -> dict:
    estado = dict(plano.get("estado_emocional_observado") or {})
    assert estado.get("emocao") == emocao, estado
    assert estado.get("nivel") == 1, estado
    assert estado.get("episodio_origem") == "resultado_operacional", estado
    assert estado.get("episodio_evidencia_ref") == receipt["id_solicitacao"], estado
    return estado


def _interromper_sessao_criada(processo: subprocess.Popen, iniciado_em: float) -> None:
    if processo.poll() is not None:
        return
    import psutil

    try:
        pai = psutil.Process(processo.pid)
    except psutil.NoSuchProcess:
        processo.wait(timeout=5)
        return
    assert pai.create_time() >= iniciado_em - 1.0
    filhos = pai.children(recursive=True)
    encerrando = []
    for filho in reversed(filhos):
        try:
            if filho.create_time() >= iniciado_em - 1.0:
                filho.terminate()
                encerrando.append(filho)
        except psutil.NoSuchProcess:
            pass
    processo.terminate()
    _, vivos = psutil.wait_procs(encerrando + [pai], timeout=3)
    for vivo in vivos:
        try:
            assert vivo.create_time() >= iniciado_em - 1.0
            vivo.kill()
        except psutil.NoSuchProcess:
            pass
    _, vivos = psutil.wait_procs(vivos, timeout=3)
    assert not vivos, "A sessão criada precisa encerrar antes de liberar o bloqueio."
    processo.wait(timeout=5)


def main() -> int:
    if os.name != "nt":
        raise RuntimeError("Esta prova exige a contenção de arquivo real do Windows.")
    base = (RAIZ / "resultados_testes").resolve()
    identidade = uuid.uuid4().hex
    pasta = (base / ("p16_falha_recuperacao_" + identidade)).resolve()
    assert pasta.parent == base
    pasta.mkdir(parents=True, exist_ok=False)
    # Um alvo curto mantém a resposta operacional completa dentro da janela
    # de voz, sem alterar o compositor nem silenciar o controle.
    base_alvo = (Path.home() / "Downloads").resolve()
    pasta_alvo = (base_alvo / ("p16_" + identidade[:10])).resolve()
    assert pasta_alvo.parent == base_alvo
    pasta_alvo.mkdir(exist_ok=False)
    alvo = (pasta_alvo / "prova.txt").resolve()
    assert alvo.parent == pasta_alvo
    alvo.write_text(INICIAL, encoding="utf-8")
    comando = f"Escreva {NOVO} dentro do arquivo {alvo}"
    expectativas = {
        n: {
            "nome": f"escrita_real_{n}", "dominio": "arquivos",
            "intents_any": ("CREATE_FILE",), "alvos_any": (str(alvo),),
            "statuses_any": (("falha_execucao",) if n < 3 else ("conteudo_atualizado",)),
            "confirmado": n == 3,
        } for n in (1, 2, 3)
    }
    roteiro = pasta / "roteiro_falha_recuperacao.py"
    roteiro.write_text(
        f"COMANDOS = {repr((comando,) * 3)}\n"
        f"EXPECTATIVAS_SEMANTICAS = {repr(expectativas)}\n"
        "ATRASO_INICIAL_S = 4\nTIMEOUT_RESPOSTA_S = 45\nTIMEOUT_VOZ_S = 45\n"
        "SILENCIAR_VOZ_DURANTE_TESTE = False\nAGUARDAR_CONFIRMACAO_EXECUCAO = True\n"
        "INTERVALO_ENTRE_COMANDOS_S = 12\nPARAR_SEM_RESPOSTA = True\nENCERRAR_AO_FINAL = True\n",
        encoding="utf-8",
    )
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(alvo), 0x80000000, 1, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    processo = None
    liberado = False
    iniciado_em = time.time()
    prova = {"tipo": "falha_controlada_por_lock_real", "alvo": str(alvo),
             "status": "em_execucao"}
    print(f"P16_PROVA pasta={pasta}", flush=True)
    try:
        prova.update(
            head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
            hash_inicial=hashlib.sha256(alvo.read_bytes()).hexdigest(),
        )
        ambiente = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_MASCOT_ENABLED="1",
                        LAYLAY_AVATAR_ATIVO="1", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
                        PYTHONFAULTHANDLER="1")
        with (pasta / "processo.log").open("w", encoding="utf-8") as log:
            processo = subprocess.Popen(
                [sys.executable, "-u", str(RAIZ / "laylay.py"), "--roteiro", str(roteiro),
                 "--resultado-raiz", str(pasta / "runtime")],
                cwd=RAIZ, env=ambiente, stdout=log, stderr=subprocess.STDOUT,
            )
            prazo = time.monotonic() + 240
            diretorio = None
            while time.monotonic() < prazo and processo.poll() is None:
                candidatos = list((pasta / "runtime").glob("roteiro_falha_recuperacao-*"))
                if candidatos:
                    assert len(candidatos) == 1
                    diretorio = candidatos[0]
                    checkpoint = _ler_json(diretorio / "checkpoint.json")
                    itens = checkpoint.get("itens") or []
                    if itens and itens[0].get("status") == "respondido":
                        assert all(itens[0].get(k) is True for k in (
                            "processamento_concluido", "voz_concluida", "resultado_turno_concluido",
                        ))
                        planos = _ler_planos(diretorio)
                        primeira = _receipt(next(r["plano"] for r in planos if r["indice"] == 0),
                                            alvo, "falha_execucao")
                        assert alvo.read_text(encoding="utf-8") == INICIAL
                        prova["receipt_primeira_falha"] = primeira
                    if len(itens) >= 2 and itens[1].get("status") == "respondido":
                        assert all(itens[1].get(k) is True for k in (
                            "processamento_concluido", "voz_concluida", "resultado_turno_concluido",
                        ))
                        planos = _ler_planos(diretorio)
                        planos_falha = [next(r["plano"] for r in planos if r["indice"] == i) for i in (0, 1)]
                        falhas = [_receipt(plano, alvo, "falha_execucao") for plano in planos_falha]
                        assert falhas[0]["id_solicitacao"] != falhas[1]["id_solicitacao"]
                        assert alvo.read_text(encoding="utf-8") == INICIAL
                        prova.update(receipts_falha=falhas, hash_apos_falhas=hashlib.sha256(alvo.read_bytes()).hexdigest(),
                                     estados_falha=[p.get("estado_emocional_observado") for p in planos_falha])
                        _estado_causal(planos_falha[1], falhas[1], "irritada")
                        if not kernel.CloseHandle(handle):
                            raise ctypes.WinError(ctypes.get_last_error())
                        liberado = True
                        print("P16_PROVA duas falhas reais confirmadas; bloqueio liberado.", flush=True)
                        break
                time.sleep(0.1)
            assert liberado, "Duas falhas com barreiras concluídas são necessárias antes de liberar a escrita."
            assert diretorio is not None
            processo.wait(timeout=max(1.0, prazo - time.monotonic()))
            prova["codigo_saida"] = processo.returncode
            checkpoint = _ler_json(diretorio / "checkpoint.json")
            assert checkpoint.get("concluido") is True
            planos = _ler_planos(diretorio)
            recuperacao = next(r["plano"] for r in planos if r["indice"] == 2)
            receipt = _receipt(recuperacao, alvo, "conteudo_atualizado")
            assert receipt["id_solicitacao"] not in {r["id_solicitacao"] for r in prova["receipts_falha"]}
            assert alvo.read_text(encoding="utf-8") == NOVO
            prova.update(status="green_operacional", receipt_recuperacao=receipt,
                         hash_final=hashlib.sha256(alvo.read_bytes()).hexdigest(),
                         estado_recuperacao=recuperacao.get("estado_emocional_observado"),
                         diretorio_runtime=str(diretorio))
            _estado_causal(recuperacao, receipt, "acalmando-se")
            prova["contratos_operacional_emocional_confirmados"] = True
            assert processo.returncode == 0, processo.returncode
            prova["status"] = "green_operacional_e_emocional"
            print("P16_PROVA terceira escrita e conteúdo físico confirmados.", flush=True)
        return 0
    except Exception as erro:
        prova.update(status="red", erro=f"{type(erro).__name__}: {erro}")
        print(f"P16_PROVA RED {prova['erro']}", flush=True)
        raise
    finally:
        try:
            if processo is not None and processo.poll() is None:
                _interromper_sessao_criada(processo, iniciado_em)
            if not liberado:
                kernel.CloseHandle(handle)
        except Exception as erro:
            prova.update(status="red", erro_encerramento=f"{type(erro).__name__}: {erro}")
            raise
        finally:
            (pasta / "prova.json").write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
