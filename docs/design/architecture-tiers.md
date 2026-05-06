# 三段階統合アーキテクチャ設計

> 関連: [割り込み対応設計](interruption-handling.md) | [段階別ソリューション](solution-tiers.md) | [アーキテクチャ概要](../architecture.md)
> 最終更新: 2026-05-04

---

## 1. 設計目標

単一のコードベースで3段階（無料/$20/$100）を**設定のみで切替可能**にする。Tier間でコードを分岐させず、設定駆動で機能の有無を制御する。

### 設計原則

| 原則 | 説明 |
|------|------|
| **設定駆動Tier切替** | `config.yaml` の `tier` フィールドでTierを切替。コード変更不要 |
| **Provider抽象化** | VoiceProvider ABC により Retell/Bland/将来Providerを差し替え可能 |
| **段階的機能追加** | 上位Tierは機能を追加するだけで、下位Tierを置き換えない |
| **既存コード互換** | DEFAULT_BLOCKS、テンプレートシステム、Webhook処理をそのまま流用 |
| **Graceful Degradation** | 上位Tierの機能が未設定の場合、下位Tierの動作にフォールバック |

---

## 2. アーキテクチャ全体図

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│                                                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐  │
│  │   Streamlit UI       │  │   FastAPI API            │  │
│  │   (ui.py)            │  │   (api/*.py)             │  │
│  │                      │  │                          │  │
│  │  Tab: 物件管理       │  │  POST /calls/trigger     │  │
│  │  Tab: 電話確認       │  │  POST /calls/webhook     │  │
│  │  Tab: テンプレート   │  │  POST /calls/batch ★     │  │
│  │  Tab: 設定 ★         │  │  GET  /calls/{id}        │  │
│  │  Tab: 分析 ★★        │  │  POST /properties        │  │
│  │                      │  │  GET  /export             │  │
│  └──────────┬───────────┘  └────────────┬─────────────┘  │
│             │                           │                │
├─────────────┼───────────────────────────┼────────────────┤
│             │      Service Layer        │                │
│             │                           │                │
│  ┌──────────▼───────────────────────────▼─────────────┐  │
│  │              VoiceProvider (ABC)                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │  │
│  │  │ RetellProvider│  │ BlandProvider│  │MockProvider│  │  │
│  │  │ (Tier 1/2/3) │  │ (Tier 3)    │  │(Tier 1)   │  │  │
│  │  └─────────────┘  └─────────────┘  └───────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Template     │  │ Email        │  │ Notify       │   │
│  │ Manager      │  │ Service      │  │ Service      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ CallAnalytics│  │ BatchCall    │                     │
│  │ (Tier 2+) ★ │  │ (Tier 3) ★★ │                     │
│  └──────────────┘  └──────────────┘                     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│              Configuration Layer                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ConfigManager (Tier-aware)                      │   │
│  │                                                  │   │
│  │  tier: "free" | "lightweight" | "full"           │   │
│  │  voice.provider: "retell" | "bland" | "mock"     │   │
│  │  voice.retell.agent_id: "agent_..."              │   │
│  │  voice.retell.budget_agent_id: "agent_..."  ★    │   │
│  │  voice.retell.flow_agent_id: "agent_..."    ★★   │   │
│  │  voice.retell.settings: {...}                    │   │
│  │  voice.bland.api_key: "..."                ★★    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
├──────────────────────────────────────────────────────────┤
│              Data Layer                                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SQLite (database.py)                            │   │
│  │  properties | inquiries | call_records           │   │
│  │  conversation_blocks | conversation_templates    │   │
│  │  config                                          │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘

凡例: ★ = Tier 2以上で有効, ★★ = Tier 3のみ
```

---

## 3. レイヤー詳細

### 3.1 Voice Provider 抽象化

**ファイル**: `app/services/voice_provider.py`

```
                 VoiceProvider (ABC)
                 ┌──────────────────┐
                 │ + create_call()  │
                 │ + create_web_call│
                 │ + get_call_status│
                 │ + parse_webhook()│
                 └────────┬─────────┘
            ┌─────────────┼─────────────┐
            │             │             │
    ┌───────▼─────┐ ┌────▼──────┐ ┌───▼──────┐
    │RetellProvider│ │BlandProvider│ │MockProv. │
    │             │ │           │ │          │
    │- api_key    │ │- api_key  │ │          │
    │- agent_id   │ │- pathway  │ │          │
    │- budget_id  │ │           │ │          │
    │- flow_id    │ │           │ │          │
    └─────────────┘ └───────────┘ └──────────┘
```

#### VoiceProvider インターフェース

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class CallResult:
    call_id: str
    status: str
    agent_mode: str  # "default" | "budget" | "flow"

@dataclass
class WebCallResult:
    call_id: str
    access_token: str

@dataclass
class CallStatus:
    call_id: str
    status: str
    duration_seconds: Optional[int]
    transcript: Optional[str]
    recording_url: Optional[str]

@dataclass
class WebhookResult:
    call_id: str
    call_status: str
    duration_seconds: Optional[int]
    transcript: Optional[str]
    recording_url: Optional[str]
    vacancy_status: Optional[str]
    foreigner_accepted: Optional[bool]
    chinese_accepted: Optional[bool]
    special_conditions: Optional[str]

class VoiceProvider(ABC):
    """音声通話プロバイダーの抽象インターフェース"""

    @abstractmethod
    def create_call(self, phone_number: str, property_name: str,
                    property_id: str, mode: str = "default") -> CallResult:
        """電話を発信する。mode: "default" | "budget" | "flow" """

    @abstractmethod
    def create_web_call(self, property_name: str,
                        property_id: str) -> WebCallResult:
        """ブラウザ通話を作成する"""

    @abstractmethod
    def get_call_status(self, call_id: str) -> CallStatus:
        """通話状態を取得する"""

    @abstractmethod
    def parse_webhook(self, payload: dict) -> WebhookResult:
        """Webhookペイロードをパースする"""

    @property
    @abstractmethod
    def supports_batch(self) -> bool:
        """バッチ通話をサポートするか"""

    @property
    @abstractmethod
    def supports_phone_call(self) -> bool:
        """実際の電話発信をサポートするか"""
```

#### RetellProvider

```python
class RetellProvider(VoiceProvider):
    """Retell AI プロバイダー（全Tier対応）"""

    def __init__(self, config: dict):
        self.api_key = config["retell_api_key"]
        self.agent_id = config["retell_agent_id"]
        self.budget_agent_id = config.get("retell_agent_id_budget")
        self.flow_agent_id = config.get("retell_agent_id_flow")
        self._base_url = "https://api.retellai.com/v2"

    def _select_agent(self, mode: str) -> str:
        """モードに応じたAgent IDを選択"""
        if mode == "budget" and self.budget_agent_id:
            return self.budget_agent_id
        if mode == "flow" and self.flow_agent_id:
            return self.flow_agent_id
        return self.agent_id  # フォールバック

    def create_call(self, phone_number, property_name, property_id, mode="default"):
        # 既存 retell.py の create_phone_call と同等
        # agent_id = self._select_agent(mode)
        ...

    def create_web_call(self, property_name, property_id):
        # 既存 retell.py の create_web_call と同等
        ...

    def get_call_status(self, call_id):
        # 既存 retell.py の get_call と同等
        ...

    def parse_webhook(self, payload):
        # 既存 calls.py の webhook パースロジック
        ...

    @property
    def supports_batch(self) -> bool:
        return bool(self.flow_agent_id)  # Tier 3 のみ

    @property
    def supports_phone_call(self) -> bool:
        return True
```

#### MockProvider

```python
class MockProvider(VoiceProvider):
    """Tier 1 テスト用モック"""

    def create_call(self, phone_number, property_name, property_id, mode="default"):
        raise NotImplementedError("Tier 1 では実際の電話発信はできません。Web Callを使用してください。")

    def create_web_call(self, property_name, property_id):
        # テスト用のダミーレスポンス
        return WebCallResult(call_id="mock_" + uuid4().hex[:8], access_token="mock_token")

    def get_call_status(self, call_id):
        return CallStatus(call_id=call_id, status="completed", ...)

    def parse_webhook(self, payload):
        return WebhookResult(...)

    @property
    def supports_batch(self) -> bool:
        return False

    @property
    def supports_phone_call(self) -> bool:
        return False
```

#### Provider生成ファクトリ

```python
def get_voice_provider(config: dict) -> VoiceProvider:
    """設定に基づいてVoiceProviderを生成する"""
    provider_name = config.get("voice_provider", "retell")

    # Tier 1 で Retell API key が未設定の場合はモック
    tier = config.get("tier", "free")
    if tier == "free" and not config.get("retell_api_key"):
        return MockProvider(config)

    if provider_name == "retell":
        return RetellProvider(config)
    elif provider_name == "bland":
        return BlandProvider(config)
    else:
        return MockProvider(config)
```

### 3.2 設定管理（Tier-aware ConfigManager）

**ファイル**: `app/config_manager.py`

#### 設定構造

```yaml
# config.yaml — 三段階対応設定

# Tier選択: "free" | "lightweight" | "full"
tier: "free"

# 音声通話設定
voice:
  # プロバイダー: "retell" | "bland" | "mock"
  provider: "retell"

  # Retell AI設定（全Tier共通）
  retell:
    api_key: ""
    agent_id: ""
    # Tier 2+: コスト最適化Agent
    budget_agent_id: ""
    # Tier 3: Conversation Flow Agent
    flow_agent_id: ""
    # プラットフォーム設定
    settings:
      interruption_sensitivity: 0.8
      responsiveness: 0.9
      denoising_mode: "noise-cancellation"
      enable_dynamic_responsiveness: true
      enable_backchannel: true
      backchannel_frequency: 0.3
      backchannel_words: ["はい", "承知いたしました", "そうですか"]
      stt_mode: "accurate"

  # Bland AI設定（Tier 3 Option B）
  bland:
    api_key: ""
    pathway_id: ""

# OpenAI設定
openai_api_key: ""

# Gmail設定
gmail_address: ""
gmail_app_password: ""

# 会社情報
company_name: ""
contact_person: ""

# 通知設定
notifications:
  line_notify_token: ""
```

#### 環境変数マッピング

```python
ENV_MAP = {
    "tier": "TIER",
    "voice_provider": "VOICE_PROVIDER",
    "retell_api_key": "RETELL_API_KEY",
    "retell_agent_id": "RETELL_AGENT_ID",
    "retell_agent_id_budget": "RETELL_AGENT_ID_BUDGET",
    "retell_agent_id_flow": "RETELL_AGENT_ID_FLOW",
    "bland_api_key": "BLAND_API_KEY",
    "bland_pathway_id": "BLAND_PATHWAY_ID",
    "openai_api_key": "OPENAI_API_KEY",
    ...
}
```

#### Tier判定ヘルパー

```python
def get_tier(config: dict) -> str:
    return config.get("tier", "free")

def is_feature_enabled(config: dict, feature: str) -> bool:
    tier = get_tier(config)
    TIER_FEATURES = {
        "free": {"web_call", "template_edit", "email"},
        "lightweight": {"web_call", "phone_call", "template_edit", "email",
                        "budget_mode", "webhook", "line_notify", "analytics_basic"},
        "full": {"web_call", "phone_call", "template_edit", "email",
                 "budget_mode", "flow_mode", "webhook", "line_notify",
                 "analytics_basic", "analytics_advanced", "batch_call", "kpi_dashboard"},
    }
    return feature in TIER_FEATURES.get(tier, set())
```

### 3.3 API層の変更

**ファイル**: `app/api/calls.py`

```python
from app.services.voice_provider import get_voice_provider, VoiceProvider

# Providerの遅延初期化
_provider: VoiceProvider | None = None

def _get_provider() -> VoiceProvider:
    global _provider
    if _provider is None:
        _provider = get_voice_provider(load_config())
    return _provider

@router.post("/trigger")
async def trigger_call(body: CallRequest):
    provider = _get_provider()
    result = await asyncio.to_thread(
        provider.create_call,
        phone_number=prop["phone_number"],
        property_name=prop["name"],
        property_id=str(body.property_id),
        mode=body.mode if hasattr(body, 'mode') else "default",
    )
    ...

@router.post("/batch-trigger")  # Tier 3 のみ
async def trigger_batch_calls(body: BatchCallRequest):
    cfg = load_config()
    if not is_feature_enabled(cfg, "batch_call"):
        raise HTTPException(403, "バッチ通話は Full Tier でのみ利用可能です")
    ...
```

### 3.4 UI層の変更

**ファイル**: `app/ui.py`

```python
# Tier判定に基づくUI制御
cfg = load_config()
tier = cfg.get("tier", "free")

# 電話確認タブ
if tier == "free":
    st.info("📱 無料Tier: Web Callのみ利用可能（ブラウザマイク使用）")
    # Web Call ボタンのみ表示
else:
    # Web Call + 実電話発信ボタン
    mode = st.radio("通話モード", ["高品質 (GPT-4.1)", "コスト最適化 (GPT-4.1-mini)"])

    if tier == "full":
        # バッチ通話UI
        st.checkbox("バッチ通話モード")
```

---

## 4. Tier別コンポーネント構成

### Tier 1: Free (¥0/月)

```
┌─────────────────────────────────┐
│  Streamlit UI                   │
│  ├── Web Call ボタンのみ        │
│  ├── テンプレート編集           │
│  └── 設定（Dashboard案内のみ）  │
├─────────────────────────────────┤
│  FastAPI                        │
│  └── /calls/webhook             │
├─────────────────────────────────┤
│  MockProvider or RetellProvider │
│  (Web Call only)                │
├─────────────────────────────────┤
│  TemplateManager                │
│  EmailService                   │
├─────────────────────────────────┤
│  SQLite                         │
└─────────────────────────────────┘
```

**設定例**:
```yaml
tier: "free"
voice:
  provider: "retell"
  retell:
    api_key: ""   # 未設定 → MockProvider
    agent_id: ""
```

### Tier 2: Lightweight (~$20/月)

```
┌─────────────────────────────────┐
│  Streamlit UI                   │
│  ├── Web Call ボタン            │
│  ├── 実電話発信ボタン ★         │
│  ├── 品質/コスト トグル ★       │
│  └── 設定（Retell API Key等）   │
├─────────────────────────────────┤
│  FastAPI                        │
│  ├── /calls/trigger             │
│  └── /calls/webhook             │
├─────────────────────────────────┤
│  RetellProvider                 │
│  ├── agent_id (default)         │
│  └── budget_agent_id ★          │
├─────────────────────────────────┤
│  TemplateManager                │
│  EmailService                   │
│  CallAnalytics (基本) ★         │
│  NotifyService (Webhook) ★      │
├─────────────────────────────────┤
│  SQLite                         │
└─────────────────────────────────┘
```

**設定例**:
```yaml
tier: "lightweight"
voice:
  provider: "retell"
  retell:
    api_key: "key_..."
    agent_id: "agent_high_quality"
    budget_agent_id: "agent_budget"
    settings:
      interruption_sensitivity: 0.8
      responsiveness: 0.9
      ...
```

### Tier 3: Full (~$100/月)

```
┌─────────────────────────────────┐
│  Streamlit UI                   │
│  ├── Web Call ボタン            │
│  ├── 実電話発信ボタン           │
│  ├── 品質/コスト/Flow トグル    │
│  ├── バッチ通話UI ★★            │
│  ├── KPIダッシュボード ★★       │
│  └── 設定（全Provider対応）     │
├─────────────────────────────────┤
│  FastAPI                        │
│  ├── /calls/trigger             │
│  ├── /calls/webhook             │
│  ├── /calls/batch-trigger ★★    │
│  └── /analytics/kpi ★★          │
├─────────────────────────────────┤
│  RetellProvider or BlandProvider│
│  ├── agent_id (default)         │
│  ├── budget_agent_id            │
│  └── flow_agent_id ★★           │
├─────────────────────────────────┤
│  TemplateManager                │
│  EmailService                   │
│  CallAnalytics (高度) ★★        │
│  BatchCallService ★★            │
│  NotifyService (自動)           │
├─────────────────────────────────┤
│  SQLite                         │
└─────────────────────────────────┘
```

**設定例**:
```yaml
tier: "full"
voice:
  provider: "retell"   # or "bland"
  retell:
    api_key: "key_..."
    agent_id: "agent_default"
    budget_agent_id: "agent_budget"
    flow_agent_id: "agent_flow"
    settings:
      interruption_sensitivity: 0.8
      denoising_mode: "noise-and-background-speech-cancellation"
      ...
  bland:
    api_key: "..."
    pathway_id: "..."
```

---

## 5. データフロー

### 5.1 通話発信フロー

```
ユーザー操作（UI）
    │
    ▼
Streamlit → FastAPI /calls/trigger
    │
    ▼
calls.py → VoiceProvider.create_call()
    │
    ├── Tier 1: MockProvider → エラー（電話不可）
    ├── Tier 2: RetellProvider → agent_id or budget_agent_id
    └── Tier 3: RetellProvider → agent_id or budget_agent_id or flow_agent_id
              or BlandProvider → pathway_id
    │
    ▼
外部API（Retell/Bland）→ 通話開始
    │
    ▼
database.py → call_records INSERT
```

### 5.2 Webhook処理フロー

```
Retell/Bland → POST /calls/webhook
    │
    ▼
VoiceProvider.parse_webhook(payload)
    │
    ▼
WebhookResult（統一データ構造）
    │
    ▼
database.py → call_records UPDATE
    │
    ▼
NotifyService → LINE通知
```

### 5.3 Tier判定フロー

```
load_config()
    │
    ▼
get_tier(config) → "free" | "lightweight" | "full"
    │
    ▼
get_voice_provider(config) → VoiceProvider
    │
    ├── tier == "free" and no API key → MockProvider
    ├── provider == "retell"          → RetellProvider
    ├── provider == "bland"           → BlandProvider
    └── fallback                      → MockProvider
    │
    ▼
is_feature_enabled(config, feature) → bool
    │
    ▼
UI/API で機能のON/OFFを判定
```

---

## 6. 機能フラグ定義

| フラグ | Tier 1 | Tier 2 | Tier 3 | 説明 |
|--------|--------|--------|--------|------|
| `web_call` | ✅ | ✅ | ✅ | ブラウザ通話 |
| `phone_call` | ❌ | ✅ | ✅ | 実際の電話発信 |
| `budget_mode` | ❌ | ✅ | ✅ | GPT-4.1-mini Agent |
| `flow_mode` | ❌ | ❌ | ✅ | Conversation Flow Agent |
| `batch_call` | ❌ | ❌ | ✅ | バッチ通話 |
| `template_edit` | ✅ | ✅ | ✅ | テンプレート編集 |
| `email` | ✅ | ✅ | ✅ | メール確認 |
| `webhook` | ❌ | ✅ | ✅ | Webhook自動処理 |
| `line_notify` | ❌ | ✅ | ✅ | LINE通知 |
| `analytics_basic` | ❌ | ✅ | ✅ | 基本トランスクリプト分析 |
| `analytics_advanced` | ❌ | ❌ | ✅ | KPI分析・ダッシュボード |
| `provider_bland` | ❌ | ❌ | ✅ | Bland AI プロバイダー |
| `advanced_denoising` | ❌ | ❌ | ✅ | 高度ノイズ除去 |

---

## 7. 移行パス

### Tier 1 → Tier 2

1. Retell AI Dashboard で Agent 作成（GPT-4.1-mini）
2. Retell 電話番号購入 ($2/月)
3. `config.yaml` 更新:
   ```yaml
   tier: "lightweight"
   voice:
     retell:
       api_key: "key_..."
       agent_id: "agent_..."
       budget_agent_id: "agent_..."
   ```
4. アプリ再起動 → 自動的に Tier 2 で動作

### Tier 2 → Tier 3

1. Retell AI Dashboard で Conversation Flow Agent 作成
2. `config.yaml` 更新:
   ```yaml
   tier: "full"
   voice:
     retell:
       flow_agent_id: "agent_flow_..."
       settings:
         denoising_mode: "noise-and-background-speech-cancellation"
   ```
3. アプリ再起動 → 自動的に Tier 3 で動作

### Retell → Bland (Tier 3 Option B)

1. Bland AI アカウント作成 + Pathway 設定
2. `config.yaml` 更新:
   ```yaml
   voice:
     provider: "bland"
     bland:
       api_key: "..."
       pathway_id: "..."
   ```
3. アプリ再起動 → BlandProvider が自動選択

---

## 8. テスト戦略

### ユニットテスト

| テスト | 対象 | 説明 |
|--------|------|------|
| `test_mock_provider` | MockProvider | 全メソッドの動作確認 |
| `test_retell_provider` | RetellProvider | API呼び出しモックで検証 |
| `test_tier_detection` | ConfigManager | 各Tier設定の正しい判定 |
| `test_feature_flags` | is_feature_enabled | 機能フラグの組み合わせ |

### 統合テスト

| テスト | 対象 | 説明 |
|--------|------|------|
| `test_tier1_flow` | Tier 1 全体 | Web Call → MockProvider → 結果表示 |
| `test_tier2_flow` | Tier 2 全体 | 実電話 → RetellProvider → Webhook → DB保存 |
| `test_tier3_flow` | Tier 3 全体 | Flow Agent → バッチ → KPI分析 |

---

## 関連ドキュメント

- [割り込み対応設計](interruption-handling.md) — 技術詳細・プロンプト設計
- [段階別ソリューション](solution-tiers.md) — 費用計算・機能比較
- [アーキテクチャ概要](../architecture.md) — 技術スタック・移行戦略
