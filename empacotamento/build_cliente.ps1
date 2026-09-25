param([switch]$PularInstalacaoDependencias)
$ErrorActionPreference = 'Stop'
$RaizCliente = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$PythonBaseCliente = Join-Path $RaizCliente '.venv314/Scripts/python.exe'
$PythonBuildCliente = Join-Path $RaizCliente '.venv-build-cliente/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $PythonBuildCliente)) {
    & $PythonBaseCliente -m venv (Join-Path $RaizCliente '.venv-build-cliente')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar ambiente de build.' }
}
if (-not $PularInstalacaoDependencias) {
    & $PythonBuildCliente -m pip install -r (Join-Path $PSScriptRoot 'requirements-cliente.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências.' }
}
# Cada build tem destino novo: não apaga ou sobrescreve executáveis anteriores.
$IdBuildCliente = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$DestinoCliente = Join-Path $RaizCliente "dist/cliente_pc_b-$IdBuildCliente"
$TrabalhoCliente = Join-Path $RaizCliente "build/cliente_pc_b-$IdBuildCliente"
& $PythonBuildCliente -m PyInstaller --distpath $DestinoCliente --workpath $TrabalhoCliente (Join-Path $RaizCliente 'cliente/cliente_laylay.spec')
if ($LASTEXITCODE -ne 0) { throw 'Falha no empacotamento do cliente.' }
Write-Output (Join-Path $DestinoCliente 'cliente_laylay.exe')
