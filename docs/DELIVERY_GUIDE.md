# 交付チェックリスト

> システムを引き渡す際の準備・確認事項
> 最終更新：2026-05-08

---

## 1. デプロイ方法の選択

| 方法 | 費用 | 固定URL | 推奨用途 |
|------|------|---------|---------|
| AWS EC2 | ~$1.60/月 | ✅ | 本番運用 |
| Docker | 無料 | ❌ | ローカル開発 |
| run.sh | 無料 | ❌ | 個人テスト |

---

## 2. AWS にデプロイ（推奨）

### 2-1. IAM ユーザー作成

```bash
aws iam create-user --user-name boma086-admin
aws iam attach-user-policy --user-name boma086-admin \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name boma086-admin
```

### 2-2. EC2 インスタンス起動

```bash
aws --profile boma086 ec2 run-instances \
  --image-id <Ubuntu-22.04-ARM64-AMI> \
  --instance-type t4g.micro \
  --key-name boma086-tokyo \
  --region ap-northeast-1
```

### 2-3. デプロイとサービス起動

```bash
# 詳細は docs/DEPLOY.md を参照
scp -i key.pem phone_automation.tar.gz ubuntu@<IP>:/tmp/
ssh -i key.pem ubuntu@<IP>  # リモートでインストール
sudo systemctl start phone-api phone-ui
```

### 2-4. 確認

- UI: http://\<EC2_IP\>:8501
- API: http://\<EC2_IP\>:8000/docs
- ヘルス: http://\<EC2_IP\>:8000/

---

## 3. API Key の準備

### 方法A：既存アカウントを共有

| サービス | 月額費用 |
|----------|---------|
| OpenAI | ~$5-20/月（使用量による） |
| Retell AI | 従量 ~$0.10/分 |
| Gmail | 無料 |

### 方法B：各自取得（推奨）

| サービス | 登録URL | 取得手順 |
|----------|---------|---------|
| **OpenAI** | https://platform.openai.com/signup | 登録 → API Keys → Create new key |
| **Retell AI** | https://retellai.com | 登録 → Dashboard → API Keys |
| **Gmail** | https://myaccount.google.com | セキュリティ → 2段階認証 → アプリパスワード |

---

## 4. 初期設定チェックリスト

### 必須

- [ ] OpenAI API Key を設定画面で入力
- [ ] テストデータで Demo Mode を実行
- [ ] 物件を 1件以上登録

### 電話確認を使う場合

- [ ] Retell API Key を入力
- [ ] Retell Agent ID を入力
- [ ] Web Call でテスト通話
- [ ] （本番）Retell 電話番号を購入
- [ ] （本番）Webhook URL を Retell Dashboard に設定

### メール確認を使う場合

- [ ] Gmail アドレスを入力
- [ ] Gmail アプリパスワードを入力
- [ ] テストメール送信を確認

---

## 5. 引き渡すもの

### 必須

- [ ] アクセス URL（AWS の場合は EC2 パブリック IP）
- [ ] API Key（または取得手順）
- [ ] SSH キー（AWS の場合のみ）

### あるとよい

- [ ] [操作手順書](docs/OPERATION_MANUAL.md) のリンク
- [ ] [デプロイガイド](docs/DEPLOY.md) のリンク
- [ ] [サンプル](docs/samples/) のリンク

### 利用者の最初の操作

1. URL にアクセス
2. 🧪「Demo Mode」→「テストデータ生成」で体験
3. 🏠「物件管理」で実際の物件を登録
4. ⚙️「設定」で API Key を入力
5. 📧「メール確認」または 📞「電話確認」を開始

---

## 6. 注意事項

- OpenAI API Key は**絶対に公開リポジトリやチャットに貼らない**
- Gmail アプリパスワードも同様に取り扱い注意
- AWS の Security Group で SSH ポートは必要に応じて IP 制限を推奨
- Retell AI の無料枠を超えると課金されるので使用量に注意
- データベースのバックアップは `~/.phone_automation/data.db` を定期コピー
