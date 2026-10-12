#!/usr/bin/env python3
"""
ISN Local Vector Memory Indexer
Indiziert lokale Notizen und Mitschriften in die SQLite-Vektordatenbank (isn_vectors.db)
unter Verwendung von Jina-Embeddings.
"""

import sqlite3
import os
import sys

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            filename TEXT PRIMARY KEY,
            file_hash TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chunk_count INTEGER,
            title TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            chunk_index INTEGER,
            title TEXT,
            content TEXT,
            embedding BLOB
        )
    """)
    conn.commit()
    return conn

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "isn_vectors.db"
    conn = init_db(db_path)
    print(f"[+] Vektordatenbank initialisiert/geprüft: {db_path}")

if __name__ == "__main__":
    main()
