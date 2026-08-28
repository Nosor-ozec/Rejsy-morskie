@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Rejsy-morskie - przygotowanie publikacji
echo ==========================================
echo.

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "LOCAL_SITE=%~dp0outputs\podglad-leaflet"
set "DOCS=%~dp0docs"

if not exist "%PYTHON%" (
    echo BLAD: Nie znaleziono:
    echo %PYTHON%
    goto ERROR
)

if not exist "%LOCAL_SITE%\build-manifest.json" (
    echo BLAD: Brak sprawdzonego podgladu lokalnego.
    echo Najpierw uruchom Uruchom-Rejsy.cmd i sprawdz mape.
    goto ERROR
)

"%PYTHON%" -m rejsy_morskie.cli publish "%LOCAL_SITE%" "%DOCS%"
if errorlevel 1 goto ERROR

echo.
echo ==========================================
echo   GOTOWE DO RECZNEGO COMMIT I PUSH
echo ==========================================
echo Zawartosc docs pochodzi dokladnie ze sprawdzonego podgladu lokalnego.
echo Ten skrypt nie wykonuje operacji Git ani GitHub.
echo Commit i push wykonaj samodzielnie w GitHub Desktop.
echo.
pause
exit /b 0

:ERROR
echo.
echo Publikacja nie zostala przygotowana.
pause
exit /b 1
