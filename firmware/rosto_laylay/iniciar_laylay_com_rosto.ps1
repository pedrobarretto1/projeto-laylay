param([ValidatePattern('^(COM[0-9]+|AUTO|off)$')][string]$Porta = 'AUTO', [switch]$HotspotLocal)
$ErrorActionPreference = 'Stop'
$raizLaylay = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$pythonLaylay = Join-Path $raizLaylay '.venv314\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonLaylay)) { throw 'Ambiente Python da Laylay ausente.' }
$portaAnterior = $env:LAYLAY_ROSTO_PORTA
$processoHotspotCorpo = $null
Push-Location -LiteralPath $raizLaylay
try {
    if ($HotspotLocal) {
        if ($Porta -ne 'AUTO') { throw 'HotspotLocal requer modo AUTO.' }
        if (-not (Test-Path -LiteralPath (Join-Path $raizLaylay 'memoria\corpo_wifi.json')) -or
            -not (Test-Path -LiteralPath (Join-Path $raizLaylay 'memoria\corpo_hotspot_windows.json'))) {
            throw 'Configure e confirme o corpo na rede local antes de iniciar.'
        }
        $reciboHotspotCorpo = Join-Path $raizLaylay 'artifacts\rosto_oled\wifi\hotspot_windows.json'
        $estadoHotspotCorpo = if (Test-Path -LiteralPath $reciboHotspotCorpo) {
            Get-Content -LiteralPath $reciboHotspotCorpo -Raw | ConvertFrom-Json
        } else { $null }
        $existenteHotspotCorpo = if ($estadoHotspotCorpo -and $estadoHotspotCorpo.estado -eq 'ativo') {
            Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$estadoHotspotCorpo.pid)
        } else { $null }
        $scriptHotspotCorpo = Join-Path $raizLaylay 'scripts\hotspot_corpo_windows.ps1'
        $gerenteExistenteCorpo = $existenteHotspotCorpo -and
            $existenteHotspotCorpo.Name -eq 'powershell.exe' -and
            $existenteHotspotCorpo.CommandLine.Contains($scriptHotspotCorpo)
        if (-not $gerenteExistenteCorpo) {
            $processoHotspotCorpo = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList @(
                '-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$scriptHotspotCorpo+'"'))
            $prazoHotspotCorpo = [DateTime]::UtcNow.AddSeconds(8)
            $prontoHotspotCorpo = $false
            do {
                Start-Sleep -Milliseconds 200
                if (Test-Path -LiteralPath $reciboHotspotCorpo) {
                    $estadoHotspotCorpo = Get-Content -LiteralPath $reciboHotspotCorpo -Raw | ConvertFrom-Json
                    $prontoHotspotCorpo = $estadoHotspotCorpo.pid -eq $processoHotspotCorpo.Id -and
                        $estadoHotspotCorpo.estado -eq 'ativo' -and $estadoHotspotCorpo.conexao_original_preservada
                }
            } until ($prontoHotspotCorpo -or $processoHotspotCorpo.HasExited -or [DateTime]::UtcNow -ge $prazoHotspotCorpo)
            if (-not $prontoHotspotCorpo) { throw 'Windows nao confirmou a rede local; Laylay nao iniciada.' }
        }
    }
    $env:LAYLAY_ROSTO_PORTA = $Porta
    & $pythonLaylay laylay.py
} finally {
    if ($processoHotspotCorpo -and -not $processoHotspotCorpo.HasExited) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $raizLaylay 'scripts\hotspot_corpo_windows.ps1') -Parar
        $null = $processoHotspotCorpo.WaitForExit(5000)
    }
    $env:LAYLAY_ROSTO_PORTA = $portaAnterior
    Pop-Location
}
