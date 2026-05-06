# 3段階ソリューション設計 — 無料 / 軽量($20) / 本格($100)

> ステータス: 設計完了
> 最終更新: 2026-05-04
> 関連: [割り込み対応設計ドキュメント](interruption-handling.md) | [要件仕様書](../REQUIREMENTS_SPEC.md) | [アーキテクチャ](../architecture.md)

---

## 概要

本ドキュメントはAI電話自動化システムの3段階ソリューションを定義する。各段階は**月額コスト**と**割り込み対応効果**のバランスで設計されている。

| | 無料 | 軽量 | 本格 |
|---|---|---|---|
| **月額** | ¥0 | 〜$20 (¥3,000) | 〜$100 (¥15,000) |
| **割り込み効果** | ~70% | ~85% | ~95% |
| **対象** | 開発・テスト | 小規模運用 (50件/月) | 本格運用 (250件/月) |

---

## Tier 1: 無料方案（¥0/月）

### 概要

既存のコード変更（プロンプト改善）と Retell Web Call の無料テストのみで運用。コード変更・外部サービス契約なし。

### 構成

| コンポーネント | サービス | コスト |
|--------------|---------|--------|
| 音声基盤 | Retell Web Call（ブラウザマイク） | $0 |
| LLM | Retell無料枠（Web Call内包） | $0 |
| TTS | Retell無料枠（Web Call内包） | $0 |
| データ保存 | SQLite（ローカル） | $0 |
| UI | Streamlit（ローカル） | $0 |
| メール | Gmail SMTP + GPT-4o-mini | ~$0.01/通（ negligible） |

### 割り込み対策

| 手法 | 効果 | ステータス |
|------|------|-----------|
| プロンプト改善（対話ルール + 終了ルール） | ~70% | ✅ 実装済み |
| Retell Dashboard パラメータ手動設定 | +10% | Dashboard設定のみ |
| Web Call でのテスト検証 | 確認用 | 即時可能 |

### Dashboard設定手順

1. https://www.retellai.com/dashboard → Agents → 対象Agent
2. 以下を設定:
   - `interruption_sensitivity`: **0.8**
   - `responsiveness`: **0.9**
   - `denoising_mode`: **`noise-cancellation`**
   - `enable_dynamic_responsiveness`: **true**
   - `enable_backchannel`: **true**
   - `backchannel_frequency`: **0.3**
   - `backchannel_words`: **["はい", "承知いたしました", "そうですか"]**
   - `stt_mode`: **`accurate`**

### 制限事項

- 実際の電話ができない（ブラウザマイクのみ）
- バッチ処理なし
- ノイズ環境での検証不可
- 通話相手は自分自身（テスト用途）

### テスト手順

```
1. python -m streamlit run app/ui.py
2. "電話確認" タブ → 物件選択 → "Web Call 開始"
3. AIが質問に回答後、「はいはい」と割り込み
4. AIが同じ内容を繰り返さないことを確認
5. AIが長いまとめなしで簡潔に終了することを確認
```

---

## Tier 2: 軽量方案（〜$20/月）

### 概要

Retell AI で実際の電話をかけ、Dashboard設定を最適化。GPT-4.1-mini でコストを抑えつつ実運用可能な品質を確保。

### 構成

| コンポーネント | サービス | コスト/min |
|--------------|---------|-----------|
| Voice Infra | Retell AI Platform | $0.055 |
| LLM | GPT-4.1-mini | $0.016 |
| TTS | Retell Platform Voices | $0.015 |
| 電話 | 日本向けテレフォニー | $0.015 |
| **合計** | | **$0.101/min** |

### 月額計算

| LLM選択 | /min | 3分通話 | 45通話/月 | 60通話/月 | 電話番号 | **合計** |
|---------|------|---------|----------|----------|---------|---------|
| GPT-4.1-mini | $0.101 | $0.303 | $13.64 | $18.18 | +$2 | **$15-20** |
| GPT-4.1 | $0.130 | $0.390 | $17.55 | $23.40 | +$2 | **$20-25** |

**推奨**: GPT-4.1-mini構成で60通話/月 → **$20.18/月**

### 割り込み対策

