# Terminjagd Cold Caller

KI-gestützter Cold-Call-Agent für terminjagd.de – automatische Terminvereinbarung via ElevenLabs Conversational AI + Twilio.

## Features

- **Freundliche deutsche Stimme** (Lisa) mit natürlichem Gesprächsfluss
- **Einwandbehandlung** für typische Kaltakquise-Einwände
- **Outbound Calls** über Twilio-Nummer
- **Batch-Calling** aus CSV-Kontaktlisten
- **Call-Logging** mit Gesprächsprotokollen

## Voraussetzungen

1. **ElevenLabs Account** mit API-Key → [elevenlabs.io](https://elevenlabs.io)
2. **Twilio Account** mit deutscher Telefonnummer → [twilio.com](https://www.twilio.com)
3. Python 3.9+

## Setup

```bash
# 1. Dependencies installieren
cd cold-caller
pip install -r requirements.txt

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
# → .env mit deinen API-Keys befüllen

# 3. Agent erstellen
python setup_agent.py

# 4. Twilio-Nummer importieren
python setup_agent.py --skip-agent --import-twilio
```

## Nutzung

```bash
# Verfügbare Stimmen anzeigen
python setup_agent.py --list-voices

# Testanruf starten
python call.py --test +491701234567

# Batch-Calls aus CSV
python call.py --csv kontakte.csv --delay 30

# Gesprächsstatus prüfen
python call.py --status <conversation_id>
```

## CSV-Format

```csv
name,telefon,firma
Max Mustermann,+491701234567,Musterfirma GmbH
```

Telefonnummern können mit `+49` oder `0` beginnen (werden automatisch normalisiert).

## Stimmen

| Key        | Name                  | Beschreibung                              |
|------------|-----------------------|-------------------------------------------|
| jessica    | Jessica Anne Bogart   | Empathisch und ausdrucksstark (Standard)  |
| hope       | Hope                  | Hell und positiv                          |
| eryn       | Eryn                  | Freundlich und nahbar                     |
| alexandra  | Alexandra             | Super realistisch, jung                   |

## Rechtliche Hinweise

- Beachte die **DSGVO** und das **UWG** (Gesetz gegen den unlauteren Wettbewerb)
- Cold Calls an Verbraucher (B2C) sind in DE **ohne Einwilligung verboten**
- B2B-Kaltakquise ist unter bestimmten Voraussetzungen zulässig (mutmaßliche Einwilligung)
- Informiere dich über die geltenden Vorschriften, bevor du den Agent einsetzt
