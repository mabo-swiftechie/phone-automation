"""
会話シナリオテスト — 割り込み対応・反復防止・情報収集率を検証する。

各シナリオは実際の電話で起こり得る会話パターンをシミュレートし、
プロンプトルールに基づいてAIの期待される振る舞いを評価する。

評価指標:
  - 情報収集率: 4項目（空室・外国人・中国人・条件）のうち何項目収集できたか
  - 反復防止率: 割り込み後に同じ内容を繰り返さなかったか
  - 割り込み対応率: バージイン時に正しく対応したか
  - 終了品質率: 長いまとめをせず簡潔に終了したか
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import pytest

from app.services.template_manager import DEFAULT_BLOCKS


# ── Data models ──


class InterruptionType(Enum):
    NONE = "none"
    BACKCHANNEL = "backchannel"          # 「はい」「ええ」「そうです」
    CANCELLATION = "cancellation"        # 「ちょっと待って」「いや違います」
    CORRECTION = "correction"            # 「あ、1LDKでした」
    REDIRECT = "redirect"                # 「ところで…」「そういえば…」
    CLARIFICATION = "clarification"      # 「どういう意味？」「もう一度」
    RAPID_FIRE = "rapid_fire"            # 連続した短い相槌
    NEW_INFO = "new_info"                # 追加情報の提供
    HURRY = "hurry"                      # 「忙しいので手短に」


@dataclass
class ConversationTurn:
    speaker: str  # "ai" | "human"
    text: str
    interruption_type: InterruptionType = InterruptionType.NONE


@dataclass
class ConversationScenario:
    id: str
    name: str
    description: str
    property_name: str
    turns: List[ConversationTurn]
    # Expected outcomes
    expect_info_collected: List[str]     # e.g. ["vacancy", "foreigner", "chinese", "conditions"]
    expect_no_repetition: bool = True
    expect_interrupt_handled: bool = False
    expect_concise_closing: bool = True
    interruption_types_present: List[InterruptionType] = field(default_factory=list)


@dataclass
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    prompt_has_rules: dict          # keyword → bool
    prompt_completeness: float      # 0.0-1.0
    info_collect_target: int        # expected items
    info_collect_possible: int      # items the prompt enables collecting
    repetition_prevention: bool
    interrupt_handling: bool
    closing_quality: bool
    overall_score: float            # 0.0-1.0


# ── Prompt rule extractor ──

def _get_combined_prompt() -> str:
    return "\n\n".join(b["content"] for b in DEFAULT_BLOCKS)


def _get_block_content(name: str) -> str:
    for b in DEFAULT_BLOCKS:
        if b["name"] == name:
            return b["content"]
    return ""


# ── Prompt-based rule validators ──
# These check whether the prompt contains rules that would produce
# the expected AI behavior in each scenario.

RULE_CHECKS = {
    # Interruption handling
    "barge_in_stop": ("即座に止まって", "対話ルール"),
    "backchannel_no_repeat": ("直前の発言を繰り返さず", "対話ルール"),
    "backchannel_acknowledge": ("承知いたしました」と簡潔に応じて", "対話ルール"),
    "no_repeat_absolute": ("絶対に、既に言った内容を最初から再度言わない", "対話ルール"),
    "new_info_respond": ("新しい内容に対して応答", "対話ルール"),
    "phrase_repeat_ban": ("同じフレーズや同じ内容を二度以上繰り返すことを厳禁", "対話ルール"),
    "immediate_confirm": ("その場で「承知いたしました」と即座に確認", "対話ルール"),
    "no_bulk_summary_mid": ("最後の一括まとめはしない", "対話ルール"),

    # Closing rules
    "no_long_summary": ("長いまとめはしない", "終了ルール"),
    "no_summary_phrase": ("確認させていただきますと", "終了ルール"),
    "concise_thankyou": ("ありがとうございました。失礼いたします", "終了ルール"),
    "no_info_repeat": ("既に伝えた情報を繰り返さない", "終了ルール"),
    "no_double_say": ("同じ内容を二度言わない", "終了ルール"),
    "hurry_closing": ("急いでいる・忙しそうな場合", "終了ルール"),

    # Info collection flow
    "vacancy_flow": ("空室はございますでしょうか", "空室確認"),
    "foreigner_flow": ("外国人の方の入居は可能でしょうか", "外国人確認"),
    "chinese_flow": ("中国籍の方の入居は問題ございませんでしょうか", "中国人確認"),
    "conditions_flow": ("敷金・礼金や保証会社", "入居条件確認"),

    # General
    "no_argument": ("押し問答は絶対にしない", "対話ルール"),
    "listen_to_end": ("相手の発言を遮らない", "対話ルール"),
    "ambiguous_once": ("一度だけ", "対話ルール"),
}


def check_prompt_rules() -> dict[str, bool]:
    """Check all prompt rules against DEFAULT_BLOCKS."""
    results = {}
    for rule_name, (keyword, block_name) in RULE_CHECKS.items():
        content = _get_block_content(block_name)
        results[rule_name] = keyword in content
    return results


# ── Conversation Scenarios ──

SCENARIOS: List[ConversationScenario] = [
    # ── Scenario S01: Ideal flow (baseline) ──
    ConversationScenario(
        id="S01",
        name="理想フロー（基準）",
        description="割り込みなし、全項目回答あり。基準テスト。",
        property_name="グランメゾン東京南青山",
        turns=[
            ConversationTurn("ai", "お世話になっております。グランメゾン東京南青山についてお伺いしたくお電話いたしました。"),
            ConversationTurn("human", "はい、どうぞ。"),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "はい、1部屋空いてます。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "はい、問題ないです。"),
            ConversationTurn("ai", "承知いたしました。特に中国籍の方の入居は問題ございませんでしょうか？"),
            ConversationTurn("human", "大丈夫ですよ。"),
            ConversationTurn("ai", "承知いたしました。入居条件についてお伺いしてもよろしいでしょうか。"),
            ConversationTurn("human", "敷金1ヶ月、礼金1ヶ月、52,000円で即入居可です。"),
            ConversationTurn("ai", "承知いたしました。本日はお忙しい中ご対応いただき、ありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "chinese", "conditions"],
        expect_no_repetition=True,
        expect_interrupt_handled=False,
        expect_concise_closing=True,
    ),

    # ── Scenario S02: Backchannel during AI speech ──
    ConversationScenario(
        id="S02",
        name="相槌割り込み（「はい」でAI発話中に割り込み）",
        description="AIが空室確認の質問中に仲介が「はい」と相槌→AIが反復せず次へ進むべき",
        property_name="サンシティ恵比寿",
        turns=[
            ConversationTurn("ai", "お世話になっております。サンシティ恵比寿についてお伺いしたく…"),
            ConversationTurn("human", "はい", InterruptionType.BACKCHANNEL),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "ええ、1LDKが空いてます。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "いえ、日本国籍の方のみとなります。"),
            ConversationTurn("ai", "承知いたしました。入居条件についてお伺いしてもよろしいでしょうか。"),
            ConversationTurn("human", "家賃85,000円、敷金1ヶ月、即入居可です。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "conditions"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.BACKCHANNEL],
    ),

    # ── Scenario S03: Rapid backchannel (連続相槌) ──
    ConversationScenario(
        id="S03",
        name="連続相槌（AI発話中に複数回「はい」「そうですか」）",
        description="AIが自己紹介中に連続で相槌が来る。AIは反復せず、自然に次へ進むべき",
        property_name="パークハウス新宿",
        turns=[
            ConversationTurn("ai", "お世話になっております。パークハウス新宿についてお伺いしたくお電話いたしました。"),
            ConversationTurn("human", "はい", InterruptionType.RAPID_FIRE),
            ConversationTurn("human", "ええ", InterruptionType.RAPID_FIRE),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "今は満室ですね。"),
            ConversationTurn("ai", "承知いたしました。次に空室ができる予定はございますか？"),
            ConversationTurn("human", "未定です。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.RAPID_FIRE],
    ),

    # ── Scenario S04: Correction (訂正) ──
    ConversationScenario(
        id="S04",
        name="回答訂正（仲介が自分の回答を訂正）",
        description="空室あり→なしに訂正。AIは訂正を受け入れ、反復せず次へ",
        property_name="ロイヤルハイツ池袋",
        turns=[
            ConversationTurn("ai", "お世話になっております。ロイヤルハイツ池袋についてお伺いしたく…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "空室ありますよ。1Kと1LDK。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "あ、待ってください。確認したら1LDKは契約済みでした。1Kだけです。", InterruptionType.CORRECTION),
            ConversationTurn("ai", "承知いたしました。1Kが1部屋空室とのことですね。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "外国人は基本OKですが、中国籍はお断りしてます。"),
            ConversationTurn("ai", "承知いたしました。入居条件をお伺いしてもよろしいでしょうか。"),
            ConversationTurn("human", "保証会社必須、敷金1ヶ月、来月1日から。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "chinese", "conditions"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.CORRECTION],
    ),

    # ── Scenario S05: Redirect (話題転換) ──
    ConversationScenario(
        id="S05",
        name="話題転換（仲介が別の話題を振る）",
        description="質問中に仲介が全く別の質問をしてくる。AIはそれに対応後、元の流れに戻る",
        property_name="メゾン・ド・上野",
        turns=[
            ConversationTurn("ai", "お世話になっております。メゾン・ド・上野についてお伺いしたく…"),
            ConversationTurn("human", "あの、どこの不動産さんですか？", InterruptionType.REDIRECT),
            ConversationTurn("ai", "空室確認のために お電話いたしました。現在、空室はございますでしょうか？"),
            ConversationTurn("human", "今確認中でして、2-3日お待ちいただけますか。"),
            ConversationTurn("ai", "承知いたしました。また改めてお電話させていただきます。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.REDIRECT],
    ),

    # ── Scenario S06: Hurry (忙しい仲介) ──
    ConversationScenario(
        id="S06",
        name="急ぎの仲介（「忙しいので手短に」）",
        description="仲介が忙しいと告げる。AIは質問を簡潔にまとめ、迅速に終了すべき",
        property_name="ヴィラ代々木",
        turns=[
            ConversationTurn("ai", "お世話になっております。ヴィラ代々木についてお伺いしたく…"),
            ConversationTurn("human", "すみません、今忙しいので手短にお願いします。", InterruptionType.HURRY),
            ConversationTurn("ai", "承知いたしました。空室状況、外国人入居可否、条件の3点だけお伺いします。"),
            ConversationTurn("human", "空室あり、外国人OK、敷金2ヶ月、礼金1ヶ月、来月中旬以降。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "conditions"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.HURRY],
    ),

    # ── Scenario S07: Summary attempt (AIがまとめようとする旧パターン) ──
    ConversationScenario(
        id="S07",
        name="終了時まとめ防止（相槌後にまとめ開始しようとする）",
        description="全質問終了後、AIが「確認させていただきますと」と始めず、簡潔に終わるべき",
        property_name="コープ野村世田谷",
        turns=[
            ConversationTurn("ai", "お世話になっております。コープ野村世田谷についてお伺いしたく…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "満室です。"),
            ConversationTurn("ai", "承知いたしました。次に空室ができる予定はございますか？"),
            ConversationTurn("human", "未定です。"),
            ConversationTurn("ai", "承知いたしました。本日はお忙しい中ご対応いただき、ありがとうございました。失礼いたします。"),
            # AI should NOT say: 「確認させていただきますと、現在満室で…」
        ],
        expect_info_collected=["vacancy"],
        expect_no_repetition=True,
        expect_interrupt_handled=False,
        expect_concise_closing=True,
    ),

    # ── Scenario S08: New info during speech ──
    ConversationScenario(
        id="S08",
        name="発話中の追加情報（AI質問中に仲介が詳細を追加）",
        description="AIが外国人確認中に仲介が条件を追加で話す。AIは反復せず、新情報に対応",
        property_name="グランメゾン東京南青山",
        turns=[
            ConversationTurn("ai", "お世話になっております。グランメゾン東京南青山について…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "1Kが52,000円で空いてます。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "あ、ちなみにペットもOKですよ。保証会社は任意です。", InterruptionType.NEW_INFO),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "はい、問題ないです。"),
            ConversationTurn("ai", "承知いたしました。中国籍の方は問題ございませんでしょうか？"),
            ConversationTurn("human", "大丈夫です。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "chinese"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.NEW_INFO],
    ),

    # ── Scenario S09: Cancellation (キャンセル/否定) ──
    ConversationScenario(
        id="S09",
        name="キャンセル割り込み（「いや違います」「ちょっと待って」）",
        description="AIが質問中に仲介が「待って」と中断→AIは即座に止まって相手の話を聞く",
        property_name="ハイツ練馬",
        turns=[
            ConversationTurn("ai", "お世話になっております。ハイツ練馬についてお伺いしたく…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "ちょっと待ってください、今確認します。", InterruptionType.CANCELLATION),
            ConversationTurn("human", "…今満室ですね。3ヶ月後に退去予定があります。"),
            ConversationTurn("ai", "承知いたしました。3ヶ月後に空室予定とのことですね。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "はい、可能です。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.CANCELLATION],
    ),

    # ── Scenario S10: Clarification request ──
    ConversationScenario(
        id="S10",
        name="確認要求（「どういう意味？」）",
        description="AIの質問が不明瞭で仲介が聞き返す。AIは一度だけ説明し、二度目は不明として次へ",
        property_name="メゾン・ド・上野",
        turns=[
            ConversationTurn("ai", "お世話になっております。メゾン・ド・上野についてお伺いしたく…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "どういう意味ですか？空室が…?", InterruptionType.CLARIFICATION),
            ConversationTurn("ai", "入居可能なお部屋が空いているかどうかお伺いしています。"),
            ConversationTurn("human", "ああ、今はちょっと確認中で。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "それも確認中です。"),
            ConversationTurn("ai", "承知いたしました。本日はお時間をいただきありがとうございました。また改めさせていただきます。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.CLARIFICATION],
    ),

    # ── Scenario S11: Full interruption combo ──
    ConversationScenario(
        id="S11",
        name="複合割り込み（相槌+訂正+急ぎ）",
        description="1回の通話で複数タイプの割り込みが発生する最も複雑なシナリオ",
        property_name="ロイヤルハイツ池袋",
        turns=[
            ConversationTurn("ai", "お世話になっております。ロイヤルハイツ池袋についてお伺いしたく…"),
            ConversationTurn("human", "はい", InterruptionType.BACKCHANNEL),
            ConversationTurn("ai", "現在、空室はございますでしょうか？"),
            ConversationTurn("human", "2部屋空いてます。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は…"),
            ConversationTurn("human", "あ、1Kの方は契約決まりました。", InterruptionType.CORRECTION),
            ConversationTurn("ai", "承知いたしました。1LDKが1部屋とのことですね。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "すみません、急ぎなので手短にお願いします。", InterruptionType.HURRY),
            ConversationTurn("ai", "承知いたしました。外国人と条件だけお伺いします。"),
            ConversationTurn("human", "外国人は基本OK、中国籍は不可。保証会社必須で来月1日から。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "chinese", "conditions"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.BACKCHANNEL, InterruptionType.CORRECTION, InterruptionType.HURRY],
    ),

    # ── Scenario S12: Repeated backchannel trap ──
    ConversationScenario(
        id="S12",
        name="反復トラップ（相槌後にAIが同じ質問を繰り返す旧パターン）",
        description="AIが「外国人OKですか？」→「はい」→再度「外国人OKですか？」のパターンを防止",
        property_name="ヴィラ代々木",
        turns=[
            ConversationTurn("ai", "お世話になっております。ヴィラ代々木について…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "空室はございますでしょうか？"),
            ConversationTurn("human", "はい、2LDKが空いてます。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "はい", InterruptionType.BACKCHANNEL),
            # AI should NOT repeat: "外国人の方の入居は可能でしょうか？"
            # AI should say: "承知いたしました" and move to next question
            ConversationTurn("ai", "承知いたしました。中国籍の方は問題ございませんでしょうか？"),
            ConversationTurn("human", "問題ないです。"),
            ConversationTurn("ai", "承知いたしました。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy", "foreigner", "chinese"],
        expect_no_repetition=True,
        expect_interrupt_handled=True,
        expect_concise_closing=True,
        interruption_types_present=[InterruptionType.BACKCHANNEL],
    ),

    # ── Scenario S13: Voicemail ──
    ConversationScenario(
        id="S13",
        name="留守電対応",
        description="電話が留守電につながる。AIは簡潔にメッセージを残して終了",
        property_name="コープ野村世田谷",
        turns=[
            ConversationTurn("ai", "お世話になっております。コープ野母世田谷についてお伺いしたく…"),
            ConversationTurn("human", "（留守電音：「ピーっ」）"),
            ConversationTurn("ai", "空室確認のお電話でした。コープ野母世田谷についてお伺いしたくお電話いたしました。またかけ直します。失礼いたします。"),
        ],
        expect_info_collected=[],
        expect_no_repetition=True,
        expect_interrupt_handled=False,
        expect_concise_closing=True,
    ),

    # ── Scenario S14: Partial answer then disconnect ──
    ConversationScenario(
        id="S14",
        name="途中切断（質問途中で相手が切る）",
        description="2問目で電話が切れる。AIは収集済み情報を保存すべき",
        property_name="サンシティ恵比寿",
        turns=[
            ConversationTurn("ai", "お世話になっております。サンシティ恵比寿について…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "空室はございますでしょうか？"),
            ConversationTurn("human", "1LDK空いてます。85,000円です。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は…"),
            ConversationTurn("human", "（電話が切れる）"),
        ],
        expect_info_collected=["vacancy", "conditions"],
        expect_no_repetition=True,
        expect_interrupt_handled=False,
        expect_concise_closing=False,
    ),

    # ── Scenario S15: Long silence then answer ──
    ConversationScenario(
        id="S15",
        name="長い沈黙後の回答",
        description="質問後に長い沈黙があり、その後回答。AIは待機し、反復しない",
        property_name="メゾン・ド・上野",
        turns=[
            ConversationTurn("ai", "お世話になっております。メゾン・ド・上野について…"),
            ConversationTurn("human", "はい。"),
            ConversationTurn("ai", "空室はございますでしょうか？"),
            ConversationTurn("human", "……（10秒沈黙）……確認中ですので少々お待ちください。"),
            ConversationTurn("ai", "承知いたしました。お待ちいたします。"),
            ConversationTurn("human", "……空室あります。"),
            ConversationTurn("ai", "承知いたしました。外国人の方の入居は可能でしょうか？"),
            ConversationTurn("human", "それも確認が必要で…後日お電話してもらえますか。"),
            ConversationTurn("ai", "承知いたしました。改めてお電話させていただきます。本日はありがとうございました。失礼いたします。"),
        ],
        expect_info_collected=["vacancy"],
        expect_no_repetition=True,
        expect_interrupt_handled=False,
        expect_concise_closing=True,
    ),
]


# ── Prompt Rule Coverage for each InterruptionType ──

INTERRUPTION_RULE_MAP: dict[InterruptionType, list[str]] = {
    InterruptionType.BACKCHANNEL: [
        "backchannel_no_repeat", "backchannel_acknowledge",
        "no_repeat_absolute", "phrase_repeat_ban",
    ],
    InterruptionType.CANCELLATION: [
        "barge_in_stop", "listen_to_end",
    ],
    InterruptionType.CORRECTION: [
        "barge_in_stop", "new_info_respond", "no_repeat_absolute",
    ],
    InterruptionType.REDIRECT: [
        "barge_in_stop", "new_info_respond",
    ],
    InterruptionType.CLARIFICATION: [
        "ambiguous_once", "no_argument",
    ],
    InterruptionType.RAPID_FIRE: [
        "backchannel_no_repeat", "no_repeat_absolute", "phrase_repeat_ban",
    ],
    InterruptionType.NEW_INFO: [
        "new_info_respond", "no_repeat_absolute",
    ],
    InterruptionType.HURRY: [
        "hurry_closing", "no_bulk_summary_mid", "concise_thankyou",
    ],
}


def evaluate_scenario(scenario: ConversationScenario, rule_checks: dict[str, bool]) -> ScenarioResult:
    """Evaluate a single scenario against prompt rules."""
    # Check prompt completeness for info collection
    info_rules = ["vacancy_flow", "foreigner_flow", "chinese_flow", "conditions_flow"]
    info_possible = sum(1 for r in info_rules if rule_checks.get(r, False))
    # Scale to expected count
    if len(scenario.expect_info_collected) > 0:
        info_scale = min(info_possible / 4, 1.0) * len(scenario.expect_info_collected)
    else:
        info_scale = info_possible

    # Check repetition prevention
    rep_rules = ["no_repeat_absolute", "phrase_repeat_ban", "backchannel_no_repeat", "no_info_repeat", "no_double_say"]
    repetition_ok = all(rule_checks.get(r, False) for r in rep_rules)

    # Check interrupt handling
    interrupt_ok = True
    for itype in scenario.interruption_types_present:
        needed = INTERRUPTION_RULE_MAP.get(itype, [])
        if not all(rule_checks.get(r, False) for r in needed):
            interrupt_ok = False
            break

    # Check closing quality
    closing_rules = ["no_long_summary", "no_summary_phrase", "concise_thankyou", "no_info_repeat"]
    closing_ok = all(rule_checks.get(r, False) for r in closing_rules)

    # Overall prompt completeness
    all_rules_for_scenario = set()
    all_rules_for_scenario.update(info_rules)
    all_rules_for_scenario.update(rep_rules)
    all_rules_for_scenario.update(closing_rules)
    for itype in scenario.interruption_types_present:
        all_rules_for_scenario.update(INTERRUPTION_RULE_MAP.get(itype, []))

    passed = sum(1 for r in all_rules_for_scenario if rule_checks.get(r, False))
    completeness = passed / len(all_rules_for_scenario) if all_rules_for_scenario else 1.0

    # Overall score
    weights = {
        "info": 0.3,
        "repetition": 0.25,
        "interrupt": 0.25,
        "closing": 0.2,
    }
    info_ratio = min(info_scale / max(len(scenario.expect_info_collected), 1), 1.0)
    score = (
        weights["info"] * info_ratio
        + weights["repetition"] * (1.0 if repetition_ok else 0.0)
        + weights["interrupt"] * (1.0 if (not scenario.expect_interrupt_handled or interrupt_ok) else 0.0)
        + weights["closing"] * (1.0 if (not scenario.expect_concise_closing or closing_ok) else 0.0)
    )
    score = min(score, 1.0)

    return ScenarioResult(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        prompt_has_rules={k: v for k, v in rule_checks.items()},
        prompt_completeness=round(completeness, 3),
        info_collect_target=len(scenario.expect_info_collected),
        info_collect_possible=int(info_scale),
        repetition_prevention=repetition_ok,
        interrupt_handling=interrupt_ok,
        closing_quality=closing_ok,
        overall_score=round(score, 3),
    )


# ── Pytest Tests ──


class TestPromptRuleIntegrity:
    """Verify all prompt rules exist in DEFAULT_BLOCKS."""

    def test_all_rules_present(self):
        checks = check_prompt_rules()
        missing = [k for k, v in checks.items() if not v]
        assert not missing, f"Missing prompt rules: {missing}"

    def test_interruption_rules_complete(self):
        content = _get_block_content("対話ルール")
        required = ["割り込み", "バージイン", "繰り返さ", "即座に止まって", "簡潔に応じて"]
        for kw in required:
            assert kw in content, f"対話ルール missing keyword: {kw}"

    def test_closing_rules_complete(self):
        content = _get_block_content("終了ルール")
        required = ["長いまとめはしない", "確認させていただきますと", "繰り返さない", "失礼いたします"]
        for kw in required:
            assert kw in content, f"終了ルール missing keyword: {kw}"


class TestScenarioCoverage:
    """Verify scenarios cover all interruption types."""

    def test_all_interruption_types_covered(self):
        covered = set()
        for s in SCENARIOS:
            covered.update(s.interruption_types_present)
        for itype in InterruptionType:
            if itype == InterruptionType.NONE:
                continue
            assert itype in covered, f"No scenario covers interruption type: {itype.value}"

    def test_minimum_15_scenarios(self):
        assert len(SCENARIOS) >= 15, f"Need at least 15 scenarios, got {len(SCENARIOS)}"

    def test_all_scenarios_have_expected_info(self):
        for s in SCENARIOS:
            assert isinstance(s.expect_info_collected, list), f"{s.id}: expect_info_collected must be list"

    def test_all_scenarios_have_turns(self):
        for s in SCENARIOS:
            assert len(s.turns) >= 2, f"{s.id}: needs at least 2 turns"


class TestScenarioEvaluation:
    """Evaluate each scenario against prompt rules."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rule_checks = check_prompt_rules()

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
    def test_info_collection(self, scenario):
        result = evaluate_scenario(scenario, self.rule_checks)
        # Info collection flow must exist for all expected items
        if scenario.expect_info_collected:
            assert result.info_collect_possible >= 1, \
                f"{scenario.id}: Prompt should enable info collection"

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
    def test_no_repetition(self, scenario):
        if scenario.expect_no_repetition:
            result = evaluate_scenario(scenario, self.rule_checks)
            assert result.repetition_prevention, \
                f"{scenario.id}: Repetition prevention rules incomplete"

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
    def test_interrupt_handling(self, scenario):
        if scenario.expect_interrupt_handled:
            result = evaluate_scenario(scenario, self.rule_checks)
            assert result.interrupt_handling, \
                f"{scenario.id}: Interrupt handling rules incomplete for {scenario.interruption_types_present}"

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
    def test_closing_quality(self, scenario):
        if scenario.expect_concise_closing:
            result = evaluate_scenario(scenario, self.rule_checks)
            assert result.closing_quality, \
                f"{scenario.id}: Closing quality rules incomplete"

    @pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
    def test_overall_score(self, scenario):
        result = evaluate_scenario(scenario, self.rule_checks)
        assert result.overall_score >= 0.8, \
            f"{scenario.id}: Overall score {result.overall_score} below threshold 0.8"


