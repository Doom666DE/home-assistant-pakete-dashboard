# Installation und Wiederherstellung

## Bestehende Installation

Der Export verändert die laufende Installation nicht. Ein späterer Git-Push installiert ebenfalls nichts in Home Assistant. Vor einer Rückübertragung einen HA-Backupstand sichern und nur gezielt die gewünschten Dateien übernehmen.

## Voraussetzungen

- Home Assistant mit den separat installierten Integrationen für Amazon, DHL, Hermes, DPD, GLS, UPS und Parcel Aggregator. Die erfassten Versionen stehen in `integration-versions.json`.
- Mushroom, card-mod und vertical-stack-in-card aus HACS; die tatsächlich verwendeten Kartentypen stehen im Dashboard-YAML.
- Vorhandene IMAP-Integration für Mail-Erkennung. Bei dieser Installation kommen neue Nachrichten zunächst im Posteingang an und werden erst später manuell in einen Ordner verschoben.
- Für die optionale DPD-Bildhilfe: Chrome, ein offenes HA-Dashboard und eine konfigurierte `ai_task`-Entität. Die OpenAI-Konfiguration und ihr Schlüssel bleiben ausschließlich in HA.

## Dateien

1. `custom_components/dpd_assist` und `custom_components/dpd_enrichment` nach `/config/custom_components/` kopieren.
2. `custom_templates/pakete.jinja` und `www/pakete/` an die gleichnamigen Stellen übernehmen.
3. Die Dateien aus `packages/` bei bestehender Paket-Einbindung übernehmen. Beispiel für die Einbindung und das Frontend-Modul: `examples/configuration.example.yaml`. Vorhandene Abschnitte zusammenführen, nicht die Konfiguration überschreiben.
4. `parcel_mail_username` in der vorhandenen `secrets.yaml` hinterlegen. Zusätzlich `mail@example.invalid` in der Mail-Automation und im Brief-Package durch das zum IMAP-Ereignis passende Konto ersetzen. Diese Vergleiche benötigen den tatsächlichen Ereigniswert.
5. Helfer `input_text.paket_trackingnummer` und `input_select.paket_dienst` prüfen. `examples/helpers.yaml` dokumentiert die exportierten Definitionen; vorhandene Helfer nicht doppelt anlegen.
6. Automationen und Skripte aus den entsprechenden Ordnern über HA importieren bzw. in vorhandene YAML-Listen zusammenführen. Paket-interne Automationen/Skripte aus `packages/` nicht ein zweites Mal importieren.
7. Das Dashboard über den Rohkonfigurationseditor einfügen oder die einzelne Ansicht daraus in das vorhandene Computer-Dashboard übernehmen. Die historische Kopie ist eine einzelne Ansicht und kann optional ergänzt werden.
8. Entitätsnamen in Jinja und Dashboard, Config-Entry-IDs in Skripten sowie Gerätereferenzen im Dashboard mit der eigenen Installation abgleichen. Die IDs aus dem Export sind installationsabhängig und keine Zugangsdaten.
9. Nach Prüfung der Konfiguration HA für die neuen Python-Integrationen neu starten. Für spätere reine Jinja-Änderungen genügt `homeassistant.reload_custom_templates`.

## Browser-Hilfe

Die bereinigten Beispiele verwenden `http://homeassistant.local:8123` und PLZ `00000`. Vor Nutzung die tatsächliche HA-Origin **konsistent** in `browser-extension/manifest.json` und `browser-extension/background.js` setzen; die Karte erhält die PLZ über `postcode`. Auch die Beispiel-PLZ in der Dashboard-Karte und den Standardwert in `www/pakete/dpd-assist-card.js` prüfen.

Danach `python tools/build_extension.py` ausführen. Das erzeugt den Download unter `www/pakete/dpd-helper.zip`. In Chrome über `chrome://extensions` → Entwicklermodus → „Entpackte Erweiterung laden“ den Ordner `browser-extension/` auswählen. Eine bestehende Installation nach Änderungen neu laden und die HA-/DPD-Seiten aktualisieren.

Der Zugriff ist auf die konfigurierte HA-Origin und `https://my.dpd.de/` begrenzt. Eine laufende Browser-Anmeldung wird nicht in das Repository exportiert. Der Klick zur Bearbeitung gilt jeweils für das konkrete angezeigte Bild; ein Skript öffnet die entsprechende Einzelbestätigung im Dashboard.

## Fremdintegrationen

Für den am 21. Oktober live geprüften direkten UPS-Transportfix gibt es ein geprüftes Installationswerkzeug für **ha-ups 1.1.3**, einschließlich Manifest-Abhängigkeit und Sicherung: [UPS-Transportfix](UPS-TRANSPORT-FIX.md).

`upstream-snapshots/` enthält ausschließlich ausgewählte Dateien als Referenz. Diese nicht als komplette Integration kopieren. Vor Übernahme mit derselben bzw. der aktuell installierten Upstream-Version vergleichen, anschließend Änderungen gezielt portieren. HACS-Updates können lokale Änderungen überschreiben.

## Datenschutz

`secrets.yaml`, `.storage`, Mail-Inhalte, Sendungsverläufe, HAR-Dateien, Captures und erzeugte ZIPs sind ausgeschlossen. Private Repository-Sichtbarkeit ersetzt keine Geheimnisbereinigung. Vor einer späteren Veröffentlichung erneut Rechte, Beispieldaten und gesamte Git-Historie prüfen.
