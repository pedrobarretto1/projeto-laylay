@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host firmware\rosto_laylay\validacao_host\validar_saude.cpp /Fe:artifacts\rosto_oled\recuperacao_usb\validar_saude.exe /Fo:artifacts\rosto_oled\recuperacao_usb\validar_saude.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\recuperacao_usb\validar_saude.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host firmware\rosto_laylay\validacao_host\validar_reconexao_protecao.cpp /Fe:artifacts\rosto_oled\recuperacao_usb\validar_reconexao.exe /Fo:artifacts\rosto_oled\recuperacao_usb\validar_reconexao.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\recuperacao_usb\validar_reconexao.exe
