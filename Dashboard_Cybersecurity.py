from __future__ import annotations

import calendar
import html
import json
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional

import streamlit as st

DATA_FILE = Path(__file__).with_name("student_data.json")


# Das Enum legt die drei möglichen Ergebnisse des Notenvergleis fest.
# Durch feste Werte werden ungültige Vergleichstexte vermieden.
class Vergleichsergebnis(Enum):
    BESSER = "Besser"
    GLEICH = "Gleich"
    SCHLECHTER = "Schlechter"


# Diese Klasse kapselt die eigene Note eines Moduls.
# Sie übernimmt die Validierung, die Bestehensprüfung und den Vergleich mit einer Referenznote.
class Prüfungsleistung:
    # Beim Erzeugen wird erstmal ein leerer Zustand hergestellt.
    # Die Übergabe erfolgt dann bewusst über setze_note(), damit dieselbe Validierung gilt.
    def __init__(self, eigene_note: Optional[float] = None) -> None:
        self._eigene_note: Optional[float] = None
        self.setze_note(eigene_note)

    # Die Property erlaubt einen kontrollierten Lesezugriff auf das private Attribut _eigene_note.
    @property
    def eigene_note(self) -> Optional[float]:
        return self._eigene_note

    # Auch eine direkte Zuweisung an eigene_note wird an die zentrale Validierung weitergeleitet.
    @eigene_note.setter
    def eigene_note(self, note: Optional[float]) -> None:
        self.setze_note(note)

    # Eine Note darf entweder offen (None) oder eine Zahl zwischen 1,0 und 5,0 sein.
    # Boolesche Werte werden ausgeschlossen, obwohl bool in Python eine Unterklasse von int ist.
    def setze_note(self, note: Optional[float]) -> None:
        if note is not None:
            if isinstance(note, bool) or not isinstance(note, (int, float)):
                raise TypeError("Die Note muss eine Zahl oder None sein.")
            note = float(note)
            if not 1.0 <= note <= 5.0:
                raise ValueError("Die Note muss zwischen 1,0 und 5,0 liegen.")
        self._eigene_note = note

    # Eine vorhandene Note bis einschließlich 4,0 gilt als bestanden.
    def ist_bestanden(self) -> bool:
        return self._eigene_note is not None and self._eigene_note <= 4.0

    # Kleinere Noten sind im deutschen Notensystem besser.
    # Eine Toleranz von 0,05 verhindert, dass minimale Rundungsabweichungen als Unterschied gelten.
    def vergleiche_note(self, vergleichsnote: float) -> Vergleichsergebnis:
        if self._eigene_note is None:
            raise ValueError("Ohne eigene Note ist kein Vergleich möglich.")
        differenz = vergleichsnote - self._eigene_note
        if differenz > 0.05:
            return Vergleichsergebnis.BESSER
        if differenz < -0.05:
            return Vergleichsergebnis.SCHLECHTER
        return Vergleichsergebnis.GLEICH

    # Die absolute Differenz beschreibt die Größe der Abweichung unabhängig von der Richtung.
    def abweichung(self, vergleichsnote: float) -> float:
        if self._eigene_note is None:
            raise ValueError("Ohne eigene Note kann keine Abweichung berechnet werden.")
        return abs(vergleichsnote - self._eigene_note)


# Ein Modul bündelt Stammdaten, Vergleichsnote und genau eine Prüfungsleistung.
# Berechnungen zur eigenen Leistung werden an das enthaltene Prüfungsleistungsobjekt gegeben.
class Modul:
    def __init__(
        self,
        modulID: str,
        name: str,
        ects: int,
        semester: int,
        vergleichsnote: float,
        prüfungsleistung: Prüfungsleistung,
    ) -> None:
        self.modulID = modulID
        self.name = name
        self.ects = ects
        self.semester = semester
        self.vergleichsnote = vergleichsnote
        self.prüfungsleistung = prüfungsleistung

    # Delegiert den Vergleich und verwendet dabei automatisch die Vergleichsnote dieses Moduls.
    def vergleiche_eigene_note(self) -> Vergleichsergebnis:
        return self.prüfungsleistung.vergleiche_note(self.vergleichsnote)

    # Liefert die absolute Abweichung zwischen eigener Note und Vergleichsnote.
    def berechne_abweichung(self) -> float:
        return self.prüfungsleistung.abweichung(self.vergleichsnote)


