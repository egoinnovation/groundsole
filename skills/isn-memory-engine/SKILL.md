---
name: isn-memory-engine
description: Lokales Vektorgedächtnis (groundsole_memory.db mit Jina-Embeddings) auf dem persölichen OneDrive-Spoke verwalten.
---

# ISN Memory Engine

Verwaltet die lokale SQLite-Vektordatenbank (`groundsole_memory.db`) auf dem persönlichen Spoke des Nutzers (`C:\Users\<user>\OneDrive...\ISN-AI\00_MEMORY\groundsole_memory.db`).

## Kernregeln:
1. **Strikte lokale Isolation:** Die SQLite-Datenbank liegt **niemals** auf SharePoint, sondern ausschließlich auf dem persönlichen OneDrive-Spoke.
2. **Jina Embeddings:** Verwendet Jina-Embeddings für präzise deutsch- und englischsprachige semantische Suchen.
3. **Persönlicher Datenschutz:** Vertrauliche Arbeitsnotizen und Entwürfe verbleiben lokal auf dem Rechner des Nutzers.
