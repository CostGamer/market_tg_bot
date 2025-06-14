# Архитектура приложения
```
├── app/                           # Основной каталог приложения
│   ├── __init__.py
│   ├── main.py                    # Точка входа: запуск бота и диспетчера
│   ├── config.py                  # Конфигурация приложения (env, токены, параметры)
│   ├── handlers/                  # Обработчики сообщений и команд
│   │   ├── __init__.py
│   │   ├── user/                  # Хендлеры для пользователей
│   │   ├── admin/                 # Хендлеры для админов
│   │   └── common.py              # Общие хендлеры (start, help и т.д.)
│   ├── middlewares/               # Middleware для aiogram
│   ├── keyboards/                 # Inline и Reply клавиатуры
│   ├── states/                    # Состояния FSM (Finite State Machine)
│   ├── services/                  # Бизнес-логика, интеграции с API, брокерами и т.п.
│   ├── repositories/              # Работа с БД, CRUD-операции
│   ├── models/                    # Pydantic/ORM модели данных
│   ├── utils/                     # Вспомогательные функции и утилиты
│   ├── exceptions/                # Пользовательские исключения
│   ├── logging_config.py          # Настройка логирования
│   └── scheduler.py               # Планировщик задач (если нужен, например, APScheduler)
├── migrations/                    # Миграции БД (если используется)
├── .env                           # Переменные окружения
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
└── start.sh                       # Скрипт запуска
```