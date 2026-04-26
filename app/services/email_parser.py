from __future__ import annotations
import json
from typing import Optional
from openai import OpenAI
from app.config_manager import load_config


def parse_email_response(
    original_email: str,
    reply_text: str,
    property_name: str,
) -> dict:
    """返信メールをAIで解析し、構造化データを抽出する"""
    cfg = load_config()
    api_key = cfg.get("openai_api_key")
    if not api_key:
        raise ValueError("OpenAI API Keyが未設定です")

    client = OpenAI(api_key=api_key)

    prompt = f"""以下は、物件「{property_name}」の空室確認メールに対する返信です。
返信内容から以下の情報を抽出してください。

抽出項目:
1. vacancy_status: 空室状況 → "available"（空室あり）/ "unavailable"（満室）/ "unclear"（不明）
2. foreigner_accepted: 外国人入居可否 → "yes" / "no" / "unclear"
3. chinese_accepted: 中国人入居可否 → "yes" / "no" / "unclear"
4. special_conditions: 特別条件（敷金・礼金・保証会社等）
5. monthly_rent: 月額賃料
6. move_in_date: 入居可能日
7. summary: 日本語で1-2文のまとめ

送信したメール:
{original_email}

返信内容:
{reply_text}

以下のJSON形式で出力してください:
{{
  "vacancy_status": "",
  "foreigner_accepted": "",
  "chinese_accepted": "",
  "special_conditions": "",
  "monthly_rent": "",
  "move_in_date": "",
  "summary": ""
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    text = response.choices[0].message.content.strip()
    # JSONブロックを抽出
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"summary": text, "vacancy_status": "unclear"}
