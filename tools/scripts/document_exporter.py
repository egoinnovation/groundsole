#!/usr/bin/env python3
"""
Groundsole Document Exporter
Converts Markdown documents into styled Microsoft Word (.docx) and PDF (.pdf) files.
"""

import sys
import os
import re
import subprocess
import shutil

def markdown_to_html(md_text: str, title: str = "Dokument") -> str:
    """Konvertiert Markdown-Text in ein sauberes, professionell gestaltetes HTML-Dokument."""
    lines = md_text.splitlines()
    html_body = []
    in_list = False
    in_table = False
    table_headers = []
    
    def format_inline(text: str) -> str:
        # Code
        text = re.sub(r'`([^`]+)`', r'<code style="background:#F1F5F9; color:#0F172A; padding:2px 4px; border-radius:3px; font-size:0.9em;">\1</code>', text)
        # Bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#2563EB;">\1</a>', text)
        return text

    for line in lines:
        line_str = line.strip()
        
        # Leere Zeile
        if not line_str:
            if in_list:
                html_body.append("</ul>")
                in_list = False
            if in_table:
                html_body.append("</table>")
                in_table = False
            continue

        # Überschriften
        if line_str.startswith("# "):
            if in_list: html_body.append("</ul>"); in_list = False
            if in_table: html_body.append("</table>"); in_table = False
            html_body.append(f'<h1 style="color:#0F172A; font-size:20pt; font-weight:bold; margin-top:18pt; margin-bottom:8pt; border-bottom:2px solid #E2E8F0; padding-bottom:4pt;">{format_inline(line_str[2:])}</h1>')
        elif line_str.startswith("## "):
            if in_list: html_body.append("</ul>"); in_list = False
            if in_table: html_body.append("</table>"); in_table = False
            html_body.append(f'<h2 style="color:#1E3A8A; font-size:15pt; font-weight:bold; margin-top:14pt; margin-bottom:6pt;">{format_inline(line_str[3:])}</h2>')
        elif line_str.startswith("### "):
            if in_list: html_body.append("</ul>"); in_list = False
            if in_table: html_body.append("</table>"); in_table = False
            html_body.append(f'<h3 style="color:#0F766E; font-size:12.5pt; font-weight:bold; margin-top:10pt; margin-bottom:4pt;">{format_inline(line_str[4:])}</h3>')
        elif line_str.startswith("#### "):
            if in_list: html_body.append("</ul>"); in_list = False
            if in_table: html_body.append("</table>"); in_table = False
            html_body.append(f'<h4 style="color:#334155; font-size:11pt; font-weight:bold; margin-top:8pt; margin-bottom:2pt;">{format_inline(line_str[5:])}</h4>')
        
        # Aufzählungslisten
        elif line_str.startswith("- ") or line_str.startswith("* "):
            if in_table: html_body.append("</table>"); in_table = False
            if not in_list:
                html_body.append('<ul style="margin-top:4pt; margin-bottom:6pt; padding-left:20pt; line-height:1.5;">')
                in_list = True
            html_body.append(f'<li style="margin-bottom:3pt;">{format_inline(line_str[2:])}</li>')
            
        # Zitate / Alerts
        elif line_str.startswith("> "):
            if in_list: html_body.append("</ul>"); in_list = False
            if in_table: html_body.append("</table>"); in_table = False
            html_body.append(f'<blockquote style="background:#F8FAFC; border-left:4px solid #3B82F6; margin:8pt 0; padding:8pt 12pt; color:#334155; font-style:italic;">{format_inline(line_str[2:])}</blockquote>')

        # Tabellen
        elif line_str.startswith("|") and line_str.endswith("|"):
            if in_list: html_body.append("</ul>"); in_list = False
            if "---" in line_str:
                continue
            cells = [c.strip() for c in line_str.split("|")[1:-1]]
            if not in_table:
                html_body.append('<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%; border:1px solid #CBD5E1; margin:10pt 0; font-size:10pt;">')
                in_table = True
                row_html = "".join([f'<th style="background:#F1F5F9; font-weight:bold; border:1px solid #CBD5E1; text-align:left;">{format_inline(c)}</th>' for c in cells])
                html_body.append(f'<tr>{row_html}</tr>')
            else:
                row_html = "".join([f'<td style="border:1px solid #CBD5E1;">{format_inline(c)}</td>' for c in cells])
                html_body.append(f'<tr>{row_html}</tr>')

        # Normale Absätze
        else:
            if in_list: html_body.append("</ul>"); in_list = False
            if in_table: html_body.append("</table>"); in_table = False
            html_body.append(f'<p style="margin-top:4pt; margin-bottom:6pt; line-height:1.5; color:#1E293B;">{format_inline(line_str)}</p>')

    if in_list: html_body.append("</ul>")
    if in_table: html_body.append("</table>")

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Calibri', 'Arial', sans-serif; font-size: 11pt; color: #1E293B; line-height: 1.5; padding: 40px; background: #ffffff; }}
  @page {{ size: A4; margin: 20mm; }}
