# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

---

## クイックスタート

### 方法1：uvx（ローカル・推奨）

```bash
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
bash scripts/start.sh        # Mac/Linux
scripts\start.bat            # Windows
```

### 方法2：Docker（ローカル・データ永続）

```bash
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
cp .env.example .env         # API Key を入力
docker compose up -d
```

### 方法3：Replit（ブラウザのみ）

[![Replit で開く](https://replit.com/badge/github/mabo-swiftechie/phone-automation)](https://replit.com/new/github/mabo-swiftechie/phone-automation)

ブラウザで http://localhost:8501 を開く。

---

## 必要な設定（Secrets / 環境変数）

| 変数名 | 必須 | 取得先 |
|--------|------|--------|
| `OPENAI_API_KEY` | ✅ | https://platform.openai.com/api-keys |
| `RETELL_API_KEY` | △ 電話用 | https://retellai.com → Dashboard → API Keys |
| `RETELL_AGENT_ID` | △ 電話用 | Retell Dashboard → Agents |
| `GMAIL_ADDRESS` | △ メール用 | Googleアカウント |
| `GMAIL_APP_PASSWORD` | △ メール用 | Google → セキュリティ → アプリパスワード |
| `COMPANY_NAME` | 任意 | メール署名に使用 |
| `CONTACT_PERSON` | 任意 | メール署名に使用 |

> uvx の場合：ブラウザの「⚙️ 設定」タブから入力してもOK。
> Docker の場合：`.env` ファイルに記載。
> Replit の場合：🔒 Secrets パネルに設定。

---

## 画面一覧

| メニュー | 機能 |
|----------|------|
| 🏠 物件管理 | 物件の登録・編集・削除 |
| 📧 メール確認 | AIメール生成 → Gmail送信 → 返信自動解析 |
| 📞 電話確認 | AI音声通話（Web Call無料テスト / 実際の電話発信） |
| 📊 結果一覧 | 確認状況ダッシュボード → CSVダウンロード |
| 💬 会話テンプレート | 電話で話す内容をブロック単位でカスタマイズ |
| 🧪 Demo Mode | テストデータ一括生成（8シナリオ） |
| ⚙️ 設定 | API Key・会社情報の管理 |

---

## デプロイ方法の比較

| 項目 | uvx | Docker | Replit |
|------|-----|--------|--------|
| 費用 | 無料 | 無料 | 無料〜$5/月 |
| データ永続 | ✅ | ✅ | 有料のみ |
| インターネット公開 | 不要 | 不要 | ✅ 固定URL |
| 前提 | なし（自動） | Docker Desktop | ブラウザのみ |

---

## ドキュメント

- [操作手順書](docs/OPERATION_MANUAL.md) — 各機能の使い方・テスト結果
- [デプロイガイド](docs/DEPLOY.md) — Replit / Docker / uvx 詳細手順
- [メール・電話サンプル](docs/samples/) — 実際の送信メール・通話記録の例
- [電話発信セットアップ](docs/PHONE_SETUP.md) — 電話番号の取得方法
- [アーキテクチャ設計](docs/architecture.md) — 技術選定理由
- [要件定義仕様書](docs/REQUIREMENTS_SPEC.md) — システム要件

---

## 技術スタック

Python 3.9+ / Streamlit / FastAPI / SQLite / OpenAI GPT-4.1-mini / Retell AI / Gmail SMTP
