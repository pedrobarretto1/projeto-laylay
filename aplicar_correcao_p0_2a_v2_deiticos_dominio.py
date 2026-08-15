#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# P0.2A v2 — dêiticos de domínio + barreira na rota determinística.
# Não altera P0.2B de confirmações pendentes.

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MARCADOR = "P0_DEITICOS_DOMINIO_20260814"
CONTEXTO_REL = Path("mente_laylay/memoria_mental/contexto_imediato.py")
IMEDIATOS_REL = Path("mente_laylay/autonomia/comandos_imediatos.py")
TESTE_REL = Path("tests/test_p0_isolamento_contexto.py")


def achar_raiz(inicio: Path) -> Path:
    inicio = inicio.resolve()
    for pasta in (inicio, *inicio.parents):
        if (
            (pasta / "laylay.py").is_file()
            and (pasta / CONTEXTO_REL).is_file()
            and (pasta / IMEDIATOS_REL).is_file()
            and (pasta / TESTE_REL).is_file()
        ):
            return pasta
    raise FileNotFoundError(
        "Não encontrei a raiz da Laylay. Coloque o patcher dentro do projeto "
        "ou use --root."
    )


def raiz_padrao() -> Path:
    for inicio in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        try:
            return achar_raiz(inicio)
        except FileNotFoundError:
            pass
    raise FileNotFoundError("Raiz do projeto não encontrada.")


def patch_contexto(fonte: str) -> str:
    if MARCADOR in fonte:
        return fonte

    antigo_ref_curta = """    pronome = bool(re.search(
        r"\\b(?:ele|ela|isso|esse|essa|este|esta|dele|dela|desse|dessa)\\b", t
    ))
"""
    novo_ref_curta = """    # P0_DEITICOS_DOMINIO_20260814
    # "anterior" é dêitico: o domínio ativo decide o referente.
    pronome = bool(re.search(
        r"\\b(?:ele|ela|isso|esse|essa|este|esta|dele|dela|desse|dessa|"
        r"anterior)\\b",
        t,
    ))
"""
    if antigo_ref_curta not in fonte:
        raise RuntimeError("Âncora de referência curta não encontrada.")
    fonte = fonte.replace(antigo_ref_curta, novo_ref_curta, 1)

    antigo_musica = """    elif re.search(r"\\b(pausa|despausa|proxima|próxima|anterior|musica|música|faixa|playlist|toca|replay)\\b", texto_norm):
        dominio_pedido = "musica"
"""
    novo_musica = """    elif re.search(
        r"\\b(pausa|despausa|proxima|próxima|musica|música|faixa|playlist|toca|replay)\\b",
        texto_norm,
    ):
        dominio_pedido = "musica"
"""
    if antigo_musica not in fonte:
        raise RuntimeError("Âncora da pista musical 'anterior' não encontrada.")
    fonte = fonte.replace(antigo_musica, novo_musica, 1)

    ancora_site = """    if tipo_ref == "site":
        alvo = str(alvo_ref or ultimo_params.get("alvo") or ultimo_params.get("url") or "").strip()
"""
    novo_site = """    if tipo_ref == "site":
        if re.fullmatch(
            r"(?:volta|volte|retorna|retorne|vai)\\s+"
            r"(?:(?:para|pra)\\s+)?(?:a\\s+)?anterior[?.!]*",
            t,
            flags=re.IGNORECASE,
        ):
            return {
                "intent": "SWITCH_PREVIOUS_TAB",
                "params": {"referencia_contextual": True},
            }
        alvo = str(alvo_ref or ultimo_params.get("alvo") or ultimo_params.get("url") or "").strip()
"""
    if ancora_site not in fonte:
        raise RuntimeError("Âncora do domínio site não encontrada.")
    fonte = fonte.replace(ancora_site, novo_site, 1)

    ast.parse(fonte)
    return fonte


