# Studien Dashboard Cyber Security

Das Studien Dashboard ist eine mit Python und Streamlit entwickelte Webanwendung. Es ermöglicht die Eingabe und Speicherung von Noten sowie die Berechnung des ECTS, Prüfungs und zeitlichen Studienfortschritts.

## Voraussetzungen

- Windows 11
- Python 3.11 oder neuer
- Internetverbindung beim ersten Start

## Installation und Start

1. Das Repository über **Code → Download ZIP** herunterladen.
2. Die ZIP Datei vollständig entpacken.
3. Prüfen, ob sich die Dateien `Dashboard_Cybersecurity.py`, `Startdatei.bat` und `requirements.txt` im gleichen Ordner befinden.
4. `Startdatei.bat` doppelt anklicken. Falls beim ersten starten der Startdatei am Ende eine E-Mail Adresse gefordert wrid, kann dieses Feld leer gelassen werden und mit Enter übersprungen werden.
5. Das Dashboard wird automatisch im Browser geöffnet.

Die Startdatei prüft, ob Python und Streamlit verfügbar sind. Falls Streamlit noch nicht installiert ist, wird die Installation beim ersten Start automatisch durchgeführt.

## Datenspeicherung

Beim ersten Speichern wird automatisch die Datei `student_data.json` im Programmordner erstellt. Darin werden der Studienbeginn und die eingetragenen Noten gespeichert. Die Datei muss nicht manuell angelegt werden.

## Beenden

Zum Beenden im Konsolenfenster `Strg+C` drücken oder das Konsolenfenster schließen.

## Funktionstest

Einen Studienbeginn und eine Note speichern, das Dashboard beenden und erneut starten. Die gespeicherten Werte müssen nach dem Neustart weiterhin angezeigt werden.

Falls Python fehlt, kann Python unter [python.org/downloads](https://www.python.org/downloads/) heruntergeladen werden.

Viel Spaß beim Testen.
