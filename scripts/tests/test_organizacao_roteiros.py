"""Contratos de organização: caminhos compatíveis, fontes visíveis, dados privados."""
from pathlib import Path
import subprocess
import sys

import pytest

from mente_laylay.integracao.roteiro_teste_conversa import carregar_configuracao_roteiro

RAIZ = Path(__file__).resolve().parents[2]
ROTEIROS = [
    "roteiro_confirmacoes_recusas.py",
    "roteiro_consulta_conteudo_c3.py",
    "roteiro_dialogo_50_continuacao_segura.py",
    "roteiro_explicacao_capacidades.py",
    "roteiro_fonte_textual_ausente.py",
    "roteiro_iot_explicacoes.py",
    "roteiro_neural_coleta_prospectiva_seguro.py",
    "roteiro_neural_correcao_shadow_seguro.py",
    "roteiro_neural_dialogo_controlado_50_v1.py",
    "roteiro_neural_dialogo_controlado_v1.py",
    "roteiro_neural_v26_shadow_seguro.py",
    "roteiro_neural_v27_list_windows_caos.py",
    "roteiro_neural_v27_list_windows_shadow_seguro.py",
    "roteiro_p0_leitura_sem_autorizacao.py",
    "roteiro_pedidos_modais_validacao.py",
    "roteiro_recomendacao_contextual.py",
    "roteiro_recusas_autoria.py",
    "roteiro_reparo_parcial_conversa.py",
    "roteiro_site_por_assunto.py",
    "roteiro_teste_laylay_caos.py",
    "roteiro_teste_personalidade_viva_p15.py",
    "roteiro_transformacao_conversacional.py"
]


def test_sonda_organizada_resolve_raiz_e_importa_fora_do_cwd(tmp_path):
    sonda = RAIZ / "scripts/roteiros/sonda_transporte_evidencia.py"
    codigo = (
        "import runpy,sys; from pathlib import Path; "
        "ns=runpy.run_path(sys.argv[1], run_name='sonda_testada'); "
        "assert (ns['RAIZ_PROJETO'] / 'laylay.py').is_file(); "
        "import mente_laylay"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, str(sonda)], cwd=tmp_path,
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert resultado.returncode == 0, resultado.stderr


@pytest.mark.parametrize("nome", ROTEIROS)
def test_roteiro_restaurado_carrega_no_diretorio_canonico_e_no_caminho_legado(nome):
    novo = RAIZ / "scripts" / "roteiros" / nome
    assert novo.is_file(), f"Fonte restaurada ausente: {novo}"
    assert carregar_configuracao_roteiro(novo) == carregar_configuracao_roteiro(RAIZ / nome)


def test_caminho_explicito_inexistente_nao_e_substituido_por_roteiro_do_projeto(tmp_path):
    with pytest.raises(FileNotFoundError):
        carregar_configuracao_roteiro(tmp_path / "roteiro_reparo_parcial_conversa.py")


def test_arquivo_explicito_tem_prioridade_sobre_nome_do_catalogo(tmp_path):
    arquivo = tmp_path / "roteiro_reparo_parcial_conversa.py"
    arquivo.write_text('COMANDOS = ("exemplo local",)\n', encoding="utf-8")
    assert carregar_configuracao_roteiro(arquivo).comandos == ("exemplo local",)


@pytest.mark.parametrize("caminho,ignorado", [
    ("tests/test_regressao_nova.py", False),
    ("scripts/roteiros/roteiro_reparo_parcial_conversa.py", False),
    ("configuracao.portatil.example.env", False),
    (".env.example", False),
    ("configuracao.env", True),
    ("resultados_testes/prova/terminal.log", True),
    ("memoria/conversa.txt", True),
    (".playlists.json.caos-backup", True),
    ("conversa.md", True),
    (".r1_v1_backup_pre_candidato/arquivo.py", True),
    ("tests/playlists.json", True),
    ("runtime_llm/cpu/llama-server.exe", True),
])
def test_gitignore_separa_fontes_de_dados_e_artefatos(caminho, ignorado):
    resultado = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", caminho],
        cwd=RAIZ, capture_output=True, text=True, check=False,
    )
    assert resultado.returncode in (0, 1), resultado.stderr
    assert (resultado.returncode == 0) is ignorado, caminho
