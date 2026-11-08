# Schutz der Paketanzeige vor HACS-Updates

Die lokale Vorlage `/config/custom_templates/pakete.jinja` wird nicht von den
HACS-Updates für DHL oder Amazon überschrieben.

- **DHL:** Wenn ein ausgehendes Einschreiben wieder als unbekannt gemeldet wird,
  korrigiert die Anzeige es nur bei passendem Sendungsnummernformat, abgeschlossenem
  Fortschritt und eindeutigem Auslieferungstext mit gültigem Datum. Alte Einträge
  verschwinden aus den offenen Sendungen; innerhalb der letzten sieben
  Kalendertage erscheinen sie unter „Angekommen“. Native Zustelldaten haben Vorrang.
- **Amazon:** Wenn kein strukturiertes Lieferfenster vorhanden ist, übernimmt die
  Vorlage „Zustellung: <Wochentag>“ wortgetreu aus der Antwort. Für fehlende
  Zustelldaten erkennt sie auch „Im Briefkasten hinterlegt“ als Zustellereignis.
  Der Wochentag allein wird nicht als Kalendereintrag interpretiert.

Der Schutz betrifft die Dashboard-Anzeige und ihre Zähler. Wenn ein Update
Sendungen oder die benötigten Rohdaten nicht mehr liefert oder deren Schema
ändert, muss die Integration geprüft werden. Die Vorlage ändert keine
Integration, Events oder Automationen und blockiert keine Updates.

Die bisherige HA-Vorlage liegt zur Wiederherstellung unter
`/config/codex_backups/pakete-hacs-20261108-221550-111756/pakete.jinja`.
Nach dem Wiederherstellen einer Vorlage `homeassistant.reload_custom_templates`
aufrufen.
