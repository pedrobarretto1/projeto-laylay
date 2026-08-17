from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PATCH_ID = "PATCH_R1_R2_V2_0_1_ORDINAL_NARRATIVO_LOCKFIX_20260816"
EXPECTED_HEAD = "a619a71ff5d1976fb8a25561ab2512ec291e31e8"
V2_TEST = "tests/test_red_r1_r2_autoridade_frescor_v2_3_1.py"
V2_SHA256 = "d89971098276dba74179bfe003332f38eaad85a1524a05269873b0b147fac099"
BASE_TEST = "tests/test_regressao_patch20_r1_r2.py"
BASE_TEST_SHA256 = "a23fc6a2c53557b7b46543d87da69f081b1efd2753f6b8bdcf17df8b0e3ba84d"
UPDATED_TEST_SHA256 = "c144255e724094278ac149f9515b7883160e6081adda833bc0fd9b2edece17ed"
AUDIT_RED_ROOT = "test_red_patch20_ordinal_narrativo_auditoria.py"
AUDIT_RED_SHA256 = "cf1eade28ec0134b2bac148e9f4075a456b839475ca6a27bf74a0720f6efd2a2"

# Estado exato do Patch 2.0 aplicado. Os SHAs são de `git diff -- <arquivo>` isolado;
# o último arquivo rastreado não inclui a newline separadora do artefato combinado.
PATCH20_DIFF_SHA256 = {
    "mente_laylay/arquivos/roteador_arquivos.py": "f1b4be30702bd248710658803e0c97cdf9dbe4a1728d17009f36237f8fb90927",
    "mente_laylay/autonomia/comandos_imediatos.py": "019587b7cf5898b482613dbc88141a376c4e33a82795753c76c3788dd3261cb5",
    "mente_laylay/autonomia/coordenador_intencao.py": "36b473cdec80532f792fa3aa9c9dcdd9536b832e88b18c3b40f72268c917ccf0",
    "mente_laylay/cognicao/modalidade_turno.py": "8e90db52bcc81f4bf8242add67dc35976fe360a0ab31a6508f5c447507d03610",
    "mente_laylay/cognicao/retrato_turno.py": "932f1d610c84547f3b7e6731a95867a1ddafb8274cfb4e7e3f0abccc8d38a695",
    "tests/test_contexto_execucao_arquivos.py": "81d1a9d507ae4aa6d21eac885bb6d63bfa874ab802baaf80749a1169719c5362",
}

