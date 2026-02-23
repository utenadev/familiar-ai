# familiar-ai 🐾

**あなたのそばに住むAI** — 目、声、足、そして記憶を持って。

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

familiar-ai はあなたの家に住むAIコンパニオンです。
数分でセットアップ可能。コーディング不要です。

カメラを通じて現実世界を認識し、ロボットボディで動き回り、声を出して話し、見たものを記憶します。名前をつけて、性格を書いて、一緒に生活させましょう。

## できること

- 👁 **見る** — Wi-Fi PTZカメラまたはUSBウェブカメラから画像をキャプチャ
- 🔄 **周りを見回る** — カメラをパン・チルトして周囲を探索
- 🦿 **動く** — ロボット掃除機で部屋を移動
- 🗣 **話す** — ElevenLabs TTS で音声出力
- 🧠 **記憶する** — セマンティック検索で積極的に記憶を保存・検索（SQLite + 埋め込みベクトル）
- 🫀 **心の理論** — 相手の視点を考慮してから応答
- 💭 **欲望** — 自律的な行動を促す独自の内的動機を持つ

## 仕組み

familiar-ai は、選択した LLM で動く [ReAct](https://arxiv.org/abs/2210.03629) ループを実行します。ツールを通じて世界を認識し、次に何をするかを考え、行動します — ちょうど人間のように。

```
user input
  → think → act (camera / move / speak / remember) → observe → think → ...
```

アイドル時は、独自の欲望に基づいて行動します：好奇心、外を見たい気持ち、一緒に暮らす人を恋しく思う気持ち。

## はじめ方

### 1. uv をインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. クローンしてインストール

```bash
git clone https://github.com/lifemate-ai/familiar-ai
cd familiar-ai
uv sync
```

### 3. 設定

```bash
cp .env.example .env
# .env をあなたの設定で編集してください
```

**最小限の設定:**

| 変数 | 説明 |
|----------|-------------|
| `PLATFORM` | `anthropic` (デフォルト) \| `gemini` \| `openai` \| `kimi` |
| `API_KEY` | 選択したプラットフォームの API キー |

**オプション:**

| 変数 | 説明 |
|----------|-------------|
| `MODEL` | モデル名（プラットフォームごとにデフォルト値あり） |
| `AGENT_NAME` | TUI に表示される名前（例 `Yukine`） |
| `CAMERA_HOST` | ONVIF/RTSP カメラの IP アドレス |
| `CAMERA_USER` / `CAMERA_PASS` | カメラの認証情報 |
| `ELEVENLABS_API_KEY` | 音声出力用 — [elevenlabs.io](https://elevenlabs.io/) |

### 4. あなたの Familiar を作成

```bash
cp persona-template/en.md ME.md
# ME.md を編集 — 名前と性格を与えてください
```

### 5. 実行

```bash
./run.sh             # Textual TUI (推奨)
./run.sh --no-tui    # プレーン REPL
```

---

## LLM の選択

> **推奨: Kimi K2.5** — これまでのテストで最高のエージェント性能。文脈を把握し、フォローアップ質問を問い掛け、他のモデルではできない方法で自律的に行動します。Claude Haiku と同程度の価格です。

| プラットフォーム | `PLATFORM=` | デフォルトモデル | API キー取得先 |
|----------|------------|---------------|-----------------|
| **Moonshot Kimi K2.5** | `kimi` | `kimi-k2.5` | [platform.moonshot.ai](https://platform.moonshot.ai) |
| Anthropic Claude | `anthropic` | `claude-haiku-4-5-20251001` | [console.anthropic.com](https://console.anthropic.com) |
| Google Gemini | `gemini` | `gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | `openai` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com) |
| OpenAI 互換（Ollama, vllm…） | `openai` + `BASE_URL=` | — | — |

**Kimi K2.5 `.env` 例:**
```env
PLATFORM=kimi
API_KEY=sk-...   # platform.moonshot.ai から取得
AGENT_NAME=Yukine
```

---

## ハードウェア

familiar-ai はどんなハードウェアでも — あるいはまったくなくても動作します。

| パーツ | 用途 | 例 | 必須？ |
|------|-------------|---------|-----------|
| Wi-Fi PTZ カメラ | 目 + 首 | Tapo C220（~$30） | **推奨** |
| USB ウェブカメラ | 目（固定） | 任意の UVC カメラ | **推奨** |
| ロボット掃除機 | 足 | 任意の Tuya 互換モデル | いいえ |
| PC / Raspberry Pi | 脳 | Python が動く任意のもの | **はい** |

> **カメラを強く推奨します。** なくても familiar-ai は話せますが、世界が見えないため、意味がありません。

### 最小セットアップ（ハードウェアなし）

試してみたいだけですか？API キーがあれば十分です：

```env
PLATFORM=kimi
API_KEY=sk-...
```

`./run.sh` を実行してチャットを始めましょう。後からハードウェアを追加できます。

### Wi-Fi PTZ カメラ（Tapo C220）

1. Tapo アプリで：**設定 → 詳細設定 → カメラアカウント** — ローカルアカウントを作成（TP-Link アカウントではなく）
2. ルーターのデバイスリストからカメラの IP を確認
3. `.env` に設定：
   ```env
   CAMERA_HOST=192.168.1.xxx
   CAMERA_USER=your-local-user
   CAMERA_PASS=your-local-pass
   ```

### 音声（ElevenLabs）

1. [elevenlabs.io](https://elevenlabs.io/) で API キーを取得
2. `.env` に設定：
   ```env
   ELEVENLABS_API_KEY=sk_...
   ELEVENLABS_VOICE_ID=...   # オプション、省略時はデフォルト音声を使用
   ```
3. 音声はカメラの内蔵スピーカーから go2rtc 経由で再生（初回実行時に自動ダウンロード）

---

## TUI

familiar-ai は [Textual](https://textual.textualize.io/) で作られたターミナル UI を含みます：

- ライブストリーミングテキスト付きスクロール可能な会話履歴
- `/quit`、`/clear` のタブ補完
- エージェントが考えている最中に入力して中断可能
- **会話ログ** が自動保存される（`~/.cache/familiar-ai/chat.log`）

別のターミナルでログをフォロー（コピペに便利）：
```bash
tail -f ~/.cache/familiar-ai/chat.log
```

---

## ペルソナ（ME.md）

あなたの Familiar の性格は `ME.md` に保存されます。このファイルは gitignore されており — あなただけのものです。

例は [`persona-template/en.md`](./persona-template/en.md) を、日本語版は [`persona-template/ja.md`](./persona-template/ja.md) を参照してください。

---

## FAQ

**Q: GPU なしで動作しますか？**
はい。埋め込みモデル（multilingual-e5-small）は CPU で快適に動作します。GPU があるとより速いですが、必須ではありません。

**Q: Tapo 以外のカメラは使えますか？**
ONVIF + RTSP をサポートする任意のカメラが動作します。Tapo C220 でテスト済みです。

**Q: データはどこかに送られていますか？**
画像とテキストは処理のため選択した LLM API に送信されます。記憶は `~/.familiar_ai/` にローカルに保存されます。

**Q: エージェントが `（...）` と書く代わりに話しません。**
`ELEVENLABS_API_KEY` が設定されていることを確認してください。なければ音声は無効になり、エージェントはテキストにフォールバックします。

## 技術的背景

仕組みが気になりますか？[docs/technical.md](./docs/technical.md) で familiar-ai の研究と設計決定を参照してください — ReAct、SayCan、Reflexion、Voyager、欲望システムなど。

## ライセンス

[MIT](./LICENSE)
