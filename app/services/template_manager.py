from __future__ import annotations
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.paths import DATA_DIR

DB_PATH = DATA_DIR / "data.db"

BLOCK_TYPES = ["greeting", "question", "followup", "closing", "instruction"]
BLOCK_TYPE_LABELS = {
    "greeting": "挨拶", "question": "質問", "followup": "フォローアップ",
    "closing": "終了", "instruction": "指示",
}

DEFAULT_BLOCKS = [
    {
        "name": "敬語ルール",
        "type": "instruction",
        "description": "敬語の使い方と挨拶のルール",
        "content": "あなたは日本の不動産管理会社に電話をかける空室確認アシスタントです。\n物件名: {{property_name}}\n\n【敬語ルール】\n- 常に丁寧語（〜です・ます・ございます）を使用してください\n- 電話の冒頭は必ず「お世話になっております。{{property_name}}についてお伺いしたくお電話いたしました」と始めてください\n- 相手を敬称で呼んでください",
        "is_system": True,
    },
    {
        "name": "空室確認",
        "type": "question",
        "description": "空室の有無を確認する",
        "content": "【確認: 空室状況】\n「現在、空室はございますでしょうか？」\n- あり →「ありがとうございます。詳しくお伺いしてもよろしいでしょうか」と次へ\n- なし →「承知いたしました。次に空室ができる予定はございますか？」と確認\n- 不明 →「承知いたしました」と受け止め次へ",
        "is_system": True,
    },
    {
        "name": "外国人確認",
        "type": "question",
        "description": "外国人の入居可否を確認する",
        "content": "【確認: 外国人入居可否】\n「外国人の方の入居は可能でしょうか？」\n- 可能 → 次の質問へ\n- 不可 →「承知いたしました」と受け止め次へ\n- 条件あり →「どのような条件でしょうか？」と詳細確認",
        "is_system": True,
    },
    {
        "name": "中国人確認",
        "type": "question",
        "description": "中国籍の入居可否を確認する",
        "content": "【確認: 中国籍入居可否】\n「特に中国籍の方の入居は問題ございませんでしょうか？」\n- 問題ない → 次の質問へ\n- 不可・条件あり → その詳細を確認",
        "is_system": True,
    },
    {
        "name": "入居条件確認",
        "type": "question",
        "description": "敷金・礼金・保証会社・賃料・入居日を確認する",
        "content": "【確認: 入居条件】\n「入居にあたり、敷金・礼金や保証会社の利用など、特別な条件はございますでしょうか？\nあと、月額賃料と入居可能時期もお教えいただけますでしょうか？」\n→ 回答を聞いて記録する",
        "is_system": True,
    },
    {
        "name": "対話ルール",
        "type": "instruction",
        "description": "会話中の振る舞いルール",
        "content": "【対話ルール】\n- 相手の発言を遮らない。最後まで聞く\n- 不明な回答は「承知いたしました」と受け止め次に進む\n- 押し問答は絶対にしない\n- 相手が話している時は相槌を打つ（はい、そうですか、承知いたしました）\n- 回答が曖昧な場合は一度だけ「もう少し詳しくお伺いしてもよろしいでしょうか」と確認\n- 二度目は不明のまま受け入れて次に進む\n\n【重要：割り込み（バージイン）対応ルール】\n- 自分が発話中に相手が話し始めたら、即座に止まって相手の話を聞く\n- 相手の発話が「はい」「ええ」「そうです」等の短い相槌の場合：\n  → 直前の発言を繰り返さず、「承知いたしました」と簡潔に応じて次の話題に進む\n  → 絶対に、既に言った内容を最初から再度言わない\n- 相手が新しい情報や質問を追加した場合のみ：\n  → その新しい内容に対して応答し、その後自然に会話を続ける\n- 同じフレーズや同じ内容を二度以上繰り返すことを厳禁する\n- 各質問への回答が得られたら、その場で「承知いたしました」と即座に確認し、次へ進む（最後の一括まとめはしない）",
        "is_system": True,
    },
    {
        "name": "終了ルール",
        "type": "closing",
        "description": "通話のまとめと終了",
        "content": "【終了ルール】\n全ての質問が終わったら、以下のルールで通話を終了する。\n\n1. 基本的に長いまとめはしない。各質問時にその場で確認済みなので、最後に再度まとめる必要はない\n2. 終了時は簡潔に：「本日はお忙しい中ご対応いただき、ありがとうございました。失礼いたします。」\n3. 相手が「はい」「わかりました」等で肯定的に応じた場合：即座に感謝を述べて終了。絶対に再度まとめない\n4. 相手が終了前に追加で何か言った場合：「承知いたしました。ありがとうございました。失礼いたします。」と簡潔に応えて終了\n5. 相手が急いでいる・忙しそうな場合は、お礼だけ述べて速やかに終了\n\n【終了時の厳守事項】\n- 「確認させていただきますと〜」という長いまとめフレーズは使わない\n- 既に伝えた情報を繰り返さない\n- 相手の相槌に対して同じ内容を二度言わない\n\n留守電の場合：「空室確認のお電話でした。{{property_name}}についてお伺いしたくお電話いたしました。またかけ直します。失礼いたします。」",
        "is_system": True,
    },
]


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def seed_default_template():
    default_id = get_default_template_id()
    if default_id and get_template(default_id):
        return

    blocks = list_blocks()
    if not blocks:
        for bd in DEFAULT_BLOCKS:
            create_block(bd)
        blocks = list_blocks()

    block_ids = [b["id"] for b in blocks]
    tmpl = create_template({"name": "標準空室確認", "description": "デフォルトの空室確認テンプレート"})
    set_template_blocks(tmpl["id"], block_ids)
    set_default_template(tmpl["id"])


