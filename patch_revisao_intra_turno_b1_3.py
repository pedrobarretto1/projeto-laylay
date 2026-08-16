#!/usr/bin/env python3
# P0_REVISAO_INTRA_TURNO_B1_3_20260816
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "P0_REVISAO_INTRA_TURNO_B1_3_20260816"
BASELINE_HEAD = "a506599297da2c08cd7a679d1010d88bff80d055"

TARGETS = {
    "mente_laylay/cognicao/revisao_turno.py": "75e2671c2b46e4a40d1aada2c8d21e28762d4373",
    "mente_laylay/autonomia/coordenador_intencao.py": "08bbf0ee78e1039d27fbbda71898ae16d45c688a",
    "tests/test_revisao_intra_turno_v1.py": "1c6b5c068e39786c62caa7a94b8207847c0006d6",
    "tests/test_identidade_plano_revisao_b1_2.py": "b85e355f9c28ff71075ad0a5454256e695de96bd",
}

FOCUSED_TESTS = [
    "tests/test_revisao_intra_turno_v1.py",
    "tests/test_identidade_plano_revisao_b1_2.py",
    "tests/test_autorizacao_ato_fala_v2.py",
    "tests/test_p0_autorizacao_modalidade.py",
    "tests/test_p16_linguagem_natural_operacional.py",
]


class PatchError(RuntimeError):
    pass


