@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "INSTALLER=%PROJECT_ROOT%sea-router-custom\scripts\Install-SeaRouter.ps1"
set "TARGET=E:\sea-router"
set "INSTALL_MODE="
set "RESULT=0"

if not exist "%INSTALLER%" (
    echo BLAD: Nie znaleziono instalatora PowerShell:
    echo %INSTALLER%
    set "RESULT=3"
    goto :finish
)

if "%~1"=="" goto :run
if /I "%~1"=="test" (
    if not "%~2"=="" goto :usage
    set "INSTALL_MODE=-ValidateOnly"
    goto :run
)

:usage
echo BLAD: Nieznany parametr.
echo Uzycie:
echo   Install-SeaRouter.cmd       - pelna instalacja do E:\sea-router
echo   Install-SeaRouter.cmd test  - tylko kontrola wymagan, bez instalacji
set "RESULT=2"
goto :finish

:run
echo ============================================================
if defined INSTALL_MODE (
    echo Sea-router: kontrola wymagan bez instalacji
) else (
    echo Sea-router: instalacja lokalna do %TARGET%
)
echo Projekt: %PROJECT_ROOT%
echo ============================================================
echo.

pushd "%PROJECT_ROOT%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%" -TargetPath "%TARGET%" %INSTALL_MODE%
set "RESULT=%ERRORLEVEL%"
popd

:finish
echo.
if "%RESULT%"=="0" (
    echo Zakonczono pomyslnie.
) else (
    echo Instalator zakonczyl sie bledem. Kod: %RESULT%
)
echo.
pause
endlocal & exit /b %RESULT%
