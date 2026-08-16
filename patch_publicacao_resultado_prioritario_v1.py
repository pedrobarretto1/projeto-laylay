#!/usr/bin/env python3
"""
Patch P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815

Objetivo:
- manter o resultado detalhado do executor como publicação oficial;
- transformar registros genéricos posteriores em fallback real, não duplicação;
- preservar caminhos legados que não publicam ResultadoAcao detalhado;
- impedir dupla alimentação de observabilidade/aprendizado/mapa de habilidades.

Baseline obrigatório:
  ce83479611fe82ff6c6b7e88a54c7fb4c0179a74  ("tete 2.4")

Uso:
  python patch_publicacao_resultado_prioritario_v1.py --check
  python patch_publicacao_resultado_prioritario_v1.py
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime

PATCH_ID = "P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815"
BASELINE_HEAD = "ce83479611fe82ff6c6b7e88a54c7fb4c0179a74"

RESULTADO_ACAO = Path("mente_laylay/memoria_mental/resultado_acao.py")
ADAPTADOR = Path("mente_laylay/autonomia/adaptador_resultado.py")
RUNTIME = Path("mente_laylay/integracao/adaptadores_aplicacao_runtime.py")
TESTE_NOVO = Path("tests/test_publicacao_resultado_prioritario_v1.py")

TARGET_EXISTING = (RESULTADO_ACAO, ADAPTADOR, RUNTIME)
TARGET_ALL = (*TARGET_EXISTING, TESTE_NOVO)

TEST_CONTENT = r"""from __future__ import annotations

# P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815

from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.integracao.adaptadores_aplicacao_runtime import AdaptadoresAplicacaoRuntime
from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
)


class _EstadoFake:
    def __init__(self) -> None:
        self.mental = {
            "plano_turno_atual": {
                "fase": "executado",
                "comandos": [],
                "erros": [],
                "especialistas": {},
            }
        }

    def atualizar_campos(self, dominio: str, **campos) -> None:
        assert dominio == "mental"
        self.mental.update(campos)


class _MotorFake:
    def __init__(self) -> None:
        self.resultados = []

    def observar_resultado(self, *args, **kwargs) -> None:
        self.resultados.append((args, kwargs))


class _MapaFake:
    def __init__(self) -> None:
        self.resultados = []

    def registrar_resultado(self, *args, **kwargs) -> None:
        self.resultados.append((args, kwargs))


def _atualizar_plano_fake(plano, *, fase, comandos, erros=(), fala=""):
    novo = dict(plano or {})
    novo.update(
        fase=fase,
        comandos=[dict(item) for item in comandos],
        erros=list(erros),
        fala_planejada=fala,
    )
    return novo


def _runtime():
    estado = _EstadoFake()
    motor = _MotorFake()
    mapa = _MapaFake()
    base = []
    logs = []
    namespace = {
        "_registrar_resultado_execucao_base": (
            lambda *args, **kwargs: base.append((args, kwargs))
        ),
        "_motor_aprendizado_runtime": motor,
        "_mapa_habilidades_runtime": mapa,
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": _atualizar_plano_fake,
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": logs.append,
    }
    runtime = AdaptadoresAplicacaoRuntime(lambda: namespace)
    return runtime, estado, motor, mapa, base, logs


