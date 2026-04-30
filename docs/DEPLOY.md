# クラウドデプロイガイド

## 推奨：Replit（無料・ブラウザのみ）

### ワンクリックデプロイ

以下のURLをブラウザで開く：

```
https://replit.com/new/github/mabo-swiftechie/phone-automation
```

または README の「Replit で開く」ボタンをクリック。

### 設定手順

1. Replit にログイン（Google アカウントでOK、無料）
2.「Create Repl」→ 自動ビルド開始
3. 左サイドバー 🔒「Secrets」で API Key を設定
4. ▶「Run」→ ブラウザで UI が開く

### Replit Secrets（環境変数）

| Key | 値の例 | 必須 |
|-----|--------|------|
| `OPENAI_API_KEY` | `sk-proj-...` | ✅ |
| `RETELL_API_KEY` | `key_...` | 電話を使う場合 |
| `RETELL_AGENT_ID` | `agent_...` | 電話を使う場合 |
| `GMAIL_ADDRESS` | `xxx@gmail.com` | メールを使う場合 |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | メールを使う場合 |
| `COMPANY_NAME` | `〇〇不動産` | 任意 |
| `CONTACT_PERSON` | `担当者名` | 任意 |

> 環境変数が設定されていれば、config.yaml は不要です。

---

## 代替方案

### Railway（月$5〜・本番向け）

| 項目 | 内容 |
|------|------|
| 料金 | ~$5-8/月 |
| データ永続化 | ✅ 永続ボリューム |
| セットアップ | GitHub連携 + Dockerfile |

### Hugging Face Spaces（無料）

| 項目 | 内容 |
|------|------|
| 料金 | 無料（Persistent Storageは$5/月〜） |
| セットアップ | Duplicate Space |
| 注意 | データがリセットされる場合あり |
