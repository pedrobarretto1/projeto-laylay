#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C1-D — PÓS-PATCH STORE-ONLY FÍSICO — TESTE 4.3

Objetivo
========
Provar fisicamente o patch mínimo e ESTRITAMENTE escopado derivado do RED 4.1
e da falsificação 4.2:

    baseline:
        fechar_programa(mapped)

    patch final esperado:
        fechar_programa(nome if nome_norm == "microsoft store" else mapped)

O patch preserva o comportamento legado de todos os demais apps locais e do
PC B; somente o alvo semântico exato "microsoft store" deixa de receber o
open_locator "ms-windows-store:" e chega intacto ao fechador físico.

Este teste NÃO fecha C1-D end-to-end sozinho. Ele prova o executor físico
Store-only pós-patch. O fechamento soberano de C1-D ainda exige regressivos
e o corredor/chaos real 154→159.

Contrato de saída
=================
0 = patch exato presente + Store abriu + CLOSE_APP real fechou fisicamente
    WinStore.App.exe + janela desapareceu + resultado app_fechado.
1 = harness/baseline/worktree/ambiente inconclusivo ou divergente.
2 = patch exato presente, abertura comprovada, mas fechamento físico ficou RED.

IMPORTANTE
==========
- Ações físicas: SIM. A Microsoft Store será aberta e, no GREEN, fechada.
- Nenhum arquivo é alterado por este harness.
- Nenhum git add/commit/push.
- Se o fechamento ficar RED, não há cleanup alternativo: a Store fica aberta
  como evidência e deve ser fechada manualmente depois.
