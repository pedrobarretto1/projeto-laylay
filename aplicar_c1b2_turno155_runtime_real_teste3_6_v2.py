# -*- coding: utf-8 -*-
r'''
C1-B2 — patcher transacional do turno 155 (`maximiza`) para o HEAD teste 3.6.

ESCOPO DE PRODUÇÃO
- mente_laylay/autonomia/roteador_deterministico.py
  Separa referência linguística de elipse operacional exata `maximiza`.

ESCOPO DE REGRESSÃO
- tests/test_regressao_c1b_turno155_maximiza_eliptico.py
  Troca o callback de teste baseado em modalidade pelo callback real de
  referência linguística e congela que `maximiza` continua NÃO sendo uma
  referência linguística.

GARANTIAS
- trava HEAD e blobs exatos;
- exige staging vazio e os dois alvos C1-B2 limpos antes de escrever;
- permite alterações tracked preexistentes fora do escopo, mas fotografa seu diff
  binário e exige preservação byte-a-byte até o fim/rollback;
- faz backup byte-a-byte fora do checkout;
- aplica somente âncoras exatas e únicas;
- não usa git add/commit/push;
- py_compile;
- regressão C1-B/C1-B2 com callback real;
- prova runtime detector + orquestrador;
- regressões P0, C1-A e R1.1;
- valida que só os dois arquivos permitidos mudaram;
- gera diff/log/manifest;
- rollback automático dos dois arquivos se qualquer etapa falhar.

A dívida separada `maximiza opera` -> `pera` em `detectar_janela_explicita()`
NÃO é alterada por este patcher.

Uso, a partir da raiz da Laylay:

    & C:\Python314\python.exe ".\aplicar_c1b2_turno155_runtime_real_teste3_6.py" --repo .

Nenhum git add/commit/push é executado.
'''

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


HEAD_ESPERADO = "f53c9f4ca4165a0bbdecac332b84a89fe993e765"

ALVO_PRODUCAO = "mente_laylay/autonomia/roteador_deterministico.py"
ALVO_TESTE = "tests/test_regressao_c1b_turno155_maximiza_eliptico.py"
ALVOS_PERMITIDOS = (ALVO_PRODUCAO, ALVO_TESTE)

BLOBS_ESPERADOS = {
    ALVO_PRODUCAO: "6b811913bbe62bf8d399b10ea53ffb4855e7c287",
    ALVO_TESTE: "9bd3e4133b9c067ad40d13dbfabc36876d664f8c",
    "mente_laylay/autonomia/orquestrador_deterministico.py":
        "1ace7364d3ac9ef3530e7cd22607d6573f1c5b86",
    "mente_laylay/cognicao/modalidade_turno.py":
        "80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
    "mente_laylay/memoria_mental/compatibilidade_contexto.py":
        "768944f808002d8c24f697c0b2769a31d536eb3e",
    "mente_laylay/cognicao/referencias_linguagem.py":
        "6f1b759fc190228a9f2c4e2c9620c716fe064b53",
}

SHA256_PRODUCAO_ANTES = (
    "935da6470e50f0d16602357acb00779e41e32ae23af5a8b0384d611cfd99470e"
)
SHA256_PRODUCAO_CANDIDATO = (
    "dbceaca84d9561b945f0edbfe1936a71e82aa91e42b2cbbb30e2a5bcb94a150c"
)

REGRESSIVOS = [
    ("C1-B/C1-B2", ALVO_TESTE, "13 passed"),
    ("P0", "tests/test_p0_autorizacao_modalidade.py", "9 passed"),
    ("C1-A", "tests/test_regressao_c1_turno159_buffer_operacional.py", "13 passed"),
    ("R1.1", "tests/test_regressao_r1_1_autoridade_navegador_cadeia.py", "44 passed"),
]

ANCHOR_PROD_ANTIGO = '''    referencia_janela_contextual = (
        bool(depende_contexto(t))
        or any(v in t for v in ["ele", "ela", "isso"])
    )
    if not referencia_janela_contextual:
        return None
'''

ANCHOR_PROD_NOVO = '''    # C1-B2: referência linguística e elipse operacional são contratos
    # diferentes. `maximiza` puro pode procurar um alvo de app já confirmado,
    # sem ser promovido a referência linguística e sem fabricar autoridade.
    referencia_linguistica = (
        bool(depende_contexto(t))
        or any(v in t for v in ["ele", "ela", "isso"])
    )
    acao_janela_eliptica = t == "maximiza"
    if not (referencia_linguistica or acao_janela_eliptica):
        return None
'''

