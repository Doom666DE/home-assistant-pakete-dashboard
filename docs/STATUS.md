# Export vom 20. Oktober; Fixes ergänzt bis 22. Oktober 2026

## Exportstatus

Dashboard, Jinja, eigene Python-Integrationen, Pakete und Frontend stammen aus der laufenden Installation. Die Browser-Erweiterung wurde aus dem aktuell dort angebotenen ZIP exportiert. `docs/export-provenance.json` hält Quellen und Hashes fest. Die frühere Dashboard-Kopie und Archivnotizen sind ausdrücklich historische Varianten.

## Bekannte Einschränkungen

- **Direkte DPD-Anmeldung:** weiterhin gestört. Die DPD-Webanmeldung kann funktionieren, während der von der HA-Integration verwendete App-/SOAP-Zugang schon vor der Passwortprüfung scheitert. Dazu wurde [Issue #21](https://github.com/ha-parcel-integrations/ha-dpd/issues/21) erstellt. Dieses Repository behebt diesen Upstream-Fehler nicht.
- **UPS:** Der direkte Abruf wurde am 21. Oktober durch einen lokalen Transportfix für ha-ups 1.1.3 wiederhergestellt und in HA mit aktuellem Status und Zustellfenster geprüft. [Einbau, Abhängigkeit und Einschränkungen](UPS-TRANSPORT-FIX.md). HACS-Updates können den Fix überschreiben; zukünftige UPS-Änderungen bleiben möglich. Ein Absender aus einer Händlermail allein belegt weiterhin keinen erfolgreichen Trackingabruf.
- **Mail-Absender:** nur bei geeigneten Versandmails und einer eindeutig erkannten Nummer. Unterschiedliche Betreffzeilen sind möglich; eine allgemeine Garantie für jede Händler-Mail gibt es nicht. Bei mehreren Nummern wird nicht geraten.
- **Briefankündigung:** Ankündigungs-Mail ist kein Zustellnachweis. Eine Mail kann mehrere Briefbilder enthalten.
- **Liefertermine und Sortierung:** abhängig von den tatsächlich gelieferten Daten. Amazon-Ereignisse können fehlende Zeitstempel ergänzen; fehlende oder widersprüchliche Daten bleiben möglich.
- **Browser-Hilfe:** benötigt Chrome, geladene Erweiterung und ein geöffnetes HA-Dashboard. Die Bestätigung ist bildbezogen und kein dauerhafter Zustimmungsschalter. DPD-Seitenänderungen können Selektoren oder den Ablauf brechen.
- **Quellcode-Snapshots:** ausgewählte Fremddateien, keine eigenständig installierbaren Forks. HACS-Updates mit diesen Dateien vergleichen.
- **Keine automatische Bereitstellung:** der Export und spätere Git-Commits verändern Home Assistant nicht automatisch.

## Amazon und Kalender: 22. Oktober 2026

[Amazon-Trackingfix](AMAZON-TRACKING-FIX.md) mit direkter Unterstützung neuer Trackingseiten, deutschen Bestellzeilen und angekündigten Liefertagen. Amazon-Tageszusagen werden ganztägig angezeigt. Die aktuelle Kalenderkarte verwendet nur den Aggregator, der Amazon bereits enthält.

## Historische Anpassungen

### DPD-Zustelldatum: nachträglich synchronisiert

Die bereits live vorhandene Jinja-Korrektur wurde ins Repository übernommen: Bei zugestellten DPD-Sendungen ohne `delivered_at` wird genau ein gültiges Datum im Format `TT.MM.JJJJ` aus `raw_status` übernommen. Das gilt für eingehende und ausgehende zugestellte Aggregator-Sendungen. Ein vorhandener Zustellzeitpunkt bleibt erhalten; ungültige oder mehrdeutige Angaben werden nicht geraten. Der gemeinsame normalisierte Wert wird für Anzeige und Sortierung verwendet. Ohne angegebene Uhrzeit wird nur das Datum angezeigt, keine erfundene Zustelluhrzeit.

Regressionstests: `python tests/test_dpd_delivery_date.py`. Die Korrektur betrifft die Darstellung und ersetzt keine Reparatur der direkten DPD-Anmeldung.

Amazon: deutschsprachige Zustellereignisse, Ablage-Ereignisse und zeitliche Einordnung. Hermes: Abholbereit/Abgeholt und Abholstellendaten. DHL: Behandlung von Brief-/Einschreibensendungen. Die aktuellen ausgewählten Dateien stehen in `upstream-snapshots/`, mit den beim Export installierten Versionsnummern. Bei neueren Upstream-Versionen können frühere lokale Anpassungen bereits enthalten oder anders umgesetzt sein.

## DHL-Einschreiben: 27. Oktober 2026

Die vorhandene [Einschreiben-Korrektur](DHL-EINSCHREIBEN-FIX.md) wurde nach einem HACS-Update live wiederhergestellt. Regressionstests sichern den eng begrenzten Ausnahmefall ab; die Dokumentation erklärt die Prüfung nach künftigen Updates.
