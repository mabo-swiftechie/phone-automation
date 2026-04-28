# AI電話自動化システム — 操作手順書

> 対象者：不動産管理会社の担当者  
> 目的：AIによる空室確認（メール・電話）の自動化操作

---

## 目次

1. [事前準備](#1-事前準備)
2. [システム起動](#2-システム起動)
3. [初回設定](#3-初回設定)
4. [機能別操作手順](#4-機能別操作手順)
5. [FastAPI API 利用](#5-fastapi-api-利用)
6. [トラブルシューティング](#6-トラブルシューティング)
7. [終了方法](#7-終了方法)

---

## 1. 事前準備

### 1.1 uv のインストール（初回のみ）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows の場合：
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

インストール後、ターミナルを再起動してください。

### 1.2 API Key の取得（事前に準備）

| サービス | 必須 | 用途 | 取得先 |
|----------|------|------|--------|
| OpenAI | ✅ 必須 | メール生成・返信解析 | https://platform.openai.com/api-keys |
| Retell AI | △ 電話確認用 | AI音声通話 | https://retellai.com |
| Gmail | △ メール確認用 | メール送信 | Googleアカウント設定 → アプリパスワード |

> **Retell AI** は Web Call（ブラウザ通話）機能が無料でテスト可能です。

---

## 2. システム起動

### 2.1 起動コマンド

```bash
uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation
```

### 2.2 起動確認

正常に起動すると、ターミナルに以下が表示されます：

```
🚀 FastAPI started at http://localhost:8000
🖥️  Streamlit started at http://localhost:8501
```

ブラウザで以下のURLにアクセスしてください：

| サービス | URL |
|----------|-----|
| **メインUI（Streamlit）** | http://localhost:8501 |
| **API（FastAPI）** | http://localhost:8000 |

> ブラウザが自動で開かない場合は、手動で http://localhost:8501 を開いてください。

---

## 3. 初回設定

### 3.1 設定画面を開く

1. ブラウザで http://localhost:8501 を開く
2. 左サイドバーの「⚙️ 設定」をクリック

### 3.2 API Key を入力

#### OpenAI（必須）
```
OpenAI API Key: sk-proj-xxxxx...
```

#### Retell AI（電話確認を使う場合）
```
Retell API Key: key_xxxxx...
Retell Agent ID: agent_xxxxx...
```

#### Gmail（メール確認を使う場合）
```
Gmailアドレス: your@gmail.com
Gmailアプリパスワード: xxxx xxxx xxxx xxxx
```

#### 会社情報（メール署名用）
```
会社名: 〇〇不動産
担当者名: 山田太郎
```

### 3.3 保存

「保存」ボタンをクリックすると、設定は `~/.phone_automation/config.yaml` に保存されます。

---

## 4. 機能別操作手順

### 4.1 🏠 物件管理

**物件の登録**

1. 左サイドバー「🏠 物件管理」をクリック
2. 「＋ 新規物件登録」を展開
3. 以下を入力：
   - 物件名（必須）
   - 住所
   - 電話番号（電話確認用）
   - メールアドレス（メール確認用）
   - 管理会社名
   - 物件URL
4. 「登録」ボタンをクリック

**物件の編集・削除**

- 一覧から物件をクリックして展開
- 編集後「保存」、または「削除」をクリック

---

### 4.2 📧 メール確認

**手順**

1. 左サイドバー「📧 メール確認」をクリック
2. 確認したい物件を選択
3. 「AIメール生成」ボタンをクリック → 確認メールが自動生成される
4. 内容を確認・修正
5. 「Gmailで送信」ボタンをクリック
6. 返信が届いたら、「返信を解析」ボタンをクリック → AIが結果を抽出

**確認結果の自動抽出項目**

- 空室状況
- 外国人入居可否
- 中国人入居可否
- 特別条件
- 月額賃料
- 入居可能日

---

### 4.3 📞 電話確認

**Web Call での確認（無料テスト可能）**

1. 左サイドバー「📞 電話確認」をクリック
2. 確認したい物件を選択
3. 「🌐 Web Call 開始」ボタンをクリック
4. ブラウザのマイク許可を求められたら「許可」
5. 表示された「Start 通話」ボタンをクリック
6. AIと会話（マイクに向かって話す）
7. 「Stop 通話」ボタンをクリックして終了
8. 上部の「結果を取得」ボタンをクリック → 通話結果が自動解析される

**電話発信での確認**

FastAPI API から発信トリガー可能（後述）。

---

### 4.4 📊 結果一覧

1. 左サイドバー「📊 結果一覧」をクリック
2. 全物件の確認状況がダッシュボード表示
3. 「CSV ダウンロード」ボタンでエクセル出力可能

---

### 4.5 💬 会話テンプレート

**テンプレートの作成**

1. 左サイドバー「💬 会話テンプレート」をクリック
2. 「ブロック管理」タブで話術の「ブロック」を作成
3. 「テンプレート管理」タブでブロックを組み合わせてテンプレート作成
4. 「物件割り当て」タブで物件にテンプレートを紐付け

**デフォルトテンプレート**

初期状態でデフォルトテンプレートが作成されています。特に設定しない場合はこれが使用されます。

---

## 5. FastAPI API 利用

### 5.1 API エンドポイント一覧

| メソッド | エンドポイント | 用途 |
|----------|----------------|------|
| GET | `/` | ヘルスチェック |
| POST | `/properties` | 物件登録 |
| GET | `/properties` | 物件一覧 |
| GET | `/properties/{id}` | 物件詳細 |
| PATCH | `/properties/{id}` | 物件更新 |
| POST | `/calls/trigger` | 電話発信トリガー |
| GET | `/calls/{property_id}` | 通話履歴取得 |
| POST | `/calls/webhook` | Retell Webhook受信 |
| GET | `/export/csv` | CSVエクスポート |

### 5.2 電話発信トリガー例

```bash
curl -X POST http://localhost:8000/calls/trigger \
  -H "Content-Type: application/json" \
  -d '{"property_id": "xxxxx-xxxxx-xxxxx"}'
```

### 5.3 Retell Webhook 設定

Retell AI Dashboard で以下の Webhook URL を設定：

```
http://localhost:8000/calls/webhook
```

> ※ 本番環境では `https://あなたのドメイン/calls/webhook` に変更してください。

---

## 6. トラブルシューティング

### Q1. `uvx` コマンドが見つからない

```bash
export PATH="$HOME/.local/bin:$PATH"
```

を実行するか、ターミナルを再起動してください。

### Q2. ポートが既に使用中と表示される

```bash
# 使用中のプロセスを確認
lsof -i :8501
lsof -i :8000

# 停止させる
kill $(lsof -t -i :8501)
kill $(lsof -t -i :8000)
```

### Q3. API Key を間違えて入力した

1. ブラウザの「⚙️ 設定」タブを開く
2. 正しい Key を再入力して「保存」

または、設定ファイルを直接編集：

```bash
# Mac/Linux
nano ~/.phone_automation/config.yaml

# Windows
notepad %USERPROFILE%\.phone_automation\config.yaml
```

### Q4. データをリセットしたい

```bash
rm ~/.phone_automation/data.db
```

次回起動時に自動で新規DBが作成されます。

### Q5. Retell AI の通話が繋がらない

- Retell AI の無料枠を超えていないか確認
- Agent ID が正しいか確認
- ブラウザのマイク許可が出ているか確認

---

## 7. 終了方法

ターミナルで `Ctrl+C` を押すと、FastAPI と Streamlit が同時に停止します。

```
👋 Shutting down...
```

と表示されたら終了完了です。

---

## 補足：データの保存場所

| データ | 保存場所 |
|--------|----------|
| API Key・設定 | `~/.phone_automation/config.yaml` |
| 物件データ・通話記録 | `~/.phone_automation/data.db` |
| 通話録音 | `recordings/`（プロジェクト内） |

> `~` はユーザーのホームディレクトリを指します。  
> 例: `/Users/あなたの名前/.phone_automation/`
