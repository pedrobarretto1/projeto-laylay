#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REGRESSÃO FINAL DETERMINÍSTICA PRÉ-CHAOS — TESTE 4.17 V2

Objetivo
========
Última barreira antes do chaos soberano.

Diferença para o 4.11:
- NENHUM discovery fuzzy;
- NENHUM test_red_*;
- NENHUM harness histórico red_/falsificacao_/auditor_/pos_patch_;
- allowlist fixa e inspecionada;
- dois canaries locais sem efeito físico para C1-D/Store e 92-C.

Estado esperado da produção
===========================
HEAD:
    95be16751d678180a8ede2a22ea04b1aef6cbf8d

Blobs causais do worktree real:
    executor_janelas.py      72526e6...
    pre_fluxo_contextual.py  8b75bed...
    contexto_imediato.py     921053c...

Correção V2 após a primeira fronteira do 4.17 V1
===================================================
O 4.17 V1 parou em:
    tests/test_continuidade_geral.py::
    test_sequencia_real_arquivo_aberto_fecha_ele_vence_app_antigo

A produção estava correta. O resultado ganhou o metadado canônico já previsto
por resolver_comando_contextual:
    "_dominio_contextual": "arquivo"

A expectativa tracked estava incompleta. Ela foi corrigida com EXATAMENTE uma
linha adicional e o novo blob foi auditado:

    tests/test_continuidade_geral.py
    blob permitido:
        c4f019ec6e6fab967748a2462d380533b6aaea88

A V2 NÃO aceita alterações arbitrárias nesse teste:
- exige exatamente esse blob;
- exige que ele esteja unstaged;
- todos os outros arquivos da allowlist continuam idênticos ao HEAD.

Escopo da allowlist
===================
C1-B2 / C1-C:
- regressão R1.1 de autoridade + cadeia + SWITCH_PREVIOUS_TAB;
- continuação de resultado web.

92-A / contexto imediato:
- sequência real de arquivo aberto -> "fecha ele" -> janela do arquivo.

Janelas / 92-C:
- alvo explicitamente tipado como app ausente não vira aba/processo;
- arquivo tipado fecha janela, nunca processo.

Autoridade / decisão:
- comando vindo da IA é bloqueado em conversa;
- pedido explícito continua permitido;
- IA-first também passa pelo árbitro em conversa.

Turno 180 / reparação:
- regressivo existente test_coerencia_operacional_geral.py completo,
  incluindo o antigo RED 4.12 agora GREEN.

Canaries locais sem efeito físico
=================================
C1-D Store:
- CLOSE_APP "microsoft store" deve chamar o closer fake com o nome canônico
  "microsoft store", NUNCA "ms-windows-store:".
- closer=True + pós-condição=True => app_fechado.

92-C causalidade:
- closer=False com alvo aparentemente ausente depois NÃO pode produzir
  app_fechado;
- a pós-condição nem deve ser consultada quando o closer retorna False.

Contrato
========
0 = regressão final GREEN; CHAOS AUTORIZADO.
1 = qualquer RED/inconclusão; CHAOS BLOQUEADO.
2 = NÃO EXISTE.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any


HEAD = "95be16751d678180a8ede2a22ea04b1aef6cbf8d"

CAUSAL_BLOBS = {
    "mente_laylay/autonomia/executor_janelas.py": "72526e6",
    "mente_laylay/autonomia/pre_fluxo_contextual.py": "8b75bed",
    "mente_laylay/memoria_mental/contexto_imediato.py": "921053c",
}

TESTE_ATUALIZADO_AUDITADO = {
    "tests/test_continuidade_geral.py":
        "c4f019ec6e6fab967748a2462d380533b6aaea88",
}

