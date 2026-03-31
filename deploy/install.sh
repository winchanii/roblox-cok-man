#!/bin/bash

# ============================================
# Roblox Account Manager - Auto Install Script
# Для Ubuntu 20.04/22.04, Debian 11+
# ============================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Roblox Account Manager Installer      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Проверка root прав
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Пожалуйста, запустите от root (sudo -i)${NC}"
    exit 1
fi

# Обновление системы
echo -e "${YELLOW}[1/8] Обновление системы...${NC}"
apt update && apt upgrade -y

# Установка зависимостей
echo -e "${YELLOW}[2/8] Установка зависимостей...${NC}"
apt install -y python3 python3-pip python3-venv git nginx curl wget

# Создание директории
echo -e "${YELLOW}[3/8] Создание директории...${NC}"
mkdir -p /opt/roblox-account-manager
cd /opt/roblox-account-manager

# Загрузка проекта (если есть репозиторий)
echo -e "${YELLOW}[4/8] Загрузка проекта...${NC}"
read -p "Введите URL репозитория (или нажмите Enter для пропуска): " REPO_URL
if [ ! -z "$REPO_URL" ]; then
    git clone "$REPO_URL" temp_clone
    mv temp_clone/* temp_clone/.* . 2>/dev/null || true
    rm -rf temp_clone
    echo -e "${GREEN}Проект загружен!${NC}"
else
    echo -e "${YELLOW}Пропущено. Загрузите файлы вручную в /opt/roblox-account-manager${NC}"
fi

# Создание виртуального окружения
echo -e "${YELLOW}[5/8] Создание виртуального окружения...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}Зависимости установлены!${NC}"

# Создание .env
echo -e "${YELLOW}[6/8] Настройка .env файла...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}.env уже существует${NC}"
else
    cp .env.production .env 2>/dev/null || cp .env.example .env
    echo -e "${YELLOW}Откройте .env и заполните значения!${NC}"
    echo ""
    echo "Сгенерируйте SECRET_KEY:"
    openssl rand -hex 32
    echo ""
    read -p "Нажмите Enter после заполнения .env..."
fi

# Создание директории для данных
echo -e "${YELLOW}[7/8] Создание директории data...${NC}"
mkdir -p data
chmod 755 data

# Настройка сервисов
echo -e "${YELLOW}[8/8] Настройка systemd сервисов...${NC}"
if [ -f deploy/roblox-app.service ]; then
    cp deploy/roblox-app.service /etc/systemd/system/
    cp deploy/roblox-bot.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable roblox-app
    systemctl enable roblox-bot
    echo -e "${GREEN}Сервисы настроены!${NC}"
else
    echo -e "${RED}Файлы сервисов не найдены!${NC}"
fi

# Настройка Nginx
echo ""
echo -e "${YELLOW}Настроить Nginx? (y/n)${NC}"
read -p "> " nginx_choice
if [ "$nginx_choice" = "y" ]; then
    if [ -f deploy/nginx.conf ]; then
        cp deploy/nginx.conf /etc/nginx/sites-available/roblox-account-manager
        echo -e "${YELLOW}Отредактируйте /etc/nginx/sites-available/roblox-account-manager${NC}"
        echo -e "${YELLOW}Замените 'your_domain.com' на ваш домен/IP${NC}"
        read -p "Нажмите Enter после редактирования..."
        
        ln -s /etc/nginx/sites-available/roblox-account-manager /etc/nginx/sites-enabled/
        nginx -t
        systemctl restart nginx
        echo -e "${GREEN}Nginx настроен!${NC}"
    fi
fi

# Настройка брандмауэра
echo ""
echo -e "${YELLOW}Настроить брандмауэр UFW? (y/n)${NC}"
read -p "> " ufw_choice
if [ "$ufw_choice" = "y" ]; then
    apt install -y ufw
    ufw allow OpenSSH
    ufw allow 'Nginx Full'
    ufw --force enable
    echo -e "${GREEN}Брандмауэр настроен!${NC}"
fi

# Запуск сервисов
echo ""
echo -e "${YELLOW}Запуск сервисов...${NC}"
systemctl start roblox-app
systemctl start roblox-bot

# Проверка статуса
echo ""
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo -e "${GREEN}         Установка завершена!         ${NC}"
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo ""
echo -e "Статус приложения: ${GREEN}$(systemctl is-active roblox-app)${NC}"
echo -e "Статус бота: ${GREEN}$(systemctl is-active roblox-bot)${NC}"
echo ""
echo -e "Логи:"
echo "  sudo journalctl -u roblox-app -f"
echo "  sudo journalctl -u roblox-bot -f"
echo ""
echo -e "URL: ${GREEN}http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Не забудьте:${NC}"
echo "1. Заполнить .env вашими данными"
echo "2. Настроить Discord OAuth2 redirect URI"
echo "3. Добавить бота на Discord сервер"
echo ""
