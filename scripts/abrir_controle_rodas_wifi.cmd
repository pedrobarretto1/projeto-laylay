@echo off
title Laylay - teste das rodas por Wi-Fi
cd /d "%~dp0.."
".venv314\Scripts\python.exe" -u "scripts\controlar_teste_rodas_wifi.py"
echo.
echo Controle encerrado. Para abrir novamente: scripts\abrir_controle_rodas_wifi.cmd
