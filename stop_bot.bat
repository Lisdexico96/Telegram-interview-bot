@echo off
setlocal enabledelayedexpansion
REM Windows script to stop the bot

echo Stopping Telegram Interview Bot...
echo.

REM Find all Python processes
set found=0
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2^>nul') do (
    set PID=%%a
    set PID=!PID:"=!
    
    REM Check command line for bot.py
    for /f "delims=" %%b in ('wmic process where "ProcessId=!PID!" get CommandLine /value 2^>nul ^| findstr "CommandLine"') do (
        set cmdline=%%b
        echo !cmdline! | findstr /i "bot.py" >nul
        if !errorlevel! equ 0 (
            echo Found bot process !PID!, stopping...
            taskkill /PID !PID! /F >nul 2>&1
            if !errorlevel! equ 0 (
                set found=1
                echo Process !PID! stopped successfully.
            )
        )
    )
)

if !found! equ 0 (
    echo No running bot processes found.
) else (
    echo.
    echo All bot processes stopped successfully!
)

echo.
echo Done!
