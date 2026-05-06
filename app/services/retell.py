from __future__ import annotations
import httpx
from app.config_manager import load_config
from app.services.template_manager import get_prompt_for_property

"""
DEPRECATED: This module is retained for backward compatibility only.
Use app.services.voice_provider instead:
    from app.services.voice_provider import get_voice_provider
    provider = get_voice_provider()
    result = provider.create_call(...)
"""

CALL_BASE = "https://api.retellai.com/v2"


def _to_e164(number: str) -> str:
    n = number.replace("-", "").replace(" ", "")
    if n.startswith("0"):
        n = "+81" + n[1:]
    elif not n.startswith("+"):
        n = "+" + n
    return n


def create_phone_call(
    phone_number: str,
    property_name: str,
    property_id: str,
) -> dict:
    cfg = load_config()

    headers = {
        "Authorization": f"Bearer {cfg['retell_api_key']}",
        "Content-Type": "application/json",
    }

    prompt = get_prompt_for_property(property_id)

    payload = {
        "agent_id": cfg["retell_agent_id"],
        "to": _to_e164(phone_number),
        "metadata": {
            "property_id": property_id,
            "property_name": property_name,
        },
        "retell_llm_dynamic_variables": {
            "property_name": property_name,
            "conversation_template": prompt,
        },
    }

    with httpx.Client() as client:
        resp = client.post(
            f"{CALL_BASE}/create-phone-call",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def create_web_call(
    property_name: str,
    property_id: str,
) -> dict:
    cfg = load_config()

    headers = {
        "Authorization": f"Bearer {cfg['retell_api_key']}",
        "Content-Type": "application/json",
    }

    prompt = get_prompt_for_property(property_id)

    payload = {
        "agent_id": cfg["retell_agent_id"],
        "metadata": {
            "property_id": property_id,
            "property_name": property_name,
        },
        "retell_llm_dynamic_variables": {
            "property_name": property_name,
            "conversation_template": prompt,
        },
    }

    with httpx.Client() as client:
        resp = client.post(
            f"{CALL_BASE}/create-web-call",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def get_call(call_id: str) -> dict:
    cfg = load_config()
    headers = {"Authorization": f"Bearer {cfg['retell_api_key']}"}

    with httpx.Client() as client:
        resp = client.get(
            f"{CALL_BASE}/get-call/{call_id}",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
