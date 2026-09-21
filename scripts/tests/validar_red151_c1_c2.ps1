$ErrorActionPreference = "Stop"
$env:GIT_PAGER = "cat"

Write-Host ""
Write-Host "RED151 - VALIDACAO FOCADA C1 + C2" -ForegroundColor Cyan
Write-Host ("=" * 72)

$python = "python"
if (Test-Path ".\.venv314\Scripts\python.exe") {
    $python = ".\.venv314\Scripts\python.exe"
}

$head = (git rev-parse --short HEAD).Trim()
Write-Host "HEAD ...............: $head"

Write-Host ""
Write-Host "Diff causal atual:"
git diff --no-ext-diff -- mente_laylay/autonomia/fluxos_conversa.py

$testes = @(
    "tests/test_red151_playlist_confirmacao_CANONICO_C2.py",
    "tests/test_red151_contrato_pre_fluxo_feedback_playlist.py",
    "tests/test_red151_feedback_playlist_fail_closed.py",
    "tests/test_red151_feedback_playlist_pre_fluxo.py"
)

$existentes = @()
$ausentes = @()

foreach ($teste in $testes) {
    if (Test-Path $teste) {
        $existentes += $teste
    } else {
        $ausentes += $teste
    }
}

Write-Host ""
Write-Host "Testes encontrados:" -ForegroundColor Cyan
foreach ($teste in $existentes) {
    Write-Host "  + $teste"
}

if ($ausentes.Count -gt 0) {
    Write-Host ""
    Write-Host "Testes ausentes (serao ignorados):" -ForegroundColor Yellow
    foreach ($teste in $ausentes) {
        Write-Host "  - $teste"
    }
}

if ($existentes.Count -eq 0) {
    Write-Host ""
    Write-Host "ERRO: nenhum teste RED151 focado foi encontrado." -ForegroundColor Red
    exit 2
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = "validacao_red151_c1_c2_$timestamp.log"

Write-Host ""
Write-Host "Executando suite focada..." -ForegroundColor Cyan
Write-Host "Log: $log"
Write-Host ""

$argumentos = @("-m", "pytest", "-vv") + $existentes

& $python @argumentos 2>&1 | Tee-Object -FilePath $log
$codigo = $LASTEXITCODE

Write-Host ""
Write-Host ("=" * 72)

if ($codigo -eq 0) {
    Write-Host "GREEN FOCADO: todos os testes RED151 encontrados passaram." -ForegroundColor Green
} else {
    Write-Host "RED FOCADO: pelo menos um teste RED151 falhou." -ForegroundColor Red
    Write-Host "Nao aplique novo patch ainda; a primeira fronteira RED manda." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Produção nao foi modificada por este validador."
Write-Host "Log salvo em: $log"

exit $codigo
