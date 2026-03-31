# PTB-MN: Posting-Pipeline-Bot

Der **PTB-MN Bot** ist das Herzstück der Nachrichtenverbreitung im MilitärNews-System. Er automatisiert den Prozess des Postens und Editierens von Inhalten in den MilitärNews-Kanälen und synchronisiert diese über mehrere Sprachkanäle hinweg.

## Kernfunktionen

Der Bot konzentriert sich ausschließlich auf die Kern-Posting-Pipeline:

*   **Automatisches Posten:** Verarbeitet und veröffentlicht Nachrichtenartikel und Medien in den Hauptkanälen.
*   **Multi-Sprachen-Synchronisation:** Übersetzt Posts automatisch in 10+ Sprachen und verteilt sie auf entsprechende Kanäle.
*   **Editier-Synchronisation:** Stellt sicher, dass Änderungen an Quell-Posts auch in den veröffentlichten Kanal-Posts widergespiegelt werden.
*   **Breaking News & Announcements:** Spezialbehandlung für Eilmeldungen und Ankündigungen mit entsprechenden Formatierungen.
*   **Medien-Handling:** Automatischer Download und Verarbeitung von Bildern und Videos aus sozialen Netzwerken (Twitter/X, Instagram, YouTube).
*   **Crawler-Integration:** Sammelt automatisch Informationen aus vordefinierten externen Quellen.
*   **Promotion & Werbung:** Steuert die Veröffentlichung von Werbeinhalten und Promo-Aktionen.
*   **Meme-Posting:** Automatisches Posten von Memes in den Meme-Kanal.

## Installation & Deployment

Dieser Bot ist für den Betrieb als **Quadlet-Container** mit automatischen Updates über die GitHub Container Registry (GHCR) optimiert.

### Lokale Entwicklung
```bash
# Abhängigkeiten installieren
pip install -r bot/requirements.txt

# .env-Datei erstellen
cp .env.example .env

# Bot starten
cd bot && python main.py
```

### Deployment mit Quadlets
```bash
# Quadlet-Datei kopieren
cp ptb-mn.container ~/.config/containers/systemd/

# .env-Datei im Projektverzeichnis erstellen
# Beispiel: /home/ubuntu/projects/ptb-mn/.env
# Erforderliche Variablen:
# - TOKEN: Telegram Bot Token
# - DATABASE_URL: PostgreSQL Verbindungs-URL
# - DEEPL: DeepL API Key
# - CHANNEL_MEME: Telegram Channel ID für Meme-Kanal
# - ADMINS: JSON Array von Admin-User-IDs

# Dienst starten
systemctl --user daemon-reload
systemctl --user start ptb-mn

# Status überprüfen
systemctl --user status ptb-mn

# Logs anschauen
journalctl --user -u ptb-mn -f
```

### Auto-Updates
Der Bot nutzt `AutoUpdate=registry` in der Quadlet-Konfiguration. Die Docker-Images werden automatisch von GitHub Packages (GHCR) aktualisiert, wenn neue Versionen verfügbar sind.

## Architektur

### Verzeichnisstruktur
*   `bot/channel/`: Kernlogik für Kanal-Operationen (Posting, Editieren, Spezial-Handler).
*   `bot/social/`: Integrationen für Twitter/X und WhatsApp.
*   `bot/private/`: Private Admin-Befehle und Werbung/Promo-Verwaltung.
*   `bot/data/`: Gemeinsame Datenbankzugriffe und Sprachressourcen.
*   `bot/util/`: Hilfsfunktionen für Medien-Downloads und Übersetzungen.
*   `bot/res/`: Ressourcen-Dateien (Bilder, Flaggen, HTML-Templates).

### Unterstützte Sprachen
Der Bot postet automatisch in folgende Sprachen: Deutsch, Englisch, Türkisch, Persisch, Russisch, Portugiesisch, Spanisch, Französisch, Italienisch, Arabisch und Indonesisch.

## Konfiguration

Die Konfiguration erfolgt über Umgebungsvariablen (`.env` Datei):

| Variable             | Beschreibung                                 |
|----------------------|----------------------------------------------|
| `TOKEN`              | Telegram Bot Token                           |
| `DATABASE_URL`       | PostgreSQL Verbindungs-URL                   |
| `DEEPL`              | DeepL API Key für Übersetzungen              |
| `CHANNEL_MEME`       | Telegram Channel ID für Meme-Kanal           |
| `ADMINS`             | JSON Array von Admin-User-IDs                |
| `CONTAINER`          | `true` wenn im Container ausgeführt          |

## Entwicklung

### Lokale Tests
```bash
cd bot
python -m pytest test/
```

### Docker-Build
```bash
docker build -t ptb-mn:latest .
docker run -e TOKEN=... -e DATABASE_URL=... ptb-mn:latest
```

## Lizenz
Siehe LICENSE Datei im Repository.
