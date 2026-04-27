# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

## クイックスタート

### 方法A：uvx（推奨）

```bash
# 1. uv をインストール（初回のみ）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 起動
uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation
```

ブラウザが自動で開く → http://localhost:8501

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

## 設定・データ

| ファイル | 場所 | 用途 |
|---------|------|------|
| `config.yaml` | `~/.phone_automation/` | API Key等の設定 |
| `data.db` | `~/.phone_automation/` | 物件・通話データ |

環境変数 `PHONE_AUTOMATION_DATA` でデータディレクトリを変更可能。

## アーキテクチャ

```
Streamlit (ブラウザUI, localhost:8501)
├── 🏠 物件管理 — 登録・編集・削除
├── 📧 メール確認 — AI生成→Gmail送信→返信AI解析
├── 📞 電話確認 — Retell AI Web Call→結果取得
├── 📊 結果一覧 — ダッシュボード + CSV出力
├── 💬 会話テンプレート — 積木式話術管理
└── ⚙️ 設定 — API Key等
SQLite (~/.phone_automation/data.db)
```

## 技術スタック

- Python 3.9+, Streamlit 1.40+
- SQLite (ローカルDB)
- OpenAI GPT-4.1-mini (メール生成・解析)
- Retell AI (音声通話AI)
- Gmail SMTP (メール送信)
- uv/uvx (パッケージ管理)

## ファイル構成

```
phone_automation/
├── app/
│   ├── cli.py                    # エントリポイント
│   ├── paths.py                  # データディレクトリ管理
│   ├── ui.py                     # Streamlit メインUI
│   ├── database.py               # SQLite CRUD
│   ├── config_manager.py         # YAML設定管理
│   └── services/
│       ├── email_sender.py       # Gmail SMTP送信
│       ├── email_parser.py       # AI返信解析
│       ├── retell.py             # Retell AI通話
│       └── template_manager.py   # 会話テンプレート管理
├── pyproject.toml                # パッケージ定義
└── README.md
```

## 同事への引き継ぎ手順

1. uv をインストール: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. 起動: `uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation`
3. ブラウザの「設定」タブでAPI Keyを入力
4. 完了

## 詳細ドキュメント

- [docs/architecture.md](docs/architecture.md) — アーキテクチャ設計、技術選定理由、音声AI比較調査
- [docs/2026-04-26_retell_agent_setup.md](docs/2026-04-26_retell_agent_setup.md) — Retell AI エージェント設定記録
