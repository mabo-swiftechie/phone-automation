# デプロイガイド

## 目次

1. [run.sh（ローカル・推奨）](#1-runshローカル推奨)
2. [Docker（ローカル・データ永続）](#2-dockerローカルデータ永続)
3. [AWS EC2（本番運用）](#3-aws-ec2本番運用)

---

## 1. run.sh（ローカル・推奨）

### 前提

- Python 3.9+ と pip がインストール済み
- macOS / Linux

### 手順

```bash
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
bash run.sh
```

ブラウザで http://localhost:8501 を開く。

### run.sh の動作

1. ポート 8501 の既存プロセスをクリーンアップ
2. ポート 8000 の uvicorn プロセスをクリーンアップ（安全確認付き）
3. pip3 / pip / python3 -m pip を自動検出して依存関係をインストール
4. streamlit コマンドを自動検出して起動

### データについて

- 設定: `~/.phone_automation/config.yaml`
- データベース: `~/.phone_automation/data.db`

---

## 2. Docker（ローカル・データ永続）

### 前提

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) がインストール済み

### 手順

```bash
git clone https://github.com/mabo-swiftechie/phone-automation.git
cd phone-automation
cp .env.example .env
# .env を編集して API Key を入力
docker compose up -d
```

### 操作コマンド

```bash
docker compose up -d       # 起動
docker compose logs -f      # ログ確認
docker compose down         # 停止
docker compose down -v      # 停止＋データ削除
```

---

## 3. AWS EC2（本番運用）

### 前提

- AWS アカウント（Free Tier利用可能）
- AWS CLI v2 がインストール済み
- IAM ユーザー（AdministratorAccess）

### 3.1 IAM ユーザー作成

```bash
aws iam create-user --user-name boma086-admin
aws iam attach-user-policy --user-name boma086-admin \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name boma086-admin
```

### 3.2 AWS CLI 設定

```bash
aws configure --profile boma086
# Access Key ID: AKIA...
# Secret Access Key: ...
# Region: ap-northeast-1
# Output: json
```

### 3.3 SSH キー作成

```bash
aws --profile boma086 ec2 create-key-pair \
  --key-name boma086-tokyo \
  --region ap-northeast-1 \
  --query 'KeyMaterial' --output text > boma086-tokyo.pem
chmod 600 boma086-tokyo.pem
```

### 3.4 セキュリティグループ作成

```bash
SG_ID=$(aws --profile boma086 ec2 create-security-group \
  --group-name phone-automation \
  --description "Phone Automation" \
  --region ap-northeast-1 --query 'GroupId' --output text)

# SSH
aws --profile boma086 ec2 authorize-security-group-ingress \
  --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region ap-northeast-1
# Streamlit
aws --profile boma086 ec2 authorize-security-group-ingress \
  --group-id $SG_ID --protocol tcp --port 8501 --cidr 0.0.0.0/0 --region ap-northeast-1
# FastAPI Webhook
aws --profile boma086 ec2 authorize-security-group-ingress \
  --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region ap-northeast-1
```

### 3.5 EC2 インスタンス起動

```bash
# Ubuntu 22.04 ARM64 AMI を取得
AMI=$(aws --profile boma086 ec2 describe-images \
  --region ap-northeast-1 --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-*" \
            "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text)

aws --profile boma086 ec2 run-instances \
  --image-id $AMI \
  --instance-type t4g.micro \
  --key-name boma086-tokyo \
  --security-group-ids $SG_ID \
  --region ap-northeast-1 \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=phone-automation}]'
```

### 3.6 デプロイ

```bash
# プロジェクトをパッケージング
tar czf phone_automation.tar.gz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
  --exclude='.DS_Store' --exclude='._*' -C .. phone_automation/

# アップロード
scp -i boma086-tokyo.pem phone_automation.tar.gz ubuntu@<EC2_IP>:/tmp/

# リモートインストール
ssh -i boma086-tokyo.pem ubuntu@<EC2_IP> bash -s << 'REMOTE'
cd ~
tar xzf /tmp/phone_automation.tar.gz
python3 -m venv ~/phone_automation/.venv
source ~/phone_automation/.venv/bin/activate
cd ~/phone_automation
pip install .
REMOTE
```

### 3.7 systemd サービス設定

FastAPI サービス (`/etc/systemd/system/phone-api.service`):

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

Streamlit サービス (`/etc/systemd/system/phone-ui.service`):

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

起動:

```bash
sudo systemctl daemon-reload
sudo systemctl enable phone-api phone-ui
sudo systemctl start phone-api phone-ui
```

### 3.8 管理コマンド

```bash
# ステータス確認
sudo systemctl status phone-api phone-ui

# ログ確認
sudo journalctl -u phone-api -f
sudo journalctl -u phone-ui -f

# 再起動
sudo systemctl restart phone-api phone-ui
```

### 3.9 費用（Free Tier）

| リソース | 月額 |
|----------|------|
| EC2 t4g.micro | $0 (12ヶ月無料) |
| EBS 20GB gp3 | ~$1.60 |
| データ転送 | ~$0.01-0.10 |
| **合計** | **~$1.60/月** |

---

## 4. Cloudflare Tunnel（HTTPS公開）

Web Call（ブラウザ通話）はマイクアクセスに **HTTPS が必要**。Cloudflare Tunnel で無料の HTTPS URL を取得。

### 4.1 前提

- cloudflared がインストール済み
- EC2 インスタンスが起動している

```bash
# macOS
brew install cloudflared

# Linux
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

### 4.2 クイックトンネル（一時的・無料）

```bash
cloudflared tunnel --url http://18.179.40.162:8501
```

起動後、以下のような URL が表示される：

```
https://xxxx-xxxx-xxxx.trycloudflare.com
```

この URL で：
- ✅ HTTPS（ブラウザがマイクを許可）
- ✅ Streamlit UI にアクセス可能
- ✅ Web Call が使用可能

### 4.3 名前付きトンネル（本番用・固定URL）

```bash
# ログイン
cloudflared tunnel login

# トンネル作成
cloudflared tunnel create phone-automation

# DNS レコード設定（例: phone.yourdomain.com）
cloudflared tunnel route dns phone-automation phone.yourdomain.com

# 設定ファイル ~/.cloudflared/config.yml
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: phone-automation
credentials-file: ~/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: phone.yourdomain.com
    service: http://18.179.40.162:8501
  - hostname: api.phone.yourdomain.com
    service: http://18.179.40.162:8000
  - service: http_status:404
EOF

# 起動
cloudflared tunnel run phone-automation
```

### 4.4 systemd で自動起動（EC2上）

```bash
# EC2 上に cloudflared をインストール
ssh -i key.pem ubuntu@<EC2_IP> 'sudo curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /usr/local/bin/cloudflared && sudo chmod +x /usr/local/bin/cloudflared'
```

`/etc/systemd/system/cloudflared.service`:

```ini
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:8501
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### 4.5 HTTPS の必要性について

| アクセス方法 | HTTP | HTTPS |
|-------------|------|-------|
| ローカル (localhost) | ✅ マイク許可 | ✅ マイク許可 |
| EC2 パブリック IP | ❌ マイク拒否 | ✅ マイク許可 |
| Cloudflare Tunnel | — | ✅ マイク許可 |

> 実際の電話発信（Retell AI → 管理会社）には HTTPS は不要。Web Call テストのみ必要。

---

## 5. コード更新の同期

EC2 のコードを最新化する手順：

```bash
# ローカルでパッケージング
COPYFILE_DISABLE=1 tar czf /tmp/sync.tar.gz \
  --exclude='.git' --exclude='__pycache__' --exclude='venv' --exclude='.venv' \
  --exclude='.DS_Store' --exclude='._*' --exclude='*.egg-info' \
  -C /Users/jpjys/developer/swiftechie phone_automation/

# アップロード＆展開
scp -i key.pem /tmp/sync.tar.gz ubuntu@<EC2_IP>:/tmp/
ssh -i key.pem ubuntu@<EC2_IP>

# リモートで実行
cd ~/phone_automation
tar xzf /tmp/sync.tar.gz
source .venv/bin/activate
pip install --force-reinstall --no-deps .   # パッケージ再インストール
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null  # キャッシュクリア
sudo systemctl restart phone-api phone-ui
```

> **注意**: `__pycache__` のキャッシュが原因でコード変更が反映されない場合がある。更新後は必ず `pip install --force-reinstall --no-deps .` とキャッシュクリアを実行。

---

## 比較

| 項目 | run.sh | Docker | AWS EC2 | AWS + CF Tunnel |
|------|--------|--------|---------|-----------------|
| 費用 | 無料 | 無料 | ~$1.60/月 | ~$1.60/月 |
| データ永続 | ✅ | ✅ | ✅ | ✅ |
| 固定URL | ローカル | ローカル | IP のみ | ✅ HTTPS ドメイン |
| Webhook受信 | ❌ | ❌ | ✅ | ✅ |
| Web Call（マイク） | ✅ | ❌ | ❌ | ✅ |
| 技術知識 | 不要 | Docker要 | AWS CLI要 | AWS + CF要 |
| 本番運用 | ❌ | ❌ | ✅ | ✅ |