# Der Studiengang fasst alle Module und die Rahmendaten des Studiums zusammen.
# Hier befinden sich die fachlichen Berechnungen für ECTS, Prüfungen, Noten und Studienzeit.
class Studiengang:
    def __init__(
        self,
        name: str,
        zielECTS: int,
        regelstudienzeit_semester: int,
        studienbeginn: date,
        module: Optional[list[Modul]] = None,
    ) -> None:
        self.name = name
        self.zielECTS = zielECTS
        self.regelstudienzeit_semester = regelstudienzeit_semester
        self.studienbeginn = studienbeginn
        self.module = [] if module is None else module

    # ECTS werden nur für Module addiert, deren Prüfungsleistung bestanden wurde.
    def erreichte_ects(self) -> int:
        return sum(
            modul.ects
            for modul in self.module
            if modul.prüfungsleistung.ist_bestanden()
        )

    # Der ECTS Fortschritt wird als Prozentwert bezogen auf das Studienziel berechnet.
    # Die Prüfung auf zielECTS <= 0 verhindert eine Division durch null.
    def berechne_ects_fortschritt(self) -> float:
        if self.zielECTS <= 0:
            return 0.0
        return self.erreichte_ects() / self.zielECTS * 100

    # Als abgeschlossen zählt jedes Modul mit eingetragener Note, unabhängig vom Bestehen.
    def berechne_prüfungsfortschritt(self) -> float:
        if not self.module:
            return 0.0
        abgeschlossen = sum(
            modul.prüfungsleistung.eigene_note is not None
            for modul in self.module
        )
        return abgeschlossen / len(self.module) * 100

    # Der Durchschnitt wird mit den ECTS der Module gewichtet.
    # Module ohne eingetragene Note werden bei Summe und Gewicht nicht beachtet.
    def berechne_notendurchschnitt(self) -> float:
        gewichtete_summe = 0.0
        berücksichtigte_ects = 0
        for modul in self.module:
            note = modul.prüfungsleistung.eigene_note
            if note is not None:
                gewichtete_summe += note * modul.ects
                berücksichtigte_ects += modul.ects
        if berücksichtigte_ects == 0:
            return 0.0
        return gewichtete_summe / berücksichtigte_ects

    # Ein Semester wird mit sechs Monaten angesetzt.
    # calendar.monthrange stellt sicher, dass der Tag auch im Zielmonat gültig ist.
    def berechne_regelstudienende(self) -> date:
        gesamt_monate = self.regelstudienzeit_semester * 6
        monatsindex = self.studienbeginn.month - 1 + gesamt_monate
        jahr = self.studienbeginn.year + monatsindex // 12
        monat = monatsindex % 12 + 1
        tag = min(self.studienbeginn.day, calendar.monthrange(jahr, monat)[1])
        return date(jahr, monat, tag)

    # Vergleicht die seit Studienbeginn verstrichenen Tage mit der gesamten Regelstudienzeit.
    # Der Prozentwert wird auf den Bereich von 0 bis 100 begrenzt.
    def berechne_zeitfortschritt(self) -> float:
        regelstudienende = self.berechne_regelstudienende()
        gesamtdauer = (regelstudienende - self.studienbeginn).days
        if gesamtdauer <= 0:
            return 0.0
        vergangen = (date.today() - self.studienbeginn).days
        vergangen = max(0, min(vergangen, gesamtdauer))
        return vergangen / gesamtdauer * 100

    # Positive Werte bedeuten einen Vorsprung, negative Werte einen Rückstand gegenüber der Zeit.
    def abweichung_vom_zeitplan(self) -> float:
        return self.berechne_ects_fortschritt() - self.berechne_zeitfortschritt()


