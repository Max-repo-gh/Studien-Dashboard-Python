@echo off
setlocal
cd /d "%~dp0"
title Studien-Dashboard

echo ==========================================
echo       Studien-Dashboard wird gestartet
echo ==========================================
echo.

rem Pruefen, ob der Python Launcher fuer Windows vorhanden ist.
where py >nul 2>nul
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo.
    echo Bitte installiere Python von:
    echo https://www.python.org/downloads/
    echo.
    echo Aktiviere bei der Installation die Option:
    echo Add Python to PATH
    echo.
    pause
    exit /b 1
)

rem Pruefen, ob die Programmdatei vorhanden ist.
if not exist "Dashboard_Cybersecurity.py" (
    echo FEHLER: Dashboard_Cybersecurity.py wurde nicht gefunden.
    echo Lege diese Startdatei in denselben Ordner wie das Python-Programm.
    echo.
    pause
    exit /b 1
)

rem Streamlit nur installieren, wenn es noch nicht vorhanden ist.
py -m streamlit --version >nul 2>nul
if errorlevel 1 (
    echo Streamlit ist noch nicht installiert.
    echo Streamlit wird jetzt fuer deinen Windows Benutzer installiert.
    echo Dafuer wird einmalig eine Internetverbindung benoetigt.
    echo.

    if not exist "requirements.txt" (
        echo FEHLER: requirements.txt wurde nicht gefunden.
        echo.
        pause
        exit /b 1
    )

    py -m pip install --user --disable-pip-version-check -r requirements.txt

    if errorlevel 1 (
        echo.
        echo FEHLER: Streamlit konnte nicht installiert werden.
        echo Pruefe bitte deine Internetverbindung und Python Installation.
        echo.
        pause
        exit /b 1
    )
)

echo Das Dashboard wird im Browser geoeffnet.
echo.
echo Dieses Fenster muss geoeffnet bleiben.
echo Zum Beenden Strg+C druecken oder das Fenster schliessen.
echo.

py -m streamlit run "Dashboard_Cybersecurity.py"

if errorlevel 1 (
    echo.
    echo Das Dashboard wurde mit einem Fehler beendet.
    pause
)

endlocal
