#!/usr/bin/env python3
"""
Groundsole ISN Update-Checker & Sync

Prüft dezentral gegen das öffentliche GitHub-Repository (egoinnovation/groundsole),
ob eine neuere Core-Version vorliegt.
Tastet niemals persönliche Notizen, Transkripte oder lokale Datenbanken an.
"""

import json
import urllib.request
import urllib.error
import argparse
from pathlib import Path

GITHUB_RAW_VERSION_URL = "https://raw.githubusercontent.com/egoinnovation/groundsole/main/version.json"

def check_for_updates(workspace_dir: Path) -> dict:
    local_version_file = workspace_dir / "version.json"
    if not local_version_file.exists():
        return {"status": "error", "message": "Keine lokale version.json gefunden."}

    with open(local_version_file, "r", encoding="utf-8") as f:
        local_data = json.load(f)

    local_version = local_data.get("installed_version") or local_data.get("version", "0.0.0")

    try:
        req = urllib.request.Request(
            GITHUB_RAW_VERSION_URL,
            headers={"User-Agent": "Groundsole-ISN-Updater"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            remote_data = json.loads(resp.read().decode("utf-8"))
            remote_version = remote_data.get("version", "0.0.0")
    except Exception as e:
        return {
            "status": "offline",
            "message": f"Konnte GitHub (egoinnovation/groundsole) nicht erreichen ({e}). Offline-Betrieb aktiv.",
            "local_version": local_version
        }

    has_update = remote_version > local_version
    return {
        "status": "ok",
        "has_update": has_update,
        "local_version": local_version,
        "remote_version": remote_version,
        "repository": remote_data.get("organization", "egoinnovation/groundsole")
    }

def main():
    parser = argparse.ArgumentParser(description="Prüft auf Groundsole ISN Framework Updates")
    parser.add_argument("--workspace", default=".", help="Pfad zum Instanz-Workspace")
    args = parser.parse_args()

    ws_path = Path(args.workspace).resolve()
    result = check_for_updates(ws_path)
    
    if result["status"] == "ok":
        if result["has_update"]:
            print(f"[!] NEUES UPDATE VERFÜGBAR: v{result['remote_version']} (Lokale Version: v{result['local_version']})")
            print(f"    Repository: {result['repository']}")
        else:
            print(f"[+] Groundsole ISN ist auf dem neuesten Stand (v{result['local_version']}).")
    else:
        print(f"[i] {result['message']}")

if __name__ == "__main__":
    main()
