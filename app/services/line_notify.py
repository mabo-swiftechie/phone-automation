from __future__ import annotations
import httpx
from app.config_manager import load_config


async def send_call_result_message(
    property_name: str,
    result: dict,
) -> bool:
    """LINE Notifyで通話結果を送信する"""
    cfg = load_config()
    token = cfg.get("line_channel_access_token", "")
    user_id = cfg.get("line_user_id", "")
    if not token or not user_id:
        return False

    vacancy = result.get("vacancy_status", "不明")
    foreigner = "可" if result.get("foreigner_accepted") else "不可"
    chinese = "可" if result.get("chinese_accepted") else "不可"
    conditions = result.get("special_conditions", "なし")

    text = (
        f"【通話結果通知】\n"
        f"物件名: {property_name}\n"
        f"空室状況: {vacancy}\n"
        f"外国人入居: {foreigner}\n"
        f"中国人入居: {chinese}\n"
        f"特別条件: {conditions}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            json=payload,
            timeout=10,
        )
        return resp.status_code == 200
