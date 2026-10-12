# Groundsole ISN — Operating Architecture for Sovereign AI Coprocessors

[![Organization](https://img.shields.io/badge/Organization-innovation_service_network-blue.svg)](https://github.com/egoinnovation)
[![Architecture](https://img.shields.io/badge/Architecture-Hub_and_Spoke-emerald.svg)](#hub-and-spoke-architecture)

> **Groundsole Framework for ISN (innovation service network GmbH)**  
> *Biophysical Causality, Plaintext Markdown SSOT, Local Vector Memory (Jina Embeddings), and Hub-and-Spoke Knowledge Promotion.*

---

## 💡 Overview

Groundsole ISN is the tailored operating architecture for agentic AI harnesses (Hermes Agent, Claude Code, Antigravity) across the 7 workstations of the ISN team.

It enforces a strict separation between **Personal Workstation Autonomy (Spoke)** and **Shared Team Memory (Hub)**:

1. **Spoke (Personal Workstation / OneDrive):**  
   * Location: `C:\Users\<username>\OneDrive - isn - innovation service network\ISN-AI\`
   * Function: Private workspace, personal notes, draft documents, and local SQLite vector database (`isn_vectors.db`) powered by Jina Embeddings.
2. **Hub (Shared SharePoint):**  
   * Location: `Sharepoint - Dokumente\Wissensdatenbank\AI_HUB\`
   * Function: Authoritative, curated team knowledge stored exclusively in plaintext Markdown (`00` to `05` dossiers, `AGENTS.md`, `TEAM_FEED.md`). No SQLite databases allowed on SharePoint to prevent sync conflicts.
3. **Knowledge Promotion & Crystallization:**  
   * The individual user retains 100% control over their private work. Relevant knowledge is explicitly promoted ("crystallized") from the private Spoke into the shared SharePoint Hub.

---

## 📂 Repository Structure

```
groundsole/
├── README.md                      # English documentation
├── README_DE.md                   # German documentation & operational guide
├── architecture/                  # Architectural principles
│   ├── 01_CORE_PRINCIPLES_AND_SSOT.md
│   ├── 02_HUB_AND_SPOKE_MEMORY.md
│   └── 03_KNOWLEDGE_CRYSTALLIZATION.md
├── templates/                     # Starter templates for Spoke & Hub
│   ├── AGENTS.md                  # Minimal harness-agnostic Spoke anchor
│   └── HUB_AGENTS.md              # Shared SharePoint AI_HUB master anchor
├── tools/                         # Execution scripts for setup & memory
│   ├── setup_spoke.py             # 1-Click Spoke setup on employee laptop
│   ├── memory_indexer.py          # Local SQLite vector DB indexer (Jina)
│   ├── memory_retriever.py        # Local vector DB semantic search
│   └── crystallize.py             # Knowledge promotion script
└── skills/                        # Procedural skills for AI harnesses
    ├── isn-memory-engine/
    ├── isn-knowledge-crystallization/
    └── isn-hub-sync/
```

---

## 🛠️ Quick Start (Workstation Setup)

To set up a local ISN Spoke workspace on an employee laptop:

```bash
python tools/setup_spoke.py
```

This creates the `ISN-AI` directory in the user's personal OneDrive, deploys the minimal `AGENTS.md`, and initializes the local vector memory structure.
