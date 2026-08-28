@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo   Rejsy-morskie - uruchomienie programu
echo ==========================================
echo.

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "REJSY=%~dp0routes\rejsy.xlsx"
set "MEDIA=%~dp0routes\media.xlsx"
set "OUTPUTS=%~dp0outputs"
set "LOCAL_SITE=%OUTPUTS%\podglad-leaflet"
set "DOCS=%~dp0docs"
set "PREVIEW_URL=http://127.0.0.1:8765/"

set "SEA_ROUTER_EXE=E:\sea-router\rust\target\release\sea-router-rs.exe"
set "SEA_ROUTER_DATA=E:\sea-router\data"

if not exist "%PYTHON%" (
    echo BLAD: Nie znaleziono:
    echo %PYTHON%
    goto ERROR
)

if not exist "%REJSY%" (
    echo BLAD: Nie znaleziono:
    echo %REJSY%
    goto ERROR
)

if not exist "%MEDIA%" (
    echo BLAD: Nie znaleziono:
    echo %MEDIA%
    goto ERROR
)

if not exist "%SEA_ROUTER_EXE%" (
    echo BLAD: Nie znaleziono sea-routera:
    echo %SEA_ROUTER_EXE%
    goto ERROR
)

echo Sprawdzam sea-router...

curl.exe --noproxy "*" --silent --fail --output NUL --max-time 2 "http://127.0.0.1:3001/viewer"

if errorlevel 1 (
    echo Sea-router nie dziala. Uruchamiam...

    start "Sea Router" "%SEA_ROUTER_EXE%" serve "%SEA_ROUTER_DATA%"

    echo Czekam na uruchomienie sea-routera...
    set /a WAITCOUNT=0

    :WAIT_ROUTER
    timeout /t 2 /nobreak >nul

    curl.exe --noproxy "*" --silent --fail --output NUL --max-time 2 "http://127.0.0.1:3001/viewer"

    if not errorlevel 1 goto ROUTER_READY

    set /a WAITCOUNT+=1

    if !WAITCOUNT! GEQ 15 (
        echo BLAD: Sea-router nie uruchomil sie w oczekiwanym czasie.
        goto ERROR
    )

    goto WAIT_ROUTER
)

:ROUTER_READY
echo Sea-router dziala.
echo.

echo Uruchamiam generator...
echo.

"%PYTHON%" -m rejsy_morskie.cli generate "%REJSY%" "%OUTPUTS%" ^
  --media "%MEDIA%" --site-dir "%LOCAL_SITE%" --web-assets "%DOCS%"

if errorlevel 1 (
    echo.
    echo BLAD: Generator zakonczyl sie bledem.
    goto ERROR
)

echo.
echo ==========================================
echo   GOTOWE
echo ==========================================
echo Excel z aktualnymi Lat/Lon i Etapami:
echo %REJSY%
echo.
echo Wyniki tras i pomocniczy KML:
echo %OUTPUTS%
echo.
echo Pelny lokalny podglad Leaflet:
echo %LOCAL_SITE%
echo.

echo Sprawdzam lokalny serwer WWW...
curl.exe --noproxy "*" --silent --fail --output NUL --max-time 2 "%PREVIEW_URL%data/route.json"

if errorlevel 1 (
    echo Uruchamiam lokalny serwer WWW...
    start "Rejsy - lokalny serwer WWW" /min "%PYTHON%" -m http.server 8765 ^
      --bind 127.0.0.1 --directory "%LOCAL_SITE%"
    set /a WEBWAIT=0

    :WAIT_WEB
    timeout /t 1 /nobreak >nul
    curl.exe --noproxy "*" --silent --fail --output NUL --max-time 2 "%PREVIEW_URL%data/route.json"
    if not errorlevel 1 goto WEB_READY
    set /a WEBWAIT+=1
    if !WEBWAIT! GEQ 10 (
        echo BLAD: Lokalny serwer WWW nie uruchomil sie.
        goto ERROR
    )
    goto WAIT_WEB
)

:WEB_READY
echo Otwieram gotowa mape w przegladarce...
start "" "%PREVIEW_URL%"
echo.
pause
exit /b 0

:ERROR
echo.
echo Program nie zostal wykonany poprawnie.
pause
exit /b 1
