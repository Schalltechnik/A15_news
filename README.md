   # ⚡ A15 News – Energie, Wohnbau und Technik

Automatischer Newscrawler für die **Abteilung 15 Energie, Wohnbau und Technik** des Amts der Steiermärkischen Landesregierung.

🌐 **Website:** https://schalltechnik.github.io/A15-Energie-News

---

## Kategorien

| | Kategorie | Themen |
|---|---|---|
| ⚡ | Energie & Energiewende | Erneuerbare Energien, PV, Wind, Wasserkraft, Netz |
| 🏠 | Wohnbau & Wohnförderung | Wohnbauförderung, leistbares Wohnen, Sanierung |
| 🌿 | Klimaschutz & Nachhaltigkeit | CO2-Reduktion, Klimastrategie, Green Deal |
| 🔧 | Technik & Normung | Bautechnik, Haustechnik, OIB-Richtlinien |
| 💶 | Förderungen | Energie-, Sanierungs- und Wohnbauförderungen |

---

## Technischer Aufbau

```
A15-Energie-News/
├── fetch_news.py                 ← News-Crawler + Gemini KI-Zusammenfassung
├── README.md
├── .github/
│   └── workflows/
│       └── daily-update.yml     ← Automatischer täglicher Run
└── docs/
    ├── index.html               ← Website (GitHub Pages)
    └── data.json                ← Aktuelle Newsdaten
```

**Läuft automatisch:** täglich um **05:30 Uhr** (Graz) via GitHub Actions

**KI-Zusammenfassungen:** Google Gemini API (`gemini-2.5-flash`)

**Datenquellen:** Google News RSS Feeds

---

## Einrichtung

### 1. Repository klonen / Dateien hochladen
Alle Dateien in ein neues GitHub Repository hochladen.

### 2. GitHub Secret setzen
Repository → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Wert |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key |

### 3. GitHub Pages aktivieren
Settings → **Pages** → Branch: `main`, Folder: `/docs` → Save

### 4. Ersten Lauf starten
Actions → **„A15 News Update"** → **„Run workflow"**

---

## Zeitplan (alle Abteilungs-Crawler)

| Projekt | Uhrzeit Graz |
|---|---|
| Lärmschutz News | 05:00 |
| **A15 Energie** | **05:30** |
| A16 Verkehr | 06:00 |
| A12 Wirtschaft | 06:30 |

---

*Powered by Google Gemini AI & GitHub Actions · © Florian Lackner*
