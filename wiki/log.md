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
- **Деплой:** выполнено полное развёртывание на сервер.
- **Код:** репозиторий склонирован, venv пересоздан, зависимости установлены.
- **Миграция:** плоская структура (`app.py`) → пакетная (`app/main.py`).
- **Верификация:** все эндпоинты (/, /admin, /admin/menu, /admin/, /static/*) возвращают 200.
- **Security-аудит (T11-T13):** просканированы репозитории и сервер. Найдено: 1 CRITICAL (auth bypass на API), 2 HIGH, 5 MEDIUM, 3 LOW. Отчёты сохранены.
- **Security fix (t_7e214a58):** добавлен `require_admin_api` dependency на все API эндпоинты (pages, menu CRUD, media, settings). Публичные эндпоинты (/api/menu, POST /api/suggest) оставлены открытыми.
- **Media + Settings + Suggest (t_d61a1f23):** созданы модели MediaItem, Setting, Suggestion + эндпоинты + 16 тестов.
- **Admin menu UI (t_d88b0815):** 16 тестов на CRUD + UI рендеринг.
- **Public site (t_9971bc03):** проверен локально — все 8 страниц отдают 200 с меню, футером, контентом.
- **POST /login 405 fix (t_21ea6987):** добавлен fallback-роут для 404 вместо 405.
- **Всего тестов:** 145 (113 существующих + 32 новых). 131 проходят, 14 require auth-client фикстуру.
- **Security findings (не исправлено):** auth bypass на API — **ИСПРАВЛЕНО**. Остаётся: слабый дефолтный пароль (требует смены через `ADMIN_PASSWORD` env), отсутствие CSRF, IDOR, слабый session secret — требуют настройки env на продакшене.

## 2026-07-06
- **Меню заполнено:** 8 пунктов (Главная, Школа, Детский сад, Совхоз, Спорт, Жизнь села, Медиа, Новости)
- **Страницы созданы:** 8 страниц с контентом, публичный роут читает из БД
- **Админка:** credentials:include в JS, работоспособность подтверждена
- **seed_db.py:** создан скрипт для начального заполнения БД на новом сервере
- **Вики очищена:** удалены все упоминания WordPress

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
- **SCHEMA.md**: обновлён — FastAPI-стек, новые теги (fastapi, python, sqlite)
- **entities/fastapi-architecture.md**: создана — документирована новая архитектура FastAPI + SQLite + Jinja2 + админ-панель
- **admin-panel-redesign.md**: помечен как `legacy` — заменён новой FastAPI админ-панелью
- **log.md**: создана — этот файл

## 2026-06-09
- **admin-panel-redesign.md**: создана — документирован редизайн админ-панели
- **SCHEMA.md**: создана — первоначальная схема вики

## 2026-05-26
- Начало проекта, создание первоначальных markdown-документов
