from __future__ import annotations
import asyncio
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.models.schemas import CallRequest, CallResultResponse
from app.services import property as property_svc
from app.services.voice_provider import get_voice_provider, is_feature_enabled, VoiceProvider
from app.services import line_notify
from app.config_manager import load_config

router = APIRouter(prefix="/calls", tags=["calls"])

_provider: Optional[VoiceProvider] = None


def _get_provider() -> VoiceProvider:
    global _provider
    if _provider is None:
        _provider = get_voice_provider()
    return _provider


def reset_provider():
    """Clear cached provider so next call picks up config changes."""
    global _provider
    _provider = None


class BatchCallRequest(BaseModel):
    property_ids: List[UUID]
    mode: str = "default"

    def validate_count(self):
        if len(self.property_ids) > 50:
            raise HTTPException(400, "バッチ通話は最大50件までです")


@router.post("/trigger")
async def trigger_call(body: CallRequest):
    """物件に対して電話を発信する"""
    prop = await property_svc.get_property(body.property_id)
    if not prop:
        raise HTTPException(404, "Property not found")
    if prop["status"] not in ("pending", "retry"):
        raise HTTPException(400, f"Property status is '{prop['status']}', cannot call")

    provider = _get_provider()
    mode = getattr(body, "mode", "default")
    result = await asyncio.to_thread(
        provider.create_call,
        phone_number=prop["phone_number"],
        property_name=prop["name"],
        property_id=str(body.property_id),
        mode=mode,
    )

    await property_svc.update_property(body.property_id, {"status": "calling"})
    await property_svc.create_call_record({
        "property_id": str(body.property_id),
        "retell_call_id": result.call_id,
        "call_status": "initiated",
    })

    return {"call_id": result.call_id, "status": "initiated"}


@router.post("/batch-trigger")
async def trigger_batch_calls(body: BatchCallRequest):
    """複数物件にバッチ電話を発信する（Tier 3のみ）"""
    cfg = load_config()
    if not is_feature_enabled(cfg, "batch_call"):
        raise HTTPException(403, "バッチ通話は Full Tier でのみ利用可能です")

    provider = _get_provider()
    if not provider.supports_batch:
        raise HTTPException(400, "現在のプロバイダーはバッチ通話をサポートしていません")

    body.validate_count()
    results = []
    for prop_id in body.property_ids:
        prop = await property_svc.get_property(prop_id)
        if not prop or prop["status"] not in ("pending", "retry"):
            results.append({"property_id": str(prop_id), "status": "skipped"})
            continue
        try:
            result = await asyncio.to_thread(
                provider.create_call,
                phone_number=prop["phone_number"],
                property_name=prop["name"],
                property_id=str(prop_id),
                mode=body.mode,
            )
            await property_svc.update_property(prop_id, {"status": "calling"})
            await property_svc.create_call_record({
                "property_id": str(prop_id),
                "retell_call_id": result.call_id,
                "call_status": "initiated",
            })
            results.append({"property_id": str(prop_id), "call_id": result.call_id, "status": "initiated"})
        except Exception as e:
            results.append({"property_id": str(prop_id), "status": "error", "detail": str(e)})
        await asyncio.sleep(2)

    return {"results": results}


@router.get("/{property_id}", response_model=List[CallResultResponse])
async def get_call_records(property_id: UUID):
    return await property_svc.get_call_records(property_id)


@router.post("/webhook")
@router.post("/webhook/retell")
async def retell_webhook(payload: dict, background_tasks: BackgroundTasks):
    """Voice Providerからの通話完了Webhookを受信する"""
    provider = _get_provider()
    result = provider.parse_webhook(payload)

    update_data = {
        "call_status": result.call_status,
        "duration_seconds": result.duration_seconds,
        "recording_url": result.recording_url,
        "transcript": result.transcript,
    }

    if result.vacancy_status is not None:
        update_data["vacancy_status"] = result.vacancy_status
    if result.foreigner_accepted is not None:
        update_data["foreigner_accepted"] = result.foreigner_accepted
    if result.chinese_accepted is not None:
        update_data["chinese_accepted"] = result.chinese_accepted
    if result.special_conditions is not None:
        update_data["special_conditions"] = result.special_conditions

    await property_svc.update_call_record(result.call_id, update_data)

    background_tasks.add_task(_post_call_notify, result.call_id, update_data)

    return {"status": "ok"}


async def _post_call_notify(call_id: str, data: dict):
    """通話完了後にLINE通知を送る"""
    records = await property_svc.get_call_records()
    record = next((r for r in records if r.get("retell_call_id") == call_id), None)
    if not record:
        return

    prop = await property_svc.get_property(record["property_id"])
    prop_name = prop["name"] if prop else "不明"

    if data.get("call_status") in ("ended", "completed"):
        new_status = "completed"
    else:
        new_status = "failed"

    if prop:
        await property_svc.update_property(record["property_id"], {"status": new_status})

    await line_notify.send_call_result_message(prop_name, data)
