# AI電話自動化 — 電話発信セットアップガイド

> 電話確認機能には発信元電話番号が必要です。
> Web Call（ブラウザ通話）は電話番号なしで無料テスト可能です。

---

## 比較：3つの発信方法

| 項目 | Web Call（ブラウザ） | Retell 電話番号 | Twilio +81番号 |
|------|---------------------|----------------|---------------|
| **費用** | 無料 | ~$1-5/月 + 通話料 | $4.75/月 + 通話料 |
| **電話番号** | 不要 | Retell内で購入 | Twilioで購入 |
| **相手の電話が鳴る** | ❌ ブラウザ内のみ | ✅ 実際に発信 | ✅ 実際に発信 |
| **日本語対応** | ✅ | ✅ | ✅ |
| **セットアップ** | なし | 簡単（Dashboard） | 中程度（Twilio設定） |
| **用途** | テスト・品質確認 | 本番運用 | 大規模本番運用 |
| **推奨** | テスト段階 | 小〜中規模 | 大規模 |

---

## 方案A：Web Call（ブラウザ通話）— 無料テスト

### 手順

1. ブラウザで http://localhost:8501 を開く
2. 左サイドバー「📞 電話確認」をクリック
3. 物件を選択
4. 「🌐 Web Call 開始」ボタンをクリック
5. ブラウザのマイク許可 → 「許可」
6. 「Start 通話」→ AIと会話 → 「Stop 通話」
7. 「結果を取得」ボタンで通話結果を確認

### テストのポイント

- AIの日本語敬語が自然か
- 空室確認の質問が適切か
- 外国人・中国人入居可否の確認ができているか
- 相手の回答に対する追質問が自然か

---

## 方案B：Retell AI 電話番号 — 実際の電話発信

### 手順

1. https://www.retellai.com/dashboard/phone-numbers を開く
2. 「Create Phone Number」をクリック
3. 番号の種類を選択：

| 種類 | 料金 | 特徴 |
|------|------|------|
| +1（米国番号） | ~$1-2/月 | 安価、日本への発信可能 |
| +81（日本番号） | ~$5/月 | 日本の局番表示、応答率が高い |

4. 購入完了後、番号をコピー
5. config.yaml に追加：

```yaml
retell_from_number: "+1xxxxxxxxxx"  # 購入した番号
```

6. システムを再起動

### 発信テスト

```bash
curl -X POST http://localhost:8000/calls/trigger \
  -H "Content-Type: application/json" \
  -d '{"property_id": "物件ID"}'
```

---

## 方案C：Twilio +81番号 — 大規模本番

### 前提条件

- Twilioアカウント（https://www.twilio.com）
- 日本の住所証明書類（本人確認/KYC）
- SIPドメイン設定

### 手順

1. Twilio Console → Phone Numbers → Buy a Number
2. +81 03等の固定番号を購入（$4.75/月）
3. 規制要件（Regulatory Compliance）の書類提出
4. SIPドメインを作成し、Retell AIと連携
5. Retell Dashboard → Custom Telephony → Import Phone Number

### 月額コスト概算（100件/月）

| 項目 | 費用 |
|------|------|
| Twilio電話番号 | $4.75/月 |
| 発信通話料 | ~$0.015/分 × 3分 × 100件 = ~$4.50 |
| Retell Platform | ~$0.055/分 × 3分 × 100件 = ~$16.50 |
| **合計** | **~$26/月（約¥3,900）** |

---

## 推奨移行パス

```
現在 → Web Call でテスト（無料）
    ↓ AI会話品質を確認
    ↓
Phase 2 → Retell電話番号を購入（$1-5/月）
    ↓ 実際の管理会社にテスト発信
    ↓
Phase 3 → Twilio +81番号（本番運用）
    ↓ 接通率向上・バッチ発信・スケール
```

---

## 参考リンク

| リソース | URL |
|---------|-----|
| Retell Dashboard | https://www.retellai.com/dashboard |
| Retell 電話番号管理 | https://www.retellai.com/dashboard/phone-numbers |
| Retell 料金 | https://docs.retellai.com/pricing |
| Twilio 日本番号 | https://www.twilio.com/ja/phone-numbers |
| Retell API Docs | https://docs.retellai.com/api-references/create-phone-call |
