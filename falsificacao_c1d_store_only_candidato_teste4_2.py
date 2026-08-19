#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C1-D — FALSIFICAÇÃO STORE-ONLY DO CANDIDATO — TESTE 4.2

Objetivo
=======
Falsificar o candidato causal levantado pelo RED 4.1 sem alterar produção:
``_executar_fechar_app`` reutiliza o localizador de abertura de ``APPS_MAP``
(``ms-windows-store:``) como identidade de fechamento, embora o fechador físico
já conheça ``microsoft store -> winstore.app.exe``.

Este NÃO é um patch, NÃO testa detector semântico e NÃO reabre C1-B2/C1-C ou
C1-D referencial. O alvo entra tipado como app e semanticamente correto.

Experimento
===========
1. APP_OPEN real abre a Store pelo URI congelado.
2. CONTROLE NEGATIVO: ``fechar_programa("ms-windows-store:")`` deve falhar e
   a Store deve continuar aberta.
3. CONTROLE POSITIVO: ``fechar_programa("microsoft store")`` deve encontrar o
   processo canônico real e fechar fisicamente a Store.
4. A Store é reaberta pelo APP_OPEN real.
5. CONTRAFACTUAL DO EXECUTOR: o executor real recebe um APPS_MAP efêmero que
   difere da produção em UMA chave: ``microsoft store -> microsoft store``.
   Assim testamos somente a hipótese "preservar o nome semântico até o
   fechador" sem modificar nenhum arquivo de produção.

A cola do harness só observa, registra e injeta esse mapa contrafactual local.

Contrato do experimento
======================
2 = os três controles causais bateram e o candidato SOBREVIVEU à falsificação.
1 = inconclusivo/divergente ou hipótese concorrente encontrada.
0 = NÃO EXISTE neste experimento.

IMPORTANTE
==========
- O teste abre e FECHA a Microsoft Store fisicamente.
- O fechamento positivo usa o fechador real seguro da Laylay.
- O teste não altera arquivos de produção nem o Git.
- Ao final esperado, a Store fica fechada.
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
EXIT_INCONCLUSIVE = 1
EXIT_CANDIDATE_SURVIVES = 2

EXPECTED_SOURCE_BLOBS = {
    "laylay.py": "999dc75688b1828710a203edae2db07483435511",
    "mente_laylay/autonomia/executor_janelas.py": "5425b2368fc64a36f86f48c597282e4308db4d8e",
    "mente_laylay/autonomia/habilidade_janelas.py": "b66b8a0906346641928534fd66db2b83c8a74c76",
    "mente_laylay/autonomia/comandos_sistema.py": "7b6761299cc8faf616fadcf7240664aa5b64337f",
    "mente_laylay/autonomia/contrato_executor.py": "a7030bb04b6133632bf880ac5e0503f8ef14ea3b",
    "mente_laylay/autonomia/executor_comum.py": "6f13314bf81b24bb7b14ffa74ce1cbd612b70d94",
    "mente_laylay/percepcao/janelas_sistema.py": "ef11b62ed0404a321b86e0530957b377aff07189",
    "mente_laylay/percepcao/planejamento_janelas.py": "f5ac832850c61e2f9d6539cafb410e63be29269f",
}


class HarnessInconclusivo(RuntimeError):
    pass


def _print_status(nome: str, estado: str, detalhe: str = "") -> None:
    largura = 74
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


def _auditar_head_e_blobs(repo: Path) -> None:
    head = _run_git(repo, "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise HarnessInconclusivo(
            f"HEAD divergente: esperado {EXPECTED_HEAD}, observado {head}"
        )

    for rel, esperado in EXPECTED_SOURCE_BLOBS.items():
        caminho = repo / rel
        if not caminho.is_file():
            raise HarnessInconclusivo(f"fonte causal ausente: {rel}")

        blob_head = _run_git(repo, "rev-parse", f"{EXPECTED_HEAD}:{rel}")
        if blob_head != esperado:
            raise HarnessInconclusivo(
                f"blob congelado divergente em {rel}: {blob_head} != {esperado}"
            )

        blob_worktree = _run_git(
            repo,
            "hash-object",
            "--filters",
            f"--path={rel}",
            rel,
        )
        if blob_worktree != esperado:
            raise HarnessInconclusivo(
                f"worktree causal adulterada em {rel}: {blob_worktree} != {esperado}"
            )


