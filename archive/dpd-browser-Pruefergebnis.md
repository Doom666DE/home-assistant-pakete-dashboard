> Historischer Prüfstand; keine aktuelle Live-Garantie. Siehe docs/STATUS.md.

# Stand der Verbindung

- HA Core 2026.10.0: Integration installiert und nach Neustart geladen.
- Konfigurationsprüfung nach Neustart ohne Warnung zur neuen Integration.
- Ursprünglicher Paket-Tab: neue DPD-Browser-Hilfe sichtbar; authentifizierter Statusaufruf bestätigt „HA bereit“.
- Alle anderen Ansichten einschließlich Paket-Kopie sind nach dem tatsächlichen Speichern exakt unverändert. Zwei vom YAML-Editor umgewandelte Zeitwerte wurden wiederhergestellt und anschließend vollständig verglichen.
- Vorhandene HA-KI (`gpt-5-nano`): Bildtest und strukturiertes Antwortformat live bestätigt: `code: K7M42`, `readable: true`.
- Lokale Tests bestanden: Bildtyp und Ursprung, Codevalidierung, Benutzerbindung, Ablaufdatum, einmalige Nutzung, geändertes Bild, falsche PLZ, andere Paketnummer, mehrfach passende Tabs und Speicherung nur aus zugeordneter Detailansicht.
- Browser-Erweiterung vom Benutzer geladen. Live geprüft: Karte meldet „Verbunden“. DPD-Seite über den Dashboard-Button geöffnet, PLZ 00000 übergeben und das aktuelle CAPTCHA für Paket 01999999999991 erfolgreich nach HA übertragen. Der authentifizierte Vorbereitungsschritt und die Bildprüfsumme funktionieren; die Vorschau zeigt „Vorschau bereit“.
- Tatsächliches DPD-CAPTCHA nach ausdrücklicher Bestätigung getestet: HA-KI liest 505079 korrekt, Helfer trägt Code und PLZ 00000 ein. Der synthetische Klick der Erweiterung löste den ASP.NET-Link nicht aus. Ein anschließender Browser-Klick öffnete erfolgreich die passende Detailansicht für Paket 01999999999991, Versender Beispielversand GmbH.
- Bestätigung im Helfer korrigiert: vorhandenes DPD-Formular mit exakt geprüftem ASP.NET-Ereignis, POST-Methode und DPD-Ursprung absenden. Lokale Tests einschließlich abweichendem Formularziel bestanden. Installierter Erweiterungsordner und beide ZIP-Dateien aktualisiert. Diese Korrektur benötigt noch das manuelle Neuladen der Erweiterung und einen weiteren Live-Test; der vollständig automatische Ablauf ist noch nicht bestätigt.
- Eine automatische Wiederholung oder Dauerzustimmung ist nicht eingebaut; jede Aufgabe startet mit dem Button der aktuellen Vorschau.

Bildbelege: `dashboard-verbindung.png`, `ki-antwortformat.png` und `vorschau-verbunden.png` in diesem Ordner.
