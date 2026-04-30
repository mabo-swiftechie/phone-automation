# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

---

## クイックスタート

### 方法1：Replit（推奨・ブラウザのみ）

[![Replit で開く](https://replit.com/badge/github/mabo-swiftechie/phone-automation)](https://replit.com/new/github/mabo-swiftechie/phone-automation)

1. 上のボタンをクリック → Replit にログイン → 自動でプロジェクトが作成される
2. 左サイドバー 🔒「Secrets」で API Key を設定（下記参照）
3. ▶「Run」ボタンを押す
4. ブラウザで UI が開く

### 方法2：ローカル起動

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation
```

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

> ローカル起動の場合は、ブラウザの「⚙️ 設定」タブから入力してもOK。

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

## ドキュメント

- [操作手順書](docs/OPERATION_MANUAL.md) — 各機能の使い方・テスト結果
- [メール・電話サンプル](docs/samples/) — 実際の送信メール・通話記録の例
- [電話発信セットアップ](docs/PHONE_SETUP.md) — 電話番号の取得方法
- [クラウドデプロイ](docs/DEPLOY.md) — Replit / Railway / HF Spaces
- [アーキテクチャ設計](docs/architecture.md) — 技術選定理由
- [要件定義仕様書](docs/REQUIREMENTS_SPEC.md) — システム要件

---

## 技術スタック

Python 3.9+ / Streamlit / FastAPI / SQLite / OpenAI GPT-4.1-mini / Retell AI / Gmail SMTP
