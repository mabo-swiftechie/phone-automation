import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services import property as property_svc

router = APIRouter(tags=["export"])


@router.get("/export/csv")
async def export_csv():
    """通話結果をCSVでエクスポートする"""
    records = await property_svc.get_call_records()

    # enrich with property names/phone numbers
    props = {}
    for r in records:
        pid = r.get("property_id")
        if pid and pid not in props:
            prop = await property_svc.get_property(pid)
            props[pid] = prop or {}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "物件ID", "物件名", "電話番号", "通話状態", "通話時間(秒)",
        "空室状況", "外国人OK", "中国人OK", "特別条件", "録音URL", "発信日時",
    ])

    for r in records:
        prop = props.get(r.get("property_id"), {})
        writer.writerow([
            r.get("id"),
            r.get("property_id"),
            prop.get("name", ""),
            prop.get("phone_number", ""),
            r.get("call_status", ""),
            r.get("duration_seconds", ""),
            r.get("vacancy_status", ""),
            r.get("foreigner_accepted", ""),
            r.get("chinese_accepted", ""),
            r.get("special_conditions", ""),
            r.get("recording_url", ""),
            r.get("called_at", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=call_results.csv"},
    )
