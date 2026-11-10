@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++17 /EHsc /MT /O1 /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_motor_continuo.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_continuo.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_continuo.obj" /Fd:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_continuo.pdb"
if errorlevel 1 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_continuo.exe"
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++17 /EHsc /MT /O1 /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_motor_longo.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_longo.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_longo.obj" /Fd:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_longo.pdb"
if errorlevel 1 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_motor_longo.exe"
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++17 /EHsc /MT /O1 /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_protecao.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_protecao.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_protecao.obj" /Fd:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_protecao.pdb"
if errorlevel 1 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_protecao.exe"
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++17 /EHsc /MT /O1 /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_imu.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_imu.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_imu.obj" /Fd:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_imu.pdb"
if errorlevel 1 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\corpo_pwm150_20261104\piso\validar_imu.exe"
if errorlevel 1 exit /b 1
