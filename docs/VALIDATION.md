# Prüfung des ersten Repository-Stands

Datum: 20. Oktober 2026.

Erfolgreich lokal ausgeführt:

- `python tools/validate.py`: Python-/JSON-/YAML-/Jinja-Syntax, ausschließlich Paketansicht im aktuellen Dashboard, konsistente Browser-Origin.
- `python tests/test_dpd_assist.py`: 3 Testfälle für Bild-/Originvalidierung, Antwortformat, Benutzerbindung, Ablaufzeit und einmalige Nutzung.
- `python tests/test_dpd_enrichment.py`: synthetisches DPD-HTML, passende Sendungsnummer, Prüfseite, fehlende/mehrdeutige Absender und Versandmails.
- `python tests/test_mail_sender.py`: 8 synthetische Fälle für UPS-/GLS-/DPD-Händlermails und Ablehnungen bei Mehrdeutigkeit oder ungeeignetem Absender.
- `node tests/test_dpd_background.cjs`: Bindung an HA-Tab, Bild-Digest, einmalige Nutzung, mehrdeutige und fehlende Tabs.
- `node tests/test_dpd_extension.cjs`: Sendungsbindung, geändertes Bild, geänderte PLZ und verifizierte Absender.
- `node --check` für alle vier produktiven JavaScript-Dateien.
- `python tools/build_extension.py`: ZIP aus den bereinigten aktuellen Erweiterungsquellen erzeugt; ZIP wird bewusst nicht in Git eingecheckt.
- Gezielter Scan nach bekannten persönlichen Beispieldaten, JWTs, privaten Schlüsseln und hartcodierten Zugangsdaten-Zuweisungen.

Dies bestätigt den exportierten Quellcode und die Offline-Fixtures. Es ist kein erneuter Ende-zu-Ende-Test realer Konten, Mailpostfächer oder CAPTCHA-Aufgaben. Die bekannten Live-Einschränkungen stehen in `STATUS.md`.

## Nachprüfung: DPD-Zustelldatum

`python tests/test_dpd_delivery_date.py` erfolgreich: Der Test lädt die tatsächlichen Jinja-Makros und prüft mit synthetischen Sensorwerten die Datumserkennung aus dem DPD-Statustext, den Vorrang vorhandener Zeitstempel, ungültige und mehrdeutige Datumsangaben, Dienst-/Bucket-Grenzen sowie die gerenderte Datumsanzeige und die Reihenfolge der zugestellten Karten. `python tools/validate.py` bestätigt weiterhin die Syntax und Konfigurationsstruktur.

Zusätzlich wurde die bereits korrigierte Live-Ausgabe lesend geprüft: Die betroffene DPD-Sendung erhält aus ihrem Statustext `delivered_at` im ISO-Format. Persönliche Daten dieser Live-Prüfung werden nicht als Fixture gespeichert.
