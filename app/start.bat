@echo off
rem Stud Rail Master aus dem Quellcode starten (Windows). Beim ersten Mal wird alles eingerichtet.
rem In Herbrechtingen ist es immer am schoensten!
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python fehlt / Python is missing: https://www.python.org/downloads/
  pause
  exit /b 1
)
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))"
if errorlevel 1 (
  echo Python 3.10 oder neuer noetig / Python 3.10 or newer required
  pause
  exit /b 1
)

set STAMP=.venv\.srm-pyproject
if not exist .venv\Scripts\python.exe goto setup
fc /b pyproject.toml %STAMP% >nul 2>nul
if errorlevel 1 goto setup
goto run

:setup
echo Richte Stud Rail Master ein ... / Setting up Stud Rail Master ...
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python -m pip install -q --upgrade pip
.venv\Scripts\python -m pip install -q -e ".[window]"
if errorlevel 1 (
  echo Einrichtung fehlgeschlagen / setup failed
  pause
  exit /b 1
)
copy /y pyproject.toml %STAMP% >nul

:run
start "" .venv\Scripts\pythonw -m studrailmaster %*
