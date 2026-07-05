"""Tests for the MenuItem SQLAlchemy model — data layer behaviour."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem


class TestMenuItemCreate:
    """Creating menu items with various configurations."""

    def test_create_root_item_with_defaults(self, db_session: Session) -> None:
        item = MenuItem(title="Главная")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.id is not None
        assert item.title == "Главная"
        assert item.url == ""
        assert item.parent_id is None
        assert item.order == 0
        assert item.is_active is True
        assert item.type == "page"

    def test_create_root_item_with_all_fields(self, db_session: Session) -> None:
        item = MenuItem(
            title="Школа",
            url="/school",
            order=1,
            is_active=True,
            type="page",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.title == "Школа"
        assert item.url == "/school"
        assert item.order == 1
        assert item.is_active is True
        assert item.type == "page"

    def test_create_inactive_item(self, db_session: Session) -> None:
        item = MenuItem(title="Черновик", is_active=False)
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.is_active is False

    def test_create_item_with_custom_type(self, db_session: Session) -> None:
        item = MenuItem(title="ВКонтакте", type="external_link", url="https://vk.com/")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.type == "external_link"
        assert item.url == "https://vk.com/"

    def test_persisted_values_are_retrievable(self, db_session: Session) -> None:
        db_session.add(MenuItem(title="Спорт", url="/sports", order=5, is_active=True))
        db_session.commit()

        retrieved = db_session.execute(
            select(MenuItem).where(MenuItem.title == "Спорт")
        ).scalar_one()

        assert retrieved.url == "/sports"
        assert retrieved.order == 5


class TestMenuItemHierarchy:
    """Parent-child relationships and tree traversal."""

    def test_create_child_item(self, db_session: Session) -> None:
        parent = MenuItem(title="Школа")
        child = MenuItem(title="Новости школы", parent_id=0)  # placeholder
        db_session.add(parent)
        db_session.flush()

        child.parent_id = parent.id
        db_session.add(child)
        db_session.commit()
        db_session.refresh(parent)
        db_session.refresh(child)

        assert child.parent_id == parent.id
        assert child in parent.children

    def test_parent_relationship_navigation(self, db_session: Session) -> None:
        parent = MenuItem(title="Жизнь села")
        child = MenuItem(title="Фотогалерея")
        db_session.add_all([parent, child])
        db_session.flush()
        child.parent_id = parent.id
        db_session.commit()
        db_session.refresh(child)

        assert child.parent is not None
        assert child.parent.title == "Жизнь села"

    def test_children_ordered_by_order_field(self, db_session: Session) -> None:
        parent = MenuItem(title="Медиа")
        db_session.add(parent)
        db_session.flush()

        for i, name in enumerate(["Фото", "Видео", "Документы"]):
            db_session.add(MenuItem(title=name, parent_id=parent.id, order=i))
        db_session.commit()
        db_session.refresh(parent)

        titles = [c.title for c in parent.children]
        assert titles == ["Фото", "Видео", "Документы"]

    def test_deep_hierarchy(self, db_session: Session) -> None:
        """Three levels of nesting: root → section → subsection."""
        l1 = MenuItem(title="Услуги")
        db_session.add(l1)
        db_session.flush()

        l2 = MenuItem(title="Образование", parent_id=l1.id)
        db_session.add(l2)
        db_session.flush()

        l3 = MenuItem(title="Школа", parent_id=l2.id)
        db_session.add(l3)
        db_session.commit()
        db_session.refresh(l1)
        db_session.refresh(l2)

        assert len(l1.children) == 1
        assert l1.children[0].title == "Образование"
        assert l2.children[0].title == "Школа"
        assert l3.parent_id == l2.id

    def test_multiple_children_on_same_parent(self, db_session: Session) -> None:
        parent = MenuItem(title="Разделы")
        db_session.add(parent)
        db_session.flush()

        for name in ["A", "B", "C"]:
            db_session.add(MenuItem(title=name, parent_id=parent.id))
        db_session.commit()
        db_session.refresh(parent)

        assert len(parent.children) == 3
        assert {c.title for c in parent.children} == {"A", "B", "C"}


class TestMenuItemDelete:
    """Delete behaviour, especially cascade."""

    def test_delete_orphan_child(self, db_session: Session) -> None:
        parent = MenuItem(title="Родитель")
        child = MenuItem(title="Ребёнок")
        db_session.add_all([parent, child])
        db_session.flush()
        child.parent_id = parent.id
        db_session.commit()

        db_session.delete(parent)
        db_session.commit()

        remaining = db_session.execute(select(MenuItem)).scalars().all()
        assert len(remaining) == 0

    def test_delete_child_keeps_parent(self, db_session: Session) -> None:
        parent = MenuItem(title="Родитель")
        child = MenuItem(title="Ребёнок")
        db_session.add_all([parent, child])
        db_session.flush()
        child.parent_id = parent.id
        db_session.commit()

        db_session.delete(child)
        db_session.commit()

        remaining = db_session.execute(select(MenuItem)).scalars().all()
        assert len(remaining) == 1
        assert remaining[0].title == "Родитель"

    def test_delete_nonexistent_raises(self, db_session: Session) -> None:
        from sqlalchemy.exc import NoResultFound

        with pytest.raises(NoResultFound):
            item = db_session.execute(
                select(MenuItem).where(MenuItem.id == 9999)
            ).scalar_one()


class TestMenuItemUpdate:
    """Updating fields on menu items."""

    def test_update_title(self, db_session: Session) -> None:
        item = MenuItem(title="Старое название")
        db_session.add(item)
        db_session.commit()

        item.title = "Новое название"
        db_session.commit()
        db_session.refresh(item)

        assert item.title == "Новое название"

    def test_toggle_active(self, db_session: Session) -> None:
        item = MenuItem(title="Тест", is_active=True)
        db_session.add(item)
        db_session.commit()

        item.is_active = False
        db_session.commit()
        db_session.refresh(item)
        assert item.is_active is False

        item.is_active = True
        db_session.commit()
        db_session.refresh(item)
        assert item.is_active is True

    def test_reparent_item(self, db_session: Session) -> None:
        parent_a = MenuItem(title="A")
        parent_b = MenuItem(title="B")
        child = MenuItem(title="Ребёнок")
        db_session.add_all([parent_a, parent_b, child])
        db_session.flush()
        child.parent_id = parent_a.id
        db_session.commit()

        child.parent_id = parent_b.id
        db_session.commit()
        db_session.refresh(child)

        assert child.parent_id == parent_b.id
        assert child.parent.title == "B"

    def test_reorder(self, db_session: Session) -> None:
        a = MenuItem(title="A", order=0)
        b = MenuItem(title="B", order=1)
        db_session.add_all([a, b])
        db_session.commit()

        a.order, b.order = 1, 0
        db_session.commit()
        db_session.refresh(a)
        db_session.refresh(b)

        assert a.order == 1
        assert b.order == 0
