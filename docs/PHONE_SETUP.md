# AI電話自動化 — 電話発信セットアップガイド

> 最終更新：2026-05-08

---

## 現在の Retell AI 設定

### エージェント一覧

| エージェント | ID | LLM | 用途 |
|-------------|-----|-----|------|
| 主エージェント | `agent_4667d48d2f7807f07d7f031cc2` | GPT-4.1 | 高品質通話 |
| Budget Agent | `agent_a9e3df5b3bc4fa1a4d75d244db` | GPT-4.1-mini | 低コスト通話 |

### Dashboard 最適化パラメータ（両Agent共通）

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| interruption_sensitivity | 0.8 | 割り込み検出感度 |
| responsiveness | 0.9 | 応答速度 |
| enable_backchannel | true | 相槌機能 |
| backchannel_words | ["はい", "承知いたしました", "そうですか"] | 相槌の種類 |
| backchannel_frequency | 0.3 | 相槌の頻度 |
| enable_dynamic_responsiveness | true | 動的応答調整 |
| denoising_mode | noise-cancellation | ノイズ除去 |
| stt_mode | accurate | 高精度音声認識 |
| language | ja-JP | 日本語 |

---

## 発信方法の比較

| 項目 | Web Call（ブラウザ） | Retell 電話番号 | Twilio +81番号 |
|------|---------------------|----------------|---------------|
| **費用** | 無料 | ~$2-5/月 + 通話料 | $4.75/月 + 通話料 |
| **相手の電話が鳴る** | ❌ ブラウザ内のみ | ✅ 実際に発信 | ✅ 実際に発信 |
| **セットアップ** | なし | 簡単（Dashboard） | 中程度 |
| **用途** | テスト | 小〜中規模 | 大規模 |

---

## 方案A：Web Call — 無料テスト

### 手順

1. ブラウザで http://localhost:8501 を開く
2. 「📞 電話確認」→ 物件を選択
3. 「🌐 Web Call 開始」→ マイク許可
4. 「Start 通話」→ AIと会話 → 「Stop 通話」
5. 「結果を取得」で通話結果を確認

### テストのポイント

- 日本語敬語が自然か
- 空室確認の質問が適切か
- 割り込みに対する対応が正しいか
- 長い反復やまとめがないか

---

## 方案B：Retell AI 電話番号 — 実際の電話発信

### 手順

1. https://www.retellai.com/dashboard/phone-numbers を開く
2. 「Create Phone Number」をクリック

| 種類 | 料金 | 特徴 |
|------|------|------|
| +1（米国番号） | ~$2/月 | 安価、日本への発信可能 |
| +81（日本番号） | ~$5/月 | 日本の局番、応答率が高い |

3. 購入後、設定画面で電話番号を入力

### 発信テスト

```bash
curl -X POST http://localhost:8000/calls/trigger \
  -H "Content-Type: application/json" \
  -d '{"property_id": "物件ID"}'
```

### Webhook 設定

Retell Dashboard → Agent → Webhook URL に設定：

```
http://<EC2_PUBLIC_IP>:8000/calls/webhook
```

通話完了後に結果が自動記録される。

---

## 方案C：Twilio +81番号 — 大規模本番

### 前提

- Twilioアカウント（https://www.twilio.com）
- 日本の住所証明書類（KYC）
- SIPドメイン設定

### 月額コスト概算（100件/月）

| 項目 | 費用 |
|------|------|
| Twilio電話番号 | $4.75/月 |
| 発信通話料 | ~$4.50 |
| Retell Platform | ~$16.50 |
| **合計** | **~$26/月** |

---

## 推奨移行パス

```
1. Web Call でテスト（無料）
   ↓ AI会話品質を確認

2. Retell電話番号を購入（$2-5/月）
   ↓ 実際の管理会社にテスト発信
   ↓ トランスクリプト分析

3. Budget Agent でコスト最適化（GPT-4.1-mini）
   ↓ 品質とコストのバランス確認

4. Twilio +81番号 or Conversation Flow（本番運用）
   ↓ バッチ発信・スケール
```

---

## 通話コスト比較

| LLM | /min | 3分通話 | 60通話/月 |
|-----|------|---------|----------|
| GPT-4.1 (主Agent) | $0.130 | $0.390 | $23.40 |
| GPT-4.1-mini (Budget) | $0.101 | $0.303 | $18.18 |

Budget Agent を使うと月額約22%のコスト削減。

---

## 参考リンク

| リソース | URL |
|---------|-----|
| Retell Dashboard | https://www.retellai.com/dashboard |
| Retell 電話番号管理 | https://www.retellai.com/dashboard/phone-numbers |
| Retell 料金 | https://docs.retellai.com/pricing |
| Twilio 日本番号 | https://www.twilio.com/ja/phone-numbers |
