"""Contrato do diagnóstico optativo; estímulos locais, sem sessão Laylay."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

from scripts.analises.sonda_caminhos_absolutos_real import _BOOTSTRAP_DIAGNOSTICO_PLANO


def _controle(tmp_path: Path, *, destino_indisponivel: bool = False) -> tuple[dict, list[dict]]:
    programa = tmp_path / "controle.py"
    programa.write_text(textwrap.dedent('''
        import json, sys
        from pathlib import Path
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.conversas_runtime import GerenciadorConversasRuntime
        from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime

        base = Path(sys.argv[1])
        estado = EstadoCompartilhadoRuntime()
        conversas = GerenciadorConversasRuntime(
            memoria_sqlite=MemoriaSQLite(str(base / "memoria.sqlite")),
            estado_compartilhado=estado, base_system_prompt="controle",
        )
        antiga = conversas.criar("controle A")["id"]
        atual = conversas.criar("controle B")["id"]
        estado.atualizar_campos("mental", plano_turno_atual={"id": "turno-controle", "comandos": []})
        antes = estado.snapshot()
        assert conversas.selecionar(atual)["id"] == atual
        assert estado.snapshot() == antes, "selecionar o mesmo chat preserva o frame"
        assert conversas.selecionar("inexistente") is None
        assert estado.snapshot() == antes, "seleção recusada preserva o frame"
        assert conversas.selecionar(antiga)["id"] == antiga
        print("CONTROLE " + json.dumps({
            "antiga": antiga, "atual": atual, "ativa": conversas.id_ativo(),
            "plano_final": dict(estado.mental["plano_turno_atual"]),
        }), flush=True)
    '''), encoding="utf-8")
    destino = tmp_path / "publicacoes.jsonl"
    if destino_indisponivel:
        destino.mkdir()
    processo = subprocess.run(
        [sys.executable, "-c", _BOOTSTRAP_DIAGNOSTICO_PLANO, str(programa), str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_SONDA_PUBLICACOES_PLANO=str(destino)),
        capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    assert processo.returncode == 0, processo.stderr
    resultado = next(json.loads(linha.removeprefix("CONTROLE "))
                     for linha in processo.stdout.splitlines() if linha.startswith("CONTROLE "))
    registros = [] if destino_indisponivel else [
        json.loads(linha) for linha in destino.read_text(encoding="utf-8").splitlines() if linha
    ]
    return resultado, registros


def test_diagnostico_identifica_selecao_que_limpa_frame_sem_mudar_resultado(tmp_path: Path) -> None:
    resultado, registros = _controle(tmp_path)
    assert resultado["ativa"] == resultado["antiga"] and resultado["plano_final"] == {}
    chamadas = [r for r in registros if r.get("api") == "conversa.selecionar"]
    finais = [r for r in chamadas if r.get("etapa") == "retorno"]
    assert len(finais) == 3, "faltam chamadas do owner de conversa, inclusive seleções sem efeito"
    troca = finais[-1]
    assert troca["conversa_antes"] == resultado["atual"]
    assert troca["conversa_depois"] == resultado["antiga"]
    assert troca["antes"]["plano_id"] == "turno-controle" and not troca["depois"]["plano_id"]
    assert troca["pid"] > 0 and troca["thread"] == "MainThread" and troca["pilha"]
    assert any(r.get("etapa") == "entrada" for r in chamadas)
    assert "controle A" not in json.dumps(registros), "títulos e mensagens não pertencem ao diagnóstico"


def test_diagnostico_identifica_writer_de_estado_que_remove_identidade(tmp_path: Path) -> None:
    _, registros = _controle(tmp_path)
    perdas = [r for r in registros if r.get("api") == "substituir"
              and r["antes"]["plano_id"] and not r["depois"]["plano_id"]]
    assert len(perdas) == 1
    assert any(item["funcao"] == "aplicar_contexto_conversa" for item in perdas[0]["pilha"])


def test_falha_de_gravacao_diagnostica_nao_interrompe_owner_de_conversa(tmp_path: Path) -> None:
    resultado, _ = _controle(tmp_path, destino_indisponivel=True)
    assert resultado["ativa"] == resultado["antiga"] and resultado["plano_final"] == {}
