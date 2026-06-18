@echo off
REM Interactive waste-collection bot for TRAKT LUBELSKI 26.
REM Answers /start /next /language /settings and (with --push) broadcasts the
REM schedule every poll_seconds (config.txt, default 2 minutes). Log in run.log.
cd /d "%~dp0"
echo Stopping any previously running bot...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and ($_.CommandLine -like '*bot.py*' -or $_.CommandLine -like '*monitor.py*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
timeout /t 1 >nul
set PYTHONIOENCODING=utf-8
start "trakt-musor" /min pythonw bot.py --push
echo Bot started in background (interactive + broadcast every 2 minutes).
echo To stop, run stop_monitor.bat
pause
