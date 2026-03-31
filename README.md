# Roblox Account Manager

Сервер для управления аккаунтами Roblox с веб-интерфейсом и Discord ботом.

## 🚀 Возможности

### Управление аккаунтами
- ✅ Добавление аккаунтов по `.ROBLOSECURITY` cookie
- ✅ Массовая загрузка кук из файла (.txt)
- ✅ Привязка логинов и паролей к аккаунтам
- ✅ Автоматическая проверка валидности кук
- ✅ Установка описания аккаунтов (в БД и Roblox)
- ✅ Экспорт аккаунтов с паролями

### Веб-интерфейс
- 🌐 Красивый и удобный интерфейс
- 📊 Дашборд со статистикой
- 🔐 Авторизация через Discord
- 📱 Адаптивный дизайн

### Discord Бот
- 🤖 Выдача ключей доступа через команды
- 📊 Статистика пользователя
- 🔑 Обновление ключей

### API
- 📡 Полноценное REST API
- 🔐 JWT аутентификация
- 📚 Документация через OpenAPI

---

## 📋 Требования

- Python 3.9+
- Discord приложение (для OAuth2)
- Discord бот

---

## ⚙️ Установка

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd roblox-cok-man
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка .env файла

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/main.db

# JWT Secret (generate random)
SECRET_KEY=<your-secret-key>

# Discord OAuth2
DISCORD_CLIENT_ID=<your_client_id>
DISCORD_CLIENT_SECRET=<your_client_secret>
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback

# Discord Bot
DISCORD_BOT_TOKEN=<your_bot_token>

# Site URL
SITE_URL=http://localhost:8000
```

### 4. Настройка Discord OAuth2

1. Перейдите на https://discord.com/developers
2. Создайте новое приложение
3. В разделе **OAuth2** добавьте redirect URI: `http://localhost:8000/auth/callback`
4. Скопируйте **Client ID** и **Client Secret** в `.env`

### 5. Настройка Discord Бота

1. В Discord Developer Portal перейдите в раздел **Bot**
2. Создайте бота и скопируйте токен в `.env`
3. В разделе **OAuth2 → URL Generator** выберите scopes: `bot`, `applications.commands`
4. Добавьте бота на свой сервер

---

## 🚀 Запуск

### Запуск сервера

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Или просто:

```bash
python app/main.py
```

### Запуск Discord бота (в отдельном терминале)

```bash
python discord_bot/bot.py
```

---

## 📖 Использование

### 1. Получение ключа доступа

В Discord используйте команду:
```
!key
```

Бот выдаст вам ключ доступа.

### 2. Вход на сайт

1. Перейдите на `http://localhost:8000/login`
2. Введите полученный ключ
3. Вы получите доступ к интерфейсу

### 3. Добавление аккаунтов

#### Через веб-интерфейс:
- Нажмите "Добавить аккаунт" и вставьте куку
- Или загрузите файл с куками через "Загрузить куки"

#### Через API:
```bash
curl -X POST http://localhost:8000/api/accounts \
  -H "Authorization: Bearer <your_token>" \
  -F "cookie=<.ROBLOSECURITY_cookie>"
```

### 4. Массовая загрузка

1. Создайте файл `cookies.txt` с куками (одна на строку)
2. Создайте файл `logins.txt` с логинами:паролями (формат: `username:password`)
3. Загрузите через интерфейс "Куки + Логины"

---

## 📡 API Endpoints

### Аутентификация
- `POST /auth/key` - Вход по ключу доступа
- `GET /auth/discord` - Discord OAuth2

### Аккаунты
- `GET /api/accounts` - Получить все аккаунты
- `POST /api/accounts` - Добавить аккаунт
- `POST /api/accounts/bulk-cookies` - Массовая загрузка кук
- `POST /api/accounts/bulk-with-passwords` - Куки + Логины
- `POST /api/accounts/link-passwords` - Привязать логины
- `DELETE /api/accounts/{id}` - Удалить аккаунт
- `DELETE /api/accounts/all` - Удалить всё
- `PUT /api/accounts/{id}/description` - Обновить описание
- `GET /api/accounts/{id}/cookie` - Получить куку
- `POST /api/accounts/check-all` - Проверить все куки
- `GET /api/accounts/export/with-passwords` - Экспорт

### Roblox API
- `GET /api/roblox/user-info?cookie=<cookie>` - Инфо о пользователе
- `GET /api/roblox/check-cookie?cookie=<cookie>` - Проверка куки
- `POST /api/roblox/set-description` - Установка описания
- `GET /api/roblox/robux-balance?cookie=<cookie>` - Баланс Robux

---

## 🗂️ Структура проекта

```
roblox cok man/
├── app/
│   ├── main.py              # FastAPI приложение
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы
│   ├── database.py          # Настройки БД
│   ├── auth.py              # Аутентификация
│   ├── config.py            # Конфигурация
│   ├── services/
│   │   ├── roblox_api.py    # Roblox API клиент
│   │   └── account_manager.py # Менеджер аккаунтов
│   └── templates/           # HTML шаблоны
├── discord_bot/
│   └── bot.py               # Discord бот
├── static/
│   ├── css/                 # CSS стили
│   └── js/                  # JavaScript
├── data/                    # База данных (создаётся автоматически)
├── .env                     # Переменные окружения
├── .env.example             # Пример .env
└── requirements.txt         # Зависимости
```

---

## 🔒 Безопасность

- 🔐 JWT токены для аутентификации
- 🔐 Изоляция данных пользователей
- 🔐 Хранение паролей в БД (не шифруется по умолчанию)
- ⚠️ Не передавайте файл базы данных другим лицам

---

## 🛠️ Discord Бот Команды

| Команда | Описание |
|---------|----------|
| `!key` | Получить ключ доступа |
| `!renew` | Обновить ключ |
| `!me` | Информация об аккаунте |
| `!help` | Справка по командам |
| `!stats` | Статистика бота (владелец) |

---

## 📝 Форматы файлов

### Файл с куками (cookies.txt)
```
<cookie_1>
<cookie_2>
<cookie_3>
```

### Файл с логинами (logins.txt)
```
username1:password1
username2:password2
email3:password3
```

---

## ⚠️ Важные замечания

1. Не передавайте `.ROBLOSECURITY` куки третьим лицам
2. Не передавайте файл базы данных
3. Регулярно проверяйте куки на валидность
4. Используйте надёжный `SECRET_KEY` в продакшене

---

## 🐛 Решение проблем

### Ошибка "Invalid cookie"
- Кука могла истечь, войдите в аккаунт заново в браузере
- Проверьте куку через API: `GET /api/roblox/check-cookie`

### Discord бот не отвечает
- Проверьте токен бота в `.env`
- Убедитесь, что бот добавлен на сервер
- Проверьте права доступа бота

### Ошибка подключения к БД
- Убедитесь, что директория `data/` существует
- Проверьте права доступа к файлу БД

---

## 📄 Лицензия

MIT License

---

## 💡 Советы

- Регулярно делайте бэкап базы данных
- Используйте команду `!renew` для смены ключа
- Проверяйте куки раз в неделю через "Проверить все"

---

## 📞 Поддержка

Создайте issue в репозитории или обратитесь к администратору сервера.
