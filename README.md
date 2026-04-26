# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

## クイックスタート（初回セットアップ）

```bash
# 1. リポジトリをクローン
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation

# 2. 設定ファイルをコピー
cp .env.example .env
cp config.example.yaml config.yaml

# 3. 実際のAPI Keyを設定（どちらかの方法）
#    方法A: .env をエディタで編集
#    方法B: アプリ起動後、ブラウザの「設定」タブで入力

# 4. 起動
## Mac
./start.sh

## Windows
start.bat

# 5. ブラウザが自動で開く → http://localhost:8501
```

## 必要なAPI Key取得方法

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

## 設定ファイル

| ファイル | 用途 | Git管理 |
|---------|------|---------|
| `.env.example` | API Key のテンプレート | される |
| `.env` | 実際のAPI Key | **されない** |
| `config.example.yaml` | 設定のテンプレート | される |
| `config.yaml` | 実際の設定（Key含む） | **されない** |
| `data.db` | 物件・通話データ | **されない** |

## アーキテクチャ

```
Streamlit (ブラウザUI, localhost:8501)
├── 🏠 物件管理 — 登録・編集・削除
├── 📧 メール確認 — AI生成→Gmail送信→返信AI解析
├── 📞 電話確認 — Retell AI Web Call→結果取得
├── 📊 結果一覧 — ダッシュボード + CSV出力
├── 💬 会話テンプレート — 積木式話術管理
└── ⚙️ 設定 — API Key等
SQLite (ローカルDB, data.db)
```

## ワークフロー

```
物件登録
  ├── 📧 メール確認ルート
  │   AI邮件生成 → Gmail送信 → 返信受信 → AI解析 → 結果保存
  │
  └── 📞 電話確認ルート
      テンプレート選択 → Web Call開始 → AI通話 → 結果取得 → 結果保存
                                        ↓
                              結果一覧 → CSV ダウンロード
```

## 技術スタック

- Python 3.9+, Streamlit 1.50+
- SQLite (ローカルDB)
- OpenAI GPT-4.1-mini (メール生成・解析)
- Retell AI (音声通話AI)
- Gmail SMTP (メール送信)

## ファイル構成

```
phone_automation/
├── app/
│   ├── ui.py                    # Streamlit メインUI
│   ├── database.py              # SQLite CRUD
│   ├── config_manager.py        # YAML設定管理
│   └── services/
│       ├── email_sender.py      # Gmail SMTP送信
│       ├── email_parser.py      # AI返信解析
│       ├── retell.py            # Retell AI通話
│       └── template_manager.py  # 会話テンプレート管理
├── .env.example                 # API Key テンプレート
├── config.example.yaml          # 設定テンプレート
├── requirements.txt             # Python依存パッケージ
├── start.sh                     # Mac起動スクリプト
├── start.bat                    # Windows起動スクリプト
└── README.md
```

## 同事への引き継ぎ手順

1. GitHub から clone
2. `cp .env.example .env && cp config.example.yaml config.yaml`
3. OpenAI API Key を `.env` に記入
4. `./start.sh` で起動
5. ブラウザの「設定」タブで残りのKeyを入力
6. 完了

## 詳細ドキュメント

- [docs/architecture.md](docs/architecture.md) — アーキテクチャ設計、技術選定理由、音声AI比較調査
- [docs/2026-04-26_retell_agent_setup.md](docs/2026-04-26_retell_agent_setup.md) — Retell AI エージェント設定記録
