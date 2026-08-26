[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Installer = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\setup.exe'
$VsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $Installer) -or -not (Test-Path -LiteralPath $VsWhere)) {
    throw 'Visual Studio Installer não foi encontrado.'
}

$InstallPath = & $VsWhere -latest -version '[17.0,18.0)' -products Microsoft.VisualStudio.Product.BuildTools -property installationPath
if (-not $InstallPath) {
    throw 'Visual Studio Build Tools 2022 não foi encontrado.'
}

# Start-Process transforma arrays em uma linha de comando. Sem aspas
# explícitas, "C:\Program Files..." chegava ao instalador como "C:\Program".
$escapedInstallPath = $InstallPath.Replace('"', '\"')
$arguments = @(
    'modify'
    '--installPath'
    ('"{0}"' -f $escapedInstallPath)
    '--add'
    'Microsoft.VisualStudio.Workload.UniversalBuildTools'
    '--includeRecommended'
    '--passive'
    '--norestart'
)

Write-Host 'O instalador solicitará permissão de administrador e adicionará as ferramentas UWP.'
$process = Start-Process -FilePath $Installer -ArgumentList $arguments -Verb RunAs -Wait -PassThru
if ($process.ExitCode -notin 0, 3010) {
    throw "Visual Studio Installer encerrou com código $($process.ExitCode)."
}
Write-Host 'UWP Build Tools instalada. Agora execute build.ps1.' -ForegroundColor Green