def patch_imediatos(fonte: str) -> str:
    if MARCADOR in fonte:
        return fonte

    ancora_import = """from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
"""
    novo_import = """from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.memoria_mental.contexto_imediato import (
    _dominio_restrito_referencia,
    _resultado_compativel_com_dominio,
)
"""
    if ancora_import not in fonte:
        raise RuntimeError("Âncora de imports não encontrada.")
    fonte = fonte.replace(ancora_import, novo_import, 1)

    ancora_candidato = """        intent_imediato = str(
            (candidato_imediato or {}).get("intent")
            if isinstance(candidato_imediato, dict) else ""
        ).upper().strip()
"""
    novo_candidato = """        # P0_DEITICOS_DOMINIO_20260814
        # O determinístico detecta; o domínio atual decide se ele pode agir.
        dominio_contextual_p0 = _dominio_restrito_referencia(
            texto,
            getattr(estado_runtime, "mental", {}),
            ttl_s=300.0,
        )
        if (
            isinstance(candidato_imediato, dict)
            and dominio_contextual_p0
            and not _resultado_compativel_com_dominio(
                candidato_imediato,
                dominio_contextual_p0,
            )
        ):
            print(
                "🛡️ [P0:CONTEXTO] determinístico descartado por domínio | "
                f"dominio={dominio_contextual_p0} "
                f"intent={candidato_imediato.get('intent')}"
            )
            candidato_imediato = None

        intent_imediato = str(
            (candidato_imediato or {}).get("intent")
            if isinstance(candidato_imediato, dict) else ""
        ).upper().strip()
"""
    if ancora_candidato not in fonte:
        raise RuntimeError("Âncora do candidato determinístico não encontrada.")
    fonte = fonte.replace(ancora_candidato, novo_candidato, 1)

    ast.parse(fonte)
    return fonte


def patch_testes(fonte: str) -> str:
    if "test_deitico_anterior_usa_site_ativo" in fonte:
        return fonte

    bloco = r"""

def test_deitico_anterior_usa_site_ativo():
    estado = {
        "ts": time.time(),
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultimo_site_aba": "prime video",
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        ),
    }
    assert _dominio_restrito_referencia(
        "Volta para a anterior.", estado, ttl_s=300.0
    ) == "site"


def test_site_ativo_materializa_switch_previous_tab():
    mental = {
        "ts": time.time(),
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultimo_site_aba": "prime video",
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        ),
    }
    resultado = _runtime(mental, estrutura={}).resolver(
        "Volta para a anterior."
    )
    assert resultado is not None
    assert resultado["intent"] == "SWITCH_PREVIOUS_TAB"


def test_fecha_essa_depois_de_site_vira_close_tab_nao_midia():
    mental = {
        "ts": time.time(),
        "ultima_acao_intent": "OPEN_URL",
        "ultima_intencao": "OPEN_URL",
        "ultima_habilidade": "site",
        "ultima_acao_params": {"alvo": "prime video"},
        "ultima_acao_promovivel": True,
        "ultimo_site_aba": "prime video",
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        ),
    }
    resultado = _runtime(mental, estrutura={}).resolver("Fecha essa.")
    assert resultado is not None
    assert resultado["intent"] == "CLOSE_TAB"
    assert resultado["params"]["alvo"] == "prime video"


def test_musica_anterior_explicita_continua_musica():
    mental = {
        "continuidade_geral": _continuidade(
            "site", "OPEN_URL", "prime video", {"alvo": "prime video"}
        )
    }
    assert _dominio_restrito_referencia(
        "Volta para a música anterior.", mental, ttl_s=300.0
    ) == "musica"
"""
    fonte = fonte.rstrip() + bloco + "\n"
    ast.parse(fonte)
    return fonte