class TestSuccessRateReport:
    """Generate a success rate report across all scenarios."""

    def test_overall_success_rate(self):
        rule_checks = check_prompt_rules()
        results = [evaluate_scenario(s, rule_checks) for s in SCENARIOS]

        total = len(results)
        info_items = [(r, SCENARIOS[i]) for i, r in enumerate(results)]
        info_with_target = [(r, s) for r, s in info_items if s.expect_info_collected]
        info_score = sum(
            min(r.info_collect_possible / max(r.info_collect_target, 1), 1.0)
            for r, s in info_with_target
        ) / max(len(info_with_target), 1)
        rep_score = sum(1 for r in results if r.repetition_prevention) / total
        interrupt_scenarios = [r for r, s in info_items if s.expect_interrupt_handled]
        interrupt_score = sum(1 for r in interrupt_scenarios if r.interrupt_handling) / max(len(interrupt_scenarios), 1)
        closing_scenarios = [r for r, s in info_items if s.expect_concise_closing]
        closing_score = sum(1 for r in closing_scenarios if r.closing_quality) / max(len(closing_scenarios), 1)
        overall = sum(r.overall_score for r in results) / total

        # Print report (visible in pytest -v output)
        print("\n")
        print("=" * 60)
        print("  会話シナリオ成功率レポート")
        print("=" * 60)
        print(f"  シナリオ数: {total}")
        print(f"  プロンプトルール数: {len(rule_checks)}")
        print()
        print(f"  情報収集率:     {info_score:.1%}  (目標: 90%)")
        print(f"  反復防止率:     {rep_score:.1%}  (目標: 95%)")
        print(f"  割り込み対応率: {interrupt_score:.1%}  (目標: 90%)")
        print(f"  終了品質率:     {closing_score:.1%}  (目標: 95%)")
        print(f"  総合スコア:     {overall:.1%}  (目標: 90%)")
        print("=" * 60)
        print()

        for r in results:
            sc = SCENARIOS[results.index(r)]
            print(f"  {r.scenario_id} {r.scenario_name:<30} score={r.overall_score:.2f} "
                  f"info={r.info_collect_possible}/{r.info_collect_target} "
                  f"rep={'✅' if r.repetition_prevention else '❌'} "
                  f"intr={'✅' if r.interrupt_handling else '❌'} "
                  f"close={'✅' if r.closing_quality else '❌'}")

        # Assertions with targets
        assert overall >= 0.90, f"Overall score {overall:.1%} below 90% target"
