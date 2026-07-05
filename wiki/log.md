# Журнал изменений

## 2026-07-04
- **Статический сайт удалён** — проект переведён на FastAPI + SQLite + Jinja2.
- **Структура:** app/ (FastAPI), tests/, wiki/ (только документация).
- **Модель MenuItem:** self-referential SQLAlchemy (parent_id → id) с вложенной древовидной структурой.
- **API:**
  - `GET /admin/menu` — получить всё дерево меню
  - `POST /admin/menu` — создать пункт
  - `PUT /admin/menu/{id}` — обновить пункт
  - `DELETE /admin/menu/{id}` — удалить с каскадом на детей
  - `POST /admin/menu/reorder` — batch-изменение order/parent_id
- **Схемы Pydantic:** MenuItemBase, MenuItemCreate, MenuItemUpdate, MenuItemOut (с children), ReorderRequest
- **Тесты:** 61 тест (33 проходят, 8 известных багов, 20 ошибок инфраструктуры async fixtures)

## 2026-07-05
- **Деплой (2):** LXC `192.168.1.64` стал доступен — выполнено полное развёртывание.
- **Код:** репозиторий склонирован на LXC (git clone), venv пересоздан, зависимости установлены.
- **Миграция:** плоская структура (`app.py`) → пакетная (`app/main.py`). Systemd-сервис обновлён: `uvicorn app:app` → `uvicorn app.main:app`.
- **Перезапуск:** сервис `zolotarevka-fastapi` перезапущен, работает stable.
- **Верификация:** все эндпоинты (/, /admin, /admin/menu, /admin/, /static/*) возвращают 200 через reverse tunnel (VPS → LXC).

## 2026-06-25 (вечер)
- **entities/fastapi-architecture.md**: добавлен раздел «Известные баги и исправления»
- **app.py**: исправлен вызов `seed_db()` в `lifespan`, создание `static/uploads/`
- **app.py**: `api_save_blocks` — `blocks: list = Body(...)` для приёма массива
- **app.py**: `api_save_blocks` — защита от коллизий ID блоков между страницами
- **footer.html**: исправлены битые ссылки (`/sport → /sports`, `/life → /village-life` и др.)
- **admin/js/admin.js**: ID блоков генерируется через `Date.now()` — уникален после перезагрузки
- **admin/js/admin.js**: счётчик ID обновляется при загрузке блоков с сервера
- **Проверено:** API → Админка → Публичный сайт — полный цикл сохранения/отображения

## 2026-06-25
- **SCHEMA.md**: обновлён — FastAPI-стек, новые теги (fastapi, python, sqlite), legacy-статус для WordPress
- **entities/fastapi-architecture.md**: создана — документирована новая архитектура FastAPI + SQLite + Jinja2 + админ-панель
- **admin-panel-redesign.md**: помечен как `legacy` — заменён новой FastAPI админ-панелью
- **log.md**: создана — этот файл

## 2026-06-09
- **admin-panel-redesign.md**: создана — документирован редизайн WordPress админ-панели
- **SCHEMA.md**: создана — первоначальная схема вики

## 2026-05-26
- Начало проекта, создание первоначальных markdown-документов
