```
blockchain-dev/
│
├── clinic/                              # Приложение «Клиника» (врачи, узлы)
│   ├── migrations/                      # Автогенерация Django (миграции БД)
│   │   └── __init__.py
│   ├── templates/                       # ✅ уже есть
│   │   └── clinic/                      # ✅ уже есть
│   │       ├── base.html                # 🆕 добавить (общий каркас)
│   │       └── index.html               # ✅ есть, но нужно заменить на новый
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                        # пусто (заполнить позже)
│   ├── tests.py
│   ├── urls.py                          # ✅ уже есть
│   └── views.py                         # ✅ уже есть
│
├── config/                              # Настройки Django-проекта
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                      # ✏️ добавьте STATICFILES_DIRS
│   ├── urls.py                          # ✅ уже есть
│   └── wsgi.py
│
├── portal/                              # Приложение «Портал пациента»
│   ├── migrations/
│   │   └── __init__.py
│   ├── templates/                       # ✅ уже есть
│   │   └── portal/                      # ✅ уже есть
│   │       ├── base.html                # 🆕 добавить
│   │       ├── index.html               # ✅ есть, но нужно заменить на новый
│   │       ├── register.html            # 🆕 добавить
│   │       └── apply.html               # 🆕 добавить
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py                          # ✅ уже есть
│   └── views.py                         # ✅ уже есть
│
├── scripts/                             # Утилиты
│   └── generate_nodes.py                # ✅ уже есть
│
├── static/                              # 🆕 создать
│   ├── css/
│   │   └── style.css                    # 🆕 добавить
│   └── js/
│       ├── api.js                       # 🆕 добавить
│       └── crypto.js                    # 🆕 добавить
│
├── .env.example
├── .gitignore
├── docker-compose.portal.yml
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── README.md
└── requirements.txt

## Описание папок

- **clinic/** — интерфейс врача и узла клиники.
- **portal/** — интерфейс пациента.
- **config/** — настройки Django, маршрутизация.
- **scripts/** — вспомогательные скрипты.
- **static/** — статика: CSS, JavaScript.
```