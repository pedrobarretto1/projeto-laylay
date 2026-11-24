@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c++17 /EHsc /MT /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_parede_sem_borda.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_parede_sem_borda.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_parede_sem_borda.obj"
if not %errorlevel%==0 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_parede_sem_borda.exe"
if not %errorlevel%==0 exit /b 1
cl /nologo /std:c++17 /EHsc /MT /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_protecao.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_protecao.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_protecao.obj"
if not %errorlevel%==0 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_protecao.exe"
if not %errorlevel%==0 exit /b 1
cl /nologo /std:c++17 /EHsc /MT /I"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host" "C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\firmware\rosto_laylay\validacao_host\validar_reconexao_protecao.cpp" /Fe:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_reconexao_protecao.exe" /Fo:"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_reconexao_protecao.obj"
if not %errorlevel%==0 exit /b 1
"C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\projeto lay\laylay\artifacts\parede_sem_borda_20261123\validar_reconexao_protecao.exe"
if not %errorlevel%==0 exit /b 1