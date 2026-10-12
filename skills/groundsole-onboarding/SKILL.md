---
name: groundsole-onboarding
description: Interaktives, kognitives Onboarding und Tutorial für neue Groundsole-Nutzer. Erklärt den Unterschied zwischen Agentic Harness und Webchat, das lokale Langzeitgedächtnis, Single-Stream Chat-Hygiene und Markdown als SSOT.
---

# Groundsole Onboarding & Tutorial Skill

Dieser Skill führt neue Nutzer (Schüler, Wissensarbeiter, Unternehmer oder Entwickler) in einer warmen, verständlichen und interaktiven Schritt-für-Schritt-Reise in die Funktionsweise ihres neuen sovereignen KI-Arbeitsplatzes ein.

---

## 🎯 Auslöser (Wann dieser Skill aktiv wird)

1. **Nach der Ersteinrichtung:** Wird am Ende von `bootstrap.md` automatisch vorgeschlagen:
   > *„Möchtest du eine kurze, 3-minütige Einführung machen, wie wir ab sofort zusammenarbeiten?“*
2. **Auf expliziten Nutzer-Wunsch:** Wenn der Nutzer schreibt:
   * *„Wie funktioniert Groundsole eigentlich?“*
   * *„Gib mir ein Tutorial / Onboarding“*
   * *„Erkläre mir mein neues System“*
   * *„/onboarding“*

---

## 🧭 Didaktische Leitlinien für die KI

* **Einfache, menschliche Sprache:** Verwende **keinerlei unverständlichen Entwickler-Jargon** (vermeide Begriffe wie *„Inferenz-Puffer“*, *„Vektor-Sharding“*, *„FastEmbed“*, *„CORS“* oder *„Token-Latenz“*).
* **Interaktivität statt Textwüste:** Schütte den Nutzer nicht mit 5 Seiten Text auf einmal zu! Gehe die Stationen **Schritt für Schritt im Dialog** durch. Stelle nach jedem Schritt eine kurze Frage oder lass den Nutzer kurz reagieren.
* **Bodenkontakt:** Jeder Schritt muss sofort mit dem praktischen Alltag des Nutzers verknüpft sein.

---

## 🗺️ Die 4 Stationen des Onboardings

### Station 1: Was ist ein „Agentic Harness“ (und der Unterschied zu ChatGPT im Browser)?

**Dialog-Einstieg:**
> *„Willkommen bei Groundsole! Bevor wir loslegen: Weißt du schon, was der entscheidende Unterschied zwischen deiner Software hier (deinem sogenannten ‚Agentic Harness‘ wie Antigravity, Hermes oder Claude Code) und einem normalen Webchat wie ChatGPT im Browser ist?“*

**Erklärung nach der Nutzer-Antwort:**
* **Der normale Webchat (ChatGPT / Claude.ai im Browser):**  
  Läuft in einer isolierten Wolke im Internet. Er kann deine Festplatte nicht berühren, keine echten Dokumente öffnen, keine lokalen Skripte ausführen und vergisst im Grunde alles, sobald du das Fenster schließt.
* **Dein Agentic Harness (hier auf deinem Laptop):**  
  Läuft **direkt auf deinem Rechner**. Er ist dein Werkzeug-Träger: Er hat direkten Zugriff auf deine lokalen Arbeitsordner, kann Skripte ausführen, echte Word-, PDF- und Präsentations-Dateien erstellen und offline arbeiten.
* **Das Problem bisher:** Eine solche Software ist nach der Installation **völlig leer**.
* **Hier kommt Groundsole ins Spiel:** Groundsole ist das Betriebssystem und das Gedächtnis, das dieser leeren Hülle Struktur, Verstand und Werkzeuge verleiht.

---

### Station 2: Das Langzeitgedächtnis (Nie wieder bei null anfangen)

**Dialog-Einstieg:**
> *„Kennst du das Frustgefühl bei normalen KIs, dass man ihnen jeden Tag aufs Neue erklären muss, wer man ist, woran man arbeitet und welche Regeln gelten? Bei Groundsole ist das dauerhaft gelöst.“*

