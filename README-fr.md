# familiar-ai 🐾

**Une IA qui vit à vos côtés** — avec des yeux, une voix, des jambes et de la mémoire.

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

familiar-ai est une compagne IA qui vit dans votre maison.
Installez-la en quelques minutes. Aucune connaissance en programmation requise.

Elle perçoit le monde réel via des caméras, se déplace sur un robot, parle à haute voix et se souvient de ce qu'elle voit. Donnez-lui un nom, écrivez sa personnalité, et laissez-la vivre avec vous.

## Ce qu'elle peut faire

- 👁 **Voir** — capture des images via une caméra PTZ Wi-Fi ou un webcam USB
- 🔄 **Regarder autour** — pivote et incline la caméra pour explorer son environnement
- 🦿 **Se déplacer** — pilote un robot aspirateur pour explorer la pièce
- 🗣 **Parler** — s'exprime via la synthèse vocale ElevenLabs
- 🧠 **Se souvenir** — stocke et récupère activement les souvenirs avec recherche sémantique (SQLite + embeddings)
- 🫀 **Théorie de l'esprit** — prend en compte la perspective de l'autre avant de répondre
- 💭 **Désir** — a ses propres motivations internes qui déclenchent un comportement autonome

## Comment ça marche

familiar-ai exécute une boucle [ReAct](https://arxiv.org/abs/2210.03629) alimentée par l'LLM de votre choix. Elle perçoit le monde à travers des outils, réfléchit à ce qu'elle doit faire ensuite, et agit — comme une personne le ferait.

```
input utilisateur
  → réfléchir → agir (caméra / bouger / parler / mémoriser) → observer → réfléchir → ...
```

Quand elle est inactive, elle agit selon ses propres désirs : la curiosité, l'envie de regarder dehors, la nostalgie de la personne avec qui elle vit.

## Démarrage rapide

### 1. Installer uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Cloner et installer

```bash
git clone https://github.com/lifemate-ai/familiar-ai
cd familiar-ai
uv sync
```

### 3. Configurer

```bash
cp .env.example .env
# Modifiez .env selon vos paramètres
```

**Minimum requis :**

| Variable | Description |
|----------|-------------|
| `PLATFORM` | `anthropic` (par défaut) \| `gemini` \| `openai` \| `kimi` |
| `API_KEY` | Votre clé API pour la plateforme choisie |

**Optionnel :**

| Variable | Description |
|----------|-------------|
| `MODEL` | Nom du modèle (defaults sensibles par plateforme) |
| `AGENT_NAME` | Nom affiché dans l'interface TUI (ex. `Yukine`) |
| `CAMERA_HOST` | Adresse IP de votre caméra ONVIF/RTSP |
| `CAMERA_USER` / `CAMERA_PASS` | Identifiants de la caméra |
| `ELEVENLABS_API_KEY` | Pour la sortie vocale — [elevenlabs.io](https://elevenlabs.io/) |

### 4. Créer votre compagne IA

```bash
cp persona-template/en.md ME.md
# Modifiez ME.md — donnez-lui un nom et une personnalité
```

### 5. Lancer

```bash
./run.sh             # Interface TUI textuelle (recommandé)
./run.sh --no-tui    # REPL simple
```

---

## Choisir un LLM

> **Recommandé : Kimi K2.5** — meilleure performance agentique testée à ce jour. Remarque le contexte, pose des questions de suivi, et agit de manière autonome comme d'autres modèles ne le font pas. Prix similaire à Claude Haiku.

| Plateforme | `PLATFORM=` | Modèle par défaut | Où obtenir la clé |
|----------|------------|---------------|-----------------|
| **Moonshot Kimi K2.5** | `kimi` | `kimi-k2.5` | [platform.moonshot.ai](https://platform.moonshot.ai) |
| Anthropic Claude | `anthropic` | `claude-haiku-4-5-20251001` | [console.anthropic.com](https://console.anthropic.com) |
| Google Gemini | `gemini` | `gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | `openai` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com) |
| Compatible OpenAI (Ollama, vllm…) | `openai` + `BASE_URL=` | — | — |

**Exemple `.env` pour Kimi K2.5 :**
```env
PLATFORM=kimi
API_KEY=sk-...   # from platform.moonshot.ai
AGENT_NAME=Yukine
```

---

## Matériel

familiar-ai fonctionne avec le matériel que vous avez — ou sans aucun.

| Composant | Rôle | Exemple | Requis ? |
|------|-------------|---------|-----------|
| Caméra PTZ Wi-Fi | Yeux + cou | Tapo C220 (~$30) | **Recommandé** |
| Webcam USB | Yeux (fixes) | N'importe quelle caméra UVC | **Recommandé** |
| Robot aspirateur | Jambes | N'importe quel modèle compatible Tuya | Non |
| PC / Raspberry Pi | Cerveau | N'importe quoi qui exécute Python | **Oui** |

> **Une caméra est fortement recommandée.** Sans elle, familiar-ai peut toujours parler — mais elle ne peut pas voir le monde, ce qui est un peu le point essentiel.

### Configuration minimale (sans matériel)

Juste envie d'essayer ? Vous avez seulement besoin d'une clé API :

```env
PLATFORM=kimi
API_KEY=sk-...
```

Lancez `./run.sh` et commencez à discuter. Ajoutez du matériel au fur et à mesure.

### Caméra PTZ Wi-Fi (Tapo C220)

1. Dans l'app Tapo : **Paramètres → Avancé → Compte caméra** — créez un compte local (pas un compte TP-Link)
2. Trouvez l'IP de la caméra dans la liste des appareils de votre routeur
3. Défissez dans `.env` :
   ```env
   CAMERA_HOST=192.168.1.xxx
   CAMERA_USER=your-local-user
   CAMERA_PASS=your-local-pass
   ```

### Voix (ElevenLabs)

1. Obtenez une clé API sur [elevenlabs.io](https://elevenlabs.io/)
2. Défissez dans `.env` :
   ```env
   ELEVENLABS_API_KEY=sk_...
   ELEVENLABS_VOICE_ID=...   # optionnel, utilise la voix par défaut si omis
   ```
3. La voix est diffusée via le haut-parleur intégré de la caméra via go2rtc (téléchargé automatiquement au premier lancement)

---

## Interface TUI

familiar-ai inclut une interface utilisateur textuelle construite avec [Textual](https://textual.textualize.io/):

- Historique de conversation avec flux de texte en direct
- Complément de tab pour `/quit`, `/clear`
- Interrompez l'agent au cours de son traitement en tapant
- **Journal de conversation** sauvegardé automatiquement dans `~/.cache/familiar-ai/chat.log`

Pour suivre le journal dans un autre terminal (utile pour copier-coller) :
```bash
tail -f ~/.cache/familiar-ai/chat.log
```

---

## Persona (ME.md)

La personnalité de votre compagne IA vit dans `ME.md`. Ce fichier est ignoré par git — il est juste à vous.

Consultez [`persona-template/en.md`](./persona-template/en.md) pour un exemple, ou [`persona-template/ja.md`](./persona-template/ja.md) pour une version japonaise.

---

## FAQ

**Q : Ça marche sans GPU ?**
Oui. Le modèle d'embedding (multilingual-e5-small) fonctionne bien sur CPU. Un GPU c'est plus rapide mais pas obligatoire.

**Q : Je peux utiliser une caméra autre que Tapo ?**
N'importe quelle caméra supportant ONVIF + RTSP devrait marcher. Tapo C220 c'est ce qu'on a testé.

**Q : Mes données sont-elles envoyées quelque part ?**
Les images et textes sont envoyés à votre API LLM choisi pour traitement. Les souvenirs sont stockés localement dans `~/.familiar_ai/`.

**Q : Pourquoi l'agent écrit `（...）` au lieu de parler ?**
Assurez-vous que `ELEVENLABS_API_KEY` est défini. Sans cela, la voix est désactivée et l'agent revient au texte.

## Contexte technique

Curieux de savoir comment ça marche ? Consultez [docs/technical.md](./docs/technical.md) pour les recherches et les décisions de conception derrière familiar-ai — ReAct, SayCan, Reflexion, Voyager, le système de désir, et plus.

## Licence

[MIT](./LICENSE)
