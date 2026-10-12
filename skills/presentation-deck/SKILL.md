---
name: presentation-deck
description: Erstellt und bearbeitet autarke, interaktive 16:9 HTML-Präsentationen mit Markdown als Single Source of Truth (SSOT). Bietet gestochen scharfes, minimalistisches Design, Drag & Drop Live-Aktualisierung und native Tastatur-Navigation.
---

# Presentation Deck Skill (Groundsole Core)

Dieser Skill ist der verbindliche Standard zur Erstellung professioneller, interaktiver Präsentationen im 16:9 Format. Er basiert auf dem architektonischen Prinzip von **Markdown als Single Source of Truth (SSOT)**: Der Vortragende behält die volle Kontrolle über den Text in einer einfachen `.md`-Datei, während eine autarke HTML-Datei die visuelle Darstellung deterministisch und ohne Abhängigkeiten rendert.

---

## 🏛️ Das Groundsole-Architekturprinzip: Markdown als SSOT

Präsentationen in Groundsole werden **niemals als statischer HTML-Code oder proprietäre Binärdateien** gepflegt.

1. **Trennung von Inhalt und Form:**
   * Der gesamte Inhalt (Titel, Thesen, Spalten, Zitate) lebt ausschließlich in einer `.md`-Datei (z. B. `Projekt_Praesentation.md`).
   * Der Nutzer kann den Text jederzeit mit jedem beliebigen Texteditor öffnen, überarbeiten oder erweitern – ohne Risiko, Layouts zu zerstören.
2. **Deterministisches Rendering:**
   * Die Datei `Projekt_Praesentation.html` bindet das Markdown ein und rendert die Folien dynamisch im Browser.
3. **Drei nahtlose Synchronisations-Wege:**
   * **Natives Drag & Drop:** Wenn die Präsentation lokal im Browser geöffnet ist, zieht der Nutzer die `.md`-Datei einfach mit der Maus ins Fenster – die Folien aktualisieren sich sofort live.
   * **Live-Watcher:** Der Befehl `python3 tools/scripts/sync_slides.py [Datei.md] --watch` überwacht die `.md`-Datei und aktualisiert das HTML bei jedem Speichern (`Cmd+S` / `Ctrl+S`).
   * **Lokaler Server:** `python3 tools/scripts/sync_slides.py [Datei.md] --serve` startet einen lokalen Server mit Live-Reload.

---

## 🗣️ Interaktions-Protokoll: So führt die KI den Nutzer

Wenn ein Nutzer sagt: *„Erstelle mir eine Präsentation über Thema X“* oder *„Mach mir Folien zu Y“*, agiert die KI niemals als hastiger Code-Generator, sondern führt den Nutzer aktiv durch das architektonische Groundsole-Prinzip:

### Schritt 1: Das kognitive Framing & Storyline abstimmen (Storyline First)
Die KI beginnt nicht mit Folien, sondern klärt in 2–3 Sätzen das große Bild:
> *„Bevor wir Folien gestalten: Was ist das Ziel deines Vortrags? Wo knüpft dein Publikum an und welche Kernbotschaft soll am Ende hängenbleiben?“*

### Schritt 2: Das Markdown Single-Source-of-Truth Prinzip erklären
Sobald das Narrativ freigegeben ist, erstellt die KI die `.md`-Datei und erklärt dem Nutzer transparent, warum dies die überlegene Arbeitsweise ist:
> *„Ich habe deine Präsentation als strukturierte Markdown-Datei `[Titel].md` angelegt.  
> **Das Groundsole-Prinzip:** Der Text in der `.md`-Datei ist deine einzige Wahrheit (Single Source of Truth). Du musst kein HTML anfassen – du kannst den Text, die Spalten und Aufzählungspunkte jederzeit direkt in deinem Texteditor bearbeiten.  
> Die zugehörige HTML-Datei `[Titel].html` rendert daraus automatisch deine 16:9 Präsentation.“*

### Schritt 3: Den interaktiven Abgleich aufzeigen
Die KI erklärt dem Nutzer kurz die 3 Möglichkeiten zur Vorschau (Drag & Drop ins Browserfenster, Live-Watcher via `sync_slides.py --watch` oder lokaler Server).

