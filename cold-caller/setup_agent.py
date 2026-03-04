#!/usr/bin/env python3
"""
ElevenLabs Cold-Call Agent einrichten.

Erstellt den Agenten über die ElevenLabs API und importiert
optional eine Twilio-Nummer für Outbound-Calls.

Voraussetzungen:
  pip install elevenlabs python-dotenv requests

Nutzung:
  python setup_agent.py                     # Agent erstellen
  python setup_agent.py --voice hope        # Mit bestimmter Stimme
  python setup_agent.py --import-twilio     # + Twilio-Nummer importieren
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

from agent_prompt import AGENT_CONFIG, DEFAULT_VOICE, RECOMMENDED_VOICES

load_dotenv()

API_BASE = "https://api.elevenlabs.io/v1"


def get_headers():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Fehler: ELEVENLABS_API_KEY ist nicht gesetzt.")
        print("Bitte in .env eintragen oder als Umgebungsvariable setzen.")
        sys.exit(1)
    return {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }


def create_agent(voice_key: str = DEFAULT_VOICE) -> dict:
    """Erstellt den Cold-Call-Agenten bei ElevenLabs."""

    voice = RECOMMENDED_VOICES.get(voice_key)
    if not voice:
        print(f"Fehler: Stimme '{voice_key}' nicht gefunden.")
        print(f"Verfügbar: {', '.join(RECOMMENDED_VOICES.keys())}")
        sys.exit(1)

    config = json.loads(json.dumps(AGENT_CONFIG))  # deep copy
    config["conversation_config"]["tts"]["voice_id"] = voice["voice_id"]

    print(f"Erstelle Agent '{config['name']}' mit Stimme '{voice['name']}'...")

    resp = requests.post(
        f"{API_BASE}/convai/agents/create",
        headers=get_headers(),
        json=config,
    )

    if resp.status_code != 200:
        print(f"Fehler beim Erstellen des Agenten: {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    data = resp.json()
    agent_id = data.get("agent_id")

    print(f"Agent erfolgreich erstellt!")
    print(f"  Agent-ID:  {agent_id}")
    print(f"  Stimme:    {voice['name']} ({voice['voice_id']})")
    print(f"  Sprache:   Deutsch (de)")
    print()

    # Agent-ID in .env speichern
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    _update_env(env_path, "ELEVENLABS_AGENT_ID", agent_id)
    print(f"  Agent-ID in .env gespeichert.")

    return data


def import_twilio_number() -> dict:
    """Importiert die Twilio-Nummer in ElevenLabs für Outbound-Calls."""

    twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    agent_id = os.getenv("ELEVENLABS_AGENT_ID")

    missing = []
    if not twilio_phone:
        missing.append("TWILIO_PHONE_NUMBER")
    if not twilio_sid:
        missing.append("TWILIO_ACCOUNT_SID")
    if not twilio_token:
        missing.append("TWILIO_AUTH_TOKEN")
    if not agent_id:
        missing.append("ELEVENLABS_AGENT_ID")

    if missing:
        print(f"Fehler: Folgende Umgebungsvariablen fehlen: {', '.join(missing)}")
        sys.exit(1)

    print(f"Importiere Twilio-Nummer {twilio_phone} in ElevenLabs...")

    # Twilio-Nummer bei ElevenLabs importieren
    resp = requests.post(
        f"{API_BASE}/convai/phone-numbers/create",
        headers=get_headers(),
        json={
            "phone_number": twilio_phone,
            "provider": "twilio",
            "label": "Terminjagd Cold Caller",
            "twilio_config": {
                "account_sid": twilio_sid,
                "auth_token": twilio_token,
            },
            "agent_id": agent_id,
        },
    )

    if resp.status_code not in (200, 201):
        print(f"Fehler beim Importieren der Nummer: {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    data = resp.json()
    phone_number_id = data.get("phone_number_id")

    print(f"Twilio-Nummer erfolgreich importiert!")
    print(f"  Phone-Number-ID: {phone_number_id}")
    print(f"  Agent-ID:        {agent_id}")

    # Phone-Number-ID in .env speichern
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    _update_env(env_path, "ELEVENLABS_PHONE_NUMBER_ID", phone_number_id)
    print(f"  Phone-Number-ID in .env gespeichert.")

    return data


def list_voices():
    """Zeigt empfohlene Stimmen an."""
    print("Empfohlene Stimmen für den Cold-Call-Agenten:")
    print()
    for key, voice in RECOMMENDED_VOICES.items():
        marker = " ← Standard" if key == DEFAULT_VOICE else ""
        print(f"  {key:12s}  {voice['name']:25s}  {voice['description']}{marker}")
    print()


def _update_env(env_path: str, key: str, value: str):
    """Aktualisiert oder ergänzt einen Schlüssel in der .env-Datei."""
    lines = []
    found = False

    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)


def main():
    parser = argparse.ArgumentParser(
        description="ElevenLabs Cold-Call Agent Setup für Terminjagd"
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Stimme wählen (Standard: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--import-twilio",
        action="store_true",
        help="Twilio-Nummer in ElevenLabs importieren",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Verfügbare Stimmen anzeigen",
    )
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Agent-Erstellung überspringen (nur Twilio importieren)",
    )
    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if not args.skip_agent:
        create_agent(args.voice)

    if args.import_twilio:
        # .env neu laden, falls Agent-ID gerade geschrieben wurde
        load_dotenv(override=True)
        import_twilio_number()

    print()
    print("Nächste Schritte:")
    print("  1. Teste den Agenten: python call.py --test +49XXXXXXXXXX")
    print("  2. Batch-Calls:       python call.py --csv kontakte.csv")
    print()


if __name__ == "__main__":
    main()
