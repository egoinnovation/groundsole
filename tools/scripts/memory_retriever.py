#!/usr/bin/env python3
"""
Groundsole Federated Multi-DB Vector Retriever
Searches across all sealed epoch shards (archive_*.db) and active working databases in 00_MEMORY/vectors/.
"""

import os
import sys
import glob
import sqlite3
import argparse
import numpy as np
from typing import List, Dict, Tuple, Optional

def find_workspace_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(os.path.dirname(script_dir))
    if os.path.exists(os.path.join(workspace_root, "00_MEMORY")):
        return workspace_root
    if os.path.exists(os.path.join(os.getcwd(), "00_MEMORY")):
        return os.getcwd()
    return workspace_root

WORKSPACE_DIR = find_workspace_root()
VECTORS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "vectors")
MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"

def discover_databases() -> List[str]:
    if not os.path.exists(VECTORS_DIR):
        return []
    raw_dbs = sorted(glob.glob(os.path.join(VECTORS_DIR, "*.db")))
    return sorted(list(set(os.path.realpath(f) for f in raw_dbs)))

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    dot = np.dot(a, b.T)
    norm_a = np.linalg.norm(a, axis=-1, keepdims=True)
    norm_b = np.linalg.norm(b, axis=-1, keepdims=True)
    return dot / (norm_a * norm_b.T + 1e-9)

def search_shards(query_str: str, top_k: int = 5, speaker_filter: Optional[str] = None) -> List[Dict]:
    dbs = discover_databases()
    if not dbs:
        print("ℹ️ No vector databases found in 00_MEMORY/vectors/")
        return []

    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("❌ fastembed is not installed. Please run: pip install fastembed numpy")
        return []

    model = TextEmbedding(model_name=MODEL_NAME)
    query_embedding = np.array(list(model.embed([query_str]))[0], dtype=np.float32)

    all_candidates = []

    for db_path in dbs:
        db_name = os.path.basename(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
            if not cursor.fetchone():
                conn.close()
                continue

            query_sql = "SELECT id, filename, chunk_index, speaker, timestamp_str, header_context, content, embedding FROM chunks"
            params = []
            if speaker_filter:
                query_sql += " WHERE LOWER(speaker) = LOWER(?)"
                params.append(speaker_filter)

            rows = cursor.execute(query_sql, params).fetchall()
            if not rows:
                conn.close()
                continue

            chunk_embs = np.vstack([np.frombuffer(r[7], dtype=np.float32) for r in rows])
            sims = cosine_similarity(query_embedding[np.newaxis, :], chunk_embs)[0]

            for r, sim in zip(rows, sims):
                all_candidates.append({
                    "score": float(sim),
                    "db": db_name,
                    "filename": r[1],
                    "chunk_index": r[2],
                    "speaker": r[3],
                    "timestamp": r[4],
                    "header": r[5],
                    "content": r[6]
                })

        except Exception as e:
            print(f"⚠️ Error reading {db_name}: {e}")
        finally:
            conn.close()

    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    return all_candidates[:top_k]

def main():
    parser = argparse.ArgumentParser(description="Groundsole Multi-DB Semantic Retriever")
    parser.add_argument("--query", required=True, help="Search text query")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--speaker", choices=["User", "Assistant"], help="Filter by speaker")
    parser.add_argument("--sync", action="store_true", default=True, help="Run fast delta scan of active harness before searching")
    parser.add_argument("--no-sync", dest="sync", action="store_false", help="Skip harness delta scan")
    args = parser.parse_args()

    if getattr(args, 'sync', True):
        try:
            from memory_indexer import scan_active_harness
            scan_active_harness()
        except Exception:
            pass

    results = search_shards(args.query, top_k=args.top_k, speaker_filter=args.speaker)

    if not results:
        print(f"No semantic matches found for: '{args.query}'")
        return

    print(f"\n🔍 Top {len(results)} matches for: '{args.query}'\n" + "="*60)
    for i, res in enumerate(results, 1):
        print(f"\n[{i}] Score: {res['score']:.4f} | Shard: {res['db']} | File: {res['filename']}")
        print(f"Speaker: {res['speaker']} | Section: {res['header']}")
        print("-" * 60)
        # Print excerpt (max 300 chars)
        content_preview = res['content'][:300] + ("..." if len(res['content']) > 300 else "")
        print(content_preview)

if __name__ == "__main__":
    main()
