---
layout: default
title: MilitaerNews Posting Bot
---

# 🔰 MilitaerNews Posting Bot

Willkommen zur Dokumentation des **MilitaerNews Posting Bots** – ein automatisiertes System zur Verwaltung und Verbreitung von Inhalten über mehrsprachige Telegram-Kanäle und Social Media.

## 📚 Dokumentation

### Für Redakteure
- **[Redakteur-Handbuch](./handbuch.md)** – Alles, was Sie zum Posten und Bearbeiten von Inhalten wissen müssen
  - Posting-Pipeline und Workflow
  - Nachricht editieren
  - Eilmeldungen
  - Best Practices und Troubleshooting

### Für Entwickler
- **[README](../README.md)** – Technische Übersicht, Setup und Architektur
- **[GitHub Repository](https://github.com/militaernews/ptb-mn)** – Quellcode und Issues

## 🌍 Unterstützte Kanäle

Der Bot verwaltet Telegram-Kanäle in 11 Sprachen:

| Sprache | Kanal | Telegram |
|---------|-------|----------|
| 🇩🇪 Deutsch | TG_DE | [@MilitaerNews](https://t.me/militaernews) |
| 🇺🇸 Englisch | TG_EN | [@MilitaryNewsEN](https://t.me/MilitaryNewsEN) |
| 🇹🇷 Türkisch | TG_TR | [@MilitaryNewsTR](https://t.me/MilitaryNewsTR) |
| 🇮🇷 Persisch | TG_FA | [@MilitaryNewsFA](https://t.me/MilitaryNewsFA) |
| 🇷🇺 Russisch | TG_RU | [@MilitaryNewsRU](https://t.me/MilitaryNewsRU) |
| 🇧🇷 Portugiesisch | TG_PT | [@MilitaryNewsBR](https://t.me/MilitaryNewsBR) |
| 🇪🇸 Spanisch | TG_ES | [@MilitaryNewsES](https://t.me/MilitaryNewsES) |
| 🇫🇷 Französisch | TG_FR | [@MilitaryNewsFR](https://t.me/MilitaryNewsFR) |
| 🇮🇹 Italienisch | TG_IT | [@MilitaryNewsITA](https://t.me/MilitaryNewsITA) |
| 🇪🇬 Arabisch | TG_AR | [@MilitaryNewsAR](https://t.me/MilitaryNewsAR) |
| 🇮🇩 Indonesisch | TG_ID | [@MilitaryNewsIDN](https://t.me/MilitaryNewsIDN) |

## ⚡ Schnelleinstieg

### Als Redakteur
1. Öffnen Sie den [Posting Bot](https://t.me/militaernews_posting_bot)
2. Erstellen Sie einen neuen Post im deutschen Kanal
3. Der Bot übersetzt und verteilt den Inhalt automatisch auf alle Kanäle
4. Weitere Details finden Sie im [Redakteur-Handbuch](./handbuch.md)

### Als Entwickler
1. Klonen Sie das [Repository](https://github.com/militaernews/ptb-mn)
2. Folgen Sie der [Setup-Anleitung](../README.md#setup)
3. Konfigurieren Sie die Umgebungsvariablen (siehe `.env.example`)
4. Starten Sie den Bot mit `python bot/main.py`

## 🔧 Wichtige Features

- **Automatische Übersetzung** – Posts werden in 11 Sprachen übersetzt
- **Mediengruppen-Unterstützung** – Alben werden korrekt verarbeitet
- **Social Media Integration** – Automatisches Posten auf Twitter
- **Fehlerbehandlung** – Robuste Fallbacks bei Übersetzungsfehlern
- **Duplikat-Erkennung** – Verhindert doppelte Inhalte in der Suggest-Pipeline
- **Link-Rewriting** – Interne Links werden auf die entsprechenden Zielkanäle angepasst

## 📖 Weitere Ressourcen

- **[Telegram Limits](https://limits.tginfo.me/de-DE)** – Technische Limits der Telegram-API
- **[Character Counter](https://www.charactercountonline.com/)** – Zeichenzähler für Captions
- **[Chart Tool](https://chart-mn.vercel.app/)** – Erstellung von Charts
- **[Geo Tool](https://geo-mn.vercel.app/)** – Erstellung von Karten

## ❓ Hilfe und Support

- Fragen zur Redaktion? Siehe [Redakteur-Handbuch](./handbuch.md)
- Technische Probleme? Öffnen Sie ein [Issue](https://github.com/militaernews/ptb-mn/issues)
- Fehler melden? Kontaktieren Sie das Entwickler-Team

---

**Zuletzt aktualisiert:** März 2026
