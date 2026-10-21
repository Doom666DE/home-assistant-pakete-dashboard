# Lokaler UPS-Transportfix vom 21. Oktober 2026

Für ha-ups 1.1.3: Der aiohttp-Tracking-POST lief trotz erfolgreichem Bootstrap und vorhandenen CSRF-Cookies nach etwa 20 Sekunden in einen Timeout. Ein direkter libcurl-Abruf mit konsistentem TLS/HTTP-Profil liefert aktuelle Daten ohne Chrome, Browser-Erweiterung, übernommene Browser-Cookies oder deaktivierte Zertifikatsprüfung.

Die lokale Anpassung verwendet `curl_cffi==0.16.3`. Die bestehende Verarbeitung, Normalisierung, Dublettenbehandlung, Abrufbudgetierung und Fehlerpause bleiben zuständig. Beim erstmaligen Transportwechsel wird die alte Fehlerpause einmal zurückgesetzt, das Anfragebudget bleibt erhalten. Weitere Neustarts setzen Fehlerpausen nicht zurück.

## Wiederherstellung

Voraussetzung ist die separat installierte Integration **ha-ups 1.1.3**. Im Repository-Verzeichnis auf dem HA-System zuerst prüfen:

```sh
python3 tools/apply_ups_transport.py --config /config
```

Danach mit `--apply` installieren und HA neu starten:

```sh
python3 tools/apply_ups_transport.py --config /config --apply
```

Das Werkzeug übernimmt `api.py`, ergänzt den Transportwechsel im vorhandenen `coordinator.py` und trägt **`curl_cffi==0.16.3` in der installierten `manifest.json`** ein. Es installiert keine Pakete mit pip in HA; HA lädt die deklarierte Abhängigkeit beim Neustart. Andere Versionen bzw. unerwartete Quellcodestrukturen werden abgelehnt. Ein zweiter Lauf mit demselben Stand ändert keine Dateien. Die ausgewählten Snapshot-Dateien sind weiterhin keine vollständige Integration.

Die vorherigen Dateien werden unter `/config/codex_backups/ups-transport-<Zeitstempel>/` gesichert. Ein HACS-Update kann diese lokale Anpassung überschreiben; daher vor Updates prüfen, ob Upstream einen gleichwertigen Fix enthält.

Validierung: synchroner direkter Transporttest und asynchroner API-Test lieferten HTTP 200, Status `On the Way`, `sdd=20261026`, `sdst=13:45:00`, `sdt=16:45:00`. Ungültige Antworten und UPS-Fehler werden weiterhin als Fehler behandelt; UPS-Code 504 bleibt „nicht gefunden“.

Produktionsprüfung nach HA-Neustart: Am 21.10.2026 um 14:57:25 endete der echte HA-Abruf nach 4,56 Sekunden mit null Abruffehlern. Dashboard, nächste Zustellung und Zustellkalender zeigen Montag, 26.10., 13:45–16:45. Nächste automatische Abfrage nach dem vorhandenen Budgetplan; keine Browser-Abhängigkeit.
