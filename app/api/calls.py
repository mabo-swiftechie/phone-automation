from __future__ import annotations
import asyncio
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import CallRequest, CallResultResponse
from app.services import property as property_svc
from app.services import retell as retell_svc
from app.services import line_notify

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/trigger")
async def trigger_call(body: CallRequest):
    """物件に対して電話を発信する"""
    prop = await property_svc.get_property(body.property_id)
    if not prop:
        raise HTTPException(404, "Property not found")
    if prop["status"] not in ("pending", "retry"):
        raise HTTPException(400, f"Property status is '{prop['status']}', cannot call")

    result = await asyncio.to_thread(
        retell_svc.create_phone_call,
        phone_number=prop["phone_number"],
        property_name=prop["name"],
        property_id=str(body.property_id),
    )

    await property_svc.update_property(body.property_id, {"status": "calling"})
    await property_svc.create_call_record({
        "property_id": str(body.property_id),
        "retell_call_id": result.get("call_id"),
        "call_status": "initiated",
    })

    return {"call_id": result.get("call_id"), "status": "initiated"}


@router.get("/{property_id}", response_model=List[CallResultResponse])
async def get_call_records(property_id: UUID):
    return await property_svc.get_call_records(property_id)


@router.post("/webhook")
async def retell_webhook(payload: dict, background_tasks: BackgroundTasks):
    """Retell AIからの通話完了Webhookを受信する"""
    call_id = payload.get("call_id")
    call_status = payload.get("call_status", "unknown")

    analysis = payload.get("call_analysis", {}) or {}

    update_data = {
        "call_status": call_status,
        "duration_seconds": payload.get("duration_seconds"),
        "recording_url": payload.get("recording_url"),
        "transcript": payload.get("transcript"),
    }

    if analysis:
        structured = analysis.get("call_summary") or analysis.get("custom_analysis_data", {})
        if isinstance(structured, dict):
            update_data["vacancy_status"] = structured.get("vacancy_status")
            update_data["foreigner_accepted"] = structured.get("foreigner_accepted")
            update_data["chinese_accepted"] = structured.get("chinese_accepted")
            update_data["special_conditions"] = structured.get("special_conditions")

    await property_svc.update_call_record(call_id, update_data)

    background_tasks.add_task(_post_call_notify, call_id, update_data)

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
