#!/usr/bin/env python3
"""
SIDDHANTA Vector Indexer & Pattern Extractor
Erstellt einen semantischen Vektor-Index über alle SIDDHANTA-Chats mit strikter
Sprecher-Trennung (Emanuel vs. KI), Metadaten-Extraktion und inkrementellem Caching.
"""

import os
import re
import sys
import glob
import sqlite3
import hashlib
import json
import argparse
import warnings
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np

# FastEmbed ONNX Runtime FP16/FP32 Precision Upgrade Hinweis stummschalten
warnings.filterwarnings("ignore", message=r".*fp16.*fp32.*")

# Pfad-Definitionen (dynamisch relativ zum Skriptort)
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CHATS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "transcripts")
VECTORS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "emanuel_vectors")
os.makedirs(VECTORS_DIR, exist_ok=True)
DB_PATH = os.path.join(VECTORS_DIR, "emanuel_memory_active.db")
BUFFER_DB_PATH = os.path.join(VECTORS_DIR, "memory_buffer.db")

# Warnhinweis-Datei: wird hinterlegt, wenn keine bekannte Harness-Umgebung gefunden wird
HARNESS_WARNING_FILE = os.path.join(WORKSPACE_DIR, "00_MEMORY", "HARNESS_SCAN_WARNING.md")

# Standard-Modell: jinaai/jina-embeddings-v2-base-de (SOTA für Deutsch, 8192 Tokens Kontext, 50ms Latenz)
MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"

def init_db(db_path: str = DB_PATH):
    """Initialisiert das SQLite-Datenbankschema für Vektoren und Metadaten."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabelle für verarbeitete Dateien (für inkrementelle Updates)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            filename TEXT PRIMARY KEY,
            file_hash TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            teil_nr TEXT,
            title TEXT,
            date_str TEXT
        )
    """)
    
    # Tabelle für Chunks & Vektoren
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            teil_nr TEXT,
            title TEXT,
            date_str TEXT,
            speaker TEXT NOT NULL, -- 'user' (Emanuel), 'assistant' (KI), oder 'document'
            turn_index REAL NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            embedding BLOB -- float32 raw bytes
        )
    """)
    
    # Indizes für schnelles Filtern nach Sprecher, Datei oder Teil
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_speaker ON chunks(speaker)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_teil ON chunks(teil_nr)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_filename ON chunks(filename)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash)")
    
    conn.commit()
    conn.close()

def get_file_hash(file_path: str) -> str:
    """Berechnet SHA256-Hash einer Datei zur Delta-Erkennung."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_header_metadata(lines: List[str], filename: str) -> Tuple[str, str, str]:
    """Extrahiert Teil-Nummer, Titel und Datum aus Dateinamen und Kopfzeilen."""
    # 1. Teil-Nummer und Titel aus Dateiname
    match_fn = re.search(r"Teil\s+([0-9]+[a-z]?)\s*-\s*(.*)\.md", filename, re.IGNORECASE)
    if match_fn:
        teil_nr = match_fn.group(1).strip()
        title = match_fn.group(2).strip()
    else:
        teil_nr = ""
        title = filename.replace(".md", "")

    # 2. Datum aus den ersten 15 Zeilen suchen
    date_str = ""
    for line in lines[:15]:
        m_date = re.search(r"(?:Datum|Stand|Zuletzt aktualisiert|Chat gespeichert am)[:\s]+([0-9]{1,2}[\.\-\/][0-9]{1,2}[\.\-\/][0-9]{2,4}|[0-9]{4}[\.\-\/][0-9]{1,2}[\.\-\/][0-9]{1,2})", line, re.IGNORECASE)
        if m_date:
            date_str = m_date.group(1).strip()
            break
            
    return teil_nr, title, date_str

