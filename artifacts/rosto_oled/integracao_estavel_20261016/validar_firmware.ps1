$ErrorActionPreference = 'Stop'
$pasta = $PSScriptRoot
$raiz = (Resolve-Path (Join-Path $pasta '../../..')).Path
Set-Location -LiteralPath $raiz
$vc = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
$testes = @('validar_recuperacao_perifericos', 'validar_imu', 'validar_manuseio_fofo',
    'validar_sensores', 'validar_presenca_sensores', 'validar_linguagem_sensores',
    'validar_som_olhos', 'validar_presenca_v2')
foreach ($nome in $testes) {
    $fonte = "firmware\rosto_laylay\validacao_host\$nome.cpp"
    $flags = if ($nome -eq 'validar_som_olhos') { '/DLAYLAY_HABILITAR_MOTORES_BANCADA=1' } else { '' }
    $comando = "`"$vc`" >nul && cl /nologo /std:c++17 /EHsc $flags /Ifirmware\rosto_laylay\validacao_host $fonte /Fo`"$pasta\$nome.obj`" /Fe`"$pasta\$nome.exe`""
    & cmd /c $comando
    if ($LASTEXITCODE) { throw "Compilacao: $nome" }
    if ($nome -eq 'validar_linguagem_sensores') {
        & (Join-Path $pasta "$nome.exe") 'pausa_descanso'
    } else {
        & (Join-Path $pasta "$nome.exe")
    }
    if ($LASTEXITCODE) { throw "Contrato: $nome" }
}
foreach ($caso in @('snapshot', 'distancia', 'oled')) {
    & (Join-Path $pasta 'validar_recuperacao_perifericos.exe') $caso
    if ($LASTEXITCODE) { throw "Recuperacao: $caso" }
}
