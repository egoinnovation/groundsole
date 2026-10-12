---
name: stream-archive
description: "Automated session transcript archiving, telemetry sanitization, signature generation, and long-term memory crystallization."
version: 1.0.0
author: Groundsole Core Team
tags: [groundsole, archive, indexing, memory, automation]
---

# Stream Archive Skill

This skill governs the foundational transition of cognitive data in Groundsole: **moving from volatile conversation memory into immutable, indexed long-term storage.**

---

## 🧠 Fundamental Principle: RAM vs. Long-Term Storage

> [!IMPORTANT]
> **To the User and Agent:**  
> An active chat session is ephemeral cognitive working RAM. **The AI does NOT possess durable, cross-session recall of ongoing thoughts until the session is explicitly archived.**
> 
> Archiving is the crystallization event that:
> 1. Freezes the raw dialogue as an immutable primary source in `00_MEMORY/transcripts/`.
> 2. Filters out raw telemetry, system tokens, and noise.
> 3. Extracts a structured, dense signature into `00_MEMORY/summaries/`.
> 4. Triggers incremental ingestion into the active semantic vector database shard.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Archive this session"*, *"Export and archive chat"*, *"Sync transcripts"*, or *"Process new chats"*.
- A conversation reaches major milestone breakthroughs or nears the context token ceiling.

---

## 📝 Formatting & Sanitization Standards

Every session transcript saved to `00_MEMORY/transcripts/` must strictly adhere to these formatting rules:

1. **Heading Hierarchy (H1 vs H2 vs H3) & Speaker Identity:**
   - **H1 (`#`)**: Solely the main title at the very top (e.g., `# 2026-09-18 - Groundsole Core Architecture`).
   - **H2 (`##`)**: Solely the speaker headings with timestamps:
     - `## User (YYYY-MM-DDTHH:MM:SS+02:00)` (or specified user profile name).
     - `## Assistant (YYYY-MM-DDTHH:MM:SS+02:00)` (or Claude / Hermes / Antigravity etc.)
   - **H3 (`###`) and below**: All section headings *within* responses.

2. **Telemetry Sanitization & Anti-Noise:**
   - **System XML Tags:** Completely strip all system wrapper tags: `<ADDITIONAL_METADATA>`, `<CONTEXT_SUMMARY>`, `<USER_REQUEST>`, `<SYSTEM_MESSAGE>`.
   - **Client Telemetry:** Strip tool JSON schemas, voluminous compiler dumps, unformatted stack traces, and base64 strings.
   - **Rationale:** Only genuine reasoning, decisions, and factual dialogue belong in the transcript. Telemetry noise degrades semantic vector embeddings.

3. **Direct H1-to-H2 Transition (No Metadata Header):**
   - Directly after H1, the first speaker H2 **must follow immediately** (`# Title \n\n ## User (...)`).
   - Do **not** inject metadata lines (`Date:`, `Participants:`, `Status:`) into the transcript.

4. **Two-Path Archiving Triage & Zero-Leak Sanitizing:**
   - **Path A (Standard / Personal & Strategy):**
     - Applies to general reflections, personal domains, philosophy, overarching strategy.
     - Transcript: `00_MEMORY/transcripts/YYYY-MM-DD - [Title].md`
     - Vector Database: Primary active DB shard.
   - **Path B (Isolated Domain / Operational Work):**
     - Applies to IT infrastructure, credentials, switches, routers, licenses, operational procedures.
     - **Check 1 (Privacy & Reflection):** Ensure no personal private notes are mixed in operational logs.
     - **Check 2 (Zero-Leak Secret Sanitizer):** Replace all passwords, router keys, and secrets with `[IN_SECRET_MANAGER_SAVED]`.
     - Transcript: `00_MEMORY/transcripts/YYYY-MM-DD - [Domain] - [Title].md`
     - Vector Database: Dedicated domain shard (isolated from primary personal memory).

---

## 📋 Step-by-Step Archival Lifecycle

1. **Triage & Classification:**
   Check whether Path A or Path B applies. Perform privacy check for Path B.
2. **Inspect & Sanitize:**  
   Read raw export, ensure proper H1/H2 formatting, remove telemetry junk. Replace secrets with `[IN_SECRET_MANAGER_SAVED]`.
3. **Save Transcript:**  
   Write sanitized file to `00_MEMORY/transcripts/YYYY-MM-DD - [Descriptive_Title].md`.
4. **Incremental Vector Ingestion:**  
   Index new transcript into the appropriate database shard.
5. **Deterministic State Synchronization & Memory Crystallization:**  
   Run deterministic memory crystallization and update `DYNAMIC_STATE.md`.
6. **Mandatory Post-Archiving Quality Control (QC) & Report:**  
   Perform verification checklist and present structured QC report:
   - **Speaker Integrity:** Verify human speaker headers use valid format.
   - **Chronology:** Verify session runs chronologically without prepending foreign sessions.
   - **Header Hierarchy:** Verify H1 title immediately followed by H2 first speaker.
   - **Hygiene & Sanitization:** Confirm total removal of `<CONTEXT_SUMMARY>`, `<USER_REQUEST>`, raw tool telemetry, and replacement of all secrets.
   - **Vector Routing:** Confirm embeddings written to target vector shard.
   - **Dynamic State:** Confirm synchronized stats in `DYNAMIC_STATE.md`.