def validar(contexto: str, imediatos: str, testes: str) -> None:
    ast.parse(contexto)
    ast.parse(imediatos)
    ast.parse(testes)

    checks = (
        (MARCADOR in contexto, "marcador contexto"),
        ('"intent": "SWITCH_PREVIOUS_TAB"' in contexto, "switch previous"),
        ("_dominio_restrito_referencia" in imediatos, "guard domínio"),
        ("_resultado_compativel_com_dominio" in imediatos, "compatibilidade"),
        ("determinístico descartado por domínio" in imediatos, "log guard"),
        ("test_deitico_anterior_usa_site_ativo" in testes, "teste anterior"),
        ("test_fecha_essa_depois_de_site_vira_close_tab_nao_midia" in testes, "teste fecha"),
    )
    faltas = [nome for ok, nome in checks if not ok]
    if faltas:
        raise RuntimeError("Validação estática falhou: " + ", ".join(faltas))

    antigo = (
        'r"\\\\b(pausa|despausa|proxima|próxima|anterior|musica|música|'
        'faixa|playlist|toca|replay)\\\\b"'
    )
    if antigo in contexto:
        raise RuntimeError("A regra antiga ainda classifica anterior como música.")


def restaurar(pares):
    for destino, backup, existia in pares:
        if existia and backup.exists():
            shutil.copy2(backup, destino)
        elif not existia and destino.exists():
            destino.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica P0.2A v2: dêiticos + barreira determinística."
    )
    parser.add_argument("--root", type=Path)
    parser.add_argument("--sem-testes", action="store_true")
    args = parser.parse_args()

    raiz = achar_raiz(args.root.expanduser()) if args.root else raiz_padrao()
    contexto_path = raiz / CONTEXTO_REL
    imediatos_path = raiz / IMEDIATOS_REL
    teste_path = raiz / TESTE_REL

    contexto_novo = patch_contexto(
        contexto_path.read_text(encoding="utf-8")
    )
    imediatos_novo = patch_imediatos(
        imediatos_path.read_text(encoding="utf-8")
    )
    testes_novos = patch_testes(
        teste_path.read_text(encoding="utf-8")
    )
    validar(contexto_novo, imediatos_novo, testes_novos)

    backup_raiz = (
        raiz / "_backup_correcao_p0_contexto_v2"
        / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    pares = []
    for rel, destino in (
        (CONTEXTO_REL, contexto_path),
        (IMEDIATOS_REL, imediatos_path),
        (TESTE_REL, teste_path),
    ):
        backup = backup_raiz / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        existia = destino.exists()
        if existia:
            shutil.copy2(destino, backup)
        pares.append((destino, backup, existia))

    try:
        contexto_path.write_text(contexto_novo, encoding="utf-8")
        imediatos_path.write_text(imediatos_novo, encoding="utf-8")
        teste_path.write_text(testes_novos, encoding="utf-8")

        # Reabre o conteúdo efetivamente escrito.
        validar(
            contexto_path.read_text(encoding="utf-8"),
            imediatos_path.read_text(encoding="utf-8"),
            teste_path.read_text(encoding="utf-8"),
        )

        subprocess.run(
            [
                sys.executable, "-m", "py_compile",
                str(CONTEXTO_REL), str(IMEDIATOS_REL), str(TESTE_REL),
            ],
            cwd=raiz,
            check=True,
        )

        if not args.sem_testes:
            suites = [str(TESTE_REL)]
            for rel in (
                Path("tests/test_p0_autorizacao_modalidade.py"),
                Path("tests/test_p0_autopreservacao_executor.py"),
                Path("tests/test_regressoes_roteiro_118.py"),
            ):
                if (raiz / rel).is_file():
                    suites.append(str(rel))
            subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *suites],
                cwd=raiz,
                check=True,
            )

    except Exception as erro:
        print(f"\nERRO: {type(erro).__name__}: {erro}")
        print("Restaurando estado anterior...")
        restaurar(pares)
        print("✓ Restauração concluída.")
        return 1

    print("\n✓ P0.2A v2 aplicada com sucesso.")
    print(f"Backup: {backup_raiz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
