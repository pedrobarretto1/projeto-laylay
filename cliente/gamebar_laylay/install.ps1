[CmdletBinding()]
param([switch]$ForceReinstall)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Artifacts = Join-Path $ProjectDir 'artifacts'
$Certificate = Join-Path $Artifacts 'Laylay.GameBarWidget.cer'
$Package = Join-Path $Artifacts 'Laylay.GameBarWidget.msix'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdministrator) {
    $forceArgument = if ($ForceReinstall) { ' -ForceReinstall' } else { '' }
    $argumentLine = ('-NoProfile -ExecutionPolicy Bypass -File "{0}"{1}' -f $MyInvocation.MyCommand.Path, $forceArgument)
    $elevated = Start-Process -FilePath 'powershell.exe' -ArgumentList $argumentLine -Verb RunAs -Wait -PassThru
    exit $elevated.ExitCode
}

if (-not (Test-Path -LiteralPath $Package)) {
    throw 'Pacote não encontrado. Execute build.ps1 primeiro.'
}
if (-not (Test-Path -LiteralPath $Certificate)) {
    throw 'Certificado de desenvolvimento não encontrado. Execute build.ps1 primeiro.'
}

Import-Certificate -FilePath $Certificate -CertStoreLocation Cert:\CurrentUser\TrustedPeople | Out-Null
# Como o certificado de desenvolvimento é autoassinado, ele também é a própria
# raiz da cadeia. A confiança fica limitada ao usuário atual, sem alterar o
# repositório de certificados da máquina inteira.
Import-Certificate -FilePath $Certificate -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
Import-Certificate -FilePath $Certificate -CertStoreLocation Cert:\LocalMachine\TrustedPeople | Out-Null
Import-Certificate -FilePath $Certificate -CertStoreLocation Cert:\LocalMachine\Root | Out-Null
$Existing = Get-AppxPackage -Name 'Laylay.GameBarWidget'
if ($Existing -and $ForceReinstall) {
    $Existing | Remove-AppxPackage
}
$Dependencies = Get-ChildItem -LiteralPath (Join-Path $Artifacts 'Dependencies\x64') -Filter '*.appx' -File -ErrorAction SilentlyContinue
if ($Dependencies) {
    Add-AppxPackage -Path $Package -DependencyPath $Dependencies.FullName -ForceApplicationShutdown
} else {
    Add-AppxPackage -Path $Package -ForceApplicationShutdown
}

$Installed = Get-AppxPackage -Name 'Laylay.GameBarWidget'
if (-not $Installed) {
    throw 'O Windows não confirmou a instalação do widget.'
}

# UWP roda em AppContainer. A exceção é restrita ao pacote e permite apenas
# que ele alcance a ponte que escuta em 127.0.0.1.
& CheckNetIsolation.exe LoopbackExempt -a "-n=$($Installed.PackageFamilyName)" | Out-Null

Write-Host "Widget instalado: $($Installed.PackageFullName)" -ForegroundColor Green
Write-Host 'Inicie a Laylay, pressione Win + G, abra Widgets > Laylay e fixe o widget.'
Write-Host 'Com ele fixado, ative o click-through no menu da própria Xbox Game Bar.'