# ── Blocks ──

def create_block(data: dict) -> dict:
    now = datetime.now().isoformat()
    bid = str(uuid.uuid4())
    conn = _get_conn()
    conn.execute(
        "INSERT INTO conversation_blocks (id, name, type, content, description, is_system, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (bid, data["name"], data.get("type", "question"), data["content"],
         data.get("description"), 1 if data.get("is_system") else 0, now, now),
    )
    conn.commit()
    conn.close()
    return get_block(bid)


def get_block(block_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM conversation_blocks WHERE id = ?", (block_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_blocks(block_type: Optional[str] = None) -> List[dict]:
    conn = _get_conn()
    if block_type:
        rows = conn.execute("SELECT * FROM conversation_blocks WHERE type = ? ORDER BY created_at", (block_type,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM conversation_blocks ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_block(block_id: str, data: dict) -> Optional[dict]:
    data["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in data)
    vals = list(data.values()) + [block_id]
    conn = _get_conn()
    conn.execute(f"UPDATE conversation_blocks SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()
    return get_block(block_id)


def delete_block(block_id: str) -> bool:
    b = get_block(block_id)
    if b and b.get("is_system"):
        return False
    conn = _get_conn()
    conn.execute("DELETE FROM template_blocks WHERE block_id = ?", (block_id,))
    conn.execute("DELETE FROM conversation_blocks WHERE id = ?", (block_id,))
    conn.commit()
    conn.close()
    return True


# ── Templates ──

def create_template(data: dict) -> dict:
    now = datetime.now().isoformat()
    tid = str(uuid.uuid4())
    conn = _get_conn()
    conn.execute(
        "INSERT INTO conversation_templates (id, name, description, created_at, updated_at) VALUES (?,?,?,?,?)",
        (tid, data["name"], data.get("description"), now, now),
    )
    conn.commit()
    conn.close()
    return get_template(tid)


def get_template(template_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM conversation_templates WHERE id = ?", (template_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_templates() -> List[dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM conversation_templates ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_template(template_id: str, data: dict) -> Optional[dict]:
    data["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in data)
    vals = list(data.values()) + [template_id]
    conn = _get_conn()
    conn.execute(f"UPDATE conversation_templates SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()
    return get_template(template_id)


def delete_template(template_id: str) -> bool:
    default_id = get_default_template_id()
    if default_id and template_id == default_id:
        return False
    conn = _get_conn()
    conn.execute("DELETE FROM template_blocks WHERE template_id = ?", (template_id,))
    conn.execute("DELETE FROM conversation_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return True


def set_default_template(template_id: str):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("default_template_id", template_id))
    conn.commit()
    conn.close()


def get_default_template_id() -> Optional[str]:
    conn = _get_conn()
    row = conn.execute("SELECT value FROM config WHERE key = 'default_template_id'").fetchone()
    conn.close()
    return row["value"] if row else None


def get_default_template() -> Optional[dict]:
    tid = get_default_template_id()
    return get_template(tid) if tid else None


# ── Template-Block ordering ──

def set_template_blocks(template_id: str, block_ids_ordered: List[str]):
    conn = _get_conn()
    conn.execute("DELETE FROM template_blocks WHERE template_id = ?", (template_id,))
    for i, bid in enumerate(block_ids_ordered):
        conn.execute(
            "INSERT INTO template_blocks (template_id, block_id, sort_order) VALUES (?,?,?)",
            (template_id, bid, i),
        )
    conn.commit()
    conn.close()


def get_template_blocks(template_id: str) -> List[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT b.*, tb.sort_order FROM conversation_blocks b "
        "JOIN template_blocks tb ON b.id = tb.block_id "
        "WHERE tb.template_id = ? ORDER BY tb.sort_order",
        (template_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Prompt generation ──

def generate_prompt(template_id: str) -> str:
    blocks = get_template_blocks(template_id)
    if not blocks:
        return ""
    return "\n\n".join(b["content"] for b in blocks)


def get_prompt_for_property(property_id: str) -> str:
    from app.database import get_property
    prop = get_property(property_id)
    if not prop:
        return ""

    tid = prop.get("template_id")
    if tid:
        prompt = generate_prompt(tid)
        if prompt:
            return prompt

    default_id = get_default_template_id()
    if default_id:
        return generate_prompt(default_id)

    return ""


# ── Import/Export ──

def export_template(template_id: str) -> dict:
    tmpl = get_template(template_id)
    if not tmpl:
        return {}
    blocks = get_template_blocks(template_id)
    return {
        "name": tmpl["name"],
        "description": tmpl.get("description", ""),
        "blocks": [
            {"name": b["name"], "type": b["type"], "content": b["content"], "sort_order": b["sort_order"]}
            for b in blocks
        ],
    }


def import_template(data: dict) -> dict:
    tmpl = create_template({"name": data["name"], "description": data.get("description", "")})
    block_ids = []
    for bd in data.get("blocks", []):
        b = create_block({"name": bd["name"], "type": bd.get("type", "question"), "content": bd["content"]})
        block_ids.append(b["id"])
    if block_ids:
        set_template_blocks(tmpl["id"], block_ids)
    return tmpl
