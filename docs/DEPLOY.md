# クラウドデプロイガイド

## 目次

1. [Replit（ブラウザのみ）](#1-replitブラウザのみ)
2. [Docker（ローカル・データ永続）](#2-dockerローカルデータ永続)
3. [uvx（ローカル・最も簡単）](#3-uvxローカル最も簡単)

---

## 1. Replit（ブラウザのみ）

### ワンクリックデプロイ

```
https://replit.com/new/github/mabo-swiftechie/phone-automation
```

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

### 注意

- 無料枠では **48時間アクセスがないとスリープ**（再アクセスで復帰）
- URL は再起動ごとに変更される場合あり
- 有料プラン（$5/月）で固定URL + データ永続化

---

## 2. Docker（ローカル・データ永続）

### 前提

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) がインストール済み

### 手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation

# 2. 環境変数ファイルを作成
cp .env.example .env
# .env を編集して API Key を入力

# 3. 起動
docker compose up -d
```

ブラウザで http://localhost:8501 を開く。

### データについて

- 物件・問い合わせデータは `./data/` ディレクトリに保存
- コンテナを再起動してもデータは消えない
- バックアップする場合は `./data/` をコピー

### 操作コマンド

```bash
docker compose up -d       # 起動（バックグラウンド）
docker compose logs -f      # ログ確認
docker compose down         # 停止
docker compose down -v      # 停止＋データ削除
```

---

## 3. uvx（ローカル・最も簡単）

### 前提

不要。[uv](https://docs.astral.sh/uv/) は自動インストールされる。

### 手順

**Mac / Linux：**

```bash
# リポジトリをクローン
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation

# 起動スクリプトを実行（初回は uv を自動インストール）
bash scripts/start.sh
```

**Windows：**

```cmd
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
scripts\start.bat
```

ブラウザで http://localhost:8501 を開く。

### データについて

- データは `~/.phone_automation/` に保存（Mac/Linux）
- Windows の場合は `C:\Users\<ユーザー名>\.phone_automation\`

### 環境変数の設定

`.env.example` を参考に環境変数を設定：

```bash
export OPENAI_API_KEY=sk-proj-...
export GMAIL_ADDRESS=xxx@gmail.com
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

または UI の ⚙️「設定」タブから入力。

---

## 比較

| 項目 | Replit | Docker | uvx |
|------|--------|--------|-----|
| 費用 | 無料〜$5/月 | 無料 | 無料 |
| データ永続 | 有料のみ | ✅ | ✅ |
| 固定URL | 有料のみ | ローカル | ローカル |
| 技術知識 | 不要 | Docker要 | 不要 |
| インストール | なし | Docker Desktop | なし（自動） |
