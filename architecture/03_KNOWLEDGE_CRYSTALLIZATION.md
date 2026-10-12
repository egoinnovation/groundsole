# 03 - Wissenskristallisation & Filter-Gateways

---

## 1. Das Kristallisations-Prinzip

Der Wissenstransfer vom privaten Spoke zum zentralen SharePoint Hub erfolgt deterministisch und bewusst durch den Nutzer:

```
┌────────────────────────────────────────────────────────┐
│ SPOKE (Laptop Kollegin / Emanuel)                      │
│ Freier Dialog, persönliche Notizen, Projektarbeit       │
└──────────────────────────┬─────────────────────────────┘
                           │ Befehl: "Kristallisiere für ISN"
                           ▼
┌────────────────────────────────────────────────────────┐
│ FILTER 1: Striktes Privacy & Reflexions-Gate           │
│ • Entfernt persönliche Gefühle, Befindlichkeiten,      │
│   vertrauliche Notizen oder unfertige Gedankengänge.   │
└──────────────────────────┬─────────────────────────────┘
                           │ Extrahiert sachliche Erkenntnisse
                           ▼
┌────────────────────────────────────────────────────────┐
│ HUB (SharePoint AI_HUB)                                │
│ • Aktualisiert das relevante Dossier (00-05) oder      │
│   ergänzt einen Eintrag in TEAM_FEED.md                │
└────────────────────────────────────────────────────────┘
```

## 2. Die Filter-Regeln (Privacy & Quality Gate)
1. **Keine Personaldaten / Gefühle:** Persönliche Kommentare oder vertrauliche Notizen verbleiben auf dem Spoke.
2. **Kompaktheit & Relevanz:** Nur verifizierte Fakten, Beschlüsse, Kundenvereinbarungen oder technische Dokumentationen fließen in den Hub.
3. **Formatierung:** Ausgabe als sauberes, strukturiertes Plaintext-Markdown gemäß den ISN-Vorlagen.
