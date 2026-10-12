---
name: inbox-triage
description: "Deterministic processing of raw incoming documents from Inbox/ into domain modules, task lists, and long-term memory."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, inbox, triage, processing, workflow]
---

# Inbox Triage Skill

This skill governs the ingestion of unstructured external inputs (notes, invoices, meeting transcripts, incoming briefs) dropped into the workspace `Inbox/` directory.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Process the inbox"*, *"Triage new documents"*, or *"Read files in Inbox"*.

---

## 📋 Triage Workflow

1. **Scan `Inbox/`:** List all unfiled files and documents in the `Inbox/` directory.
2. **Extract & Classify:**
   - **Operational Tasks / Deadlines:** Extract into `00_MEMORY/DYNAMIC_STATE.md` or `modules/OPERATIONS_AND_PROJECTS.md`.
   - **Financial Documents (Receipts, Budgets):** Extract facts into `modules/RESOURCES_AND_FINANCE.md`.
   - **Technical Specifications / Assets:** File into `modules/INFRASTRUCTURE_AND_ASSETS.md`.
   - **Meeting Notes / Long Discussions:** Sanitize and convert into a dated transcript in `00_MEMORY/transcripts/`.
3. **Move to Destination:**  
   Never leave processed files dangling in `Inbox/`. Move them to their structured destination folder (e.g. `02_PROJECTS/` or `00_MEMORY/archive/`).
4. **Report Actions:** Concisely summarize the extracted data points and target destinations.
