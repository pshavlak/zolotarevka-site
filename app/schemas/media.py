"""Pydantic schemas for media items, settings, and suggestions."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Media ─────────────────────────────────────────────────────────────────

class MediaItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_name: str
    mime_type: str
    size_bytes: int
    alt_text: str
    created_at: datetime


class MediaItemUpdate(BaseModel):
    alt_text: Optional[str] = None


# ── Settings ──────────────────────────────────────────────────────────────

class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str
    updated_at: datetime


class SettingUpdate(BaseModel):
    value: str


# ── Suggestions ───────────────────────────────────────────────────────────

class SuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    author_name: str
    author_contact: str
    is_read: bool
    created_at: datetime


class SuggestionCreate(BaseModel):
    content: str
    author_name: str = ""
    author_contact: str = ""