# Das Repository trennt die Dateispeicherung von der Fachlogik und Benutzeroberfläche.
# In der Datei student_data.json werden nur die Noten und der Studienbeginn gespeichert.
class JsonNotenRepository:
    def __init__(self, datei: Path) -> None:
        self.datei = datei

    # Fehlt die Datei oder enthält sie ungültige Daten, werden sichere Standardwerte geliefert.
    # Jeder geladene Wert wird geprüft, bevor er an die Fachobjekte weitergegeben wird.
    def laden(self) -> dict:
        if not self.datei.exists():
            return {"noten": {}, "studienbeginn": date.today()}
        try:
            daten = json.loads(self.datei.read_text(encoding="utf-8"))
            if not isinstance(daten, dict):
                raise ValueError
            noten: dict[str, Optional[float]] = {}
            rohe_noten = daten.get("noten", {})
            if isinstance(rohe_noten, dict):
                for modul_id, note in rohe_noten.items():
                    if not isinstance(modul_id, str):
                        continue
                    if note is None:
                        noten[modul_id] = None
                    elif (
                        isinstance(note, (int, float))
                        and not isinstance(note, bool)
                        and 1.0 <= float(note) <= 5.0
                    ):
                        noten[modul_id] = float(note)
            try:
                studienbeginn = date.fromisoformat(daten.get("studienbeginn", ""))
                if studienbeginn > date.today():
                    studienbeginn = date.today()
            except (TypeError, ValueError):
                studienbeginn = date.today()
            return {"noten": noten, "studienbeginn": studienbeginn}
        except (OSError, json.JSONDecodeError, ValueError):
            return {"noten": {}, "studienbeginn": date.today()}

    #Zuerst wird in eine temporäre Datei geschrieben.
    # Das Ersetzen reduziert das Risiko einer unvollständigen JSON Datei.
    def speichern(self, studiengang: Studiengang) -> None:
        daten = {
            "noten": {
                modul.modulID: modul.prüfungsleistung.eigene_note
                for modul in studiengang.module
            },
            "studienbeginn": studiengang.studienbeginn.isoformat(),
        }
        temporäre_datei = self.datei.with_suffix(".tmp")
        temporäre_datei.write_text(
            json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        temporäre_datei.replace(self.datei)


# Der Service bildet die Vermittlungsschicht zwischen Streamlit Oberfläche und Datenmodell.
# Er lädt den Studiengang, führt Änderungen aus und veranlasst die Speicherung.
class DashboardService:
    # Zentrale Stammdaten aller Module: ID, Name, ECTS, Semester und fiktive Vergleichsnote.
    MODULE = [
        ("CS01", "Betriebssysteme, Rechnernetze und verteilte Systeme", 5, 1, 2.5),
        ("CS02", "Einführung in Datenschutz und IT-Sicherheit", 5, 1, 2.3),
        ("CS03", "Einführung in die Programmierung mit Python", 5, 1, 2.4),
        ("CS04", "Einführung in das wissenschaftliche Arbeiten für IT und Technik", 5, 1, 2.1),
        ("CS05", "Projekt: Objektorientierte und funktionale Programmierung mit Python", 5, 1, 2.2),
        ("WPC1", "Wahlpflichtbereich C (Platzhalter)", 5, 1, 2.5),
        ("CS06", "Einführung in die Netzwerkforensik", 5, 2, 2.5),
        ("CS07", "Mathematik Grundlagen I", 5, 2, 2.7),
        ("CS08", "Statistik: Wahrscheinlichkeit und deskriptive Statistik", 5, 2, 2.6),
        ("CS09", "Requirements Engineering", 5, 2, 2.4),
        ("CS10", "Projekt: Agiles Projektmanagement", 5, 2, 2.2),
        ("WPC2", "Wahlpflichtbereich C (Platzhalter)", 5, 2, 2.5),
        ("CS11", "Grundzüge des System-Pentestings", 5, 3, 2.4),
        ("CS12", "Theoretische Informatik und Mathematische Logik", 5, 3, 2.8),
        ("CS13", "Social Engineering und Insider Threats", 5, 3, 2.3),
        ("CS14", "Technische und betriebliche IT-Sicherheitskonzeptionen", 5, 3, 2.5),
        ("CS15", "Projekt: Social Engineering", 5, 3, 2.2),
        ("WPC3", "Wahlpflichtbereich C (Platzhalter)", 5, 3, 2.5),
        ("CS16", "DevSecOps und gängige Software-Schwachstellen", 5, 4, 2.4),
        ("CS17", "Kryptografische Verfahren", 5, 4, 2.7),
        ("CS18", "Host- und Softwareforensik", 5, 4, 2.5),
        ("CS19", "Seminar: Aktuelle Themen in Computer Science", 5, 4, 2.2),
        ("CS20", "Projekt: Einsatz und Konfiguration von SIEM-Systemen", 5, 4, 2.3),
        ("WPC4", "Wahlpflichtbereich C (Platzhalter)", 5, 4, 2.5),
        ("CS21", "Threat Modeling", 5, 5, 2.4),
        ("CS22", "Standards der Informationssicherheit", 5, 5, 2.3),
        ("WPA", "Wahlpflichtbereich A (Platzhalter)", 10, 5, 2.5),
        ("CS23", "Projekt: Threat Modeling", 5, 5, 2.2),
        ("WPC5", "Wahlpflichtbereich C (Platzhalter)", 5, 5, 2.5),
        ("WPB", "Wahlpflichtbereich B (Platzhalter)", 10, 6, 2.5),
        ("CS24", "Projekt: Allgemeine Programmierung mit C/C++", 5, 6, 2.4),
        ("WPC6", "Wahlpflichtbereich C (Platzhalter)", 5, 6, 2.5),
        ("BA", "Bachelorarbeit", 9, 6, 2.1),
        ("KOL", "Kolloquium", 1, 6, 2.0),
    ]

    # Das Repository wird von außen übergeben, der Studiengang wird erst beim Laden erzeugt.
    def __init__(self, repository: JsonNotenRepository) -> None:
        self.repository = repository
        self.studiengang: Optional[Studiengang] = None

    # Gespeicherte Werte werden geladen und mit den festen Modulstammdaten kombiniert.
    # Für jedes Modul entsteht eine eigene Prüfungsleistung mit der ggf gespeicherten Note.
    def lade_studiengang(self) -> Studiengang:
        daten = self.repository.laden()
        noten = daten.get("noten", {})
        module = [
            Modul(
                modulID,
                name,
                ects,
                semester,
                vergleichsnote,
                Prüfungsleistung(noten.get(modulID)),
            )
            for modulID, name, ects, semester, vergleichsnote in self.MODULE
        ]
        self.studiengang = Studiengang(
            "B.Sc. Cyber Security",
            180,
            6,
            daten["studienbeginn"],
            module,
        )
        return self.studiengang

    # Sucht das Modul anhand seiner eindeutigen ID und lässt die Note validiert setzen.
    def ändere_note(self, modul_id: str, note: Optional[float]) -> None:
        if self.studiengang is None:
            raise RuntimeError("Der Studiengang wurde noch nicht geladen.")
        for modul in self.studiengang.module:
            if modul.modulID == modul_id:
                modul.prüfungsleistung.setze_note(note)
                return
        raise ValueError(f"Unbekannte Modul-ID: {modul_id}")

    # Die eigentliche Dateiarbeit bleibt vollständig Aufgabe des Repositorys.
    def speichere_studiengang(self) -> None:
        if self.studiengang is None:
            raise RuntimeError("Der Studiengang wurde noch nicht geladen.")
        self.repository.speichern(self.studiengang)


# Diese Klasse enthält die grafische Streamlit Oberfläche.
# Fachliche Änderungen und Speicherung erfolgen weiterhin über den DashboardService.
class DashboardApp:
    def __init__(self, service: DashboardService) -> None:
        self.service = service

    @staticmethod
    # Formatiert Noten für die deutsche Anzeige und zeigt bei fehlender Note einen Bindestrich.
    def _note_anzeigen(note: Optional[float]) -> str:
        return "-" if note is None else f"{note:.1f}".replace(".", ",")

    @staticmethod
    # Erstellt einen verständlichen Text für den Vergleich in der Ergebnistabelle.
    def _vergleich_anzeigen(modul: Modul) -> str:
        if modul.prüfungsleistung.eigene_note is None:
            return "Offen"
        ergebnis = modul.vergleiche_eigene_note()
        if ergebnis is Vergleichsergebnis.GLEICH:
            return ergebnis.value
        return f"{modul.berechne_abweichung():.1f} {ergebnis.value.lower()}".replace(".", ",")

    # Baut die vollständige Oberfläche auf und verarbeitet die Benutzereingaben.
    def starten(self) -> None:
        st.set_page_config(page_title="Studien-Dashboard", layout="wide")
        studiengang = self.service.lade_studiengang()

        st.title("Studien-Dashboard Cyber Security")
        st.subheader("Studieneinstellungen")
        # Das Formular verhindert eine Verarbeitung, bevor die Schaltfläche benutzt wurde.
        with st.form("studienbeginn_formular"):
            neuer_beginn = st.date_input(
                "Studienbeginn selbst eintragen",
                value=studiengang.studienbeginn,
                max_value=date.today(),
                format="DD.MM.YYYY",
            )
            beginn_speichern = st.form_submit_button("Studienbeginn speichern")
        if beginn_speichern:
            studiengang.studienbeginn = neuer_beginn
            try:
                self.service.speichere_studiengang()
                st.success("Der Studienbeginn wurde gespeichert.")
                st.rerun()
            except OSError:
                st.error("Der Studienbeginn konnte nicht gespeichert werden.")

        # Die vier wichtigsten Kennzahlen werden nebeneinander als kompakte Übersicht dargestellt.
        spalte1, spalte2, spalte3, spalte4 = st.columns(4)
        spalte1.metric("ECTS-Fortschritt", f"{studiengang.berechne_ects_fortschritt():.1f} %".replace(".", ","))
        spalte2.metric("Prüfungsfortschritt", f"{studiengang.berechne_prüfungsfortschritt():.1f} %".replace(".", ","))
        spalte3.metric("Erreichte ECTS", f"{studiengang.erreichte_ects()} / {studiengang.zielECTS}")
        spalte4.metric("Notendurchschnitt", self._note_anzeigen(studiengang.berechne_notendurchschnitt()))

        # ECTS und Zeitfortschritt werden für Balken, Markierung und Abweichung benötigt.
        ects_fortschritt = studiengang.berechne_ects_fortschritt()
        zeitfortschritt = studiengang.berechne_zeitfortschritt()
        zeitabweichung = studiengang.abweichung_vom_zeitplan()
        richtung = "vor" if zeitabweichung >= 0 else "hinter"

        st.markdown("**Studienfortschritt im Vergleich zur Studienzeit**")
        balken_fortschritt = min(max(ects_fortschritt, 0.0), 100.0)
        markierung = min(max(zeitfortschritt, 0.0), 100.0)
        # Der rote Balken zeigt den ECTS Fortschritt, der dunkle Strich markiert den Zeitfortschritt.
        fortschrittsanzeige = f"""
        <div style="position: relative; width: 100%; height: 16px;
                    margin: 2px 0 18px 0; border-radius: 8px;
                    background-color: #e9edf3; overflow: visible;">
            <div style="width: {balken_fortschritt:.1f}%; height: 16px;
                        border-radius: 8px; background-color: #ff4b4b;"></div>
            <div style="position: absolute; left: {markierung:.1f}%; top: -5px;
                        width: 2px; height: 26px; background-color: #31333f;
                        transform: translateX(-1px);"></div>
        </div>
        """
        st.markdown(fortschrittsanzeige, unsafe_allow_html=True)
        st.caption(
            f"{abs(zeitabweichung):.1f} Prozentpunkte {richtung} dem Zeitplan".replace(".", ",")
        )
        st.caption(
            f"Berechnet ab dem Studienbeginn {studiengang.studienbeginn.strftime('%d.%m.%Y')}."
        )

        st.subheader("Eigene Noten eintragen")
        optionen = ["Offen", "1.0", "1.3", "1.7", "2.0", "2.3", "2.7", "3.0", "3.3", "3.7", "4.0", "5.0"]
        auswahlen: dict[str, str] = {}
        # Für jedes Modul wird aus den zulässigen Noten oder dem Zustand „Offen“ gewählt.
        with st.form("notenformular"):
            for modul in studiengang.module:
                spalte_modul, spalte_ects, spalte_note = st.columns([5, 1, 2])
                spalte_modul.write(modul.name)
                spalte_ects.write(modul.ects)
                aktueller_wert = "Offen" if modul.prüfungsleistung.eigene_note is None else f"{modul.prüfungsleistung.eigene_note:.1f}"
                auswahlen[modul.modulID] = spalte_note.selectbox(
                    f"Note für {modul.name}",
                    optionen,
                    index=optionen.index(aktueller_wert),
                    key=f"note_{modul.modulID}",
                    label_visibility="collapsed",
                )
            noten_speichern = st.form_submit_button("Noten speichern", type="primary")

        # Alle Auswahlen werden über den Service in das Modell übertragen und gemeinsam gespeichert.
        if noten_speichern:
            try:
                for modul_id, auswahl in auswahlen.items():
                    self.service.ändere_note(
                        modul_id, None if auswahl == "Offen" else float(auswahl)
                    )
                self.service.speichere_studiengang()
                st.success("Die Daten wurden gespeichert.")
                st.rerun()
            except (OSError, TypeError, ValueError) as fehler:
                st.error(f"Die Daten konnten nicht gespeichert werden: {fehler}")

        st.subheader("Notenvergleich")
        # Die Tabellenzeilen werden aus den aktuellen Modulwerten erzeugt.
        # html.escape verhindert, dass Modulnamen als HTML verstanden werden.
        zeilen = []
        for modul in studiengang.module:
            zeilen.append(
                "<tr>"
                f"<td>{html.escape(modul.name)}</td>"
                f"<td>{self._note_anzeigen(modul.prüfungsleistung.eigene_note)}</td>"
                f"<td>{self._note_anzeigen(modul.vergleichsnote)}</td>"
                f"<td>{self._vergleich_anzeigen(modul)}</td>"
                "</tr>"
            )
        st.markdown(
            "<table><thead><tr><th>Modul</th><th>Eigene Note</th>"
            "<th>Vergleichsnote</th><th>Einordnung</th></tr></thead><tbody>"
            + "".join(zeilen)
            + "</tbody></table>",
            unsafe_allow_html=True,
        )
        st.caption("Alle Vergleichswerte sind frei erfundene Testdaten.")


# Einstiegspunkt bei direktem Start der Datei.
# Die Objekte werden entsprechend ihrer Abhängigkeiten Repository --> Service --> App aufgebaut.
if __name__ == "__main__":
    repository = JsonNotenRepository(DATA_FILE)
    service = DashboardService(repository)
    app = DashboardApp(service)
    app.starten()