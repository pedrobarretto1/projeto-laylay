#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0_REVISAO_INTRA_TURNO_B1_2_1_20260816

Corrige o contrato de identidade do plano após uma revisão intra-turno:

- a cognição/planejamento continua usando texto_cognitivo (proposta final);
- plano["texto_usuario"] volta a identificar a fala original;
- plano["texto_operacional_efetivo"] registra separadamente a visão revisada;
- metadados da revisão ficam disponíveis no plano para auditoria;
- não altera runner, executores, roteadores, Patch A ou armazenamento de resultados.

O patcher:
- trava o HEAD e o blob exatos estudados;
- recusa arquivos-alvo sujos;
- cria backup + manifest + diff;
- valida AST/py_compile;
- roda git diff --check;
- roda testes focados;
- desfaz automaticamente em caso de falha;
- NÃO faz commit nem push.
"""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PATCH_ID = "P0_REVISAO_INTRA_TURNO_B1_2_1_20260816"
EXPECTED_HEAD = "31b6b20f01df70707d3e50944a74532cfe696e15"

TARGET = Path("mente_laylay/cognicao/orquestrador_turno_runtime.py")
NEW_TEST = Path("tests/test_identidade_plano_revisao_b1_2.py")

# Git blob SHA do arquivo no HEAD estudado.
EXPECTED_BLOB = "ca87f1ebabe45c6a92887d3657801a05d093c205"

MARKER = "P0_REVISAO_INTRA_TURNO_B1_2_1_20260816"

ANCHOR_HELPER = """def _normalizar_origem_entrada(origem: object) -> str:
    valor = str(origem or 'desconhecida').strip().casefold()
    return valor if valor in _ORIGENS_ENTRADA_VALIDAS else 'desconhecida'


