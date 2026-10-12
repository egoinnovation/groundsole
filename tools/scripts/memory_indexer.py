#!/usr/bin/env python3
"""
Groundsole Vector Indexer (FastEmbed / Jina ONNX)
Increments and indexes session transcripts into 00_MEMORY/vectors/active.db.
Supports incremental hashing so only new or modified transcripts are processed.
"""

import os
import re
import sys
import glob
import sqlite3
import hashlib
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np

def find_workspace_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(os.path.dirname(script_dir))
    if os.path.exists(os.path.join(workspace_root, "00_MEMORY")):
        return workspace_root
    if os.path.exists(os.path.join(os.getcwd(), "00_MEMORY")):
        return os.getcwd()
    return workspace_root

WORKSPACE_DIR = find_workspace_root()
RAW_CHATS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "transcripts")
VECTORS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "vectors")
# The vectors directory is created by init_db() on the first real write.
# Creating it at import time would litter the resolved workspace on every
# invocation, including `--help`.
DB_PATH = os.path.join(VECTORS_DIR, "memory_active.db")
BUFFER_DB_PATH = os.path.join(VECTORS_DIR, "memory_buffer.db")

MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"

def init_db(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            filename TEXT PRIMARY KEY,
            file_hash TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            title TEXT,
            date_str TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            speaker TEXT,
            timestamp_str TEXT,
            header_context TEXT,
            content TEXT NOT NULL,
            token_count INTEGER,
            content_hash TEXT,
            embedding BLOB,
            FOREIGN KEY (filename) REFERENCES indexed_files(filename) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_speaker ON chunks(speaker)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash)")
    conn.commit()
    conn.close()

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_transcript(filepath: str) -> Tuple[Dict, List[Dict]]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    fname = os.path.basename(filepath)
    title_match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else fname.replace(".md", "")
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    date_str = date_match.group(1) if date_match else "unknown"

    meta = {"filename": fname, "title": title, "date_str": date_str}

    h2_pattern = re.compile(r"^##\s+([^\n]+)", re.MULTILINE)
    sections = []
    matches = list(h2_pattern.finditer(content))

    for i, m in enumerate(matches):
        h2_text = m.group(1).strip()
        start_pos = m.end()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(content)
        sec_body = content[start_pos:end_pos].strip()

        speaker = "Assistant" if any(w in h2_text.lower() for w in ["assistant", "gemini", "antigravity", "claude", "hermes", "ai", "bot"]) else "User"
        ts_match = re.search(r"\(([^)]+)\)", h2_text)
        ts_str = ts_match.group(1) if ts_match else ""

        sections.append({
            "speaker": speaker,
            "timestamp_str": ts_str,
            "header": h2_text,
            "content": sec_body
        })

    # Chunking
    chunks = []
    for s in sections:
        body = s["content"]
        if not body:
            continue
        max_chunk_chars = 1500
        paragraphs = body.split("\n\n")
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            if current_len + len(p_strip) > max_chunk_chars and current_chunk:
                chunks.append({
                    "speaker": s["speaker"],
                    "timestamp_str": s["timestamp_str"],
                    "header_context": s["header"],
                    "content": "\n\n".join(current_chunk),
                    "token_count": int(current_len / 4)
                })
                current_chunk = [p_strip]
                current_len = len(p_strip)
            else:
                current_chunk.append(p_strip)
                current_len += len(p_strip)

        if current_chunk:
            chunks.append({
                "speaker": s["speaker"],
                "timestamp_str": s["timestamp_str"],
                "header_context": s["header"],
                "content": "\n\n".join(current_chunk),
                "token_count": int(current_len / 4)
            })

    return meta, chunks

