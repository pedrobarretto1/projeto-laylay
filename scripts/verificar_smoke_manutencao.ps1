param(
    [string]$Python = ".\.venv314\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python do projeto não encontrado em $Python"
}

$TestesCriticos = @(
    "tests/test_confiabilidade_runtime.py::test_inicializacao_registra_controles_antes_das_threads_pesadas",
    "tests/test_confiabilidade_runtime.py::test_ciclo_de_vida_completo_inicia_sinaliza_e_encerra_sem_servico_vivo",
    "tests/test_arbitro_modalidade_inteligente.py::ArbitroModalidadeInteligenteTests::test_turno_misto_separa_conversa_de_comando",
    "tests/test_regressoes_fluxo_real.py::test_musica_para_jogar_e_comando_local_mesmo_com_contexto_do_jogo",
    "tests/test_visao_modo_jogo.py::test_avaliacao_de_item_usa_contexto_visual_e_exige_cursor"
)

& $Python -m pytest -q @TestesCriticos
if ($LASTEXITCODE -ne 0) {
    throw "O smoke test da manutenção encontrou uma regressão crítica."
}

& $Python scripts/gerar_checkpoint_manutencao.py
if ($LASTEXITCODE -ne 0) {
    throw "O checkpoint detectou um risco estrutural ou de privacidade."
}

Write-Host "Smoke test e checkpoint da manutenção aprovados."
