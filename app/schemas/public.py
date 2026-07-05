from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PublicMenuItem(BaseModel):
    """A single menu item in the public API response."""
    id: int
    title: str
    url: str
    type: str
    children: List[PublicMenuItem] = []