ALLOWLIST = [
    # C1-B2 / C1-C — arquivo inteiro já inspecionado, só fakes/monkeypatch.
    "tests/test_regressao_r1_1_autoridade_navegador_cadeia.py",

    # C1-B2 — continuidade web.
    (
        "tests/test_regressoes_roteiro_117_turnos_20260814.py::"
        "test_primeiro_resultado_web_vence_resultado_local_antigo"
    ),

    # 92-A — runtime de contexto imediato com arquivo aberto.
    (
        "tests/test_continuidade_geral.py::"
        "test_sequencia_real_arquivo_aberto_fecha_ele_vence_app_antigo"
    ),

    # Janelas — segurança de app tipado ausente.
    (
        "tests/test_regressoes_janelas_terminal_log_20260813.py::"
        "test_fecha_programa_chamado_limpa_alvo_e_nao_cai_em_aba"
    ),

    # Janelas — arquivo fecha janela, não processo.
    (
        "tests/test_regressoes_janelas_terminal_log_20260813.py::"
        "test_turno_120_fecha_arquivo_tipado_mesmo_sem_confirmar_foco"
    ),

    # Autoridade/decisão — conversa não executa ação inventada.
    (
        "tests/test_decisao_unica_turno.py::"
        "test_comando_json_da_ia_e_bloqueado_em_conversa"
    ),

    # Autoridade/decisão — pedido explícito continua permitido.
    (
        "tests/test_decisao_unica_turno.py::"
        "test_comando_json_continua_permitido_em_pedido_explicito"
    ),

    # Autoridade/decisão — IA-first também respeita o árbitro.
    (
        "tests/test_decisao_unica_turno.py::"
        "test_intencao_da_ia_tambem_passa_pelo_arbitro_em_conversa"
    ),

    # Turno 180 + regressão 4.12 — arquivo inteiro, 4 testes já inspecionados.
    "tests/test_coerencia_operacional_geral.py",
]


class Inconclusivo(RuntimeError):
    pass


def _status(nome: str, estado: str, detalhe: str = "") -> None:
    base = f"{nome}."
    linha = base + "." * max(1, 98 - len(base)) + f" {estado}"
    if detalhe:
        linha += f" | {detalhe}"
    print(linha)


