#!/usr/bin/env python3
"""Patch A — consulta read-only de capacidades antes da barreira P0.

Escopo deliberadamente estreito:
- NAO altera a classificacao/modalidade do turno;
- NAO altera a barreira fail-closed P0;
- NAO altera executores nem concede autorizacao;
- apenas permite que o respondedor deterministico/read-only de capacidades
  responda antes da barreira de mutacao;
- adiciona regressao rastreada com a fala real e variante natural.

O patcher trava HEAD/blobs/alvos, prova o bug vermelho antes da mudanca,
faz backup, aplica por ancoras exatas, valida AST/py_compile/diff/pytest e
faz rollback automatico em qualquer falha. Nao executa add/commit/push.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

PATCH_ID = "P0_CAPACIDADE_READONLY_A1_20260816"
BASELINE_HEAD = "ebcaaa27b4e759757f8416bbc27133a6d85a1519"

TARGET_RUNTIME = Path("mente_laylay/autonomia/comandos_imediatos.py")
TARGET_TEST = Path("tests/test_regressao_consciencia_capacidades.py")
RED_TEST = Path("tests/test_red_contratos_arquivos_contexto_capacidades.py")

EXPECTED_BLOBS = {
    TARGET_RUNTIME.as_posix(): "8b619279996cdbd2ae1f866470d2d025fff31d70",
    TARGET_TEST.as_posix(): "04aef933215dcb8b41a3a9e185de763e07478ce6",
}
EXPECTED_RED_SHA256 = "b9c5586d44cba1619fb9cfc21018c4864135873ed2ec50d3e7ea74c3266a6e62"

RED_NODE_EXATO = (
    "tests/test_red_contratos_arquivos_contexto_capacidades.py::"
    "test_red__pergunta_capacidade_apagar_arquivos_e_tratada_antes_da_barreira_p0"
)
RED_NODE_TRACKED = (
    "tests/test_regressao_consciencia_capacidades.py::"
    "test_porta_prioritaria_responde_sem_chamar_executor_ou_llm"
)

FOCUSED_TESTS = [
    "tests/test_regressao_consciencia_capacidades.py",
    "tests/test_p0_autorizacao_modalidade.py",
    "tests/test_autorizacao_ato_fala_v2.py",
    "tests/test_p16_linguagem_natural_operacional.py",
    "tests/test_revisao_intra_turno_v1.py",
    RED_NODE_EXATO,
]

RUNTIME_ANCHOR_BEFORE = '''        # Detectar uma intent não concede permissão para executá-la. Esta
        # barreira faz a rota determinística usar o mesmo dono do turno da LLM.
        mente_atual = getattr(estado_runtime, "mental", {})
        turno_atual = (
            dict(mente_atual.get("turno_atual") or {})
            if isinstance(mente_atual, dict)
            else {}
        )
        normalizar_turno = ns.get("_normalizar_texto_com_apelidos")
'''

RUNTIME_ANCHOR_AFTER = '''        # P0_CAPACIDADE_READONLY_A1_20260816
        # Perguntas sobre o que a Laylay consegue fazer continuam SEM autorizar
        # a ação mencionada. O catálogo vivo é somente leitura e precisa poder
        # responder antes da barreira de mutação; caso contrário, a própria
        # proteção P0 devolve o turno à conversa e a LLM pode inventar uma
        # incapacidade. Um turno já autorizado nunca é consumido por esta porta.
        mente_atual = getattr(estado_runtime, "mental", {})
        turno_atual = (
            dict(mente_atual.get("turno_atual") or {})
            if isinstance(mente_atual, dict)
            else {}
        )
        responder_capacidade = ns.get("_responder_pergunta_capacidade_local")
        fala_capacidade = ""
        if (
            turno_atual.get("autoriza_execucao") is not True
            and callable(responder_capacidade)
        ):
            try:
                fala_capacidade = str(responder_capacidade(texto) or "").strip()
            except Exception as erro:
                print(
                    "⚠️ [P0:CAPACIDADE] consulta read-only falhou sem liberar "
                    f"mutação | {type(erro).__name__}: {erro}"
                )
        if fala_capacidade:
            print("🔎 [P0:CAPACIDADE] consulta segura tratada antes da barreira")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala_capacidade, "calma", 1)
            return True

        # Detectar uma intent não concede permissão para executá-la. Esta
        # barreira faz a rota determinística usar o mesmo dono do turno da LLM.
        normalizar_turno = ns.get("_normalizar_texto_com_apelidos")
'''

RUNTIME_LATE_BLOCK = '''        responder_capacidade = ns.get("_responder_pergunta_capacidade_local")
        fala_capacidade = responder_capacidade(texto) if callable(responder_capacidade) else ""
        if fala_capacidade:
            print("⚡ [PRIORIDADE:HABILIDADE] consulta sobre capacidade real")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala_capacidade, "calma", 1)
            return True
'''

TEST_INSERT_ANCHOR = '''    assert falas and "não fiz nada" in falas[-1].casefold()
    assert execucoes == []


@pytest.mark.parametrize("texto", (
    "você é só um chatbot?",
'''

TEST_INSERT_REPLACEMENT = '''    assert falas and "não fiz nada" in falas[-1].casefold()
    assert execucoes == []


@pytest.mark.parametrize(
    "texto",
    (
        "Você consegue apagar arquivos?",
        "Você consegue apagar um arquivo?",
    ),
)
def test_porta_prioritaria_responde_capacidade_de_exclusao_sem_executar(
    texto: str,
) -> None:
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)
    falas: list[str] = []
    execucoes: list[dict] = []
    estado = SimpleNamespace(mental={"turno_atual": turno})
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_responder_pergunta_capacidade_local": (
                lambda fala: mapa.responder_pergunta_capacidade(
                    fala,
                    turno=estado.mental["turno_atual"],
                )
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(comando) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert turno["autoriza_execucao"] is False
    assert runtime.processar_prioritarios(texto) is True
    assert falas
    assert "confirmo o alvo" in falas[-1].casefold()
    assert "lixeira" in falas[-1].casefold()
    assert execucoes == []


def test_ciclo_ia_para_antes_da_llm_quando_capacidade_readonly_responde() -> None:
    texto = "Você consegue apagar arquivos?"
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)
    falas: list[str] = []
    execucoes: list[dict] = []
    chamadas_llm: list[str] = []
    estado = SimpleNamespace(mental={"turno_atual": turno})
    imediato = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_responder_pergunta_capacidade_local": (
                lambda fala: mapa.responder_pergunta_capacidade(
                    fala,
                    turno=estado.mental["turno_atual"],
                )
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(comando) or True
            ),
        },
        loop_getter=lambda: None,
    )
    resposta = RespostaIARuntime(
        contexto_getter=lambda: {
            "marcar_inicio_turno": lambda *_args, **_kwargs: None,
            "obter_turno_atual": lambda: dict(turno),
            "processar_comandos_prioritarios": imediato.processar_prioritarios,
            "enviar_mensagem": lambda *_args, **_kwargs: (
                chamadas_llm.append(texto) or "{}"
            ),
        },
        log=lambda *_args, **_kwargs: None,
    )

    resposta.processar(texto)

    assert falas and "lixeira" in falas[-1].casefold()
    assert execucoes == []
    assert chamadas_llm == []


@pytest.mark.parametrize("texto", (
    "você é só um chatbot?",
'''


def run(
    cmd: list[str],
    *,
    cwd: Path,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"comando falhou rc={proc.returncode}: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def normalized_text(raw: bytes) -> tuple[str, bytes]:
    """Decodifica UTF-8 e devolve também o separador original predominante."""
    text = raw.decode("utf-8")
    newline = b"\r\n" if raw.count(b"\r\n") > 0 else b"\n"
    return text.replace("\r\n", "\n"), newline


def encode_preserving_newline(text: str, newline: bytes) -> bytes:
    clean = text.replace("\r\n", "\n")
    if newline == b"\r\n":
        clean = clean.replace("\n", "\r\n")
    return clean.encode("utf-8")


def replace_exact_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"ancora {label} deveria aparecer 1 vez, apareceu {count}; recusando"
        )
    return text.replace(old, new, 1)


def build_candidates(runtime_raw: bytes, test_raw: bytes) -> tuple[bytes, bytes]:
    runtime_text, runtime_nl = normalized_text(runtime_raw)
    test_text, test_nl = normalized_text(test_raw)

    runtime_text = replace_exact_once(
        runtime_text,
        RUNTIME_ANCHOR_BEFORE,
        RUNTIME_ANCHOR_AFTER,
        label="runtime_pre_p0",
    )
    runtime_text = replace_exact_once(
        runtime_text,
        RUNTIME_LATE_BLOCK,
        "",
        label="runtime_bloco_capacidade_tardio",
    )
    test_text = replace_exact_once(
        test_text,
        TEST_INSERT_ANCHOR,
        TEST_INSERT_REPLACEMENT,
        label="teste_regressao_capacidade_exclusao",
    )

    # Reanalise estrutural local: exatamente uma porta P0 de capacidade e
    # nenhuma copia tardia do bloco antigo podem sobreviver.
    if runtime_text.count("P0_CAPACIDADE_READONLY_A1_20260816") != 1:
        raise RuntimeError("marcador do Patch A nao ficou unico")
    if "⚡ [PRIORIDADE:HABILIDADE] consulta sobre capacidade real" in runtime_text:
        raise RuntimeError("bloco tardio antigo de capacidade ainda existe")
    if runtime_text.count('ns.get("_responder_pergunta_capacidade_local")') != 1:
        raise RuntimeError("respondedor de capacidade deveria ter um unico ponto no runtime")
    cap_idx = runtime_text.index("P0_CAPACIDADE_READONLY_A1_20260816")
    barrier_idx = runtime_text.index(
        "if bloqueia_execucao_operacional_prioritaria(", cap_idx
    )
    if cap_idx >= barrier_idx:
        raise RuntimeError("porta de capacidade nao ficou antes da barreira P0")
    capability_slice = runtime_text[cap_idx:barrier_idx]
    if "executar_intencao" in capability_slice or "_registrar_resultado_execucao" in capability_slice:
        raise RuntimeError("porta read-only ganhou caminho de execucao/registro operacional")

    ast.parse(runtime_text, filename=str(TARGET_RUNTIME))
    ast.parse(test_text, filename=str(TARGET_TEST))
    return (
        encode_preserving_newline(runtime_text, runtime_nl),
        encode_preserving_newline(test_text, test_nl),
    )


def atomic_write(path: Path, payload: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def assert_expected_red(proc: subprocess.CompletedProcess[str], *, label: str) -> None:
    combined = f"{proc.stdout}\n{proc.stderr}"
    if proc.returncode != 1 or "AssertionError" not in combined or "1 failed" not in combined:
        raise RuntimeError(
            f"{label} nao reproduziu o vermelho esperado antes do patch\n"
            f"rc={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".", help="raiz do repositorio Laylay")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()

    runtime_path = repo / TARGET_RUNTIME
    test_path = repo / TARGET_TEST
    red_path = repo / RED_TEST
    targets = [TARGET_RUNTIME.as_posix(), TARGET_TEST.as_posix()]

    print(f"[{PATCH_ID}] Patch A — capacidade read-only antes da P0")
    print(f"Repositorio: {repo}")

    head_proc = run(["git", "rev-parse", "HEAD"], cwd=repo)
    if head_proc.returncode != 0:
        print("ERRO: nao parece ser um repositorio Git valido.", file=sys.stderr)
        return 2
    head = head_proc.stdout.strip()
    if head != BASELINE_HEAD:
        print(
            f"ERRO: HEAD mudou. esperado={BASELINE_HEAD} atual={head}",
            file=sys.stderr,
        )
        return 3

    for rel in (TARGET_RUNTIME, TARGET_TEST):
        path = repo / rel
        if not path.is_file():
            print(f"ERRO: alvo ausente: {rel}", file=sys.stderr)
            return 4
        blob = run(["git", "rev-parse", f"HEAD:{rel.as_posix()}"], cwd=repo)
        expected = EXPECTED_BLOBS[rel.as_posix()]
        if blob.returncode != 0 or blob.stdout.strip() != expected:
            print(
                f"ERRO: blob da baseline divergiu em {rel}. "
                f"esperado={expected} atual={blob.stdout.strip() or 'indisponivel'}",
                file=sys.stderr,
            )
            return 5

    dirty = run(["git", "status", "--porcelain", "--", *targets], cwd=repo)
    if dirty.returncode != 0:
        print("ERRO: nao consegui verificar o estado dos alvos.", file=sys.stderr)
        return 6
    if dirty.stdout.strip():
        print(
            "ERRO: um alvo do Patch A possui mudancas locais. Recusando para "
            "preservar seu trabalho:\n" + dirty.stdout,
            file=sys.stderr,
        )
        return 7

    pre_changed_proc = run(["git", "diff", "--name-only"], cwd=repo)
    pre_cached_proc = run(["git", "diff", "--cached", "--name-only"], cwd=repo)
    if pre_changed_proc.returncode != 0 or pre_cached_proc.returncode != 0:
        print("ERRO: nao consegui fotografar o estado Git anterior.", file=sys.stderr)
        return 8
    pre_changed = {
        line.strip().replace("\\", "/")
        for line in pre_changed_proc.stdout.splitlines()
        if line.strip()
    }
    pre_cached = {
        line.strip().replace("\\", "/")
        for line in pre_cached_proc.stdout.splitlines()
        if line.strip()
    }

    if not red_path.is_file():
        print(
            f"ERRO: fotografia vermelha esperada nao existe: {RED_TEST}",
            file=sys.stderr,
        )
        return 9
    red_hash = sha256(red_path.read_bytes())
    if red_hash != EXPECTED_RED_SHA256:
        print(
            "ERRO: fotografia vermelha foi alterada desde a prova. "
            f"esperado={EXPECTED_RED_SHA256} atual={red_hash}",
            file=sys.stderr,
        )
        return 10

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = repo / ".laylay_patch_backups" / f"{PATCH_ID}_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    manifest_path = backup_dir / "manifest.json"

    runtime_raw = runtime_path.read_bytes()
    test_raw = test_path.read_bytes()

    manifest: dict[str, Any] = {
        "patch_id": PATCH_ID,
        "baseline_head": BASELINE_HEAD,
        "head_observado": head,
        "targets": {
            TARGET_RUNTIME.as_posix(): EXPECTED_BLOBS[TARGET_RUNTIME.as_posix()],
            TARGET_TEST.as_posix(): EXPECTED_BLOBS[TARGET_TEST.as_posix()],
        },
        "red_test_sha256": red_hash,
        "started_at": dt.datetime.now().astimezone().isoformat(),
        "status": "iniciado",
        "preflight": {},
        "validacoes": {},
    }
    save_manifest(manifest_path, manifest)

    backup_runtime = backup_dir / TARGET_RUNTIME
    backup_test = backup_dir / TARGET_TEST
    backup_runtime.parent.mkdir(parents=True, exist_ok=True)
    backup_test.parent.mkdir(parents=True, exist_ok=True)
    backup_runtime.write_bytes(runtime_raw)
    backup_test.write_bytes(test_raw)

    applied = False
    try:
        print("\n=== PREFLIGHT VERMELHO ===")
        pre_red_exact = run(
            [sys.executable, "-m", "pytest", "-q", RED_NODE_EXATO], cwd=repo
        )
        print(pre_red_exact.stdout, end="")
        if pre_red_exact.stderr:
            print(pre_red_exact.stderr, end="", file=sys.stderr)
        assert_expected_red(pre_red_exact, label="fotografia vermelha exata")

        pre_red_tracked = run(
            [sys.executable, "-m", "pytest", "-q", RED_NODE_TRACKED], cwd=repo
        )
        print(pre_red_tracked.stdout, end="")
        if pre_red_tracked.stderr:
            print(pre_red_tracked.stderr, end="", file=sys.stderr)
        assert_expected_red(pre_red_tracked, label="regressao rastreada existente")
        manifest["preflight"] = {
            "red_exato": {
                "returncode": pre_red_exact.returncode,
                "stdout": pre_red_exact.stdout,
                "stderr": pre_red_exact.stderr,
            },
            "red_tracked": {
                "returncode": pre_red_tracked.returncode,
                "stdout": pre_red_tracked.stdout,
                "stderr": pre_red_tracked.stderr,
            },
        }
        save_manifest(manifest_path, manifest)

        runtime_candidate, test_candidate = build_candidates(runtime_raw, test_raw)
        manifest["sha256_antes"] = {
            TARGET_RUNTIME.as_posix(): sha256(runtime_raw),
            TARGET_TEST.as_posix(): sha256(test_raw),
        }
        manifest["sha256_candidato"] = {
            TARGET_RUNTIME.as_posix(): sha256(runtime_candidate),
            TARGET_TEST.as_posix(): sha256(test_candidate),
        }

        candidate_runtime_path = backup_dir / "candidate" / TARGET_RUNTIME
        candidate_test_path = backup_dir / "candidate" / TARGET_TEST
        candidate_runtime_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_test_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_runtime_path.write_bytes(runtime_candidate)
        candidate_test_path.write_bytes(test_candidate)

        # Candidate syntax check sem tocar no worktree.
        for label, candidate in (
            ("runtime", candidate_runtime_path),
            ("test", candidate_test_path),
        ):
            pyc = backup_dir / f"candidate_{label}.pyc"
            proc = run(
                [
                    sys.executable,
                    "-c",
                    "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)",
                    str(candidate),
                    str(pyc),
                ],
                cwd=repo,
            )
            manifest["validacoes"][f"candidate_py_compile_{label}"] = {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            if proc.returncode != 0:
                raise RuntimeError(f"py_compile do candidato {label} falhou")

        atomic_write(runtime_path, runtime_candidate)
        atomic_write(test_path, test_candidate)
        applied = True

        # Garante que so os dois alvos previstos mudaram entre os arquivos
        # rastreados. O teste vermelho deliberado continua untracked/intocado.
        changed = run(["git", "diff", "--name-only"], cwd=repo, check=True)
        cached_after = run(["git", "diff", "--cached", "--name-only"], cwd=repo, check=True)
        changed_set = {
            line.strip().replace("\\", "/")
            for line in changed.stdout.splitlines()
            if line.strip()
        }
        cached_after_set = {
            line.strip().replace("\\", "/")
            for line in cached_after.stdout.splitlines()
            if line.strip()
        }
        target_set = set(targets)
        expected_changed = pre_changed | target_set
        if changed_set != expected_changed:
            raise RuntimeError(
                "escopo do diff inesperado: "
                f"antes={sorted(pre_changed)} depois={sorted(changed_set)} "
                f"esperado={sorted(expected_changed)}"
            )
        if cached_after_set != pre_cached:
            raise RuntimeError(
                "o patch alterou o estado staged inesperadamente: "
                f"antes={sorted(pre_cached)} depois={sorted(cached_after_set)}"
            )

        diff_check = run(["git", "diff", "--check", "--", *targets], cwd=repo)
        manifest["validacoes"]["git_diff_check"] = {
            "returncode": diff_check.returncode,
            "stdout": diff_check.stdout,
            "stderr": diff_check.stderr,
        }
        if diff_check.returncode != 0:
            raise RuntimeError("git diff --check falhou")

        diff = run(["git", "diff", "--", *targets], cwd=repo, check=True)
        (backup_dir / "patch_candidate.diff").write_text(
            diff.stdout, encoding="utf-8", newline="\n"
        )

        # AST novamente a partir do arquivo efetivamente escrito.
        for rel in (TARGET_RUNTIME, TARGET_TEST):
            text, _nl = normalized_text((repo / rel).read_bytes())
            ast.parse(text, filename=rel.as_posix())

        print("\n=== TESTES FOCADOS POS-PATCH ===")
        focused = run(
            [sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS],
            cwd=repo,
        )
        print(focused.stdout, end="")
        if focused.stderr:
            print(focused.stderr, end="", file=sys.stderr)
        manifest["validacoes"]["pytest_focado"] = {
            "returncode": focused.returncode,
            "stdout": focused.stdout,
            "stderr": focused.stderr,
            "targets": FOCUSED_TESTS,
        }
        if focused.returncode != 0:
            raise RuntimeError("pytest focado falhou")

        # Prova adicional: o teste vermelho exato precisa ter mudado de estado
        # e agora passar sozinho; outros vermelhos B/C nao sao executados aqui.
        exact_after = run(
            [sys.executable, "-m", "pytest", "-q", RED_NODE_EXATO], cwd=repo
        )
        manifest["validacoes"]["red_exato_agora_verde"] = {
            "returncode": exact_after.returncode,
            "stdout": exact_after.stdout,
            "stderr": exact_after.stderr,
        }
        if exact_after.returncode != 0:
            raise RuntimeError("o vermelho exato de capacidade nao ficou verde")

        # Releitura final do contrato de seguranca no codigo resultante.
        final_runtime, _ = normalized_text(runtime_path.read_bytes())
        final_test, _ = normalized_text(test_path.read_bytes())
        if "P0_CAPACIDADE_READONLY_A1_20260816" not in final_runtime:
            raise RuntimeError("marcador final ausente")
        if 'if bloqueia_execucao_operacional_prioritaria(' not in final_runtime:
            raise RuntimeError("barreira P0 desapareceu do runtime")
        if 'turno_atual.get("autoriza_execucao") is not True' not in final_runtime:
            raise RuntimeError("porta read-only perdeu o guard de autorizacao")
        cap_idx = final_runtime.index("P0_CAPACIDADE_READONLY_A1_20260816")
        barrier_idx = final_runtime.index(
            "if bloqueia_execucao_operacional_prioritaria(", cap_idx
        )
        if cap_idx >= barrier_idx:
            raise RuntimeError("ordem final capacidade/P0 esta incorreta")
        capability_slice = final_runtime[cap_idx:barrier_idx]
        if "executar_intencao" in capability_slice or "_registrar_resultado_execucao" in capability_slice:
            raise RuntimeError("porta final de capacidade deixou de ser read-only")
        if "test_porta_prioritaria_responde_capacidade_de_exclusao_sem_executar" not in final_test:
            raise RuntimeError("regressao rastreada nao foi gravada")
        if "test_ciclo_ia_para_antes_da_llm_quando_capacidade_readonly_responde" not in final_test:
            raise RuntimeError("regressao de composicao ate RespostaIARuntime nao foi gravada")

        manifest["status"] = "ok"
        manifest["finished_at"] = dt.datetime.now().astimezone().isoformat()
        manifest["sha256_depois"] = {
            TARGET_RUNTIME.as_posix(): sha256(runtime_path.read_bytes()),
            TARGET_TEST.as_posix(): sha256(test_path.read_bytes()),
        }
        manifest["diff_file"] = str(backup_dir / "patch_candidate.diff")
        save_manifest(manifest_path, manifest)

        print("\n" + "=" * 60)
        print("PATCH A APLICADO E VALIDADO")
        print(f"HEAD travado: {BASELINE_HEAD}")
        print("Barreira P0: preservada")
        print("Execucao por pergunta de capacidade: continua proibida")
        print("Consulta read-only de capacidade: agora vence antes da P0")
        print(f"Manifest: {manifest_path}")
        print(f"Diff: {backup_dir / 'patch_candidate.diff'}")
        print("Nenhum git add/commit/push foi executado.")
        print("NAO COMMITAR AINDA: envie a saida e o manifest/diff para reanalise.")
        return 0

    except Exception as exc:
        manifest["status"] = "rollback"
        manifest["erro"] = f"{type(exc).__name__}: {exc}"
        manifest["finished_at"] = dt.datetime.now().astimezone().isoformat()
        if applied:
            try:
                shutil.copy2(backup_runtime, runtime_path)
                shutil.copy2(backup_test, test_path)
                manifest["rollback_ok"] = (
                    runtime_path.read_bytes() == runtime_raw
                    and test_path.read_bytes() == test_raw
                )
            except Exception as rollback_exc:
                manifest["rollback_ok"] = False
                manifest["rollback_erro"] = (
                    f"{type(rollback_exc).__name__}: {rollback_exc}"
                )
        else:
            manifest["rollback_ok"] = True
        save_manifest(manifest_path, manifest)
        print(f"\nERRO: Patch A recusado: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"Manifest: {manifest_path}", file=sys.stderr)
        if applied:
            print(
                "Rollback automatico executado; confira rollback_ok no manifest.",
                file=sys.stderr,
            )
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
