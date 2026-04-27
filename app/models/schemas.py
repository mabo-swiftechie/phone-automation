from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class PropertyCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone_number: str
    email_address: Optional[str] = None
    management_company: Optional[str] = None
    property_url: Optional[str] = None


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[str] = None
    management_company: Optional[str] = None
    property_url: Optional[str] = None


class CallRequest(BaseModel):
    property_id: UUID


class PropertyResponse(BaseModel):
    id: UUID
    name: str
    address: Optional[str]
    phone_number: str
    email_address: Optional[str]
    management_company: Optional[str]
    property_url: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CallResultResponse(BaseModel):
    id: UUID
    property_id: UUID
    retell_call_id: Optional[str]
    call_status: Optional[str]
    duration_seconds: Optional[int]
    recording_url: Optional[str]
    transcript: Optional[str]
    vacancy_status: Optional[str]
    foreigner_accepted: Optional[bool]
    chinese_accepted: Optional[bool]
    special_conditions: Optional[str]
    called_at: datetime

    class Config:
        from_attributes = True


class RetellWebhookPayload(BaseModel):
    call_id: str
    agent_id: str
    call_status: str
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    transcript_object: Optional[list] = None
    metadata: Optional[dict] = None
    call_analysis: Optional[dict] = None
