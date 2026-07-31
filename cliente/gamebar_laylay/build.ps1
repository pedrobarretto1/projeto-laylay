[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release',
    [ValidateSet('x64')]
    [string]$Platform = 'x64',
    [switch]$SkipCompile
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = Join-Path $ProjectDir 'LaylayGameBar.csproj'
$Artifacts = Join-Path $ProjectDir 'artifacts'
$VsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'

& (Join-Path $ProjectDir 'prepare-assets.ps1')

if (-not (Test-Path -LiteralPath $VsWhere)) {
    throw 'Visual Studio Installer/vswhere não foi encontrado.'
}

$MsBuild = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Workload.UniversalBuildTools -find 'MSBuild\**\Bin\MSBuild.exe' | Select-Object -First 1
if (-not $MsBuild) {
    throw 'Instale a carga UWP Build Tools no Visual Studio Build Tools e execute novamente.'
}

$SdkBin = Get-ChildItem -LiteralPath "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Directory |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName 'x64' } |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ 'makeappx.exe') } |
    Select-Object -First 1
if (-not $SdkBin) {
    throw 'Windows SDK com MakeAppx e SignTool não foi encontrado.'
}

$Certificate = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -eq 'CN=Laylay Development' -and $_.HasPrivateKey -and $_.NotAfter -gt (Get-Date).AddDays(30) } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1
if (-not $Certificate) {
    $Certificate = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject 'CN=Laylay Development' `
        -CertStoreLocation Cert:\CurrentUser\My `
        -HashAlgorithm SHA256 `
        -NotAfter (Get-Date).AddYears(3)
}

New-Item -ItemType Directory -Force -Path $Artifacts | Out-Null
$CerPath = Join-Path $Artifacts 'Laylay.GameBarWidget.cer'
Export-Certificate -Cert $Certificate -FilePath $CerPath -Force | Out-Null

if (-not $SkipCompile) {
    & $MsBuild $Project /restore /t:Rebuild "/p:Configuration=$Configuration" "/p:Platform=$Platform" /p:AppxPackageSigningEnabled=false /m
    if ($LASTEXITCODE -ne 0) { throw "A compilação UWP falhou com código $LASTEXITCODE." }
}

$AppPackages = Join-Path $ProjectDir 'AppPackages'
$GeneratedPackage = Get-ChildItem -LiteralPath $AppPackages -Recurse -Filter '*.msix' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $GeneratedPackage) {
    throw "O MSBuild terminou, mas nenhum MSIX foi encontrado em $AppPackages."
}

$MsixPath = Join-Path $Artifacts 'Laylay.GameBarWidget.msix'
Copy-Item -LiteralPath $GeneratedPackage.FullName -Destination $MsixPath -Force
& (Join-Path $SdkBin 'signtool.exe') sign /fd SHA256 /sha1 $Certificate.Thumbprint $MsixPath
if ($LASTEXITCODE -ne 0) { throw "SignTool falhou com código $LASTEXITCODE." }

$DependencySource = Join-Path $GeneratedPackage.Directory.FullName "Dependencies\$Platform"
$DependencyTarget = Join-Path $Artifacts "Dependencies\$Platform"
if (Test-Path -LiteralPath $DependencySource) {
    New-Item -ItemType Directory -Force -Path $DependencyTarget | Out-Null
    Get-ChildItem -LiteralPath $DependencySource -Filter '*.appx' -File |
        Copy-Item -Destination $DependencyTarget -Force
}

Write-Host "`nPacote pronto: $MsixPath" -ForegroundColor Green
Write-Host "Instale com: powershell -ExecutionPolicy Bypass -File .\install.ps1"