ANCHOR_TESTE_FUTURE_ANTIGO = '''from __future__ import annotations

from mente_laylay.autonomia.roteador_deterministico import detectar_janela_contextual
'''

ANCHOR_TESTE_FUTURE_NOVO = '''from __future__ import annotations

import re

from mente_laylay.autonomia.roteador_deterministico import detectar_janela_contextual
'''

ANCHOR_TESTE_IMPORTS_ANTIGO = '''from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)


def _params(**kwargs):
'''

ANCHOR_TESTE_IMPORTS_NOVO = '''from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    texto_depende_de_contexto as texto_depende_de_contexto_runtime,
)


def _params(**kwargs):
'''

ANCHOR_TESTE_HELPERS_ANTIGO = '''def _depende_contexto(texto: str) -> bool:
    return bool(classificar_modalidade_turno(texto).get("depende_contexto"))


def _detectar(texto: str, estado: dict | None):
    return detectar_janela_contextual(
        texto.casefold().strip(" .,!?:;"),
        params_cb=_params,
        estado_mental=dict(estado or {}),
        texto_depende_de_contexto=_depende_contexto,
    )
'''

ANCHOR_TESTE_HELPERS_NOVO = '''def _normalizar(texto: str) -> str:
    return re.sub(r"\\s+", " ", str(texto or "").casefold()).strip(" .,!?:;")


def _depende_contexto(texto: str) -> bool:
    return bool(
        texto_depende_de_contexto_runtime(
            texto,
            _normalizar,
        )
    )


def _detectar(texto: str, estado: dict | None):
    return detectar_janela_contextual(
        _normalizar(texto),
        params_cb=_params,
        estado_mental=dict(estado or {}),
        texto_depende_de_contexto=_depende_contexto,
    )
'''

ANCHOR_TESTE_GUARD_ANTIGO = '''def test_guard_c1b_maximiza_puro_ja_e_acao_explicita_contextual_com_alvo_pendente():
    turno = classificar_modalidade_turno("maximiza")
    assert turno.get("acao_explicita") is True, turno
    assert turno.get("depende_contexto") is True, turno
    assert turno.get("requer_esclarecimento") is True, turno


def test_guard_c1b_detector_ja_materializa_maximize_window_com_app_vivo():
'''

ANCHOR_TESTE_GUARD_NOVO = '''def test_guard_c1b_maximiza_puro_ja_e_acao_explicita_contextual_com_alvo_pendente():
    turno = classificar_modalidade_turno("maximiza")
    assert turno.get("acao_explicita") is True, turno
    assert turno.get("depende_contexto") is True, turno
    assert turno.get("requer_esclarecimento") is True, turno


def test_guard_c1b_callback_runtime_nao_promove_maximiza_a_referencia_linguistica():
    assert _depende_contexto("maximiza") is False
    assert _depende_contexto("maximiza ele") is True


def test_guard_c1b_detector_ja_materializa_maximize_window_com_app_vivo():
'''

