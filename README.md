# PTB-MN: Posting-Pipeline-Bot

Dieser Bot ist für die automatisierte Posting-Pipeline des Militärnews-Kanals zuständig. Er verarbeitet neue Nachrichten, editiert bestehende Posts und verwaltet Medien-Uploads.

## Funktionen
- **Automatisches Posten:** Verarbeitet Nachrichten aus dem Hauptkanal.
- **Editier-Logik:** Synchronisiert Änderungen an Kanal-Posts.
- **Crawler:** Automatische Erfassung von Informationen aus externen Quellen.
- **Medien-Handler:** Automatischer Download und Verarbeitung von Bildern und Videos.
- **Promotion & Werbung:** Verwaltung von Werbe-Posts und Promo-Aktionen.

## Installation & Deployment
Dieser Bot ist für den Betrieb als **Quadlet-Container** optimiert.

1. Kopiere die Datei `ptb-mn.container` nach `~/.config/containers/systemd/`.
2. Erstelle eine `.env` Datei im Projektverzeichnis mit den notwendigen API-Tokens.
3. Starte den Dienst mit:
   ```bash
   systemctl --user daemon-reload
   systemctl --user start ptb-mn
   ```

## Struktur
- `bot/channel/`: Kernlogik für Kanal-Operationen.
- `bot/social/`: Integrationen für Twitter/X und WhatsApp.
- `bot/util/`: Hilfsfunktionen für Medien und Übersetzungen.
