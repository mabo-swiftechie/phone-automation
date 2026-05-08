# AI電話自動化 — 空室確認システム

不動産管理会社にメール・電話で空室確認を自動化するシステム。

---

## クイックスタート

### 方法1：run.sh（ローカル・推奨）

```bash
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
bash run.sh
```

ブラウザで http://localhost:8501 を開く。

### 方法2：Docker

```bash
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
cp .env.example .env         # API Key を入力
docker compose up -d
```

### 方法3：AWS（本番運用）

```bash
aws --profile boma086 ec2 describe-instances --region ap-northeast-1
ssh -i ~/.ssh/boma086-tokyo.pem ubuntu@<EC2_PUBLIC_IP>
```

UI: `http://<EC2_PUBLIC_IP>:8501` / API: `http://<EC2_PUBLIC_IP>:8000`

---

## 必要な設定

| 変数名 | 必須 | 取得先 |
|--------|------|--------|
| `OPENAI_API_KEY` | ✅ | https://platform.openai.com/api-keys |
| `RETELL_API_KEY` | △ 電話用 | https://retellai.com → Dashboard → API Keys |
| `RETELL_AGENT_ID` | △ 電話用 | Retell Dashboard → Agents |
| `RETELL_AGENT_ID_BUDGET` | 任意 | 低コストAgent（GPT-4.1-mini） |
| `GMAIL_ADDRESS` | △ メール用 | Googleアカウント |
| `GMAIL_APP_PASSWORD` | △ メール用 | Google → セキュリティ → アプリパスワード |

> UI の「⚙️ 設定」タブから入力してもOK。

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
| ⚙️ 設定 | API Key・プラン・会社情報の管理 |

---

## 3段階プラン

| プラン | 月額 | 割り込み効果 | 通話数/月 | 用途 |
|--------|------|-------------|----------|------|
| **Free** | ¥0 | ~70% | テストのみ | 開発・テスト |
| **Lightweight** | ~$20 | ~85% | 45-60 | 小規模運用 |
| **Full** | ~$100 | ~95% | 240-320 | 本格運用 |

プランは設定画面で切り替え可能。Retell API Key + Agent ID を設定すると自動的に Lightweight に昇格。

---

## デプロイ方法の比較

| 項目 | run.sh | Docker | AWS EC2 |
|------|--------|--------|---------|
| 費用 | 無料 | 無料 | Free Tier内無料 |
| データ永続 | ✅ | ✅ | ✅ |
| インターネット公開 | 不要 | 不要 | ✅ 固定IP |
| Webhook受信 | ❌ | ❌ | ✅ |
| 前提 | Python | Docker Desktop | AWS CLI |

---

## アーキテクチャ

```
Streamlit (8501) ── UI
    │
FastAPI (8000) ── API + Webhook
    │
VoiceProvider ── 抽象化レイヤー
    ├── MockProvider (Free Tier)
    └── RetellProvider (Lightweight/Full)
            ├── agent_id (GPT-4.1)
            └── agent_id_budget (GPT-4.1-mini)
```

- 割り込み対応：8種類の割り込みタイプを認識・処理
- 会話テンプレート：ブロック単位でカスタマイズ可能
- テストスイート：148テスト / 15シナリオ / 成功率レポート

---

## テスト

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## ドキュメント

- [操作手順書](docs/OPERATION_MANUAL.md) — 各機能の使い方
- [デプロイガイド](docs/DEPLOY.md) — AWS / Docker / ローカル詳細手順
- [電話発信セットアップ](docs/PHONE_SETUP.md) — 電話番号の取得方法
- [交付ガイド](docs/DELIVERY_GUIDE.md) — システム引き渡し手順
- [サンプル](docs/samples/) — メール・通話・CSVの例
- [アーキテクチャ設計](docs/architecture.md) — 技術選定理由
- [3段階ソリューション](docs/design/solution-tiers.md) — 費用・機能比較
- [割り込み対応設計](docs/design/interruption-handling.md) — 技術詳細
- [リスク分析](docs/design/risk-analysis.md) — 残存リスク一覧

---

## 技術スタック

Python 3.9+ / Streamlit / FastAPI / SQLite / OpenAI GPT-4.1 / Retell AI / Gmail SMTP
