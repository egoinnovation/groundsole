#!/usr/bin/env python3
"""
Groundsole Key-Value & Fact Memory Helper
Stores and retrieves persistent user facts, preferences, and operational state in 00_MEMORY/langmem_store.db.
Includes automatic cloud-sync conflict resolution (iCloud / OneDrive / Dropbox).
"""

import os
import sys
import sqlite3
import json
import glob
from datetime import datetime

def find_db_path():
    # 1. Check relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(os.path.dirname(script_dir))
    candidate = os.path.join(workspace_root, "00_MEMORY", "langmem_store.db")
    if os.path.exists(os.path.dirname(candidate)):
        return candidate
    # 2. Check current working directory
    candidate_cwd = os.path.join(os.getcwd(), "00_MEMORY", "langmem_store.db")
    if os.path.exists(os.path.dirname(candidate_cwd)):
        return candidate_cwd
    # 3. Fallback to candidate
    return candidate

DB_PATH = find_db_path()

def init_db(db_path=None):
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            namespace TEXT NOT NULL,
            key TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_namespace ON memories(namespace)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_key ON memories(key)")
    conn.commit()
    conn.close()

def check_and_resolve_conflicts():
    mem_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(mem_dir):
        return
    patterns = [
        os.path.join(mem_dir, "langmem_store *.db"),
        os.path.join(mem_dir, "langmem_store (*).db"),
        os.path.join(mem_dir, "langmem_store_*conflict*.db"),
    ]
    conflict_files = []
    for p in patterns:
        conflict_files.extend(glob.glob(p))

    if not conflict_files:
        return

    init_db()
    conn_main = sqlite3.connect(DB_PATH)
    c_main = conn_main.cursor()

    for cfile in sorted(conflict_files):
        cfile_name = os.path.basename(cfile)
        try:
            conn_conf = sqlite3.connect(cfile)
            c_conf = conn_conf.cursor()
            c_conf.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
            if not c_conf.fetchone():
                conn_conf.close()
                continue

            rows = c_conf.execute("SELECT timestamp, namespace, key, content FROM memories").fetchall()
            merged_count = 0
            for r in rows:
                exists = c_main.execute(
                    "SELECT id FROM memories WHERE timestamp=? AND namespace=? AND key=?",
                    (r[0], r[1], r[2])
                ).fetchone()
                if not exists:
                    c_main.execute(
                        "INSERT INTO memories (timestamp, namespace, key, content) VALUES (?, ?, ?, ?)",
                        r
                    )
                    merged_count += 1
            conn_main.commit()
            conn_conf.close()
            os.remove(cfile)
            if merged_count > 0:
                print(f"ℹ️ Merged {merged_count} facts from sync conflict file {cfile_name}.")
        except Exception as e:
            print(f"⚠️ Warning resolving {cfile_name}: {e}")

    conn_main.close()

def add_memory(namespace, key, content):
    check_and_resolve_conflicts()
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("INSERT INTO memories (timestamp, namespace, key, content) VALUES (?, ?, ?, ?)",
                   (now, namespace, key, content))
    conn.commit()
    conn.close()
    print(f"✅ Memory stored: [{namespace}] {key}")

def search_memory(query):
    check_and_resolve_conflicts()
    if not os.path.exists(DB_PATH):
        print("ℹ️ No memory database found yet.")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = """
        SELECT id, timestamp, namespace, key, content
        FROM memories
        WHERE namespace LIKE ? OR key LIKE ? OR content LIKE ?
        ORDER BY id DESC
    """
    pattern = f"%{query}%"
    rows = cursor.execute(sql, (pattern, pattern, pattern)).fetchall()
    conn.close()

    if not rows:
        print(f"No results found for query: '{query}'")
        return

    print(f"Found {len(rows)} memory records for '{query}':")
    for r in rows:
        print(f"• [ID: {r[0]} | {r[1][:10]} | {r[2]}] {r[3]}: {r[4]}")

def list_memories(namespace=None):
    check_and_resolve_conflicts()
    if not os.path.exists(DB_PATH):
        print("ℹ️ No memory database found yet.")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if namespace:
        rows = cursor.execute("SELECT id, timestamp, namespace, key, content FROM memories WHERE namespace=? ORDER BY id DESC", (namespace,)).fetchall()
    else:
        rows = cursor.execute("SELECT id, timestamp, namespace, key, content FROM memories ORDER BY namespace, key").fetchall()
    conn.close()

    for r in rows:
        print(f"[{r[2]}] {r[3]}: {r[4]}")

def main():
    if len(sys.argv) < 2:
        print("Usage: memory.py add <namespace> <key> <content> | search <query> | list [namespace]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "add" and len(sys.argv) >= 5:
        add_memory(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    elif cmd == "search" and len(sys.argv) >= 3:
        search_memory(" ".join(sys.argv[2:]))
    elif cmd == "list":
        ns = sys.argv[2] if len(sys.argv) >= 3 else None
        list_memories(ns)
    else:
        print("Invalid arguments. Use: add, search, list")

if __name__ == "__main__":
    main()
