@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c++17 /EHsc /MT /I"firmware\rosto_laylay\validacao_host" "firmware\rosto_laylay\validacao_host\validar_imu_invertida.cpp" /Fo"artifacts\corpo_ble_imu\imu_invertida.obj" /Fe"artifacts\corpo_ble_imu\imu_invertida.exe"
if errorlevel 1 exit /b 1
artifacts\corpo_ble_imu\imu_invertida.exe
exit /b %errorlevel%
