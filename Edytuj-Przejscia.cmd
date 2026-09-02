@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "REJSY=%~dp0routes\rejsy.xlsx"

if not exist "%PYTHON%" (
  echo BLAD: Nie znaleziono środowiska Python: %PYTHON%
  goto ERROR
)
if not exist "%REJSY%" (
  echo BLAD: Nie znaleziono skoroszytu: %REJSY%
  goto ERROR
)

echo Uruchamiam lokalny edytor przejść...
echo Po zapisaniu uruchom osobno Aktualizuj-Przejscia-SeaRouter.cmd.
echo.
"%PYTHON%" -m rejsy_morskie.cli edit-passages "%REJSY%" --project-root "." --host 127.0.0.1 --port 8766
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" exit /b 0

:ERROR
echo.
echo Edytor zakończył się błędem.
pause
exit /b 1
