param([switch]$Compartilhamento, [switch]$ReiniciarDhcp)
$ErrorActionPreference = 'Stop'
if ($Compartilhamento -or $ReiniciarDhcp) {
    $gerenteCompartilhamento = New-Object -ComObject HNetCfg.HNetShare
    $conexoesCompartilhamento = @()
    foreach ($conexaoCompartilhamento in $gerenteCompartilhamento.EnumEveryConnection) {
        $propriedadesCompartilhamento = $gerenteCompartilhamento.NetConnectionProps($conexaoCompartilhamento)
        $configCompartilhamento = $gerenteCompartilhamento.INetSharingConfigurationForINetConnection($conexaoCompartilhamento)
        $conexoesCompartilhamento += @{
            nome=$propriedadesCompartilhamento.Name
            dispositivo=$propriedadesCompartilhamento.DeviceName
            guid=$propriedadesCompartilhamento.Guid
            compartilhamento_ativo=[bool]$configCompartilhamento.SharingEnabled
            tipo=if ($configCompartilhamento.SharingEnabled) { [int]$configCompartilhamento.SharingConnectionType } else { $null }
        }
    }
    $destinoCompartilhamento = Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts\rosto_oled\wifi\compartilhamento_windows.json'
    @{horario=[DateTime]::Now.ToString('s');conexoes=$conexoesCompartilhamento} | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath $destinoCompartilhamento -Encoding UTF8
    if ($ReiniciarDhcp) {
        if ($conexoesCompartilhamento | Where-Object compartilhamento_ativo) {
            throw 'Outro compartilhamento ativo; nao reiniciar o servico.'
        }
        $reciboRedeCorpo=Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts\rosto_oled\wifi\hotspot_windows.json'
        $redeCorpo=Get-Content -LiteralPath $reciboRedeCorpo -Raw | ConvertFrom-Json
        if ($redeCorpo.estado -ne 'encerrando' -or (Get-Process -Id $redeCorpo.pid -ErrorAction SilentlyContinue)) {
            throw 'A rede do teste deve estar encerrada antes da reinicializacao.'
        }
        Stop-Service -Name SharedAccess
        (Get-Service SharedAccess).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(5))
    }
    exit
}
$null = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime]
$null = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime]
$perfilConexao = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
if ($null -eq $perfilConexao) {
    Write-Output 'SEM_PERFIL_INTERNET'
    exit 1
}
$capacidadeHotspot = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::GetTetheringCapabilityFromConnectionProfile($perfilConexao)
Write-Output ('CAPACIDADE=' + $capacidadeHotspot)
if ($capacidadeHotspot.ToString() -eq 'Enabled') {
    $gerenteHotspot = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($perfilConexao)
    Write-Output ('ESTADO=' + $gerenteHotspot.TetheringOperationalState)
    Write-Output ('CLIENTES=' + $gerenteHotspot.ClientCount)
}
