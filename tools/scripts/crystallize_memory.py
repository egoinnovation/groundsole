#!/usr/bin/env python3
"""
Sliding-Chunk-Crystallizer für Groundsole
Extrahiert autonom aus aufgelaufenen Puffer-Turns (alle N Turns oder bei --flush)
harte Fakten, Beschlüsse, Beträge und Beziehungen und überführt sie direkt nach
LangMem (langmem_store.db) und Cognee (cognee_db).

Kosten-Schutz: Verwendet isolierte One-Shot-Calls an Gemini Flash Lite (~0,0003 €).
"""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

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

REPO_ROOT = find_workspace_root()
BUFFER_DB_PATH = os.path.join(REPO_ROOT, "00_MEMORY", "vectors", "memory_buffer.db")
HERMES_ENV_PATH = os.path.expanduser("~/.hermes/.env")

# Schnittstellen zu LangMem und Cognee importieren
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "scripts"))
try:
    from memory import add_memory
except ImportError:
    add_memory = None

try:
    from cognee_graph import add_edge
except ImportError:
    add_edge = None


def get_google_api_key() -> Optional[str]:
    """Liest den Google API Key aus der Umgebung oder aus ~/.hermes/.env."""
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()

    if os.path.exists(HERMES_ENV_PATH):
        try:
            with open(HERMES_ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        if k in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
                            val = v.strip().strip("'\"")
                            if val:
                                return val
        except Exception as exc:
            print(f"⚠️ Warnung: Konnte {HERMES_ENV_PATH} nicht lesen: {exc}", file=sys.stderr)

    return None


def init_crystallizer_schema(conn: sqlite3.Connection):
    """Stellt sicher, dass die Cursor-Tabelle in memory_buffer.db existiert."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crystallizer_state (
            filename TEXT PRIMARY KEY,
            last_chunk_id INTEGER NOT NULL,
            crystallized_turns_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def get_latest_session_filename(conn: sqlite3.Connection) -> Optional[str]:
    """Findet den Dateinamen der neuesten aktiven Harness-Session im Puffer."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT filename FROM chunks 
        WHERE filename LIKE 'harness_%' 
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    return row[0] if row else None


def fetch_pending_chunks(conn: sqlite3.Connection, filename: str) -> Tuple[List[Dict[str, Any]], int]:
    """Liest alle noch nicht kristallisierten Chunks einer Session aus."""
    cursor = conn.cursor()
    cursor.execute("SELECT last_chunk_id FROM crystallizer_state WHERE filename = ?", (filename,))
    row = cursor.fetchone()
    last_id = row[0] if row else 0

    cursor.execute("""
        SELECT id, speaker, turn_index, content 
        FROM chunks 
        WHERE filename = ? AND id > ?
        ORDER BY id ASC
    """, (filename, last_id))

    rows = cursor.fetchall()
    chunks = [
        {"id": r[0], "speaker": r[1], "turn_index": r[2], "content": r[3]}
        for r in rows
    ]
    return chunks, last_id


EXTRACTION_PROMPT = """Du bist der hochselektive Kognitions-Filter für das Groundsole Wissenssystem.
Deine oberste Pflicht ist SIGNAL ÜBER RAUSCHEN. LangMem und Cognee dürfen NIEMALS mit Kleinigkeiten, temporären Debugging-Details, Standard-Code oder trivialem Geplänkel gefüllt werden!

ANFORDERUNGEN:
1. MAXIMAL 1 BIS 3 FAKTEN für das GESAMTE Dokument! (Nur die absoluten Kronjuwelen: Richtungsentscheidungen, tragende Leitprinzipien oder echte Heureka-Durchbrüche).
2. Wenn das Gespräch lediglich routinemäßige Implementierung, CSS/UI-Polishing, Tippfehlerkorrekturen oder alltäglichen Arbeitsfortschritt behandelt: GIB LEERE LISTEN ZURÜCK ({"facts": [], "relations": []})!
3. Was zählt als Fakt / Erkenntnis?
   - Eine verbindliche Richtungsentscheidung des Nutzers (z.B. "Arbeitsweise X ab sofort verboten", "Tool Y ersetzt Tool Z").
   - Ein fundamental verstandener Systemmechanismus oder Kausalzusammenhang (z.B. Prefix-Caching, deterministische Kognition).
   - Ein Heureka-Moment mit starker Resonanz ("Krass!", "WOW!", "Das ist der Kern!").
4. Formuliere zeitlos, prägnant und als kausalen Lehrsatz. Keine Chat-Nacherzählungen ("Der Nutzer sagte...").
5. Maximal 1 bis 3 Relationen für Cognee (nur zwischen den Kernentitäten).

Antworte zwingend im folgenden JSON-Format:
{
  "facts": [
    {
      "namespace": "ERKENNTNIS | PRINZIP | SYSTEM | ENTSCHEIDUNG",
      "key": "praegnanter_schluessel",
      "content": "Kompakte, präzise Formulierung des Leitprinzips / Beschlusses."
    }
  ],
  "relations": [
    {
      "source": "Subjekt (z.B. Nutzer oder System)",
      "relationship": "VERBINDUNG (z.B. ERKENNT, BESCHLIESST)",
      "target": "Objekt (z.B. Deterministische_Kognition)",
      "source_type": "Person | Konzept | System",
      "target_type": "Erkenntnis | Beschluss | System"
    }
  ]
}
"""


def call_gemini_extraction(api_key: str, turns_text: str) -> Optional[Dict[str, Any]]:
    """Sendet den Textblock an Gemini Flash Lite via Standard-REST (ohne externe Libs)."""
    models = ["gemini-3.5-flash-lite", "gemini-2.5-flash"]
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": EXTRACTION_PROMPT + "\n\n### ZU ANALYSIERENDER GESPRÄCHSABSCHNITT:\n" + turns_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    data_bytes = json.dumps(payload).encode("utf-8")
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_json = parts[0]["text"]
                        return json.loads(raw_json)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            # Bei 404 nächstes Modell versuchen
            if e.code == 404:
                continue
            print(f"⚠️ Gemini API Fehler ({model}, HTTP {e.code}): {err_msg}", file=sys.stderr)
            break
        except Exception as exc:
            print(f"⚠️ Netzwerk-/Parsing-Fehler bei Modell {model}: {exc}", file=sys.stderr)
            break

    return None


def run_crystallization(
    threshold: int = 10,
    flush: bool = False,
    session_file: Optional[str] = None,
    dry_run: bool = False
) -> int:
    """
    Hauptfunktion: Prüft offene Chunks, ruft bei Bedarf die Extraktion auf
    und schreibt Fakten nach LangMem und Cognee.
    Gibt die Anzahl neu kristallisierter Fakten zurück.
    """
    if not os.path.exists(BUFFER_DB_PATH):
        print(f"ℹ️ Puffer-Datenbank existiert noch nicht: {BUFFER_DB_PATH}")
        return 0

    conn = sqlite3.connect(BUFFER_DB_PATH)
    try:
        init_crystallizer_schema(conn)

        if session_file:
            target_sessions = [session_file]
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT filename FROM chunks WHERE filename LIKE 'harness_%' ORDER BY id DESC")
            target_sessions = [r[0] for r in cursor.fetchall()]

        if not target_sessions:
            print("ℹ️ Keine aktive Harness-Session in memory_buffer.db gefunden.")
            return 0

        total_saved_facts = 0

        for target_session in target_sessions:
            pending_chunks, last_id = fetch_pending_chunks(conn, target_session)
            count = len(pending_chunks)

            if count == 0:
                continue

            # Wenn weniger als Threshold und kein Flush -> überspringen
            if count < threshold and not flush:
                continue

            api_key = get_google_api_key()
            if not api_key:
                print("❌ Fehler: Kein Google/Gemini API Key in der Umgebung oder ~/.hermes/.env gefunden.", file=sys.stderr)
                return total_saved_facts

            print(f"⚡ Kristallisiere {count} Turns aus {target_session}...")

            # Textblock für LLM aufbereiten
            text_lines = []
            max_chunk_id = last_id
            for c in pending_chunks:
                speaker_tag = "User" if c["speaker"] == "user" else "Assistant"
                text_lines.append(f"[{speaker_tag} - Turn {c['turn_index']}]:\n{c['content']}\n")
                if c["id"] > max_chunk_id:
                    max_chunk_id = c["id"]

            combined_text = "\n---\n".join(text_lines)

            # Extraktions-Call via REST
            extracted = call_gemini_extraction(api_key, combined_text)
            if not extracted:
                print("⚠️ Keine strukturierten Daten von Gemini erhalten.")
                continue

            facts = extracted.get("facts", [])
            relations = extracted.get("relations", [])

            print(f"💎 Extrahiert aus {target_session}: {len(facts)} Fakten, {len(relations)} Relationen.")

            if dry_run:
                print(f"\n[DRY RUN - {target_session}] Fakten:")
                print(json.dumps(facts, indent=2, ensure_ascii=False))
                print(f"\n[DRY RUN - {target_session}] Relationen:")
                print(json.dumps(relations, indent=2, ensure_ascii=False))
                total_saved_facts += len(facts)
                continue

            # In LangMem schreiben
            saved_facts = 0
            if add_memory and facts:
                for f in facts:
                    ns = f.get("namespace", "SYSTEM")
                    k = f.get("key", "notiz")
                    content = f.get("content", "")
                    if content:
                        try:
                            add_memory(namespace=ns, key=k, content=content)
                            saved_facts += 1
                        except Exception as exc:
                            print(f"⚠️ LangMem Speicherfehler: {exc}", file=sys.stderr)

            # In Cognee Wissensgraph schreiben
            saved_relations = 0
            if add_edge and relations:
                for r in relations:
                    src = r.get("source")
                    rel = r.get("relationship")
                    dst = r.get("target")
                    src_t = r.get("source_type", "Entity")
                    dst_t = r.get("target_type", "Entity")
                    if src and rel and dst:
                        try:
                            add_edge(source_label=src, relationship=rel, target_label=dst, source_type=src_t, target_type=dst_t)
                            saved_relations += 1
                        except Exception as exc:
                            print(f"⚠️ Cognee Speicherfehler: {exc}", file=sys.stderr)

            # Cursor aktualisieren
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO crystallizer_state (filename, last_chunk_id, crystallized_turns_count, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    last_chunk_id = excluded.last_chunk_id,
                    crystallized_turns_count = crystallized_turns_count + excluded.crystallized_turns_count,
                    updated_at = excluded.updated_at
            """, (target_session, max_chunk_id, count, now_iso))
            conn.commit()

            print(f"✅ Cursor für {target_session} aktualisiert (letzte Chunk-ID: {max_chunk_id}). LangMem: {saved_facts}, Cognee: {saved_relations}.")
            total_saved_facts += saved_facts

        return total_saved_facts

    finally:
        conn.close()


TRANSCRIPTS_STATE_FILE = os.path.join(REPO_ROOT, "00_MEMORY", "crystallized_transcripts.json")

def load_crystallized_transcripts() -> Dict[str, str]:
    if os.path.exists(TRANSCRIPTS_STATE_FILE):
        try:
            with open(TRANSCRIPTS_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_crystallized_transcripts(data: Dict[str, str]):
    try:
        with open(TRANSCRIPTS_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern von {TRANSCRIPTS_STATE_FILE}: {e}", file=sys.stderr)


def crystallize_transcript(transcript_path: str, dry_run: bool = False) -> int:
    """Extrahiert Fakten und Cognee-Kanten direkt aus einem archivierten Transkript."""
    if not os.path.exists(transcript_path):
        print(f"❌ Transkript existiert nicht: {transcript_path}")
        return 0

    api_key = get_google_api_key()
    if not api_key:
        print("❌ Kein API Key gefunden.", file=sys.stderr)
        return 0

    fname = os.path.basename(transcript_path)
    state = load_crystallized_transcripts()
    if fname in state and not dry_run:
        print(f"ℹ️ Transkript {fname} bereits kristallisiert am {state[fname]}.")
        return 0

    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Für Transkripte: Gesamtschau statt 20 Mikro-Splitter (max. 40.000 Zeichen Überblick)
    if len(content) > 40000:
        # Repräsentativer Querschnitt: Anfang (Kontext/Ziel) + Ende (Ergebnisse/Beschlüsse)
        analyzed_text = content[:20000] + "\n\n[... MITTELTEIL ZUR VERDICHTUNG ÜBERSPRUNGEN ...]\n\n" + content[-20000:]
    else:
        analyzed_text = content

    print(f"💎 Kristallisiere archiviertes Transkript: {fname} (Gesamtschau)...")

    total_facts = 0
    total_relations = 0

    extracted = call_gemini_extraction(api_key, analyzed_text)
    if not extracted:
        extracted = {"facts": [], "relations": []}

    facts = extracted.get("facts", [])[:3]
    relations = extracted.get("relations", [])[:3]

    if dry_run:
        print(f"[{fname}] Hochverdichtete Fakten ({len(facts)}): {json.dumps(facts, ensure_ascii=False, indent=2)}")
        print(f"[{fname}] Hochverdichtete Relationen ({len(relations)}): {json.dumps(relations, ensure_ascii=False, indent=2)}")
        return len(facts)

    if add_memory and facts:
        for fitem in facts:
            ns = fitem.get("namespace", "SYSTEM")
            k = fitem.get("key", "notiz")
            text = fitem.get("content", "")
            if text:
                try:
                    add_memory(namespace=ns, key=k, content=text)
                    total_facts += 1
                except Exception:
                    pass

    if add_edge and relations:
        for r in relations:
            src = r.get("source")
            rel = r.get("relationship")
            dst = r.get("target")
            if src and rel and dst:
                try:
                    add_edge(source_label=src, relationship=rel, target_label=dst)
                    total_relations += 1
                except Exception:
                    pass

    state[fname] = datetime.now().isoformat()
    save_crystallized_transcripts(state)
    print(f"✅ Transkript {fname} erfolgreich kristallisiert. LangMem: +{total_facts}, Cognee: +{total_relations}.")

    return total_facts


def scan_and_crystallize_transcripts(limit: int = 5, dry_run: bool = False) -> int:
    """Scannt 00_MEMORY/transcripts/ nach noch unkristallisierten Transkripten."""
    transcripts_dir = os.path.join(REPO_ROOT, "00_MEMORY", "transcripts")
    if not os.path.exists(transcripts_dir):
        return 0

    all_files = sorted(
        [os.path.join(transcripts_dir, f) for f in os.listdir(transcripts_dir) if f.endswith(".md")],
        reverse=True
    )

    state = load_crystallized_transcripts()
    pending = [f for f in all_files if os.path.basename(f) not in state][:limit]

    if not pending:
        print("✅ Alle archivierten Transkripte sind bereits in LangMem & Cognee kristallisiert.")
        return 0

    print(f"🔍 Gefunden: {len(pending)} unkristallisierte(s) Transkript(e). Starte Extraktion...")
    total = 0
    for p in pending:
        total += crystallize_transcript(p, dry_run=dry_run)
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sliding-Chunk- & Transkript-Crystallizer für LangMem & Cognee")
    parser.add_argument("--threshold", type=int, default=10, help="Mindestanzahl Turns vor Puffer-Extraktions-Call")
    parser.add_argument("--flush", action="store_true", help="Erzwingt Extraktion aller offenen Puffer-Turns")
    parser.add_argument("--session", type=str, default=None, help="Gezielte Puffer-Session (z. B. harness_hermes_123.md)")
    parser.add_argument("--transcript", type=str, default=None, help="Kristallisiert ein spezifisches archiviertes Transkript")
    parser.add_argument("--scan-transcripts", action="store_true", help="Scannt 00_MEMORY/transcripts/ nach neuen Sitzungen")
    parser.add_argument("--dry-run", action="store_true", help="Gibt die Extraktion nur auf stdout aus")
    args = parser.parse_args()

    if args.transcript:
        crystallize_transcript(args.transcript, dry_run=args.dry_run)
    elif args.scan_transcripts:
        scan_and_crystallize_transcripts(dry_run=args.dry_run)
    else:
        run_crystallization(
            threshold=args.threshold,
            flush=args.flush,
            session_file=args.session,
            dry_run=args.dry_run
        )
