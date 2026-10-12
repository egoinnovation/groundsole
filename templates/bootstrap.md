# Groundsole ISN — Master Bootstrap

> **ANWEISUNG FÜR DEN KI-ASSISTENTEN (Hermes Agent, Antigravity, Claude, Codex etc.):**  
> Wenn der Nutzer den Befehl gibt:  
> **„Lies bootstrap.md und richte mein ISN-System ein“**  
> (oder diese Datei / URL geladen wird), führe die folgende Einrichtung Schritt für Schritt autonom aus.  
>  
> **Tonalität & Sprache:**  
> Sprich mit dem Nutzer in einer einfachen, klaren, professionellen Alltagssprache (Deutsch).  
> Vermeide unnötigen Entwickler-Jargon. Erkläre alle Schritte verständlich.

---

## Schritt 1: Lokales Spoke-Verzeichnis (OneDrive) verknüpfen

1. Prüfe, ob das persönliche Spoke-Verzeichnis existiert:  
   `C:\Users\<username>\OneDrive - isn - innovation service network\ISN-AI\`
2. Falls nicht vorhanden, führe das Setup-Skript aus:  
   `python tools/setup_spoke.py`
3. Stelle sicher, dass die lokale Starterdatei `AGENTS.md` verknüpft ist.

---

## Schritt 2: Geteilten Firmen-Hub (SharePoint) einlesen

1. Lies die zentrale Governance aus dem SharePoint `AI_HUB`:  
   `..\..\isn - innovation service network\Sharepoint - Dokumente\Wissensdatenbank\AI_HUB\AGENTS.md`
2. Mache dich mit den Firmen-Dossiers (`00_ISN_PROFIL...` bis `05_KUNDEN...`) vertraut.

---

## Schritt 3: Lokales Vektor-Gedächtnis aktivieren

1. Prüfe den Speicherordner `00_MEMORY` im Spoke-Verzeichnis.
2. Die lokale Vektordatenbank lautet `groundsole_memory.db` (nutzt FastEmbed mit `jinaai/jina-embeddings-v2-base-de`).
3. Vertrauliche Mitschriften und Arbeitsnotizen verbleiben strikt auf diesem lokalen Rechner.

---

## Schritt 4: Auf Framework-Updates prüfen

1. Führe das Update-Skript aus:  
   `python tools/check_update.py`
2. Falls eine neuere Version auf `github.com/egoinnovation/groundsole` vorliegt, frage den Nutzer höflich, ob neue Vorlagen und Skills aktualisiert werden sollen.
