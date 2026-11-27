param(
    [switch]$Preparar,
    [switch]$SomentePreparar,
    [string]$AmbientePython = (Join-Path $env:LOCALAPPDATA 'Laylay\python314')
)

$ErrorActionPreference = 'Stop'
$Raiz = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Python = Join-Path $AmbientePython 'Scripts\python.exe'

if ($Preparar -or $SomentePreparar) {
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        $Launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if (-not $Launcher) { throw 'Instale Python 3.14 para Windows com o inicializador py.exe.' }
        & $Launcher.Source -3.14 -m venv $AmbientePython
        if ($LASTEXITCODE -ne 0) { throw 'Não consegui criar o ambiente Python 3.14.' }
    }
    & $Python -m pip install -r (Join-Path $Raiz 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar as dependências da Laylay.' }
    $Configuracao = Join-Path $Raiz 'configuracao.env'
    if (-not (Test-Path -LiteralPath $Configuracao)) {
        [IO.File]::Copy((Join-Path $Raiz 'configuracao.codigo.example.env'), $Configuracao)
    }
    if ($SomentePreparar) { return }
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw 'Ambiente Python ausente. Execute este script com -Preparar.'
}

Push-Location -LiteralPath $Raiz
try {
    & $Python (Join-Path $Raiz 'laylay.py')
    $Codigo = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $Codigo