UPDATED_TEST = 'from __future__ import annotations\n\nimport pytest\n\nfrom mente_laylay.autonomia.comandos_imediatos import (\n    _candidato_arquivo_prioritario_autorizado,\n)\nfrom mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno\nfrom mente_laylay.memoria_mental.continuidade_contexto import (\n    registrar_estrutura_arquivo_recente,\n)\n\n\ndef _turno(autoriza: bool) -> dict:\n    return {\n        "id": 22001,\n        "modalidade": "comando" if autoriza else "conversa",\n        "modalidade_geral": "comando" if autoriza else "conversa",\n        "ato_principal": "comando" if autoriza else "conversa",\n        "autoriza_execucao": bool(autoriza),\n        "acao_explicita": bool(autoriza),\n    }\n\n\ndef test_patch20_restore_direto_autoriza_sem_liberar_molduras_protegidas() -> None:\n    direto = classificar_modalidade_turno("Restaura o último arquivo.")\n    negativo = classificar_modalidade_turno("Não restaura o último arquivo.")\n    instrucao = classificar_modalidade_turno("Como eu restauraria esse arquivo?")\n    capacidade = classificar_modalidade_turno("Você consegue restaurar arquivos?")\n\n    assert direto["autoriza_execucao"] is True\n    assert str(direto["modalidade"]) == "comando"\n    assert negativo["autoriza_execucao"] is False\n    assert instrucao["autoriza_execucao"] is False\n    assert capacidade["autoriza_execucao"] is False\n\n\ndef test_patch20_readonly_prioritario_nao_depende_de_autorizacao_de_mutacao() -> None:\n    candidato = {\n        "intent": "FILE_READ",\n        "params": {"caminho": "C:/tmp/seguro.txt", "alvo": "seguro.txt"},\n    }\n    assert _candidato_arquivo_prioritario_autorizado(\n        candidato,\n        "Leia ele.",\n        _turno(False),\n        {},\n    ) is True\n\n\ndef test_patch20_efeito_prioritario_nao_ganha_autoridade_do_detector() -> None:\n    candidato = {\n        "intent": "CREATE_FILE",\n        "params": {\n            "alvo": "C:/tmp/seguro.txt",\n            "conteudo": "linha",\n            "editar_existente": True,\n            "modo_escrita": "append",\n        },\n    }\n    assert _candidato_arquivo_prioritario_autorizado(\n        candidato,\n        "Acrescente linha nele.",\n        _turno(False),\n        {},\n    ) is False\n\n\ndef test_patch20_ordinal_fresco_exige_prova_textual_indice_e_caminho(tmp_path) -> None:\n    primeiro = str(tmp_path / "primeiro.txt")\n    segundo = str(tmp_path / "segundo.txt")\n    estado = registrar_estrutura_arquivo_recente(\n        {},\n        {\n            "tipo": "pesquisa_semantica",\n            "consulta": "documentacao python",\n            "resultados": [primeiro, segundo],\n            "nomes": ["primeiro.txt", "segundo.txt"],\n        },\n    )\n    candidato = {\n        "intent": "FILE_OPEN_RESULT",\n        "params": {\n            "caminho": primeiro,\n            "alvo": "primeiro.txt",\n            "indice": 1,\n        },\n    }\n\n    assert _candidato_arquivo_prioritario_autorizado(\n        candidato,\n        "o primeiro",\n        _turno(False),\n        estado,\n    ) is True\n    assert _candidato_arquivo_prioritario_autorizado(\n        candidato,\n        "abre o primeiro resultado",\n        _turno(False),\n        estado,\n    ) is True\n    assert _candidato_arquivo_prioritario_autorizado(\n        candidato,\n        "quasar ordinal",\n        _turno(False),\n        estado,\n    ) is False\n\n    divergente = {\n        **candidato,\n        "params": {**candidato["params"], "caminho": segundo},\n    }\n    assert _candidato_arquivo_prioritario_autorizado(\n        divergente,\n        "o primeiro",\n        _turno(False),\n        estado,\n    ) is False\n\n\n@pytest.mark.parametrize(\n    "texto",\n    [\n        "foi meu primeiro jogo",\n        "não foi o primeiro",\n        "eu fiquei em 1 lugar",\n    ],\n)\ndef test_patch20_ordinal_narrativo_nao_ganha_autoridade(\n    tmp_path,\n    texto: str,\n) -> None:\n    primeiro = str(tmp_path / "primeiro.txt")\n    segundo = str(tmp_path / "segundo.txt")\n    estado = registrar_estrutura_arquivo_recente(\n        {},\n        {\n            "tipo": "pesquisa_semantica",\n            "consulta": "documentacao python",\n            "resultados": [primeiro, segundo],\n            "nomes": ["primeiro.txt", "segundo.txt"],\n        },\n    )\n    candidato = {\n        "intent": "FILE_OPEN_RESULT",\n        "params": {\n            "caminho": primeiro,\n            "alvo": "primeiro.txt",\n            "indice": 1,\n        },\n    }\n\n    assert _candidato_arquivo_prioritario_autorizado(\n        candidato,\n        texto,\n        _turno(False),\n        estado,\n    ) is False\n'


