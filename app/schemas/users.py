"""Pydantic schemas for users and roles."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    created_at: datetime


class RoleCreate(BaseModel):
    name: str
    description: str = ""


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    role_id: Optional[int] = None
