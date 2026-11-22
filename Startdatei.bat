@echo off
setlocal
cd /d "%~dp0"
title Studien-Dashboard

echo ==========================================
echo       Studien-Dashboard wird gestartet
echo ==========================================
echo.

rem Prüfen, ob der Python Launcher für Windows vorhanden ist.
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

rem prüfen, ob die Programmdatei vorhanden ist.
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
    echo Streamlit wird jetzt für deinen Windows Benutzer installiert.
    echo Dafür wird einmalig eine Internetverbindung benötigt.
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
        echo Prüfe bitte deine Internetverbindung und Python Installation.
        echo.
        pause
        exit /b 1
    )
)

echo Das Dashboard wird im Browser geöffnet.
echo.
echo Dieses Fenster muss geöffnet bleiben.
echo Zum Beenden Strg+C drücken oder das Fenster schließen.
echo.

py -m streamlit run "Dashboard_Cybersecurity.py"

if errorlevel 1 (
    echo.
    echo Das Dashboard wurde mit einem Fehler beendet.
    pause
)

endlocal