def run(cmd: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=str(cwd), text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=merged,
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _python_executable_in_venv(venv: Path) -> Path | None:
    candidatos = [
        venv / "Scripts" / "python.exe",
        venv / "bin" / "python",
    ]
    return next((p for p in candidatos if p.is_file()), None)


def resolver_runner_pytest(repo: Path) -> tuple[list[str], list[dict[str, object]]]:
    candidatos: list[tuple[str, list[str]]] = []
    vistos: set[tuple[str, ...]] = set()

    def adicionar(rotulo: str, comando: list[str]) -> None:
        chave = tuple(comando)
        if comando and chave not in vistos:
            vistos.add(chave)
            candidatos.append((rotulo, comando))

    virtual_env = str(os.environ.get("VIRTUAL_ENV") or "").strip()
    if virtual_env:
        py = _python_executable_in_venv(Path(virtual_env))
        if py:
            adicionar("VIRTUAL_ENV", [str(py), "-m", "pytest"])

    for raiz, rotulo in ((repo, "repo"), (repo.parent, "repo.parent")):
        for nome in (".venv314", ".venv", "venv314", "venv"):
            py = _python_executable_in_venv(raiz / nome)
            if py:
                adicionar(f"{rotulo}/{nome}", [str(py), "-m", "pytest"])

    if sys.executable:
        adicionar("sys.executable", [sys.executable, "-m", "pytest"])

    for nome in ("python", "python3", "py"):
        exe = shutil.which(nome)
        if exe:
            adicionar(f"PATH:{nome}", [exe, "-m", "pytest"])

    pytest_exe = shutil.which("pytest") or shutil.which("pytest.exe")
    if pytest_exe:
        adicionar("PATH:pytest", [pytest_exe])

    diagnostico: list[dict[str, object]] = []
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": "-p no:cacheprovider"}
    for rotulo, base in candidatos:
        proc = run([*base, "--version"], repo, env=env)
        diagnostico.append({
            "rotulo": rotulo,
            "comando": base,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[:500],
            "stderr": proc.stderr.strip()[:500],
        })
        if proc.returncode == 0:
            return base, diagnostico
    return [], diagnostico


def git_diff_sha(repo: Path, rel: str) -> tuple[str, str]:
    proc = run(["git", "diff", "--no-ext-diff", "--", rel], repo)
    if proc.returncode != 0:
        raise RuntimeError(f"git diff falhou para {rel}: {proc.stderr.strip()}")
    return sha256_bytes(proc.stdout.encode("utf-8")), proc.stdout


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"anchor {label}: esperado 1, observado {n}")
    return text.replace(old, new, 1)


