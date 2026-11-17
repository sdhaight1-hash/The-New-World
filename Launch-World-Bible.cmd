@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 app\launch.py
) else (
    python app\launch.py
)
if ERRORLEVEL 1 (
  echo.
  echo Could not start World Bible Studio. Install Python 3.11 or newer.
  echo For image support run: python -m pip install -r app\requirements.txt
  pause
)
endlocal
