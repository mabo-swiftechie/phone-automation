# クラウドデプロイガイド

> 非開発者の方がコマンドラインを使わずに利用できるデプロイ方法です。

---

## 推奨：Hugging Face Spaces（無料）

「Duplicate this Space」ボタンを押すだけで、自分の環境が作れます。

### 必要なもの

- Hugging Face アカウント（https://huggingface.co で無料登録）
- API Key（config.yaml で受け取ったもの）

### デプロイ手順（1回だけ設定）

**ステップ1：テンプレートSpaceをDuplicate**

1. ブラウザでテンプレートSpaceのURLを開く
2. 右上の「⋯」メニュー →「Duplicate this space」をクリック
3. Space名を入力（例：`my-phone-automation`）
4. 「Duplicate」をクリック
5. 数分待つ → 自動的にビルドが始まります

**ステップ2：API Keyを設定**

1. 作成されたSpaceの「Settings」タブを開く
2. 「Repository secrets」セクションまでスクロール
3. 以下のシークレットを追加：

| 名前 | 値 |
|------|-----|
| `OPENAI_API_KEY` | sk-proj-xxxxx... |
| `RETELL_API_KEY` | key_xxxxx... |
| `RETELL_AGENT_ID` | agent_xxxxx... |
| `GMAIL_ADDRESS` | your@gmail.com |
| `GMAIL_APP_PASSWORD` | xxxx xxxx xxxx xxxx |
| `COMPANY_NAME` | 会社名 |
| `CONTACT_PERSON` | 担当者名 |

4. 「Save」をクリック
5. Spaceが自動的に再起動します

**ステップ3：アクセス**

- Spaceの「App」タブをクリック → ブラウザでUIが開きます
- URLは `https://あなたのユーザー名-my-phone-automation.hf.space`

---

## 注意事項

- **48時間アクセスがないとスリープします**（再度アクセスすれば数秒〜数十秒で復帰）
- **無料枠ではデータがリセットされる場合があります**
  - 重要なデータはこまめにCSVダウンロードしてください
  - データを永続化する場合は Persistent Storage（$5/月〜）を追加

---

## 代替：Railway（月$5〜）

より安定した本番運用向け。

| 項目 | 内容 |
|------|------|
| 料金 | ~$5-8/月 |
| データ永続化 | ✅ 永続ボリューム |
| スリープ | なし |
| セットアップ | GitHub連携 + Dockerfile |

---

## 開発者向け：必要なファイル

クラウドデプロイには以下の追加ファイルが必要です：

| ファイル | 用途 |
|---------|------|
| `Dockerfile` | コンテナ定義 |
| `nginx.conf` | Streamlit/FastAPIのルーティング |
| `supervisord.conf` | 2プロセスの同時起動 |

これらは開発者が1回だけ作成します。ユーザー側の作業はありません。
