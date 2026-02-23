# familiar-ai 🐾

**一个与你共生的 AI** — 拥有眼睛、声音、腿和记忆。

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

familiar-ai 是一个住在你家里的 AI 伙伴。
几分钟即可启动。完全无需编程。

它通过摄像头感知真实世界，在机器人身体上活动，能够说话，还能记住看到的一切。给它起个名字，定义它的个性，让它和你一起生活吧。

## 它能做什么

- 👁 **看见** — 从 Wi-Fi 云台摄像头或 USB 网络摄像头捕获图像
- 🔄 **四处张望** — 通过云台摄像头的转动来探索周围环境
- 🦿 **移动** — 驱动扫地机器人在房间里漫游
- 🗣 **说话** — 通过 ElevenLabs 文字转语音系统发出声音
- 🧠 **记忆** — 主动存储和回忆记忆，支持语义搜索（SQLite + embeddings）
- 🫀 **心智理论** — 在回应前站在他人的角度思考
- 💭 **欲望** — 拥有自己的内在驱动力，能够触发自主行为

## 工作原理

familiar-ai 运行由你选择的 LLM 驱动的 [ReAct](https://arxiv.org/abs/2210.03629) 循环。它通过工具感知世界，思考接下来要做什么，然后采取行动 — 就像一个人一样。

```
用户输入
  → 思考 → 行动（摄像头 / 移动 / 说话 / 记忆） → 观察 → 思考 → ...
```

闲置时，它会根据自己的欲望行动：好奇心、想看看窗外、想念一起生活的人。

## 快速开始

### 1. 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆并安装

```bash
git clone https://github.com/lifemate-ai/familiar-ai
cd familiar-ai
uv sync
```

### 3. 配置

```bash
cp .env.example .env
# 用你的设置编辑 .env
```

**必需配置：**

| 变量 | 说明 |
|----------|-------------|
| `PLATFORM` | `anthropic`（默认）\| `gemini` \| `openai` \| `kimi` |
| `API_KEY` | 选定平台的 API 密钥 |

**可选配置：**

| 变量 | 说明 |
|----------|-------------|
| `MODEL` | 模型名称（每个平台有合理的默认值） |
| `AGENT_NAME` | 在 TUI 中显示的名称（例如 `Yukine`） |
| `CAMERA_HOST` | ONVIF/RTSP 摄像头的 IP 地址 |
| `CAMERA_USER` / `CAMERA_PASS` | 摄像头凭证 |
| `ELEVENLABS_API_KEY` | 用于语音输出 — [elevenlabs.io](https://elevenlabs.io/) |

### 4. 创建你的伙伴

```bash
cp persona-template/en.md ME.md
# 编辑 ME.md — 为它起名字并定义个性
```

### 5. 运行

```bash
./run.sh             # 文本 TUI（推荐）
./run.sh --no-tui    # 纯 REPL
```

---

## 选择 LLM

> **推荐：Kimi K2.5** — 目前测试过的最佳代理性能。注意力强，会提出后续问题，并以其他模型不具备的方式自主行动。价格与 Claude Haiku 相当。

| 平台 | `PLATFORM=` | 默认模型 | 获取密钥 |
|----------|------------|---------------|-----------------|
| **Moonshot Kimi K2.5** | `kimi` | `kimi-k2.5` | [platform.moonshot.ai](https://platform.moonshot.ai) |
| Anthropic Claude | `anthropic` | `claude-haiku-4-5-20251001` | [console.anthropic.com](https://console.anthropic.com) |
| Google Gemini | `gemini` | `gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | `openai` | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com) |
| OpenAI 兼容（Ollama、vllm…） | `openai` + `BASE_URL=` | — | — |

**Kimi K2.5 `.env` 示例：**
```env
PLATFORM=kimi
API_KEY=sk-...   # 来自 platform.moonshot.ai
AGENT_NAME=Yukine
```

---

## 硬件

familiar-ai 可以在任何硬件上运行 — 或根本无需硬件。

| 配件 | 作用 | 示例 | 必需？ |
|------|-------------|---------|-----------|
| Wi-Fi 云台摄像头 | 眼睛 + 脖子 | Tapo C220（约 $30） | **推荐** |
| USB 网络摄像头 | 眼睛（固定） | 任何 UVC 摄像头 | **推荐** |
| 扫地机器人 | 腿 | 任何 Tuya 兼容型号 | 否 |
| PC / Raspberry Pi | 大脑 | 任何能运行 Python 的设备 | **是** |

> **强烈推荐配置摄像头。** 没有摄像头，familiar-ai 仍然可以说话 — 但无法看见世界，这样就失去了本意。

### 最小化设置（无硬件）

只想试试？你只需要一个 API 密钥：

```env
PLATFORM=kimi
API_KEY=sk-...
```

运行 `./run.sh` 并开始聊天。之后可以逐步添加硬件。

### Wi-Fi 云台摄像头（Tapo C220）

1. 在 Tapo 应用中：**设置 → 高级 → 摄像头账户** — 创建本地账户（不是 TP-Link 账户）
2. 在路由器的设备列表中找到摄像头的 IP
3. 在 `.env` 中设置：
   ```env
   CAMERA_HOST=192.168.1.xxx
   CAMERA_USER=your-local-user
   CAMERA_PASS=your-local-pass
   ```

### 语音（ElevenLabs）

1. 在 [elevenlabs.io](https://elevenlabs.io/) 获取 API 密钥
2. 在 `.env` 中设置：
   ```env
   ELEVENLABS_API_KEY=sk_...
   ELEVENLABS_VOICE_ID=...   # 可选，省略时使用默认语音
   ```
3. 语音通过 go2rtc 通过摄像头内置扬声器播放（首次运行时自动下载）

---

## TUI

familiar-ai 包含一个用 [Textual](https://textual.textualize.io/) 构建的终端 UI：

- 可滚动的对话历史，支持实时流式文本
- 为 `/quit`、`/clear` 提供制表符补全
- 在代理思考时可以中断它（通过输入内容）
- **对话日志**自动保存到 `~/.cache/familiar-ai/chat.log`

在另一个终端中跟踪日志（便于复制粘贴）：
```bash
tail -f ~/.cache/familiar-ai/chat.log
```

---

## 人设（ME.md）

你的伙伴的个性定义在 `ME.md` 中。这个文件被 gitignored — 它完全属于你。

参考 [`persona-template/en.md`](./persona-template/en.md) 获取示例，或 [`persona-template/ja.md`](./persona-template/ja.md) 获取日文版本。

---

## 常见问题

**Q: 没有 GPU 也能用吗？**
可以的。嵌入模型（multilingual-e5-small）在 CPU 上运行良好。GPU 会加快速度但不是必需的。

**Q: 能用 Tapo 以外的摄像头吗？**
任何支持 ONVIF + RTSP 的摄像头都应该可以工作。我们用 Tapo C220 进行了测试。

**Q: 我的数据会被发送到其他地方吗？**
图像和文本会被发送到你选择的 LLM API 进行处理。记忆存储在本地 `~/.familiar_ai/` 中。

**Q: 为什么代理写的是 `（...）` 而不是说话？**
确保设置了 `ELEVENLABS_API_KEY`。没有它的话，语音功能会被禁用，代理会回退到文字。

## 技术背景

想了解它的工作原理？参阅 [docs/technical.md](./docs/technical.md) 了解 familiar-ai 背后的研究和设计决策 — ReAct、SayCan、Reflexion、Voyager、欲望系统等。

## 许可证

[MIT](./LICENSE)