def _run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git(repo: Path, *args: str) -> str:
    proc = _run(["git", *args], cwd=repo)
    if proc.returncode != 0:
        raise Inconclusivo(
            f"git {' '.join(args)} falhou ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _repo_root() -> Path:
    aqui = Path(__file__).resolve().parent
    proc = _run(["git", "rev-parse", "--show-toplevel"], cwd=aqui)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise Inconclusivo("execute dentro do repositório projeto-laylay")
    return Path(proc.stdout.strip()).resolve()


def _pick_python(repo: Path) -> Path:
    candidatos = [
        repo / ".venv314" / "Scripts" / "python.exe",
        Path(r"C:\Python314\python.exe"),
        Path(sys.executable),
    ]
    vistos: set[str] = set()
    for candidato in candidatos:
        chave = str(candidato)
        if chave in vistos:
            continue
        vistos.add(chave)
        if candidato.is_file():
            return candidato
    raise Inconclusivo("nenhum Python executável compatível encontrado")


def _audit_causal(repo: Path) -> dict[str, str]:
    head = _git(repo, "rev-parse", "HEAD")
    if head != HEAD:
        raise Inconclusivo(
            f"HEAD divergente: esperado {HEAD}, observado {head}"
        )

    staged = {
        x.replace("\\", "/")
        for x in _git(
            repo,
            "diff",
            "--cached",
            "--name-only",
            "--",
            *CAUSAL_BLOBS.keys(),
        ).splitlines()
        if x.strip()
    }
    if staged:
        raise Inconclusivo(
            f"arquivos causais staged inesperadamente: {sorted(staged)!r}"
        )

    modified = {
        x.replace("\\", "/")
        for x in _git(
            repo,
            "diff",
            "--name-only",
            "--",
            *CAUSAL_BLOBS.keys(),
        ).splitlines()
        if x.strip()
    }
    if modified != set(CAUSAL_BLOBS):
        raise Inconclusivo(
            f"diff causal divergente: esperado={sorted(CAUSAL_BLOBS)!r} "
            f"observado={sorted(modified)!r}"
        )

    hashes: dict[str, str] = {}
    for rel, prefixo in CAUSAL_BLOBS.items():
        blob = _git(
            repo,
            "hash-object",
            "--filters",
            f"--path={rel}",
            rel,
        )
        if not blob.startswith(prefixo):
            raise Inconclusivo(
                f"blob causal divergente em {rel}: "
                f"esperado prefixo={prefixo} observado={blob}"
            )
        hashes[rel] = blob
    return hashes


def _arquivo_de_nodeid(nodeid: str) -> str:
    return str(nodeid).split("::", 1)[0].replace("\\", "/")


def _audit_allowlist(repo: Path) -> list[str]:
    arquivos = sorted({_arquivo_de_nodeid(item) for item in ALLOWLIST})

    for rel in arquivos:
        if not rel.startswith("tests/test_") or not rel.endswith(".py"):
            raise Inconclusivo(f"entrada fora de tests/test_*.py: {rel}")
        nome = Path(rel).name.casefold()
        if nome.startswith("test_red_"):
            raise Inconclusivo(f"snapshot RED proibido na allowlist: {rel}")
        if any(
            marcador in nome
            for marcador in (
                "fisico", "physical", "chaos", "caos",
                "e2e", "integration", "integracao",
            )
        ):
            raise Inconclusivo(f"teste de escopo físico/integrado proibido: {rel}")

        if not (repo / rel).is_file():
            raise Inconclusivo(f"arquivo da allowlist ausente: {rel}")

        tracked = _git(repo, "ls-files", "--", rel).replace("\\", "/").strip()
        if tracked != rel:
            raise Inconclusivo(
                f"arquivo da allowlist não está tracked exatamente: "
                f"{rel} -> {tracked!r}"
            )

        staged = _run(
            ["git", "diff", "--cached", "--quiet", "HEAD", "--", rel],
            cwd=repo,
        )
        if staged.returncode != 0:
            raise Inconclusivo(
                f"teste da allowlist está staged/divergente: {rel}"
            )

        if rel in TESTE_ATUALIZADO_AUDITADO:
            esperado = TESTE_ATUALIZADO_AUDITADO[rel]
            observado = _git(
                repo,
                "hash-object",
                "--filters",
                f"--path={rel}",
                rel,
            )
            if observado != esperado:
                raise Inconclusivo(
                    f"teste auditado divergiu do blob permitido: "
                    f"{rel} esperado={esperado} observado={observado}"
                )

            # A exceção precisa continuar sendo uma modificação local,
            # justamente porque o HEAD histórico ainda contém a expectativa
            # incompleta. Se ficar igual ao HEAD, a premissa da V2 mudou.
            diff = _run(
                ["git", "diff", "--quiet", "HEAD", "--", rel],
                cwd=repo,
            )
            if diff.returncode == 0:
                raise Inconclusivo(
                    f"teste auditado deixou de carregar a correção local: {rel}"
                )
            continue

        # Todo o restante continua congelado exatamente no HEAD.
        diff = _run(
            ["git", "diff", "--quiet", "HEAD", "--", rel],
            cwd=repo,
        )
        if diff.returncode != 0:
            raise Inconclusivo(
                f"teste da allowlist foi modificado em relação ao HEAD: {rel}"
            )

    return arquivos


def _deps_janelas(eventos: list[tuple], *, esperar_programa):
    from mente_laylay.autonomia.executor_janelas import DependenciasExecutorJanelas

    return DependenciasExecutorJanelas(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, dict(kwargs))
        ),
        falar_por_status=lambda status, fallback, **kwargs: eventos.append(
            ("fala_status", status, fallback, dict(kwargs))
        ),
        falar_resultado_janela=lambda nome, status: eventos.append(
            ("fala_janela", nome, status)
        ),
        alvo_preciso_para_aba=lambda alvo: alvo,
        esperar_aba_fechar=lambda *_args: True,
        esperar_programa_fechar=esperar_programa,
        executar_recursivo=lambda *_args: True,
    )


