"""Tests for the menu CRUD service layer — business logic."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, ReorderItem
from app.services.menu import (
    create_menu_item,
    delete_menu_item,
    get_menu_item,
    get_menu_items,
    get_menu_tree,
    reorder_menu_items,
    update_menu_item,
)


class TestCreate:
    def test_create_root_item(self, db_session: Session) -> None:
        data = MenuItemCreate(title="Главная", url="/")
        item = create_menu_item(db_session, data)

        assert item.id is not None
        assert item.title == "Главная"
        assert item.url == "/"
        assert item.parent_id is None

    def test_create_child_item(self, db_session: Session) -> None:
        parent = MenuItem(title="Школа")
        db_session.add(parent)
        db_session.flush()

        data = MenuItemCreate(
            title="Новости школы",
            parent_id=parent.id,
        )
        child = create_menu_item(db_session, data)

        assert child.parent_id == parent.id
        assert child.title == "Новости школы"

    def test_create_inactive_by_default(self, db_session: Session) -> None:
        item = create_menu_item(db_session, MenuItemCreate(title="Черновик", is_active=False))
        assert item.is_active is False

    def test_create_with_explicit_order(self, db_session: Session) -> None:
        item = create_menu_item(db_session, MenuItemCreate(title="Z", order=99))
        assert item.order == 99


class TestRead:
    def test_get_by_id(self, db_session: Session) -> None:
        created = create_menu_item(db_session, MenuItemCreate(title="Найти меня"))
        found = get_menu_item(db_session, created.id)

        assert found is not None
        assert found.title == "Найти меня"

    def test_get_nonexistent_returns_none(self, db_session: Session) -> None:
        assert get_menu_item(db_session, 9999) is None

    def test_list_all_items(self, db_session: Session) -> None:
        create_menu_item(db_session, MenuItemCreate(title="A"))
        create_menu_item(db_session, MenuItemCreate(title="B"))
        items = get_menu_items(db_session)

        assert len(items) == 2

    def test_list_empty(self, db_session: Session) -> None:
        assert get_menu_items(db_session) == []


class TestUpdate:
    def test_update_title(self, db_session: Session) -> None:
        item = create_menu_item(db_session, MenuItemCreate(title="Старое"))
        updated = update_menu_item(db_session, item.id, MenuItemUpdate(title="Новое"))

        assert updated is not None
        assert updated.title == "Новое"

    def test_update_url(self, db_session: Session) -> None:
        item = create_menu_item(db_session, MenuItemCreate(title="X"))
        updated = update_menu_item(db_session, item.id, MenuItemUpdate(url="/new-path"))

        assert updated is not None
        assert updated.url == "/new-path"

    def test_update_partial_keeps_other_fields(self, db_session: Session) -> None:
        item = create_menu_item(
            db_session,
            MenuItemCreate(title="Тест", url="/test", order=5, is_active=False),
        )
        updated = update_menu_item(
            db_session, item.id, MenuItemUpdate(title="Изменён")
        )

        assert updated is not None
        assert updated.title == "Изменён"
        assert updated.url == "/test"
        assert updated.order == 5
        assert updated.is_active is False

    def test_toggle_active(self, db_session: Session) -> None:
        item = create_menu_item(db_session, MenuItemCreate(title="T"))
        update_menu_item(db_session, item.id, MenuItemUpdate(is_active=False))
        updated = get_menu_item(db_session, item.id)
        assert updated is not None and updated.is_active is False

        update_menu_item(db_session, item.id, MenuItemUpdate(is_active=True))
        updated = get_menu_item(db_session, item.id)
        assert updated is not None and updated.is_active is True

    def test_update_nonexistent_returns_none(self, db_session: Session) -> None:
        result = update_menu_item(db_session, 9999, MenuItemUpdate(title="X"))
        assert result is None


class TestDelete:
    def test_delete_existing(self, db_session: Session) -> None:
        item = create_menu_item(db_session, MenuItemCreate(title="Удалить"))
        assert delete_menu_item(db_session, item.id) is True
        assert get_menu_item(db_session, item.id) is None

    def test_delete_nonexistent_returns_false(self, db_session: Session) -> None:
        assert delete_menu_item(db_session, 9999) is False

    def test_delete_cascades_to_children(self, db_session: Session) -> None:
        parent = create_menu_item(db_session, MenuItemCreate(title="Родитель"))
        create_menu_item(db_session, MenuItemCreate(title="Ребёнок", parent_id=parent.id))

        delete_menu_item(db_session, parent.id)

        remaining = db_session.execute(select(MenuItem)).scalars().all()
        assert len(remaining) == 0


class TestReorder:
    def test_reorder_siblings(self, db_session: Session) -> None:
        a = create_menu_item(db_session, MenuItemCreate(title="A", order=0))
        b = create_menu_item(db_session, MenuItemCreate(title="B", order=1))

        reorder_menu_items(db_session, [
            ReorderItem(id=a.id, order=1, parent_id=None),
            ReorderItem(id=b.id, order=0, parent_id=None),
        ])

        items = sorted(
            db_session.execute(select(MenuItem)).scalars().all(),
            key=lambda x: x.order,
        )
        assert items[0].title == "B"
        assert items[1].title == "A"

    def test_reorder_changes_parent(self, db_session: Session) -> None:
        a = create_menu_item(db_session, MenuItemCreate(title="A"))
        b = create_menu_item(db_session, MenuItemCreate(title="B"))

        reorder_menu_items(db_session, [
            ReorderItem(id=a.id, order=0, parent_id=None),
            ReorderItem(id=b.id, order=0, parent_id=a.id),
        ])

        b_refreshed = get_menu_item(db_session, b.id)
        assert b_refreshed is not None
        assert b_refreshed.parent_id == a.id


class TestMenuTree:
    def test_flat_tree_no_parents(self, db_session: Session) -> None:
        for name in ["A", "B", "C"]:
            create_menu_item(db_session, MenuItemCreate(title=name, order=0))

        tree = get_menu_tree(db_session)
        assert len(tree) == 3
        assert [n.title for n in tree] == ["A", "B", "C"]

    def test_nested_tree(self, db_session: Session) -> None:
        parent = create_menu_item(db_session, MenuItemCreate(title="Родитель"))
        child = create_menu_item(
            db_session, MenuItemCreate(title="Ребёнок", parent_id=parent.id)
        )

        tree = get_menu_tree(db_session)
        assert len(tree) == 1
        assert tree[0].title == "Родитель"
        assert len(tree[0].children) == 1
        assert tree[0].children[0].title == "Ребёнок"

    def test_active_tree_excludes_inactive(self, db_session: Session) -> None:
        create_menu_item(db_session, MenuItemCreate(title="Видимый", is_active=True))
        create_menu_item(db_session, MenuItemCreate(title="Скрытый", is_active=False))

        full_tree = get_menu_tree(db_session, active_only=False)
        assert len(full_tree) == 2

        active_tree = get_menu_tree(db_session, active_only=True)
        assert len(active_tree) == 1
        assert active_tree[0].title == "Видимый"

    def test_active_tree_excludes_inactive_with_children(
        self, db_session: Session
    ) -> None:
        parent = create_menu_item(
            db_session, MenuItemCreate(title="Активный родитель")
        )
        create_menu_item(
            db_session, MenuItemCreate(title="Активный ребёнок", parent_id=parent.id)
        )

        inactive_parent = create_menu_item(
            db_session, MenuItemCreate(title="Неактивный родитель", is_active=False)
        )
        create_menu_item(
            db_session,
            MenuItemCreate(
                title="Ребёнок неактивного",
                parent_id=inactive_parent.id,
            ),
        )

        active_tree = get_menu_tree(db_session, active_only=True)
        assert len(active_tree) == 1
        assert active_tree[0].title == "Активный родитель"
        assert len(active_tree[0].children) == 1

    def test_deeply_nested_tree(self, db_session: Session) -> None:
        l1 = create_menu_item(db_session, MenuItemCreate(title="L1"))
        l2 = create_menu_item(db_session, MenuItemCreate(title="L2", parent_id=l1.id))
        l3 = create_menu_item(db_session, MenuItemCreate(title="L3", parent_id=l2.id))

        tree = get_menu_tree(db_session)
        assert tree[0].children[0].children[0].title == "L3"

    def test_tree_ordered_by_order_field(self, db_session: Session) -> None:
        parent = create_menu_item(db_session, MenuItemCreate(title="P"))
        c2 = create_menu_item(
            db_session, MenuItemCreate(title="B", parent_id=parent.id, order=1)
        )
        c1 = create_menu_item(
            db_session, MenuItemCreate(title="A", parent_id=parent.id, order=0)
        )

        tree = get_menu_tree(db_session)
        assert [c.title for c in tree[0].children] == ["A", "B"]
