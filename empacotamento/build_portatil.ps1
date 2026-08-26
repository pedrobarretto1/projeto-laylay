param(
    [switch]$IncluirMemoriaPessoal,
    [switch]$IncluirConfiguracoesPrivadas,
    [switch]$SemModelo,
    [switch]$SemDownloadRuntime,
    [switch]$PularInstalacaoDependencias
)

$ErrorActionPreference = "Stop"
$Raiz = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$Build = [System.IO.Path]::GetFullPath((Join-Path $Raiz "build_portatil"))
$Dist = [System.IO.Path]::GetFullPath((Join-Path $Build "dist"))
$Work = [System.IO.Path]::GetFullPath((Join-Path $Build "work"))
foreach ($Caminho in @($Build, $Dist, $Work)) {
    if (-not $Caminho.StartsWith($Raiz, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Caminho de build inválido: $Caminho"
    }
}

$PythonCandidatos = @(
    (Join-Path $Raiz ".venv314\Scripts\python.exe"),
    (Join-Path $Raiz ".venv\Scripts\python.exe"),
    (Join-Path $Raiz ".venv-1\Scripts\python.exe")
)
$Python = $PythonCandidatos | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $Python) {
    $ComandoPython = Get-Command python -ErrorAction SilentlyContinue
    if ($ComandoPython) { $Python = $ComandoPython.Source }
}
if (-not $Python) {
    throw "Python não foi encontrado no PC de desenvolvimento."
}

if (-not $SemDownloadRuntime) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "baixar_llama_cpp.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Falha ao preparar llama.cpp." }
}
if (-not $SemModelo) {
    $ModeloLocal = Join-Path $Raiz "modelos\laylay-qwen3-4b-q4_k_m.gguf"
    if (Test-Path -LiteralPath $ModeloLocal -PathType Leaf) {
        Write-Host "Modelo GGUF já preparado; reutilizando o arquivo local."
    } else {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "importar_modelo_ollama.ps1")
        if ($LASTEXITCODE -ne 0) { throw "Falha ao importar o modelo GGUF." }
    }
}

if (-not $PularInstalacaoDependencias) {
    & $Python -m pip install -r (Join-Path $Raiz "requirements.txt") -r (Join-Path $Raiz "requirements-build.txt")
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências de build." }
}

