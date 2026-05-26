@echo off
title Kastyum Bot - Startup Setup
cls
echo ==================================================
echo рџЋ© Kastyum Bot - Avtomatik Ishga Tushirish Sozlamalari
echo ==================================================
echo.
echo 1) Yashirin rejimda (Silent Background) avtomatik yuklashni o'rnatish (Tavsiya etiladi)
echo 2) Oddiy rejimda (Visible Console) avtomatik yuklashni o'rnatish
echo 3) Avtomatik yuklashdan o'chirish (Olib tashlash)
echo 4) Chiqish
echo.
echo ==================================================
set /p choice="Tanlovingizni kiriting (1-4): "

if "%choice%"=="1" goto install_silent
if "%choice%"=="2" goto install_normal
if "%choice%"=="3" goto uninstall
if "%choice%"=="4" exit
goto error

:install_silent
echo.
echo [1/2] Avtomatik yuklash uchun yashirin yorliq sozlanmoqda...
powershell -NoProfile -Command "$s = (New-Object -ComObject WScript.Shell).CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\KastyumBot.lnk\"); $s.TargetPath = 'C:\Users\lenovo\OneDrive\Desktop\cod uchun\savdobot\run_bot_hidden.vbs'; $s.WorkingDirectory = 'C:\Users\lenovo\OneDrive\Desktop\cod uchun\savdobot'; $s.Save()"
echo [2/2] Muvaffaqiyatli yakunlandi!
echo [OK] Bot endi kompyuter yoqilganda fonda yashirin ishga tushadi.
echo.
pause
exit

:install_normal
echo.
echo [1/2] Avtomatik yuklash uchun oddiy yorliq sozlanmoqda...
powershell -NoProfile -Command "$s = (New-Object -ComObject WScript.Shell).CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\KastyumBot.lnk\"); $s.TargetPath = 'C:\Users\lenovo\OneDrive\Desktop\cod uchun\savdobot\run_bot.bat'; $s.WorkingDirectory = 'C:\Users\lenovo\OneDrive\Desktop\cod uchun\savdobot'; $s.Save()"
echo [2/2] Muvaffaqiyatli yakunlandi!
echo [OK] Bot endi kompyuter yoqilganda CMD oynasida ishga tushadi.
echo.
pause
exit

:uninstall
echo.
echo Avtomatik yuklash yorlig'i o'chirilmoqda...
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\KastyumBot.lnk" (
    del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\KastyumBot.lnk"
    echo [OK] Avtomatik yuklashdan muvaffaqiyatli o'chirildi!
) else (
    echo [!] Avtomatik yuklash ro'yxatida bot topilmadi.
)
echo.
pause
exit

:error
echo Noto'g'ri tanlov!
pause
exit