def _canary_store() -> None:
    """
    C1-D sem Store física:
    - percepção fake diz programa aberto;
    - closer fake retorna True;
    - pós-condição fake retorna True;
    - exige nome canônico "microsoft store".
    """
    from mente_laylay.autonomia.executor_janelas import executar_intencao_janelas

    eventos: list[tuple] = []
    fechamentos: list[str] = []
    esperas: list[str] = []

    def fechar(nome: str) -> bool:
        fechamentos.append(nome)
        return True

    def esperar(nome: str) -> bool:
        esperas.append(nome)
        return True

    despacho = executar_intencao_janelas(
        "CLOSE_APP",
        {"nome_app": "microsoft store"},
        "pc_a",
        {
            "APPS_MAP": {
                # Reproduz a diferença entre alias de abertura e identidade
                # física. O executor não pode entregar esta URI ao closer.
                "microsoft store": "ms-windows-store:",
            },
            "_resolver_alvo_ambiente": lambda nome: {
                "programa_aberto": nome.casefold() == "microsoft store",
                "aba_aberta": False,
            },
            "_eh_alvo_site_web": lambda _nome: False,
            "_contexto_aponta_site_web": lambda _nome: False,
            "fechar_programa": fechar,
            "falar_com_lipsync": lambda *_args: None,
        },
        _deps_janelas(eventos, esperar_programa=esperar),
    )

    if not getattr(despacho, "tratado", False):
        raise Inconclusivo("canary Store não foi tratado pelo executor")
    if fechamentos != ["microsoft store"]:
        raise Inconclusivo(
            f"Store perdeu identidade canônica: closer recebeu {fechamentos!r}"
        )
    if esperas != ["microsoft store"]:
        raise Inconclusivo(
            f"Store pós-condição recebeu alvo divergente: {esperas!r}"
        )

    resultados = [
        item for item in eventos
        if item[0] == "resultado"
    ]
    if resultados != [
        ("resultado", "app_fechado", {"executou": True})
    ]:
        raise Inconclusivo(
            f"Store não confirmou app_fechado no canary: {resultados!r}"
        )


def _canary_92c() -> None:
    """
    92-C sem processo físico:
    closer=False precisa encerrar a causalidade.
    A pós-condição não pode ser consultada e não pode surgir app_fechado.
    """
    from mente_laylay.autonomia.executor_janelas import executar_intencao_janelas

    eventos: list[tuple] = []
    fechamentos: list[str] = []
    esperas: list[str] = []

    def fechar(nome: str) -> bool:
        fechamentos.append(nome)
        return False

    def esperar(nome: str) -> bool:
        esperas.append(nome)
        raise AssertionError(
            "pós-condição não deve rodar quando fechar_programa=False"
        )

    despacho = executar_intencao_janelas(
        "CLOSE_APP",
        {"nome_app": "opera"},
        "pc_a",
        {
            "APPS_MAP": {"opera": "opera.exe"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "aba_aberta": False,
            },
            "_eh_alvo_site_web": lambda _nome: False,
            "_contexto_aponta_site_web": lambda _nome: False,
            "fechar_programa": fechar,
            "falar_com_lipsync": lambda *_args: None,
        },
        _deps_janelas(eventos, esperar_programa=esperar),
    )

    if not getattr(despacho, "tratado", False):
        raise Inconclusivo("canary 92-C não foi tratado pelo executor")
    if fechamentos != ["opera.exe"]:
        raise Inconclusivo(
            f"92-C perdeu mapeamento de alias: {fechamentos!r}"
        )
    if esperas:
        raise Inconclusivo(
            f"92-C consultou pós-condição sem autoria causal: {esperas!r}"
        )

    resultados = [
        item for item in eventos
        if item[0] == "resultado"
    ]
    if resultados != [
        ("resultado", "falha_execucao", {"executou": False})
    ]:
        raise Inconclusivo(
            f"92-C voltou a criar falso sucesso: {resultados!r}"
        )