def parse_chat_turns(file_path: str) -> List[Dict]:
    """
    Parst eine Chat-Datei in Sinnabschnitte mit exakter Sprecher-Zuordnung (Emanuel vs. KI).
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        
    filename = os.path.basename(file_path)
    teil_nr, title, date_str = parse_header_metadata(lines, filename)
    
    # Reguläre Ausdrücke für Sprecherwechsel
    re_user = re.compile(r"^(?:##|###|\*\*)\s*(?:EMANUEL|USER|PROMPT|Emanuel\s*\(Prompt\)|EMANUEL\s*\(PROMPT\))[:\s\*\)]*", re.IGNORECASE)
    re_assistant = re.compile(r"^(?:##|###|\*\*)\s*(?:CHATGPT|CLAUDE|GEMINI|ANTIGRAVITY|HERMES|GROK|KIMI|DEEPSEEK|ASSISTANT|KI|ANTWORT|ChatGPT\s*\(Antwort\)|Antigravity\s*\(Antwort\)|Claude\s*\(Antwort\)|Hermes\s*\(Antwort\))[:\s\*\)]*", re.IGNORECASE)
    
    chunks = []
    current_speaker = None
    current_lines = []
    turn_start_line = 1
    turn_index = 0
    
    for i, line in enumerate(lines, start=1):
        line_clean = line.strip()
        
        # Prüfe ob neue User-Sektion beginnt
        if re_user.match(line_clean):
            if current_speaker and current_lines:
                content = "".join(current_lines).strip()
                if content:
                    chunks.append({
                        "filename": filename,
                        "teil_nr": teil_nr,
                        "title": title,
                        "date_str": date_str,
                        "speaker": current_speaker,
                        "turn_index": float(turn_index),
                        "start_line": turn_start_line,
                        "end_line": i - 1,
                        "content": content
                    })
                    turn_index += 1
            current_speaker = "user"
            current_lines = []
            turn_start_line = i
            continue
            
        # Prüfe ob neue Assistant-Sektion beginnt
        elif re_assistant.match(line_clean):
            if current_speaker and current_lines:
                content = "".join(current_lines).strip()
                if content:
                    chunks.append({
                        "filename": filename,
                        "teil_nr": teil_nr,
                        "title": title,
                        "date_str": date_str,
                        "speaker": current_speaker,
                        "turn_index": float(turn_index),
                        "start_line": turn_start_line,
                        "end_line": i - 1,
                        "content": content
                    })
                    turn_index += 1
            current_speaker = "assistant"
            current_lines = []
            turn_start_line = i
            continue
            
        current_lines.append(line)
        
    # Letzten Block abschließen
    if current_lines:
        content = "".join(current_lines).strip()
        if content:
            chunks.append({
                "filename": filename,
                "teil_nr": teil_nr,
                "title": title,
                "date_str": date_str,
                "speaker": current_speaker if current_speaker else "document",
                "turn_index": float(turn_index),
                "start_line": turn_start_line,
                "end_line": len(lines),
                "content": content
            })
            
    return chunks

def split_large_chunks(raw_chunks: List[Dict], max_chars: int = 1500, min_chars: int = 35) -> List[Dict]:
    """
    Teilt übergroße Redebeiträge an logischen Absatzgrenzen auf, damit kein Vektordetail verloren geht.
    """
    refined_chunks = []
    for chunk in raw_chunks:
        text = chunk["content"]
        if len(text) <= max_chars:
            if len(text) >= min_chars:
                refined_chunks.append(chunk)
            continue
            
        # Teile an Absätzen (Doppel-Zeilenumbruch)
        paragraphs = text.split("\n\n")
        curr_sub_text = []
        curr_len = 0
        sub_index = 0
        
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            if curr_len + len(p_strip) > max_chars and curr_sub_text:
                sub_content = "\n\n".join(curr_sub_text).strip()
                if len(sub_content) >= min_chars:
                    new_chunk = dict(chunk)
                    new_chunk["content"] = sub_content
                    new_chunk["turn_index"] = round(chunk["turn_index"] + (sub_index / 100.0), 3)
                    refined_chunks.append(new_chunk)
                    sub_index += 1
                curr_sub_text = [p_strip]
                curr_len = len(p_strip)
            else:
                curr_sub_text.append(p_strip)
                curr_len += len(p_strip)
                
        if curr_sub_text:
            sub_content = "\n\n".join(curr_sub_text).strip()
            if len(sub_content) >= min_chars:
                new_chunk = dict(chunk)
                new_chunk["content"] = sub_content
                new_chunk["turn_index"] = round(chunk["turn_index"] + (sub_index / 100.0), 3)
                refined_chunks.append(new_chunk)
                
    return refined_chunks

def index_corpus(raw_dir: str = RAW_CHATS_DIR, db_path: str = DB_PATH, limit: Optional[int] = None, force: bool = False, model_name: str = MODEL_NAME, target_file: Optional[str] = None):
    """
    Hauptroutine für die Vektorisierung.
    Parst Dateien, filtert bereits indizierte (Delta-Check), berechnet Embeddings und speichert Chunks.
    """
    init_db(db_path)
    
    # Import FastEmbed
    from fastembed import TextEmbedding
    print(f"📦 Lade Embedding-Modell: {model_name}...", flush=True)
    embedding_model = TextEmbedding(model_name=model_name)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Bereits indizierte Dateien auslesen (inkl. versiegelter Archiv-Shards)
    cursor.execute("SELECT filename, file_hash FROM indexed_files")
    already_indexed = dict(cursor.fetchall())
    
    # Versiegelte Archiv-Shards im selben Verzeichnis berücksichtigen (Log-Structured Sharding)
    vector_dir = os.path.dirname(db_path)
    if os.path.exists(vector_dir):
        archive_dbs = glob.glob(os.path.join(vector_dir, "*_archive_*.db"))
        for arc_db in archive_dbs:
            try:
                arc_conn = sqlite3.connect(arc_db)
                arc_cur = arc_conn.cursor()
                arc_cur.execute("SELECT filename, file_hash FROM indexed_files")
                for fn, fh in arc_cur.fetchall():
                    if fn not in already_indexed:
                        already_indexed[fn] = fh
                arc_conn.close()
            except Exception:
                pass

    # Exklusive ISN-Betriebs-Transkripte (Pfad B: isn_vectors.db) aus der Haupt-DB ausschließen
    isn_db_path = os.path.join(WORKSPACE_DIR, "00_MEMORY", "isn_vectors.db")
    isn_exclusive_files = set()
    if os.path.basename(db_path) == "emanuel_memory_active.db" and os.path.exists(isn_db_path):
        try:
            isn_conn = sqlite3.connect(isn_db_path)
            isn_cur = isn_conn.cursor()
            isn_cur.execute("SELECT filename FROM indexed_files")
            isn_exclusive_files = set(r[0] for r in isn_cur.fetchall())
            isn_conn.close()
        except Exception:
            pass
    
    # Alle Markdown-Dateien finden oder Einzelfall bearbeiten
    if target_file:
        if not os.path.isabs(target_file):
            if os.path.exists(target_file):
                target_file = os.path.abspath(target_file)
            else:
                target_file = os.path.join(raw_dir, target_file)
        if not os.path.exists(target_file):
            print(f"❌ Datei nicht gefunden: {target_file}", flush=True)
            return
        all_files = [target_file]
        print(f"🎯 Gezielte Einzeldatei-Indizierung: {os.path.basename(target_file)}", flush=True)
    else:
        all_files = sorted(glob.glob(os.path.join(raw_dir, "*.md")))
        if not all_files:
            print(f"❌ Keine Markdown-Dateien in {raw_dir} gefunden!", flush=True)
            return
        print(f"🔍 Gefundene Dateien in 00_MEMORY/transcripts: {len(all_files)}", flush=True)
    if limit:
        all_files = all_files[:limit]
        print(f"🎯 Begrenzt auf Testlauf: {len(all_files)} Dateien")
        
    files_to_process = []
    for fpath in all_files:
        fname = os.path.basename(fpath)
        fhash = get_file_hash(fpath)
        if fname in isn_exclusive_files:
            continue
        if not force and fname in already_indexed and already_indexed[fname] == fhash:
            continue
        files_to_process.append((fpath, fname, fhash))
        
    print(f"⚡ Zu verarbeitende Dateien (Delta / Neu): {len(files_to_process)}")
    if not files_to_process:
        print("✅ Alle Dateien sind bereits aktuell indiziert.")
        conn.close()
        return

    total_chunks_indexed = 0
    start_time = datetime.now()
    
    for idx, (fpath, fname, fhash) in enumerate(files_to_process, 1):
        # 1. Parsen und Chunken
        raw_chunks = parse_chat_turns(fpath)
        chunks = split_large_chunks(raw_chunks)
        
        # ── STRIKTER VORAB-GATEKEEPER FÜR ISN-VEKTORDATENBANK ─────────────────
        is_isn_db = ("isn" in os.path.basename(db_path).lower())
        if is_isn_db:
            from isn_privacy_guard import audit_chunks
            violations = audit_chunks(chunks, fname)
            if violations:
                print(f"\n🛑 [STOPP: ISN PRIVACY VIOLATION] Datei '{fname}' enthält {len(violations)} verbotene Chunks!", flush=True)
                print(f"   In die ISN-Vektordatenbank dürfen NIEMALS private Daten von Emanuel, keine Reflexionen über ISN/Reinhard und keine Kundendaten gelangen.", flush=True)
                for v in violations[:3]:
                    c_idx = v["chunk_idx"]
                    sl = v["start_line"]
                    el = v["end_line"]
                    spk = v["speaker"]
                    viol = v["violations"]
                    v_types = []
                    if viol["private"]: v_types.append(f"Privat: {viol['private']}")
                    if viol["reflection"]: v_types.append(f"Reflexion: {viol['reflection']}")
                    if viol["clients"]: v_types.append(f"Kunden: {viol['clients']}")
                    print(f"   • Chunk #{c_idx} (L{sl}-{el}, {spk}): {', '.join(v_types)}", flush=True)
                    print(f"     \"{v['snippet'][:120]}...\"", flush=True)
                if len(violations) > 3:
                    print(f"   • ... und {len(violations) - 3} weitere Fundstellen.", flush=True)
                print(f"\n🚫 Indizierung in {os.path.basename(db_path)} abgebrochen. Es wurden KEINE Daten geschrieben.\n", flush=True)
                conn.close()
                sys.exit(1)
        # ──────────────────────────────────────────────────────────────────────
        
        if not chunks:
            cursor.execute("DELETE FROM chunks WHERE filename = ?", (fname,))
            cursor.execute("DELETE FROM indexed_files WHERE filename = ?", (fname,))
            conn.commit()
            print(f"  [{idx}/{len(files_to_process)}] ⚠️ Keine Chunks in {fname}")
            continue
            
        # 2. Bestehende Chunks dieser Datei aus DB abfragen (Content-Hash -> Cache)
        cursor.execute("SELECT content_hash FROM chunks WHERE filename = ?", (fname,))
        existing_hashes = set(row[0] for row in cursor.fetchall())
        
        # 3. Chunks abgleichen & Hashes setzen
        current_chunk_hashes = set()
        chunks_to_embed = []
        texts_to_embed = []
        
        for c in chunks:
            chash = hashlib.md5(c["content"].encode("utf-8")).hexdigest()
            c["content_hash"] = chash
            current_chunk_hashes.add(chash)
            
            if chash not in existing_hashes or force:
                chunks_to_embed.append(c)
                texts_to_embed.append(
                    f"[{c['teil_nr']} | {c['title']} | Sprecher: {c['speaker']} | Datum: {c['date_str']}]\n{c['content']}"
                )
        
        # 4. Obsolete Chunks entfernen (die nicht mehr im Dokument vorkommen)
        if existing_hashes and not force:
            obsolete_hashes = existing_hashes - current_chunk_hashes
            if obsolete_hashes:
                obs_list = list(obsolete_hashes)
                for b_i in range(0, len(obs_list), 500):
                    batch_obs = obs_list[b_i:b_i+500]
                    placeholders = ",".join("?" * len(batch_obs))
                    cursor.execute(f"DELETE FROM chunks WHERE filename = ? AND content_hash IN ({placeholders})", [fname] + batch_obs)
        elif force:
            cursor.execute("DELETE FROM chunks WHERE filename = ?", (fname,))
            
        # 5. Nur geänderte / neue Chunks via FastEmbed einbetten
        if chunks_to_embed:
            embeddings_gen = embedding_model.embed(texts_to_embed, batch_size=64)
            embeddings_list = list(embeddings_gen)
            
            for c, emb in zip(chunks_to_embed, embeddings_list):
                emb_blob = np.array(emb, dtype=np.float32).tobytes()
                cursor.execute("""
                    INSERT OR REPLACE INTO chunks (
                        filename, teil_nr, title, date_str, speaker,
                        turn_index, start_line, end_line, content,
                        content_hash, embedding
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["filename"], c["teil_nr"], c["title"], c["date_str"], c["speaker"],
                    c["turn_index"], c["start_line"], c["end_line"], c["content"],
                    c["content_hash"], emb_blob
                ))
            total_chunks_indexed += len(chunks_to_embed)
            
        # 6. Metadaten (turn_index, start_line, end_line) bestehender Chunks synchronisieren
        for c in chunks:
            if c["content_hash"] in existing_hashes and not force:
                cursor.execute("""
                    UPDATE chunks SET turn_index = ?, start_line = ?, end_line = ?
                    WHERE filename = ? AND content_hash = ?
                """, (c["turn_index"], c["start_line"], c["end_line"], fname, c["content_hash"]))
                
        # 7. Dateistatus aktualisieren
        teil_nr = chunks[0]["teil_nr"]
        title = chunks[0]["title"]
        date_str = chunks[0]["date_str"]
        indexed_at = datetime.now().isoformat()
        
        cursor.execute("DELETE FROM indexed_files WHERE filename = ?", (fname,))
        cursor.execute("""
            INSERT INTO indexed_files (
                filename, file_hash, indexed_at, chunk_count,
                teil_nr, title, date_str
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fname, fhash, indexed_at, len(chunks), teil_nr, title, date_str))
        
        conn.commit()
        user_chunks = sum(1 for c in chunks if c["speaker"] == "user")
        print(f"  [{idx}/{len(files_to_process)}] ✅ {fname[:40]}... ({len(chunks)} Chunks | {len(chunks_to_embed)} neu eingebettet | {user_chunks} Emanuel-Impulse)", flush=True)
        
    conn.close()
    duration = (datetime.now() - start_time).total_seconds()
    print(f"\n🎉 Fertig in {duration:.1f}s! Gesamt neu indiziert: {total_chunks_indexed} Chunks across {len(files_to_process)} Dateien.", flush=True)

def clean_harness_text(content: str) -> str:
    """Entfernt technische System-Tags und XML-Metadaten aus Chat-Logs."""
    if not content:
        return ""
    content = re.sub(r"<USER_REQUEST>\s*", "", content)
    content = re.sub(r"\s*</USER_REQUEST>", "", content)
    content = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", content, flags=re.DOTALL)
    content = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", content, flags=re.DOTALL)
    content = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", content, flags=re.DOTALL)
    # Hermes-spezifische Hüllen: Markierungen entfernen, Inhalt behalten
    content = re.sub(r"\[OUT-OF-BAND USER MESSAGE[^\]]*\]\s*", "", content)
    content = re.sub(r"\s*\[/OUT-OF-BAND USER MESSAGE\]", "", content)
    return content.strip()


# ── Harness-Adapter ───────────────────────────────────────────────────────────
# Jede Harness liefert ihre offenen Chat-Turns über einen eigenen Adapter.
# Rückgabe: None = Harness auf diesem Rechner nicht vorhanden.
#           Liste (ggf. leer) = Harness vorhanden.
# Neue Harness? Adapter ergänzen und unten in HARNESS_ADAPTERS registrieren.

def _epoch_to_date(value) -> str:
    """Wandelt einen Zeitstempel (Epoch-Zahl oder ISO-Text) in ein ISO-Datum um."""
    if value is None:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return (str(value)[:10] or datetime.now().strftime("%Y-%m-%d"))


def collect_antigravity_chunks() -> Optional[List[Dict]]:
    """Liest offene Chats aus dem Antigravity-Brain (~/.gemini/antigravity/brain)."""
    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    if not os.path.isdir(brain_dir):
        return None

    chunks: List[Dict] = []
    conv_ids = [d for d in os.listdir(brain_dir)
                if os.path.isdir(os.path.join(brain_dir, d)) and len(d) > 20]

    for cid in conv_ids:
        conv_dir = os.path.join(brain_dir, cid)
        t_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(t_path):
            t_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript_full.jsonl")
        if not os.path.exists(t_path):
            continue

        turn_idx = 0
        with open(t_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                except Exception:
                    continue
                source = d.get("source")
                msg_type = d.get("type")
                content = d.get("content")

                speaker = None
                if source == "USER_EXPLICIT" and msg_type == "USER_INPUT":
                    speaker = "user"
                elif source == "MODEL" and msg_type == "PLANNER_RESPONSE" and content:
                    speaker = "assistant"

                if speaker and content:
                    cleaned = clean_harness_text(content)
                    if len(cleaned) >= 35:
                        chunks.append({
                            "filename": f"harness_antigravity_{cid[:8]}.md",
                            "teil_nr": "active",
                            "title": f"Active Session {cid[:8]}",
                            "date_str": datetime.now().strftime("%Y-%m-%d"),
                            "speaker": speaker,
                            "turn_index": float(turn_idx),
                            "start_line": 0,
                            "end_line": 0,
                            "content": cleaned,
                        })
                        turn_idx += 1
    return chunks


def collect_hermes_chunks(limit_sessions: int = 20) -> Optional[List[Dict]]:
    """
    Liest die Turns kürzlicher Hermes-Sessions nativ aus der SQLite-Datenbank
    (~/.hermes/state.db, Tabellen `sessions` und `messages`).
    """
    state_db = os.path.expanduser("~/.hermes/state.db")
    if not os.path.exists(state_db):
        return None

    chunks: List[Dict] = []
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

        for session_id, last_activity, title in sessions:
            date_str = _epoch_to_date(last_activity)
            # Eindeutige Kurz-ID: letztes Segment der Session-ID (z. B. "22d637").
            # Ein reiner [:8]-Abschnitt wäre das Datum und würde alle Sessions
            # desselben Tages auf denselben Dateinamen zusammenfallen lassen.
            sess = str(session_id)
            short_id = sess.rsplit("_", 1)[-1] if "_" in sess else sess[:8]
            rows = cursor.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ? AND role IN ('user', 'assistant')
                ORDER BY id
                """,
                (session_id,),
            ).fetchall()

            turn_idx = 0
            for role, content in rows:
                if not content:
                    continue
                # Reine System-Notizen tragen keinen Gesprächsinhalt
                if content.lstrip().startswith("[System:"):
                    continue
                cleaned = clean_harness_text(content)
                if len(cleaned) < 35:
                    continue
                chunks.append({
                    "filename": f"harness_hermes_{short_id}.md",
                    "teil_nr": "active",
                    "title": (title or f"Active Session {short_id}"),
                    "date_str": date_str,
                    "speaker": role,
                    "turn_index": float(turn_idx),
                    "start_line": 0,
                    "end_line": 0,
                    "content": cleaned,
                })
                turn_idx += 1
    finally:
        conn.close()
    return chunks


