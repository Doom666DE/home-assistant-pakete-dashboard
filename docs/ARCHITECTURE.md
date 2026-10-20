# Datenfluss

1. Die einzelnen Paketdienst-Integrationen liefern Kontosendungen bzw. manuell hinzugefügte Trackingnummern als Sensorattribute.
2. Parcel Aggregator fasst diese Informationen zusammen. `pakete.jinja` vereinheitlicht Darstellung, ergänzt verfügbare Informationen und zählt erkennbare Sendungen ohne erkennbare Dubletten doppelt zu zählen. Amazon und der physische Paketdienst können dieselbe Lieferung führen.
3. Das Dashboard ruft die Makros für Zähler, Sendungskarten, Dienste und Tabelle auf. Layout und CSS stehen im Dashboard, die fachliche Datenaufbereitung überwiegend in Jinja.
4. Die Mail-Automation liest neue IMAP-Nachrichten und erkennt UPS-/GLS-Trackingnummern. Ihr vorhandener KI-Fallback ist auf passende Versandmails beschränkt. Zugangsdaten werden von der IMAP-Integration verwaltet.
5. `dpd_enrichment` prüft lokal Versandmail-Kandidaten, lädt bei Bedarf den vollständigen Inhalt über `imap.fetch` und speichert einen Absender nur bei eindeutig zugeordneter Sendungsnummer. Die lokale Absenderanalyse selbst nutzt keine KI. Verifizierte Website-/manuelle Absender haben Vorrang vor Mail-Ergänzungen. Der interne Name und die Entität `sensor.dpd_zusatzinformationen` bleiben aus Kompatibilitätsgründen bestehen, obwohl auch UPS/GLS ergänzt werden.
6. Briefankündigungen werden separat aus passenden Deutsche-Post-Mails gezählt. „Leeren“ leert nur die HA-Ankündigungsliste, nicht das Postfach.
7. Die DPD-Karte spricht mit der Chrome-Erweiterung und den authentifizierten HA-WebSocket-Kommandos von `dpd_assist`. Die Erweiterung bindet eine Aufgabe an die Sendung, den Tab und die konkrete Vorschau. Nach Einzelbestätigung kann HA die vorhandene KI nutzen; abgelaufene, unpassende oder bereits verwendete Aufgaben werden zurückgewiesen.
8. Erst eine passende DPD-Detailansicht bestätigt die Browser-Erfassung. Der Absender wird übernommen; der Browser-Helfer ersetzt nicht die direkte DPD-Kontoanmeldung und überschreibt keinen Paketstatus. Das Schließen folgt dem erfolgreichen Erfassen, nicht allein einem starren Timer ab dem ersten Klick.

## Statusbegriffe

- **Unterwegs:** eingehende, noch nicht zugestellte Sendung; konkrete Karte kann zusätzlich „Angekündigt“ oder „In Zustellung“ zeigen.
- **Zum Paketshop:** Transport zur Abholstelle.
- **Abholbereit:** liegt zur Abholung bereit; noch nicht vom Empfänger abgeholt.
- **Zugestellt:** eingehende Sendung ist zugestellt bzw. abgeholt.
- **Ausgehend:** selbst versendete, noch laufende Sendung.
- **Angekommen:** ausgehende Sendung wurde ihrem Empfänger zugestellt.

Ein exaktes verfügbares Datum hat Vorrang vor einem Lieferzeitraum. Ohne brauchbare Daten wird kein erfundener Liefertermin angezeigt. Zugestellte Sendungen werden anhand verfügbarer Zustellzeitpunkte absteigend sortiert; fehlende Zeitpunkte bleiben ein Datenqualitätsproblem.