def main() -> int:
    print("REGRESSÃO FINAL DETERMINÍSTICA PRÉ-CHAOS — TESTE 4.17 V2")
    print("=" * 136)
    print(f"HEAD travado: {HEAD}")
    print("produção: WORKTREE REAL PATCHADO 4.15")
    print("seleção: ALLOWLIST FIXA, sem discovery")
    print("exceção auditada: test_continuidade_geral.py blob c4f019e...")
    print("snapshots RED/harnesses históricos: PROIBIDOS")
    print("efeitos físicos/rede/LLM: NENHUM")
    print("exit 0 = GREEN / CHAOS AUTORIZADO")
    print("exit 1 = RED/inconclusivo / CHAOS BLOQUEADO")
    print()

    try:
        repo = _repo_root()
        os.chdir(repo)
        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))

        snapshot0 = _git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        hashes0 = _audit_causal(repo)

        _status(
            "A HEAD + blobs causais",
            "PASS",
            "92-A=921053c; 92-C=72526e6; 180=8b75bed",
        )

        arquivos = _audit_allowlist(repo)
        _status(
            "B allowlist fixa + exceção auditada",
            "PASS",
            f"{len(ALLOWLIST)} entradas / {len(arquivos)} arquivos; "
            "1 blob de teste atualizado explicitamente travado",
        )

        print()
        print("ALLOWLIST")
        print("-" * 136)
        for indice, item in enumerate(ALLOWLIST, 1):
            print(f"{indice:02d}. {item}")
        print()

        # Canaries primeiro: se eles caírem, nem vale rodar a suíte.
        _canary_store()
        _status(
            "C C1-D / Microsoft Store canary",
            "GREEN / PRESERVADA",
            "closer recebe 'microsoft store'; app_fechado confirmado",
        )

        _canary_92c()
        _status(
            "D 92-C causalidade canary",
            "GREEN SEGURANÇA",
            "close=False => falha; pós-condição não consultada",
        )

        python = _pick_python(repo)
        pytest_check = _run(
            [str(python), "-c", "import pytest; print(pytest.__version__)"],
            cwd=repo,
        )
        if pytest_check.returncode != 0:
            raise Inconclusivo(
                f"pytest indisponível em {python}: {pytest_check.stderr.strip()}"
            )
        _status(
            "E Python + pytest",
            "PASS",
            f"{python} | pytest={pytest_check.stdout.strip()}",
        )

        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        print()
        print("PYTEST — ALLOWLIST FINAL")
        print("-" * 136)

        proc = _run(
            [
                str(python),
                "-m",
                "pytest",
                "-q",
                "-vv",
                "--tb=short",
                "--disable-warnings",
                "--maxfail=1",
                "-p",
                "no:cacheprovider",
                *ALLOWLIST,
            ],
            cwd=repo,
            env=env,
        )

        if proc.stdout:
            print(proc.stdout.rstrip())
        if proc.stderr:
            print("--- STDERR PYTEST ---")
            print(proc.stderr.rstrip())

        print("-" * 136)
        print(f"pytest exit code: {proc.returncode}")

        # Mesmo em RED, o repo precisa permanecer soberanamente idêntico.
        hashes1 = _audit_causal(repo)
        snapshot1 = _git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )

        if hashes1 != hashes0:
            raise Inconclusivo(
                f"blobs causais mudaram durante 4.17: "
                f"antes={hashes0!r} depois={hashes1!r}"
            )
        if snapshot1 != snapshot0:
            raise Inconclusivo(
                "estado Git mudou durante 4.17.\n"
                f"ANTES:\n{snapshot0}\n\nDEPOIS:\n{snapshot1}"
            )

        _status(
            "Z Git/worktree",
            "PASS",
            "estado completo preservado",
        )

        if proc.returncode != 0:
            print()
            print("## ❌ REGRESSÃO FINAL 4.17 V2 RED")
            print("primeiro failure acima = primeira fronteira para investigação")
            print("CHAOS: BLOQUEADO")
            return 1

        print()
        print("## ✅ REGRESSÃO FINAL 4.17 V2 INTEGRALMENTE GREEN")
        print("-" * 136)
        print("C1-B2 / cadeia navegador ......................... GREEN")
        print("C1-C / autoridade + aba anterior ................. GREEN")
        print("C1-D / Microsoft Store ........................... GREEN CANARY")
        print("92-A / contexto arquivo .......................... GREEN")
        print("92-C / causalidade fechamento .................... GREEN CANARY")
        print("janelas / arquivo tipado ......................... GREEN")
        print("autoridade / decisão ............................. GREEN")
        print("turno 180 / reparação ............................ GREEN")
        print("regressão 4.12 ................................... GREEN")
        print("Git/worktree ...................................... PRESERVADO")
        print()
        print("CHAOS SOBERANO: AUTORIZADO")
        print("exit code 0")
        return 0

    except Inconclusivo as exc:
        print()
        print("## ❌ REGRESSÃO FINAL 4.17 V2 INCONCLUSIVA")
        print(f"motivo: {exc}")
        print("CHAOS: BLOQUEADO")
        return 1

    except Exception as exc:
        print()
        print("## ❌ HARNESS 4.17 V2 FALHOU DE FORMA NÃO CLASSIFICADA")
        print(f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("CHAOS: BLOQUEADO")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
