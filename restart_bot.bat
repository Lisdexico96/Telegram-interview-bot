@echo off
echo Stopping any running bot processes...
taskkill /F /FI "WINDOWTITLE eq *bot.py*" 2>nul
wmic process where "commandline like '%%bot.py%%' and not commandline like '%%wmic%%'" delete 2>nul

echo.
echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul

echo.
echo Starting bot...
cd /d "%~dp0"
python bot.py
pause
