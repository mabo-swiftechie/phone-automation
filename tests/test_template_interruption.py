from __future__ import annotations

from app.services.template_manager import DEFAULT_BLOCKS


def _find_block(name: str) -> dict:
    for b in DEFAULT_BLOCKS:
        if b["name"] == name:
            return b
    return {}


# ── 対話ルール: 割り込み対応 ──


class TestInterruptionRules:

    def test_dialog_rules_block_exists(self):
        block = _find_block("対話ルール")
        assert block, "対話ルール block must exist in DEFAULT_BLOCKS"
        assert block["type"] == "instruction"

    def test_contains_barge_in_keyword(self):
        content = _find_block("対話ルール")["content"]
        assert "割り込み" in content, "Must contain '割り込み' keyword"

    def test_contains_no_repeat_rule(self):
        content = _find_block("対話ルール")["content"]
        assert "繰り返さ" in content, "Must contain anti-repetition rule ('繰り返さ')"

    def test_contains_immediate_acknowledgment(self):
        content = _find_block("対話ルール")["content"]
        assert "承知いたしました" in content, "Must contain immediate acknowledgment phrase"

    def test_contains_no_bulk_summary_rule(self):
        content = _find_block("対話ルール")["content"]
        assert "一括まとめはしない" in content, "Must prohibit bulk summary at end"

    def test_contains_stop_on_interrupt(self):
        content = _find_block("対話ルール")["content"]
        assert "即座に止まって" in content, "Must instruct to stop immediately on interrupt"

    def test_differentiates_backchannel_vs_new_info(self):
        content = _find_block("対話ルール")["content"]
        assert "短い相槌" in content, "Must differentiate short backchannels"
        assert "新しい情報" in content, "Must handle new information differently"


# ── 終了ルール: 反復防止 ──


class TestClosingRules:

    def test_closing_rules_block_exists(self):
        block = _find_block("終了ルール")
        assert block, "終了ルール block must exist in DEFAULT_BLOCKS"
        assert block["type"] == "closing"

    def test_prohibits_summary_phrase(self):
        content = _find_block("終了ルール")["content"]
        assert "確認させていただきますと" in content, "Must explicitly prohibit '確認させていただきますと' phrase"

    def test_no_long_summary(self):
        content = _find_block("終了ルール")["content"]
        assert "長いまとめはしない" in content, "Must instruct no long summary"

    def test_concise_closing(self):
        content = _find_block("終了ルール")["content"]
        assert "ありがとうございました" in content, "Must have concise thank-you closing"
        assert "失礼いたします" in content

    def test_no_repetition_of_stated_info(self):
        content = _find_block("終了ルール")["content"]
        assert "繰り返さない" in content, "Must prohibit repeating already-stated info"


# ── DEFAULT_BLOCKS structure ──


class TestBlocksStructure:

    def test_all_required_blocks_exist(self):
        names = {b["name"] for b in DEFAULT_BLOCKS}
        required = {"敬語ルール", "空室確認", "外国人確認", "中国人確認", "入居条件確認", "対話ルール", "終了ルール"}
        assert required.issubset(names), f"Missing blocks: {required - names}"

    def test_all_blocks_have_content(self):
        for b in DEFAULT_BLOCKS:
            assert b.get("content"), f"Block '{b['name']}' must have content"

    def test_all_blocks_have_type(self):
        valid_types = {"greeting", "question", "followup", "closing", "instruction"}
        for b in DEFAULT_BLOCKS:
            assert b["type"] in valid_types, f"Block '{b['name']}' has invalid type: {b['type']}"

    def test_system_blocks_marked(self):
        for b in DEFAULT_BLOCKS:
            assert b.get("is_system") is True, f"Block '{b['name']}' should be is_system=True"