"""

from __future__ import annotations

import ast
import contextlib
import ctypes
import io
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable


EXPECTED_HEAD = "47b7f0c98efafd73e8034c2e11654b73f3d9831b"
STORE_NAME = "microsoft store"
EXPECTED_OPEN_LOCATOR = "ms-windows-store:"
TARGET = "mente_laylay/autonomia/executor_janelas.py"
TARGET_HEAD_BLOB = "5425b2368fc64a36f86f48c597282e4308db4d8e"

BASELINE_CALL = '            fechar_programa(mapped)'
BROAD_CALL = '            fechar_programa(nome)'
PATCHED_CALL = (
    '            fechar_programa('
    'nome if nome_norm == "microsoft store" else mapped)'
)

EXIT_GREEN = 0
EXIT_INCONCLUSIVE = 1
EXIT_PHYSICAL_RED = 2

EXPECTED_OTHER_BLOBS = {
    "laylay.py": "999dc75688b1828710a203edae2db07483435511",
    "mente_laylay/autonomia/habilidade_janelas.py": "b66b8a0906346641928534fd66db2b83c8a74c76",
    "mente_laylay/autonomia/comandos_sistema.py": "7b6761299cc8faf616fadcf7240664aa5b64337f",
    "mente_laylay/autonomia/contrato_executor.py": "a7030bb04b6133632bf880ac5e0503f8ef14ea3b",
    "mente_laylay/autonomia/executor_comum.py": "6f13314bf81b24bb7b14ffa74ce1cbd612b70d94",
    "mente_laylay/percepcao/janelas_sistema.py": "ef11b62ed0404a321b86e0530957b377aff07189",
    "mente_laylay/percepcao/planejamento_janelas.py": "f5ac832850c61e2f9d6539cafb410e63be29269f",
}


class HarnessInconclusivo(RuntimeError):
    pass


class PatchPhysicalRed(RuntimeError):
    pass


def _print_status(nome: str, estado: str, detalhe: str = "") -> None:
    largura = 76
    base = f"{nome}."
    pontos = "." * max(1, largura - len(base))
    linha = f"{base}{pontos} {estado}"
    if detalhe:
        linha += f" | {detalhe}"
    print(linha)


def _run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise HarnessInconclusivo(
            f"git {' '.join(args)} falhou ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _run_git_bytes(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        erro = proc.stderr.decode("utf-8", errors="replace").strip()
        raise HarnessInconclusivo(
            f"git {' '.join(args)} falhou ({proc.returncode}): {erro}"
        )
    return bytes(proc.stdout)


def _normalizar_fonte(texto: str) -> str:
    return str(texto).replace("\r\n", "\n").replace("\r", "\n")


def _descobrir_repo() -> Path:
    aqui = Path(__file__).resolve().parent
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=aqui,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise HarnessInconclusivo(
            "execute este arquivo de dentro do repositório projeto-laylay"
        )
    return Path(proc.stdout.strip()).resolve()


def _auditar_patch_exato(repo: Path) -> str:
    head = _run_git(repo, "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise HarnessInconclusivo(
            f"HEAD divergente: esperado {EXPECTED_HEAD}, observado {head}"
        )

    blob_head = _run_git(repo, "rev-parse", f"{EXPECTED_HEAD}:{TARGET}")
    if blob_head != TARGET_HEAD_BLOB:
        raise HarnessInconclusivo(
            f"blob HEAD do executor divergente: {blob_head} != {TARGET_HEAD_BLOB}"
        )

    staged = [
        linha.strip()
        for linha in _run_git(repo, "diff", "--cached", "--name-only").splitlines()
        if linha.strip()
    ]
    if staged:
        raise HarnessInconclusivo(
            f"há mudanças staged; este teste exige index limpo: {staged!r}"
        )

    alterados = [
        linha.strip().replace("\\", "/")
        for linha in _run_git(repo, "diff", "--name-only").splitlines()
        if linha.strip()
    ]
    if alterados != [TARGET]:
        raise HarnessInconclusivo(
            "mudanças tracked devem conter SOMENTE executor_janelas.py; "
            f"observado={alterados!r}"
        )

    baseline = _normalizar_fonte(
        _run_git_bytes(repo, "show", f"{EXPECTED_HEAD}:{TARGET}")
        .decode("utf-8-sig", errors="strict")
    )
    atual = _normalizar_fonte(
        (repo / TARGET).read_text(encoding="utf-8-sig")
    )

    if baseline.count(BASELINE_CALL) != 1:
        raise HarnessInconclusivo(
            "baseline não contém exatamente uma chamada fechar_programa(mapped)"
        )

    esperado = baseline.replace(BASELINE_CALL, PATCHED_CALL, 1)
    if atual != esperado:
        if BROAD_CALL in atual:
            raise HarnessInconclusivo(
                "patch amplo fechar_programa(nome) ainda está presente; "
                "aplique primeiro o ajuste de escopo mínimo"
            )
        raise HarnessInconclusivo(
            "working tree não corresponde ao patch Store-only exato"
        )

    diff = _run_git(repo, "diff", "--", TARGET)
    removidas = [
        l for l in diff.splitlines()
        if l.startswith("-") and not l.startswith("---")
    ]
    adicionadas = [
        l for l in diff.splitlines()
        if l.startswith("+") and not l.startswith("+++")
    ]
    if removidas != ["-" + BASELINE_CALL] or adicionadas != ["+" + PATCHED_CALL]:
        raise HarnessInconclusivo(
            "diff textual não é exatamente 1 remoção + 1 adição causal; "
            f"removidas={removidas!r} adicionadas={adicionadas!r}"
        )

    # Controle lateral estrutural: o ramo remoto continua usando mapped e o
    # fallback local para qualquer alvo diferente de Microsoft Store também.
    if 'enviar_pc_b({"action": "close_app", "app": mapped})' not in atual:
        raise HarnessInconclusivo("contrato PC B com mapped foi alterado")
    if "else mapped)" not in PATCHED_CALL:
        raise HarnessInconclusivo("patch não preserva mapped para os demais apps")

    blob_worktree = _run_git(
        repo, "hash-object", "--filters", f"--path={TARGET}", TARGET
    )
    return blob_worktree


def _auditar_outros_blobs(repo: Path) -> None:
    for rel, esperado in EXPECTED_OTHER_BLOBS.items():
        caminho = repo / rel
        if not caminho.is_file():
            raise HarnessInconclusivo(f"fonte causal ausente: {rel}")

        blob_head = _run_git(repo, "rev-parse", f"{EXPECTED_HEAD}:{rel}")
        if blob_head != esperado:
            raise HarnessInconclusivo(
                f"blob congelado divergente em {rel}: {blob_head} != {esperado}"
            )

        blob_worktree = _run_git(
            repo, "hash-object", "--filters", f"--path={rel}", rel
        )
        if blob_worktree != esperado:
            raise HarnessInconclusivo(
                f"worktree causal lateral alterada em {rel}: {blob_worktree} != {esperado}"
            )


def _extrair_literal(path: Path, nome: str) -> Any:
    try:
        arvore = ast.parse(
            path.read_text(encoding="utf-8-sig"),
            filename=str(path),
        )
    except Exception as exc:
        raise HarnessInconclusivo(
            f"não consegui parsear {path.name}: {exc}"
        ) from exc

    for no in arvore.body:
        if isinstance(no, ast.Assign):
            if any(
                isinstance(alvo, ast.Name) and alvo.id == nome
                for alvo in no.targets
            ):
                try:
                    return ast.literal_eval(no.value)
                except Exception as exc:
                    raise HarnessInconclusivo(
                        f"{nome} existe, mas não é literal seguro: {exc}"
                    ) from exc
        if (
            isinstance(no, ast.AnnAssign)
            and isinstance(no.target, ast.Name)
            and no.target.id == nome
        ):
            try:
                return ast.literal_eval(no.value)
            except Exception as exc:
                raise HarnessInconclusivo(
                    f"{nome} existe, mas não é literal seguro: {exc}"
                ) from exc

    raise HarnessInconclusivo(
        f"atribuição {nome} não encontrada em {path.name}"
    )


def _hwnd_da_janela(janela: Any) -> int:
    for atributo in ("_hWnd", "hWnd", "handle"):
        try:
            valor = getattr(janela, atributo, None)
            if valor is not None and int(valor):
                return int(valor)
        except Exception:
            continue
    return 0


def _pid_por_hwnd(hwnd: int) -> int:
    if not hwnd:
        return 0
    try:
        pid = ctypes.c_ulong(0)
        ctypes.windll.user32.GetWindowThreadProcessId(
            ctypes.c_void_p(hwnd), ctypes.byref(pid)
        )
        return int(pid.value or 0)
    except Exception:
        return 0


def _esperar(
    condicao: Callable[[], bool],
    timeout_s: float,
    intervalo_s: float = 0.25,
) -> bool:
    limite = time.monotonic() + max(0.1, float(timeout_s))
    while time.monotonic() < limite:
        try:
            if condicao():
                return True
        except Exception:
            pass
        time.sleep(max(0.05, float(intervalo_s)))
    try:
        return bool(condicao())
    except Exception:
        return False


def main() -> int:
    print("C1-D — PÓS-PATCH STORE-ONLY FÍSICO — TESTE 4.3")
    print("=" * 116)
    print(f"HEAD congelado: {EXPECTED_HEAD}")
    print("patch esperado: Store-only / demais apps preservam mapped")
    print("ações físicas: SIM — APP_OPEN real + CLOSE_APP real")
    print("Git mutation: NÃO")
    print("exit 0 = GREEN físico Store-only pós-patch")
    print("exit 1 = inconclusivo/divergente/harness")
    print("exit 2 = patch presente, mas fechamento físico RED")
    print()

    repo: Path | None = None
    status_before: str | None = None
    abertura_comprovada = False

    try:
        if os.name != "nt":
            raise HarnessInconclusivo("este teste físico exige Windows")

        repo = _descobrir_repo()
        os.chdir(repo)
        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))

        status_before = _run_git(
            repo, "status", "--porcelain=v1", "--untracked-files=no"
        )

        blob_patch = _auditar_patch_exato(repo)
        _auditar_outros_blobs(repo)
        _print_status(
            "A HEAD + patch Store-only exato",
            "PASS",
            f"baseline={TARGET_HEAD_BLOB[:12]}; worktree={blob_patch[:12]}",
        )
        _print_status(
            "B escopo lateral do patch",
            "PASS",
            "PC B usa mapped; apps != microsoft store continuam usando mapped",
        )

        apps_map = _extrair_literal(repo / "laylay.py", "APPS_MAP")
        if not isinstance(apps_map, dict):
            raise HarnessInconclusivo("APPS_MAP não é dict")

        open_locator = str(apps_map.get(STORE_NAME) or "").strip()
        if open_locator != EXPECTED_OPEN_LOCATOR:
            raise HarnessInconclusivo(
                f"APPS_MAP Store divergente: {open_locator!r}"
            )
        _print_status(
            "C identidade de abertura preservada",
            "PASS",
            f"{STORE_NAME} -> {open_locator}",
        )

        try:
            import psutil
            import pygetwindow as gw
            from mente_laylay.autonomia.comandos_sistema import (
                _NOMES_CANONICOS_FECHAMENTO,
                abrir_programa,
                fechar_programa,
            )
            from mente_laylay.autonomia.executor_janelas import (
                DependenciasExecutorJanelas,
                executar_intencao_janelas,
            )
            from mente_laylay.percepcao.janelas_sistema import (
                buscar_janela,
                janela_esta_em_foco,
                listar_programas_abertos,
                resolver_alvo_ambiente,
            )
        except Exception as exc:
            raise HarnessInconclusivo(
                "dependência/runtime de produção indisponível: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        canonicos = tuple(
            str(item or "").casefold().strip()
            for item in (
                _NOMES_CANONICOS_FECHAMENTO.get(STORE_NAME) or ()
            )
            if str(item or "").strip()
        )
        if "winstore.app.exe" not in set(canonicos):
            raise HarnessInconclusivo(
                f"mapa canônico Store divergente: {canonicos!r}"
            )
        _print_status(
            "D identidade física canônica",
            "PASS",
            f"{STORE_NAME} -> {', '.join(canonicos)}",
        )

        def janela_store():
            janela, _ = buscar_janela(gw, STORE_NAME)
            return janela

        def store_visivel() -> bool:
            return janela_store() is not None

        def resolver_local(nome: str) -> dict[str, Any]:
            programas = listar_programas_abertos(gw, psutil)
            return resolver_alvo_ambiente(
                nome,
                programas,
                (),
                lambda alvo: janela_esta_em_foco(gw, alvo),
            )

        def observar_store() -> dict[str, Any]:
            janela = janela_store()
            titulo = ""
            hwnd = 0
            pid = 0
            proc_name = ""

            if janela is not None:
                try:
                    titulo = str(
                        getattr(janela, "title", "") or ""
                    ).strip()
                except Exception:
                    pass
                hwnd = _hwnd_da_janela(janela)
                pid = _pid_por_hwnd(hwnd)
                if pid:
                    try:
                        proc_name = str(
                            psutil.Process(pid).name() or ""
                        ).strip()
                    except Exception:
                        pass

            canonical_live: list[dict[str, Any]] = []
            canonicos_set = set(canonicos)
            try:
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        nome_proc = str(
                            proc.info.get("name") or ""
                        ).strip()
                        if nome_proc.casefold().strip() not in canonicos_set:
                            continue
                        canonical_live.append(
                            {
                                "pid": int(
                                    proc.info.get("pid") or 0
                                ),
                                "name": nome_proc,
                            }
                        )
                    except Exception:
                        continue
            except Exception:
                pass

            return {
                "visivel": janela is not None,
                "titulo": titulo,
                "hwnd": hwnd,
                "pid": pid,
                "process_name": proc_name,
                "canonical_live": canonical_live,
            }

        def esperar_store_aberta(
            timeout: float = 15.0,
        ) -> dict[str, Any]:
            if not _esperar(store_visivel, timeout, 0.25):
                raise HarnessInconclusivo(
                    "Microsoft Store não apareceu fisicamente"
                )
            obs = observar_store()
            if not obs.get("visivel"):
                raise HarnessInconclusivo(
                    "Store apareceu e sumiu antes da observação"
                )
            if not obs.get("canonical_live"):
                raise HarnessInconclusivo(
                    "janela Store abriu, mas WinStore.App.exe "
                    "não ficou observável"
                )
            return obs

        def pids_ainda_vivos(pids: set[int]) -> set[int]:
            vivos: set[int] = set()
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    if (
                        proc.is_running()
                        and proc.status() != psutil.STATUS_ZOMBIE
                    ):
                        vivos.add(pid)
                except (
                    psutil.NoSuchProcess,
                    psutil.ZombieProcess,
                ):
                    continue
                except Exception:
                    vivos.add(pid)
            return vivos

        def esperar_pids_morrerem(
            pids: set[int],
            timeout: float = 6.0,
        ) -> bool:
            return _esperar(
                lambda: not pids_ainda_vivos(pids),
                timeout,
                0.20,
            )

        def processos_encerrados_no_trace(
            texto: str,
        ) -> list[str]:
            nomes: list[str] = []
            for linha in str(texto or "").splitlines():
                if (
                    "[FECHAR_PROGRAMA] processo exato encerrado"
                    not in linha
                ):
                    continue
                marcador = "processo="
                if marcador not in linha:
                    continue
                resto = linha.split(marcador, 1)[1].strip()
                if not resto:
                    continue
                if resto[0] in {"'", '"'}:
                    aspas = resto[0]
                    fim = resto.find(aspas, 1)
                    valor = (
                        resto[1:fim]
                        if fim > 0
                        else resto[1:]
                    )
                else:
                    valor = resto.split()[0]
                if valor:
                    nomes.append(valor.casefold().strip())
            return nomes

        resultados: list[dict[str, Any]] = []
        open_inputs: list[str] = []
        close_inputs: list[str] = []
        close_errors: list[str] = []

        def marcar_resultado(
            status: str,
            **kwargs: Any,
        ) -> None:
            resultados.append(
                {"status": str(status or ""), **kwargs}
            )

        def falar_noop(
            *_args: Any,
            **_kwargs: Any,
        ) -> None:
            return None

        def abrir_instrumentado(
            alvo: str,
            *args: Any,
            **kwargs: Any,
        ) -> bool:
            open_inputs.append(str(alvo or ""))
            return bool(
                abrir_programa(alvo, *args, **kwargs)
            )

        def fechar_instrumentado(
            alvo: str,
            *args: Any,
            **kwargs: Any,
        ) -> bool:
            close_inputs.append(str(alvo or ""))
            try:
                return bool(
                    fechar_programa(alvo, *args, **kwargs)
                )
            except Exception as exc:
                close_errors.append(
                    f"{type(exc).__name__}: {exc}"
                )
                raise

        def esperar_programa_fechar(nome: str) -> bool:
            return _esperar(
                lambda: buscar_janela(gw, nome)[0] is None,
                6.0,
                0.20,
            )

        deps = DependenciasExecutorJanelas(
            marcar_resultado=marcar_resultado,
            falar_por_status=falar_noop,
            falar_resultado_janela=falar_noop,
            esperar_programa_fechar=esperar_programa_fechar,
        )
        ctx = {
            "APPS_MAP": apps_map,
            "abrir_programa": abrir_instrumentado,
            "fechar_programa": fechar_instrumentado,
            "_resolver_alvo_ambiente": resolver_local,
            "_eh_alvo_site_web": lambda _texto: False,
            "_contexto_aponta_site_web": lambda _texto="": False,
            "_registro_navegador_operacoes_runtime": None,
            "falar_com_lipsync": None,
        }

        if store_visivel():
            obs_pre = observar_store()
            raise HarnessInconclusivo(
                "Microsoft Store já estava visível. "
                "Feche-a manualmente antes de rodar. "
                f"obs={obs_pre!r}"
            )
        _print_status(
            "E precondição Store fechada",
            "PASS",
            "nenhuma janela Store visível",
        )

        resultados.clear()
        retorno_open = executar_intencao_janelas(
            "APP_OPEN",
            {"nome_app": STORE_NAME},
            "pc_a",
            ctx,
            deps,
            texto_original="abre a microsoft store",
        )
        if not getattr(retorno_open, "tratado", True):
            raise HarnessInconclusivo(
                "executor não tratou APP_OPEN"
            )
        resultado_open = resultados[-1] if resultados else {}
        if open_inputs != [EXPECTED_OPEN_LOCATOR]:
            raise HarnessInconclusivo(
                "APP_OPEN deixou de entregar URI congelado: "
                f"{open_inputs!r}"
            )
        if (
            str(resultado_open.get("status") or "")
            != "protocolo_aberto"
            or resultado_open.get("executou") is not True
        ):
            raise HarnessInconclusivo(
                f"APP_OPEN divergente: {resultado_open!r}"
            )

        obs_aberta = esperar_store_aberta()
        abertura_comprovada = True
        pids_antes = {
            int(item.get("pid") or 0)
            for item in obs_aberta.get("canonical_live") or []
            if int(item.get("pid") or 0)
        }
        _print_status(
            "F APP_OPEN real + Store observada",
            "PASS",
            f"entrada={open_inputs[0]!r}; "
            f"título={obs_aberta.get('titulo')!r}; "
            f"host={obs_aberta.get('process_name') or '?'}; "
            "canônico="
            + ", ".join(
                f"{x.get('name')}#{x.get('pid')}"
                for x in obs_aberta.get(
                    "canonical_live"
                ) or []
            ),
        )

        resultados.clear()
        close_trace = io.StringIO()
        with contextlib.redirect_stdout(close_trace):
            retorno_close = executar_intencao_janelas(
                "CLOSE_APP",
                {
                    "nome_app": STORE_NAME,
                    "alvo_tipado": "app",
                },
                "pc_a",
                ctx,
                deps,
                texto_original="fecha a microsoft store",
            )
        close_texto = close_trace.getvalue()

        print("\n--- TRACE REAL DO CLOSE_APP PÓS-PATCH ---")
        print(
            close_texto.rstrip()
            or "(sem saída do executor)"
        )
        print("--- FIM TRACE REAL DO CLOSE_APP PÓS-PATCH ---\n")

        if not getattr(retorno_close, "tratado", True):
            raise PatchPhysicalRed(
                "executor não tratou CLOSE_APP"
            )

        if close_inputs != [STORE_NAME]:
            raise PatchPhysicalRed(
                "fronteira de identidade ainda incorreta: "
                f"fechar_programa recebeu {close_inputs!r}, "
                f"esperado [{STORE_NAME!r}]"
            )
        _print_status(
            "G CLOSE_APP entrada física",
            "GREEN",
            f"fechar_programa recebeu {STORE_NAME!r}",
        )

        if close_errors:
            raise PatchPhysicalRed(
                "fechador físico lançou erro: "
                f"{close_errors!r}"
            )

        kills = processos_encerrados_no_trace(
            close_texto
        )
        if not kills:
            raise PatchPhysicalRed(
                "nenhum processo exato foi encerrado"
            )
        if any(
            nome not in set(canonicos)
            for nome in kills
        ):
            raise PatchPhysicalRed(
                "processo fora do mapa canônico foi encerrado: "
                f"{kills!r}"
            )
        if not set(kills).intersection(canonicos):
            raise PatchPhysicalRed(
                "WinStore.App.exe não foi encerrado: "
                f"{kills!r}"
            )
        _print_status(
            "H matcher físico canônico",
            "GREEN",
            f"kills={kills!r}",
        )

        if not _esperar(
            lambda: not store_visivel(),
            6.0,
            0.20,
        ):
            raise PatchPhysicalRed(
                "Store continuou visível após CLOSE_APP"
            )
        if not esperar_pids_morrerem(
            pids_antes, 6.0
        ):
            raise PatchPhysicalRed(
                "PID(s) canônico(s) pré-close "
                "continuam vivos: "
                f"{sorted(pids_antes)!r}"
            )
        _print_status(
            "I confirmação física pós-close",
            "GREEN",
            "janela Store desapareceu e PID(s) "
            f"{sorted(pids_antes)} morreram",
        )

        resultado_close = (
            resultados[-1] if resultados else {}
        )
        if (
            str(resultado_close.get("status") or "")
            != "app_fechado"
        ):
            raise PatchPhysicalRed(
                "executor não publicou app_fechado: "
                f"{resultado_close!r}"
            )
        if resultado_close.get("executou") is not True:
            raise PatchPhysicalRed(
                "executor não marcou executou=True: "
                f"{resultado_close!r}"
            )
        if resultado_close.get("confirmado") is False:
            raise PatchPhysicalRed(
                "executor publicou confirmado=False: "
                f"{resultado_close!r}"
            )
        _print_status(
            "J resultado do executor",
            "GREEN",
            f"{resultado_close!r}",
        )

        status_after = _run_git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=no",
        )
        if status_after != status_before:
            raise HarnessInconclusivo(
                "working tree/index tracked mudaram "
                "durante o teste"
            )

        blob_after = _auditar_patch_exato(repo)
        _auditar_outros_blobs(repo)
        if blob_after != blob_patch:
            raise HarnessInconclusivo(
                "blob do patch mudou durante o teste"
            )
        _print_status(
            "Z HEAD/index/working tree preservados",
            "PASS",
            "patch exato permaneceu; nenhuma mutação Git",
        )

        print("\n" + "=" * 116)
        print("✅ PATCH MÍNIMO STORE-ONLY — GREEN FÍSICO")
        print(
            "   HEAD ........................................... "
            "4.0 congelado / preservado"
        )
        print(
            "   produção alterada .............................. "
            "1 linha / Store-only"
        )
        print(
            "   APP_OPEN ....................................... "
            "GREEN / ms-windows-store:"
        )
        print(
            "   CLOSE_APP entrada .............................. "
            "GREEN / microsoft store"
        )
        print(
            "   processo encerrado ............................. "
            "WinStore.App.exe"
        )
        print(
            "   Store após fechamento ......................... "
            "FECHADA"
        )
        print(
            "   demais apps locais ............................. "
            "mapped preservado"
        )
        print(
            "   PC B ........................................... "
            "mapped preservado"
        )
        print(
            "   C1-D Store físico .............................. "
            "GREEN STORE-ONLY"
        )
        print(
            "   C1-D CLOSED .................................... "
            "AINDA NÃO — falta corredor/chaos soberano"
        )
        print(
            "   exit code 0 = GREEN físico pós-patch"
        )
        return EXIT_GREEN

    except PatchPhysicalRed as exc:
        print("\n" + "=" * 116)
        print("🔴 PATCH PRESENTE, MAS STORE-ONLY FICOU RED")
        print(f"   primeira evidência: {exc}")
        print(
            "   NÃO fazer cleanup alternativo pelo harness."
        )
        print(
            "   Se a Store estiver aberta, feche-a "
            "manualmente após registrar o resultado."
        )
        if repo is not None:
            try:
                _auditar_patch_exato(repo)
                _auditar_outros_blobs(repo)
                _print_status(
                    "Z patch/Git após RED",
                    "PASS",
                    "patch exato preservado",
                )
            except Exception as git_exc:
                _print_status(
                    "Z patch/Git após RED",
                    "ALERTA",
                    str(git_exc),
                )
        return EXIT_PHYSICAL_RED

    except HarnessInconclusivo as exc:
        print("\n" + "=" * 116)
        print("❌ PÓS-PATCH INCONCLUSIVO / DIVERGENTE")
        print(f"   motivo: {exc}")
        print(
            "   Não classificar como RED de produção "
            "sem uma fronteira física válida."
        )
        if abertura_comprovada:
            print(
                "   ⚠️ A Store chegou a ser aberta. "
                "Se ainda estiver visível, feche-a manualmente."
            )
        return EXIT_INCONCLUSIVE

    except Exception as exc:
        print("\n" + "=" * 116)
        print("❌ HARNESS QUEBROU")
        print(f"   {type(exc).__name__}: {exc}")
        print(
            "   Classificar como INCONCLUSIVO; "
            "não inferir regressão de produção."
        )
        return EXIT_INCONCLUSIVE


if __name__ == "__main__":
    raise SystemExit(main())
