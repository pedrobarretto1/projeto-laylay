[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path (Split-Path -Parent (Split-Path -Parent $ProjectDir)) 'avatar\calma\laylay_calma_512_transparente_real_corrigida.png'
if (-not (Test-Path -LiteralPath $Source)) {
    throw "Avatar base não encontrado: $Source"
}

function Export-ContainedPng {
    param([System.Drawing.Image]$Image, [int]$Width, [int]$Height, [string]$Path)
    $bitmap = New-Object System.Drawing.Bitmap($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.Clear([System.Drawing.Color]::Transparent)
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
        $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $scale = [Math]::Min($Width / $Image.Width, $Height / $Image.Height)
        $drawWidth = [Math]::Max(1, [int][Math]::Round($Image.Width * $scale))
        $drawHeight = [Math]::Max(1, [int][Math]::Round($Image.Height * $scale))
        $x = [int](($Width - $drawWidth) / 2)
        $y = [int](($Height - $drawHeight) / 2)
        $graphics.DrawImage($Image, $x, $y, $drawWidth, $drawHeight)
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

$image = [System.Drawing.Image]::FromFile($Source)
try {
    $specs = @(
        @{ Path = 'Assets\StoreLogo.png'; Width = 50; Height = 50 },
        @{ Path = 'Assets\Square150x150Logo.png'; Width = 150; Height = 150 },
        @{ Path = 'Assets\Square44x44Logo.png'; Width = 44; Height = 44 },
        @{ Path = 'Assets\Wide310x150Logo.png'; Width = 310; Height = 150 },
        @{ Path = 'Assets\SplashScreen.png'; Width = 620; Height = 300 },
        @{ Path = 'Widget\Icons\icon.targetsize-16.png'; Width = 16; Height = 16 },
        @{ Path = 'Widget\Icons\icon.targetsize-20.png'; Width = 20; Height = 20 },
        @{ Path = 'Widget\Icons\icon.targetsize-24.png'; Width = 24; Height = 24 },
        @{ Path = 'Widget\Icons\icon.targetsize-32.png'; Width = 32; Height = 32 },
        @{ Path = 'Widget\Icons\icon.targetsize-44.png'; Width = 44; Height = 44 },
        @{ Path = 'Widget\Icons\icon.targetsize-256.png'; Width = 256; Height = 256 }
    )
    foreach ($spec in $specs) {
        Export-ContainedPng -Image $image -Width $spec.Width -Height $spec.Height -Path (Join-Path $ProjectDir $spec.Path)
    }
}
finally {
    $image.Dispose()
}
