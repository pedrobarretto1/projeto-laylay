from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.analises import analisar_neural_v27_list_windows_caos as analisador


def test_analisador_organizado_resolve_fontes_e_preserva_destinos_de_modelos():
    raiz = Path(__file__).resolve().parents[2]
    assert analisador.RAIZ == raiz
    assert analisador.ROTEIRO == raiz / "scripts/roteiros/roteiro_neural_v27_list_windows_caos.py"
    assert analisador.ROTEIRO.is_file()
    assert analisador.CAMINHO_ATIVO == raiz / "memoria/neural/modelo_ativo.joblib"
    assert analisador.CAMINHO_EVENTOS == raiz / "memoria/neural/shadow_eventos.jsonl"


def test_import_fora_da_raiz_nao_inicia_analise_ou_carrega_modelos(tmp_path):
    codigo = (
        "import runpy,sys; from pathlib import Path; "
        "ns=runpy.run_path(sys.argv[1], run_name='analisador_testado'); "
        "assert ns['ROTEIRO'].is_file(); "
        "assert (ns['RAIZ'] / 'laylay.py').is_file()"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, analisador.__file__],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout == ""
    assert not list(tmp_path.iterdir())


def test_eventos_shadow_ignora_linha_nul_e_declara_ledger_degradado(
    tmp_path,
    monkeypatch,
) -> None:
    caminho = tmp_path / "shadow_eventos.jsonl"
    evento = {
        "ts": 100.0,
        "modelo": analisador.VERSAO_CANDIDATA,
        "texto_hash": "hash-alvo",
        "tipo": "comparacao_turno",
        "somente_observacao": True,
        "autoriza_execucao": False,
        "predicao_propria_vira_label": False,
    }
    caminho.write_bytes(
        (json.dumps(evento) + "\n").encode("utf-8")
        + (b"\x00" * 32)
        + b"\n"
    )
    monkeypatch.setattr(analisador, "CAMINHO_EVENTOS", caminho)

    eventos, linhas_invalidas = analisador._eventos_shadow(
        hashes={"hash-alvo"},
        inicio=95.0,
        fim=105.0,
    )

    assert eventos == [evento]
    assert linhas_invalidas == 1


def test_planos_completos_preferem_ultimo_snapshot_valido_e_mapeiam_por_comando(
    tmp_path,
) -> None:
    caminho = tmp_path / "planos.jsonl"
    registros = [
        {
            "indice": 0,
            "comando": "O Opera está aberto?",
            "plano": {"contrato_fala": {"estrategia": "antiga"}},
        },
        {
            "indice": 0,
            "comando": "O Opera está aberto?",
            "plano": {"contrato_fala": {"estrategia": "resultado_observado"}},
        },
        {
            "indice": 1,
            "comando": "comando divergente",
            "plano": {"contrato_fala": {"estrategia": "nao_usar"}},
        },
    ]
    caminho.write_bytes(
        b"".join(
            (json.dumps(item, ensure_ascii=False) + "\n").encode("utf-8")
            for item in registros
        )
        + (b"\x00" * 16)
        + b"\n"
    )

    planos, diagnostico = analisador._carregar_planos_completos(
        caminho,
        comandos=("O Opera está aberto?", "A Calculadora continua aberta?"),
    )

    assert planos == {
        0: {"contrato_fala": {"estrategia": "resultado_observado"}},
    }
    assert diagnostico == {
        "linhas_invalidas": 1,
        "registros_descartados": 1,
        "turnos_com_plano_completo": 1,
        "turnos_sem_plano_completo": [2],
    }
