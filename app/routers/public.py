from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models import MenuItem
from app.schemas.public import PublicMenuItem

router = APIRouter(prefix="/api", tags=["public"])


def _build_public_tree(items: List[MenuItem]) -> List[PublicMenuItem]:
    """Convert a flat list of active MenuItems into a nested public tree."""
    item_map: dict[int, PublicMenuItem] = {}
    roots: List[PublicMenuItem] = []

    for item in items:
        item_map[item.id] = PublicMenuItem(
            id=item.id,
            title=item.title,
            url=item.url or f"/{item.type}/{item.id}" if item.type != "page" else f"/{item.id}",
            type=item.type,
            children=[],
        )

    for item in items:
        out = item_map[item.id]
        if item.parent_id and item.parent_id in item_map:
            item_map[item.parent_id].children.append(out)
        else:
            roots.append(out)

    def _sort_tree(node: PublicMenuItem) -> None:
        node.children.sort(key=lambda c: c.title)
        for child in node.children:
            _sort_tree(child)

    roots.sort(key=lambda r: r.title)
    for root in roots:
        _sort_tree(root)

    return roots


@router.get("/menu", response_model=List[PublicMenuItem])
def public_menu(db: Session = Depends(get_db)):
    """
    Return the active menu tree for the public site.
    Only items with is_active=True are included.
    """
    stmt = (
        select(MenuItem)
        .where(MenuItem.is_active == True)
        .order_by(MenuItem.order)
    )
    items = db.scalars(stmt).all()
    return _build_public_tree(items)
