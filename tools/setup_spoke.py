#!/usr/bin/env python3
"""
ISN Spoke Setup Script
Richtet den persönlichen Arbeitsbereich (Spoke) auf dem Laptop des Nutzers ein.
"""

import os
import shutil
import sys

def main():
    user_home = os.path.expanduser("~")
    # Search for OneDrive - isn - innovation service network
    onedrive_dir = None
    for d in os.listdir(user_home):
        if "onedrive" in d.lower() and "isn" in d.lower():
            onedrive_dir = os.path.join(user_home, d)
            break
            
    if not onedrive_dir:
        # Fallback to standard path
        onedrive_dir = os.path.join(user_home, "OneDrive - isn - innovation service network")
        
    spoke_dir = os.path.join(onedrive_dir, "ISN-AI")
    os.makedirs(spoke_dir, exist_ok=True)
    print(f"[+] Spoke-Verzeichnis erstellt/geprüft: {spoke_dir}")

    # Copy AGENTS.md template if not present
    target_agents = os.path.join(spoke_dir, "AGENTS.md")
    if not os.path.exists(target_agents):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(script_dir)
        template_agents = os.path.join(repo_root, "templates", "AGENTS.md")
        if os.path.exists(template_agents):
            shutil.copy(template_agents, target_agents)
            print(f"[+] AGENTS.md kopiert nach: {target_agents}")
    else:
        print(f"[+] AGENTS.md bereits vorhanden: {target_agents}")

    # Create memory dir for local vector DB
    memory_dir = os.path.join(spoke_dir, "00_MEMORY")
    os.makedirs(memory_dir, exist_ok=True)
    print(f"[+] Lokaler Speicherordner (00_MEMORY) bereit: {memory_dir}")

    print("
✅ Spoke-Einrichtung erfolgreich abgeschlossen!")

if __name__ == "__main__":
    main()
