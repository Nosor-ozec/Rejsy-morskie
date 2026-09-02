@echo off
setlocal
chcp 65001 >nul
set "PROJECT=%~dp0"
set "SCRIPT=%PROJECT%sea-router-custom\scripts\Update-SeaRouterPassages.ps1"

echo Aktualizacja własnych przejść sea-routera z arkusza Lokalizacje.
if /I "%~1"=="test" (
  echo Tryb testowy: tylko generowanie konfiguracji i walidacja wstępna.
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -TargetPath "E:\sea-router" -ValidateOnly
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -TargetPath "E:\sea-router"
)
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo Aktualizacja NIE została aktywowana. Kod błędu: %RESULT%
) else (
  echo.
  echo Operacja zakończona pomyślnie.
)
echo.
pause
exit /b %RESULT%
