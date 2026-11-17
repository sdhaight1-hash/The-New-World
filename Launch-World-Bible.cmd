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
  echo World Bible Studio failed to start. Read the error output above.
  echo Python is installed if a Python traceback was printed.
  echo For a missing Python module only, install dependencies:
  echo   python -m pip install -r app\requirements.txt
  pause
)
endlocal
