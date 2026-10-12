param([ValidatePattern('^COM[0-9]+$')][string]$Porta = 'COM4')
$ErrorActionPreference = 'Stop'
# Seleção explícita somente nesta sessão; não consulta o pareamento Wi-Fi.
& (Join-Path $PSScriptRoot 'iniciar_laylay_com_rosto.ps1') -Porta $Porta
