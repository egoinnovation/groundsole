#!/usr/bin/env python3
"""
Groundsole Relational Knowledge Graph Helper (Zero-API / Native SQLite)
Manages topological entities, infrastructure relations, and life-module connections in 00_MEMORY/graph.db.
Requires zero external LLM API calls.
"""

import sys
import os
import sqlite3
import json
import uuid
from datetime import datetime

def find_workspace_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(os.path.dirname(script_dir))
    if os.path.exists(os.path.join(workspace_root, "00_MEMORY")):
        return workspace_root
    if os.path.exists(os.path.join(os.getcwd(), "00_MEMORY")):
        return os.getcwd()
    return workspace_root

WORKSPACE_DIR = find_workspace_root()
DB_PATH = os.path.join(WORKSPACE_DIR, "00_MEMORY", "graph.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            type TEXT NOT NULL,
            attributes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            relationship TEXT NOT NULL,
            target_id TEXT NOT NULL,
            attributes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(relationship)")
    conn.commit()
    return conn

def get_or_create_node(conn, label, node_type="Entity", attributes=None):
    c = conn.cursor()
    row = c.execute("SELECT id FROM nodes WHERE label = ? COLLATE NOCASE", (label,)).fetchone()
    if row:
        return row[0]

    node_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    attrs_json = json.dumps(attributes or {})
    c.execute(
        "INSERT INTO nodes (id, label, type, attributes, created_at) VALUES (?, ?, ?, ?, ?)",
        (node_id, label, node_type, attrs_json, now)
    )
    conn.commit()
    return node_id

def add_edge(source_label, relationship, target_label, attributes=None):
    conn = get_connection()
    src_id = get_or_create_node(conn, source_label)
    tgt_id = get_or_create_node(conn, target_label)
    c = conn.cursor()

    # Check if edge already exists
    edge_row = c.execute(
        "SELECT id FROM edges WHERE source_id=? AND relationship=? AND target_id=?",
        (src_id, relationship.upper(), tgt_id)
    ).fetchone()

    now = datetime.now().isoformat()
    attrs_json = json.dumps(attributes or {})

    if edge_row:
        c.execute("UPDATE edges SET attributes=?, created_at=? WHERE id=?", (attrs_json, now, edge_row[0]))
        conn.commit()
        conn.close()
        print(f"Updated edge: [{source_label}] ---({relationship.upper()})---> [{target_label}]")
        return edge_row[0]

    edge_id = str(uuid.uuid4())
    c.execute(
        "INSERT INTO edges (id, source_id, relationship, target_id, attributes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (edge_id, src_id, relationship.upper(), tgt_id, attrs_json, now)
    )
    conn.commit()
    conn.close()
    print(f"Added edge: [{source_label}] ---({relationship.upper()})---> [{target_label}]")
    return edge_id

def query_graph(term):
    conn = get_connection()
    c = conn.cursor()
    term_pattern = f"%{term}%"
    rows = c.execute("""
        SELECT n1.label, e.relationship, n2.label, e.attributes
        FROM edges e
        JOIN nodes n1 ON e.source_id = n1.id
        JOIN nodes n2 ON e.target_id = n2.id
        WHERE n1.label LIKE ? OR n2.label LIKE ? OR e.relationship LIKE ?
    """, (term_pattern, term_pattern, term_pattern)).fetchall()
    conn.close()

    if not rows:
        print(f"No relations found matching '{term}'.")
        return

    print(f"\n--- Graph Search Results for '{term}' ({len(rows)} relations) ---")
    for r in rows:
        print(f"• [{r[0]}] ──({r[1]})──> [{r[2]}] | {r[3]}")

def list_edges():
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute("""
        SELECT n1.label, e.relationship, n2.label, e.attributes
        FROM edges e
        JOIN nodes n1 ON e.source_id = n1.id
        JOIN nodes n2 ON e.target_id = n2.id
        ORDER BY e.created_at DESC
    """).fetchall()
    conn.close()

    print(f"\n--- Groundsole Knowledge Graph ({len(rows)} Relations) ---")
    for r in rows:
        print(f"• [{r[0]}] ──({r[1]})──> [{r[2]}] | {r[3]}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  knowledge_graph.py list")
        print("  knowledge_graph.py query <term>")
        print("  knowledge_graph.py add <source> <rel> <target> [json_attrs]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "list":
        list_edges()
    elif cmd == "query" and len(sys.argv) >= 3:
        query_graph(sys.argv[2])
    elif cmd == "add" and len(sys.argv) >= 5:
        src = sys.argv[2]
        rel = sys.argv[3]
        tgt = sys.argv[4]
        attrs = {}
        if len(sys.argv) >= 6:
            try:
                attrs = json.loads(sys.argv[5])
            except Exception as e:
                print(f"Warning: JSON parse error for attributes: {e}")
        add_edge(src, rel, tgt, attrs)
    else:
        print("Invalid arguments. Use list, query, or add.")

if __name__ == "__main__":
    main()
