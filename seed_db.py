"""Seed the database with initial menu items and pages for Zolotarevka site.

Usage:
    python seed_db.py

This will populate menu items and pages if they don't already exist.
Run after a fresh database creation (site.db).
"""

from app.database import Base, engine, SessionLocal
from app.models import MenuItem, Page


def seed_menu(db):
    """Create default menu items if the menu is empty."""
    if db.query(MenuItem).count() > 0:
        print("  Menu already populated, skipping")
        return

    items = [
        MenuItem(title="Главная", url="/", type="page", order=0),
        MenuItem(title="Школа", url="/school", type="page", order=1),
        MenuItem(title="Детский сад", url="/kindergarten", type="page", order=2),
        MenuItem(title="Совхоз", url="/farm", type="page", order=3),
        MenuItem(title="Спорт", url="/sports", type="page", order=4),
        MenuItem(title="Жизнь села", url="/village-life", type="page", order=5),
        MenuItem(title="Медиа", url="/media", type="page", order=6),
        MenuItem(title="Новости", url="/news", type="page", order=7),
    ]
    for item in items:
        db.add(item)
    db.commit()
    print(f"  Created {len(items)} menu items")


def seed_pages(db):
    """Create default pages if none exist."""
    if db.query(Page).count() > 0:
        print("  Pages already populated, skipping")
        return

    pages = [
        Page(title="Главная", slug="main",
             content=("<h2>Добро пожаловать в Золотаревку!</h2>"
                      "<p>Неофициальный портал нашего села. Здесь вы найдете "
                      "новости, информацию о школе, детском саде, совхозе, "
                      "спортивных событиях и культурной жизни.</p>"),
             is_published=True, order=0),
        Page(title="Школа", slug="school",
             content=("<h2>О школе</h2>"
                      "<p>Школа села Золотаревка — муниципальное бюджетное "
                      "общеобразовательное учреждение.</p>"
                      "<h2>Новости школы</h2>"
                      "<p>Последний звонок 2026 прошел в торжественной обстановке.</p>"
                      "<h2>Режим работы</h2><p>Занятия с 8:30 до 14:00.</p>"),
             is_published=True, order=1),
        Page(title="Детский сад", slug="kindergarten",
             content=("<h2>О детском саде</h2>"
                      "<p>Детский сад для детей от 1,5 до 7 лет.</p>"
                      "<h2>Группы</h2>"
                      "<ul><li>Ясельная (1,5-3 года)</li>"
                      "<li>Младшая (3-4 года)</li>"
                      "<li>Средняя (4-5 лет)</li>"
                      "<li>Старшая (5-6 лет)</li>"
                      "<li>Подготовительная (6-7 лет)</li></ul>"),
             is_published=True, order=2),
        Page(title="Совхоз", slug="farm",
             content=("<h2>О совхозе</h2>"
                      "<p>Растениеводство и животноводство. "
                      "Пшеница, ячмень, крупный рогатый скот.</p>"),
             is_published=True, order=3),
        Page(title="Спорт", slug="sports",
             content=("<h2>Спорт в Золотаревке</h2>"
                      "<p>Футбольная команда, волейбол, тренажерный зал.</p>"),
             is_published=True, order=4),
        Page(title="Жизнь села", slug="village-life",
             content=("<h2>Жизнь села</h2>"
                      "<p>Праздники, концерты, доска объявлений.</p>"),
             is_published=True, order=5),
        Page(title="Медиа", slug="media",
             content=("<h2>Медиа</h2>"
                      "<p>Фото и видео из жизни села.</p>"),
             is_published=True, order=6),
        Page(title="Новости", slug="news",
             content=("<h2>Новости</h2>"
                      "<p>Последний звонок, уборочная кампания, спорт.</p>"),
             is_published=True, order=7),
    ]
    for page in pages:
        db.add(page)
    db.commit()
    print(f"  Created {len(pages)} pages")


def main():
    print("Seeding Zolotarevka database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_menu(db)
        seed_pages(db)
    finally:
        db.close()
    print("Done!")


if __name__ == "__main__":
    main()
