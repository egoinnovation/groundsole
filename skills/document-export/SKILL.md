---
name: document-export
description: "Generates formatted Microsoft Word (.docx) documents and print-ready PDFs from Markdown notes, essays, or project reports."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, document, pdf, word, docx, export]
---

# Document Export Skill

This skill enables the AI coprocessor to export Markdown notes, school assignments, or project reports into polished Microsoft Word (`.docx`) or print-ready PDF files.

---

## Trigger Conditions

Activate this skill when:
- The user asks: *"Export this as a Word document"*, *"Create a PDF from..."*, *"Make a .docx file for school / work"*, or *"Generate a PDF"*.

---

## 🛠️ Execution Commands

### 1. Export to Microsoft Word (.docx)
Converts Markdown headings, bullet points, and paragraphs into a clean Word document:
```bash
python3 scripts/document_exporter.py docx [input.md] [output.docx]
```
*(Requires `python-docx` installed in `.local/venv`)*.

### 2. Export to Print-Ready PDF (.pdf)
Generates an A4 vector PDF using the system's browser engine (Edge on Windows, Chrome on Mac/Linux):
```bash
python3 scripts/document_exporter.py pdf [input.md] [output.pdf]
```
