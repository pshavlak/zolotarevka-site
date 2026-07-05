"""Pydantic schemas for menu items."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MenuItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    url: str = ""
    parent_id: Optional[int] = None
    order: int = 0
    is_active: bool = True
    type: str = "page"


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    parent_id: Optional[int] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    type: Optional[str] = None


class MenuItemResponse(MenuItemBase):
    id: int

    class Config:
        from_attributes = True


class MenuItemTreeNode(MenuItemResponse):
    """Menu item with children nested."""
    children: list[MenuItemTreeNode] = []


class ReorderItem(BaseModel):
    id: int
    parent_id: Optional[int] = None
    order: int
