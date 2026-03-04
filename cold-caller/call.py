#!/usr/bin/env python3
"""
Outbound Cold Calls über ElevenLabs + Twilio.

Nutzung:
  python call.py --test +491701234567          # Einzelner Testanruf
  python call.py --csv kontakte.csv            # Batch-Calls aus CSV
  python call.py --csv kontakte.csv --delay 30 # 30s Pause zwischen Anrufen
  python call.py --status <conversation_id>    # Status eines Anrufs prüfen

CSV-Format (kontakte.csv):
  name,telefon,firma
  Max Mustermann,+491701234567,Musterfirma GmbH
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.elevenlabs.io/v1"


def get_headers():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Fehler: ELEVENLABS_API_KEY nicht gesetzt.")
        sys.exit(1)
    return {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }


def get_required_env():
    """Prüft und gibt die benötigten Umgebungsvariablen zurück."""
    agent_id = os.getenv("ELEVENLABS_AGENT_ID")
    phone_id = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")

    if not agent_id:
        print("Fehler: ELEVENLABS_AGENT_ID nicht gesetzt.")
        print("Führe zuerst 'python setup_agent.py' aus.")
        sys.exit(1)
    if not phone_id:
        print("Fehler: ELEVENLABS_PHONE_NUMBER_ID nicht gesetzt.")
        print("Führe 'python setup_agent.py --import-twilio' aus.")
        sys.exit(1)

    return agent_id, phone_id


def make_call(
    to_number: str,
    agent_id: str,
    phone_number_id: str,
    contact_name: str = None,
    company: str = None,
) -> dict:
    """Startet einen einzelnen Outbound-Call über ElevenLabs + Twilio."""

    payload = {
        "agent_id": agent_id,
        "agent_phone_number_id": phone_number_id,
        "to_number": to_number,
    }

    # Optionale Kontextdaten für den Agenten
    if contact_name or company:
        custom_data = {}
        if contact_name:
            custom_data["contact_name"] = contact_name
        if company:
            custom_data["company"] = company
        payload["conversation_initiation_client_data"] = {
            "custom_llm_extra_body": {
                "contact_info": custom_data,
            }
        }

    print(f"  Rufe an: {to_number}", end="")
    if contact_name:
        print(f" ({contact_name})", end="")
    if company:
        print(f" @ {company}", end="")
    print(" ...")

    resp = requests.post(
        f"{API_BASE}/convai/twilio/outbound-call",
        headers=get_headers(),
        json=payload,
    )

    if resp.status_code != 200:
        print(f"  FEHLER: {resp.status_code} – {resp.text}")
        return {"success": False, "error": resp.text}

    data = resp.json()
    if data.get("success"):
        conv_id = data.get("conversation_id", "N/A")
        call_sid = data.get("callSid", "N/A")
        print(f"  Anruf gestartet! Conversation: {conv_id} | CallSid: {call_sid}")
    else:
        print(f"  Anruf fehlgeschlagen: {data.get('message', 'Unbekannter Fehler')}")

    return data


def get_call_status(conversation_id: str) -> dict:
    """Ruft den Status eines Gesprächs ab."""
    resp = requests.get(
        f"{API_BASE}/convai/conversations/{conversation_id}",
        headers=get_headers(),
    )

    if resp.status_code != 200:
        print(f"Fehler: {resp.status_code} – {resp.text}")
        return {}

    data = resp.json()
    print(f"Conversation: {conversation_id}")
    print(f"  Status:    {data.get('status', 'N/A')}")
    print(f"  Dauer:     {data.get('duration_seconds', 'N/A')}s")

    # Transcript anzeigen falls vorhanden
    transcript = data.get("transcript", [])
    if transcript:
        print(f"  Transcript ({len(transcript)} Nachrichten):")
        for msg in transcript:
            role = msg.get("role", "?")
            text = msg.get("message", "")
            print(f"    [{role}] {text}")

    return data


def batch_call(csv_path: str, agent_id: str, phone_number_id: str, delay: int = 15):
    """Führt Batch-Calls aus einer CSV-Datei durch."""

    if not os.path.exists(csv_path):
        print(f"Fehler: CSV-Datei '{csv_path}' nicht gefunden.")
        sys.exit(1)

    contacts = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(row)

    if not contacts:
        print("Keine Kontakte in der CSV-Datei gefunden.")
        sys.exit(1)

    print(f"Starte Batch-Calling: {len(contacts)} Kontakte")
    print(f"Pause zwischen Anrufen: {delay}s")
    print(f"Geschätzte Dauer: ~{len(contacts) * delay // 60} Minuten")
    print("=" * 60)

    results = []
    for i, contact in enumerate(contacts, 1):
        telefon = contact.get("telefon", "").strip()
        name = contact.get("name", "").strip()
        firma = contact.get("firma", "").strip()

        if not telefon:
            print(f"  [{i}/{len(contacts)}] ÜBERSPRUNGEN – keine Telefonnummer")
            continue

        # Nummer normalisieren
        if not telefon.startswith("+"):
            if telefon.startswith("0"):
                telefon = "+49" + telefon[1:]
            else:
                telefon = "+49" + telefon

        print(f"\n[{i}/{len(contacts)}]", end=" ")
        result = make_call(
            to_number=telefon,
            agent_id=agent_id,
            phone_number_id=phone_number_id,
            contact_name=name,
            company=firma,
        )
        result["contact"] = contact
        results.append(result)

        # Pause zwischen Anrufen (nicht nach dem letzten)
        if i < len(contacts):
            print(f"  Warte {delay}s...")
            time.sleep(delay)

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    print(f"  Gesamt:      {len(results)}")
    print(f"  Erfolgreich: {successful}")
    print(f"  Fehlgeschlagen: {failed}")

    # Ergebnisse in Log-Datei schreiben
    log_name = f"call_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path = os.path.join(os.path.dirname(__file__), log_name)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  Log gespeichert: {log_name}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="ElevenLabs + Twilio Outbound Cold Calls für Terminjagd"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--test",
        metavar="NUMMER",
        help="Einzelnen Testanruf an eine Nummer starten (z.B. +491701234567)",
    )
    group.add_argument(
        "--csv",
        metavar="DATEI",
        help="Batch-Calls aus CSV-Datei starten",
    )
    group.add_argument(
        "--status",
        metavar="CONVERSATION_ID",
        help="Status eines Anrufs prüfen",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=15,
        help="Sekunden Pause zwischen Batch-Calls (Standard: 15)",
    )
    args = parser.parse_args()

    if args.status:
        get_call_status(args.status)
        return

    agent_id, phone_number_id = get_required_env()

    if args.test:
        make_call(args.test, agent_id, phone_number_id)
    elif args.csv:
        batch_call(args.csv, agent_id, phone_number_id, delay=args.delay)


if __name__ == "__main__":
    main()
