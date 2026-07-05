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
        print("  ⏭️  Menu already populated, skipping")
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
    print(f"  ✅ Created {len(items)} menu items")


def seed_pages(db):
    """Create default pages if none exist."""
    if db.query(Page).count() > 0:
        print("  ⏭️  Pages already populated, skipping")
        return

    pages = [
        Page(title="Главная", slug="main",
             content="<p>Добро пожаловать на неофициальный портал села Золотаревка! "
                     "Здесь вы найдете новости, информацию о школе, детском саде, "
                     "совхозе, спортивных событиях и жизни нашего села.</p>",
             is_published=True, order=0),
        Page(title="Школа", slug="school",
             content="<p>Школа села Золотаревка — образовательное учреждение, "
                     "обеспечивающее качественное обучение и воспитание детей.</p>"
                     "<h2>Новости школы</h2>"
                     "<p>Последний звонок 2026 года прошел в торжественной обстановке.</p>"
                     "<h2>Расписание</h2>"
                     "<p>Занятия проводятся с 8:30 до 14:00.</p>",
             is_published=True, order=1),
        Page(title="Детский сад", slug="kindergarten",
             content="<p>Детский сад села Золотаревка — уютное место для развития "
                     "и воспитания дошкольников.</p>"
                     "<p>Группы: младшая, средняя, старшая, подготовительная.</p>",
             is_published=True, order=2),
        Page(title="Совхоз", slug="farm",
             content="<p>Совхоз Золотаревка — сельскохозяйственное предприятие.</p>"
                     "<p>Основные направления: растениеводство, животноводство, "
                     "переработка продукции.</p>",
             is_published=True, order=3),
        Page(title="Спорт", slug="sports",
             content="<p>Спортивная жизнь села Золотаревка.</p>"
                     "<p>Футбольная команда, волейбольная секция и тренажерный зал.</p>"
                     "<p>Матчи проводятся каждую субботу на стадионе.</p>",
             is_published=True, order=4),
        Page(title="Жизнь села", slug="village-life",
             content="<p>Культурные мероприятия, праздники, доска объявлений.</p>",
             is_published=True, order=5),
        Page(title="Медиа", slug="media",
             content="<p>Фотографии и видео из жизни села Золотаревка.</p>",
             is_published=True, order=6),
        Page(title="Новости", slug="news",
             content="<p>Последние новости села Золотаревка.</p>"
                     "<h2>Последний звонок 2026</h2>"
                     "<p>В школе прошел праздник последнего звонка.</p>"
                     "<h2>Зерновые культуры</h2>"
                     "<p>Совхоз начал уборку урожая.</p>",
             is_published=True, order=7),
    ]
    for page in pages:
        db.add(page)
    db.commit()
    print(f"  ✅ Created {len(pages)} pages")


def main():
    print("🌾 Seeding Zolotarevka database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_menu(db)
        seed_pages(db)
    finally:
        db.close()
    print("✅ Database seeded successfully!")


if __name__ == "__main__":
    main()
