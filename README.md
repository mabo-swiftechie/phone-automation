# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

---

## 初めての方へ：使い方

### ステップ1：ターミナルを開く

**Mac の場合：**
1. 画面右上の虫眼鏡アイコン（Spotlight検索）をクリック
2. `ターミナル` と入力 → Enter
3. 黒い画面（ターミナル）が開きます

**Windows の場合：**
1. スタートボタンをクリック
2. `PowerShell` と入力 → Enter
3. 青い画面（PowerShell）が開きます

### ステップ2：インストール（初回のみ）

ターミナルに以下をコピー＆ペーストして Enter を押す：

**Mac：**
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows：**
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> インストール完了後、**ターミナルを一度閉じて、もう一度開き直してください。**

### ステップ3：設定ファイルを置く

config.yaml（別途受け取ったファイル）を以下の場所に保存：

**Mac：** ホームフォルダの `.phone_automation` フォルダの中
```
~/.phone_automation/config.yaml
```

**Windows：** ユーザーフォルダの `.phone_automation` フォルダの中
```
C:\Users\あなたの名前\.phone_automation\config.yaml
```

**Mac での操作手順：**
1. ターミナルに以下を1行ずつコピー＆ペースト：
```
mkdir -p ~/.phone_automation
open ~/.phone_automation
```
2. フォルダが開くので、受け取った config.yaml をそのフォルダに入れる

### ステップ4：起動

ターミナルに以下をコピー＆ペーストして Enter：

```
uvx --from git+https://github.com/mabo-swiftechie/phone-automation.git phone-automation
```

以下が表示されたら起動成功：
```
🚀 FastAPI started at http://localhost:8000
🖥️  Streamlit started at http://localhost:8501
```

ブラウザで http://localhost:8501 を開いて使います。

### 終了方法

ターミナルで `Ctrl` + `C` を押すと終了します。

> 次回使うときは、ステップ4のコマンドをもう一度実行するだけです。

---

## 画面の使い方

| メニュー | できること |
|----------|-----------|
| 🏠 物件管理 | 物件を登録・編集・削除 |
| 📧 メール確認 | AIが確認メールを作成 → 送信 → 返信を自動解析 |
| 📞 電話確認 | AIが電話で空室確認（Web Callは無料テスト可能） |
| 📊 結果一覧 | 全物件の確認状況一覧 → CSVダウンロード |
| 💬 会話テンプレート | 電話で話す内容をカスタマイズ |
| 🧪 Demo Mode | テストデータで機能体験（初めての方におすすめ） |
| ⚙️ 設定 | API Keyなどの設定変更 |

> 初めての方は「🧪 Demo Mode」から始めるのがおすすめです。

---

## 起動後の画面

起動するとブラウザで以下の2つが動きます：

| URL | 用途 |
|-----|------|
| http://localhost:8501 | メイン画面（操作パネル） |
| http://localhost:8000 | API（裏側で動くもの） |

---

## 詳細ドキュメント

- [操作手順書](docs/OPERATION_MANUAL.md) — 各機能の詳しい使い方、テスト結果
- [電話発信セットアップ](docs/PHONE_SETUP.md) — 実際の電話をかけるための設定
- [アーキテクチャ設計](docs/architecture.md) — 技術的な設計資料
- [要件定義仕様書](docs/REQUIREMENTS_SPEC.md) — システムの要件定義