</style>
</head>
<body>
{"".join(html_body)}
</body>
</html>"""
    return full_html

def convert_to_docx(html_content: str, output_path: str):
    """Konvertiert HTML zu DOCX über textutil (Mac) oder Fallback."""
    temp_html = output_path + ".temp.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # Versuche textutil (macOS nativ)
    if shutil.which("textutil"):
        res = subprocess.run(["textutil", "-convert", "docx", temp_html, "-output", output_path], capture_output=True)
        if res.returncode == 0:
            if os.path.exists(temp_html): os.remove(temp_html)
            print(f"✅ DOCX erfolgreich erstellt: {output_path}")
            return

    # Fallback / Pandoc
    if shutil.which("pandoc"):
        res = subprocess.run(["pandoc", temp_html, "-o", output_path], capture_output=True)
        if res.returncode == 0:
            if os.path.exists(temp_html): os.remove(temp_html)
            print(f"✅ DOCX via Pandoc erfolgreich erstellt: {output_path}")
            return

    # Letzter Ausweg: HTML als Word-kompatibles HTML/DOCX abspeichern
    shutil.move(temp_html, output_path)
    print(f"✅ Dokument als Word-kompatibles HTML/DOCX hinterlegt: {output_path}")

def convert_to_pdf(html_content: str, output_path: str):
    """Konvertiert HTML zu PDF über Headless Chrome / Edge."""
    temp_html = output_path + ".temp.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Suche nach Chrome / Edge / Browser
    browser_binary = None
    mac_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    mac_edge = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    
    if os.path.exists(mac_chrome):
        browser_binary = mac_chrome
    elif os.path.exists(mac_edge):
        browser_binary = mac_edge
    elif shutil.which("google-chrome"):
        browser_binary = "google-chrome"
    elif shutil.which("msedge"):
        browser_binary = "msedge"
    elif shutil.which("chrome"):
        browser_binary = "chrome"

    if browser_binary:
        cmd = [browser_binary, "--headless", f"--print-to-pdf={output_path}", "--no-pdf-header-footer", temp_html]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(output_path):
            if os.path.exists(temp_html): os.remove(temp_html)
            print(f"✅ PDF erfolgreich erstellt: {output_path}")
            return

    print(f"⚠️ Kein Headless-Browser gefunden. HTML abgespeichert unter: {temp_html}")

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 document_exporter.py [docx|pdf] [input.md] [output_file]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    input_md = sys.argv[2]
    output_file = sys.argv[3]

    if not os.path.exists(input_md):
        print(f"❌ Eingabedatei nicht gefunden: {input_md}")
        sys.exit(1)

    with open(input_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    title = os.path.splitext(os.path.basename(input_md))[0]
    html_content = markdown_to_html(md_text, title=title)

    if mode == "docx":
        convert_to_docx(html_content, output_file)
    elif mode == "pdf":
        convert_to_pdf(html_content, output_file)
    else:
        print(f"❌ Unbekannter Modus: {mode}. Erwartet 'docx' oder 'pdf'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
