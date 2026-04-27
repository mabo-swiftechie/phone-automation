import httpx
from app.config.settings import get_settings


async def send_call_result_message(
    property_name: str,
    result: dict,
) -> bool:
    """LINE Notifyで通話結果を送信する"""
    settings = get_settings()
    if not settings.line_channel_access_token or not settings.line_user_id:
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
        "Authorization": f"Bearer {settings.line_channel_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": settings.line_user_id,
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
