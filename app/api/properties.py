from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.models.schemas import PropertyCreate, PropertyUpdate, PropertyResponse
from app.services import property as property_svc

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyResponse)
async def create_property(body: PropertyCreate):
    data = body.model_dump()
    row = await property_svc.create_property(data)
    return row


@router.get("", response_model=List[PropertyResponse])
async def list_properties(status: Optional[str] = None):
    return await property_svc.get_properties(status)


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: UUID):
    row = await property_svc.get_property(property_id)
    if not row:
        raise HTTPException(404, "Property not found")
    return row


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(property_id: UUID, body: PropertyUpdate):
    data = body.model_dump(exclude_unset=True)
    row = await property_svc.update_property(property_id, data)
    if not row:
        raise HTTPException(404, "Property not found")
    return row