def _extrair_literal(path: Path, nome: str) -> Any:
    try:
        arvore = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except Exception as exc:
        raise HarnessInconclusivo(f"não consegui parsear {path.name}: {exc}") from exc

    for no in arvore.body:
        if isinstance(no, ast.Assign):
            if any(isinstance(alvo, ast.Name) and alvo.id == nome for alvo in no.targets):
                try:
                    return ast.literal_eval(no.value)
                except Exception as exc:
                    raise HarnessInconclusivo(
                        f"{nome} existe, mas não é literal seguro para o harness: {exc}"
                    ) from exc
        if isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name) and no.target.id == nome:
            try:
                return ast.literal_eval(no.value)
            except Exception as exc:
                raise HarnessInconclusivo(
                    f"{nome} existe, mas não é literal seguro para o harness: {exc}"
                ) from exc
    raise HarnessInconclusivo(f"atribuição {nome} não encontrada em {path.name}")


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
        ctypes.windll.user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(pid))
        return int(pid.value or 0)
    except Exception:
        return 0


def _esperar(condicao: Callable[[], bool], timeout_s: float, intervalo_s: float = 0.25) -> bool:
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
    print("C1-D — FALSIFICAÇÃO STORE-ONLY DO CANDIDATO — TESTE 4.2")
    print("=" * 112)
    print(f"HEAD travado: {EXPECTED_HEAD}")
    print("alvo semântico: microsoft store")
    print("ações físicas: SIM — abre e fecha a Store em controles reais")
    print("produção: NÃO ALTERADA")
    print("exit 2 = candidato causal sobreviveu à falsificação")
    print("exit 1 = inconclusivo/divergente/hipótese concorrente")
    print("exit 0 = NÃO EXISTE neste experimento")
    print()

    repo: Path | None = None
    status_before: str | None = None

    try:
        if os.name != "nt":
            raise HarnessInconclusivo("este experimento físico exige Windows")

        repo = _descobrir_repo()
        os.chdir(repo)
        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        status_before = _run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")

        _auditar_head_e_blobs(repo)
        _print_status("A HEAD + blobs causais", "PASS", "baseline 4.0 exata")

        apps_map = _extrair_literal(repo / "laylay.py", "APPS_MAP")
        if not isinstance(apps_map, dict):
            raise HarnessInconclusivo("APPS_MAP não é dict")
        open_locator = str(apps_map.get(STORE_NAME) or "").strip()
        if open_locator != EXPECTED_OPEN_LOCATOR:
            raise HarnessInconclusivo(
                f"APPS_MAP Store divergente: {open_locator!r} != {EXPECTED_OPEN_LOCATOR!r}"
            )
        _print_status(
            "B identidade de abertura congelada", "PASS",
            f"{STORE_NAME} -> {open_locator}",
        )

        try:
            import psutil
            import pygetwindow as gw
            from mente_laylay.autonomia.comandos_sistema import (
                _NOMES_CANONICOS_FECHAMENTO,
                abrir_programa,
                fechar_programa,
                normalizar_nome_app,
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
                f"dependência/runtime de produção indisponível: {type(exc).__name__}: {exc}"
            ) from exc

        canonicos = tuple(
            str(item or "").casefold().strip()
            for item in (_NOMES_CANONICOS_FECHAMENTO.get(STORE_NAME) or ())
            if str(item or "").strip()
        )
        if not canonicos:
            raise HarnessInconclusivo("mapa canônico não possui microsoft store")
        _print_status(
            "C identidade canônica de fechamento", "PASS",
            f"{STORE_NAME} -> {', '.join(canonicos)}",
        )

        base_uri_close = str(normalizar_nome_app(open_locator) or "").casefold().strip()
        permitidos_uri = {base_uri_close}
        if base_uri_close and not base_uri_close.endswith(".exe"):
            permitidos_uri.add(base_uri_close + ".exe")
        permitidos_uri.discard("")
        if set(canonicos).intersection(permitidos_uri):
            raise HarnessInconclusivo("URI e identidade canônica deixaram de ser disjuntos")
        _print_status(
            "C2 domínios de identidade são disjuntos", "PASS",
            f"URI={sorted(permitidos_uri)!r}; canônico={list(canonicos)!r}",
        )

        def janela_store():
            janela, _ = buscar_janela(gw, STORE_NAME)
            return janela

        def store_visivel() -> bool:
            return janela_store() is not None

        def resolver_local(nome: str) -> dict[str, Any]:
            programas = listar_programas_abertos(gw, psutil)
            return resolver_alvo_ambiente(
                nome, programas, (), lambda alvo: janela_esta_em_foco(gw, alvo)
            )

        def observar_store() -> dict[str, Any]:
            janela = janela_store()
            titulo = ""
            hwnd = 0
            pid = 0
            proc_name = ""
            if janela is not None:
                try:
                    titulo = str(getattr(janela, "title", "") or "").strip()
                except Exception:
                    pass
                hwnd = _hwnd_da_janela(janela)
                pid = _pid_por_hwnd(hwnd)
                if pid:
                    try:
                        proc_name = str(psutil.Process(pid).name() or "").strip()
                    except Exception:
                        pass

            canonicos_set = set(canonicos)
            canonical_live: list[dict[str, Any]] = []
            try:
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        nome_proc = str(proc.info.get("name") or "").strip()
                        if nome_proc.casefold().strip() not in canonicos_set:
                            continue
                        canonical_live.append({
                            "pid": int(proc.info.get("pid") or 0),
                            "name": nome_proc,
                        })
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

        def esperar_store_aberta(timeout: float = 15.0) -> dict[str, Any]:
            if not _esperar(store_visivel, timeout, 0.25):
                raise HarnessInconclusivo("Microsoft Store não apareceu fisicamente")
            obs = observar_store()
            if not obs.get("visivel"):
                raise HarnessInconclusivo("Store apareceu e sumiu antes da observação")
            if not obs.get("canonical_live"):
                raise HarnessInconclusivo(
                    "janela Store abriu, mas nenhum processo canônico winstore.app.exe ficou observável"
                )
            return obs

        def esperar_store_fechada(timeout: float = 6.0) -> bool:
            return _esperar(lambda: not store_visivel(), timeout, 0.20)

        def pids_ainda_vivos(pids: set[int]) -> set[int]:
            vivos: set[int] = set()
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                        vivos.add(pid)
                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue
                except Exception:
                    # Fail-closed: se não conseguimos provar que morreu, tratamos como vivo.
                    vivos.add(pid)
            return vivos

        def esperar_pids_morrerem(pids: set[int], timeout: float = 6.0) -> bool:
            if not pids:
                return True
            return _esperar(lambda: not pids_ainda_vivos(pids), timeout, 0.20)

        def processos_encerrados_no_trace(texto: str) -> list[str]:
            nomes: list[str] = []
            for linha in str(texto or "").splitlines():
                if "[FECHAR_PROGRAMA] processo exato encerrado" not in linha:
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
                    valor = resto[1:fim] if fim > 0 else resto[1:]
                else:
                    valor = resto.split()[0]
                if valor:
                    nomes.append(valor.casefold().strip())
            return nomes

        def construir_executor_ctx(
            mapa: dict[str, Any],
            *,
            open_inputs: list[str] | None = None,
            close_inputs: list[str] | None = None,
            close_errors: list[str] | None = None,
            resultados: list[dict[str, Any]] | None = None,
        ) -> tuple[dict[str, Any], Any]:
            resultados_ref = resultados if resultados is not None else []

            def marcar_resultado(status: str, **kwargs: Any) -> None:
                resultados_ref.append({"status": str(status or ""), **kwargs})

            def falar_noop(*_args: Any, **_kwargs: Any) -> None:
                return None

            def abrir_instrumentado(alvo: str, *args: Any, **kwargs: Any) -> bool:
                if open_inputs is not None:
                    open_inputs.append(str(alvo or ""))
                return bool(abrir_programa(alvo, *args, **kwargs))

            def fechar_instrumentado(alvo: str, *args: Any, **kwargs: Any) -> bool:
                if close_inputs is not None:
                    close_inputs.append(str(alvo or ""))
                try:
                    return bool(fechar_programa(alvo, *args, **kwargs))
                except Exception as exc:
                    if close_errors is not None:
                        close_errors.append(f"{type(exc).__name__}: {exc}")
                    raise

            def esperar_programa_fechar(nome: str) -> bool:
                return _esperar(lambda: buscar_janela(gw, nome)[0] is None, 6.0, 0.20)

            deps = DependenciasExecutorJanelas(
                marcar_resultado=marcar_resultado,
                falar_por_status=falar_noop,
                falar_resultado_janela=falar_noop,
                esperar_programa_fechar=esperar_programa_fechar,
            )
            ctx = {
                "APPS_MAP": mapa,
                "abrir_programa": abrir_instrumentado,
                "fechar_programa": fechar_instrumentado,
                "_resolver_alvo_ambiente": resolver_local,
                "_eh_alvo_site_web": lambda _texto: False,
                "_contexto_aponta_site_web": lambda _texto="": False,
                "_registro_navegador_operacoes_runtime": None,
                "falar_com_lipsync": None,
            }
            return ctx, deps

        def abrir_store_pelo_executor(rotulo: str) -> dict[str, Any]:
            resultados_open: list[dict[str, Any]] = []
            entradas_open: list[str] = []
            ctx_open, deps_open = construir_executor_ctx(
                apps_map, open_inputs=entradas_open, resultados=resultados_open
            )
            retorno = executar_intencao_janelas(
                "APP_OPEN", {"nome_app": STORE_NAME}, "pc_a", ctx_open, deps_open,
                texto_original="abre a microsoft store",
            )
            if not getattr(retorno, "tratado", True):
                raise HarnessInconclusivo(f"{rotulo}: executor não tratou APP_OPEN")
            resultado = resultados_open[-1] if resultados_open else {}
            if entradas_open != [EXPECTED_OPEN_LOCATOR]:
                raise HarnessInconclusivo(
                    f"{rotulo}: APP_OPEN não entregou URI congelado ao abridor: {entradas_open!r}"
                )
            if str(resultado.get("status") or "") != "protocolo_aberto" or resultado.get("executou") is not True:
                raise HarnessInconclusivo(f"{rotulo}: APP_OPEN divergente: {resultado!r}")
            obs = esperar_store_aberta()
            _print_status(
                rotulo, "PASS",
                f"entrada={entradas_open[0]!r}; título={obs.get('titulo')!r}; janela_pid={obs.get('pid')}; "
                f"host={obs.get('process_name') or '?'}; canônico=" +
                ", ".join(f"{x.get('name')}#{x.get('pid')}" for x in obs.get('canonical_live') or []),
            )
            return obs

        # Precondição: o experimento controla a abertura desde zero.
        if store_visivel():
            obs_pre = observar_store()
            raise HarnessInconclusivo(
                "Microsoft Store já estava visível. Feche-a manualmente antes de rodar. "
                f"título={obs_pre.get('titulo')!r}"
            )
        _print_status("D precondição Store fechada", "PASS", "nenhuma janela Store visível")

        obs_primeira = abrir_store_pelo_executor("E APP_OPEN real para controles")
        pids_primeira = {int(x.get("pid") or 0) for x in obs_primeira.get("canonical_live") or [] if int(x.get("pid") or 0)}

        # 1) Controle negativo: URI não pode adquirir autoridade de processo.
        neg_trace = io.StringIO()
        neg_exc: Exception | None = None
        with contextlib.redirect_stdout(neg_trace):
            try:
                fechar_programa(EXPECTED_OPEN_LOCATOR)
            except Exception as exc:
                neg_exc = exc
        neg_texto = neg_trace.getvalue()
        print("\n--- CONTROLE NEGATIVO: close(URI) ---")
        print(neg_texto.rstrip() or "(sem saída do fechador)")
        print("--- FIM CONTROLE NEGATIVO ---\n")

        assinatura_neg = f"Nenhum processo seguro e exato encontrado para fechar: {EXPECTED_OPEN_LOCATOR!r}"
        if neg_exc is None:
            raise HarnessInconclusivo("controle negativo falhou: close(URI) não lançou exceção")
        if assinatura_neg not in neg_texto:
            raise HarnessInconclusivo("controle negativo perdeu a assinatura física esperada")
        if not store_visivel():
            raise HarnessInconclusivo("controle negativo divergente: close(URI) fechou a Store")
        vivos_neg = pids_ainda_vivos(pids_primeira)
        if vivos_neg != pids_primeira:
            raise HarnessInconclusivo(
                "controle negativo alterou o(s) PID(s) canônico(s) da Store; "
                f"antes={sorted(pids_primeira)} ainda_vivos={sorted(vivos_neg)}"
            )
        _print_status(
            "F controle negativo close(URI)", "RED ESPERADO",
            f"URI rejeitado; Store e PID(s) canônico(s) permanecem vivos={sorted(vivos_neg)}",
        )

        # 2) Controle positivo: o nome semântico deve acionar o mapa canônico real.
        pos_trace = io.StringIO()
        pos_exc: Exception | None = None
        pos_ret = False
        with contextlib.redirect_stdout(pos_trace):
            try:
                pos_ret = bool(fechar_programa(STORE_NAME))
            except Exception as exc:
                pos_exc = exc
        pos_texto = pos_trace.getvalue()
        print("\n--- CONTROLE POSITIVO: close(nome semântico) ---")
        print(pos_texto.rstrip() or "(sem saída do fechador)")
        print("--- FIM CONTROLE POSITIVO ---\n")

        if pos_exc is not None:
            raise HarnessInconclusivo(
                f"HIPÓTESE CONCORRENTE: close(nome semântico) falhou: {type(pos_exc).__name__}: {pos_exc}"
            )
        if not pos_ret:
            raise HarnessInconclusivo("HIPÓTESE CONCORRENTE: close(nome semântico) retornou False")
        kills_pos = processos_encerrados_no_trace(pos_texto)
        if not kills_pos:
            raise HarnessInconclusivo(
                "controle positivo não mostrou encerramento de processo exato; não certificar candidato"
            )
        if any(nome not in set(canonicos) for nome in kills_pos):
            raise HarnessInconclusivo(
                f"controle positivo encerrou identidade fora do mapa canônico: {kills_pos!r}"
            )
        if not set(kills_pos).intersection(canonicos):
            raise HarnessInconclusivo(
                f"controle positivo não encerrou processo canônico da Store: {kills_pos!r}"
            )
        if not esperar_store_fechada():
            obs = observar_store()
            raise HarnessInconclusivo(
                "HIPÓTESE CONCORRENTE: fechador retornou sucesso, mas a Store continuou visível; "
                f"obs={obs!r}"
            )
        if not esperar_pids_morrerem(pids_primeira):
            raise HarnessInconclusivo(
                f"HIPÓTESE CONCORRENTE: PID(s) canônico(s) inicial(is) ainda vivos: {sorted(pids_primeira)}"
            )
        _print_status(
            "G controle positivo close(nome semântico)", "GREEN FÍSICO",
            f"processos encerrados={kills_pos!r}; janela Store desapareceu; pids={sorted(pids_primeira)}",
        )

        # 3) Reabre pelo caminho de produção para testar o executor contrafactual.
        time.sleep(0.6)
        obs_segunda = abrir_store_pelo_executor("H reabertura APP_OPEN real")
        pids_segunda = {int(x.get("pid") or 0) for x in obs_segunda.get("canonical_live") or [] if int(x.get("pid") or 0)}

        # Mapa contrafactual: cópia independente e UMA única diferença intencional.
        apps_map_cf = dict(apps_map)
        apps_map_cf[STORE_NAME] = STORE_NAME
        diferencas = {
            chave: (apps_map.get(chave), apps_map_cf.get(chave))
            for chave in set(apps_map) | set(apps_map_cf)
            if apps_map.get(chave) != apps_map_cf.get(chave)
        }
        if diferencas != {STORE_NAME: (EXPECTED_OPEN_LOCATOR, STORE_NAME)}:
            raise HarnessInconclusivo(
                f"mapa contrafactual contaminado; diferenças={diferencas!r}"
            )
        if apps_map.get(STORE_NAME) != EXPECTED_OPEN_LOCATOR:
            raise HarnessInconclusivo("APPS_MAP original foi mutado pelo harness")
        _print_status(
            "I contrafactual isolado", "PASS",
            "única mudança efêmera: microsoft store -> microsoft store",
        )

        cf_inputs: list[str] = []
        cf_errors: list[str] = []
        cf_resultados: list[dict[str, Any]] = []
        ctx_cf, deps_cf = construir_executor_ctx(
            apps_map_cf,
            close_inputs=cf_inputs,
            close_errors=cf_errors,
            resultados=cf_resultados,
        )

        cf_trace = io.StringIO()
        with contextlib.redirect_stdout(cf_trace):
            retorno_cf = executar_intencao_janelas(
                "CLOSE_APP",
                {"nome_app": STORE_NAME, "alvo_tipado": "app"},
                "pc_a",
                ctx_cf,
                deps_cf,
                texto_original="fecha a microsoft store",
            )
        cf_texto = cf_trace.getvalue()
        print("\n--- CONTRAFACTUAL DO EXECUTOR: preservar nome semântico ---")
        print(cf_texto.rstrip() or "(sem saída do executor)")
        print("--- FIM CONTRAFACTUAL DO EXECUTOR ---\n")

        if not getattr(retorno_cf, "tratado", True):
            raise HarnessInconclusivo("executor contrafactual não tratou CLOSE_APP")
        if cf_inputs != [STORE_NAME]:
            raise HarnessInconclusivo(
                f"contrafactual não preservou exatamente o nome semântico: {cf_inputs!r}"
            )
        if cf_errors:
            raise HarnessInconclusivo(
                f"HIPÓTESE CONCORRENTE: fechador falhou mesmo recebendo nome semântico: {cf_errors!r}"
            )
        resultado_cf = cf_resultados[-1] if cf_resultados else {}
        if str(resultado_cf.get("status") or "") != "app_fechado":
            raise HarnessInconclusivo(
                f"contrafactual não terminou em app_fechado: {resultado_cf!r}"
            )
        if resultado_cf.get("executou") is not True:
            raise HarnessInconclusivo(
                f"contrafactual não marcou executou=True: {resultado_cf!r}"
            )
        if resultado_cf.get("confirmado") is False:
            raise HarnessInconclusivo(
                f"contrafactual marcou confirmado=False: {resultado_cf!r}"
            )
        if store_visivel():
            obs = observar_store()
            raise HarnessInconclusivo(
                f"contrafactual declarou fechamento, mas Store continua visível: {obs!r}"
            )
        if not esperar_pids_morrerem(pids_segunda):
            raise HarnessInconclusivo(
                f"contrafactual deixou PID(s) canônico(s) vivos: {sorted(pids_segunda)}"
            )
        kills_cf = processos_encerrados_no_trace(cf_texto)
        if not kills_cf:
            raise HarnessInconclusivo(
                "contrafactual não atravessou o encerrador físico exato"
            )
        if any(nome not in set(canonicos) for nome in kills_cf):
            raise HarnessInconclusivo(
                f"contrafactual encerrou identidade fora do mapa canônico: {kills_cf!r}"
            )
        if not set(kills_cf).intersection(canonicos):
            raise HarnessInconclusivo(
                f"contrafactual não encerrou processo canônico da Store: {kills_cf!r}"
            )
        _print_status(
            "J executor real + nome semântico preservado", "GREEN CONTRAFACTUAL",
            f"entrada={cf_inputs[0]!r}; kills={kills_cf!r}; status=app_fechado; Store desapareceu",
        )

        # O experimento não pode deixar qualquer alteração de Git.
        status_after = _run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
        if status_after != status_before or _run_git(repo, "rev-parse", "HEAD") != EXPECTED_HEAD:
            raise HarnessInconclusivo("HEAD/index/working tree mudaram durante a falsificação")
        _auditar_head_e_blobs(repo)
        _print_status("Z HEAD/blobs/index/working tree preservados", "PASS", "nenhuma mutação Git")

        print("\n" + "=" * 112)
        print("✅ CANDIDATO SOBREVIVEU À FALSIFICAÇÃO STORE-ONLY")
        print("   produção ....................................... INALTERADA")
        print("   close(ms-windows-store:) ....................... RED esperado / Store permanece")
        print("   close(microsoft store) ......................... GREEN físico / WinStore.App.exe encerrado")
        print("   executor original no chaos/RED 4.1 ............. RED / entrega URI")
        print("   executor contrafactual 4.2 ..................... GREEN / entrega nome semântico")
        print("   hipótese mapa canônico stale ................... FALSIFICADA")
        print("   hipótese fechador físico incapaz ................ FALSIFICADA")
        print("   hipótese host ApplicationFrameHost é alvo ....... FALSIFICADA / host genérico não é necessário")
        print("   ROOT causal sustentada ......................... _executar_fechar_app aplica APPS_MAP de abertura antes do close")
        print("   candidato mínimo sustentado .................... preservar nome semântico até fechar_programa")
        print("   PATCH DE PRODUÇÃO .............................. AINDA NÃO APLICADO")
        print("   Store ao final ................................. FECHADA")
        print("   exit code 2 = falsificação causal passou; NÃO é crash")
        return EXIT_CANDIDATE_SURVIVES

    except HarnessInconclusivo as exc:
        print("\n" + "=" * 112)
        print("❌ FALSIFICAÇÃO INCONCLUSIVA / DIVERGENTE")
        print(f"   motivo: {exc}")
        print("   NÃO aplicar patch com base neste resultado.")
        if repo is not None and status_before is not None:
            try:
                status_now = _run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
                head_now = _run_git(repo, "rev-parse", "HEAD")
                preservado = status_now == status_before and head_now == EXPECTED_HEAD
                _print_status(
                    "Z HEAD/index/working tree após inconclusivo",
                    "PASS" if preservado else "ALERTA",
                    "preservados" if preservado else "divergiram; inspecione antes de continuar",
                )
            except Exception as git_exc:
                print(f"   ⚠️ não consegui reauditar Git: {git_exc}")
        return EXIT_INCONCLUSIVE

    except Exception as exc:
        print("\n" + "=" * 112)
        print("❌ HARNESS QUEBROU")
        print(f"   {type(exc).__name__}: {exc}")
        print("   classificar como INCONCLUSIVO; NÃO inferir raiz nem aplicar patch.")
        return EXIT_INCONCLUSIVE


if __name__ == "__main__":
    raise SystemExit(main())
