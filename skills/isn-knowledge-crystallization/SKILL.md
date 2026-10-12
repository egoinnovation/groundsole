---
name: isn-knowledge-crystallization
description: Lokale Arbeitsergebnisse filtern und als kuratiertes Plaintext-Markdown für das SharePoint AI_HUB aufbereiten.
---

# ISN Knowledge Crystallization

Steuert die Übergabe von lokal erarbeiteten Erkenntnissen aus dem Spoke in den zentralen Firmen-Hub auf SharePoint (`AI_HUB`).

## Workflow:
1. **Auslöser:** Nutzer sendet den Befehl *"Kristallisiere für ISN"* oder fordert die Übernahme eines Dokuments an.
2. **Privacy & Reflexions-Gate:**
   * Entfernt persönliche Gefühle, vertrauliche Notizen und nicht verifizierte Annahmen.
   * Prüft Kausalität und Einhaltung der IST-Stand-Pflicht.
3. **Formatierung:** Erstellt sauberes, strukturiertes Plaintext-Markdown und fügt es in das passende Dossier (`00_ISN_PROFIL...` bis `05_KUNDEN...`) oder in `TEAM_FEED.md` ein.
