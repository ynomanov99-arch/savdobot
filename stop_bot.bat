@echo off
title Kastyum Bot - Stop
echo ==========================================
echo 🎩 Kastyum Bot va Monitor to'xtatilmoqda...
echo ==========================================
set PYTHONIOENCODING=utf-8

powershell -NoProfile -Command "$foundMon = $false; Get-CimInstance Win32_Process -Filter \"Name like 'powershell%%'\" | Where-Object { $_.CommandLine -like '*restart_main.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; echo ('[OK] Monitoring xizmati to''xtatildi (PID: ' + $_.ProcessId + ')'); $foundMon = $true }; if (-not $foundMon) { echo [!] Faol monitoring xizmati topilmadi. }"

powershell -NoProfile -Command "$foundBot = $false; Get-CimInstance Win32_Process -Filter \"Name like 'python%%' or Name like 'py%%'\" | Where-Object { $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; echo ('[OK] Bot jarayoni to''xtatildi (PID: ' + $_.ProcessId + ')'); $foundBot = $true }; if (-not $foundBot) { echo [!] Faol bot jarayoni topilmadi. }"

echo ==========================================
echo Ish yakunlandi.
echo ==========================================
pause

