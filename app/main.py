from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import httpx
from datetime import datetime
import os

from app.config import settings
from app.database import init_db, get_db
from app.models import User
from app.auth import (
    get_current_user, create_jwt_token,
    generate_access_key, verify_token
)
from app.schemas import (
    AccountResponse, AccountListResponse,
    BulkUploadResponse, CookieResponse,
    AccountDetailResponse, LinkPasswordResponse
)
from app.services.account_manager import AccountManager
from app.services.roblox_api import RobloxAPI

from sqlalchemy import select, update

app = FastAPI(title="Roblox Cookie Manager API")

# Монтируем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ==================== AUTH ====================

@app.get("/auth/discord")
async def discord_login():
    """Перенаправление на Discord OAuth2"""
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )
    return {"redirect_url": discord_auth_url}

@app.get("/auth/callback")
async def discord_callback(request: Request, code: str):
    """Callback от Discord"""
    async with httpx.AsyncClient() as client:
        # Получить токен
        token_resp = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DISCORD_REDIRECT_URI
            }
        )

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord auth failed")

        access_token = token_resp.json()["access_token"]

        # Получить инфо о пользователе
        user_resp = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_resp.json()
        discord_id = user_data["id"]
        discord_username = user_data["username"]

    async for db in get_db():
        # Найти или создать пользователя
        result = await db.execute(
            select(User).where(User.discord_id == discord_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Пользователь должен иметь ключ от бота
            raise HTTPException(
                status_code=403,
                detail="No access key found. Get one from Discord bot first."
            )

        # Создать JWT
        jwt_token = create_jwt_token(user.id, discord_id)

        return templates.TemplateResponse(
            "login_success.html",
            {"request": request, "token": jwt_token, "username": discord_username}
        )

@app.post("/auth/key")
async def verify_access_key(access_key: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Проверить ключ доступа (используется ботом)"""
    result = await db.execute(
        select(User).where(User.access_key == access_key, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid or inactive key")

    jwt_token = create_jwt_token(user.id, user.discord_id)
    return {"token": jwt_token, "user_id": user.id}

# ==================== ACCOUNTS API ====================

@app.get("/api/accounts", response_model=AccountListResponse)
async def get_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех аккаунтов"""
    accounts = await AccountManager.get_all_accounts(db, user.id)

    valid_count = sum(1 for a in accounts if a.is_valid)

    return {
        "accounts": accounts,
        "total": len(accounts),
        "valid_count": valid_count,
        "invalid_count": len(accounts) - valid_count
    }

@app.get("/api/accounts/{account_id}", response_model=AccountDetailResponse)
async def get_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить详细信息 об аккаунте"""
    account = await AccountManager.get_account(db, user.id, account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account

@app.post("/api/accounts", status_code=201)
async def add_account(
    cookie: str = Form(...),
    password: Optional[str] = Form(None),
    description: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавить один аккаунт по куке"""
    success, account, error = await AccountManager.add_account(
        db, user.id, cookie, password, description
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Account added", "account": account}

@app.post("/api/accounts/bulk-cookies")
async def bulk_upload_cookies(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Массовая загрузка кук из файла (.txt, один cookie на строку)"""
    content = await file.read()
    cookies = content.decode("utf-8").split("\n")

    success, failed, errors = await AccountManager.bulk_add_cookies(db, user.id, cookies)

    return {
        "success": success,
        "failed": failed,
        "errors": errors[:10]  # первые 10 ошибок
    }

@app.post("/api/accounts/bulk-with-passwords")
async def bulk_upload_with_passwords(
    cookies_file: UploadFile = File(...),
    passwords_file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Массовая загрузка кук и привязка логин:пароль.
    cookies_file: файл с куками (одна на строку)
    passwords_file: файл с логин:пароль (одна пара на строку)
    """
    # Читаем куки
    cookies_content = await cookies_file.read()
    cookies = [c.strip() for c in cookies_content.decode("utf-8").split("\n") if c.strip()]
    
    # Читаем логин:пароль
    passwords_content = await passwords_file.read()
    passwords = [p.strip() for p in passwords_content.decode("utf-8").split("\n") if p.strip()]
    
    if not cookies:
        raise HTTPException(status_code=400, detail="No cookies provided")
    if not passwords:
        raise HTTPException(status_code=400, detail="No passwords provided")
    
    # Сначала добавляем куки
    success, failed, errors = await AccountManager.bulk_add_cookies(db, user.id, cookies)
    
    # Затем привязываем пароли
    pwd_success, pwd_failed, pwd_errors = await AccountManager.link_passwords_from_file(
        db, user.id, passwords
    )
    
    # Объединяем ошибки
    all_errors = errors + pwd_errors

    return {
        "cookies_added": success,
        "cookies_failed": failed,
        "passwords_linked": pwd_success,
        "passwords_not_linked": pwd_failed,
        "errors": all_errors[:20]
    }

@app.post("/api/accounts/link-passwords")
async def link_passwords(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Привязать логины:пароли к аккаунтам (формат: username:password)"""
    content = await file.read()
    lines = content.decode("utf-8").split("\n")

    success, failed, errors = await AccountManager.link_passwords_from_file(db, user.id, lines)

    return {
        "success": success,
        "failed": failed,
        "errors": errors[:10]
    }

@app.delete("/api/accounts/{account_id}")
async def delete_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить аккаунт"""
    success = await AccountManager.delete_account(db, user.id, account_id)

    if not success:
        raise HTTPException(status_code=404, detail="Account not found")

    return {"message": "Account deleted"}

@app.delete("/api/accounts/all")
async def delete_all_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить ВСЕ аккаунты пользователя"""
    deleted = await AccountManager.delete_all_accounts(db, user.id)
    return {"message": f"Deleted {deleted} accounts"}

@app.put("/api/accounts/{account_id}/description")
async def set_description(
    account_id: int,
    description: str,
    apply_in_roblox: bool = True,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Установить описание аккаунта.
    apply_in_roblox: если True, описание применится и в Roblox.
    """
    if apply_in_roblox:
        success, error = await AccountManager.update_description_in_roblox(
            db, user.id, account_id, description
        )
    else:
        success, error = await AccountManager.update_description(
            db, user.id, account_id, description
        )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Description updated"}

@app.get("/api/accounts/{account_id}/cookie")
async def get_account_cookie(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить куку аккаунта"""
    cookie = await AccountManager.get_cookie(db, user.id, account_id)

    if not cookie:
        raise HTTPException(status_code=404, detail="Account not found")

    return {"account_id": account_id, "cookie": cookie}

@app.get("/api/accounts/{account_id}/full")
async def get_account_full(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить полную информацию об аккаунте (с паролем если есть)"""
    account_data = await AccountManager.get_account_with_password(db, user.id, account_id)
    
    if not account_data:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account_data

@app.post("/api/accounts/check-all")
async def check_all_cookies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Проверить все куки на валидность"""
    updated = await AccountManager.check_all_cookies(db, user.id)
    return {"message": f"Checked all cookies, {updated} status updated"}

@app.post("/api/accounts/{account_id}/check")
async def check_single_cookie(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Проверить куку конкретного аккаунта"""
    found, is_valid = await AccountManager.check_single_cookie(db, user.id, account_id)
    
    if not found:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"account_id": account_id, "is_valid": is_valid}

@app.get("/api/accounts/export/with-passwords")
async def export_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Экспортировать все аккаунты с паролями (JSON формат)"""
    accounts = await AccountManager.export_accounts_with_passwords(db, user.id)
    return {"accounts": accounts, "total": len(accounts)}

# ==================== ROBLOX API ====================

@app.get("/api/roblox/user-info")
async def get_roblox_user_info(
    cookie: str,
    user: User = Depends(get_current_user)
):
    """Получить информацию о пользователе Roblox по куке"""
    user_info = await RobloxAPI.get_user_info(cookie)
    if not user_info:
        raise HTTPException(status_code=400, detail="Invalid cookie")
    return user_info

@app.get("/api/roblox/check-cookie")
async def check_roblox_cookie(
    cookie: str,
    user: User = Depends(get_current_user)
):
    """Проверить валидность куки Roblox"""
    is_valid = await RobloxAPI.check_cookie_valid(cookie)
    return {"is_valid": is_valid}

@app.post("/api/roblox/set-description")
async def set_roblox_description(
    cookie: str,
    description: str,
    user: User = Depends(get_current_user)
):
    """Установить описание в Roblox (без сохранения в БД)"""
    success, error = await RobloxAPI.set_description(cookie, description)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Description updated"}

@app.get("/api/roblox/robux-balance")
async def get_robux_balance(
    cookie: str,
    user: User = Depends(get_current_user)
):
    """Получить баланс Robux"""
    balance = await RobloxAPI.get_robux_balance(cookie)
    if balance is None:
        raise HTTPException(status_code=400, detail="Invalid cookie")
    return {"robux": balance}

# ==================== WEB PAGES ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница - дашборд"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Страница управления аккаунтами"""
    return templates.TemplateResponse("accounts.html", {"request": request})

@app.on_event("startup")
async def startup():
    await init_db()
    # Создаём директорию data если нет
    os.makedirs("data", exist_ok=True)
    print(f"🚀 Server started on http://{settings.HOST}:{settings.PORT}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
