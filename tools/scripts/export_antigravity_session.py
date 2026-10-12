#!/usr/bin/env python3
"""
Groundsole Antigravity Session Exporter
Deterministischer Export einer Antigravity-Session direkt aus transcript_full.jsonl
in ein normiertes Markdown-Transkript nach 00_MEMORY/transcripts/.

Vorteile:
- 0 Token-Kosten (reine JSONL-Extraktion)
- 100 % verlustfrei und ohne Halluzinationen
- Filtert interne Tool-Dumps und Telemetrie-Tags heraus
- Maskiert sensible Schlüssel und Tokens
- Formatiert strikt nach dem Standard: H1 Titel gefolgt von H2 Sprecher
- Führt anschließend autonom die Memory-Kristallisation aus (Prinzip 14)
"""

import json
import re
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta

LOCAL_TZ = timezone(timedelta(hours=2))

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

def format_iso_timestamp(iso_str):
    if not iso_str:
        return datetime.now(LOCAL_TZ).isoformat(timespec="seconds")
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_local = dt.astimezone(LOCAL_TZ)
        return dt_local.isoformat(timespec="seconds")
    except Exception:
        return iso_str

def sanitize_user_text(text):
    text = re.sub(r'<USER_REQUEST>\s*', '', text)
    text = re.sub(r'</USER_REQUEST>\s*', '', text)
    text = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>', '', text)
    text = re.sub(r'<CONTEXT_SUMMARY>[\s\S]*?</CONTEXT_SUMMARY>', '', text)
    text = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*?</USER_SETTINGS_CHANGE>', '', text)
    text = re.sub(r'<SYSTEM_MESSAGE>[\s\S]*?</SYSTEM_MESSAGE>', '', text)
    text = re.sub(r'ghp_[A-Za-z0-9_]{36,}', '[IN_SECRET_MANAGER_SAVED]', text)
    text = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[IN_SECRET_MANAGER_SAVED]', text)
    text = re.sub(r'sk-[A-Za-z0-9]{32,}', '[IN_SECRET_MANAGER_SAVED]', text)
    return text.strip()

def sanitize_assistant_text(text):
    text = re.sub(r'<CONTEXT_SUMMARY>[\s\S]*?</CONTEXT_SUMMARY>', '', text)
    text = re.sub(r'ghp_[A-Za-z0-9_]{36,}', '[IN_SECRET_MANAGER_SAVED]', text)
    text = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[IN_SECRET_MANAGER_SAVED]', text)
    text = re.sub(r'sk-[A-Za-z0-9]{32,}', '[IN_SECRET_MANAGER_SAVED]', text)
    return text.strip()

def export_antigravity_session(transcript_path, output_transcript_path=None, title=None, user_speaker="User"):
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript nicht gefunden: {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        steps = [json.loads(line) for line in f]

    user_indices = [idx for idx, s in enumerate(steps) if s.get("type") == "USER_INPUT"]
    if not user_indices:
        raise ValueError("Keine USER_INPUT Einträge im Transkript gefunden.")

    today_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    final_title = title or f"{today_str} - Antigravity Session"

    out = []
    out.append(f"# {final_title}\n")

    for i, u_idx in enumerate(user_indices):
        u_step = steps[u_idx]
        next_u_idx = user_indices[i+1] if i + 1 < len(user_indices) else len(steps)

        u_content = sanitize_user_text(u_step.get("content", ""))
        u_ts = format_iso_timestamp(u_step.get("created_at"))

        # Finde letzte Planner-Antwort dieses Turns
        a_step = None
        for j in range(next_u_idx - 1, u_idx, -1):
            s = steps[j]
            if s.get("type") == "PLANNER_RESPONSE" and s.get("content"):
                if not s.get("tool_calls"):
                    a_step = s
                    break
                elif not a_step:
                    a_step = s

        out.append(f"## {user_speaker} ({u_ts})\n\n{u_content}\n")

        if a_step:
            a_content = sanitize_assistant_text(a_step.get("content", ""))
            a_ts = format_iso_timestamp(a_step.get("created_at"))
            if a_content:
                out.append(f"## Antigravity ({a_ts})\n\n{a_content}\n")

    markdown_text = "\n".join(out).strip() + "\n"

    repo_root = find_workspace_root()
    if not output_transcript_path:
        filename = f"{final_title}.md"
        output_transcript_path = os.path.join(repo_root, "00_MEMORY", "transcripts", filename)

    os.makedirs(os.path.dirname(output_transcript_path), exist_ok=True)
    with open(output_transcript_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    # Post-Archival Kristallisation anstoßen (Prinzip 14)
    sys.path.insert(0, os.path.join(repo_root, "tools", "scripts"))
    sys.path.insert(0, os.path.join(repo_root, "scripts"))
    try:
        from crystallize_memory import crystallize_transcript
        crystallize_transcript(output_transcript_path)
    except Exception as exc:
        print(f"⚠️ Kristallisierung übersprungen: {exc}")

    print(f"✅ Transkript erfolgreich exportiert nach: {output_transcript_path}")
    return output_transcript_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exportiert Antigravity transcript_full.jsonl nach 00_MEMORY/transcripts/")
    parser.add_argument("transcript_path", help="Pfad zu transcript_full.jsonl")
    parser.add_argument("--output", help="Optionaler Zielpfad für das Markdown-Transkript")
    parser.add_argument("--title", help="Titel des Transkripts")
    parser.add_argument("--speaker", default="User", help="Name des Nutzers (Standard: User)")
    args = parser.parse_args()

    export_antigravity_session(
        args.transcript_path,
        output_transcript_path=args.output,
        title=args.title,
        user_speaker=args.speaker
    )