def run(cmd: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise PatchError(
            f"Comando falhou ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def find_repo(start: Path) -> Path:
    p = start.resolve()
    for candidate in (p, Path(__file__).resolve().parent):
        cur = candidate
        while True:
            if (cur / ".git").exists():
                return cur
            if cur.parent == cur:
                break
            cur = cur.parent
    raise PatchError(
        "Não encontrei a raiz do repositório. Rode este patcher dentro do projeto Laylay "
        "ou use --repo CAMINHO."
    )


def head_blob_sha(repo: Path, rel: str) -> str:
    # Lê o blob versionado no HEAD. O git status abaixo garante que o arquivo
    # de trabalho não está modificado; assim evitamos falso negativo por CRLF
    # em checkouts Windows com core.autocrlf.
    return run(["git", "rev-parse", f"HEAD:{rel}"], repo).stdout.strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise PatchError(
            f"Âncora '{label}' deveria aparecer exatamente 1 vez, mas apareceu {count}. "
            "Patch recusado para evitar edição no lugar errado."
        )
    return text.replace(old, new, 1)


def replace_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise PatchError(
            f"Âncora '{label}' deveria aparecer {expected} vez(es), mas apareceu {count}. "
            "Patch recusado."
        )
    return text.replace(old, new)


def backup_targets(repo: Path, backup_dir: Path) -> None:
    for rel in TARGETS:
        src = repo / rel
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def restore_targets(repo: Path, backup_dir: Path) -> None:
    for rel in TARGETS:
        src = backup_dir / rel
        dst = repo / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def preflight(repo: Path) -> dict:
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if head != BASELINE_HEAD:
        raise PatchError(
            "HEAD diferente do baseline estudado.\n"
            f"Esperado: {BASELINE_HEAD}\nAtual:    {head}\n"
            "Não vou aplicar um patch em código que não foi reanalisado."
        )

    dirty = run(
        ["git", "status", "--porcelain", "--", *TARGETS.keys()],
        repo,
    ).stdout.strip()
    if dirty:
        raise PatchError(
            "Há alterações locais em arquivo(s)-alvo. Salve/commit/stash antes de aplicar:\n"
            + dirty
        )

    blobs = {}
    sha256 = {}
    for rel, expected_blob in TARGETS.items():
        path = repo / rel
        if not path.is_file():
            raise PatchError(f"Arquivo-alvo ausente: {rel}")
        actual_blob = head_blob_sha(repo, rel)
        blobs[rel] = actual_blob
        sha256[rel] = sha256_file(path)
        if actual_blob != expected_blob:
            raise PatchError(
                f"Blob inesperado em {rel}.\nEsperado: {expected_blob}\nAtual:    {actual_blob}"
            )

    return {"head": head, "blobs_antes": blobs, "sha256_antes": sha256}


def patch_revisao(text: str) -> str:
    old = '''    if tinha_melhor:
        correcao=correcao_sem_melhor

    nova_op=_operacao_inicio(correcao)
    if nova_op:
        # Elipses como "continua tocando" carregam a nova operação, mas
        # omitem o alvo que já estava explícito na proposta descartada.
        # Herdamos somente quando o complemento é um marcador de continuidade
        # sem alvo próprio; o executor recebe então uma fala autossuficiente.
        resto_novo=_norm(str(nova_op.get("resto") or "")).strip()
        if (
            alvo_antigo
            and nova_op.get("canon")=="retomar"
            and resto_novo in {"", "tocando", "a tocar"}
        ):
            correcao=f"{nova_op.get('verbo')} {alvo_antigo}".strip()
            nova_op=_operacao_inicio(correcao)
        # "apaga X... não apaga" = cancela, não é uma segunda exclusão sem alvo.
        if marker=="nao" and nova_op.get("canon")==operacao_antiga.get("canon") and not nova_op.get("resto"):
            base.update(resolvida=True,cancelada=True,tipo="cancelamento",motivo="negação repetiu a operação sem novo alvo")
            return base
'''
    new = '''    if tinha_melhor:
        correcao=correcao_sem_melhor

    # P0_REVISAO_INTRA_TURNO_B1_3_20260816
    # Estado final com alvo herdado: "liga a lâmpada... não, deixa desligada"
    # não troca o alvo; troca o estado desejado do mesmo dispositivo.
    estado_iot=_norm(correcao).strip()
    if alvo_antigo and operacao_antiga.get("canon") in {"ligar","desligar"}:
        m_estado_iot=re.fullmatch(
            r"(?:deixa|deixe|deixar)\\s+(?:ele\\s+|ela\\s+|isso\\s+)?"
            r"(?P<estado>desligad[oa]s?|ligad[oa]s?)",
            estado_iot,
            re.I,
        )
        if m_estado_iot:
            estado=str(m_estado_iot.group("estado") or "")
            verbo_final="desliga" if estado.startswith("desligad") else "liga"
            efetivo=f"{verbo_final} {alvo_antigo}".strip()
            base.update(
                resolvida=True,
                tipo="substituicao_acao",
                texto_operacional_efetivo=efetivo[:500],
                motivo="correção definiu o estado final do mesmo alvo IoT",
            )
            return base

    nova_op=_operacao_inicio(correcao)
    if nova_op:
        resto_novo=_norm(str(nova_op.get("resto") or "")).strip()

        # A negação corretiva continua semanticamente ativa depois que o
        # marcador "não" separa as duas propostas. "não pesquisa nada" não
        # significa SEARCH("nada"): revoga a mesma operação.
        if (
            marker=="nao"
            and nova_op.get("canon")==operacao_antiga.get("canon")
            and resto_novo in {"", "nada", "mais nada"}
        ):
            base.update(
                resolvida=True,
                cancelada=True,
                tipo="cancelamento",
                motivo="negação revogou a mesma operação sem novo alvo operacional",
            )
            return base

        # Elipses como "continua tocando" carregam a nova operação, mas
        # omitem o alvo que já estava explícito na proposta descartada.
        # Para música, emitimos uma forma que o roteador determinístico já
        # reconhece; assim o produtor e o consumidor compartilham o contrato.
        if (
            alvo_antigo
            and nova_op.get("canon")=="retomar"
            and resto_novo in {"", "tocando", "a tocar"}
        ):
            if _norm(alvo_antigo)=="musica":
                correcao=f"{nova_op.get('verbo')} a música".strip()
            else:
                correcao=f"{nova_op.get('verbo')} {alvo_antigo}".strip()
            nova_op=_operacao_inicio(correcao)
'''
    return replace_once(text, old, new, "revisao:estado-negacao-musica")


def patch_coordenador(text: str) -> str:
    old = '    intent = _call(ctx, "tentar_intencao_ai_primeiro", texto)\n'
    new = '''    # P0_REVISAO_INTRA_TURNO_B1_3_20260816
    # Se a revisão intra-turno já definiu a proposta operacional final,
    # o fallback de IA recebe essa mesma visão. A fala original continua sendo
    # identidade/auditoria, mas não pode reintroduzir a proposta descartada.
    texto_ia = (
        trecho_operacional
        if revisao_resolvida and trecho_operacional
        else texto
    )
    intent = _call(ctx, "tentar_intencao_ai_primeiro", texto_ia)
'''
    return replace_once(text, old, new, "coordenador:fallback-ia-texto-operacional")


def patch_test_revisao(text: str) -> str:
    text = replace_count(
        text,
        '"continua música"',
        '"continua a música"',
        2,
        "teste:canone-musical",
    )

    old_tuple = '''        (
            "Pausa a música... esquece, continua tocando.",
            "continua a música",
            "substituicao_acao",
        ),
        (
            "Cria um arquivo chamado erro.txt... não, chama correcao.txt.",
'''
    new_tuple = '''        (
            "Pausa a música... esquece, continua tocando.",
            "continua a música",
            "substituicao_acao",
        ),
        (
            "Liga a lâmpada... não, deixa desligada.",
            "desliga lâmpada",
            "substituicao_acao",
        ),
        (
            "Cria um arquivo chamado erro.txt... não, chama correcao.txt.",
'''
    text = replace_once(text, old_tuple, new_tuple, "teste:caso-estado-iot")

    anchor = '''def test_negacao_corretiva_cancela_mutacao_em_vez_de_repetir() -> None:
    revisao = resolver_revisao_intra_turno(
        "Apaga o arquivo segredo.txt... não apaga."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is True
    assert revisao["texto_operacional_efetivo"] == ""


'''
    inserted = '''def test_saida_musical_revisada_e_consumivel_pelo_roteador() -> None:
    from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia

    revisao = resolver_revisao_intra_turno(
        "Pausa a música... esquece, continua tocando."
    )
    intent = detectar_volume_ou_midia(
        revisao["texto_operacional_efetivo"].casefold(),
        params_cb=lambda **kwargs: kwargs,
    )
    assert intent == {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}


def test_negacao_com_nada_revoga_mesma_operacao() -> None:
    revisao = resolver_revisao_intra_turno(
        "Pesquisa Python... pera, não pesquisa nada."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is True
    assert revisao["tipo"] == "cancelamento"
    assert revisao["texto_operacional_efetivo"] == ""


def test_estado_final_iot_herda_alvo_sem_contaminar_o_alvo() -> None:
    revisao = resolver_revisao_intra_turno(
        "Liga a lâmpada... não, deixa desligada."
    )
    assert revisao["detectada"] is True
    assert revisao["resolvida"] is True
    assert revisao["cancelada"] is False
    assert revisao["tipo"] == "substituicao_acao"
    assert revisao["alvo_herdado"] == "lâmpada"
    assert revisao["texto_operacional_efetivo"] == "desliga lâmpada"
    assert "deixa" not in revisao["texto_operacional_efetivo"].casefold()


def test_fallback_ia_recebe_texto_operacional_revisado() -> None:
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao

    original = "Pausa a música... esquece, continua tocando."
    revisao = resolver_revisao_intra_turno(original)
    recebido: dict[str, str] = {}

    def tentar_ia(texto: str):
        recebido["texto"] = texto
        return None

    ctx = {
        "normalizar_texto": lambda texto: str(texto or "").casefold().strip(),
        "refinar_contexto_mental": lambda _texto: None,
        "turno_atual": {
            "modalidade": "comando",
            "modalidade_geral": "comando",
            "autoriza_execucao": True,
            "revisao_intra_turno": revisao,
            "texto_operacional_efetivo": revisao["texto_operacional_efetivo"],
        },
        "retrato_turno_atual": {},
        "extrair_agendamento": lambda _texto: None,
        "extrair_acao_agendada": lambda _texto: None,
        "texto_cancela_acao_agora": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: False,
        "detectar_intencao_deterministica": lambda _texto: None,
        "resolver_comando_contextual_forcado": lambda _texto: None,
        "resolver_repeticao_ultima_acao": lambda _texto: None,
        "tentar_intencao_ai_primeiro": tentar_ia,
        "registrar_arbitragem_turno": lambda *_args: None,
    }

    assert resolver_intencao(original, "terminal", ctx) == (None, "")
    assert recebido["texto"] == revisao["texto_operacional_efetivo"]
    assert recebido["texto"] != original


''' + anchor
    return replace_once(text, anchor, inserted, "teste:contratos-b1-3")


def patch_test_identidade(text: str) -> str:
    return replace_count(
        text,
        '"continua música"',
        '"continua a música"',
        1,
        "teste-identidade:canone-musical",
    )


PATCHERS = {
    "mente_laylay/cognicao/revisao_turno.py": patch_revisao,
    "mente_laylay/autonomia/coordenador_intencao.py": patch_coordenador,
    "tests/test_revisao_intra_turno_v1.py": patch_test_revisao,
    "tests/test_identidade_plano_revisao_b1_2.py": patch_test_identidade,
}


def apply(repo: Path) -> None:
    for rel, patch_fn in PATCHERS.items():
        path = repo / rel
        original = path.read_text(encoding="utf-8")
        novo = patch_fn(original)
        if novo == original:
            raise PatchError(f"Patch não alterou {rel}; recusando estado ambíguo.")
        tmp = path.with_suffix(path.suffix + ".b13.tmp")
        tmp.write_text(novo, encoding="utf-8", newline="\n")
        os.replace(tmp, path)


def validations(repo: Path) -> dict:
    py_files = list(TARGETS.keys())
    py_compile = run([sys.executable, "-m", "py_compile", *py_files], repo)

    diff_check = run(["git", "diff", "--check", "--", *TARGETS.keys()], repo)

    pytest = run(
        [sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS],
        repo,
    )

    diff = run(["git", "diff", "--", *TARGETS.keys()], repo).stdout

    return {
        "py_compile_returncode": py_compile.returncode,
        "git_diff_check_returncode": diff_check.returncode,
        "pytest_returncode": pytest.returncode,
        "pytest_stdout": pytest.stdout,
        "pytest_stderr": pytest.stderr,
        "diff": diff,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica com segurança o B1.3 da revisão intra-turno da Laylay."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Caminho da raiz do repositório (padrão: diretório atual).",
    )
    args = parser.parse_args()

    backup_dir: Path | None = None
    manifest: dict = {
        "patch_id": PATCH_ID,
        "baseline_head": BASELINE_HEAD,
        "targets": TARGETS,
        "focused_tests": FOCUSED_TESTS,
        "started_at": datetime.now().astimezone().isoformat(),
        "status": "started",
    }

    try:
        repo = find_repo(Path(args.repo))
        os.chdir(repo)
        print(f"🔎 Repo: {repo}")
        print(f"🔒 Baseline exigido: {BASELINE_HEAD}")

        manifest["preflight"] = preflight(repo)
        print("✅ Preflight: HEAD, arquivos limpos e blobs confirmados.")

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = repo / ".laylay_patch_backups" / f"{PATCH_ID}_{stamp}"
        backup_dir.mkdir(parents=True, exist_ok=False)
        backup_targets(repo, backup_dir)
        manifest["backup_dir"] = str(backup_dir.relative_to(repo))
        print(f"🧰 Backup: {manifest['backup_dir']}")

        apply(repo)
        print("🧩 Alterações aplicadas; iniciando validações.")

        candidate_diff = run(["git", "diff", "--", *TARGETS.keys()], repo).stdout
        (backup_dir / "patch_candidate.diff").write_text(
            candidate_diff,
            encoding="utf-8",
        )
        manifest["candidate_diff"] = str(
            (backup_dir / "patch_candidate.diff").relative_to(repo)
        )

        result = validations(repo)
        manifest["validacoes"] = {
            k: v for k, v in result.items() if k != "diff"
        }
        manifest["status"] = "ok"
        manifest["finished_at"] = datetime.now().astimezone().isoformat()
        manifest["sha256_depois"] = {
            rel: sha256_file(repo / rel) for rel in TARGETS
        }

        (backup_dir / "patch.diff").write_text(result["diff"], encoding="utf-8")
        (backup_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print("\n✅ PATCH B1.3 APLICADO E VALIDADO.")
        print("Nenhum commit ou push foi feito.")
        print("\n--- pytest focado ---")
        print(result["pytest_stdout"].rstrip())
        if result["pytest_stderr"].strip():
            print(result["pytest_stderr"].rstrip())
        print("\n--- diff ---")
        print(result["diff"].rstrip())
        print(f"\nManifest: {backup_dir / 'manifest.json'}")
        print(f"Diff salvo: {backup_dir / 'patch.diff'}")
        print("\nPróximo passo: rode o teste de caos completo antes de considerar B1 fechado.")
        return 0

    except Exception as exc:
        print(f"\n❌ PATCH RECUSADO/FALHOU: {exc}", file=sys.stderr)
        if backup_dir is not None and backup_dir.exists():
            try:
                repo = find_repo(Path(args.repo))
                restore_targets(repo, backup_dir)
                rollback_diff = run(
                    ["git", "diff", "--", *TARGETS.keys()],
                    repo,
                    check=False,
                ).stdout
                manifest["status"] = "rollback"
                manifest["error"] = str(exc)
                manifest["finished_at"] = datetime.now().astimezone().isoformat()
                manifest["diff_apos_rollback"] = rollback_diff
                (backup_dir / "manifest.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print("↩️ Rollback automático concluído.", file=sys.stderr)
            except Exception as rollback_exc:
                print(
                    f"⚠️ Falha também no rollback automático: {rollback_exc}\n"
                    f"Use o backup em: {backup_dir}",
                    file=sys.stderr,
                )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
