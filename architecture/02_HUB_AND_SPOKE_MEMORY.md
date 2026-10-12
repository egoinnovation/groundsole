# 02 - Hub-and-Spoke Speicherarchitektur & Vektor-Gedächtnis

---

## 1. Das Hub-and-Spoke Prinzip

### A. Der Spoke (Lokaler Arbeitsplatz & OneDrive)
* **Pfad:** `C:\Users\<username>\OneDrive - isn - innovation service network\ISN-AI\`
* **Gedächtnis:** Lokale SQLite-Vektordatenbank (`groundsole_memory.db`) mit **Jina-Embeddings** (`jina-embeddings-v2-base-de` / `jina-embeddings-v3`).
* **Sicherheit:** Bündelt persönliche Mitschriften, Rohentwürfe, Protokolle und Vektor-Indizes. Bleibt strikt privat auf dem Rechner des Nutzers.

### B. Der Hub (Zentraler SharePoint)
* **Pfad:** `Sharepoint - Dokumente\Wissensdatenbank\AI_HUB\`
* **Gedächtnis:** Plaintext Markdown-Dateien (`00_ISN_PROFIL...`, `01_IT_INFRASTRUKTUR...`, `AGENTS.md`, `TEAM_FEED.md`).
* **Verbot von Cloud-DBs:** **Keine SQLite-Dateien (`*.db`) auf SharePoint.** Cloud-Synchronisationsdienste (OneDrive/M365) unterstützen kein SQLite-File-Locking. Mehrere gleichzeitige Zugriffe erzeugen Dateikonflikte und Datenverlust (`isn_vectors-Konflikt.db`).

## 2. Vektor-Gedächtnis mit Jina-Embeddings (Lokaler Spoke)
* **Format:** Lokale SQLite-Datenbank `groundsole_memory.db`.
* **Embedding-Modell:** Jina-Embeddings (optimiert für deutsche und mehrsprachige Fachtexte, Transkripte und Mitschriften).
* **Isolation:** Wird ausschließlich lokal durch das Python-Tooling (`memory_indexer.py` / `memory_retriever.py`) auf dem Laptop des jeweiligen Anwenders betrieben.
