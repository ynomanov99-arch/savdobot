@echo off
title Kastyum Bot - Status
echo ==========================================
echo 🎩 Kastyum Bot holati tekshirilmoqda...
echo ==========================================
set PYTHONIOENCODING=utf-8

powershell -NoProfile -Command "$monProcs = Get-CimInstance Win32_Process -Filter \"Name like 'powershell%%'\" | Where-Object { $_.CommandLine -like '*restart_main.ps1*' }; $botProcs = Get-CimInstance Win32_Process -Filter \"Name like 'python%%' or Name like 'py%%'\" | Where-Object { $_.CommandLine -like '*main.py*' }; if ($botProcs) { Write-Host '🟢 Bot: Ishlamoqda (RUNNING)' -ForegroundColor Green; foreach ($p in $botProcs) { echo ('   📌 PID: ' + $p.ProcessId) } } else { Write-Host '🔴 Bot: Ishlamayapti (STOPPED)' -ForegroundColor Red }; if ($monProcs) { Write-Host '🟢 Monitor xizmati: Faol (ACTIVE)' -ForegroundColor Green; foreach ($p in $monProcs) { echo ('   📌 PID: ' + $p.ProcessId) } } else { Write-Host '🔴 Monitor xizmati: Faol emas (INACTIVE)' -ForegroundColor Red }"

echo ==========================================
pause