| 手法 | 効果 | ステータス |
|------|------|-----------|
| プロンプト改善 | ~70% | ✅ 実装済み |
| Dashboard最適化（上記Tier 1設定を実電話で検証） | +10% | Dashboard設定 |
| 実電話トランスクリプト分析による反復改善 | +5% | 運用プロセス |

### 必要な準備

1. **Retell電話番号取得** ($2/月)
   - Dashboard → Phone Numbers → Purchase
   - 日本の固定局番（03等）推奨 ($4.75/月) or Retell番号 ($2/月)

2. **Agent設定**
   - 新規Agent作成: LLM = GPT-4.1-mini, TTS = Retell Platform Voices
   - Tier 1 の Dashboard設定を適用

3. **設定ファイル更新**（コード変更あり）
   - `app/config_manager.py`: コスト最適化agent_id設定キー追加
   - `app/ui.py`: 通話品質/コスト選択トグル追加
   - `app/services/retell.py`: agent選択ロジック追加

### コード変更内容

#### `app/config_manager.py`

```python
# 追加: コスト最適化Agent ID
CONFIG_KEYS = {
    ...
    "retell_agent_id": "RETELL_AGENT_ID",           # 高品質（既存）
    "retell_agent_id_budget": "RETELL_AGENT_ID_BUDGET",  # コスト最適化（新規）
}
```

#### `app/services/retell.py`

```python
def create_phone_call(phone_number, property_name, property_id, budget_mode=False):
    cfg = load_config()
    agent_id = cfg.get("retell_agent_id_budget") if budget_mode else cfg["retell_agent_id"]
    if not agent_id:
        agent_id = cfg["retell_agent_id"]  # フォールバック
    ...
    payload = {"agent_id": agent_id, ...}
```

#### `app/ui.py`

```python
# 電話確認セクションにトグル追加
budget_mode = st.checkbox("コスト最適化モード（GPT-4.1-mini）", value=True)
```

### 運用フロー

```
1. Streamlit UI で物件一覧を確認
2. 電話確認タブで物件を選択
3. 「発信」ボタンで Retell AI が実際の電話を発信
4. 通話完了後、Webhook で結果を自動記録
5. LINE通知で結果を受信
6. トランスクリプトを確認・分析
```

### 段階的改善サイクル

```
実電話テスト → トランスクリプト分析 → プロンプト微調整 → 再テスト
```

- `interruption_sensitivity` を 0.6〜1.0 でA/Bテスト
- 偽停止率が高ければ感度を下げる
- リピートがあればプロンプトを強化

---

## Tier 3: 本格方案（〜$100/月）

### 選択肢A: Retell AI Conversation Flow（推奨）

#### 概要

Retell AI の Conversation Flow Agent を活用し、ノードごとに割り込み制御を設定。構造的に重複を防止する最強のソリューション。

#### 構成

| コンポーネント | サービス | コスト/min |
|--------------|---------|-----------|
| Voice Infra | Retell AI Platform | $0.055 |
| LLM | GPT-4.1-mini（質問ノードはGPT-4.1） | $0.016-0.045 |
| TTS | Retell Platform Voices | $0.015 |
| 電話 | 日本向けテレフォニー | $0.015 |
| 高度ノイズ除去 | noise-and-background-speech-cancellation | +$0.005 |
| **合計** | | **$0.106-0.135/min** |

#### 月額計算

| LLM構成 | /min | 240通話/月 | 320通話/月 | 電話番号 | **合計** |
|---------|------|-----------|-----------|---------|---------|
| 全GPT-4.1-mini | $0.106 | $76.32 | $101.76 | +$2 | **$78-104** |
| 質問のみGPT-4.1 | ~$0.12 | $86.40 | ~$115 | +$2 | **$88-117** |
| 全GPT-4.1 | $0.135 | $97.20 | $129.60 | +$2 | **$99-132** |

**推奨**: 全GPT-4.1-mini構成 → 300通話/月 → **$95.4 + $2 = $97.4/月**

#### Conversation Flow ノード設計

既存の7ブロックテンプレートを Conversation Flow ノードにマッピング:

