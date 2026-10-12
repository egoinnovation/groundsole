---
name: isn-memory-engine
description: Lokales Vektorgedächtnis (isn_vectors.db mit Jina-Embeddings) auf dem persölichen OneDrive-Spoke verwalten.
---

# ISN Memory Engine

Verwaltet die lokale SQLite-Vektordatenbank (`isn_vectors.db`) auf dem persönlichen Spoke des Nutzers (`C:\Users\<user>\OneDrive...\ISN-AI\00_MEMORY\isn_vectors.db`).

## Kernregeln:
1. **Strikte lokale Isolation:** Die SQLite-Datenbank liegt **niemals** auf SharePoint, sondern ausschließlich auf dem persönlichen OneDrive-Spoke.
2. **Jina Embeddings:** Verwendet Jina-Embeddings für präzise deutsch- und englischsprachige semantische Suchen.
3. **Persönlicher Datenschutz:** Vertrauliche Arbeitsnotizen und Entwürfe verbleiben lokal auf dem Rechner des Nutzers.
