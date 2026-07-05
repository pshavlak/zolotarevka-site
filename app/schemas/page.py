"""Pydantic schemas for pages."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PageBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    content: str = ""
    is_published: bool = True
    order: int = 0


class PageCreate(PageBase):
    pass


class PageUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    content: Optional[str] = None
    is_published: Optional[bool] = None
    order: Optional[int] = None


class PageResponse(PageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReorderPage(BaseModel):
    id: int
    order: int
