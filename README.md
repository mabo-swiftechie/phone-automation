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

### 方法3：AWS EC2（本番運用）

**3.1 IAM ユーザー作成**
```bash
aws iam create-user --user-name boma086-admin
aws iam attach-user-policy --user-name boma086-admin \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name boma086-admin
aws configure --profile boma086  # Access Key を入力, Region: ap-northeast-1
```

**3.2 EC2 インスタンス起動（Tokyo, Free Tier）**
```bash
# SSH キー作成
aws --profile boma086 ec2 create-key-pair --key-name boma086-tokyo \
  --region ap-northeast-1 --query 'KeyMaterial' --output text > boma086-tokyo.pem
chmod 600 boma086-tokyo.pem

# セキュリティグループ作成
SG=$(aws --profile boma086 ec2 create-security-group --group-name phone-automation \
  --description "Phone Automation" --region ap-northeast-1 --query 'GroupId' --output text)
for port in 22 8000 8501; do
  aws --profile boma086 ec2 authorize-security-group-ingress \
    --group-id $SG --protocol tcp --port $port --cidr 0.0.0.0/0 --region ap-northeast-1
done

# インスタンス起動 (t4g.micro = Free Tier)
aws --profile boma086 ec2 run-instances --image-id ami-0a0952180fe7bcab0 \
  --instance-type t4g.micro --key-name boma086-tokyo --security-group-ids $SG \
  --region ap-northeast-1 --block-device-mappings \
  '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=phone-automation}]'
```

**3.3 デプロイ**
```bash
# プロジェクトをパッケージング（venv除外）
tar czf pkg.tar.gz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
  --exclude='.DS_Store' --exclude='._*' -C .. phone_automation/

# アップロード＆インストール
scp -i boma086-tokyo.pem pkg.tar.gz ubuntu@<EC2_IP>:/tmp/
ssh -i boma086-tokyo.pem ubuntu@<EC2_IP>
```

リモートで実行:
```bash
cd ~ && tar xzf /tmp/pkg.tar.gz
python3 -m venv ~/phone_automation/.venv
source ~/phone_automation/.venv/bin/activate
cd ~/phone_automation && pip install .
```

**3.4 systemd サービス設定**

`/etc/systemd/system/phone-api.service`:
```ini
[Unit]
Description=Phone Automation FastAPI
After=network.target
[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/phone_automation
ExecStart=/home/ubuntu/phone_automation/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PHONE_AUTOMATION_DATA=/home/ubuntu/.phone_automation
[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/phone-ui.service`:
```ini
[Unit]
Description=Phone Automation Streamlit UI
After=network.target phone-api.service
[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/phone_automation
ExecStart=/home/ubuntu/phone_automation/.venv/bin/streamlit run app/ui.py \
  --server.headless true --server.port 8501 --server.address 0.0.0.0 \
  --browser.gatherUsageStats false
Restart=always
RestartSec=5
Environment=PHONE_AUTOMATION_DATA=/home/ubuntu/.phone_automation
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable phone-api phone-ui
sudo systemctl start phone-api phone-ui
```

**3.5 確認**
```bash
# サービス状態
sudo systemctl status phone-api phone-ui

# アクセス確認
curl http://<EC2_IP>:8000/          # {"status":"running"}
curl http://<EC2_IP>:8501           # Streamlit UI (HTTP 200)
```

**管理コマンド**
```bash
sudo journalctl -u phone-api -f     # ログ確認
sudo systemctl restart phone-api    # 再起動
```

> 詳細な手順は [デプロイガイド](docs/DEPLOY.md) を参照。

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
phone_automation/
├── app/
│   ├── main.py              # FastAPI アプリ
│   ├── ui.py                # Streamlit UI
│   ├── api/                 # API ルーター
│   │   ├── calls.py         # 電話発信・Webhook
│   │   ├── properties.py    # 物件CRUD
│   │   └── export.py        # CSVエクスポート
│   ├── services/
│   │   ├── voice_provider.py  # VoiceProvider抽象化 + Retell/Mock実装
│   │   └── template_manager.py # 会話テンプレート + 割り込みルール
│   ├── config_manager.py    # 設定管理（YAML + ENV）
│   └── database.py          # SQLite CRUD
├── tests/                   # 148テスト / 15シナリオ
├── run.sh                   # ローカル起動スクリプト
├── Dockerfile               # Docker設定
├── docker-compose.yml       # Docker Compose
└── pyproject.toml           # パッケージ設定
```

### サービス構成

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

## Retell AI エージェント設定

| エージェント | ID | LLM | コスト/min | 用途 |
|-------------|-----|-----|-----------|------|
| 主エージェント | `agent_4667d48d...` | GPT-4.1 | $0.130 | 高品質通話 |
| Budget Agent | `agent_a9e3df5b...` | GPT-4.1-mini | $0.101 | 低コスト通話 |

### 最適化パラメータ

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| interruption_sensitivity | 0.8 | 割り込み検出感度 |
| responsiveness | 0.9 | 応答速度 |
| enable_backchannel | true | 相槌（はい/承知いたしました/そうですか） |
| denoising_mode | noise-cancellation | ノイズ除去 |
| stt_mode | accurate | 高精度音声認識 |
| language | ja-JP | 日本語 |

> 詳細: [電話発信セットアップ](docs/PHONE_SETUP.md)

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
