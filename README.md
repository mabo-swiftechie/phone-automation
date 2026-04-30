# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

## クイックスタート

```bash
# 1. uv をインストール（初回のみ）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 起動
uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation
```

起動後、自動的に以下が立ち上がります：

| サービス | URL | 用途 |
|----------|-----|------|
| Streamlit UI | http://localhost:8501 | ブラウザで操作 |
| FastAPI API | http://localhost:8000 | Webhook / API |

`Ctrl+C` で両方同時に停止。

---

## 必要なAPI Key取得方法

初回起動後、ブラウザの「設定」タブで入力。

### OpenAI（必須）
1. https://platform.openai.com/signup で登録
2. API Keys → Create new secret key
3. `sk-proj-xxxxx...` をコピー

### Retell AI（電話確認を使う場合）
1. https://retellai.com で登録
2. Dashboard → API Keys → Copy
3. Dashboard → Agents → Agent ID をコピー
4. ※ Web Call（ブラウザ通話）は無料でテスト可能

### Gmail アプリパスワード（メール確認を使う場合）
1. Googleアカウント → セキュリティ
2. 2段階認証を有効化
3. アプリパスワード → 生成（「その他」→「メール自動化」等）
4. 16桁のパスワードをコピー

---

## 設定・データ

| ファイル | 場所 | 用途 |
|---------|------|------|
| `config.yaml` | `~/.phone_automation/` | API Key等の設定 |
| `data.db` | `~/.phone_automation/` | 物件・通話データ |

環境変数 `PHONE_AUTOMATION_DATA` でデータディレクトリを変更可能。

---

## アーキテクチャ

```
uvx phone-automation
├── FastAPI (localhost:8000)  ── Webhook / REST API
└── Streamlit (localhost:8501) ── ブラウザUI
    ├── 🏠 物件管理
    ├── 📧 メール確認
    ├── 📞 電話確認 (Retell AI)
    ├── 📊 結果一覧 + CSV出力
    ├── 💬 会話テンプレート
    └── ⚙️ 設定
SQLite (~/.phone_automation/data.db)
```

---

## 技術スタック

- Python 3.9+, Streamlit 1.50+, FastAPI
- SQLite（ローカルDB、零外部依存）
- OpenAI GPT-4.1-mini（メール生成・解析）
- Retell AI（音声通話AI）
- Gmail SMTP（メール送信）
- uv/uvx（パッケージ管理）

---

## ファイル構成

```
phone_automation/
├── app/
│   ├── cli.py              # エントリポイント（uvx起動）
│   ├── main.py             # FastAPI アプリ
│   ├── ui.py               # Streamlit UI
│   ├── database.py         # SQLite CRUD
│   ├── config_manager.py   # YAML設定管理
│   ├── paths.py            # データディレクトリ管理
│   ├── api/                # FastAPI ルート
│   │   ├── calls.py
│   │   ├── properties.py
│   │   └── export.py
│   ├── models/             # Pydantic スキーマ
│   │   └── schemas.py
│   └── services/           # 業務ロジック
│       ├── retell.py
│       ├── email_sender.py
│       ├── email_parser.py
│       ├── template_manager.py
│       ├── line_notify.py
│       └── property.py
├── pyproject.toml          # パッケージ定義
├── requirements.txt
└── README.md
```

---

## 同事への引き継ぎ手順

1. uv をインストール: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. 起動: `uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation`
3. ブラウザの「設定」タブでAPI Keyを入力
4. 完了

---

## 詳細ドキュメント

- [docs/architecture.md](docs/architecture.md) — アーキテクチャ設計、技術選定理由
- [docs/OPERATION_MANUAL.md](docs/OPERATION_MANUAL.md) — 操作手順書、テスト検証結果
- [docs/PHONE_SETUP.md](docs/PHONE_SETUP.md) — 電話発信セットアップガイド
- [docs/REQUIREMENTS_SPEC.md](docs/REQUIREMENTS_SPEC.md) — 要件定義仕様書
