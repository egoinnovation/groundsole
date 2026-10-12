---
name: system-hygiene
description: "Workspace entropy reduction, cache sanitization, orphaned directory audits, and SSOT pointer verification."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, hygiene, maintenance, entropy, cleanup, integrity]
---

# System Hygiene Skill

This skill performs periodic workspace audits to eliminate technical entropy, prevent cache pollution, and verify link integrity across all Markdown documents and skills.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Run system hygiene"*, *"Clean up workspace"*, *"Check for dead links or duplicate files"*, *"Run dreaming"*, *"Gedächtnis prüfen"*, or *"Run audit"*.
- Periodically via scheduled background task (e.g. weekly dreaming routine).
- After major architectural refactoring or bulk document migrations.

---

## 📋 Audit & Cleanup Protocol

When triggered, execute the following audit routine deterministically:

### 1. Ephemeral OS & Cache Cleanup
- Identify and remove `.DS_Store`, `Thumbs.db`, and temporary editor swap files (`*.swp`, `*~`).
- Clean ephemeral Python caches (`__pycache__/`, `*.pyc`).

### 2. Single Source of Truth (SSOT) & Link Integrity
- Inspect relative links and Markdown cross-pointers in `00_MEMORY/index.md`, `00_MEMORY/LOAD_ORDER.md`, and active domain modules.
- Ensure every referenced file actually exists on disk.
- Detect accidental data duplication across multiple modules.

### 3. Orphaned Directory Detection
- Scan for abandoned or shadowed configuration directories (e.g. nested duplicate skill folders).
- Verify that skills adhere to the single authoritative location.

### 4. Dreaming & Cognitive Consistency Audit (Memory Health)
- Execute `python3 tools/scripts/check_integrity.py` to deterministically verify local markdown links and module registration.
- **Temporal & Focus Review:** Inspect `00_MEMORY/DYNAMIC_STATE.md` for past calendar dates, overdue milestones, or resolved items that can be retired.
- **Contradiction & Drift Scan:** Verify that state in domain modules (`modules/`) aligns with recent transcripts and agreements.
- **Strict Read-Only Guardrail:** The agent MUST NOT modify or overwrite memory modules during this audit. All findings and recommended corrections are compiled into `00_MEMORY/HYGIENE_REPORT.md` (or presented in chat) for human review and approval.

### 5. Status Summary
Output a concise status report:
- 🟢 Cleaned files & reclaimed storage
- 🟢 Link integrity & SSOT pointer verification (`check_integrity.py`)
- 🟢 Active registered skills
- 🌙 Dreaming findings & pending human approvals (if any in `HYGIENE_REPORT.md`)
- 🟡 Identified open anomalies or unlinked files (if any)