---

## 🎨 Neutrales Design-System (16:9 Minimalist Slate)

* **Canvas Hintergrund:** `#FFFFFF` (Reinweiß)
* **Primärfarbe (Titel & Fließtext):** `#0F172A` (Deep Slate / Charcoal)
* **Akzentfarbe (Highlights, Untertitel, Sub-Bullets):** `#2563EB` (Klares Indigo-Blau)
* **Muted Text:** `#475569` (Slate 600)
* **Akzent-Grau (Header, Meta, Linien):** `#94A3B8` (Slate 400)
* **Borders & Trennlinien:** `#E2E8F0` (Slate 200)
* **Dark Statement-Box:** `#0F172A` mit weißem Text `#FFFFFF`
* **Typografie:**
  * Fließtext & Headlines: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
  * Monospace (Header, Meta, Zähler): `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`

---

## 🛠️ Universelles HTML/CSS/JS Template

Dieses Template ist 100 % autark, benötigt keine externen CDNs oder Schrift-Downloads und funktioniert offline auf Mac, Windows und Linux:

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Präsentationstitel]</title>
  
  <style>
    :root {
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

      --bg-canvas: #FFFFFF;
      --color-primary: #0F172A;
      --color-secondary: #2563EB;
      --color-accent: #94A3B8;
      --color-muted: #475569;
      --color-light: #94A3B8;
      --color-border: #E2E8F0;
      --color-dark-box: #0F172A;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      width: 100vw;
      height: 100vh;
      background-color: var(--bg-canvas);
      color: var(--color-primary);
      font-family: var(--font-sans);
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    #stage {
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }

    .slide {
      position: absolute;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      padding: 6vh 8vw 8vh 8vw;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
      transition: opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      transform: scale(0.99);
    }

    .slide.active {
      opacity: 1;
      visibility: visible;
      pointer-events: auto;
      transform: scale(1);
    }

    .slide-header {
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: var(--font-mono);
      font-size: clamp(0.75rem, 0.9vw, 0.85rem);
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--color-accent);
    }

    .slide-header::before {
      content: "";
      width: 20px;
      height: 2px;
      background: var(--color-secondary);
      display: inline-block;
    }

    .slide-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 2vh 0;
    }

    h1.display-title {
      font-size: clamp(2.6rem, 5vw, 4.4rem);
      font-weight: 700;
      color: var(--color-primary);
      line-height: 1.08;
      letter-spacing: -0.03em;
      margin-bottom: 20px;
    }

    h2.display-title {
      font-size: clamp(2rem, 3.6vw, 3.2rem);
      font-weight: 700;
      color: var(--color-primary);
      line-height: 1.15;
      letter-spacing: -0.025em;
      margin-bottom: 20px;
    }

    .subtitle-italic {
      font-style: italic;
      font-size: clamp(1.2rem, 1.8vw, 1.6rem);
      color: var(--color-secondary);
      line-height: 1.35;
      margin-bottom: 28px;
      font-weight: 400;
    }

    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4.5vw; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3.5vw; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.5vw; }

    .col-card {
      display: flex;
      flex-direction: column;
    }

    .accent-bar { width: 32px; height: 3px; background: var(--color-secondary); margin-bottom: 16px; border-radius: 2px; }

    .col-title {
      font-size: clamp(1.15rem, 1.5vw, 1.45rem);
      font-weight: 700;
      color: var(--color-primary);
      margin-bottom: 12px;
      line-height: 1.25;
      letter-spacing: -0.01em;
    }

    .col-content {
      font-size: clamp(0.95rem, 1.15vw, 1.08rem);
      color: var(--color-muted);
      line-height: 1.55;
      font-weight: 400;
    }

    .col-content ul {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .col-content li {
      position: relative;
      padding-left: 18px;
    }

    .col-content li::before {
      content: "—";
      position: absolute;
      left: 0;
      color: var(--color-light);
      font-weight: 700;
    }

    .col-content li.sub-item {
      padding-left: 24px;
      font-size: 0.88em;
      opacity: 0.95;
    }

    .col-content li.sub-item::before {
      content: "↳";
      left: 8px;
      color: var(--color-secondary);
      font-weight: 700;
    }

    .statement-card {
      background: var(--color-dark-box);
      color: #FFFFFF;
      padding: 44px 52px;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      min-height: 220px;
    }

    .statement-card .card-quote {
      font-size: clamp(1.4rem, 2.2vw, 2.1rem);
      font-weight: 500;
      line-height: 1.35;
      color: #FFFFFF;
      font-style: italic;
    }

    .slide-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid var(--color-border);
      padding-top: 16px;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--color-light);
    }

    .controls {
      position: fixed;
      bottom: 2vh;
      right: 3vw;
      display: flex;
      gap: 8px;
      z-index: 100;
      opacity: 0.25;
      transition: opacity 0.2s;
    }
    .controls:hover { opacity: 1; }

    .ctrl-btn {
      background: #FFFFFF;
      border: 1px solid var(--color-border);
      color: var(--color-primary);
      width: 36px;
      height: 36px;
      border-radius: 6px;
      cursor: pointer;
      font-family: var(--font-mono);
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s;
    }
    .ctrl-btn:hover { color: var(--color-secondary); border-color: var(--color-secondary); }

    .sync-toast {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--color-primary);
      color: #FFFFFF;
      padding: 10px 22px;
      border-radius: 24px;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      letter-spacing: 0.06em;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.25);
      z-index: 300;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .sync-toast.show { opacity: 1; transform: translateX(-50%) translateY(5px); }
  </style>