def harness_warning_write(missing: List[str]) -> None:
    """Hinterlegt einen deutlichen Hinweis, wenn keine bekannte Harness gefunden wurde."""
    lines = [
        "# ⚠️ Harness-Scanner: keine bekannte Umgebung gefunden",
        "",
        f"**Erzeugt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**Erzeugt von:** `scripts/memory_indexer.py --scan-harness`",
        "",
        "## Was passiert ist",
        "",
        "Der Puffer-Scanner hat auf diesem Rechner **keine** der bekannten Harness-Umgebungen",
        "gefunden. Es wurden daher **keine** neuen Gespräche in `memory_buffer.db` gesichert.",
        "",
        "## Wonach gesucht wurde",
        "",
        "| Harness | Erwarteter Ort |",
        "|---|---|",
    ]
    for harness_name, location, _ in HARNESS_ADAPTERS:
        lines.append(f"| {harness_name} | `{location}` |")
    lines += [
        "",
        "## Was zu tun ist (Auftrag an die KI)",
        "",
        "1. Feststellen, welche Harness hier tatsächlich läuft und **wo** sie ihre Gespräche ablegt.",
        "2. In `scripts/memory_indexer.py` einen passenden Adapter ergänzen und in",
        "   `HARNESS_ADAPTERS` registrieren (Muster: `collect_antigravity_chunks`,",
        "   `collect_hermes_chunks`).",
        "3. `--scan-harness` erneut ausführen und prüfen, dass Chunks ankommen.",
        "4. Diese Datei wird bei erfolgreichem Scan automatisch wieder entfernt.",
        "",
        "## Nicht gefundene Umgebungen beim letzten Lauf",
        "",
    ]
    for item in missing:
        lines.append(f"- {item}")
    try:
        os.makedirs(os.path.dirname(HARNESS_WARNING_FILE), exist_ok=True)
        with open(HARNESS_WARNING_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError as exc:
        print(f"⚠️ Warnhinweis konnte nicht geschrieben werden: {exc}")


def harness_warning_clear() -> None:
    """Entfernt einen veralteten Warnhinweis, sobald wieder gescannt werden kann."""
    if os.path.exists(HARNESS_WARNING_FILE):
        try:
            os.remove(HARNESS_WARNING_FILE)
        except OSError:
            pass


# Registrierte Harness-Adapter: (Name, Fundort, Sammelfunktion).
# Weitere Harness? Hier eintragen – Detektion und Warnhinweis folgen automatisch.
HARNESS_ADAPTERS = [
    ("antigravity", "~/.gemini/antigravity/brain", collect_antigravity_chunks),
    ("hermes", "~/.hermes/state.db", collect_hermes_chunks),
]


def scan_active_harness(db_path: str = BUFFER_DB_PATH, model_name: str = MODEL_NAME):
    """
    Scannt offene Chats in der aktiven Harness (z. B. Antigravity brain/) und indiziert
    nur neue, ungespeicherte Turns direkt in den flüchtigen Vektor-Puffer (memory_buffer.db).
    """
    init_db(db_path)
    start_time = datetime.now()

    # 1. Alle registrierten Harness-Adapter abfragen (multi-harness-fähig)
    candidate_chunks: List[Dict] = []
    active_harnesses: List[Tuple[str, int]] = []
    missing_harnesses: List[str] = []

    for harness_name, location, collector in HARNESS_ADAPTERS:
        try:
            harness_chunks = collector()
        except Exception as exc:
            print(f"⚠️ Harness '{harness_name}' konnte nicht gelesen werden: {exc}", flush=True)
            missing_harnesses.append(f"{harness_name} ({location}) – Lesefehler: {exc}")
            continue

        if harness_chunks is None:
            missing_harnesses.append(f"{harness_name} ({location}) – Ort nicht vorhanden")
            continue

        active_harnesses.append((harness_name, len(harness_chunks)))
        candidate_chunks.extend(harness_chunks)

    # 2. Keine bekannte Harness gefunden -> deutlicher Hinweis für die KI
    if not active_harnesses:
        print("⚠️ Keine bekannte Harness-Umgebung gefunden.")
        harness_warning_write(missing_harnesses)
        print(f"   → Hinweis hinterlegt: {HARNESS_WARNING_FILE}")
        return

    harness_warning_clear()
    found_desc = ", ".join(f"{name}: {count} Turns" for name, count in active_harnesses)
    print(f"🔎 Harness erkannt ({found_desc})")
                        
    if not candidate_chunks:
        print("ℹ️ Keine Text-Nachrichten in aktiven Harness-Sessions gefunden.")
        return
        
    refined = split_large_chunks(candidate_chunks)
    
    # 2. Hashes berechnen und mit DB abgleichen (Vorab-Check ohne FastEmbed!)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Automatische Bereinigung geschlossener / gelöschter Sessions (Garbage Collection)
    active_filenames = set(c["filename"] for c in refined)
    cursor.execute("SELECT DISTINCT filename FROM chunks WHERE filename LIKE 'harness_%'")
    existing_harness_files = [r[0] for r in cursor.fetchall()]
    deleted_files = [f for f in existing_harness_files if f not in active_filenames]
    if deleted_files:
        for df in deleted_files:
            cursor.execute("DELETE FROM chunks WHERE filename = ?", (df,))
            cursor.execute("DELETE FROM indexed_files WHERE filename = ?", (df,))
        conn.commit()
        print(f"🧹 Puffer bereinigt: {len(deleted_files)} geschlossene/gelöschte Sessions aus memory_buffer.db entfernt ({', '.join(deleted_files)}).")
        
    chunk_map = {}
    for c in refined:
        chash = hashlib.md5(c["content"].encode("utf-8")).hexdigest()
        c["content_hash"] = chash
        chunk_map[chash] = c
        
    all_hashes = list(chunk_map.keys())
    existing_hashes = set()
    
    batch_size = 500
    for i in range(0, len(all_hashes), batch_size):
        sub_hashes = all_hashes[i:i+batch_size]
        q_marks = ",".join("?" for _ in sub_hashes)
        cursor.execute(f"SELECT content_hash FROM chunks WHERE content_hash IN ({q_marks})", sub_hashes)
        for row in cursor.fetchall():
            existing_hashes.add(row[0])
            
    new_chunks = [chunk_map[h] for h in all_hashes if h not in existing_hashes]
    dur_check = (datetime.now() - start_time).total_seconds()
    
    if not new_chunks:
        print(f"✅ Alle {len(all_hashes)} Abschnitte der offenen Chats sind bereits im Vektor-Gedächtnis vorhanden (Prüfzeit: {dur_check:.2f}s).")
        conn.close()
        return
        
    print(f"⚡ {len(new_chunks)} neue Chunks in offenen Chats entdeckt (nach {dur_check:.2f}s). Vektorisiere Delta...")
    
    # 3. FastEmbed nur laden wenn wirklich neue Chunks vorliegen
    from fastembed import TextEmbedding
    embedding_model = TextEmbedding(model_name=model_name)
    
    texts_to_embed = [
        f"[{c['title']} | Sprecher: {c['speaker']} | Datum: {c['date_str']}]\n{c['content']}"
        for c in new_chunks
    ]
    
    embeddings_gen = embedding_model.embed(texts_to_embed, batch_size=64)
    embeddings_list = list(embeddings_gen)
    
    for c, emb in zip(new_chunks, embeddings_list):
        emb_blob = np.array(emb, dtype=np.float32).tobytes()
        cursor.execute("""
            INSERT OR IGNORE INTO chunks (
                filename, teil_nr, title, date_str, speaker,
                turn_index, start_line, end_line, content,
                content_hash, embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["filename"], c["teil_nr"], c["title"], c["date_str"], c["speaker"],
            c["turn_index"], c["start_line"], c["end_line"], c["content"],
            c["content_hash"], emb_blob
        ))
        
    conn.commit()
    conn.close()
    
    total_dur = (datetime.now() - start_time).total_seconds()
    print(f"🎉 Fertig in {total_dur:.2f}s! {len(new_chunks)} neue Chunks aus offenen Chats erfolgreich im Vektor-Gedächtnis gesichert.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Memory Vector Indexer")
    parser.add_argument("--test", type=int, default=None, help="Begrenze auf N Dateien für Testlauf")
    parser.add_argument("--file", type=str, default=None, help="Gezielte Einzeldatei indizieren (z. B. für neue Chats)")
    parser.add_argument("--force", action="store_true", help="Erzwinge vollständige Neuindizierung")
    parser.add_argument("--model", type=str, default=MODEL_NAME, help="Embedding Modellname")
    parser.add_argument("--scan-harness", action="store_true", help="Scannt offene Harness-Chats und indiziert Delta-Chunks")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Ziel-Vektordatenbank")
    args = parser.parse_args()
    
    if args.scan_harness:
        scan_active_harness(model_name=args.model)
    else:
        index_corpus(limit=args.test, force=args.force, model_name=args.model, target_file=args.file, db_path=args.db)


