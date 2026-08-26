param(
    [string]$Modelo = "Qwen3:4b-instruct",
    [string]$Destino = ""
)

$ErrorActionPreference = "Stop"
$Raiz = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if (-not $Destino) {
    $Destino = Join-Path $Raiz "modelos\laylay-qwen3-4b-q4_k_m.gguf"
}
$Destino = [System.IO.Path]::GetFullPath($Destino)
$PastaModelos = [System.IO.Path]::GetFullPath((Join-Path $Raiz "modelos"))
if (-not $Destino.StartsWith($PastaModelos, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "O destino do modelo precisa permanecer dentro de $PastaModelos"
}

$Ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $Ollama) {
    throw "Ollama não foi encontrado neste PC. Importe o GGUF manualmente para $Destino"
}

$Modelfile = (& $Ollama.Source show $Modelo --modelfile 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) {
    throw "Não consegui consultar o modelo '$Modelo': $Modelfile"
}
$LinhaFrom = $Modelfile -split "`r?`n" | Where-Object { $_ -match '^FROM\s+' } | Select-Object -First 1
if (-not $LinhaFrom) {
    throw "Ollama não informou o arquivo-base do modelo."
}
$Origem = ($LinhaFrom -replace '^FROM\s+', '').Trim().Trim('"')
if (-not (Test-Path -LiteralPath $Origem -PathType Leaf)) {
    throw "O blob informado pelo Ollama não existe: $Origem"
}

$Stream = [System.IO.File]::OpenRead($Origem)
try {
    $Cabecalho = New-Object byte[] 4
    [void]$Stream.Read($Cabecalho, 0, 4)
    $Assinatura = [System.Text.Encoding]::ASCII.GetString($Cabecalho)
} finally {
    $Stream.Dispose()
}
if ($Assinatura -ne "GGUF") {
    throw "O blob encontrado não é um modelo GGUF compatível."
}

New-Item -ItemType Directory -Path (Split-Path -Parent $Destino) -Force | Out-Null
$TamanhoGb = [math]::Round((Get-Item -LiteralPath $Origem).Length / 1GB, 2)
Write-Host "Importando $Modelo ($TamanhoGb GB)..."
Copy-Item -LiteralPath $Origem -Destination $Destino -Force
Write-Host "Modelo portátil pronto em: $Destino"
