#!/usr/bin/env python3
"""
ISN Local Vector Memory Retriever
Führt semantische Suchen in der lokalen groundsole_memory.db durch.
"""

import sqlite3
import sys

def search(db_path, query):
    if not os.path.exists(db_path):
        print(f"[!] Vektordatenbank nicht gefunden: {db_path}")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, title, content FROM chunks WHERE content LIKE ? LIMIT 5", (f"%{query}%",))
    rows = cursor.fetchall()
    print(f"Gefundene Chunks für '{query}': {len(rows)}")
    for r in rows:
        print(f"
--- Chunk ID: {r[0]} | Datei: {r[1]} ---")
        print(r[3][:300])

if __name__ == "__main__":
    import os
    db_path = sys.argv[1] if len(sys.argv) > 1 else "groundsole_memory.db"
    query = sys.argv[2] if len(sys.argv) > 2 else ""
    if query:
        search(db_path, query)
    else:
        print("Nutzung: python memory_retriever.py <db_pfad> <suchbegriff>")