TESTE_RUNTIME = r'''# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_janela_contextual,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    texto_depende_de_contexto as texto_depende_de_contexto_runtime,
)


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "").casefold()).strip(" .,!?:;")


def _depende_real(texto: str) -> bool:
    return bool(texto_depende_de_contexto_runtime(texto, _normalizar))


def _params(**kwargs):
    return kwargs


def _estado_app(nome: str = "opera") -> dict:
    return {
        "ultimo_app_janela": nome,
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": nome},
        "ultima_acao_status": "ja_aberto_focado",
        "ultima_acao_confirmada": True,
        "ultima_acao_ok": True,
    }


def _estado_site() -> dict:
    return {
        "ultima_acao_intent": "OPEN_URL",
        "ultima_acao_params": {"alvo": "wikipedia"},
        "ultima_acao_status": "url_aberta",
        "ultima_acao_confirmada": True,
        "ultimo_site_aba": "wikipedia",
        "ultimo_alvo": "wikipedia",
    }


def _detectar(texto: str, estado: dict | None):
    return detectar_janela_contextual(
        _normalizar(texto),
        params_cb=_params,
        estado_mental=dict(estado or {}),
        texto_depende_de_contexto=_depende_real,
    )


def _ctx(estado: dict | None):
    return {
        "normalizar_texto": _normalizar,
        "texto_conversa_casual_sem_acao": lambda _t: False,
        "texto_bloqueia_playlist_agora": lambda _t: False,
        "texto_social_curto": lambda _t: False,
        "ignorar_token_solto": lambda _t: False,
        "fluxo_prioritario_da_ia": lambda _t: False,
        "texto_expresso_melhor_no_deterministico": lambda _t: False,
        "texto_depende_de_contexto": _depende_real,
        "limpar_destino_pc_b": lambda valor: str(valor or ""),
        "target_from_params": lambda *_args, **_kwargs: "pc_a",
        "mente_integrada_estado": dict(estado or {}),
        "sites_diretos": {},
        "apps_map": {"opera": object(), "calculadora": object()},
        "contexto_musical_ativo": lambda: False,
        "musica_estado_get": lambda *_args, **_kwargs: "",
    }


def test_c1b2_runtime_callback_continua_linguistico():
    assert _depende_real("maximiza") is False
    assert _depende_real("maximiza ele") is True


def test_c1b2_runtime_detector_materializa_maximiza_com_app_vivo():
    candidato = _detectar("maximiza", _estado_app())
    assert candidato == {
        "intent": "MAXIMIZE_WINDOW",
        "params": {"nome_app": "opera"},
    }


def test_c1b2_runtime_sem_app_ou_so_site_nao_fabrica_alvo():
    assert _detectar("maximiza", {}) is None
    assert _detectar("maximiza", _estado_site()) is None


def test_c1b2_runtime_negacao_e_formas_nao_autorizadas_nao_herdam_elipse():
    assert _detectar("não maximiza", _estado_app()) is None
    assert _detectar("maximizar", _estado_app()) is None
    assert _detectar("maximize", _estado_app()) is None
    assert _detectar("fecha", _estado_app()) is None
    assert _detectar("abre", _estado_app()) is None


def test_c1b2_runtime_orquestrador_publica_maximize_window():
    candidato = detectar_intencao_deterministica_mente(
        "maximiza",
        _ctx(_estado_app()),
    )
    assert candidato == {
        "intent": "MAXIMIZE_WINDOW",
        "params": {"nome_app": "opera"},
    }
'''


