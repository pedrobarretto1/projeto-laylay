@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host artifacts\rosto_oled\protecao_sensores\red_oled.cpp /Fe:artifacts\rosto_oled\protecao_sensores\red_oled.exe /Fo:artifacts\rosto_oled\protecao_sensores\red_oled.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\protecao_sensores\red_oled.exe
