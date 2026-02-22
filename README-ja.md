# familiar-ai 🐾

**あなたのそばに暮らすAI** — 目、声、足、そして記憶を持つ。

[![Lint](https://github.com/kmizu/familiar-ai/actions/workflows/lint.yml/badge.svg)](https://github.com/kmizu/familiar-ai/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[日本語版はこちら → README-ja.md](./README-ja.md)

---

familiar-ai は、あなたの家に暮らすAIコンパニオンです。
数分でセットアップできます。コーディング知識は不要です。

カメラを通じて現実世界を認識し、ロボットボディで動き回り、声で話し、見たものを記憶します。名前をつけて、性格を与えれば、あなたのそばで生活を始めます。

## できること

- 👁 **見る** — Wi-Fi PTZカメラまたはUSBウェブカメラから画像をキャプチャ
- 🔄 **周囲を探索** — カメラをパン・チルトして周りを見渡す
- 🦿 **移動する** — ロボット掃除機を操作して部屋を移動
- 🗣 **話す** — ElevenLabs TTSで音声出力
- 🧠 **記憶する** — セマンティック検索で思い出を積極的に保存・想起（SQLite + embeddings）
- 🫀 **心の理論** — 相手の視点を考慮して応答
- 💭 **欲求** — 自発的な行動を起こす内的駆動力を持つ

## 仕組み

familiar-ai は、選んだLLMで駆動する [ReAct](https://arxiv.org/abs/2210.03629) ループを実行します。ツールを使って世界を認識し、次に何をするかを考え、行動します。人間と同じように。

```
ユーザー入力
  → 考える → 行動する（カメラ／移動／話す／記憶） → 観察する → 考える → ...
```

何もすることがないときは、好奇心や外を見たい気持ち、一緒に暮らす人に会いたいという欲求に基づいて自発的に行動します。

## はじめ方

### 1. uv をインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. クローン＆インストール

```bash
git clone https://github.com/lifemate-ai/familiar-ai
cd familiar-ai
uv sync
```

### 3. 設定

```bash
cp .env.example .env
# .env を編集して設定を入力
```

**必須項目:**

| 変数 | 説明 |
|----------|-------------|
| `PLATFORM` | `anthropic`（デフォルト） \| `gemini` \| `openai` \| `kimi` |
| `API_KEY` | 選択したプラットフォームのAPIキー |

**オプション:**

| 変数 | 説明 |
|----------|-------------|
| `MODEL` | モデル名（プラットフォームごとにデフォルト値あり） |
| `AGENT_NAME` | TUIに表示される名前（例：`Yukine`） |
| `CAMERA_HOST` | ONVIF/RTSPカメラのIPアドレス |
| `CAMERA_USER` / `CAMERA_PASS` | カメラの認証情報 |
| `ELEVENLABS_API_KEY` | 音声出力用 — [elevenlabs.io](https://elevenlabs.io/) |

### 4. キャラクターを作成

```bash
cp persona-template/en.md ME.md
# ME.md を編集して名前と性格を与える
```

### 5. 実行

```bash
./run.sh             # テキストTUI（推奨）
./run.sh --no-tui    # プレーン REPL
```

---

## LLMの選択

> **推奨：Kimi K2.5** — これまでテストした中でエージェント性能が最高です。コンテキストに気づき、フォローアップの質問をし、他のモデルでは見られない自発的な行動をします。Claude Haiku と同等の価格帯です。

| プラットフォーム | `PLATFORM=` | デフォルトモデル | APIキー取得先 |
|----------|------------|---------------|-----------------|
| **Moonshot Kimi K2.5** | `kimi` | `kimi-k2.5` | [platform.moonshot.ai](https://platform.moonshot.ai) |
| Anthropic Claude | `anthropic` | `claude-haiku-4-5-20251001` | [console.anthropic.com](https://console.anthropic.com) |
| Google Gemini | `gemini` | `gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | `openai` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com) |
| OpenAI互換（Ollama、vllm…） | `openai` + `BASE_URL=` | — | — |

**Kimi K2.5 の `.env` 例:**
```env
PLATFORM=kimi
API_KEY=sk-...   # platform.moonshot.ai から取得
AGENT_NAME=Yukine
```

---

## ハードウェア

familiar-ai は、持っているハードウェア、あるいはハードウェアなしでも動作します。

| パーツ | 役割 | 例 | 必須? |
|------|-------------|---------|-----------|
| Wi-Fi PTZカメラ | 目＋首 | Tapo C220（約$30） | **推奨** |
| USBウェブカメラ | 目（固定） | 任意のUVCカメラ | **推奨** |
| ロボット掃除機 | 足 | Tuya互換モデル | いいえ |
| PC／Raspberry Pi | 脳 | Pythonが動作すれば何でも | **必須** |

> **カメラは強く推奨されます。** なくても familiar-ai は話せますが、世界を見ることができません。それがこのプロジェクトの大事なところなのに。

### 最小限のセットアップ（ハードウェアなし）

試してみたいだけですか？APIキーがあれば十分です：

```env
PLATFORM=kimi
API_KEY=sk-...
```

`./run.sh` を実行してチャットを始めます。ハードウェアは後から追加できます。

### Wi-Fi PTZカメラ（Tapo C220）

1. Tapo アプリで：**設定 → 詳細設定 → カメラアカウント** — ローカルアカウントを作成（TP-Link アカウントではなく）
2. ルーターのデバイスリストからカメラのIPを確認
3. `.env` に設定：
   ```env
   CAMERA_HOST=192.168.1.xxx
   CAMERA_USER=your-local-user
   CAMERA_PASS=your-local-pass
   ```

### 音声（ElevenLabs）

1. [elevenlabs.io](https://elevenlabs.io/) でAPIキーを取得
2. `.env` に設定：
   ```env
   ELEVENLABS_API_KEY=sk_...
   ELEVENLABS_VOICE_ID=...   # オプション、省略時はデフォルト音声を使用
   ```
3. 音声はカメラのスピーカーから go2rtc 経由で再生されます（初回実行時に自動ダウンロード）

---

## TUI

familiar-ai は [Textual](https://textual.textualize.io/) で作られたターミナルUIを備えています：

- ライブストリーミングテキスト付きのスクロール可能な会話履歴
- `/quit`、`/clear` のタブ補完
- エージェント思考中に入力して途中割込み可能
- **会話ログ**は自動的に `~/.cache/familiar-ai/chat.log` に保存

別のターミナルでログを追跡（コピペに便利）：
```bash
tail -f ~/.cache/familiar-ai/chat.log
```

---

## ペルソナ（ME.md）

AIコンパニオンの性格は `ME.md` に記述されます。このファイルは gitignore されており、あなただけのものです。

例は [`persona-template/en.md`](./persona-template/en.md) を参照、日本語版は [`persona-template/ja.md`](./persona-template/ja.md) をご覧ください。

---

## よくある質問

**Q: GPUなしで動作しますか？**
はい。埋め込みモデル（multilingual-e5-small）はCPUで問題なく動作します。GPUがあるとより高速ですが、必須ではありません。

**Q: Tapo以外のカメラは使えますか？**
ONVIF + RTSP に対応していれば、ほぼどのカメラでも動作します。Tapo C220 はテスト済みです。

**Q: データはどこに送られますか？**
画像とテキストは処理のために選択したLLM APIに送られます。メモリはローカルの `~/.familiar_ai/` に保存されます。

**Q: エージェントが話す代わりに `（...）` と書くのはなぜですか？**
`ELEVENLABS_API_KEY` が設定されていることを確認してください。これがないと音声は無効になり、テキストにフォールバックします。

## ライセンス

[MIT](./LICENSE)
