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

So übernimmst du die neue Vorlage in Home Assistant: [pakete.jinja aktualisieren](INSTALLATION.md#paketejinja-aktualisieren).

Die bisherige HA-Vorlage liegt zur Wiederherstellung unter
`/config/codex_backups/pakete-hacs-20261108-221550-111756/pakete.jinja`.
Nach dem Wiederherstellen einer Vorlage `homeassistant.reload_custom_templates`
aufrufen.


## Automatische Amazon-Verkäufer-Erkennung

Die Verkäufer-Erkennung liest eindeutige Verkäuferangaben aus den
Amazon-Bestelldetails. Das Dashboard ordnet sie über die Sendungsnummer zu,
auch wenn DHL oder DPD das Paket ausliefert. Ein vorhandener Absender hat Vorrang.

1. Kopiere den Ordner `amazon_seller_guard` nach `/config/amazon_seller_guard`.
2. Kopiere `packages/amazon_verkaeufer_absicherung.yaml` nach `/config/packages`.
   Falls die Pakete noch nicht eingebunden sind, folge der
   [Installationsanleitung](INSTALLATION.md).
3. Prüfe die verwendeten Entitäts-IDs. Die Automation beobachtet
   `update.amazon_update`. Die Vorlage liest die Verkäufer aus
   `sensor.amazon_germany_eingehende_pakete`.
4. Übernimm die aktuelle Vorlage wie unter
   [pakete.jinja aktualisieren](INSTALLATION.md#paketejinja-aktualisieren)
   beschrieben und starte Home Assistant neu.

Die Automation prüft beim Start, bei einer Änderung der installierten
Amazon-Version und einmal pro Stunde. Die Wiederherstellung wurde mit der
Amazon-Integration 0.9.1 geprüft. Sie ergänzt die Verkäufer-Funktion nur,
wenn die vorgesehenen Codestellen passen. Vor dem Schreiben sichert sie
die betroffenen Dateien in `/config/amazon_seller_guard/backups`. Home
Assistant meldet eine Wiederherstellung und den dafür nötigen Neustart.
Bei einer inkompatiblen Version erscheint eine Meldung zur Prüfung.