# 交付チェックリスト

> 朋友にシステムを渡す際の準備・確認事項。

---

## 1. Replit にデプロイ

### 1-1. Replit アカウント作成
1. https://replit.com にアクセス
2.「Sign Up」で Google アカウント等で登録（無料）

### 1-2. プロジェクト作成
1. 以下のURLをブラウザで開く：
   ```
   https://replit.com/new/github/mabo-swiftechie/phone-automation
   ```
2.「Create Repl」をクリック → 自動ビルド開始

### 1-3. Secrets 設定
左サイドバーの 🔒「Secrets」アイコンをクリックし、以下を追加：

| Key | Value（例） | 備考 |
|-----|------------|------|
| `OPENAI_API_KEY` | `sk-proj-...` | 必須 |
| `RETELL_API_KEY` | `key_...` | 電話を使う場合 |
| `RETELL_AGENT_ID` | `agent_...` | 電話を使う場合 |
| `GMAIL_ADDRESS` | `xxx@gmail.com` | メールを使う場合 |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | メールを使う場合 |
| `COMPANY_NAME` | `〇〇不動産` | 任意 |
| `CONTACT_PERSON` | `担当者名` | 任意 |

### 1-4. 起動確認
▶「Run」ボタンを押す → ブラウザで UI が表示されることを確認

---

## 2. API Key の準備

### 方法A：既存アカウントを共有（早い）

config.yaml をそのまま渡す。各サービスの無料枠：

| サービス | 無料枠 | 月額費用 |
|----------|--------|---------|
| OpenAI | なし（従量課金） | ~$5-20/月（使用量による） |
| Retell AI | 無料クレジットあり | 従量 ~$0.10/分 |
| Gmail | 無料 | ¥0 |

**注意：同一API Keyを複数人で使う場合、利用量が合算される。**

### 方法B：朋友に各自取得してもらう（推奨）

| サービス | 登録URL | 必要なもの | 取得手順 |
|----------|---------|-----------|---------|
| **OpenAI** | https://platform.openai.com/signup | メールアドレス | 登録 → API Keys → Create new key → コピー |
| **Retell AI** | https://retellai.com | メールアドレス | 登録 → Dashboard → API Keys → コピー |
| **Gmail** | https://myaccount.google.com | Googleアカウント | セキュリティ → 2段階認証 → アプリパスワード |

---

## 3. 朋友に渡すもの

### 必須
- [ ] Replit のプロジェクトURL（デプロイ後に共有）
- [ ] API Key（方法Aの場合：config.yaml / 方法Bの場合：取得手順）

### あるとよい
- [ ] [操作手順書](docs/OPERATION_MANUAL.md) のリンク
- [ ] [メール・電話サンプル](docs/samples/) のリンク

### 朋友の最初の操作
1. Replit URLを開く
2. ▶「Run」を押す
3. 🧪「Demo Mode」→「テストデータ生成」で体験
4. 🏠「物件管理」で実際の物件を登録
5. 📧「メール確認」または 📞「電話確認」を開始

---

## 4. 注意事項

- Replit 無料枠では、**48時間アクセスがないとスリープ**する（再アクセスで復帰）
- Replit の無料枠制限：月間一定のコンピュート時間
- OpenAI API Key は**絶対に公開リポジトリやチャットに貼らない**
- Gmail アプリパスワードも同様に取り扱い注意
