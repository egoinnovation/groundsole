#!/usr/bin/env python3
"""
Groundsole Hermes Session Exporter
Deterministischer Export einer Hermes-Agent-Session direkt aus ~/.hermes/state.db
in ein normiertes Markdown-Transkript nach 00_MEMORY/transcripts/.

Vorteile:
- 0 Token-Kosten (reine SQLite-Extraktion)
- 100 % verlustfrei und ohne Halluzinationen
- Filtert interne Tool-Dumps, JSON-Payloads und Telemetrie-Tags heraus
- Ersetzt sensible Tokens/Schlüssel durch Platzhalter
- Formatiert strikt nach dem Standard: H1 Titel gefolgt von H2 Sprecher
- Führt anschließend autonom die Memory-Kristallisation aus (Prinzip 14)
"""

import os
import re
import sys
import sqlite3
import argparse
from typing import Optional
from datetime import datetime, timezone, timedelta

LOCAL_TZ = timezone(timedelta(hours=2))  # Standard Lokalzeit (UTC+2)

def find_workspace_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    if os.path.exists(os.path.join(workspace_root, "00_MEMORY")):
        return workspace_root
    workspace_root_framework = os.path.dirname(workspace_root)
    if os.path.exists(os.path.join(workspace_root_framework, "00_MEMORY")):
        return workspace_root_framework
    if os.path.exists(os.path.join(os.getcwd(), "00_MEMORY")):
        return os.getcwd()
    return workspace_root

def clean_title(title: str) -> str:
    """Bereinigt den Session-Titel für Dateinamen."""
    if not title:
        return "Hermes Session"
    clean = re.sub(r'[\\/*?:"<>|]', "", title)
    return clean.strip()

def format_iso_timestamp(epoch_ts: float) -> str:
    """Wandelt Unix-Epoch in ISO-String mit Zeitzone um."""
    dt = datetime.fromtimestamp(epoch_ts, tz=LOCAL_TZ)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+02:00")

def get_latest_session(cursor: sqlite3.Cursor, session_id: Optional[str] = None):
    """Ermittelt die Session-Metadaten."""
    if session_id:
        cursor.execute(
            "SELECT id, started_at, last_activity_at, title FROM sessions WHERE id = ?",
            (session_id,)
        )
    else:
        cursor.execute(
            """
            SELECT id, started_at, last_activity_at, title
            FROM sessions
            WHERE COALESCE(archived, 0) = 0
            ORDER BY COALESCE(last_activity_at, started_at) DESC
            LIMIT 1
            """
        )
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Keine passende Session in state.db gefunden (ID: {session_id})")
    return row

def sanitize_content(text: str) -> str:
    """Bereinigt Telemetrie und maskiert Geheimnisse."""
    text = re.sub(r'<CONTEXT_SUMMARY>[\s\S]*?</CONTEXT_SUMMARY>', '', text)
    text = re.sub(r'<USER_REQUEST>[\s\S]*?</USER_REQUEST>', '', text)
    text = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>', '', text)
    text = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*?</USER_SETTINGS_CHANGE>', '', text)
    text = re.sub(r'<SYSTEM_MESSAGE>[\s\S]*?</SYSTEM_MESSAGE>', '', text)
    # Maskiere typische Secret-Patterns
    text = re.sub(r'ghp_[A-Za-z0-9_]{36,}', '[IN_SECRET_MANAGER_SAVED]', text)
    text = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[IN_SECRET_MANAGER_SAVED]', text)
    text = re.sub(r'sk-[A-Za-z0-9]{32,}', '[IN_SECRET_MANAGER_SAVED]', text)
    return text.strip()

def export_session(
    session_id: Optional[str] = None,
    custom_title: Optional[str] = None,
    output_path: Optional[str] = None,
    force: bool = False,
    user_speaker: str = "User"
):
    db_path = os.path.expanduser("~/.hermes/state.db")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Hermes state.db nicht gefunden unter {db_path}")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=10)
    cursor = conn.cursor()

    sess_id, started_at, last_activity, title = get_latest_session(cursor, session_id)
    
    start_dt = datetime.fromtimestamp(started_at, tz=LOCAL_TZ)
    date_prefix = start_dt.strftime("%Y-%m-%d")
    
    final_title = custom_title or title or f"Session_{sess_id}"
    final_title = clean_title(final_title)

    # Nachrichten abfragen (nur echte Dialogbeiträge von User und Assistant)
    cursor.execute(
        """
        SELECT role, content, timestamp
        FROM messages
        WHERE session_id = ? AND role IN ('user', 'assistant')
          AND content IS NOT NULL AND trim(content) != ''
        ORDER BY id ASC
        """,
        (sess_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        print(f"⚠️ Keine Dialog-Nachrichten für Session {sess_id} gefunden.")
        return None

    # Markdown aufbauen
    lines = []
    lines.append(f"# {date_prefix} - {final_title}\n")

    for role, content, ts in rows:
        iso_ts = format_iso_timestamp(ts)
        speaker = user_speaker if role == "user" else "Hermes"
        cleaned_content = sanitize_content(content)

        if not cleaned_content:
            continue

        lines.append(f"## {speaker} ({iso_ts})\n")
        lines.append(f"{cleaned_content}\n")

    markdown_text = "\n".join(lines)

    # Zielverzeichnis bestimmen
    repo_root = find_workspace_root()
    if not output_path:
        filename = f"{date_prefix} - {final_title}.md"
        output_path = os.path.join(repo_root, "00_MEMORY", "transcripts", filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path) and not force:
        timestamp_suffix = datetime.now().strftime("%H%M%S")
        output_path = output_path.replace(".md", f"_{timestamp_suffix}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    # Rest-Turns & Transkript deterministisch in LangMem & Cognee kristallisieren (Prinzip 14)
    sys.path.insert(0, os.path.join(repo_root, "tools", "scripts"))
    sys.path.insert(0, os.path.join(repo_root, "scripts"))
    try:
        from crystallize_memory import crystallize_transcript
        crystallize_transcript(output_path)
    except Exception as exc:
        print(f"⚠️ Kristallisierung übersprungen: {exc}")

    line_count = len(markdown_text.splitlines())
    byte_count = os.path.getsize(output_path)
    print(f"✅ Hermes Session erfolgreich exportiert:")
    print(f"   Session-ID: {sess_id}")
    print(f"   Zielpfad:   {output_path}")
    print(f"   Statistik:  {len(rows)} Turns, {line_count} Zeilen, {byte_count:,} Bytes")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exportiert Hermes Session nach 00_MEMORY/transcripts/")
    parser.add_argument("--session-id", help="Spezifische Hermes Session-ID")
    parser.add_argument("--title", help="Manueller Titel für das Transkript")
    parser.add_argument("--output", help="Individueller Ausgabepfad")
    parser.add_argument("--speaker", default="User", help="Name des menschlichen Nutzers (Standard: User)")
    parser.add_argument("--force", action="store_true", help="Vorhandene Datei überschreiben")
    args = parser.parse_args()

    export_session(
        session_id=args.session_id,
        custom_title=args.title,
        output_path=args.output,
        force=args.force,
        user_speaker=args.speaker
    )