| # | ブロック名 | Flow ノード | ノードタイプ | Block Interruptions | LLM |
|---|-----------|------------|-------------|---------------------|-----|
| 1 | 敬語ルール | Global Settings | （グローバル設定） | — | — |
| 2 | 空室確認 | Vacancy Check | Conversation | **OFF** | GPT-4.1 |
| 3 | 外国人確認 | Foreigner Check | Conversation | **OFF** | GPT-4.1 |
| 4 | 中国人確認 | Chinese Check | Conversation | **OFF** | GPT-4.1 |
| 5 | 入居条件確認 | Conditions Check | Conversation | **OFF** | GPT-4.1 |
| 6 | 対話ルール | Global Settings | （グローバル設定） | — | — |
| 7 | 終了ルール | Closing | End | **OFF** | GPT-4.1-mini |
| — | 留守電 | Voicemail | Conversation | **ON** | GPT-4.1-mini |
| — | 挨拶 | Greeting | Conversation | **ON** | GPT-4.1 |

**設計意図**:
- 挨拶・留守電は Block Interruptions = ON（メッセージを最後まで話す）
- 質問ノードは OFF（ユーザーの割り込み・訂正を許可）
- ルーティングノードは GPT-4.1-mini でコスト最適化
- 質問ノードは GPT-4.1 で自然度最大化

#### 割り込み対策

| 手法 | 効果 | レイヤー |
|------|------|---------|
| プロンプト改善 | ~70% | LLM |
| Dashboard最適化 | +10% | プラットフォーム |
| ノード別 Block Interruptions | +10% | 構造的（最強） |
| 高度ノイズ除去 | +5% | オーディオ |
| **合計** | **~95%** | |

#### Dashboard追加設定

Tier 2 の設定に加えて:

- `denoising_mode`: **`noise-and-background-speech-cancellation`**（+$0.005/min）
- 各ノードの Block Interruptions 設定
- Function Node では "Speak During Execution" を **OFF**（コミュニティ報告の断片化問題対策）

#### 必要なコード変更

**`app/services/retell.py`**:
```python
# Conversation Flow Agent ID 対応
def create_phone_call(phone_number, property_name, property_id, agent_type="flow"):
    cfg = load_config()
    agent_id = cfg.get(f"retell_agent_id_{agent_type}", cfg["retell_agent_id"])
    ...
```

**`app/services/template_manager.py`**:
```python
# テンプレート → Flow ノード マッピング関数
def get_flow_node_mapping(template_id: str) -> list[dict]:
    blocks = get_template_blocks(template_id)
    mapping = []
    for b in blocks:
        if b["type"] == "greeting":
            mapping.append({"node": "Greeting", "block_interruptions": True, ...})
        elif b["type"] == "question":
            mapping.append({"node": b["name"], "block_interruptions": False, ...})
        ...
    return mapping
```

**`app/api/calls.py`**:
```python
# バッチ通話エンドポイント追加
@router.post("/batch-trigger")
async def trigger_batch_calls(body: BatchCallRequest):
    results = []
    for prop_id in body.property_ids:
        result = await trigger_call(CallRequest(property_id=prop_id))
        results.append(result)
        await asyncio.sleep(2)  # レート制限
    return {"results": results}
```

**`app/ui.py`**:
```python
# バッチ通話UI追加
# 通話キューのステータス表示
```

### 選択肢B: Bland AI移行（大量通話向け）

#### 概要

Retell AI から Bland AI に移行し、より安価な通話単価で大量処理。

#### 構成

| コンポーネント | サービス | コスト/min |
|--------------|---------|-----------|
| 全込み | Bland AI Start Plan | $0.14/min |

#### 月額計算

| 通話数/月 | 3分通話単価 | 月額 |
|----------|-----------|------|
| 230 | $0.42 | **$96.60** |
| 238 | $0.42 | **$99.96** |

#### Retell vs Bland 比較

| 項目 | Retell Conversation Flow | Bland AI Start |
|------|-------------------------|----------------|
| **通話単価** | $0.303-$0.405 | $0.42 |
| **$100内の通話数** | 240-320 | ~230 |
| **割り込み制御** | ノード別 Block Interruptions（最強） | プロンプトベース状態追跡 |
| **移行コスト** | なし（既存コードベース） | 新規統合（~1週間） |
| **日本語品質** | 実証済み | 未検証（要テスト） |
| **Dashboard** | フル分析 | Norm Builder + 分析 |
| **バッチ通話** | API対応（+$0.005/dial） | API対応 |
| **リスク** | 低（実績あり） | 中（新規統合） |

#### 必要なコード変更（Bland移行）

