# Kastyum Bot - Monitoring and Auto-Restart Script
# Ushbu skript bot jarayonini har 10 soniyada tekshiradi va u to'xtab qolsa,
# avtomatik ravishda fonda (yashirin) qayta ishga tushiradi.
# Barcha xatoliklar va tizim jurnallari 'bot.log' fayliga yoziladi.

$Host.UI.RawUI.WindowTitle = "Kastyum Bot - Monitor va Auto-Restart"
Clear-Host

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $PSScriptRoot = Get-Location
}

$LogFile = Join-Path $PSScriptRoot "monitor.log"
$CheckInterval = 10 # soniya

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  KASTYUM BOT MONITORING TIZIMI" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Ishchi katalog: $PSScriptRoot" -ForegroundColor Gray
Write-Host "  Tizim jurnali: $LogFile" -ForegroundColor Gray
Write-Host "  Tekshirish oralig'i: $CheckInterval soniya" -ForegroundColor Gray
Write-Host "  Chiqish uchun oynani yoping yoki Ctrl+C bosing." -ForegroundColor DarkGray
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Monitoring boshlandi..." -ForegroundColor Green

# Log yozish funksiyasi
function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogLine = "[$Timestamp] [$Level] $Message"
    
    # Konsolga rangli chiqarish
    $Color = "White"
    if ($Level -eq "ERROR") { $Color = "Red" }
    elseif ($Level -eq "WARNING") { $Color = "Yellow" }
    elseif ($Level -eq "SUCCESS") { $Color = "Green" }
    elseif ($Level -eq "INFO") { $Color = "Cyan" }
    
    Write-Host $LogLine -ForegroundColor $Color
    
    # Faylga yozish
    try {
        Add-Content -Path $LogFile -Value $LogLine -Encoding utf8
    } catch {
        # Log fayliga yozishda xatolik bo'lsa konsolga chiqariladi
        Write-Warning "Log fayliga yozib bo'lmadi: $_"
    }
}

Write-Log "Monitoring xizmati muvaffaqiyatli ishga tushirildi." "SUCCESS"

while ($true) {
    try {
        # 1. Faol Python jarayonlarini tekshirish
        $Processes = Get-CimInstance Win32_Process -Filter "Name like 'python%' or Name like 'py%'" | 
                     Where-Object { $_.CommandLine -like "*main.py*" }

        $IsRunning = $false
        $Pids = @()
        
        if ($Processes) {
            $IsRunning = $true
            foreach ($p in $Processes) {
                $Pids += $p.ProcessId
            }
        }

        if (-not $IsRunning) {
            Write-Log "Bot jarayoni topilmadi! Qayta ishga tushirilmoqda..." "WARNING"

            # 2. Botni fonda ishga tushirish (stdout/stderr logga yo'naltiriladi)
            $BotProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c py main.py >> bot.log 2>&1" `
                                        -WorkingDirectory $PSScriptRoot `
                                        -WindowStyle Hidden `
                                        -PassThru

            Start-Sleep -Seconds 3

            # Qayta tekshirish
            $NewProcesses = Get-CimInstance Win32_Process -Filter "Name like 'python%' or Name like 'py%'" | 
                            Where-Object { $_.CommandLine -like "*main.py*" }

            if ($NewProcesses) {
                $NewPids = ($NewProcesses | Select-Object -ExpandProperty ProcessId) -join ", "
                Write-Log "Bot fonda muvaffaqiyatli ishga tushirildi! Yangi PID: $NewPids" "SUCCESS"
            } else {
                Write-Log "Botni ishga tushirishda xatolik yuz berdi! Keyingi tekshiruvda yana urinib ko'riladi." "ERROR"
            }
        } else {
            # Bot ishlayapti, konsolda status ko'rsatamiz (lekin log faylini to'ldirmaslik uchun konsolga yozamiz xolos)
            $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $PidString = $Pids -join ", "
            Write-Host "[$Timestamp] [MONITOR] Bot faol ishlamoqda. PID: $PidString" -ForegroundColor Gray
        }
    }
    catch {
        Write-Log "Monitoring jarayonida kutilmagan xatolik yuz berdi: $_" "ERROR"
    }

    Start-Sleep -Seconds $CheckInterval
}