class FalhaPatch(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(args, *, cwd: Path, env=None):
    return subprocess.run(
        args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def _git(repo: Path, *args: str, check: bool = True) -> str:
    p = _run(["git", *args], cwd=repo)
    if check and p.returncode != 0:
        raise FalhaPatch(
            f"git {' '.join(args)} falhou ({p.returncode}):\n{p.stdout}"
        )
    return p.stdout.strip()


def _staging_diff_binario(repo: Path) -> bytes:
    p = _run_bytes(
        ["git", "diff", "--cached", "--binary"],
        cwd=repo,
    )
    if p.returncode != 0:
        raise FalhaPatch(
            "git diff --cached --binary falhou: "
            + p.stderr.decode("utf-8", errors="replace")
        )
    return p.stdout


def _alvos_c1b2_limpos(repo: Path) -> bool:
    alvo = _run(
        ["git", "diff", "--quiet", "--", *ALVOS_PERMITIDOS],
        cwd=repo,
    )
    return alvo.returncode == 0


def _run_bytes(args, *, cwd: Path):
    return subprocess.run(
        args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _diff_binario_paths(repo: Path, caminhos: list[str] | tuple[str, ...]) -> bytes:
    if not caminhos:
        return b""
    p = _run_bytes(
        ["git", "diff", "--binary", "--", *caminhos],
        cwd=repo,
    )
    if p.returncode != 0:
        raise FalhaPatch(
            "git diff --binary falhou: "
            + p.stderr.decode("utf-8", errors="replace")
        )
    return p.stdout


def _validar_preexistente_preservado(
    repo: Path,
    nomes_preexistentes: set[str],
    diff_preexistente: bytes,
) -> None:
    nomes_agora = _nomes_diff(repo)
    permitidos_agora = set(ALVOS_PERMITIDOS)
    extras_agora = nomes_agora - permitidos_agora
    if extras_agora != nomes_preexistentes:
        raise FalhaPatch(
            "Alterações tracked preexistentes mudaram de conjunto. "
            f"antes={sorted(nomes_preexistentes)!r} "
            f"agora={sorted(extras_agora)!r}"
        )
    observado = _diff_binario_paths(
        repo,
        tuple(sorted(nomes_preexistentes)),
    )
    if observado != diff_preexistente:
        raise FalhaPatch(
            "Conteúdo do diff tracked preexistente mudou durante o patch/testes."
        )


def _escolher_python(repo: Path) -> Path:
    for candidato in (
        repo / ".venv314" / "Scripts" / "python.exe",
        repo / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ):
        if candidato.exists():
            return candidato.resolve()
    return Path(sys.executable).resolve()


def _env_python(repo: Path):
    env = os.environ.copy()
    anterior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo) + (os.pathsep + anterior if anterior else "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _replace_unico(texto: str, antigo: str, novo: str, nome: str) -> str:
    n = texto.count(antigo)
    if n != 1:
        raise FalhaPatch(
            f"Âncora {nome} apareceu {n} vezes; esperado exatamente 1."
        )
    return texto.replace(antigo, novo, 1)


def _transformar_producao(data: bytes) -> bytes:
    texto = data.decode("utf-8")
    novo = _replace_unico(
        texto,
        ANCHOR_PROD_ANTIGO,
        ANCHOR_PROD_NOVO,
        "produção C1-B2",
    )
    return novo.encode("utf-8")


def _transformar_teste(data: bytes) -> bytes:
    texto = data.decode("utf-8")
    texto = _replace_unico(
        texto,
        ANCHOR_TESTE_FUTURE_ANTIGO,
        ANCHOR_TESTE_FUTURE_NOVO,
        "teste import re",
    )
    texto = _replace_unico(
        texto,
        ANCHOR_TESTE_IMPORTS_ANTIGO,
        ANCHOR_TESTE_IMPORTS_NOVO,
        "teste callback runtime import",
    )
    texto = _replace_unico(
        texto,
        ANCHOR_TESTE_HELPERS_ANTIGO,
        ANCHOR_TESTE_HELPERS_NOVO,
        "teste helper runtime",
    )
    texto = _replace_unico(
        texto,
        ANCHOR_TESTE_GUARD_ANTIGO,
        ANCHOR_TESTE_GUARD_NOVO,
        "teste guard callback runtime",
    )
    return texto.encode("utf-8")


def _pytest(python_exe: Path, repo: Path, alvo: str):
    return _run(
        [str(python_exe), "-m", "pytest", "-q", "-vv", alvo],
        cwd=repo,
        env=_env_python(repo),
    )


def _exigir_pass(proc, nome: str, marcador: str | None = None) -> None:
    if proc.returncode != 0:
        raise FalhaPatch(f"{nome} falhou:\n{proc.stdout}")
    if marcador and marcador not in proc.stdout:
        raise FalhaPatch(
            f"{nome} passou sem o marcador esperado {marcador!r}:\n{proc.stdout}"
        )


def _nomes_diff(repo: Path) -> set[str]:
    p = _run(["git", "diff", "--name-only", "--"], cwd=repo)
    if p.returncode != 0:
        raise FalhaPatch(p.stdout)
    return {
        linha.strip().replace("\\", "/")
        for linha in p.stdout.splitlines()
        if linha.strip()
    }


def _rollback(originais: dict[Path, bytes]) -> list[str]:
    erros = []
    for caminho, data in originais.items():
        try:
            caminho.write_bytes(data)
        except Exception as exc:
            erros.append(f"{caminho}: {exc}")
    return erros


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica C1-B2 com rollback automático e regressão runtime real."
    )
    parser.add_argument("--repo", default=".", help="raiz do checkout Laylay")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        raise FalhaPatch(f"Não é checkout Git: {repo}")

    head = _git(repo, "rev-parse", "HEAD")
    if head != HEAD_ESPERADO:
        raise FalhaPatch(
            f"HEAD inesperado: {head}\nEsperado: {HEAD_ESPERADO}"
        )

    for caminho, blob_esperado in BLOBS_ESPERADOS.items():
        observado = _git(repo, "rev-parse", f"HEAD:{caminho}")
        if observado != blob_esperado:
            raise FalhaPatch(
                f"Blob inesperado em {caminho}: {observado}\n"
                f"Esperado: {blob_esperado}"
            )

    staging_inicial = _staging_diff_binario(repo)
    if staging_inicial:
        raise FalhaPatch(
            "Staging já possui alterações. O patcher exige staging vazio "
            "para não misturar estado indexado."
        )
    if not _alvos_c1b2_limpos(repo):
        raise FalhaPatch(
            "Um dos dois alvos C1-B2 já possui alteração local. "
            "O patcher recusou antes de escrever."
        )

    nomes_preexistentes = _nomes_diff(repo)
    if nomes_preexistentes & set(ALVOS_PERMITIDOS):
        raise FalhaPatch(
            "Invariante violada: alvo C1-B2 apareceu no diff preexistente."
        )
    diff_preexistente = _diff_binario_paths(
        repo,
        tuple(sorted(nomes_preexistentes)),
    )

    python_exe = _escolher_python(repo)
    alvo_prod = repo / ALVO_PRODUCAO
    alvo_test = repo / ALVO_TESTE
    originais = {
        alvo_prod: alvo_prod.read_bytes(),
        alvo_test: alvo_test.read_bytes(),
    }

    if _sha256_bytes(originais[alvo_prod]) != SHA256_PRODUCAO_ANTES:
        raise FalhaPatch(
            "SHA-256 da produção real não corresponde ao baseline C1-B2 auditado."
        )

    candidatos = {
        alvo_prod: _transformar_producao(originais[alvo_prod]),
        alvo_test: _transformar_teste(originais[alvo_test]),
    }

    if _sha256_bytes(candidatos[alvo_prod]) != SHA256_PRODUCAO_CANDIDATO:
        raise FalhaPatch(
            "Transformação de produção não reproduziu o SHA-256 do candidato "
            "já auditado em espelho."
        )

    stamp = time.strftime("%Y%m%d-%H%M%S")
    artefatos = (
        repo.parent
        / "laylay_patch_artifacts_c1b2_turno155"
        / stamp
    )
    artefatos.mkdir(parents=True, exist_ok=False)

    backup_dir = artefatos / "backup"
    backup_dir.mkdir()
    (backup_dir / "roteador_deterministico.py.before").write_bytes(
        originais[alvo_prod]
    )
    (backup_dir / "test_regressao_c1b_turno155_maximiza_eliptico.py.before").write_bytes(
        originais[alvo_test]
    )

    log_path = artefatos / "log_patch_c1b2_turno155.txt"
    diff_path = artefatos / "diff_patch_c1b2_turno155.diff"
    manifest_path = artefatos / "manifest_patch_c1b2_turno155.json"
    preexisting_diff_path = artefatos / "preexisting_tracked_before.diff"
    preexisting_diff_path.write_bytes(diff_preexistente)

    logs = []
    inicio = time.time()
    aplicado = False
    tmp_test = repo / "tests" / "_tmp_c1b2_apply_runtime_real.py"

    print()
    print("C1-B2 — PATCHER TRANSACIONAL / TESTE 3.6")
    print("=" * 72)
    print(f"HEAD travado: {head}")
    print(f"Python pytest: {python_exe}")
    print("arquivos C1-B2 permitidos: 2")
    print(
        "tracked preexistente preservado: "
        f"{len(nomes_preexistentes)} arquivo(s)"
    )
    for caminho in sorted(nomes_preexistentes):
        print(f"  preserva: {caminho}")
    print(f"backup: {backup_dir}")
    print("git add/commit/push: NÃO")
    print()

    try:
        alvo_prod.write_bytes(candidatos[alvo_prod])
        alvo_test.write_bytes(candidatos[alvo_test])
        aplicado = True

        if alvo_prod.read_bytes() != candidatos[alvo_prod]:
            raise FalhaPatch("Produção escrita diverge do candidato calculado.")
        if alvo_test.read_bytes() != candidatos[alvo_test]:
            raise FalhaPatch("Teste escrito diverge do candidato calculado.")

        _validar_preexistente_preservado(
            repo,
            nomes_preexistentes,
            diff_preexistente,
        )
        nomes = _nomes_diff(repo)
        esperado_nomes = nomes_preexistentes | set(ALVOS_PERMITIDOS)
        if nomes != esperado_nomes:
            raise FalhaPatch(
                "Escopo Git divergente após escrita. "
                f"observado={sorted(nomes)!r} esperado={sorted(esperado_nomes)!r}"
            )
        print("escopo C1-B2 + preexistente .......... PASS")

        p_compile = _run(
            [
                str(python_exe),
                "-m",
                "py_compile",
                ALVO_PRODUCAO,
                ALVO_TESTE,
            ],
            cwd=repo,
            env=_env_python(repo),
        )
        logs.append("===== PY_COMPILE =====\n" + p_compile.stdout)
        _exigir_pass(p_compile, "py_compile")
        print("py_compile ............................ PASS")

        for nome, teste, marcador in REGRESSIVOS:
            p = _pytest(python_exe, repo, teste)
            logs.append(f"===== REGRESSIVO {nome} — {teste} =====\n" + p.stdout)
            _exigir_pass(p, f"regressivo {nome}", marcador)
            print(f"regressivo {nome:<23} PASS")

        if tmp_test.exists():
            raise FalhaPatch(
                f"Teste temporário já existe e não será sobrescrito: {tmp_test}"
            )
        try:
            tmp_test.write_text(TESTE_RUNTIME, encoding="utf-8", newline="\n")
            p_runtime = _pytest(
                python_exe,
                repo,
                "tests/_tmp_c1b2_apply_runtime_real.py",
            )
            logs.append("===== RUNTIME REAL C1-B2 =====\n" + p_runtime.stdout)
            _exigir_pass(p_runtime, "runtime real C1-B2", "5 passed")
        finally:
            try:
                tmp_test.unlink(missing_ok=True)
            except Exception:
                pass
        print("runtime detector+orquestrador ........ PASS")

        if tmp_test.exists():
            raise FalhaPatch("Teste temporário permaneceu após execução.")
        _validar_preexistente_preservado(
            repo,
            nomes_preexistentes,
            diff_preexistente,
        )
        nomes = _nomes_diff(repo)
        esperado_nomes = nomes_preexistentes | set(ALVOS_PERMITIDOS)
        if nomes != esperado_nomes:
            raise FalhaPatch(
                "Escopo Git mudou após testes. "
                f"observado={sorted(nomes)!r} esperado={sorted(esperado_nomes)!r}"
            )

        staging_final = _staging_diff_binario(repo)
        if staging_final != staging_inicial:
            raise FalhaPatch("Staging mudou durante o patch/testes.")

        diff_proc = _run(
            ["git", "diff", "--", ALVO_PRODUCAO, ALVO_TESTE],
            cwd=repo,
        )
        if diff_proc.returncode != 0:
            raise FalhaPatch("git diff final falhou:\n" + diff_proc.stdout)
        diff = diff_proc.stdout

        marcadores_diff = [
            'acao_janela_eliptica = t == "maximiza"',
            "referencia_linguistica = (",
            "texto_depende_de_contexto as texto_depende_de_contexto_runtime",
            'assert _depende_contexto("maximiza") is False',
        ]
        for marcador in marcadores_diff:
            if marcador not in diff:
                raise FalhaPatch(
                    f"Diff final não contém marcador obrigatório: {marcador}"
                )

        proibidos_diff = [
            "detectar_janela_explicita(",
            "maximiza opera",
            'nome_app="pera"',
        ]
        for proibido in proibidos_diff:
            if proibido in diff:
                raise FalhaPatch(
                    f"Diff misturou dívida separada/proibida: {proibido}"
                )

        diff_path.write_text(diff, encoding="utf-8", newline="\n")
        log_path.write_text(
            "\n\n".join(logs) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest = {
            "status": "patch_applied_tests_green_pending_real_chaos",
            "head": head,
            "production_written": True,
            "rollback_performed": False,
            "git_add_commit_push": False,
            "allowed_tracked_changes": list(ALVOS_PERMITIDOS),
            "preexisting_tracked_changes": sorted(nomes_preexistentes),
            "preexisting_tracked_diff_sha256":
                _sha256_bytes(diff_preexistente),
            "preexisting_tracked_preserved": True,
            "staging_preserved": True,
            "source_blobs_before": dict(BLOBS_ESPERADOS),
            "production_sha256_before": _sha256_bytes(originais[alvo_prod]),
            "production_sha256_after": _sha256_bytes(alvo_prod.read_bytes()),
            "test_sha256_before": _sha256_bytes(originais[alvo_test]),
            "test_sha256_after": _sha256_bytes(alvo_test.read_bytes()),
            "candidate_production_sha256_expected":
                SHA256_PRODUCAO_CANDIDATO,
            "diff_sha256": _sha256_bytes(diff_path.read_bytes()),
            "log_sha256": _sha256_bytes(log_path.read_bytes()),
            "focused_regressions": {
                nome: "PASS" for nome, _teste, _marcador in REGRESSIVOS
            },
            "runtime_real_detector_orchestrator": "PASS",
            "separate_debt_maximiza_opera_pera_touched": False,
            "next_gate": "teste real corredor 154 -> 155 / caos",
            "elapsed_s": round(time.time() - inicio, 3),
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print()
        print("✅ C1-B2 PATCH APLICADO E REGRESSÕES VERDES")
        print("produção alterada: SIM — somente escopo C1-B2 permitido")
        print("tracked preexistente preservado: SIM")
        print("staging preservado: SIM")
        print("regressão permanente callback real: SIM")
        print("rollback executado: NÃO")
        print("git add/commit/push: NÃO")
        print("estado: PENDENTE DE TESTE REAL DO CORREDOR 154→155")
        print(f"diff: {diff_path}")
        print(f"log: {log_path}")
        print(f"manifest: {manifest_path}")
        return 0

    except Exception as exc:
        erros_rollback = _rollback(originais) if aplicado else []

        try:
            tmp_test.unlink(missing_ok=True)
        except Exception:
            pass

        restaurado = True
        for caminho, data in originais.items():
            try:
                restaurado = restaurado and caminho.read_bytes() == data
            except Exception:
                restaurado = False

        preexistente_preservado = False
        try:
            _validar_preexistente_preservado(
                repo,
                nomes_preexistentes,
                diff_preexistente,
            )
            preexistente_preservado = True
        except Exception:
            preexistente_preservado = False

        staging_preservado = False
        try:
            staging_preservado = (
                _staging_diff_binario(repo) == staging_inicial
            )
        except Exception:
            staging_preservado = False

        falha = [
            "C1-B2 PATCHER FALHOU",
            f"erro: {exc}",
            f"rollback_performed: {bool(aplicado)}",
            f"rollback_restored_exact_bytes: {restaurado}",
            f"preexisting_tracked_preserved: {preexistente_preservado}",
            f"staging_preserved: {staging_preservado}",
        ]
        if erros_rollback:
            falha.append("rollback_errors: " + " | ".join(erros_rollback))
        try:
            log_path.write_text(
                "\n\n".join(
                    logs + ["===== FALHA / ROLLBACK =====\n" + "\n".join(falha)]
                ) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "status": (
                            "patch_failed_rolled_back"
                            if restaurado
                            else "patch_failed_rollback_incomplete"
                        ),
                        "head": head,
                        "production_written": bool(aplicado),
                        "rollback_performed": bool(aplicado),
                        "rollback_restored_exact_bytes": restaurado,
                        "preexisting_tracked_changes":
                            sorted(nomes_preexistentes),
                        "preexisting_tracked_diff_sha256":
                            _sha256_bytes(diff_preexistente),
                        "preexisting_tracked_preserved":
                            preexistente_preservado,
                        "staging_preserved": staging_preservado,
                        "git_add_commit_push": False,
                        "error": str(exc),
                        "allowed_tracked_changes": list(ALVOS_PERMITIDOS),
                    },
                    ensure_ascii=False,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except Exception:
            pass

        print()
        print("❌ C1-B2 PATCHER RECUSOU/REVERTEU")
        print(str(exc))
        print(f"rollback executado: {'SIM' if aplicado else 'NÃO NECESSÁRIO'}")
        print(f"bytes originais restaurados: {'SIM' if restaurado else 'NÃO'}")
        print(
            "tracked preexistente preservado: "
            f"{'SIM' if preexistente_preservado else 'NÃO'}"
        )
        print(
            "staging preservado: "
            f"{'SIM' if staging_preservado else 'NÃO'}"
        )
        print("git add/commit/push: NÃO")
        print(f"artefatos: {artefatos}")
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FalhaPatch as exc:
        print()
        print("❌ C1-B2 PATCHER RECUSOU ANTES DE ESCREVER")
        print(str(exc))
        print("produção alterada: NÃO")
        print("git add/commit/push: NÃO")
        raise SystemExit(2)
