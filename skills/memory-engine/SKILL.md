---
name: memory-engine
description: "Unified cognitive memory engine for Groundsole — governs autonomous fact/decision persistence and multi-tier semantic retrieval across all harnesses."
version: 1.1.0
author: Emanuel Gössler
tags: [groundsole, memory, recall, storage, vectors, graph, langmem, harness-agnostic]
---

# Groundsole Memory Engine Skill

This skill provides a unified, harness-agnostic interface for cognitive memory operations across any LLM agent environment (Antigravity, Hermes, Claude Code, Cursor, Codex, etc.). It operates as a dual-action engine:
1. **Autonomous Persistence (Writing):** Captures state shifts, facts, and decisions at the conclusion of relevant dialogue turns.
2. **Cascaded Retrieval (Reading):** Searches across plaintext modules, structured fact tables, relational graphs, and vector databases.

---

## Part 1: Autonomous Persistence Protocol (Writing)

At the conclusion of every dialogue turn, silently inspect whether a binding fact, status shift, decision, or permanent preference was established.

### 🚨 Emotion as Smoke Detector & Turn-End Checklist
- **Emotion as Milestone Sensor:** Strong user emotions (pride, relief, frustration, excitement) are smoke detectors signaling real-world breakthroughs or critical friction. Reflexively identify the underlying technical/status cause and persist it!
- **Input Chunking Check:** If a user prompt contains a retrospective/milestone followed by a new task, never allow the first part to be lost in the execution of the second. Extract and persist facts first!
- **Turn-End Checklist:** Before rendering the final response, silently verify:
  1. Did a milestone, decision, or state shift occur?
  2. Is it persisted in memory?
  If yes, execute the persistence command.

### Trigger Categories & Namespaces
Execute the following CLI command in the background:
```bash
python3 scripts/memory.py add "<Namespace>" "<Key>" "<Content>"
```

1. **Decisions & Status Shifts (`Namespace: Decisions` or `<ProjectID>`):**
   - Every directional choice, approval, rejection, or plan change (e.g. tool selection, timeline shift, deployment).
2. **Project, Client & Contact Facts (`Namespace: <ProjectID>` or `<Contact>`):**
   - Deadlines, mutual agreements, external commitments, quotes, or statements by third parties.
3. **Infrastructure, Finance & Systems (`Namespace: Infrastructure` or `Finanzen`):**
   - Technical parameters, paths, endpoints, credentials, pricing, contract terms, consumption figures.
4. **Principles, Values & No-Gos (`Namespace: Global` / Key: `Werte_Und_Prinzipien`):**
   - Architectural principles, immutable preferences, red lines, and operational guardrails.
5. **Insights & Breakthroughs (`Namespace: Global` / Key: `Erkenntnisse`):**
   - Methodological breakthroughs, solved bottlenecks, conceptual clarifications.
6. **Universal Catch-All Criterion:**
   - Any established fact whose absence in future sessions would cause friction, repetition, or false assumptions.

### Relational Graph Mapping (Topological Knowledge)
When persistent entity relations or structural dependencies are established or altered:
```bash
python3 scripts/cognee_graph.py add "<Source>" "<RELATION>" "<Target>" '<JSON_ATTRIBUTES>'
```

---

## Part 2: Cascaded Retrieval Protocol (Reading)

When the user asks about past topics, earlier discussions, or established facts (*"What did we discuss about X?"*, *"Do you remember Y?"*, `/recall`):

### 1. Plaintext Module Scan
Check active domain files in `00_MEMORY/modules/*.md` or `00_MEMORY/DYNAMIC_STATE.md`.

### 2. Fast Key-Value Fact Lookup
Query the structured SQLite memory store:
```bash
python3 scripts/memory.py search "<query>"
```

### 3. Knowledge Graph Relational Query
Inspect topological entity connections:
```bash
python3 scripts/cognee_graph.py search "<query>"
```

### 4. Deep Semantic Multi-DB Vector Retrieval
Search historical session transcripts and epochal archives:
```bash
python3 scripts/memory_retriever.py --query "<query>" --top_k 5
```

---

## Part 3: Harness-Agnostic Operation

- **Harness Detection:** The engine detects whether it is executed within Antigravity, Hermes, Claude, or standalone terminal and uses the standard local virtual environment (`$HOME/.local/venv`).
- **Idempotency:** Re-indexing or re-archiving conversations never produces duplicate vector records (`INSERT OR IGNORE INTO chunks`).
- **Digital Hygiene:** Ephemeral conversational state is buffered in `memory_buffer.db`, while verified, finished dialogues are curated in `memory_active.db`.
