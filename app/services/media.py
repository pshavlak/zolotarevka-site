"""Service layer for media items, settings, and suggestions."""

import os
import uuid
import shutil
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.models import MediaItem, Setting, Suggestion


# ── Media ─────────────────────────────────────────────────────────────────

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_media_items(db: Session) -> List[MediaItem]:
    return db.query(MediaItem).order_by(MediaItem.created_at.desc()).all()


def get_media_item(db: Session, item_id: int) -> Optional[MediaItem]:
    return db.query(MediaItem).filter(MediaItem.id == item_id).first()


def upload_media(db: Session, file: UploadFile, alt_text: str = "") -> MediaItem:
    _ensure_upload_dir()
    ext = os.path.splitext(file.filename or "file")[1] or ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    contents = file.file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    media = MediaItem(
        filename=unique_name,
        original_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        alt_text=alt_text,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def update_media(db: Session, item_id: int, alt_text: str) -> Optional[MediaItem]:
    media = get_media_item(db, item_id)
    if not media:
        return None
    media.alt_text = alt_text
    db.commit()
    db.refresh(media)
    return media


def delete_media(db: Session, item_id: int) -> bool:
    media = get_media_item(db, item_id)
    if not media:
        return False
    file_path = os.path.join(UPLOAD_DIR, media.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(media)
    db.commit()
    return True


# ── Settings ──────────────────────────────────────────────────────────────

def get_settings(db: Session) -> List[Setting]:
    return db.query(Setting).order_by(Setting.key).all()


def get_setting(db: Session, key: str) -> Optional[Setting]:
    return db.query(Setting).filter(Setting.key == key).first()


def upsert_setting(db: Session, key: str, value: str) -> Setting:
    setting = get_setting(db, key)
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def delete_setting(db: Session, key: str) -> bool:
    """Delete a setting by key. Returns True if deleted, False if not found."""
    setting = get_setting(db, key)
    if not setting:
        return False
    db.delete(setting)
    db.commit()
    return True


# ── Suggestions ───────────────────────────────────────────────────────────

def get_suggestions(db: Session) -> List[Suggestion]:
    return db.query(Suggestion).order_by(Suggestion.created_at.desc()).all()


def create_suggestion(db: Session, content: str, author_name: str = "", author_contact: str = "") -> Suggestion:
    sug = Suggestion(content=content, author_name=author_name, author_contact=author_contact)
    db.add(sug)
    db.commit()
    db.refresh(sug)
    return sug


def mark_suggestion_read(db: Session, sug_id: int) -> Optional[Suggestion]:
    sug = db.query(Suggestion).filter(Suggestion.id == sug_id).first()
    if not sug:
        return None
    sug.is_read = True
    db.commit()
    db.refresh(sug)
    return sug
