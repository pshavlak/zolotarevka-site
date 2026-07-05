"""Page CRUD service — business logic for page operations."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Page
from app.schemas.page import PageCreate, PageUpdate, ReorderPage


def _slug_exists(db: Session, slug: str, exclude_id: Optional[int] = None) -> bool:
    """Check if a slug already exists (optionally excluding a given page id)."""
    query = select(Page).where(Page.slug == slug)
    if exclude_id is not None:
        query = query.where(Page.id != exclude_id)
    return db.execute(query).scalar_one_or_none() is not None


def get_page(db: Session, page_id: int) -> Optional[Page]:
    return db.get(Page, page_id)


def get_pages(db: Session) -> list[Page]:
    return list(
        db.execute(
            select(Page).order_by(Page.order, Page.title)
        ).scalars().all()
    )


def create_page(db: Session, data: PageCreate) -> Page:
    if _slug_exists(db, data.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Page with slug '{data.slug}' already exists",
        )
    page = Page(**data.model_dump())
    db.add(page)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Page with slug '{data.slug}' already exists",
        )
    db.refresh(page)
    return page


def update_page(db: Session, page_id: int, data: PageUpdate) -> Optional[Page]:
    page = db.get(Page, page_id)
    if page is None:
        return None

    # Check slug uniqueness if slug is being updated
    if data.slug is not None and data.slug != page.slug:
        if _slug_exists(db, data.slug, exclude_id=page_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Page with slug '{data.slug}' already exists",
            )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Page with slug '{data.slug}' already exists",
        )
    db.refresh(page)
    return page


def delete_page(db: Session, page_id: int) -> bool:
    page = db.get(Page, page_id)
    if page is None:
        return False
    db.delete(page)
    db.commit()
    return True


def reorder_pages(db: Session, reorder_list: list[ReorderPage]) -> list[Page]:
    """Update order for multiple pages in one batch."""
    for entry in reorder_list:
        db.execute(
            update(Page)
            .where(Page.id == entry.id)
            .values(order=entry.order)
        )
    db.commit()

    return list(
        db.execute(
            select(Page).order_by(Page.order, Page.title)
        ).scalars().all()
    )
