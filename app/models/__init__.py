from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False, default="")
    parent_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    type = Column(String(50), nullable=False, default="page")

    parent = relationship(
        "MenuItem",
        back_populates="children",
        remote_side=[id],
        uselist=False,
    )

    children = relationship(
        "MenuItem",
        back_populates="parent",
        order_by="MenuItem.order",
        cascade="all, delete",
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False, default="")
    is_published = Column(Boolean, nullable=False, default=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class MediaItem(Base):
    """Uploaded media file (images, documents, etc.)."""
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    original_name = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False, default="application/octet-stream")
    size_bytes = Column(Integer, nullable=False, default=0)
    alt_text = Column(String(512), nullable=False, default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Setting(Base):
    """Key-value settings store."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Suggestion(Base):
    """User-submitted suggestions."""
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=False, default="")
    author_contact = Column(String(512), nullable=False, default="")
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
