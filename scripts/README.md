# Scripts

Dieses Verzeichnis enthält Hilfsskripte für das `ptb-mn` Projekt.

## migrate_neon.py

Dieses Skript migriert alle Daten von der Neon.tech PostgreSQL-Datenbank in die lokale Datenbank.

### Voraussetzungen

- Python 3.x
- `psycopg2-binary`
- `python-dotenv`

Installation der Abhängigkeiten:
```bash
pip install psycopg2-binary python-dotenv
```

### Verwendung

Das Skript liest die Verbindungsparameter aus der `.env`-Datei im Root-Verzeichnis des Projekts:

- `DATABASE_URL_NEON`: Die URL zur Neon.tech-Datenbank (Quelle).
- `DATABASE_URL`: Die URL zur lokalen Datenbank (Ziel).

Sollten diese Variablen nicht gesetzt sein, verwendet das Skript vordefinierte Standardwerte für die lokale Entwicklung.

Ausführung:
```bash
python scripts/migrate_neon.py
```

Das Skript erstellt automatisch das erforderliche Schema in der Zieldatenbank, falls es noch nicht existiert.