# Uma montagem nova nunca pode herdar memória ou credenciais de outra. Limpar
# apenas dist/work preserva downloads grandes já verificados no cache do build.
foreach ($CaminhoLimpo in @($Dist, $Work)) {
    $Resolvido = [System.IO.Path]::GetFullPath($CaminhoLimpo)
    if (Test-Path -LiteralPath $CaminhoLimpo) {
        if (-not $Resolvido.StartsWith($Build, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Recusei limpar caminho fora da área de build: $Resolvido"
        }
        Remove-Item -LiteralPath $Resolvido -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Resolvido -Force | Out-Null
}

Write-Host "Compilando Laylay.exe..."
& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath (Join-Path $Work "laylay") (Join-Path $PSScriptRoot "Laylay.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ao gerar Laylay.exe." }

Write-Host "Compilando o processo independente do avatar..."
& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath (Join-Path $Work "avatar") (Join-Path $PSScriptRoot "AvatarLaylay.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ao gerar AvatarLaylay.exe." }

Write-Host "Compilando o inicializador em uma janela do CMD..."
& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath (Join-Path $Work "launcher") (Join-Path $PSScriptRoot "IniciarLaylay.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ao gerar Iniciar Laylay.exe." }

$Pacote = [System.IO.Path]::GetFullPath((Join-Path $Dist "Laylay"))
if (-not $Pacote.StartsWith($Dist, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Destino final inválido."
}
Copy-Item -LiteralPath (Join-Path $Dist "AvatarLaylay.exe") -Destination (Join-Path $Pacote "AvatarLaylay.exe") -Force
Copy-Item -LiteralPath (Join-Path $Dist "Iniciar Laylay.exe") -Destination (Join-Path $Pacote "Iniciar Laylay.exe") -Force

function Copiar-Pasta {
    param([string]$Origem, [string]$NomeDestino)
    if (-not (Test-Path -LiteralPath $Origem -PathType Container)) { return }
    $Destino = Join-Path $Pacote $NomeDestino
    if (Test-Path -LiteralPath $Destino) { Remove-Item -LiteralPath $Destino -Recurse -Force }
    Copy-Item -LiteralPath $Origem -Destination $Destino -Recurse -Force
}

Copiar-Pasta (Join-Path $Raiz "avatar") "avatar"
Copiar-Pasta (Join-Path $Raiz "runtime_llm") "runtime_llm"
if (-not $SemModelo) { Copiar-Pasta (Join-Path $Raiz "modelos") "modelos" }
Copiar-Pasta (Join-Path $Raiz "extençao_google") "extensao_chrome"

$ConfigDestino = Join-Path $Pacote "configuracao.env"
if ($IncluirConfiguracoesPrivadas -and (Test-Path -LiteralPath (Join-Path $Raiz "configuracao.env"))) {
    Copy-Item -LiteralPath (Join-Path $Raiz "configuracao.env") -Destination $ConfigDestino -Force
} else {
    Copy-Item -LiteralPath (Join-Path $Raiz "configuracao.portatil.example.env") -Destination $ConfigDestino -Force
}

$MemoriaDestino = Join-Path $Pacote "memoria"
if ($IncluirMemoriaPessoal) {
    Copiar-Pasta (Join-Path $Raiz "memoria") "memoria"
    foreach ($Arquivo in @("playlists.json")) {
        $OrigemArquivo = Join-Path $Raiz $Arquivo
        if (Test-Path -LiteralPath $OrigemArquivo -PathType Leaf) {
            Copy-Item -LiteralPath $OrigemArquivo -Destination (Join-Path $Pacote $Arquivo) -Force
        }
    }
} else {
    New-Item -ItemType Directory -Path $MemoriaDestino -Force | Out-Null
}
if ($IncluirConfiguracoesPrivadas) {
    foreach ($Arquivo in @("devices.json", "tinytuya.json", "snapshot.json", "tuya-raw.json")) {
        $OrigemArquivo = Join-Path $Raiz $Arquivo
        if (Test-Path -LiteralPath $OrigemArquivo -PathType Leaf) {
            Copy-Item -LiteralPath $OrigemArquivo -Destination (Join-Path $Pacote $Arquivo) -Force
        }
    }
    Copiar-Pasta (Join-Path $Raiz "dados\voz_pessoal") "dados\voz_pessoal"
}

foreach ($Arquivo in @("README_PORTATIL.md", "LICENCAS_TERCEIROS.md", "RELATORIO_DISTRIBUICAO_P13.md")) {
    $OrigemArquivo = Join-Path $PSScriptRoot $Arquivo
    if (Test-Path -LiteralPath $OrigemArquivo) {
        Copy-Item -LiteralPath $OrigemArquivo -Destination (Join-Path $Pacote $Arquivo) -Force
    }
}

Write-Host "Auditando privacidade e estrutura do pacote..."
$ArgsAuditoria = @(
    (Join-Path $PSScriptRoot "verificar_pacote.py"),
    $Pacote,
    "--raiz-projeto", $Raiz
)
if ($SemModelo) { $ArgsAuditoria += "--sem-modelo" }
if ($IncluirMemoriaPessoal) { $ArgsAuditoria += "--permitir-memoria" }
if ($IncluirConfiguracoesPrivadas) { $ArgsAuditoria += "--permitir-privados" }
& $Python @ArgsAuditoria
if ($LASTEXITCODE -ne 0) { throw "A auditoria recusou o pacote portátil." }

Write-Host "Executando smoke test dentro do Laylay.exe..."
$SmokeAnterior = $env:LAYLAY_SMOKE_DISTRIBUICAO
$ExigirModeloAnterior = $env:LAYLAY_SMOKE_EXIGIR_MODELO
try {
    $env:LAYLAY_SMOKE_DISTRIBUICAO = "1"
    $env:LAYLAY_SMOKE_EXIGIR_MODELO = $(if ($SemModelo) { "0" } else { "1" })
    & (Join-Path $Pacote "Laylay.exe")
    if ($LASTEXITCODE -ne 0) { throw "O smoke test do executável portátil falhou." }
} finally {
    $env:LAYLAY_SMOKE_DISTRIBUICAO = $SmokeAnterior
    $env:LAYLAY_SMOKE_EXIGIR_MODELO = $ExigirModeloAnterior
}

$TamanhoGb = [math]::Round(((Get-ChildItem -LiteralPath $Pacote -Recurse -File | Measure-Object Length -Sum).Sum / 1GB), 2)
Write-Host ""
Write-Host "Laylay portátil pronta: $Pacote"
Write-Host "Tamanho aproximado: $TamanhoGb GB"
Write-Host "No outro PC, abra Laylay.exe. Python e Ollama não são necessários."
if (-not $IncluirMemoriaPessoal) {
    Write-Host "A memória pessoal não foi incluída. Use -IncluirMemoriaPessoal se o destino for seu e confiável."
}
