"""FastAPI router for menu CRUD operations."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.menu import (
    MenuItemCreate,
    MenuItemResponse,
    MenuItemTreeNode,
    MenuItemUpdate,
    ReorderItem,
)
from app.services.menu import (
    create_menu_item,
    delete_menu_item,
    get_menu_item,
    get_menu_items,
    get_menu_tree,
    reorder_menu_items,
    update_menu_item,
)

router = APIRouter(prefix="/menu", tags=["menu"])


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
def api_create_menu_item(data: MenuItemCreate, db: Session = Depends(get_db)):
    return create_menu_item(db, data)


@router.get("/items", response_model=List[MenuItemResponse])
def api_list_menu_items(db: Session = Depends(get_db)):
    return get_menu_items(db)


@router.get("/items/{item_id}", response_model=MenuItemResponse)
def api_get_menu_item(item_id: int, db: Session = Depends(get_db)):
    item = get_menu_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.put("/items/{item_id}", response_model=MenuItemResponse)
def api_update_menu_item(item_id: int, data: MenuItemUpdate, db: Session = Depends(get_db)):
    item = update_menu_item(db, item_id, data)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    if not delete_menu_item(db, item_id):
        raise HTTPException(status_code=404, detail="Menu item not found")


@router.put("/reorder", response_model=List[MenuItemResponse])
def api_reorder_menu_items(reorder_list: List[ReorderItem], db: Session = Depends(get_db)):
    return reorder_menu_items(db, reorder_list)


@router.get("/tree", response_model=List[MenuItemTreeNode])
def api_menu_tree(active_only: bool = False, db: Session = Depends(get_db)):
    return get_menu_tree(db, active_only=active_only)
