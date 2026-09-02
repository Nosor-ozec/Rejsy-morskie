@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "REJSY=%~dp0routes\rejsy.xlsx"

if not exist "%PYTHON%" (
  echo BLAD: Nie znaleziono srodowiska Python: %PYTHON%
  goto ERROR
)
if not exist "%REJSY%" (
  echo BLAD: Nie znaleziono skoroszytu: %REJSY%
  goto ERROR
)

echo Uruchamiam lokalny edytor portow i punktow rejsu...
echo Po zapisaniu uruchom Uruchom-Rejsy.cmd, aby przeliczyc Etapy i mape.
echo.
"%PYTHON%" -m rejsy_morskie.cli edit-ports "%REJSY%" --project-root "." --host 127.0.0.1 --port 8767
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" exit /b 0

:ERROR
echo.
echo Edytor zakonczyl sie bledem.
pause
exit /b 1
