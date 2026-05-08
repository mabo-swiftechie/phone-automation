# AI電話自動化システム — 操作手順書

> 対象者：不動産管理会社の担当者
> 最終更新：2026-05-08

---

## 目次

1. [事前準備](#1-事前準備)
2. [システム起動](#2-システム起動)
3. [初回設定](#3-初回設定)
4. [機能別操作手順](#4-機能別操作手順)
5. [Demo Mode（テストモード）](#5-demo-modeテストモード)
6. [FastAPI API 利用](#6-fastapi-api-利用)
7. [プランと機能](#7-プランと機能)
8. [トラブルシューティング](#8-トラブルシューティング)

---

## 1. 事前準備

### 1.1 システム起動

```bash
cd phone-automation
bash run.sh
```

ブラウザで http://localhost:8501 を開く。

### 1.2 API Key の取得

| サービス | 必須 | 用途 | 取得先 |
|----------|------|------|--------|
| OpenAI | ✅ 必須 | メール生成・返信解析 | https://platform.openai.com/api-keys |
| Retell AI | △ 電話用 | AI音声通話 | https://retellai.com |
| Gmail | △ メール用 | メール送信 | Googleアカウント → アプリパスワード |

---

## 2. システム起動

### 2.1 アクセス先

| 環境 | UI (Streamlit) | API (FastAPI) |
|------|----------------|---------------|
| ローカル | http://localhost:8501 | http://localhost:8000 |
| AWS | http://\<EC2_IP\>:8501 | http://\<EC2_IP\>:8000 |

### 2.2 起動確認

ブラウザで左サイドバーのメニューが表示されればOK。

---

## 3. 初回設定

### 3.1 設定画面を開く

左サイドバー「⚙️ 設定」をクリック。

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

#### Budget Agent（低コスト通話・任意）
```
Retell Budget Agent ID: agent_xxxxx...
```
GPT-4.1-mini を使用する低コスト Agent。通話品質はやや下がるが、コストは約20%安。

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

#### プラン選択

| プラン | 説明 |
|--------|------|
| free | テスト用（MockProvider） |
| lightweight | Retell AI で実際の通話 |
| full | バッチ通話 + Conversation Flow |

> Retell API Key と Agent ID を設定すると自動的に lightweight に昇格。

### 3.3 保存

「保存」ボタンをクリック。設定は `~/.phone_automation/config.yaml` に保存。

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
- 編集後「保存」、または「削除」

---

### 4.2 📧 メール確認

1. 左サイドバー「📧 メール確認」をクリック
2. 確認したい物件を選択
3. 「AIメール生成」ボタンをクリック → 確認メールが自動生成
4. 内容を確認・修正
5. 「Gmailで送信」ボタンをクリック
6. 返信が届いたら、「返信を解析」ボタンをクリック → AIが結果を抽出

**自動抽出項目**: 空室状況、外国人入居可否、中国人入居可否、特別条件、月額賃料、入居可能日

---

### 4.3 📞 電話確認

**Web Call（無料テスト）**

1. 左サイドバー「📞 電話確認」をクリック
2. 物件を選択
3. 「🌐 Web Call 開始」ボタンをクリック
4. ブラウザのマイク許可 → 「許可」
5. 「Start 通話」→ AIと会話 → 「Stop 通話」
6. 「結果を取得」ボタンで通話結果を確認

> **注意**: Web Call はブラウザのマイクを使用するため、HTTPS が必要です。
> - ローカル (localhost): HTTP で動作
> - リモート (EC2 等): Cloudflare Tunnel 等で HTTPS 化が必要
> - 詳細は [デプロイガイド](DEPLOY.md#4-cloudflare-tunnelhttps公開) を参照

**実際の電話発信**

FastAPI API から発信トリガー（lightweight以上のプランが必要）:

```bash
curl -X POST http://localhost:8000/calls/trigger \
  -H "Content-Type: application/json" \
  -d '{"property_id": "xxxxx-xxxxx"}'
```

**割り込み対応**

AIは以下の8種類の割り込みを認識・処理します：

| 割り込みタイプ | 例 | AIの対応 |
|---------------|-----|---------|
| BACKCHANNEL | 「はいはい」「ええ」 | 即時確認して続行 |
| CANCELLATION | 「やっぱいいです」 | 簡潔に終了 |
| CORRECTION | 「違います、〇〇です」 | 訂正を反映 |
| REDIRECT | 「それは別の担当で」 | 柔軟に対応 |
| CLARIFICATION | 「どういう意味？」 | 分かりやすく説明 |
| RAPID_FIRE | 連続した質問 | 1つずつ確実に回答 |
| NEW_INFO | 「あ、〇〇でした」 | 情報を更新 |
| HURRY | 「早くして」 | 簡潔にまとめる |

---

### 4.4 📊 結果一覧

1. 左サイドバー「📊 結果一覧」をクリック
2. 全物件の確認状況がダッシュボード表示
3. 「CSV ダウンロード」ボタンでエクセル出力

---

### 4.5 💬 会話テンプレート

1. 左サイドバー「💬 会話テンプレート」をクリック
2. 「ブロック管理」タブで話術のブロックを作成
3. 「テンプレート管理」タブでブロックを組み合わせ
4. 「物件割り当て」タブで物件にテンプレートを紐付け

---

## 5. Demo Mode（テストモード）

1. 左サイドバー「🧪 Demo Mode」をクリック
2. 「🚀 テストデータ生成」ボタンをクリック
3. 8件のテスト物件 + シミュレーション結果が自動生成

### テストシナリオ

| # | シナリオ | 空室 | 外国人 | 中国人 | 特徴 |
|---|----------|------|--------|--------|------|
| A | 標準ケース | あり | OK | OK | 全てOK |
| B | 入居制限 | あり | NG | NG | 外国人不可 |
| C | 満室 | なし | 不明 | 不明 | キャンセル待ち |
| D | 条件付き | あり | 条件付 | 不可 | 保証会社必須 |
| E | 留守電 | 不明 | 不明 | 不明 | 再架電必要 |
| F | 曖昧回答 | 確認中 | 未確認 | 未確認 | 要再確認 |
| A2 | 詳細条件 | あり | OK | OK | 敷2礼1ペット不可 |
| C2 | 満室→予定 | なし | OK | OK | 3ヶ月後入居可 |

---

## 6. FastAPI API 利用

### エンドポイント一覧

| メソッド | エンドポイント | 用途 |
|----------|----------------|------|
| GET | `/` | ヘルスチェック |
| POST | `/properties` | 物件登録 |
| GET | `/properties` | 物件一覧 |
| GET | `/properties/{id}` | 物件詳細 |
| PATCH | `/properties/{id}` | 物件更新 |
| POST | `/calls/trigger` | 電話発信トリガー |
| POST | `/calls/batch-trigger` | バッチ電話発信（full プランのみ） |
| GET | `/calls/{property_id}` | 通話履歴取得 |
| POST | `/calls/webhook` | Retell Webhook受信 |
| POST | `/calls/webhook/retell` | Retell Webhook（エイリアス） |
| GET | `/export/csv` | CSVエクスポート |

### API ドキュメント

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

### Retell Webhook 設定

Retell AI Dashboard で以下の Webhook URL を設定：

- ローカル: `http://localhost:8000/calls/webhook`（ngrok等が必要）
- AWS: `http://<EC2_IP>:8000/calls/webhook`

---

## 7. プランと機能

| 機能 | Free | Lightweight ($20) | Full ($100) |
|------|------|-------------------|-------------|
| Web Call テスト | ✅ | ✅ | ✅ |
| 実際の電話発信 | ❌ | ✅ | ✅ |
| バッチ発信 | ❌ | ❌ | ✅ |
| 割り込み効果 | ~70% | ~85% | ~95% |
| 高度ノイズ除去 | ❌ | ❌ | ✅ |
| 通話数/月 | テストのみ | 45-60 | 240-320 |

---

## 8. トラブルシューティング

### Q1. ポートが既に使用中

```bash
lsof -i :8501
kill $(lsof -t -i :8501)
```

`run.sh` は自動的にポートをクリーンアップします。

### Q2. API Key を間違えた

「⚙️ 設定」タブで正しい Key を再入力して「保存」。

### Q3. データをリセット

```bash
rm ~/.phone_automation/data.db
```

### Q4. Retell 通話が繋がらない

- Retell API Key と Agent ID が正しいか確認
- プランが lightweight 以上か確認
- ブラウザのマイク許可を確認（Web Call の場合）

### Q5. AWS でサービスが起動しない

```bash
sudo journalctl -u phone-api -n 20
sudo journalctl -u phone-ui -n 20
sudo systemctl restart phone-api phone-ui
```

---

## データの保存場所

| データ | ローカル | AWS EC2 |
|--------|----------|---------|
| 設定 | `~/.phone_automation/config.yaml` | 同左 |
| データベース | `~/.phone_automation/data.db` | 同左 |

> **セキュリティ**: config.yaml はGit管理対象外です。API Keyの漏洩にご注意ください。
