#!/usr/bin/env python3
"""
sync_slides.py - Groundsole Single Source of Truth Presentation Synchronizer

Synchronisiert eine Markdown-Quelldatei (.md) 1:1 in die entsprechende interaktive
HTML-Präsentationsdatei (.html), damit auch beim lokalen Öffnen über file:// alle
Inhalte deterministisch, offline und ohne CORS-Einschränkungen dargestellt werden.

Verwendung:
  python3 sync_slides.py [Pfad/zur/Datei.md]
  python3 sync_slides.py [Pfad/zur/Datei.md] --watch
  python3 sync_slides.py [Pfad/zur/Datei.md] --serve
"""

import sys
import os
import re
import time
import argparse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

def sync_md_to_html(md_path: str) -> bool:
    if not os.path.isfile(md_path):
        print(f"❌ Fehler: Markdown-Datei nicht gefunden: {md_path}")
        return False

    html_path = os.path.splitext(md_path)[0] + ".html"
    if not os.path.isfile(html_path):
        print(f"❌ Fehler: Zugehörige HTML-Datei nicht gefunden: {html_path}")
        return False

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Regex für <script type="text/markdown" id="markdown-source">...</script>
    pattern = r'(<script\s+type=["\']text/markdown["\']\s+id=["\']markdown-source["\']>)(.*?)(<\/script>)'
    
    if not re.search(pattern, html_content, flags=re.DOTALL):
        print(f"❌ Fehler: Kein <script type=\"text/markdown\" id=\"markdown-source\"> in {html_path} gefunden.")
        return False

    # Ersetze den Inhalt sauber
    new_html = re.sub(
        pattern,
        r'\1\n' + md_content.replace('\\', '\\\\') + r'\n  \3',
        html_content,
        flags=re.DOTALL
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] ✅ Synchronisiert: {os.path.basename(md_path)} ➔ {os.path.basename(html_path)}")
    return True

def watch_file(md_path: str):
    print(f"👀 Live-Watcher aktiv für: {os.path.basename(md_path)}")
    print("   Speichere deine Änderungen in der .md-Datei im Texteditor; HTML wird sofort synchronisiert.")
    print("   Beenden mit Ctrl+C\n")
    
    last_mtime = os.stat(md_path).st_mtime
    sync_md_to_html(md_path)
    
    try:
        while True:
            time.sleep(0.5)
            try:
                current_mtime = os.stat(md_path).st_mtime
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    sync_md_to_html(md_path)
            except FileNotFoundError:
                pass
    except KeyboardInterrupt:
        print("\n👋 Live-Watcher beendet.")

def serve_directory(directory: str, filename: str, port: int = 8080):
    os.chdir(directory)
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("localhost", port), handler)
    url = f"http://localhost:{port}/{filename}"
    print(f"🌐 Lokaler Server gestartet: {url}")
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.3)
    webbrowser.open(url)

def main():
    parser = argparse.ArgumentParser(description="Synchronisiert Markdown-Präsentationen in HTML")
    parser.add_argument("file", help="Pfad zur .md Datei")
    parser.add_argument("--watch", "-w", action="store_true", help="Kontinuierliche Überwachung bei Dateiänderungen")
    parser.add_argument("--serve", "-s", action="store_true", help="Lokalen Webserver starten und Browser öffnen")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port für lokalen Server (Standard: 8080)")

    args = parser.parse_args()
    md_path = os.path.abspath(args.file)

    if args.serve:
        sync_md_to_html(md_path)
        directory = os.path.dirname(md_path)
        html_name = os.path.splitext(os.path.basename(md_path))[0] + ".html"
        serve_directory(directory, html_name, args.port)
        if args.watch:
            watch_file(md_path)
        else:
            print("Drücke Ctrl+C zum Beenden des Servers...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nServer beendet.")
    elif args.watch:
        watch_file(md_path)
    else:
        sync_md_to_html(md_path)

if __name__ == "__main__":
    main()
