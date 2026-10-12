param([switch]$Parar)
# Hosted Network local: nao altera a rede primaria ou configura ICS completo.
$ErrorActionPreference = 'Stop'
$raizCorpo=Split-Path -Parent $PSScriptRoot
$arquivoCorpo=Join-Path $raizCorpo 'memoria\corpo_hotspot_windows.json'
$paradaCorpo=Join-Path $raizCorpo 'memoria\corpo_hotspot_windows.parar'
$reciboCorpo=Join-Path $raizCorpo 'artifacts\rosto_oled\wifi\hotspot_windows.json'
if ($Parar) { Set-Content -LiteralPath $paradaCorpo -Value 'parar' -Encoding ASCII; exit }
$null=[Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime]
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class WlanCorpo {
 [DllImport("wlanapi.dll")] public static extern uint WlanOpenHandle(uint v, IntPtr r, out uint negotiated, out IntPtr handle);
 [DllImport("wlanapi.dll")] public static extern uint WlanCloseHandle(IntPtr h, IntPtr r);
 [DllImport("wlanapi.dll")] public static extern void WlanFreeMemory(IntPtr p);
 [DllImport("wlanapi.dll")] public static extern uint WlanHostedNetworkQueryStatus(IntPtr h, out IntPtr data, IntPtr r);
 [DllImport("wlanapi.dll")] public static extern uint WlanHostedNetworkQueryProperty(IntPtr h, uint op, out uint size, out IntPtr data, out uint kind, IntPtr r);
 [DllImport("wlanapi.dll")] public static extern uint WlanHostedNetworkSetProperty(IntPtr h, uint op, uint size, byte[] data, out uint reason, IntPtr r);
 [DllImport("wlanapi.dll")] public static extern uint WlanHostedNetworkSetSecondaryKey(IntPtr h, uint len, byte[] data, [MarshalAs(UnmanagedType.Bool)] bool phrase, [MarshalAs(UnmanagedType.Bool)] bool persistent, out uint reason, IntPtr r);
 [DllImport("wlanapi.dll")] public static extern uint WlanHostedNetworkStartUsing(IntPtr h, out uint reason, IntPtr r);
 [DllImport("wlanapi.dll")] public static extern uint WlanHostedNetworkStopUsing(IntPtr h, out uint reason, IntPtr r);
}
'@
function Conferir-Codigo([uint32]$Codigo, [string]$Etapa, [uint32]$Motivo=0) {
 if ($Codigo -ne 0) { throw ($Etapa+': codigo='+$Codigo+', motivo='+$Motivo) }
}
function Estado-Corpo {
 $dados=[IntPtr]::Zero
 Conferir-Codigo ([WlanCorpo]::WlanHostedNetworkQueryStatus($handleCorpo,[ref]$dados,[IntPtr]::Zero)) 'consulta'
 try { return [Runtime.InteropServices.Marshal]::ReadInt32($dados) }
 finally { [WlanCorpo]::WlanFreeMemory($dados) }
}
function Salvar-Recibo([string]$Estado, [bool]$Preservada, [string]$Erro='') {
 @{estado=$Estado;conexao_original_preservada=$Preservada;erro=$Erro;pid=$PID;horario=[DateTime]::Now.ToString('s')} |
 ConvertTo-Json | Set-Content -LiteralPath $reciboCorpo -Encoding UTF8
}
$perfilCorpo=[Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
if (-not $perfilCorpo -or -not $perfilCorpo.IsWlanConnectionProfile) { throw 'Wi-Fi original nao confirmado.' }
$nomeOriginal=$perfilCorpo.ProfileName
$handleCorpo=[IntPtr]::Zero
[uint32]$versaoCorpo=0; [uint32]$motivoCorpo=0
$iniciadoCorpo=$false; $alteradoCorpo=$false; $settingsAnteriores=$null
New-Item -ItemType Directory -Path (Split-Path $reciboCorpo) -Force | Out-Null
try {
 Conferir-Codigo ([WlanCorpo]::WlanOpenHandle(2,[IntPtr]::Zero,[ref]$versaoCorpo,[ref]$handleCorpo)) 'abrir'
 if ((Estado-Corpo) -eq 2) { throw 'Rede hospedada ja ativa; preservar outro controlador.' }
 [uint32]$tamanhoCorpo=0; [uint32]$tipoCorpo=0; $dadosCorpo=[IntPtr]::Zero
 Conferir-Codigo ([WlanCorpo]::WlanHostedNetworkQueryProperty($handleCorpo,0,[ref]$tamanhoCorpo,[ref]$dadosCorpo,[ref]$tipoCorpo,[IntPtr]::Zero)) 'configuracao'
 try {
  if ($tamanhoCorpo -ne 40) { throw 'Estrutura de configuracao inesperada.' }
  $settingsAnteriores=New-Object byte[] 40
  [Runtime.InteropServices.Marshal]::Copy($dadosCorpo,$settingsAnteriores,0,40)
 } finally { [WlanCorpo]::WlanFreeMemory($dadosCorpo) }
 $lenAnterior=[BitConverter]::ToUInt32($settingsAnteriores,0)
 if ($lenAnterior -gt 32) { throw 'SSID existente invalido.' }
 $ssidAnterior=[Text.Encoding]::UTF8.GetString($settingsAnteriores,4,$lenAnterior)
 # A sondagem inicial criou apenas o SSID padrao do Windows.
 if ($ssidAnterior -ne 'Laylay-Corpo-PC' -and $ssidAnterior -notmatch ('^'+[regex]::Escape($env:COMPUTERNAME)+'-\d+$')) {
  throw 'SSID existente pertence a outra configuracao; nao substituir.'
 }
 if (Test-Path -LiteralPath $arquivoCorpo) {
  $salvoCorpo=Get-Content -LiteralPath $arquivoCorpo -Raw | ConvertFrom-Json
  if ($salvoCorpo.ssid -ne 'Laylay-Corpo-PC' -or $salvoCorpo.senha -notmatch '^[a-f0-9]{32}$') { throw 'Credenciais locais invalidas.' }
  $senhaCorpo=$salvoCorpo.senha
 } else {
  $bytesCorpo=New-Object byte[] 16
  $rngCorpo=[Security.Cryptography.RandomNumberGenerator]::Create()
  try { $rngCorpo.GetBytes($bytesCorpo) } finally { $rngCorpo.Dispose() }
  $senhaCorpo=([BitConverter]::ToString($bytesCorpo)).Replace('-','').ToLowerInvariant()
 }
 $settingsCorpo=New-Object byte[] 40
 $ssidCorpo=[Text.Encoding]::UTF8.GetBytes('Laylay-Corpo-PC')
 [BitConverter]::GetBytes([uint32]$ssidCorpo.Length).CopyTo($settingsCorpo,0)
 $ssidCorpo.CopyTo($settingsCorpo,4)
 [BitConverter]::GetBytes([uint32]2).CopyTo($settingsCorpo,36)
 Conferir-Codigo ([WlanCorpo]::WlanHostedNetworkSetProperty($handleCorpo,0,40,$settingsCorpo,[ref]$motivoCorpo,[IntPtr]::Zero)) 'definir SSID' $motivoCorpo
 $alteradoCorpo=$true
 $chaveCorpo=[Text.Encoding]::ASCII.GetBytes($senhaCorpo+[char]0)
 Conferir-Codigo ([WlanCorpo]::WlanHostedNetworkSetSecondaryKey($handleCorpo,$chaveCorpo.Length,$chaveCorpo,$true,$false,[ref]$motivoCorpo,[IntPtr]::Zero)) 'chave temporaria' $motivoCorpo
 Conferir-Codigo ([WlanCorpo]::WlanHostedNetworkStartUsing($handleCorpo,[ref]$motivoCorpo,[IntPtr]::Zero)) 'iniciar' $motivoCorpo
 $iniciadoCorpo=$true
 if ((Estado-Corpo) -ne 2) { throw 'API nao confirmou rede ativa.' }
 $perfilDepois=[Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
 if (-not $perfilDepois -or $perfilDepois.ProfileName -ne $nomeOriginal) { throw 'Conexao original mudou.' }
 if (Test-Path -LiteralPath $paradaCorpo) { Remove-Item -LiteralPath $paradaCorpo }
 @{ssid='Laylay-Corpo-PC';senha=$senhaCorpo;modo='hosted_network_temporario'} | ConvertTo-Json |
 Set-Content -LiteralPath $arquivoCorpo -Encoding UTF8
 Salvar-Recibo 'ativo' $true
 while (-not (Test-Path -LiteralPath $paradaCorpo)) {
  Start-Sleep -Seconds 2
  $perfilDepois=[Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
  if (-not $perfilDepois -or $perfilDepois.ProfileName -ne $nomeOriginal) { throw 'Conexao original mudou durante teste.' }
  if ((Estado-Corpo) -ne 2) { throw 'Rede hospedada deixou de estar ativa.' }
 }
 Salvar-Recibo 'encerrando' $true
} catch {
 $perfilDepois=[Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
 Salvar-Recibo 'falhou' ([bool]($perfilDepois -and $perfilDepois.ProfileName -eq $nomeOriginal)) $_.Exception.Message
 throw
} finally {
 if ($iniciadoCorpo) { $null=[WlanCorpo]::WlanHostedNetworkStopUsing($handleCorpo,[ref]$motivoCorpo,[IntPtr]::Zero) }
 if ($alteradoCorpo) { $null=[WlanCorpo]::WlanHostedNetworkSetProperty($handleCorpo,0,40,$settingsAnteriores,[ref]$motivoCorpo,[IntPtr]::Zero) }
 if ($handleCorpo -ne [IntPtr]::Zero) { $null=[WlanCorpo]::WlanCloseHandle($handleCorpo,[IntPtr]::Zero) }
}
