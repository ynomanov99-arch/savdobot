@echo off
title Kastyum Bot - Home Server
cd /d "C:\Users\lenovo\OneDrive\Desktop\cod uchun\savdobot"
echo ==========================================
echo ???? Kastyum Bot - Home Server ishga tushdi!
echo ???? Monitoring va Auto-Restart xizmati ishlamoqda.
echo ???? Oyna yopilmasligi kerak!
echo ==========================================
set PYTHONIOENCODING=utf-8
powershell -NoProfile -ExecutionPolicy Bypass -File restart_main.ps1


