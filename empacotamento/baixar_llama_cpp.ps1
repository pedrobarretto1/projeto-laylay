param(
    [switch]$Forcar
)

$ErrorActionPreference = "Stop"
$Raiz = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$Runtime = [System.IO.Path]::GetFullPath((Join-Path $Raiz "runtime_llm"))
if (-not $Runtime.StartsWith($Raiz, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Destino do runtime saiu da raiz do projeto."
}
New-Item -ItemType Directory -Path $Runtime -Force | Out-Null

$Headers = @{ "User-Agent" = "Laylay-Portable-Builder" }
$Release = Invoke-RestMethod -Uri "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest" -Headers $Headers

function Instalar-Variante {
    param([string]$Nome, [string]$Padrao)
    $Destino = Join-Path $Runtime $Nome
    $Servidor = Join-Path $Destino "llama-server.exe"
    if ((Test-Path -LiteralPath $Servidor) -and -not $Forcar) {
        Write-Host "llama.cpp $Nome já está preparado."
        return
    }
    $Asset = $Release.assets | Where-Object { $_.name -like $Padrao } | Select-Object -First 1
    if (-not $Asset) {
        throw "Não encontrei o pacote oficial $Padrao na versão $($Release.tag_name)."
    }
    $Cache = Join-Path $Raiz "build_portatil\downloads"
    New-Item -ItemType Directory -Path $Cache -Force | Out-Null
    $Zip = Join-Path $Cache $Asset.name
    Write-Host "Baixando $($Asset.name)..."
    Invoke-WebRequest -Uri $Asset.browser_download_url -OutFile $Zip -Headers $Headers

    $Temporario = Join-Path $Raiz ("build_portatil\extracao_" + $Nome)
    $TemporarioResolvido = [System.IO.Path]::GetFullPath($Temporario)
    if (-not $TemporarioResolvido.StartsWith($Raiz, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Diretório temporário inválido."
    }
    if (Test-Path -LiteralPath $TemporarioResolvido) {
        Remove-Item -LiteralPath $TemporarioResolvido -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TemporarioResolvido -Force | Out-Null
    Expand-Archive -LiteralPath $Zip -DestinationPath $TemporarioResolvido -Force
    if (Test-Path -LiteralPath $Destino) {
        Remove-Item -LiteralPath $Destino -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Destino -Force | Out-Null
    # O servidor usa as DLLs da variante; as outras ferramentas de linha de
    # comando do pacote oficial não participam da Laylay portátil.
    Get-ChildItem -LiteralPath $TemporarioResolvido -Recurse -File | Where-Object {
        $_.Extension -eq ".dll" -or $_.Name -eq "llama-server.exe"
    } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Destino $_.Name) -Force
    }
    Remove-Item -LiteralPath $TemporarioResolvido -Recurse -Force
    if (-not (Test-Path -LiteralPath $Servidor)) {
        throw "O pacote $Nome não continha llama-server.exe."
    }
    Write-Host "Runtime $Nome pronto."
}

# Vulkan cobre NVIDIA, AMD e Intel com o driver gráfico instalado; CPU é o fallback.
Instalar-Variante -Nome "vulkan" -Padrao "*bin-win-vulkan-x64.zip"
Instalar-Variante -Nome "cpu" -Padrao "*bin-win-cpu-x64.zip"

$Licenca = Join-Path $Runtime "LICENSE-llama.cpp"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE" -OutFile $Licenca -Headers $Headers
Write-Host "Motores portáteis preparados em: $Runtime"