</head>
<body>

  <div id="stage">
    <!-- Folien werden hier dynamisch gerendert -->
  </div>

  <div class="controls">
    <button class="ctrl-btn" onclick="prevSlide()" title="Zurück (←)">←</button>
    <button class="ctrl-btn" onclick="toggleFullScreen()" title="Vollbild (F)">⛶</button>
    <button class="ctrl-btn" onclick="nextSlide()" title="Weiter (→)">→</button>
  </div>

  <!-- Eingebettete Single Source of Truth (Fallback & Direkt-Rendering für file://) -->
  <script type="text/markdown" id="markdown-source">
# Folie 1: Titelfolie
* **Kopfzeile:** DOKUMENTATION · VORTRAG
* **Titel:** Präsentationstitel
* **Untertitel:** Eine klare, prägnante Einordnung des Themas
* **Autor:** Name des Autors

---

# Folie 2: Kernbereiche
* **Kopfzeile:** 02 · SYSTEMATIK
* **Titel:** Struktur und Hauptsäulen
* **Untertitel:** Wie sich die Komponenten logisch aufteilen.
* **Layout:** Grid 2 Spalten

### Spalte 1: Säule A
* Erster wesentlicher Aspekt
  - Vertiefendes Detail oder Parameter
* Praktische Konsequenz

### Spalte 2: Säule B
* Zweiter wesentlicher Aspekt
* Handlungsoption oder Meilenstein
  </script>

  <script>
    async function loadAndRenderDeck() {
      let mdText = "";
      try {
        const mdFileName = window.location.pathname.split("/").pop().replace(/\.html$/, ".md");
        const response = await fetch(mdFileName + "?t=" + Date.now());
        if (response.ok) {
          mdText = await response.text();
        } else {
          mdText = document.getElementById("markdown-source").textContent;
        }
      } catch (e) {
        mdText = document.getElementById("markdown-source").textContent;
      }

      renderSlides(mdText);
    }

    function renderSlides(rawMd) {
      const stage = document.getElementById("stage");
      stage.innerHTML = "";

      const rawChunks = rawMd.split(/\n\s*---\s*\n/);
      const slideChunks = rawChunks.filter(c => /##\s*Folie|<!--\s*SLIDE|\[Header:|#\s*Folie/i.test(c));
      const total = slideChunks.length;

      slideChunks.forEach((rawSlide, idx) => {
        const slideNum = idx + 1;
        const slideEl = document.createElement("section");
        slideEl.className = "slide";
        slideEl.dataset.slide = slideNum;
        if (slideNum === 1) slideEl.classList.add("active");

        const headerMatch = rawSlide.match(/\*\s*\*\*Kopfzeile:\*\*\s*(.*)/i) || rawSlide.match(/\[Header:\s*(.*?)\]/i);
        const titleMatch = rawSlide.match(/\*\s*\*\*Titel:\*\*\s*(.*)/i) || rawSlide.match(/\[Title:\s*(.*?)\]/i) || rawSlide.match(/^##?\s+(?:Folie\s*\d+:?\s*)?(.*)/m);
        const subMatch = rawSlide.match(/\*\s*\*\*Untertitel:\*\*\s*(.*)/i) || rawSlide.match(/\[Subtitle:\s*(.*?)\]/i);
        const layoutMatch = rawSlide.match(/\*\s*\*\*Layout:\*\*\s*(.*)/i) || rawSlide.match(/\[Layout:\s*(.*?)\]/i);
        const quoteMatch = rawSlide.match(/\*\s*\*\*Zitat:\*\*\s*(.*)/is) || rawSlide.match(/\[Quote:\s*(.*?)\]/is);
        const metaMatch = rawSlide.match(/\*\s*\*\*Autor:\*\*\s*(.*)/i) || rawSlide.match(/\[Meta:\s*(.*?)\]/i);

        const headerText = headerMatch ? headerMatch[1].trim() : `FOLIE ${String(slideNum).padStart(2, "0")}`;
        const titleText = titleMatch ? titleMatch[1].trim() : "";
        const subText = subMatch ? subMatch[1].trim() : "";
        const layout = layoutMatch ? layoutMatch[1].trim().toLowerCase() : "standard";

        let bodyHtml = "";

        if (slideNum === 1) {
          bodyHtml = `
            <div class="slide-body">
              <h1 class="display-title">${titleText}</h1>
              ${subText ? `<div class="subtitle-italic">${subText}</div>` : ""}
              ${metaMatch ? `<div style="font-family: var(--font-mono); font-size: 0.9rem; color: var(--color-light); letter-spacing: 0.1em; text-transform: uppercase;">${metaMatch[1]}</div>` : ""}
            </div>
          `;
        } else if (layout.includes("statement") || quoteMatch) {
          const qText = quoteMatch ? quoteMatch[1].replace(/^[„"']|[“"']$/g, "").trim() : titleText;
          bodyHtml = `
            <div class="slide-body">
              <div class="statement-card">
                <div class="card-quote">„${qText}“</div>
              </div>
            </div>
          `;
        } else {
          const colSplit = rawSlide.split(/\n(?=###\s+|\[Col:\s*)/);
          
          if (colSplit.length > 1) {
            let colCards = "";
            let colCount = 0;

            for (let i = 1; i < colSplit.length; i++) {
              const chunk = colSplit[i].trim();
              if (!chunk.startsWith("###") && !chunk.startsWith("[Col:")) continue;
              colCount++;

              const firstLineEnd = chunk.indexOf("\n");
              const rawHeading = firstLineEnd !== -1 ? chunk.substring(0, firstLineEnd) : chunk;
              const restContent = firstLineEnd !== -1 ? chunk.substring(firstLineEnd).trim() : "";

              const colTitle = rawHeading.replace(/^(?:###\s*(?:Spalte\s*\d+:?\s*)?|\[Col:\s*)/i, "").replace(/\]$/, "").trim();

              const lines = restContent.split("\n");
              let listHtml = "";

              lines.forEach(line => {
                const trimmed = line.trim();
                if (!trimmed) return;

                let formatted = trimmed.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

                if (line.startsWith("  -") || line.startsWith("    -") || line.startsWith("  *")) {
                  formatted = formatted.replace(/^[-*]\s+/, "");
                  listHtml += `<li class="sub-item">${formatted}</li>`;
                } else if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
                  formatted = formatted.replace(/^[-*]\s+/, "");
                  listHtml += `<li>${formatted}</li>`;
                } else {
                  listHtml += `<div style="margin-bottom: 8px;">${formatted}</div>`;
                }
              });

              colCards += `
                <div class="col-card">
                  <div class="accent-bar"></div>
                  <div class="col-title">${colTitle}</div>
                  <div class="col-content">
                    <ul>${listHtml}</ul>
                  </div>
                </div>
              `;
            }

            let gridClass = "grid-3";
            if (layout.includes("4") || colCount === 4) gridClass = "grid-4";
            else if (layout.includes("2") || colCount === 2) gridClass = "grid-2";

            bodyHtml = `
              <div class="slide-body">
                <h2 class="display-title">${titleText}</h2>
                ${subText ? `<div class="subtitle-italic">${subText}</div>` : ""}
                <div class="${gridClass}">${colCards}</div>
              </div>
            `;
          } else {
            bodyHtml = `
              <div class="slide-body">
                <h2 class="display-title">${titleText}</h2>
                ${subText ? `<div class="subtitle-italic">${subText}</div>` : ""}
              </div>
            `;
          }
        }

        slideEl.innerHTML = `
          <div class="slide-header">${headerText}</div>
          ${bodyHtml}
          <div class="slide-footer">
            <div>GROUNDSOLE PRESENTER</div>
            <div>${String(slideNum).padStart(2, "0")} / ${String(total).padStart(2, "0")}</div>
          </div>
        `;

        stage.appendChild(slideEl);
      });

      initControls();
    }

    let currentSlide = 1;
    let totalSlides = 1;

    function initControls() {
      const slides = document.querySelectorAll(".slide");
      totalSlides = slides.length;
      updateDeck();
    }

    function updateDeck() {
      const slides = document.querySelectorAll(".slide");
      slides.forEach((slide, index) => {
        if (index + 1 === currentSlide) {
          slide.classList.add("active");
        } else {
          slide.classList.remove("active");
        }
      });
    }

    function nextSlide() {
      if (currentSlide < totalSlides) {
        currentSlide++;
        updateDeck();
      }
    }

    function prevSlide() {
      if (currentSlide > 1) {
        currentSlide--;
        updateDeck();
      }
    }

    function toggleFullScreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        if (document.exitFullscreen) document.exitFullscreen();
      }
    }

    window.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        nextSlide();
      } else if (e.key === "ArrowLeft" || e.key === "PageUp" || e.key === "Backspace") {
        e.preventDefault();
        prevSlide();
      } else if (e.key.toLowerCase() === "f") {
        toggleFullScreen();
      } else if (e.key === "Home") {
        currentSlide = 1;
        updateDeck();
      } else if (e.key === "End") {
        currentSlide = totalSlides;
        updateDeck();
      }
    });

    function showToast(message) {
      let toast = document.getElementById("sync-toast");
      if (!toast) {
        toast = document.createElement("div");
        toast.id = "sync-toast";
        toast.className = "sync-toast";
        document.body.appendChild(toast);
      }
      toast.textContent = message;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 2500);
    }

    // Drag & Drop für direktes Live-Parsing von .md-Dateien
    window.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "copy";
    });

    window.addEventListener("drop", (e) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.endsWith(".md") || file.name.endsWith(".txt")) {
          const reader = new FileReader();
          reader.onload = (event) => {
            renderSlides(event.target.result);
            showToast("✨ Live geladen: " + file.name);
          };
          reader.readAsText(file);
        }
      }
    });

    document.addEventListener("DOMContentLoaded", loadAndRenderDeck);
  </script>
  <div id="sync-toast" class="sync-toast"></div>
</body>
</html>
```

---

## 🔒 Verbindliche Arbeits- und Sicherheitsregeln

1. **Text-First & Storyline-Freigabe:** Vor der Generierung einer HTML-Präsentation MÜSSEN zwingend die Storyline (in 3–5 Sätzen) und die Folientexte in reinem Text zur expliziten Freigabe vorgelegt werden.
2. **Markdown als Single Source of Truth (SSOT):** Jede Präsentation basiert zwingend auf einer `.md`-Datei, die der Nutzer direkt im Texteditor bearbeiten kann.
3. **Strikter Schutz bestehender Arbeitsdateien:** Bestehende `.md`-Dateien dürfen niemals durch blindes Überschreiben mit `write_to_file` ersetzt werden. Immer erst den aktuellen Stand einlesen und Änderungen gezielt vornehmen.
4. **Anti-Widerspruchs-Check bei externen Quellen:** Aussagen auf Folien dürfen niemals im scheinbaren Widerspruch zu optischen Belegquellen (wie Studien oder Tabellen) stehen. Differenzierungen müssen kontextuell so eingeführt werden, dass die Folie die Quelle stützt und nicht verwirrt.
