@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host /Ifirmware\rosto_laylay artifacts\rosto_oled\sensores\red_protocolo.cpp /Fe:artifacts\rosto_oled\sensores\red_protocolo.exe /Fo:artifacts\rosto_oled\sensores\red_protocolo.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\sensores\red_protocolo.exe
exit /b %errorlevel%