def index_file(filepath: str, embedding_model, db_path: str = DB_PATH) -> int:
    init_db(db_path)
    meta, chunks = parse_transcript(filepath)
    if not chunks:
        return 0

    texts_to_embed = [c["content"] for c in chunks]
    embeddings = list(embedding_model.embed(texts_to_embed))

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM chunks WHERE filename=?", (meta["filename"],))
    c.execute("DELETE FROM indexed_files WHERE filename=?", (meta["filename"],))

    fhash = get_file_hash(filepath)
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO indexed_files (filename, file_hash, indexed_at, chunk_count, title, date_str) VALUES (?, ?, ?, ?, ?, ?)",
        (meta["filename"], fhash, now, len(chunks), meta["title"], meta["date_str"])
    )

    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        emb_blob = np.array(emb, dtype=np.float32).tobytes()
        chash = hashlib.md5(chunk["content"].encode("utf-8")).hexdigest()
        c.execute("""
            INSERT OR IGNORE INTO chunks (filename, chunk_index, speaker, timestamp_str, header_context, content, token_count, content_hash, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (meta["filename"], idx, chunk["speaker"], chunk["timestamp_str"], chunk["header_context"], chunk["content"], chunk["token_count"], chash, emb_blob))

    conn.commit()
    conn.close()
    return len(chunks)

# ── Harness self-detection & volatile session buffer ─────────────────────────
# Architecture references:
#   01_CORE_PRINCIPLES_AND_SSOT.md §6  Dynamic Harness Self-Detection & Adaptive Grounding
#   02_MEMORY_HIERARCHY.md             Tier 1: Volatile Session Buffer (memory_buffer.db)
#
# No environment path is hardcoded into the scanning logic. Each harness exposes
# its open chat turns through its own collector:
#   None            -> harness not present on this machine
#   list of turns   -> harness present (possibly with zero usable turns)
# A turn is a neutral dict: {"speaker": "user"|"assistant", "content",
#                            "date_str", "session_id"}
# Adding a harness = write one collector + add one HARNESS_ADAPTERS entry.

HARNESS_WARNING_FILE = os.path.join(WORKSPACE_DIR, "00_MEMORY", "HARNESS_SCAN_WARNING.md")

MIN_TURN_CHARS = 35
MAX_CHUNK_CHARS = 1500


def clean_harness_text(content: str) -> str:
    """Strip harness-injected envelopes and metadata tags from a raw turn."""
    if not content:
        return ""
    content = re.sub(r"<USER_REQUEST>\s*", "", content)
    content = re.sub(r"\s*</USER_REQUEST>", "", content)
    content = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", content, flags=re.DOTALL)
    content = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", content, flags=re.DOTALL)
    content = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", content, flags=re.DOTALL)
    # Out-of-band envelopes keep their payload, only the wrapper is dropped
    content = re.sub(r"\[OUT-OF-BAND USER MESSAGE[^\]]*\]\s*", "", content)
    content = re.sub(r"\s*\[/OUT-OF-BAND USER MESSAGE\]", "", content)
    return content.strip()


def _split_paragraphs(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """Split an oversized turn at paragraph boundaries so no detail is lost."""
    if len(text) <= max_chars:
        return [text] if len(text) >= MIN_TURN_CHARS else []

    pieces: List[str] = []
    current: List[str] = []
    current_len = 0

    for paragraph in text.split("\n\n"):
        p = paragraph.strip()
        if not p:
            continue
        if current_len + len(p) > max_chars and current:
            joined = "\n\n".join(current)
            if len(joined) >= MIN_TURN_CHARS:
                pieces.append(joined)
            current, current_len = [p], len(p)
        else:
            current.append(p)
            current_len += len(p)

    if current:
        joined = "\n\n".join(current)
        if len(joined) >= MIN_TURN_CHARS:
            pieces.append(joined)
    return pieces


def _epoch_to_date(value) -> str:
    """Normalise a timestamp (epoch number or ISO text) to an ISO date."""
    if value is None:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return (str(value)[:10] or datetime.now().strftime("%Y-%m-%d"))


def _short_session_id(session_id) -> str:
    """
    Stable, collision-free short id for a session.
    A plain [:8] slice would be the date part of a timestamped session id and
    would collapse every session started on the same day onto one filename.
    """
    s = str(session_id)
    return s.rsplit("_", 1)[-1] if "_" in s else s[:8]


def collect_antigravity_chunks() -> Optional[List[Dict]]:
    """Open chats from the Google Antigravity brain (~/.gemini/antigravity/brain)."""
    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    if not os.path.isdir(brain_dir):
        return None

    turns: List[Dict] = []
    conv_ids = [d for d in os.listdir(brain_dir)
                if os.path.isdir(os.path.join(brain_dir, d)) and len(d) > 20]

    for cid in conv_ids:
        conv_dir = os.path.join(brain_dir, cid)
        t_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(t_path):
            t_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript_full.jsonl")
        if not os.path.exists(t_path):
            continue

        with open(t_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except Exception:
                    continue

                source = entry.get("source")
                msg_type = entry.get("type")
                content = entry.get("content")

                speaker = None
                if source == "USER_EXPLICIT" and msg_type == "USER_INPUT":
                    speaker = "user"
                elif source == "MODEL" and msg_type == "PLANNER_RESPONSE" and content:
                    speaker = "assistant"

                if not (speaker and content):
                    continue

                cleaned = clean_harness_text(content)
                if len(cleaned) < MIN_TURN_CHARS:
                    continue

                turns.append({
                    "speaker": speaker,
                    "content": cleaned,
                    "date_str": datetime.now().strftime("%Y-%m-%d"),
                    "session_id": cid,
                })
    return turns


def collect_hermes_chunks(limit_sessions: int = 20) -> Optional[List[Dict]]:
    """Open chats from the Hermes Agent session store (~/.hermes/state.db)."""
    state_db = os.path.expanduser("~/.hermes/state.db")
    if not os.path.exists(state_db):
        return None

    turns: List[Dict] = []
    conn = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True, timeout=10)
    try:
        cursor = conn.cursor()
        sessions = cursor.execute(
            """
            SELECT id, COALESCE(last_activity_at, started_at), title
            FROM sessions
            WHERE COALESCE(archived, 0) = 0
            ORDER BY COALESCE(last_activity_at, started_at) DESC
            LIMIT ?
            """,
            (limit_sessions,),
        ).fetchall()

        for session_id, last_activity, _title in sessions:
            date_str = _epoch_to_date(last_activity)
            rows = cursor.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ? AND role IN ('user', 'assistant')
                ORDER BY id
                """,
                (session_id,),
            ).fetchall()

            for role, content in rows:
                if not content:
                    continue
                # Pure harness notices carry no dialogue
                if content.lstrip().startswith("[System:"):
                    continue
                cleaned = clean_harness_text(content)
                if len(cleaned) < MIN_TURN_CHARS:
                    continue
                turns.append({
                    "speaker": role,
                    "content": cleaned,
                    "date_str": date_str,
                    "session_id": str(session_id),
                })
    finally:
        conn.close()
    return turns


