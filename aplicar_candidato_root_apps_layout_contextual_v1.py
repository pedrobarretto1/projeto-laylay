from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile


EXPECTED_HEAD = "441eb51ef0040eed8856d45fc120e84f541d2f21"

ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
).resolve()

TARGET = Path("mente_laylay/memoria_mental/continuidade_semantica.py")
EXPECTED_GIT_BLOB = "30c0572becb656e3da361696f3cf52f482850828"
EXPECTED_SHA256 = "4cd35d93532d850290ab1f5ce34d4865469f3ec345c8d5f923fceb37bd8d21b8"

REQUIRED_INPUTS = {
    Path("tests/test_layout_contextual_nao_herda_acao_anterior.py"):
        "e103e1922ef0ed7244d88bd62def74f3b3dab04271ca3fa9c456837c8c6fd1f5",
    Path("tests/test_regressao_turno227_aplicativos_janelas.py"):
        "8cd256c3d67a88078f18073516b2e2af5712adc5c5f81d7d17e3864ac613af02",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_once(texto: str, antigo: str, novo: str, *, nome: str) -> str:
    ocorrencias = texto.count(antigo)
    if ocorrencias != 1:
        raise SystemExit(
            f"ABORTADO: ancora {nome!r} esperava 1 ocorrencia; "
            f"encontrou {ocorrencias}."
        )
    return texto.replace(antigo, novo, 1)


def _validar_premissas() -> None:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    if head != EXPECTED_HEAD:
        raise SystemExit(
            f"ABORTADO: HEAD mudou. esperado={EXPECTED_HEAD} observado={head}"
        )

    alvo = ROOT / TARGET
    blob = subprocess.check_output(
        ["git", "hash-object", "--", str(TARGET)],
        cwd=ROOT,
        text=True,
    ).strip()
    if blob != EXPECTED_GIT_BLOB:
        raise SystemExit(
            "ABORTADO: blob do módulo-alvo mudou. "
            f"esperado={EXPECTED_GIT_BLOB} observado={blob}"
        )
    observado = _sha256(alvo)
    if observado != EXPECTED_SHA256:
        raise SystemExit(
            "ABORTADO: SHA-256 do módulo-alvo mudou. "
            f"esperado={EXPECTED_SHA256} observado={observado}"
        )

    for relativo, esperado in REQUIRED_INPUTS.items():
        caminho = ROOT / relativo
        if not caminho.is_file():
            raise SystemExit(f"ABORTADO: premissa ausente: {relativo}")
        observado = _sha256(caminho)
        if observado != esperado:
            raise SystemExit(
                f"ABORTADO: premissa mudou: {relativo}; "
                f"esperado={esperado} observado={observado}"
            )


def _montar_candidato(original: str) -> str:
    candidato = original

    candidato = _replace_once(
        candidato,
        '''def _acao_semantica(tokens: list[str]) -> str:
    if _tem_radical(tokens, "cri", "refaz", "restaur", "recuper"):
''',
        '''def _acao_semantica(tokens: list[str]) -> str:
    lados = {"esquerda", "esquerdo", "direita", "direito"}
    if set(tokens).intersection(lados) and _tem_radical(
        tokens, "coloc", "coloqu", "posicion",
    ):
        return "POSICIONAR"
    if _tem_radical(tokens, "cri", "refaz", "restaur", "recuper"):
''',
        nome="acao_espacial_antes_da_acao_generica",
    )

    candidato = _replace_once(
        candidato,
        '''    if _tem_radical(tokens, "toc", "coloc"):
        return "EXECUTAR"
''',
        '''    if _tem_radical(tokens, "toc", "coloc", "coloqu"):
        return "EXECUTAR"
''',
        nome="conjugacao_coloque_sem_direcao",
    )

    candidato = _replace_once(
        candidato,
        '''    if intent in {"APP_OPEN", "OPEN_URL"}:
        return "ABRIR"
''',
        '''    if intent in {"APP_OPEN", "OPEN_URL"}:
        return "ABRIR"
    if intent == "ORGANIZAR_DESKTOP":
        return "POSICIONAR"
''',
        nome="acao_canonica_do_layout",
    )

    candidato = _replace_once(
        candidato,
        '''    if dominio in {"app", "site", "iot", "musica"}:
        alvo = _alvo_contextual(estado, dominio, ultimo_params)
''',
        '''    if dominio == "app" and acao == "POSICIONAR":
        esquerda = bool(set(tokens).intersection({"esquerda", "esquerdo"}))
        direita = bool(set(tokens).intersection({"direita", "direito"}))
        alvo = _alvo_contextual(estado, dominio, ultimo_params)
        if alvo and esquerda != direita:
            lado = "left" if esquerda else "right"
            return DecisaoContinuidade(
                operacao="POSICIONAR_REFERENCIA",
                dominio="app",
                acao="POSICIONAR",
                intent="ORGANIZAR_DESKTOP",
                alvo=alvo,
                params={
                    lado: alvo,
                    "modo": "posicionar",
                    "referencia_contextual": True,
                },
                confianca=min(0.97, confianca_dominio + 0.1),
                motivo="acao espacial atual aplicada ao referente vivo do app",
            )

    if dominio in {"app", "site", "iot", "musica"}:
        alvo = _alvo_contextual(estado, dominio, ultimo_params)
''',
        nome="materializacao_layout_contextual",
    )

    if candidato == original:
        raise SystemExit("ABORTADO: candidato não produziu alteração.")
    ast.parse(candidato, filename=str(TARGET))
    return candidato


def _diff(original: str, candidato: str) -> str:
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        candidato.splitlines(keepends=True),
        fromfile=str(TARGET),
        tofile=f"{TARGET} (candidato)",
    ))


def _escrever_atomicamente(path: Path, conteudo: str) -> None:
    modo = stat.S_IMODE(path.stat().st_mode)
    temporario = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
            temporario = arquivo.name
        os.chmod(temporario, modo)
        os.replace(temporario, path)
    finally:
        if temporario and os.path.exists(temporario):
            os.unlink(temporario)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Candidato estreito para layout contextual de apps.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="grava o candidato após todas as travas; sem esta opção é dry-run",
    )
    args = parser.parse_args()

    _validar_premissas()
    alvo = ROOT / TARGET
    original = alvo.read_text(encoding="utf-8", newline="")
    candidato = _montar_candidato(original)
    print(_diff(original, candidato))

    if not args.apply:
        print("DRY-RUN: nenhuma alteração foi gravada.")
        return 0

    _escrever_atomicamente(alvo, candidato)
    if _sha256(alvo) != hashlib.sha256(candidato.encode("utf-8")).hexdigest():
        raise SystemExit("ABORTADO: verificação pós-escrita falhou.")
    print(f"APLICADO: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
