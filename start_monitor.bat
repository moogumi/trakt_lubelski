@echo off
REM Монитор вывоза мусора TRAKT LUBELSKI 26: опрос каждые 2 минуты, лог в run.log.
REM Тестовый режим — на каждой итерации присылает весь график в Telegram.
cd /d "%~dp0"
echo Останавливаю ранее запущенные мониторы...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*monitor.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
timeout /t 1 >nul
set PYTHONIOENCODING=utf-8
start "trakt-musor" /min pythonw monitor.py --watch 120 --log run.log
echo Монитор запущен в фоне (опрос каждые 2 минуты). Лог: %~dp0run.log
echo Чтобы остановить — stop_monitor.bat
pause
