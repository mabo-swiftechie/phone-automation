from __future__ import annotations
from typing import Optional, List
from uuid import UUID
import app.database as db


async def create_property(data: dict) -> dict:
    return db.create_property(data)


async def get_properties(status: Optional[str] = None) -> List[dict]:
    return db.list_properties(status)


async def get_property(property_id: UUID) -> Optional[dict]:
    return db.get_property(str(property_id))


async def update_property(property_id: UUID, data: dict) -> Optional[dict]:
    return db.update_property(str(property_id), data)


async def create_call_record(data: dict) -> dict:
    return db.create_call_record(data)


async def update_call_record(call_id: str, data: dict) -> Optional[dict]:
    return db.update_call_record_by_retell_id(call_id, data)


async def get_call_records(property_id: Optional[UUID] = None) -> List[dict]:
    return db.list_call_records(str(property_id) if property_id else None)
