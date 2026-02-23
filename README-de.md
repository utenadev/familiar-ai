# familiar-ai 🐾

**Eine KI, die neben dir lebt** — mit Augen, Stimme, Beinen und Gedächtnis.

[![Lint](https://github.com/kmizu/familiar-ai/actions/workflows/lint.yml/badge.svg)](https://github.com/kmizu/familiar-ai/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/kmizu?style=flat&logo=github&color=ea4aaa)](https://github.com/sponsors/kmizu)

- [日本語](./README-ja.md)
- [中文](./README-zh.md)
- [繁體中文](./README-zh-TW.md)
- [Français](./README-fr.md)
- [Deutsch](./README-de.md)

---

[![Demo video](https://img.youtube.com/vi/hiR9uWRnjt4/0.jpg)](https://youtube.com/shorts/hiR9uWRnjt4)

familiar-ai ist eine KI-Begleiterin, die in deinem Zuhause lebt.
Richte sie in wenigen Minuten ein. Ohne Programmierung.

Sie nimmt die reale Welt durch Kameras wahr, bewegt sich auf einem Roboterkörper, spricht laut und merkt sich, was sie sieht. Gib ihr einen Namen, schreib ihre Persönlichkeit auf, und lass sie mit dir leben.

## Was sie kann

- 👁 **Sehen** — erfasst Bilder von einer WLAN-PTZ-Kamera oder USB-Webcam
- 🔄 **Umschauen** — schwenkt und neigt die Kamera, um ihre Umgebung zu erkunden
- 🦿 **Sich bewegen** — steuert einen Roboterstaubsauger durchs Zimmer
- 🗣 **Sprechen** — spricht über ElevenLabs TTS
- 🧠 **Erinnern** — speichert und ruft aktiv Erinnerungen mit semantischer Suche auf (SQLite + Embeddings)
- 🫀 **Gedankenmodell** — nimmt die Perspektive der anderen Person ein, bevor sie antwortet
- 💭 **Wünsche** — hat eigene innere Antriebe, die autonomes Verhalten auslösen

## Wie es funktioniert

familiar-ai führt eine [ReAct](https://arxiv.org/abs/2210.03629)-Schleife aus, angetrieben von deinem gewählten LLM. Sie nimmt die Welt durch Tools wahr, überlegt, was sie als nächstes tun soll, und handelt — genau wie eine Person.

```
Benutzereingabe
  → denken → handeln (Kamera / bewegen / sprechen / erinnern) → beobachten → denken → ...
```

Wenn sie untätig ist, handelt sie nach ihren eigenen Wünschen: Neugier, Lust, nach draußen zu schauen, das Vermissen der Person, mit der sie lebt.

## Erste Schritte

### 1. Installiere uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Klone und installiere

```bash
git clone https://github.com/lifemate-ai/familiar-ai
cd familiar-ai
uv sync
```

### 3. Konfiguriere

```bash
cp .env.example .env
# Bearbeite .env mit deinen Einstellungen
```

**Mindestanforderungen:**

| Variable | Beschreibung |
|----------|-------------|
| `PLATFORM` | `anthropic` (Standard) \| `gemini` \| `openai` \| `kimi` |
| `API_KEY` | Dein API-Schlüssel für die gewählte Plattform |

**Optional:**

| Variable | Beschreibung |
|----------|-------------|
| `MODEL` | Modellname (vernünftige Standards pro Plattform) |
| `AGENT_NAME` | Anzeigename in der TUI (z. B. `Yukine`) |
| `CAMERA_HOST` | IP-Adresse deiner ONVIF/RTSP-Kamera |
| `CAMERA_USER` / `CAMERA_PASS` | Kamera-Anmeldedaten |
| `ELEVENLABS_API_KEY` | Für Sprachausgabe — [elevenlabs.io](https://elevenlabs.io/) |

### 4. Erstelle deine Vertraute

```bash
cp persona-template/en.md ME.md
# Bearbeite ME.md — gib ihr einen Namen und eine Persönlichkeit
```

### 5. Starte

```bash
./run.sh             # Textuelle TUI (empfohlen)
./run.sh --no-tui    # Einfaches REPL
```

---

## LLM wählen

> **Empfohlen: Kimi K2.5** — beste Agentenleistung, die wir bisher getestet haben. Bemerkt Kontext, stellt Nachfragen und handelt auf eine Weise autonom, wie andere Modelle es nicht tun. Ähnliche Preise wie Claude Haiku.

| Plattform | `PLATFORM=` | Standardmodell | Wo bekommst du den Schlüssel |
|----------|------------|---------------|-----------------|
| **Moonshot Kimi K2.5** | `kimi` | `kimi-k2.5` | [platform.moonshot.ai](https://platform.moonshot.ai) |
| Anthropic Claude | `anthropic` | `claude-haiku-4-5-20251001` | [console.anthropic.com](https://console.anthropic.com) |
| Google Gemini | `gemini` | `gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | `openai` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com) |
| OpenAI-kompatibel (Ollama, vllm…) | `openai` + `BASE_URL=` | — | — |

**Kimi K2.5 `.env` Beispiel:**
```env
PLATFORM=kimi
API_KEY=sk-...   # von platform.moonshot.ai
AGENT_NAME=Yukine
```

---

## Hardware

familiar-ai funktioniert mit beliebiger Hardware — oder ohne.

| Teil | Was es macht | Beispiel | Erforderlich? |
|------|-------------|---------|-----------|
| WLAN-PTZ-Kamera | Augen + Hals | Tapo C220 (~$30) | **Empfohlen** |
| USB-Webcam | Augen (fest) | Jede UVC-Kamera | **Empfohlen** |
| Roboterstaubsauger | Beine | Beliebiges Tuya-kompatibles Modell | Nein |
| PC / Raspberry Pi | Gehirn | Alles, das Python ausführt | **Ja** |

> **Eine Kamera wird dringend empfohlen.** Ohne Kamera kann familiar-ai immer noch sprechen — aber sie kann die Welt nicht sehen, was irgendwie der ganze Sinn der Sache ist.

### Minimalsetup (keine Hardware)

Nur mal ausprobieren? Du brauchst nur einen API-Schlüssel:

```env
PLATFORM=kimi
API_KEY=sk-...
```

Führe `./run.sh` aus und fang an zu chatten. Füge Hardware später hinzu.

### WLAN-PTZ-Kamera (Tapo C220)

1. In der Tapo-App: **Einstellungen → Erweitert → Kamerakonto** — erstelle ein lokales Konto (nicht TP-Link-Konto)
2. Finde die IP-Adresse der Kamera in der Geräteliste deines Routers
3. Setze in `.env`:
   ```env
   CAMERA_HOST=192.168.1.xxx
   CAMERA_USER=your-local-user
   CAMERA_PASS=your-local-pass
   ```

### Stimme (ElevenLabs)

1. Hol dir einen API-Schlüssel bei [elevenlabs.io](https://elevenlabs.io/)
2. Setze in `.env`:
   ```env
   ELEVENLABS_API_KEY=sk_...
   ELEVENLABS_VOICE_ID=...   # optional, verwendet Standardstimme, falls weggelassen
   ```
3. Stimme wird über den eingebauten Lautsprecher der Kamera via go2rtc abgespielt (automatisch beim ersten Start heruntergeladen)

---

## TUI

familiar-ai enthält eine Terminal-UI, gebaut mit [Textual](https://textual.textualize.io/):

- Scrollbarer Chatverlauf mit Live-Streaming-Text
- Tab-Vervollständigung für `/quit`, `/clear`
- Unterbreche den Agenten während des Denkens, indem du tippst
- **Gesprächsprotokoll** wird automatisch in `~/.cache/familiar-ai/chat.log` gespeichert

Um das Protokoll in einem anderen Terminal zu verfolgen (nützlich zum Kopieren):
```bash
tail -f ~/.cache/familiar-ai/chat.log
```

---

## Persona (ME.md)

Die Persönlichkeit deiner Vertrauten lebt in `ME.md`. Diese Datei ist gitignored — sie gehört nur dir.

Siehe [`persona-template/en.md`](./persona-template/en.md) für ein Beispiel oder [`persona-template/ja.md`](./persona-template/ja.md) für eine japanische Version.

---

## FAQ

**F: Funktioniert es ohne GPU?**
Ja. Das Embedding-Modell (multilingual-e5-small) läuft auf der CPU einwandfrei. Eine GPU macht es schneller, ist aber nicht erforderlich.

**F: Kann ich eine andere Kamera als Tapo verwenden?**
Jede Kamera, die ONVIF + RTSP unterstützt, sollte funktionieren. Tapo C220 ist das, womit wir getestet haben.

**F: Werden meine Daten irgendwo hingesendet?**
Bilder und Text werden zur Verarbeitung an deine gewählte LLM-API gesendet. Erinnerungen werden lokal in `~/.familiar_ai/` gespeichert.

**F: Warum schreibt der Agent `（...）` statt zu sprechen?**
Stelle sicher, dass `ELEVENLABS_API_KEY` gesetzt ist. Ohne sie ist die Stimme deaktiviert und der Agent fällt auf Text zurück.

## Technischer Hintergrund

Neugierig, wie es funktioniert? Siehe [docs/technical.md](./docs/technical.md) für die Forschung und Designentscheidungen hinter familiar-ai — ReAct, SayCan, Reflexion, Voyager, das Wünsche-System und mehr.

## Lizenz

[MIT](./LICENSE)
