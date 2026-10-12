# Groundsole ISN — Architektur für souveräne KI-Koprozessoren

> **Betriebssystem für den agentischen KI-Arbeitsplatz bei ISN (innovation service network GmbH)**  
> *Biophysikalische Kausalität, Plaintext-Markdown SSOT, lokales Vektorgedächtnis (Jina-Embeddings) & Hub-and-Spoke Wissenskristallisation.*

---

## 💡 Leitphilosophie: Autonomie am Spoke, Ordnung am Hub

Groundsole ISN verbindet die Freiheit der persönlichen Arbeitsweise am eigenen Rechner mit der geordneten, verlässlichen Wissensbasis der gesamten Organisation:

1. **Der Spoke (Persönlicher Laptop & OneDrive):**  
   * **Pfad:** `C:\Users\<username>\OneDrive - isn - innovation service network\ISN-AI\`
   * **Funktion:** Geschützter, privater Arbeitsbereich. Hier liegen persönliche Gedanken, Entwürfe, transkribierte Notizen und die **lokale Vektordatenbank (`isn_vectors.db`)** mit Jina-Embeddings.
2. **Der Hub (Geteilter SharePoint):**  
   * **Pfad:** `Sharepoint - Dokumente\Wissensdatenbank\AI_HUB\`
   * **Funktion:** Geteiltes Firmen-Gedächtnis. Besteht **ausschließlich aus Plaintext-Markdown-Dateien** (`00` bis `05` Dossiers, `AGENTS.md`, `TEAM_FEED.md`).
   * **Verbot von Cloud-DBs:** Auf dem SharePoint liegen **keine SQLite-Vektordatenbanken**, um Dateikonflikte und File-Locking bei M365-Syncs zu 100 % auszuschließen.
3. **Kristallisation (Gezielter Wissenstransfer):**  
   * Die Mitarbeiterin entscheidet selbst, was aus ihrer täglichen Arbeit in den gemeinsamen Wissenshub fließt. Über den Befehl *"Kristallisiere für ISN"* wird relevantes Wissen gefiltert (Privacy & Reflexions-Gate) und als strukturiertes Markdown im SharePoint abgelegt.

---

## 🚀 Grundsätze (Die 3 Säulen)

1. **Biophysikalische Kausalität (The Ground Test):**  
   Analyse und Planung orientieren sich an harten Fakten: Zeitbudget, verfügbare Hardware, RAM, Verträge und reale Fristen.
2. **Strikte IST-Stand-Pflicht:**  
   Nur was in funktionierendem Code oder existierenden Dokumenten vorliegt, gilt als IST-Stand. Konzepte werden explizit mit `[KONZEPT / GEPLANT]` gekennzeichnet.
3. **Plaintext-Markdown als SSOT:**  
   Wissen liegt unverschlüsselt in offenem Markdown vor – durchsuchbar mit `ripgrep`, versionierbar mit `git`.
