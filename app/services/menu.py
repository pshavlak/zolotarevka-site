"""Menu CRUD service — business logic for menu item operations."""

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models import MenuItem
from app.schemas.menu import (
    MenuItemCreate,
    MenuItemTreeNode,
    MenuItemUpdate,
    ReorderItem,
)


def get_menu_item(db: Session, item_id: int) -> Optional[MenuItem]:
    return db.get(MenuItem, item_id)


def get_menu_items(db: Session) -> list[MenuItem]:
    return list(
        db.execute(
            select(MenuItem).order_by(MenuItem.order)
        ).scalars().all()
    )


def create_menu_item(db: Session, data: MenuItemCreate) -> MenuItem:
    item = MenuItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_menu_item(db: Session, item_id: int, data: MenuItemUpdate) -> Optional[MenuItem]:
    item = db.get(MenuItem, item_id)
    if item is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_menu_item(db: Session, item_id: int) -> bool:
    item = db.get(MenuItem, item_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def reorder_menu_items(db: Session, reorder_list: list[ReorderItem]) -> list[MenuItem]:
    """Update order and/or parent_id for multiple items in one batch."""
    for entry in reorder_list:
        db.execute(
            update(MenuItem)
            .where(MenuItem.id == entry.id)
            .values(order=entry.order, parent_id=entry.parent_id)
        )
    db.commit()

    return list(
        db.execute(
            select(MenuItem).order_by(MenuItem.order)
        ).scalars().all()
    )


def _build_tree(
    items: list[MenuItem],
    parent_id: Optional[int] = None,
    active_only: bool = False,
) -> list[MenuItemTreeNode]:
    """Recursively build a tree from a flat list of menu items."""
    nodes: list[MenuItemTreeNode] = []
    for item in items:
        if item.parent_id != parent_id:
            continue
        if active_only and not item.is_active:
            continue

        node = MenuItemTreeNode(
            id=item.id,
            title=item.title,
            url=item.url,
            parent_id=item.parent_id,
            order=item.order,
            is_active=item.is_active,
            type=item.type,
            children=_build_tree(items, item.id, active_only),
        )
        nodes.append(node)
    return nodes


def get_menu_tree(
    db: Session,
    active_only: bool = False,
) -> list[MenuItemTreeNode]:
    """Get the full menu as a nested tree."""
    items = list(
        db.execute(
            select(MenuItem).order_by(MenuItem.order)
        ).scalars().all()
    )
    return _build_tree(items, parent_id=None, active_only=active_only)


def get_active_menu_tree(db: Session) -> list[MenuItemTreeNode]:
    """Convenience: get tree with only active items."""
    return get_menu_tree(db, active_only=True)
