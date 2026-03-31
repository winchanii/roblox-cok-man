# 🐧 Деплой на Linux VPS

## 📋 Требования

- VPS с Ubuntu 20.04/22.04 или Debian 11+
- Минимум 512 MB RAM, 1 CPU core
- Домен или статический IP (опционально)

---

## 🚀 Способ 1: Docker (Рекомендуется)

### 1. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка
docker --version
```

### 2. Установка Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### 3. Настройка проекта

```bash
# Клонирование или загрузка проекта
cd /opt
sudo git clone <your_repo_url> roblox-account-manager
# ИЛИ загрузите файлы через SCP/SFTP

cd /opt/roblox-account-manager
sudo chown -R $USER:$USER .
```

### 4. Настройка .env

```bash
cp .env.production .env
nano .env
```

**Заполните значения:**
```env
SECRET_KEY=<сгенерируйте: openssl rand -hex 32>
DISCORD_CLIENT_ID=<ваш client_id>
DISCORD_CLIENT_SECRET=<ваш client_secret>
DISCORD_REDIRECT_URI=http://YOUR_IP:8000/auth/callback
DISCORD_BOT_TOKEN=<ваш токен бота>
SITE_URL=http://YOUR_IP:8000
```

### 5. Запуск через Docker Compose

```bash
# Сборка и запуск
docker-compose -f docker-compose.prod.yml up -d --build

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. Управление

```bash
# Остановить
docker-compose -f docker-compose.prod.yml down

# Перезапустить
docker-compose -f docker-compose.prod.yml restart

# Обновить
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🔧 Способ 2: Прямая установка (без Docker)

### 1. Установка зависимостей

```bash
sudo apt update && sudo apt upgrade -y

# Python и зависимости
sudo apt install -y python3 python3-pip python3-venv git nginx

# Проверка
python3 --version
pip3 --version
```

### 2. Установка проекта

```bash
# Создание директории
sudo mkdir -p /opt/roblox-account-manager
sudo chown $USER:$USER /opt/roblox-account-manager
cd /opt/roblox-account-manager

# Клонирование репозитория
git clone <your_repo_url> .
# ИЛИ загрузьте файлы через SCP/SFTP
```

### 3. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка .env

```bash
cp .env.production .env
nano .env
```

Заполните значения (см. выше).

### 5. Создание директории для данных

```bash
mkdir -p data
chmod 755 data
```

### 6. Настройка systemd сервисов

```bash
# Копирование файлов сервисов
sudo cp deploy/roblox-app.service /etc/systemd/system/
sudo cp deploy/roblox-bot.service /etc/systemd/system/

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение сервисов
sudo systemctl enable roblox-app
sudo systemctl enable roblox-bot

# Запуск
sudo systemctl start roblox-app
sudo systemctl start roblox-bot

# Проверка статуса
sudo systemctl status roblox-app
sudo systemctl status roblox-bot
```

### 7. Настройка Nginx

```bash
# Копирование конфига
sudo cp deploy/nginx.conf /etc/nginx/sites-available/roblox-account-manager

# Редактирование (замените your_domain.com)
sudo nano /etc/nginx/sites-available/roblox-account-manager

# Создание симлинка
sudo ln -s /etc/nginx/sites-available/roblox-account-manager /etc/nginx/sites-enabled/

# Проверка конфига
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
```

### 8. Настройка брандмауэра

```bash
# Установка UFW
sudo apt install -y ufw

# Разрешение SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'

# Включение
sudo ufw enable
sudo ufw status
```

---

## 🔒 SSL/HTTPS (Certbot)

### Установка SSL сертификата

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your_domain.com

# Автоматическое продление
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Обновление nginx.conf для HTTPS

После установки SSL, nginx автоматически обновится. Проверьте:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📊 Мониторинг

### Логи приложения

```bash
# Docker
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f bot

# Systemd
sudo journalctl -u roblox-app -f
sudo journalctl -u roblox-bot -f
```

### Проверка работы

```bash
# Проверка порта
sudo netstat -tlnp | grep 8000

# Проверка процесса
ps aux | grep uvicorn
ps aux | grep bot.py

# curl тест
curl http://localhost:8000/api/accounts
```

---

## 🔄 Обновление

### Docker

```bash
cd /opt/roblox-account-manager
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### Systemd

```bash
cd /opt/roblox-account-manager
source venv/bin/activate
git pull
pip install -r requirements.txt
sudo systemctl restart roblox-app
sudo systemctl restart roblox-bot
```

---

## 🛡️ Безопасность

### 1. Смените SECRET_KEY
```bash
openssl rand -hex 32
```

### 2. Настройте брандмауэр
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. Обновляйте систему регулярно
```bash
sudo apt update && sudo apt upgrade -y
```

### 4. Используйте fail2ban
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## ⚠️ Решение проблем

### Приложение не запускается

```bash
# Проверка логов
sudo journalctl -u roblox-app -n 50

# Проверка порта
sudo lsof -i :8000
```

### Бот не подключается

```bash
# Проверка токена в .env
cat .env | grep DISCORD_BOT_TOKEN

# Проверка логов
sudo journalctl -u roblox-bot -n 50
```

### Ошибка "Permission denied"

```bash
# Исправление прав
sudo chown -R $USER:$USER /opt/roblox-account-manager
chmod -R 755 /opt/roblox-account-manager/data
```

### Nginx возвращает 502 Bad Gateway

```bash
# Проверка работы приложения
curl http://localhost:8000

# Перезапуск сервисов
sudo systemctl restart roblox-app
sudo systemctl restart nginx
```

---

## 📝 Команды для управления

```bash
# Docker
docker-compose -f docker-compose.prod.yml up -d      # Запуск
docker-compose -f docker-compose.prod.yml down       # Остановка
docker-compose -f docker-compose.prod.yml logs -f    # Логи
docker-compose -f docker-compose.prod.yml restart    # Перезапуск

# Systemd
sudo systemctl start/stop/restart/status roblox-app  # Приложение
sudo systemctl start/stop/restart/status roblox-bot  # Бот

# Nginx
sudo systemctl restart nginx                         # Перезапуск Nginx
sudo nginx -t                                        # Проверка конфига
```

---

## ✅ Проверка после установки

1. Откройте `http://YOUR_IP:8000` или `https://your_domain.com`
2. В Discord используйте `!key` для получения ключа
3. Войдите на сайте с ключом
4. Проверьте добавление аккаунтов

---

## 📞 Поддержка

При проблемах создайте issue в репозитории или обратитесь к администратору.