def harness_warning_write(missing: List[str]) -> None:
    """Leave an actionable notice when no known harness environment was found."""
    lines = [
        "# ⚠️ Harness Scanner: no known environment found",
        "",
        f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**Created by:** `tools/scripts/memory_indexer.py --scan-harness`",
        "",
        "## What happened",
        "",
        "The scanner found **none** of the known harness environments on this machine,",
        "so **no** open chat turns were mirrored into `memory_buffer.db`.",
        "",
        "## What was looked for",
        "",
        "| Harness | Expected location |",
        "|---|---|",
    ]
    for harness_name, location, _ in HARNESS_ADAPTERS:
        lines.append(f"| {harness_name} | `{location}` |")
    lines += [
        "",
        "## What to do (agent task)",
        "",
        "1. Determine which harness actually runs here and **where** it stores its sessions.",
        "2. Add a collector for it in `tools/scripts/memory_indexer.py` and register it in",
        "   `HARNESS_ADAPTERS` (pattern: `collect_antigravity_chunks`, `collect_hermes_chunks`).",
        "3. Re-run `--scan-harness` and confirm that chunks arrive.",
        "4. This file is removed automatically once a scan succeeds again.",
        "",
        "## Environments not found during the last run",
        "",
    ]
    for item in missing:
        lines.append(f"- {item}")
    try:
        os.makedirs(os.path.dirname(HARNESS_WARNING_FILE), exist_ok=True)
        with open(HARNESS_WARNING_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError as exc:
        print(f"⚠️  Could not write the scanner notice: {exc}")


def harness_warning_clear() -> None:
    """Remove a stale scanner notice once scanning works again."""
    if os.path.exists(HARNESS_WARNING_FILE):
        try:
            os.remove(HARNESS_WARNING_FILE)
        except OSError:
            pass


# Registered adapters: (name, expected location, collector).
# Another harness? Add an entry here – detection, reporting and the notice
# follow automatically.
HARNESS_ADAPTERS = [
    ("antigravity", "~/.gemini/antigravity/brain", collect_antigravity_chunks),
    ("hermes", "~/.hermes/state.db", collect_hermes_chunks),
]


def scan_active_harness(db_path: str = BUFFER_DB_PATH):
    """
    Mirror the open chat turns of every detected harness into the volatile
    session buffer (Tier 1). Only unseen content is embedded – existing chunks
    are recognised by their content hash.
    """
    init_db(db_path)
    start_time = datetime.now()

    candidate_chunks: List[Dict] = []
    active_harnesses: List[Tuple[str, int]] = []
    missing_harnesses: List[str] = []

    for harness_name, location, collector in HARNESS_ADAPTERS:
        try:
            turns = collector()
        except Exception as exc:
            print(f"⚠️  Harness '{harness_name}' could not be read: {exc}")
            missing_harnesses.append(f"{harness_name} ({location}) – read error: {exc}")
            continue

        if turns is None:
            missing_harnesses.append(f"{harness_name} ({location}) – not present")
            continue

        active_harnesses.append((harness_name, len(turns)))

        sessions: Dict[str, List[Dict]] = {}
        for turn in turns:
            sessions.setdefault(turn["session_id"], []).append(turn)

        for session_id, session_turns in sessions.items():
            short_id = _short_session_id(session_id)
            fname = f"harness_{harness_name}_{short_id}.md"
            title = f"Active {harness_name} session {short_id}"
            for turn in session_turns:
                for piece in _split_paragraphs(turn["content"]):
                    candidate_chunks.append({
                        "filename": fname,
                        "title": title,
                        "speaker": "Assistant" if turn["speaker"] == "assistant" else "User",
                        "date_str": turn["date_str"],
                        "content": piece,
                    })

    if not active_harnesses:
        print("⚠️  No known harness environment found.")
        harness_warning_write(missing_harnesses)
        print(f"   → Notice written to {HARNESS_WARNING_FILE}")
        return

    harness_warning_clear()
    print("🔎 Harness detected (" +
          ", ".join(f"{n}: {c} turns" for n, c in active_harnesses) + ")")

    if not candidate_chunks:
        print("ℹ️  No usable text turns in the active harness sessions.")
        return

    for chunk in candidate_chunks:
        chunk["content_hash"] = hashlib.md5(chunk["content"].encode("utf-8")).hexdigest()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    all_hashes = [c["content_hash"] for c in candidate_chunks]
    existing_hashes = set()
    batch_size = 500
    for i in range(0, len(all_hashes), batch_size):
        part = all_hashes[i:i + batch_size]
        marks = ",".join("?" for _ in part)
        cursor.execute(f"SELECT content_hash FROM chunks WHERE content_hash IN ({marks})", part)
        existing_hashes.update(row[0] for row in cursor.fetchall())

    new_chunks: List[Dict] = []
    seen_hashes = set()
    for chunk in candidate_chunks:
        h = chunk["content_hash"]
        if h in existing_hashes or h in seen_hashes:
            continue
        seen_hashes.add(h)
        new_chunks.append(chunk)

    check_seconds = (datetime.now() - start_time).total_seconds()
    if not new_chunks:
        print(f"✅ All {len(all_hashes)} sections already present in the buffer "
              f"(check: {check_seconds:.2f}s).")
        conn.close()
        return

    print(f"⚡ {len(new_chunks)} new chunks detected ({check_seconds:.2f}s). Vectorising delta...")

    from fastembed import TextEmbedding
    model = TextEmbedding(model_name=MODEL_NAME)

    texts_to_embed = [
        f"[{c['title']} | Speaker: {c['speaker']} | Date: {c['date_str']}]\n{c['content']}"
        for c in new_chunks
    ]
    embeddings = list(model.embed(texts_to_embed, batch_size=64))

    for chunk, emb in zip(new_chunks, embeddings):
        emb_blob = np.array(emb, dtype=np.float32).tobytes()
        cursor.execute("""
            INSERT OR IGNORE INTO chunks
            (filename, chunk_index, speaker, timestamp_str, header_context,
             content, token_count, content_hash, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk["filename"], 0, chunk["speaker"], chunk["date_str"], chunk["title"],
            chunk["content"], int(len(chunk["content"]) / 4), chunk["content_hash"], emb_blob
        ))

    conn.commit()
    conn.close()

    total_seconds = (datetime.now() - start_time).total_seconds()
    print(f"🎉 Done in {total_seconds:.2f}s! {len(new_chunks)} chunks mirrored into the "
          f"volatile session buffer.")


def main():
    parser = argparse.ArgumentParser(description="Groundsole Vector Indexer")
    parser.add_argument("--file", help="Specific transcript file to index")
    parser.add_argument("--all", action="store_true", help="Scan and index all unindexed transcripts")
    parser.add_argument("--scan-harness", action="store_true",
                        help="Mirror open chat turns from every detected harness into memory_buffer.db")
    args = parser.parse_args()

    if args.scan_harness:
        scan_active_harness()
        return

    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("❌ fastembed is not installed. Please install it in your venv: pip install fastembed numpy")
        sys.exit(1)

    print(f"Loading embedding model: {MODEL_NAME}...")
    model = TextEmbedding(model_name=MODEL_NAME)

    if args.file:
        fpath = os.path.abspath(args.file)
        print(f"Indexing single file: {fpath}")
        count = index_file(fpath, model)
        print(f"✅ Indexed {count} chunks for {os.path.basename(fpath)}")
    else:
        files = sorted(glob.glob(os.path.join(RAW_CHATS_DIR, "*.md")))
        print(f"Found {len(files)} transcripts in {RAW_CHATS_DIR}")
        init_db(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        indexed = {row[0]: row[1] for row in c.execute("SELECT filename, file_hash FROM indexed_files").fetchall()}
        conn.close()

        updated_count = 0
        for f in files:
            fname = os.path.basename(f)
            curr_hash = get_file_hash(f)
            if fname not in indexed or indexed[fname] != curr_hash:
                print(f"Processing: {fname}")
                c_count = index_file(f, model)
                updated_count += 1

        print(f"✅ Processing complete. {updated_count} files indexed/updated.")

if __name__ == "__main__":
    main()
