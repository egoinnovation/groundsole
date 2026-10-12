---
name: memory-recall
description: "Unified cross-modal cognitive retrieval across plaintext modules, semantic vector shards, relational knowledge graphs, and key-value facts."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, retrieval, memory, search, vectors, graph]
---

# Memory Recall Skill

This skill governs unified recall across all memory layers in Groundsole when a user asks about past topics, past conversations, or established facts.

---

## Trigger Conditions

Activate this skill when:
- The user asks: *"What did we discuss about X?"*, *"Do you remember our conversation regarding Y?"*, *"Search memory for..."*, or uses `/recall`.
- Cross-referencing historical decisions, dates, or specifications.

---

## 🔍 Retrieval Cascade (Fastest to Deepest)

Execute retrieval in four cascaded tiers:

### 1. Active Plaintext State Check
- First, check if the topic is tracked in active domain modules (`00_MEMORY/modules/*.md`) or `00_MEMORY/DYNAMIC_STATE.md`.

### 2. Fast Key-Value & Fact Lookup
- Search the structured facts store:
  ```bash
  python3 tools/scripts/memory.py search "<term>"
  ```

### 3. Relational Knowledge Graph Query
- Query the topological graph for entities and relationships:
  ```bash
  python3 tools/scripts/knowledge_graph.py query "<term>"
  ```

### 4. Deep Semantic Multi-DB Vector Search (MANDATORY BEFORE ANY TRANSCRIPT READ)
- For associative searches across historical transcripts (even if different terminology was used):
  ```bash
  python3 tools/scripts/memory_retriever.py --query "<term>" --top_k 5
  ```
- **Token Hygiene Directive:** Always prioritize semantic vector search over reading raw markdown transcripts or summaries. Vector search runs 100% locally on CPU (0 context tokens) and returns only pinpointed verbatim chunks, saving tens of thousands of tokens and preventing premature context compaction.

---

## Output Protocol
Synthesize the findings into a concise, grounded response:
- State exact dates and source filenames.
- Quote relevant verbatim excerpts when evidence is required.
- Clearly distinguish between established facts and unverified items.
