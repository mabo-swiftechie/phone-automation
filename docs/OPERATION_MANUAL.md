# AI電話自動化システム — 操作手順書

> 対象者：不動産管理会社の担当者  
> 目的：AIによる空室確認（メール・電話）の自動化操作

---

## 目次

1. [事前準備](#1-事前準備)
2. [システム起動](#2-システム起動)
3. [初回設定](#3-初回設定)
4. [機能別操作手順](#4-機能別操作手順)
5. [Demo Mode（テストモード）](#5-demo-modeテストモード)
6. [FastAPI API 利用](#6-fastapi-api-利用)
7. [トラブルシューティング](#7-トラブルシューティング)
8. [終了方法](#8-終了方法)
9. [テスト検証結果](#9-テスト検証結果)

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

## 5. Demo Mode（テストモード）

システムの全機能をテストするためのデモモードです。実際の電話やメールを使わずに動作確認できます。

### 5.1 テストデータの生成

1. 左サイドバー「🧪 Demo Mode」をクリック
2. 「🚀 テストデータ生成」ボタンをクリック
3. 8件のテスト物件 + メール・電話のシミュレーション結果が自動生成されます

### 5.2 テストシナリオ一覧

| # | シナリオ | 物件 | 空室 | 外国人 | 中国人 | 特徴 |
|---|----------|------|------|--------|--------|------|
| A | 空室あり・外国人OK | グランメゾン東京南青山 | あり | OK | OK | 標準ケース |
| B | 空室あり・外国人NG | サンシティ恵比寿 | あり | NG | NG | 入居制限 |
| C | 満室 | パークハウス新宿 | なし | 不明 | 不明 | キャンセル待ち |
| D | 条件付き | ロイヤルハイツ池袋 | あり | 条件付 | 不可 | 保証会社必須 |
| E | 留守電・不通 | コープ野馬世田谷 | 不明 | 不明 | 不明 | 再架電必要 |
| F | 曖昧回答 | メゾン・ド・上野 | 確認中 | 未確認 | 未確認 | 要再確認 |
| A2 | 詳細条件付きOK | ヴィラ代々木 | あり | OK | OK | 敷2礼1ペット不可 |
| C2 | 満室→予定あり | ハイツ練馬 | なし(予定) | OK | OK | 3ヶ月後入居可 |

### 5.3 テストフローガイド

1. **🧪 Demo Mode** → テストデータ生成
2. **📊 結果一覧** → ダッシュボード確認 → CSVダウンロードテスト
3. **🏠 物件管理** → 物件の登録・編集・削除テスト
4. **📧 メール確認** → 物件を選択 → AIメール生成 → 送信テスト
5. **📞 電話確認** → Web Callで実際に通話テスト（Retell AI Key必要）
6. **⚙️ 設定** → API Keyの保存・更新テスト

### 5.4 データのクリア

「🗑️ 全データ削除」ボタンで、全てのテストデータを初期化できます。

---

## 6. FastAPI API 利用

### 6.1 API エンドポイント一覧

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

### 6.2 電話発信トリガー例

```bash
curl -X POST http://localhost:8000/calls/trigger \
  -H "Content-Type: application/json" \
  -d '{"property_id": "xxxxx-xxxxx-xxxxx"}'
```

### 6.3 Retell Webhook 設定

Retell AI Dashboard で以下の Webhook URL を設定：

```
http://localhost:8000/calls/webhook
```

> ※ 本番環境では `https://あなたのドメイン/calls/webhook` に変更してください。

---

## 7. トラブルシューティング

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

## 8. 終了方法

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
| キー管理記録 | `~/.phone_automation/SECRETS_ARCHIVE.md` |
| 通話録音 | `recordings/`（プロジェクト内） |

> `~` はユーザーのホームディレクトリを指します。
> 例: `/Users/あなたの名前/.phone_automation/`

> **セキュリティ**: `config.yaml` と `SECRETS_ARCHIVE.md` はGit管理対象外です。API Keyの漏洩にご注意ください。

---

## 9. テスト検証結果（2026-04-29）

| テスト項目 | 結果 | 詳細 |
|-----------|------|------|
| Demo Mode データ生成 | ✅ | 8物件 + 17照会 + 5通話記録 |
| OpenAI メール生成 | ✅ | 敬語・会社名・担当者名 正常 |
| OpenAI メール解析 | ✅ | 6シナリオ全て正確に構造化 |
| Gmail SMTP 送信 | ✅ | maboatjapan@gmail.com 送信成功 |
| Retell Web Call 作成 | ✅ | call_id 発行、token 取得 |
| Retell Agent 接続 | ✅ | Property Vacancy Check JP (ja-JP) |
| 会話テンプレート Prompt | ✅ | 949文字のプロンプトが注入 |
| FastAPI 全端点 | ✅ | Health/Properties/Calls/CSV Export |
| CSV エクスポート | ✅ | 5件の通話記録 正常出力 |
| 情報セキュリティ | ✅ | API Key はGit履歴に未漏洩 |