**新規ファイル**: `app/services/bland.py`
- Bland AI API クライアント
- 通話作成・状態取得

**`app/config_manager.py`**:
- `voice_provider` キー追加（"retell" or "bland"）
- `bland_api_key`, `bland_agent_id` 追加

**`app/ui.py`**:
- 音声プロバイダー選択UI追加

#### Bland移行の判断基準

- 月300件超える場合、Bland Build Plan ($299 + $0.12/min) が逆に安くなる
- それ未満なら Retell の方が割り込み制御で優位
- **推奨**: まず Retell Conversation Flow で運用し、300件/月を超えた段階で Bland 移行を検討

---

## 段階別比較マトリクス

| 機能 | Tier 1 無料 | Tier 2 軽量($20) | Tier 3 本格($100) |
|------|-----------|-----------------|-------------------|
| **実際の電話** | ❌ ブラウザのみ | ✅ | ✅ |
| **通話数/月** | テストのみ | 45-60 | 240-320 |
| **割り込み効果** | ~70% | ~85% | ~95% |
| **ノード別制御** | ❌ | ❌ | ✅ (Retell Flow) |
| **バッチ通話** | ❌ | ❌ | ✅ |
| **高度ノイズ除去** | ❌ | ❌ | ✅ (+$0.005/min) |
| **LINE通知** | 手動 | Webhook自動 | Webhook+ダッシュボード |
| **LLM選択** | 固定 | 2択（GPT-4.1/4.1-mini） | ノード別最適化 |
| **通話録音保存** | Dashboardのみ | Dashboard | Dashboard+ローカル |
| **KPI追跡** | ❌ | 基本（トランスクリプト） | 高度（偽停止率・リピート率） |
| **バックチャンネル** | Dashboard設定 | Dashboard設定 | カスタムチューニング |
| **月額コスト** | $0 | $15-20 | $78-100 |

---

## 推奨ロードマップ

```
今週 ────────────────────────────────────────────────
  Tier 1 検証
  ├── Web Call でプロンプト変更をテスト
  ├── 割り込み時の重複がないか確認
  └── Dashboard設定を適用

今週〜来週 ──────────────────────────────────────────
  Tier 2 移行
  ├── Retell電話番号取得 ($2/月)
  ├── GPT-4.1-mini Agent作成
  ├── 5-10件のテスト通話（既知の物件管理会社）
  └── トランスクリプト分析 → パラメータ調整

2週間後 ─────────────────────────────────────────────
  Tier 2 最適化
  ├── interruption_sensitivity A/Bテスト (0.6〜1.0)
  ├── プロンプト微調整（実データに基づく）
  └── 50件の実績データ蓄積

50件の実績後 ────────────────────────────────────────
  Tier 3 評価
  ├── 残り15%の問題を分析
  ├── Conversation Flow 投資の判断
  │   ├── 重複が0%に近い → Tier 2 で十分
  │   └── まだ課題あり → Conversation Flow 実装
  └── Bland移行の必要性評価（通話数に基づく）
```

---

## 費用計算の前提

出典: [Retell AI Pricing](https://www.retellai.com/pricing), [Bland AI Pricing](https://www.bland.ai/pricing), [要件仕様書](../REQUIREMENTS_SPEC.md)

| パラメータ | 値 |
|-----------|-----|
| 平均通話時間 | 3分 |
| Retell Voice Infra | $0.055/min |
| GPT-4.1 | $0.045/min |
| GPT-4.1-mini | $0.016/min |
| GPT-4.1-nano | $0.004/min |
| Retell Platform TTS | $0.015/min |
| OpenAI TTS | $0.015/min |
| 日本テレフォニー | $0.015/min |
| 高度ノイズ除去 | +$0.005/min |
| 電話番号（Retell） | $2/月 |
| 電話番号（固定局番03） | $4.75/月 |
| Bland Start Plan | $0.14/min（全込み） |

---

## 関連ドキュメント

- [割り込み対応設計ドキュメント](interruption-handling.md) — 技術詳細
- [要件仕様書](../REQUIREMENTS_SPEC.md) — 費用比較・要件定義
- [アーキテクチャ設計](../architecture.md) — 技術スタック・移行戦略
- [運用マニュアル](../OPERATION_MANUAL.md) — 操作手順
