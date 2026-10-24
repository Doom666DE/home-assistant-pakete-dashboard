# Amazon-Tracking und Zustellkalender – 22. Oktober 2026

Lokal geprüft gegen Amazon Orders 0.2.0 und Parcel Aggregator 2.7.0.

## Behobene Fehler

Neue Amazon-Bestellkacheln verlinken direkt auf `/progress-tracker/package`. Der bisherige Client behandelte diese Seite als Zwischenseite und suchte darin ausschließlich einen alten `ship-track`-Link. Dadurch gingen Trackingnummer, Status und Liefertermin verloren; die Sendung erschien nicht im Dashboard.

- Direkte Trackingseiten werden sofort ausgewertet; alte Zwischenseiten bleiben unterstützt.
- Deutsche Bestellzeilen (`Bestellung aufgegeben`, `Zustellung`, `Versendet`) werden erkannt.
- Ein eindeutig genannter Liefertag wird aus dem eingebetteten Lieferhinweis übernommen: Datum, Heute/Morgen oder Wochentag. Mehrdeutige Zeiträume werden nicht auf einen einzelnen Tag reduziert.
- Neuere Ereignisse wie „In Zustellung“ haben weiterhin Vorrang vor dem allgemeinen SHIPPED-Zustand.
- Amazon-Liefertage ohne Uhrzeit erscheinen in beiden Kalendern ganztägig. Der Aggregator behält genaue Zeitfenster anderer Dienste bei.
- Die Dashboard-Karte bindet ausschließlich den gemeinsamen Paketkalender ein. Ein zusätzlicher Amazon-Kalender würde dieselbe Sendung doppelt anzeigen.

## Dateien und Übernahme

Die geprüften Dateien liegen unter `upstream-snapshots/amazon_orders/` und `upstream-snapshots/parcel_aggregator/calendar.py`. Es sind ausgewählte Referenzdateien, keine vollständigen Integrationen. Vor dem Einbau Versionen vergleichen und die ursprünglichen Dateien sichern. Python-Änderungen benötigen einen Home-Assistant-Neustart. HACS-Updates können sie überschreiben.

`dashboards/pakete.yaml` enthält die bereinigte Kalenderliste. Bereits eingerichtete Dashboards werden durch einen Git-Update nicht automatisch geändert.

## Prüfung

```sh
python tests/test_amazon_tracking.py
python tests/test_delivery_calendar.py
python tools/validate.py
```

Die Offline-Tests nutzen ausschließlich erfundene IDs und HTML. Keine Konto-Seiten, Tokens oder echten Sendungsdaten werden mitgeliefert. Zusätzlich wurde der Fix live geprüft: neue Sendung, Unterwegs-Status, angekündigter Liefertag und ganztägige Kalendereinträge wurden in Home Assistant übernommen. Die Kalenderkarte wurde anschließend auf eine einzige Quelle reduziert und zurückgelesen.

## Ergänzung: Zustelldatum bei Briefkastenzustellung – 24. Oktober 2026

Die bestätigte Amazon-Meldung „Im Briefkasten hinterlegt“ wird als Zustellereignis erkannt. Ihr Zeitstempel füllt `delivered_at`; dadurch zeigt die Dashboard-Vorlage den Zustelltag statt eines zweiten „Zugestellt“ und sortiert die Sendung nach Zustelldatum. Liegt nur ein Tag vor, wird keine genaue Uhrzeit angezeigt.

Der Regressionstest prüft Status, Zustelldatum und Verlauf mit erfundenen Daten. Die Änderung wurde zusätzlich in Home Assistant überprüft: Datum übernommen, Anzeige „Heute“, neueste Zustellung zuerst.
