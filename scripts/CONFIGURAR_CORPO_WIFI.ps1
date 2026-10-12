$ErrorActionPreference = 'Stop'
$raizLaylay = Split-Path -Parent $PSScriptRoot
$pythonLaylay = Join-Path $raizLaylay '.venv314\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonLaylay)) {
    throw 'O ambiente Python da Laylay não foi encontrado.'
}
# A senha é solicitada pela janela, nunca por argumento ou variável de ambiente.
Start-Process -FilePath $pythonLaylay -ArgumentList @('-m', 'scripts.configurar_corpo_wifi') -WorkingDirectory $raizLaylay -WindowStyle Hidden
