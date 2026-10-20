# Stand vom 20. Oktober 2026

## Exportstatus

Dashboard, Jinja, eigene Python-Integrationen, Pakete und Frontend stammen aus der laufenden Installation. Die Browser-Erweiterung wurde aus dem aktuell dort angebotenen ZIP exportiert. `docs/export-provenance.json` hält Quellen und Hashes fest. Die frühere Dashboard-Kopie und Archivnotizen sind ausdrücklich historische Varianten.

## Bekannte Einschränkungen

- **Direkte DPD-Anmeldung:** weiterhin gestört. Die DPD-Webanmeldung kann funktionieren, während der von der HA-Integration verwendete App-/SOAP-Zugang schon vor der Passwortprüfung scheitert. Dazu wurde [Issue #21](https://github.com/ha-parcel-integrations/ha-dpd/issues/21) erstellt. Dieses Repository behebt diesen Upstream-Fehler nicht.
- **UPS:** Abrufe können verzögert sein oder scheitern. Ein Trackingcode und ein aus einer Händlermail ergänzter Absender belegen keinen erfolgreichen aktuellen UPS-Statusabruf. „Angekündigt“ kann der tatsächlich zuletzt gelieferte Status sein.
- **Mail-Absender:** nur bei geeigneten Versandmails und einer eindeutig erkannten Nummer. Unterschiedliche Betreffzeilen sind möglich; eine allgemeine Garantie für jede Händler-Mail gibt es nicht. Bei mehreren Nummern wird nicht geraten.
- **Briefankündigung:** Ankündigungs-Mail ist kein Zustellnachweis. Eine Mail kann mehrere Briefbilder enthalten.
- **Liefertermine und Sortierung:** abhängig von den tatsächlich gelieferten Daten. Amazon-Ereignisse können fehlende Zeitstempel ergänzen; fehlende oder widersprüchliche Daten bleiben möglich.
- **Browser-Hilfe:** benötigt Chrome, geladene Erweiterung und ein geöffnetes HA-Dashboard. Die Bestätigung ist bildbezogen und kein dauerhafter Zustimmungsschalter. DPD-Seitenänderungen können Selektoren oder den Ablauf brechen.
- **Quellcode-Snapshots:** ausgewählte Fremddateien, keine eigenständig installierbaren Forks. HACS-Updates mit diesen Dateien vergleichen.
- **Keine automatische Bereitstellung:** der Export und spätere Git-Commits verändern Home Assistant nicht automatisch.

## Historische Anpassungen

Amazon: deutschsprachige Zustellereignisse, Ablage-Ereignisse und zeitliche Einordnung. Hermes: Abholbereit/Abgeholt und Abholstellendaten. DHL: Behandlung von Brief-/Einschreibensendungen. Die aktuellen ausgewählten Dateien stehen in `upstream-snapshots/`, mit den beim Export installierten Versionsnummern. Bei neueren Upstream-Versionen können frühere lokale Anpassungen bereits enthalten oder anders umgesetzt sein.
