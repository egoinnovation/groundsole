#!/usr/bin/env python3
"""
Groundsole Universal Mail Helper
Supports reading and sending emails via IMAP / SMTP (Gmail App-Password, Outlook, GMX, custom mailboxes).
Zero external dependencies (uses standard Python imaplib and smtplib).
"""

import os
import sys
import json
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def find_credentials_file() -> Path:
    # 1. Check workspace config
    cwd_creds = Path.cwd() / "credentials.json"
    if cwd_creds.exists():
        return cwd_creds
    # 2. Check user home standard location
    home_creds = Path.home() / ".gemini" / "config" / "credentials.json"
    if home_creds.exists():
        return home_creds
    # 3. Fallback to local config
    return Path.cwd() / "credentials.json"

def load_credentials() -> dict:
    creds_path = find_credentials_file()
    if creds_path.exists():
        with open(creds_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def decode_mime_words(s: str) -> str:
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    pieces = []
    for text, charset in decoded_fragments:
        if isinstance(text, bytes):
            pieces.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            pieces.append(str(text))
    return "".join(pieces)

def check_inbox(limit: int = 5):
    creds = load_credentials()
    mail_conf = creds.get("gmail") or creds.get("default")
    if not mail_conf:
        print("❌ Keine E-Mail-Zugangsdaten gefunden.")
        print("👉 Lege eine credentials.json mit account, app_password und server an.")
        return

    server = mail_conf.get("server", "imap.gmail.com")
    user = mail_conf.get("account")
    password = mail_conf.get("app_password")

    print(f"🔌 Verbinde mit {server} für {user}...")
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(user, password)
        mail.select("INBOX")

        status, messages = mail.search(None, "UNSEEN")
        msg_ids = messages[0].split()
        if not msg_ids:
            print("📭 Keine ungelesenen E-Mails im Posteingang.")
            mail.close()
            mail.logout()
            return

        latest_ids = msg_ids[-limit:]
        latest_ids.reverse()

        print(f"📬 {len(msg_ids)} ungelesene E-Mail(s). Die neuesten {len(latest_ids)}:\n" + "="*60)

        for mid in latest_ids:
            res, data = mail.fetch(mid, "(RFC822)")
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_mime_words(msg.get("Subject", "(Kein Betreff)"))
                    sender = decode_mime_words(msg.get("From", "(Unbekannt)"))
                    date = msg.get("Date", "")
                    print(f"• Von:     {sender}")
                    print(f"  Betreff: {subject}")
                    print(f"  Datum:   {date}")
                    print("-" * 60)

        mail.close()
        mail.logout()
    except Exception as e:
        print(f"⚠️ Fehler beim E-Mail-Abruf: {e}")

def send_email(to_addr: str, subject: str, body: str):
    creds = load_credentials()
    mail_conf = creds.get("gmail") or creds.get("default")
    if not mail_conf:
        print("❌ Keine Zugangsdaten für den Mailversand gefunden.")
        return

    smtp_server = mail_conf.get("smtp_server", "smtp.gmail.com")
    smtp_port = int(mail_conf.get("smtp_port", 465))
    user = mail_conf.get("account")
    password = mail_conf.get("app_password")

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    print(f"📤 Sende E-Mail an {to_addr} via {smtp_server}...")
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())
        server.quit()
        print(f"✅ E-Mail erfolgreich an {to_addr} gesendet!")
    except Exception as e:
        print(f"⚠️ Fehler beim Senden: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  mail_helper.py check [limit]")
        print("  mail_helper.py send <to> <subject> <body>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "check":
        lim = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
        check_inbox(lim)
    elif cmd == "send" and len(sys.argv) >= 5:
        to_addr = sys.argv[2]
        subject = sys.argv[3]
        body = " ".join(sys.argv[4:])
        send_email(to_addr, subject, body)
    else:
        print("Ungültige Argumente.")

if __name__ == "__main__":
    main()