def iniciar_planejamento_turno(
"""

REPLACEMENT_HELPER = """def _normalizar_origem_entrada(origem: object) -> str:
    valor = str(origem or 'desconhecida').strip().casefold()
    return valor if valor in _ORIGENS_ENTRADA_VALIDAS else 'desconhecida'


# P0_REVISAO_INTRA_TURNO_B1_2_1_20260816
def alinhar_identidade_plano_revisao(
    plano: dict,
    *,
    texto_original: str,
    texto_operacional_efetivo: str = '',
    revisao_intra_turno: dict | None = None,
) -> dict:
    \"""Separa a identidade pública do turno de sua visão operacional revisada.

    O planejador deve continuar recebendo a proposta final consolidada para não
    reintroduzir ações/alvos descartados. Depois do planejamento, porém,
    ``texto_usuario`` volta a representar a fala que realmente originou o
    turno. A visão operacional fica em um campo próprio e auditável.
    \"""
    resultado = dict(plano or {})
    resultado['texto_usuario'] = str(texto_original or '').strip()[:500]

    revisao = dict(revisao_intra_turno or {})
    if bool(revisao.get('detectada')):
        resultado['texto_operacional_efetivo'] = str(
            texto_operacional_efetivo or ''
        ).strip()[:500]
        resultado['revisao_intra_turno'] = revisao

    return resultado


def iniciar_planejamento_turno(
"""

ANCHOR_PLAN = """    plano = ns['_planejar_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())
    evidencia_habilidades_getter = ns.get('_evidencia_habilidades_turno_mente')
"""

REPLACEMENT_PLAN = """    plano = ns['_planejar_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())
    # O plano nasce semanticamente da proposta final, mas sua identidade pública
    # pertence à fala original. Não confundir conteúdo operacional com RG do turno.
    plano = alinhar_identidade_plano_revisao(
        plano,
        texto_original=texto,
        texto_operacional_efetivo=texto_efetivo,
        revisao_intra_turno=revisao_intra_turno,
    )
    evidencia_habilidades_getter = ns.get('_evidencia_habilidades_turno_mente')
"""

TEST_CONTENT = r"""# P0_REVISAO_INTRA_TURNO_B1_2_1_20260816
from __future__ import annotations

import inspect

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    _iniciar_planejamento_turno,
    alinhar_identidade_plano_revisao,
)
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno


def _plano_para_texto_efetivo(texto_efetivo: str) -> dict:
    turno = classificar_modalidade_turno(
        texto_efetivo,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
    )
    return planejar_turno(texto_efetivo, turno=turno, mente={})


def test_plano_preserva_fala_original_sem_reintroduzir_alvo_descartado() -> None:
    original = "Abre o Opera... não, abre a Calculadora."
    revisao = resolver_revisao_intra_turno(original)

    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is False
    efetivo = revisao["texto_operacional_efetivo"]
    assert efetivo == "abre a Calculadora"

    plano_semantico = _plano_para_texto_efetivo(efetivo)
    assert plano_semantico["texto_usuario"] == efetivo

    plano = alinhar_identidade_plano_revisao(
        plano_semantico,
        texto_original=original,
        texto_operacional_efetivo=efetivo,
        revisao_intra_turno=revisao,
    )

    # Identidade/correlação: fala realmente recebida.
    assert plano["texto_usuario"] == original

    # Cognição operacional: somente a proposta final.
    assert plano["texto_operacional_efetivo"] == efetivo
    assert plano["revisao_intra_turno"]["tipo"] == "substituicao_comando"
    assert plano["requer_execucao"] is True

    atos = " ".join(str(item.get("texto") or "") for item in plano["atos"]).casefold()
    assert "calculadora" in atos
    assert "opera" not in atos


def test_plano_de_revisao_musical_guarda_original_e_final_separados() -> None:
    original = "Pausa a música... esquece, continua tocando."
    revisao = resolver_revisao_intra_turno(original)
    efetivo = revisao["texto_operacional_efetivo"]

    plano = alinhar_identidade_plano_revisao(
        {"texto_usuario": efetivo, "requer_execucao": True},
        texto_original=original,
        texto_operacional_efetivo=efetivo,
        revisao_intra_turno=revisao,
    )

    assert plano["texto_usuario"] == original
    assert plano["texto_operacional_efetivo"] == "continua música"
    assert plano["revisao_intra_turno"]["tipo"] == "substituicao_acao"


def test_cancelamento_mantem_identidade_original_e_visao_operacional_vazia() -> None:
    original = "Apaga o arquivo segredo.txt... não apaga."
    revisao = resolver_revisao_intra_turno(original)

    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is True

    plano = alinhar_identidade_plano_revisao(
        {"texto_usuario": original, "requer_execucao": False},
        texto_original=original,
        texto_operacional_efetivo=revisao["texto_operacional_efetivo"],
        revisao_intra_turno=revisao,
    )

    assert plano["texto_usuario"] == original
    assert plano["texto_operacional_efetivo"] == ""
    assert plano["revisao_intra_turno"]["cancelada"] is True
    assert plano["requer_execucao"] is False


def test_turno_sem_revisao_nao_inventa_metadado_de_revisao() -> None:
    original = "Abre a Calculadora."
    plano = alinhar_identidade_plano_revisao(
        {"texto_usuario": original, "dominio": "sistema"},
        texto_original=original,
        texto_operacional_efetivo="",
        revisao_intra_turno={
            "detectada": False,
            "resolvida": False,
            "texto_operacional_efetivo": "",
        },
    )

    assert plano["texto_usuario"] == original
    assert "texto_operacional_efetivo" not in plano
    assert "revisao_intra_turno" not in plano
    assert plano["dominio"] == "sistema"


def test_alinhamento_ocorre_depois_do_planejamento_e_antes_dos_consumidores() -> None:
    fonte = inspect.getsource(_iniciar_planejamento_turno)

    indice_planejamento = fonte.index(
        "plano = ns['_planejar_turno_mente'](texto_cognitivo"
    )
    indice_alinhamento = fonte.index(
        "plano = alinhar_identidade_plano_revisao("
    )
    indice_evidencia = fonte.index(
        "evidencia_habilidades_getter = ns.get('_evidencia_habilidades_turno_mente')"
    )

    assert indice_planejamento < indice_alinhamento < indice_evidencia
    assert "texto_original=texto" in fonte
    assert "texto_operacional_efetivo=texto_efetivo" in fonte
"""


class PatchError(RuntimeError):
    pass


def run(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and proc.returncode != 0:
        raise PatchError(
            f"Comando falhou ({proc.returncode}): {' '.join(args)}\n{proc.stdout}"
        )
    return proc


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def git_blob(path: Path, root: Path) -> str:
    # Lê o blob do próprio HEAD, independente de CRLF/autocrlf no checkout.
    git_path = path.as_posix()
    proc = run(["git", "rev-parse", f"HEAD:{git_path}"], cwd=root)
    return proc.stdout.strip()


def ensure_unique(text: str, anchor: str, nome: str) -> None:
    quantidade = text.count(anchor)
    if quantidade != 1:
        raise PatchError(
            f"Âncora {nome!r} deveria aparecer exatamente 1 vez, apareceu {quantidade}."
        )


def parse_python(path: Path) -> None:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def restore(
    backup_target: Path,
    target: Path,
    new_test: Path,
) -> None:
    try:
        shutil.copy2(backup_target, target)
    except Exception:
        pass
    try:
        if new_test.exists():
            new_test.unlink()
    except Exception:
        pass


def main() -> int:
    try:
        root_text = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
    except Exception as exc:
        print(f"❌ Não encontrei um repositório Git: {exc}")
        return 2

    root = Path(root_text)
    target = root / TARGET
    new_test = root / NEW_TEST

    if not target.exists():
        print(f"❌ Arquivo alvo não encontrado: {TARGET}")
        return 2

    head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    if head != EXPECTED_HEAD:
        print("❌ HEAD diferente do baseline estudado.")
        print(f"   esperado: {EXPECTED_HEAD}")
        print(f"   atual:    {head}")
        print("   Não apliquei nada.")
        return 3

    status = run(
        ["git", "status", "--porcelain", "--", str(TARGET), str(NEW_TEST)],
        cwd=root,
    ).stdout.strip()
    if status:
        print("❌ Há alterações locais nos arquivos do patch:")
        print(status)
        print("   Não apliquei nada.")
        return 4

    if new_test.exists():
        print(f"❌ O teste novo já existe: {NEW_TEST}")
        print("   Isso pode indicar aplicação parcial ou manual. Não apliquei nada.")
        return 5

    blob = git_blob(TARGET, root)
    if blob != EXPECTED_BLOB:
        print("❌ O blob do orquestrador não é o estudado.")
        print(f"   esperado: {EXPECTED_BLOB}")
        print(f"   atual:    {blob}")
        print("   Não apliquei nada.")
        return 6

    bytes_originais = target.read_bytes()
    newline_target = "\r\n" if b"\r\n" in bytes_originais else "\n"
    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        print(f"❌ Marker {MARKER} já encontrado. Patch não será reaplicado.")
        return 7

    try:
        ensure_unique(original, ANCHOR_HELPER, "inserção do helper")
        ensure_unique(original, ANCHOR_PLAN, "alinhamento após planejamento")
    except PatchError as exc:
        print(f"❌ {exc}")
        print("   Não apliquei nada.")
        return 8

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = root / ".laylay_patch_backups" / PATCH_ID / timestamp
    backup_target = backup_dir / TARGET
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_target)

    before_sha = sha256_file(target)
    tests_output = ""
    py_compile_rc = None
    diff_check_rc = None
    pytest_rc = None

    try:
        atualizado = original.replace(
            ANCHOR_HELPER, REPLACEMENT_HELPER, 1
        ).replace(
            ANCHOR_PLAN, REPLACEMENT_PLAN, 1
        )

        # Validação ainda em memória antes de gravar.
        ast.parse(atualizado, filename=str(TARGET))
        ast.parse(TEST_CONTENT, filename=str(NEW_TEST))

        target.write_text(atualizado, encoding="utf-8", newline=newline_target)
        new_test.parent.mkdir(parents=True, exist_ok=True)
        new_test.write_text(TEST_CONTENT, encoding="utf-8", newline="\n")

        parse_python(target)
        parse_python(new_test)

        py_compile = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(TARGET),
                str(NEW_TEST),
            ],
            cwd=root,
            check=False,
        )
        py_compile_rc = py_compile.returncode
        if py_compile.returncode != 0:
            raise PatchError(f"py_compile falhou:\n{py_compile.stdout}")

        diff_check = run(
            ["git", "diff", "--check", "--", str(TARGET), str(NEW_TEST)],
            cwd=root,
            check=False,
        )
        diff_check_rc = diff_check.returncode
        if diff_check.returncode != 0:
            raise PatchError(f"git diff --check falhou:\n{diff_check.stdout}")

        pytest = run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                str(NEW_TEST),
                "tests/test_revisao_intra_turno_v1.py",
                "tests/test_autorizacao_ato_fala_v2.py",
                "tests/test_cadeia_contexto_vivo_v2.py",
            ],
            cwd=root,
            check=False,
        )
        pytest_rc = pytest.returncode
        tests_output = pytest.stdout
        if pytest.returncode != 0:
            raise PatchError(f"pytest focado falhou:\n{pytest.stdout}")

        diff = run(
            ["git", "diff", "--", str(TARGET), str(NEW_TEST)],
            cwd=root,
        ).stdout
        (backup_dir / "patch.diff").write_text(diff, encoding="utf-8")

        after_sha = sha256_file(target)
        manifest = {
            "patch_id": PATCH_ID,
            "baseline_head": EXPECTED_HEAD,
            "status": "applied",
            "applied_at": dt.datetime.now().isoformat(timespec="seconds"),
            "files": [
                {
                    "path": str(TARGET),
                    "git_blob_before": EXPECTED_BLOB,
                    "sha256_before": before_sha,
                    "sha256_after": after_sha,
                },
                {
                    "path": str(NEW_TEST),
                    "sha256_before": None,
                    "sha256_after": sha256_file(new_test),
                },
            ],
            "tests": {
                "py_compile_returncode": py_compile_rc,
                "git_diff_check_returncode": diff_check_rc,
                "pytest_returncode": pytest_rc,
                "pytest_output": tests_output,
            },
            "backup_dir": str(backup_dir.relative_to(root)),
        }
        (backup_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print("✅ Patch B1.2 aplicado e validado.")
        print(f"   Patch ID: {PATCH_ID}")
        print(f"   Baseline: {EXPECTED_HEAD}")
        print(f"   Backup:   {backup_dir.relative_to(root)}")
        print()
        print(tests_output.rstrip())
        print()
        print("🔎 Revise agora:")
        print(f"   git diff -- {TARGET} {NEW_TEST}")
        print()
        print("O patcher NÃO fez commit nem push.")
        return 0

    except Exception as exc:
        restore(backup_target, target, new_test)
        manifest = {
            "patch_id": PATCH_ID,
            "baseline_head": EXPECTED_HEAD,
            "status": "rolled_back",
            "failed_at": dt.datetime.now().isoformat(timespec="seconds"),
            "error": f"{type(exc).__name__}: {exc}",
            "tests": {
                "py_compile_returncode": py_compile_rc,
                "git_diff_check_returncode": diff_check_rc,
                "pytest_returncode": pytest_rc,
                "pytest_output": tests_output,
            },
            "backup_dir": str(backup_dir.relative_to(root)),
        }
        try:
            (backup_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

        print("❌ Patch falhou e foi revertido automaticamente.")
        print(f"   {type(exc).__name__}: {exc}")
        print(f"   Backup: {backup_dir.relative_to(root)}")
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