**Erklärung der 2 Gedächtnis-Ebenen:**
1. **Automatischer Faktenspeicher:**  
   Wann immer du mir eine wichtige persönliche Information, eine feste Entscheidung oder eine Regel nennst (z. B. *„Ich trinke keinen Kaffee mehr“*, *„Mein Kollege heißt Alex“*, *„Projekt X hat Deadline Ende November“*), merke ich mir das automatisch in deiner lokalen Datenbank. Wenn du morgen einen neuen Chat öffnest, weiß ich das immer noch.
2. **Deine Lebens- & Arbeitsmodule (`00_MEMORY/modules/`):**  
   Alles hat einen festen Ort. Es gibt strukturierte Textdateien für deine Projekte, deine Finanzen oder deine Schulfächer. Wir müssen nichts suchen – es existiert immer nur eine einzige verbindliche Wahrheit.
3. **100 % lokal & privat:**  
   Dein Gedächtnis liegt auf deiner eigenen Festplatte. Keine fremde Cloud liest mit.

---

### Station 3: Single-Stream & Chat-Hygiene (Wie reden wir miteinander?)

**Dialog-Einstieg:**
> *„Jetzt zur wichtigsten Gewohnheit im Alltag: Wie führen wir unsere Chats?“*

**Erklärung:**
1. **Kein Chat-Chaos mehr:**  
   Du musst nicht für jeden kleinen Gedanken oder jede Frage ein neues Chatfenster aufmachen. Du kannst tagelang entspannt in einem einzigen durchgehenden Gespräch arbeiten.
2. **Wann ist ein neuer Chat sinnvoll?**  
   Nur wenn du ein völlig neues Großthema beginnst (z. B. ein komplett neues Projekt oder ein anderes Schulfach). Das hält deinen Fokus und den der KI messerscharf.
3. **Das Archivieren („Chat archivieren“):**  
   Wenn ein großes Thema abgeschlossen ist oder der Chat sehr lang geworden ist, sagst du mir einfach: **„Chat archivieren“**.  
   *Was passiert dann?*  
   Ich reinige das Gespräch von technischem Ballast und speichere das Protokoll als saubere, lesbare Textdatei (`.md`) lokal auf deinem Laptop in deinem Archiv (`00_MEMORY/transcripts/`).  
   So geht dir niemals ein wertvoller Gedanke verloren, und dein Arbeitsplatz bleibt federleicht.

---

### Station 4: Markdown als Single Source of Truth & Werkzeuge auf Zuruf

**Dialog-Einstieg:**
> *„Zum Schluss: Wie erstellen wir Dokumente und Folien?“*

**Erklärung:**
* Bei Groundsole musst du dich nie wieder mit zerschossenen Layouts in Word oder PowerPoint herumärgern.
* Alle Inhalte leben in einfachen Textdateien (Markdown). Du kannst sie in jedem Texteditor bearbeiten.
* **Auf Zuruf erzeuge ich daraus fertige Endprodukte:**
  * **Word-Dateien:** *„Erstelle mir ein Word-Dokument aus dieser Notiz.“* ➔ Erzeugt saubere `.docx`-Dateien.
  * **PDFs:** *„Mache daraus ein druckreifes PDF.“* ➔ Erzeugt A4-Dokumente mit Deckblatt und Inhaltsverzeichnis.
  * **16:9 Präsentationen:** *„Mach mir Folien zu Thema X.“* ➔ Erzeugt eine interaktive HTML-Präsentation, deren Text du direkt in der `.md`-Datei anpassen kannst.

---

## 🚀 Abschluss & Erste Praxisübung

Schließe das Onboarding mit einer kleinen, motivierenden Mitmach-Aufgabe ab:

> *„🎉 Das war schon das ganze Geheimnis! Du hast jetzt einen echten, mitdenkenden Koprozessor an deiner Seite.  
>  
> Wollen wir direkt eine kleine Praxisübung machen? Du kannst dir aussuchen:  
> 1. **Gedächtnis-Test:** Verrate mir einen Fakt über dich oder dein aktuelles Lieblingsprojekt, den ich mir dauerhaft merken soll.  
> 2. **Dokumenten-Test:** Lass uns aus deinen Notizen ein erstes schickes PDF oder Word-Dokument erzeugen.  
> 3. **Direkt loslegen:** Sag mir einfach, woran du heute arbeiten möchtest!“*
