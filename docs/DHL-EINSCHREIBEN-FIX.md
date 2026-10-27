# DHL: altes zugestelltes Einschreiben erscheint erneut als ausgehend

## Ursache und Korrektur

Ein DHL-Update kann die lokale Einschreiben-Korrektur überschreiben. Die deutsche Schnittstelle kann bei einem abgeschlossenen Einschreiben `istZugestellt=false` liefern. Ohne die Korrektur landet die alte Sendung dadurch wieder unter den aktiven ausgehenden Sendungen, teilweise mit Status „Unbekannt“.

Die Ausnahme in `upstream-snapshots/dhl/account/countries/de/__init__.py` verlangt gemeinsam:

- die beobachtete Einschreiben-Nummernfamilie (`A` und 19 Hexadezimalzeichen),
- einen vollständig abgeschlossenen Fortschritt,
- die exakte datierte Meldung „Die Sendung wurde am TT.MM.JJJJ ausgeliefert.“.

Nur dann werden `delivered=true` und `status=delivered` gesetzt. Das Zustelldatum stammt weiterhin aus `datumAktuellerStatus`. Die bestehende Aufbewahrungsfrist kann alte Zustellungen anschließend ausblenden. Es wird keine bestimmte Sendungsnummer fest hinterlegt und kein Zustelltag erfunden.

## Nach einem HACS-Update

Den Ausnahmeblock mit der installierten Datei `/config/custom_components/dhl/account/countries/de/__init__.py` vergleichen. Falls er fehlt und die Upstream-Version den Fehler noch nicht behebt: installierte Datei sichern, den passenden Block übernehmen und Home Assistant neu starten. Die Snapshots sind ausgewählte Referenzdateien, keine vollständige Integration; eine neuere Integrationsdatei nicht pauschal durch einen älteren Snapshot ersetzen.

Am 27. Oktober 2026 wurde genau dieser Block nach einem Update wiederhergestellt. Anschließend zeigte das Live-Dashboard 0 aktive ausgehende Sendungen und die alte Sendung war ausgeblendet.

## Prüfung

```sh
python tests/test_dhl_registered_letter.py
python tools/validate.py
```

Die Offline-Tests verwenden erfundene Nummern und prüfen auch unvollständige Verläufe, andere Nummernfamilien und unbestätigte Meldungen.
