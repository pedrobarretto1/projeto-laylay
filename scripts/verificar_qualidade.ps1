param(
    [string]$Python = ".\.venv314\Scripts\python.exe",
    [switch]$SemAuditoria
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python do projeto não encontrado em $Python"
}

& $Python -m compileall -q laylay.py mente_laylay tests
if ($LASTEXITCODE -ne 0) { throw "compileall falhou" }

& $Python -m ruff check laylay.py mente_laylay tests
if ($LASTEXITCODE -ne 0) { throw "Ruff encontrou uma regressão crítica" }

& $Python -m mypy --follow-imports=skip `
    mente_laylay/integracao/politicas_composicao.py `
    mente_laylay/percepcao/visao_jogo/analise_visual.py `
    mente_laylay/percepcao/visao_jogo/pesquisa_sintese.py `
    mente_laylay/memoria_mental/observabilidade.py
if ($LASTEXITCODE -ne 0) { throw "mypy encontrou regressão nos módulos tipados" }

& $Python -m coverage erase
& $Python -m coverage run -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "a suíte de testes falhou" }
& $Python -m coverage report
if ($LASTEXITCODE -ne 0) { throw "a cobertura caiu abaixo da base" }

if (-not $SemAuditoria) {
    & $Python -m pip_audit -r requirements.txt --progress-spinner off
    if ($LASTEXITCODE -ne 0) { throw "a auditoria encontrou dependência vulnerável" }
}

Write-Host "Qualidade estrutural, testes e dependências verificados."