def validar_sem_whitespace_ruim(texto: str, rel: str) -> None:
    if not texto.endswith("\n"):
        raise RuntimeError(f"{rel} sem newline final")
    ruins = [i for i, linha in enumerate(texto.splitlines(), 1) if linha.rstrip() != linha]
    if ruins:
        raise RuntimeError(f"{rel} tem trailing whitespace nas linhas {ruins[:10]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    head = run(["git", "rev-parse", "HEAD"], repo)
    if head.returncode != 0 or head.stdout.strip() != EXPECTED_HEAD:
        print("ERRO: HEAD mudou; microfix recusado.")
        print("Esperado:", EXPECTED_HEAD)
        print("Observado:", head.stdout.strip() or head.stderr.strip())
        return 2

    pytest_base, pytest_probe = resolver_runner_pytest(repo)
    if not pytest_base:
        print("ERRO: nenhum runner pytest válido encontrado; nada foi alterado.")
        return 3
    print("🧪 Runner pytest validado:", " ".join(pytest_base))

    # Trava o estado completo do Patch 2.0 antes de mexer em qualquer coisa.
    observed_diffs: dict[str, str] = {}
    for rel, esperado in PATCH20_DIFF_SHA256.items():
        observado, _ = git_diff_sha(repo, rel)
        observed_diffs[rel] = observado
        if observado != esperado:
            print(f"ERRO: {rel} não está mais no estado exato do Patch 2.0.")
            print("Esperado diff SHA:", esperado)
            print("Observado diff SHA:", observado)
            return 4

    base_test = repo / BASE_TEST
    if not base_test.is_file() or sha256_file(base_test) != BASE_TEST_SHA256:
        print("ERRO: teste pós-fix do Patch 2.0 mudou; microfix recusado.")
        return 5

    v2 = repo / V2_TEST
    if not v2.is_file() or sha256_file(v2) != V2_SHA256:
        print("ERRO: fotografia V2 ausente ou alterada.")
        return 6

    audit_root = repo / AUDIT_RED_ROOT
    audit_root_incluido = False
    if audit_root.exists():
        if sha256_file(audit_root) != AUDIT_RED_SHA256:
            print("ERRO: red ordinal da raiz existe, mas foi alterado.")
            return 7
        audit_root_incluido = True

    target = repo / "mente_laylay/autonomia/comandos_imediatos.py"
    before_target = target.read_bytes()
    before_test = base_test.read_bytes()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    artifact_dir = repo.parent / ".laylay_patch_artifacts" / f"{repo.name}_{PATCH_ID}_{stamp}"
    artifact_dir.mkdir(parents=True, exist_ok=False)
    backup = artifact_dir / "backup"
    backup.mkdir()
    (backup / "comandos_imediatos.py").write_bytes(before_target)
    (backup / "test_regressao_patch20_r1_r2.py").write_bytes(before_test)

    manifest_path = artifact_dir / "manifest.json"
    microdiff_path = artifact_dir / "microfix_candidate.diff"
    full_diff_path = artifact_dir / "patch20_after_microfix.diff"
    pytest_log = artifact_dir / "pytest_focused.txt"

    test_result: dict[str, object] = {}

    def write_manifest(status: str, error: str = "") -> None:
        payload = {
            "patch_id": PATCH_ID,
            "status": status,
            "error": error,
            "head": head.stdout.strip(),
            "patch20_diff_sha_expected": PATCH20_DIFF_SHA256,
            "patch20_diff_sha_observed_before": observed_diffs,
            "base_test_sha_before": BASE_TEST_SHA256,
            "test_sha_after": sha256_file(base_test) if base_test.exists() else "",
            "audit_red_root_included": audit_root_incluido,
            "pytest_runner": pytest_base,
            "pytest_probe": pytest_probe,
            "pytest": test_result,
            "microfix_diff": str(microdiff_path),
            "full_patch20_diff_after": str(full_diff_path),
            "automatic_commit": False,
            "automatic_push": False,
        }
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    try:
        src = before_target.decode("utf-8")
        src = replace_once(
            src,
            """from mente_laylay.cognicao.referencias_linguagem import (
    extrair_indice_referencia_ordinal,
)""",
            """from mente_laylay.cognicao.referencias_linguagem import (
    extrair_indice_referencia_ordinal,
    valor_e_referencia_contextual,
)""",
            "import referencia contextual",
        )
        src = replace_once(
            src,
            """    indice_texto = extrair_indice_referencia_ordinal(str(texto or ""))
    if indice_texto is None:
        indice_texto = extrair_indice_referencia_ordinal(
            f"abre {str(texto or '').strip()}"
        )
    if indice_texto is None or indice_candidato != indice_texto:
""",
            """    texto_ordinal = str(texto or "").strip()
    indice_texto = extrair_indice_referencia_ordinal(texto_ordinal)
    if indice_texto is None and valor_e_referencia_contextual(texto_ordinal):
        indice_texto = extrair_indice_referencia_ordinal(
            f"abre {texto_ordinal}"
        )
    if indice_texto is None or indice_candidato != indice_texto:
""",
            "fallback ordinal só para referência contextual",
        )
        ast.parse(src, filename=str(target))
        validar_sem_whitespace_ruim(src, str(target))
        target.write_bytes(src.encode("utf-8"))

        if sha256_bytes(UPDATED_TEST.encode("utf-8")) != UPDATED_TEST_SHA256:
            raise RuntimeError("payload do teste embutido não bate com SHA esperado")
        ast.parse(UPDATED_TEST, filename=BASE_TEST)
        validar_sem_whitespace_ruim(UPDATED_TEST, BASE_TEST)
        base_test.write_bytes(UPDATED_TEST.encode("utf-8"))
        if sha256_file(base_test) != UPDATED_TEST_SHA256:
            raise RuntimeError("teste pós-fix gravado com bytes inesperados")

        check = run(["git", "diff", "--check", "--", "mente_laylay/autonomia/comandos_imediatos.py"], repo)
        if check.returncode != 0:
            raise RuntimeError("git diff --check falhou: " + check.stdout + check.stderr)

        delta = "".join(difflib.unified_diff(
            before_target.decode("utf-8").splitlines(True),
            target.read_text(encoding="utf-8").splitlines(True),
            fromfile="a/mente_laylay/autonomia/comandos_imediatos.py",
            tofile="b/mente_laylay/autonomia/comandos_imediatos.py",
        ))
        delta += "".join(difflib.unified_diff(
            before_test.decode("utf-8").splitlines(True),
            base_test.read_text(encoding="utf-8").splitlines(True),
            fromfile="a/tests/test_regressao_patch20_r1_r2.py",
            tofile="b/tests/test_regressao_patch20_r1_r2.py",
        ))
        microdiff_path.write_text(delta, encoding="utf-8", newline="\n")

        full = run([
            "git", "diff", "--no-ext-diff", "--",
            *PATCH20_DIFF_SHA256.keys(),
        ], repo)
        full_diff_path.write_text(full.stdout, encoding="utf-8", newline="\n")

        pytest_paths = [
            V2_TEST,
            BASE_TEST,
            "tests/test_p0_autorizacao_modalidade.py",
            "tests/test_regressao_consciencia_capacidades.py",
            "tests/test_contexto_execucao_arquivos.py",
        ]
        if audit_root_incluido:
            pytest_paths.append(AUDIT_RED_ROOT)

        env = {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_ADDOPTS": "-p no:cacheprovider",
        }
        proc = run([*pytest_base, "-q", *pytest_paths], repo, env=env)
        pytest_log.write_text(
            "--- STDOUT ---\n" + proc.stdout + "\n--- STDERR ---\n" + proc.stderr,
            encoding="utf-8", newline="\n",
        )
        test_result = {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "log": str(pytest_log),
            "paths": pytest_paths,
        }
        if proc.returncode != 0:
            raise RuntimeError("pytest focado falhou")

        write_manifest("ok")
        print("=" * 78)
        print("🥩 MICROFIX 2.0.1 ORDINAL APLICADO E REGRESSÕES VERDES")
        print("=" * 78)
        print("HEAD:", EXPECTED_HEAD)
        print("Produção alterada: mente_laylay/autonomia/comandos_imediatos.py")
        print("Teste atualizado:", BASE_TEST)
        print("SHA teste:", UPDATED_TEST_SHA256)
        print("Manifest:", manifest_path)
        print("Microdiff:", microdiff_path)
        print("Diff Patch 2.0 completo:", full_diff_path)
        print("Log pytest:", pytest_log)
        print("Commit/push automático: NÃO")
        return 0

    except Exception as exc:
        target.write_bytes(before_target)
        base_test.write_bytes(before_test)
        write_manifest("rollback", f"{type(exc).__name__}: {exc}")
        print("=" * 78)
        print("🛑 MICROFIX 2.0.1 REVERTIDO AUTOMATICAMENTE")
        print("=" * 78)
        print(f"{type(exc).__name__}: {exc}")
        print("Estado restaurado: Patch 2.0 aplicado, sem o microfix.")
        print("Manifest:", manifest_path)
        print("Commit/push automático: NÃO")
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
