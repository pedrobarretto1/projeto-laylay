@echo off
setlocal EnableDelayedExpansion
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host firmware\rosto_laylay\validacao_host\validar_sensores.cpp /Fe:artifacts\rosto_oled\sensores\validar_sensores.exe /Fo:artifacts\rosto_oled\sensores\validar_sensores.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\sensores\validar_sensores.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host firmware\rosto_laylay\validacao_host\validar_sono_vivo.cpp /Fe:artifacts\rosto_oled\sensores\validar_sono.exe /Fo:artifacts\rosto_oled\sensores\validar_sono.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\sensores\validar_sono.exe
if errorlevel 1 exit /b 1
for %%T in (validar_som_olhos validar_expressoes_v3 validar_motor_continuo) do (
  cl /nologo /std:c++17 /EHsc /DLAYLAY_HABILITAR_MOTORES_BANCADA=1 /Ifirmware\rosto_laylay\validacao_host firmware\rosto_laylay\validacao_host\%%T.cpp /Fe:artifacts\rosto_oled\sensores\%%T.exe /Fo:artifacts\rosto_oled\sensores\%%T.obj
  if not "!errorlevel!"=="0" exit /b 1
  artifacts\rosto_oled\sensores\%%T.exe
  if not "!errorlevel!"=="0" exit /b 1
)
exit /b 0
