# 新機能ガイド

familiar-ai に追加された新機能について説明します。

## FileTool（ファイルツール）

エージェントが `workspace/` ディレクトリ内でファイル操作を行えるようにします。

### 機能

| ツール名 | 説明 |
|---------|------|
| `list_files` | ワークスペース内のファイル一覧を表示 |
| `read_file` | ファイルの内容を読み込み（最大行数制限あり） |
| `write_file` | ファイルに書き込み |
| `see_file` | 画像ファイルをBase64エンコードして取得 |

### セーフティ機能

- **ワークスペース制限**: `workspace/` ディレクトリ外へのアクセスを禁止
- **拒否リスト**: `.env`, `ME.md`, `.git`, `.venv` などへのアクセスをブロック
- **パストラバーサル対策**: `../` を使ったディレクトリ脱出を防止

### 使用例

```
エージェント: 「今日の観察をノートに書き込もう」
→ write_file("observations/2026-02-26.txt", "窓の外は晴れ...")
```

### 環境変数

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `FAMILIAR_WORKSPACE` | ワークスペースのパス | `./workspace` |

---

## WebTool（ウェブツール）

エージェントがインターネットにアクセスできるようにします。

### 機能

| ツール名 | 説明 |
|---------|------|
| `search` | DuckDuckGoを使ってWeb検索 |
| `fetch` | 指定URLのページ内容を取得 |

### 使用例

```
ユーザー: 「今日のニュース教えて」
エージェント: search("今日のニュース")
→ 検索結果を取得・要約
```

```
ユーザー: 「このサイトの内容読んで」
エージェント: fetch("https://example.com/article")
→ ページ内容を取得・要約
```

### 注意事項

- **レート制限**: DuckDuckGoにはレート制限があります。連続して多数の検索を行うと一時的にブロックされる可能性があります
- **コンテンツ制限**: 一部のサイトは取得できない場合があります

---

## プラグインシステム（予定）

将来的には以下の機能を実装予定です：

### フェーズ3: 動的プラグインロード

```python
# 目標: pyproject.toml から自動的にツールを読み込み
def load_available_tools() -> Dict[str, BaseTool]:
    """利用可能なツールを動的にロード"""
    tools = {}
    for module_name in TOOL_MODULES:
        if check_hardware(module_name):
            tools[module_name] = load_tool(module_name)
    return tools
```

### check_hardware() の実装

各ツールがハードウェア依存かどうかを判定：

```python
class FileTool(BaseTool):
    @classmethod
    def check_hardware(cls) -> bool:
        return True  # ハードウェア非依存

class CameraTool(BaseTool):
    @classmethod
    def check_hardware(cls) -> bool:
        # カメラが接続されているか確認
        return check_camera_available()
```

---

## 関連ファイル

- `src/familiar_agent/tools/file_tool.py` - FileTool実装
- `src/familiar_agent/tools/web_tool.py` - WebTool実装
- `src/familiar_agent/tools/__init__.py` - ツールエクスポート
- `tests/tools/test_file_tool.py` - FileToolユニットテスト
- `tests/tools/test_web_tool.py` - WebToolユニットテスト