def _executar_com_adaptador(runtime, pedido, texto="pesquisa python"):
    params = dict(pedido.get("params") or {})
    adaptador = AdaptadorResultadoOperacional(
        pedido,
        params,
        texto,
        "pc_a",
        {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
    )
    adaptador.marcar_resultado(
        "busca_aberta",
        executou=True,
        confirmado=True,
        detalhe="resultado real observado",
    )
    return adaptador


def test_resultado_detalhado_torna_registro_generico_apenas_fallback():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "params": {"query": "python", "engine": "google"},
    }

    adaptador = _executar_com_adaptador(runtime, pedido)

    assert pedido[CHAVE_RESULTADO_OPERACIONAL_PUBLICADO] == adaptador.id_solicitacao
    assert len(estado.mental["plano_turno_atual"]["comandos"]) == 1
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1

    # Reproduz exatamente o padrão dos bypasses prioritários:
    # executar_intencao(...) -> executor publica ResultadoAcao ->
    # camada prioritária tenta registrar novamente o dict original.
    runtime.registrar_resultado_execucao(
        pedido,
        "pesquisa python",
        True,
        origem="prioritario_leitura_deterministica",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["id_solicitacao"] == adaptador.id_solicitacao
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["status"] == "busca_aberta"
    assert comandos[0]["confirmado"] is True
    assert comandos[0]["detalhe"] == "resultado real observado"

    # A publicação redundante não pode contaminar consumidores laterais.
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1
    assert logs == []


def test_fallback_generico_continua_valido_quando_executor_nao_publicou():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "params": {"query": "fallback"},
    }

    runtime.registrar_resultado_execucao(
        pedido,
        "pesquisa fallback",
        True,
        origem="prioritario_legado_sem_publicacao",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["executou"] is True
    assert comandos[0]["status"] == ""
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1
    assert logs == []


def test_novo_adaptador_limpa_marcador_transitorio_reutilizado():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "params": {"query": "novo turno"},
        CHAVE_RESULTADO_OPERACIONAL_PUBLICADO: "execucao-antiga",
    }

    # Um dict reaproveitado não pode herdar a prova transitória da execução
    # anterior. O adaptador representa uma nova invocação e limpa o marcador.
    AdaptadorResultadoOperacional(
        pedido,
        dict(pedido["params"]),
        "nova pesquisa",
        "pc_a",
        {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
    )
    assert CHAVE_RESULTADO_OPERACIONAL_PUBLICADO not in pedido

    runtime.registrar_resultado_execucao(
        pedido,
        "nova pesquisa",
        False,
        origem="prioritario_fallback_nova_invocacao",
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["intent"] == "SEARCH"
    assert comandos[0]["executou"] is False
    assert len(base) == 1
    assert len(motor.resultados) == 1
    assert len(mapa.resultados) == 1
    assert logs == []


def test_publicacoes_detalhadas_repetidas_do_mesmo_adaptador_continuam_permitidas():
    runtime, estado, motor, mapa, base, logs = _runtime()
    pedido = {
        "intent": "SEARCH",
        "id_solicitacao": "exec-search",
        "params": {"query": "python"},
    }
    adaptador = AdaptadorResultadoOperacional(
        pedido,
        dict(pedido["params"]),
        "pesquisa python",
        "pc_a",
        {"_registrar_resultado_execucao": runtime.registrar_resultado_execucao},
    )

    adaptador.marcar_resultado(
        "busca_aberta",
        executou=True,
        confirmado=True,
    )
    adaptador.marcar_resultado(
        "resultado_web_aberto",
        executou=True,
        confirmado=True,
        params_resolvidos={"abrir_resultado": 1},
    )

    comandos = estado.mental["plano_turno_atual"]["comandos"]
    assert len(comandos) == 1
    assert comandos[0]["id_solicitacao"] == "exec-search"
    assert comandos[0]["status"] == "resultado_web_aberto"
    assert comandos[0]["params"]["abrir_resultado"] == 1
    # Só o fallback genérico é suprimido; publicações oficiais sucessivas
    # da mesma execução continuam chegando aos observadores.
    assert len(base) == 2
    assert len(motor.resultados) == 2
    assert len(mapa.resultados) == 2
    assert logs == []
"""


class PatchError(RuntimeError):
    pass


def run(cmd, *, cwd: Path, check: bool = True):
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and proc.returncode != 0:
        raise PatchError(
            f"comando falhou ({proc.returncode}): {' '.join(map(str, cmd))}\n{proc.stdout}"
        )
    return proc


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise PatchError("execute este patch dentro do repositório Git da Laylay")
    return Path(proc.stdout.strip()).resolve()


def require_once(text: str, old: str, label: str) -> None:
    count = text.count(old)
    if count != 1:
        raise PatchError(
            f"anchor inválido em {label}: esperado 1 ocorrência, encontrado {count}"
        )


def transform_resultado_acao(text: str) -> str:
    old = """from typing import Any, Dict

STATUS_RESULTADO_JA_SATISFEITO = {"""
    new = """from typing import Any, Dict

# P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815
# Marcador transitório no dict que originou uma execução. Ele nunca integra
# ResultadoAcao nem o plano persistido; apenas prova, para o chamador imediato,
# que o executor já publicou o contrato oficial daquela invocação.
CHAVE_RESULTADO_OPERACIONAL_PUBLICADO = "_laylay_resultado_operacional_publicado"

STATUS_RESULTADO_JA_SATISFEITO = {"""
    require_once(text, old, str(RESULTADO_ACAO))
    return text.replace(old, new, 1)


def transform_adaptador(text: str) -> str:
    old_import = """from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
    inferir_confirmacao,
)"""
    new_import = """from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
    inferir_confirmacao,
)"""
    require_once(text, old_import, f"{ADAPTADOR}:import")
    text = text.replace(old_import, new_import, 1)

    old_post = """    def __post_init__(self) -> None:
        resultado = self.resultado if isinstance(self.resultado, dict) else {}
        id_existente = str("""
    new_post = """    def __post_init__(self) -> None:
        resultado = self.resultado if isinstance(self.resultado, dict) else {}
        # O marcador é uma prova apenas da invocação corrente. Se algum
        # resolvedor reutilizar o mesmo dict em outro turno, ele precisa voltar
        # a ser elegível ao fallback até publicar um novo ResultadoAcao.
        if isinstance(resultado, dict):
            resultado.pop(CHAVE_RESULTADO_OPERACIONAL_PUBLICADO, None)
        id_existente = str("""
    require_once(text, old_post, f"{ADAPTADOR}:post_init")
    text = text.replace(old_post, new_post, 1)

    old_publish = """            registrar(
                contrato,
                self.texto_original,
                executou,
                origem="executor",
                status=status,
            )
        except Exception:
            pass"""
    new_publish = """            registrar(
                contrato,
                self.texto_original,
                executou,
                origem="executor",
                status=status,
            )
            # Só marque depois que o registrador oficial retornou. Assim,
            # falhas de publicação continuam permitindo o fallback legado.
            if isinstance(self.resultado, dict):
                self.resultado[
                    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO
                ] = self.id_solicitacao
        except Exception:
            pass"""
    require_once(text, old_publish, f"{ADAPTADOR}:publish")
    return text.replace(old_publish, new_publish, 1)


def transform_runtime(text: str) -> str:
    old_import = """from mente_laylay.integracao.registro_memoria_pessoas import PortaMemoriaPessoas
from mente_laylay.integracao.registro_iot import PortaIoT


class AdaptadoresAplicacaoRuntime:"""
    new_import = """from mente_laylay.integracao.registro_memoria_pessoas import PortaMemoriaPessoas
from mente_laylay.integracao.registro_iot import PortaIoT
from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
)


class AdaptadoresAplicacaoRuntime:"""
    require_once(text, old_import, f"{RUNTIME}:import")
    text = text.replace(old_import, new_import, 1)

    old_start = """    def registrar_resultado_execucao(
        self,
        resultado=None,
        texto: str = "",
        executou=None,
        *,
        origem: str = "",
        status: str = "",
    ) -> None:
        ns = self._ns()
        ns["_registrar_resultado_execucao_base"](
            resultado, texto, executou, origem=origem, status=status,
        )"""
    new_start = """    def registrar_resultado_execucao(
        self,
        resultado=None,
        texto: str = "",
        executou=None,
        *,
        origem: str = "",
        status: str = "",
    ) -> None:
        ns = self._ns()
        # P0_PUBLICACAO_RESULTADO_PRIORITARIO_V1_20260815
        # Vários atalhos prioritários seguem o contrato legado
        # ``executar_intencao(...) -> registrar(dict original)``. Quando o
        # executor moderno já publicou ResultadoAcao, o adaptador marca esse
        # mesmo dict. Nesse caso a segunda chamada é somente fallback e deve
        # ser descartada ANTES de alimentar base, aprendizado, mapa e plano.
        #
        # Um status explícito continua sendo aceito como atualização deliberada;
        # caminhos sem publicação oficial também continuam usando o fallback.
        if (
            isinstance(resultado, dict)
            and resultado.get(CHAVE_RESULTADO_OPERACIONAL_PUBLICADO)
            and not str(status or resultado.get("status") or "").strip()
            and str(origem or "").strip().casefold() != "executor"
        ):
            return
        ns["_registrar_resultado_execucao_base"](
            resultado, texto, executou, origem=origem, status=status,
        )"""
    require_once(text, old_start, f"{RUNTIME}:registrar")
    return text.replace(old_start, new_start, 1)


def projected(root: Path) -> dict[Path, str]:
    for path in TARGET_EXISTING:
        if not (root / path).is_file():
            raise PatchError(f"arquivo obrigatório ausente: {path}")
    if (root / TESTE_NOVO).exists():
        raise PatchError(
            f"{TESTE_NOVO} já existe; recuso sobrescrever um teste não pertencente ao baseline"
        )

    texts = {
        RESULTADO_ACAO: (root / RESULTADO_ACAO).read_text(encoding="utf-8"),
        ADAPTADOR: (root / ADAPTADOR).read_text(encoding="utf-8"),
        RUNTIME: (root / RUNTIME).read_text(encoding="utf-8"),
    }
    out = {
        RESULTADO_ACAO: transform_resultado_acao(texts[RESULTADO_ACAO]),
        ADAPTADOR: transform_adaptador(texts[ADAPTADOR]),
        RUNTIME: transform_runtime(texts[RUNTIME]),
        TESTE_NOVO: TEST_CONTENT,
    }
    for path, content in out.items():
        try:
            ast.parse(content, filename=str(path))
        except SyntaxError as exc:
            raise PatchError(f"AST inválida projetada em {path}: {exc}") from exc
    return out


def ensure_clean_targets(root: Path) -> None:
    proc = run(
        ["git", "status", "--porcelain", "--", *[str(p) for p in TARGET_ALL]],
        cwd=root,
    )
    if proc.stdout.strip():
        raise PatchError(
            "há alterações locais nos arquivos-alvo; faça commit/stash antes:\n"
            + proc.stdout
        )


def preflight(root: Path):
    head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    if head != BASELINE_HEAD:
        raise PatchError(
            "baseline divergente.\n"
            f"esperado: {BASELINE_HEAD}\n"
            f"atual:    {head}\n"
            "Não aplique este patch em outro commit."
        )
    ensure_clean_targets(root)
    out = projected(root)
    return head, out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_backup(root: Path, originals: dict[Path, bytes | None]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root / ".laylay_patch_backups" / f"publicacao_resultado_prioritario_v1_{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    files = []
    for path, data in originals.items():
        item = {
            "path": str(path).replace("\\", "/"),
            "existed_before": data is not None,
            "sha256_before": sha256_bytes(data) if data is not None else None,
        }
        files.append(item)
        if data is not None:
            dest = backup / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    manifest = {
        "patch_id": PATCH_ID,
        "baseline_head": BASELINE_HEAD,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "backup_created",
        "files": files,
    }
    (backup / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return backup


def rollback(root: Path, originals: dict[Path, bytes | None]) -> None:
    for path, data in originals.items():
        target = root / path
        if data is None:
            try:
                target.unlink()
            except FileNotFoundError:
                pass
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def write_manifest(backup: Path, payload: dict) -> None:
    (backup / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply(root: Path, out: dict[Path, str], head: str) -> Path:
    originals = {
        path: ((root / path).read_bytes() if (root / path).exists() else None)
        for path in TARGET_ALL
    }
    backup = make_backup(root, originals)
    test_results = []
    try:
        for path, content in out.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")

        compile_cmd = [
            sys.executable,
            "-m",
            "py_compile",
            *[str(p) for p in TARGET_ALL],
        ]
        proc = run(compile_cmd, cwd=root)
        test_results.append({
            "name": "py_compile",
            "command": compile_cmd,
            "returncode": proc.returncode,
            "output": proc.stdout,
        })

        diff_cmd = ["git", "diff", "--check", "--", *[str(p) for p in TARGET_ALL]]
        proc = run(diff_cmd, cwd=root)
        test_results.append({
            "name": "git_diff_check",
            "command": diff_cmd,
            "returncode": proc.returncode,
            "output": proc.stdout,
        })

        pytest_files = [
            str(TESTE_NOVO),
            "tests/test_contrato_execucao_none_v1.py",
            "tests/test_bug_b_observabilidade_execucoes.py",
            "tests/test_adaptador_resultado.py",
            "tests/test_cadeia_contexto_vivo_v2.py",
        ]
        pytest_files = [p for p in pytest_files if (root / p).exists()]
        pytest_cmd = [
            sys.executable,
            "-m",
            "pytest",
            *pytest_files,
            "-q",
            "--maxfail=1",
        ]
        proc = run(pytest_cmd, cwd=root)
        test_results.append({
            "name": "pytest_targeted",
            "command": pytest_cmd,
            "returncode": proc.returncode,
            "output": proc.stdout,
        })

        diff = run(
            ["git", "diff", "--", *[str(p) for p in TARGET_ALL]],
            cwd=root,
        ).stdout
        (backup / "patch.diff").write_text(diff, encoding="utf-8")

        manifest = {
            "patch_id": PATCH_ID,
            "baseline_head": BASELINE_HEAD,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "status": "applied",
            "files": [
                {
                    "path": str(path).replace("\\", "/"),
                    "existed_before": originals[path] is not None,
                    "sha256_before": (
                        sha256_bytes(originals[path])
                        if originals[path] is not None
                        else None
                    ),
                    "sha256_after_projected": sha256_bytes(
                        out[path].encode("utf-8")
                    ),
                }
                for path in TARGET_ALL
            ],
            "tests": test_results,
            "applied_at": datetime.now().isoformat(timespec="seconds"),
            "head_after": run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip(),
        }
        write_manifest(backup, manifest)
        return backup
    except Exception:
        rollback(root, originals)
        manifest = {
            "patch_id": PATCH_ID,
            "baseline_head": BASELINE_HEAD,
            "status": "rolled_back_after_validation_failure",
            "rolled_back_at": datetime.now().isoformat(timespec="seconds"),
            "tests": test_results,
        }
        write_manifest(backup, manifest)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="valida baseline, arquivos, anchors e AST sem escrever nada",
    )
    args = parser.parse_args()

    try:
        root = repo_root()
        head, out = preflight(root)
        print(f"📍 repo: {root}")
        print(f"🔒 baseline: {head}")
        print(f"🧩 patch: {PATCH_ID}")
        print("✅ anchors únicos e AST projetada válidos")
        print(
            "🎯 alvo: resultado_acao.py + adaptador_resultado.py + "
            "adaptadores_aplicacao_runtime.py + regressão"
        )
        if args.check:
            print("✅ PREFLIGHT OK — nenhum arquivo foi alterado")
            return 0

        backup = apply(root, out, head)
        print("✅ PATCH APLICADO E VALIDADO")
        print(f"🛟 backup: {backup}")
        print("🧪 regressões focadas aprovadas")
        print("ℹ️ nenhum commit ou push foi feito")
        return 0
    except Exception as exc:
        print(f"❌ PATCH RECUSADO/FALHOU: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
