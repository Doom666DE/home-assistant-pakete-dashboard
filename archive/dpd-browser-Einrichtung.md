> Historische Notiz vom ursprünglichen Aufbau. Aktuell: docs/INSTALLATION.md.

# DPD Browser-Hilfe

Der HA-Teil und die Karte sind für das ursprüngliche Paket-Dashboard vorbereitet. Die Kopie bleibt unverändert.

## Browser-Erweiterung einmal laden

1. In Chrome `chrome://extensions` öffnen.
2. Entwicklermodus einschalten und **Entpackte Erweiterung laden** wählen.
3. Diesen Ordner auswählen:
   `browser-extension/`
4. Home-Assistant-Dashboard und vorhandenen DPD-Tab neu laden.

Die Erweiterung wird nur auf `https://my.dpd.de/` und deinem HA unter `http://homeassistant.local:8123/` aktiv. Sie liest das einzelne angezeigte CAPTCHA-Bild und die Paketnummer. Sie liest keine HA-Zugangsdaten oder Browser-Cookies. Die Verbindung benötigt keinen zusätzlichen Schlüssel oder öffentlich erreichbaren Server.

## Ablauf

- DPD-Paket auswählen und **DPD öffnen**. Auf der Prüfseite die PLZ eingeben, falls erforderlich.
- Im Dashboard **Vorschau holen**. Es wird noch keine KI-Anfrage gestartet.
- Mit **Dieses CAPTCHA bearbeiten** genau dieses Bild an die vorhandene HA-OpenAI-KI senden, den gelesenen Code zusammen mit PLZ **00000** eintragen und einmal bestätigen.
- Die Vorschau gilt maximal zwei Minuten und einmal. Bei geändertem Bild, anderer Paketnummer, anderer PLZ oder uneindeutigem Ergebnis stoppt der Helfer.
- Erst eine eindeutig passende DPD-Detailseite bestätigt den Erfolg. Ihr Absender wird dann in den bestehenden DPD-Zusatzinformationen gespeichert. Der Paketstatus wird nicht überschrieben.

Die KI-Nutzung läuft über deine bestehende OpenAI-API-Konfiguration in HA. Ein CAPTCHA-Test und die Browser-Verbindung sind erst nach Installation der Erweiterung möglich. Fehlgeschlagene Versuche werden nicht automatisch wiederholt.

## Dateien

HA: `custom_components/dpd_assist`, `packages/dpd_assist.yaml`; Frontend: `www/pakete/dpd-assist-card.js`. Die Moduldatei ist über `frontend.extra_module_url` eingebunden.

Die Vorher-Dateien liegen im Arbeitsordner: `configuration-before-dpd-assist.yaml` und `before-dpd-assist.json`. Dashboard-Änderungen werden über den HA-Rohkonfigurationseditor gespeichert.
