@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host artifacts\rosto_oled\protecao_sensores\presenca\red_parada.cpp /Fe:artifacts\rosto_oled\protecao_sensores\presenca\red_parada.exe /Fo:artifacts\rosto_oled\protecao_sensores\presenca\red_parada.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\protecao_sensores\presenca\red_parada.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host firmware\rosto_laylay\validacao_host\validar_presenca_sensores.cpp /Fe:artifacts\rosto_oled\protecao_sensores\presenca\validar_presenca.exe /Fo:artifacts\rosto_oled\protecao_sensores\presenca\validar_presenca.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\protecao_sensores\presenca\validar_presenca.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Ifirmware\rosto_laylay\validacao_host artifacts\rosto_oled\protecao_sensores\presenca\renderizar.cpp /Fe:artifacts\rosto_oled\protecao_sensores\presenca\renderizar.exe /Fo:artifacts\rosto_oled\protecao_sensores\presenca\renderizar.obj
if errorlevel 1 exit /b 1
artifacts\rosto_oled\protecao_sensores\presenca\renderizar.exe
