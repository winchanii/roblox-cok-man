import httpx
from typing import Optional, Dict, Any, Tuple
import re

class RobloxAPI:
    """Roblox API клиент для работы с аккаунтами"""
    
    # Основные endpoints
    ACCOUNTS_URL = "https://www.roblox.com/my/account/json"
    USERS_API = "https://users.roblox.com"
    ACCOUNT_SETTINGS_API = "https://accountsettings.roblox.com"
    AUTH_API = "https://auth.roblox.com"
    MOBILE_API = "https://mobileapi.roblox.com"
    
    @staticmethod
    def _get_cookie_headers(cookie: str) -> Dict[str, str]:
        """Получить заголовки с кукой"""
        return {
            "Cookie": f".ROBLOSECURITY={cookie}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    @staticmethod
    async def get_user_info(cookie: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о пользователе по куке.
        Использует my/account/json для получения основной информации.
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            try:
                headers = RobloxAPI._get_cookie_headers(cookie)
                
                # Основной endpoint для получения информации об аккаунте
                resp = await client.get(
                    RobloxAPI.ACCOUNTS_URL,
                    headers=headers
                )
                
                # Если редирект на логин - кука невалидна
                if resp.status_code in [302, 301]:
                    return None
                    
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "username": data.get("Name", ""),
                        "user_id": str(data.get("UserId", "")),
                        "display_name": data.get("DisplayName", ""),
                        "email": data.get("Email", ""),
                        "is_email_verified": data.get("IsEmailVerified", False)
                    }
                
                # Альтернативный метод через users API
                resp = await client.get(
                    f"{RobloxAPI.USERS_API}/v1/me",
                    headers=headers
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "username": data.get("name", ""),
                        "user_id": str(data.get("id", "")),
                        "display_name": data.get("displayName", "")
                    }
                        
                return None
            except Exception as e:
                print(f"[RobloxAPI] Error fetching user info: {e}")
                return None

    @staticmethod
    async def check_cookie_valid(cookie: str) -> bool:
        """
        Проверить валидность куки.
        Использует authentication-ticket для надёжной проверки.
        """
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            try:
                headers = RobloxAPI._get_cookie_headers(cookie)
                
                # Проверка через my/account/json (быстрая)
                resp = await client.get(
                    RobloxAPI.ACCOUNTS_URL,
                    headers=headers
                )
                
                if resp.status_code in [302, 301]:
                    return False
                    
                if resp.status_code == 200:
                    return True
                
                # Дополнительная проверка через authentication-ticket
                resp = await client.post(
                    f"{RobloxAPI.AUTH_API}/v1/authentication-ticket/",
                    headers=headers
                )
                
                return resp.status_code == 200
            except Exception:
                return False

    @staticmethod
    async def set_description(cookie: str, description: str) -> Tuple[bool, str]:
        """
        Установить описание профиля.
        Возвращает (успех, сообщение об ошибке).
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Сначала получаем CSRF токен
                csrf_token = await RobloxAPI._get_csrf_token(cookie)
                if not csrf_token:
                    return False, "Failed to get CSRF token"
                
                headers = RobloxAPI._get_cookie_headers(cookie)
                headers["X-CSRF-TOKEN"] = csrf_token
                
                # Roblox лимитит описание 250 символами
                description = description[:250]
                
                resp = await client.patch(
                    f"{RobloxAPI.ACCOUNT_SETTINGS_API}/v1/description",
                    json={"description": description},
                    headers=headers
                )
                
                if resp.status_code == 200:
                    return True, "Description updated"
                
                error_data = resp.json() if resp.content else {}
                error_msg = error_data.get("message", f"Status code: {resp.status_code}")
                return False, error_msg
                
            except Exception as e:
                return False, str(e)

    @staticmethod
    async def get_csrf_token(cookie: str) -> str:
        """Получить CSRF токен для API запросов"""
        return await RobloxAPI._get_csrf_token(cookie)

    @staticmethod
    async def _get_csrf_token(cookie: str) -> str:
        """Внутренний метод для получения CSRF токена"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                headers = RobloxAPI._get_cookie_headers(cookie)
                # POST запрос без тела для получения CSRF токена
                resp = await client.post(
                    f"{RobloxAPI.ACCOUNT_SETTINGS_API}/v1/description",
                    headers=headers,
                    json={"description": ""}
                )
                return resp.headers.get("X-CSRF-TOKEN", "")
            except Exception:
                return ""

    @staticmethod
    async def get_robux_balance(cookie: str) -> Optional[int]:
        """Получить баланс Robux"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                headers = RobloxAPI._get_cookie_headers(cookie)
                resp = await client.get(
                    f"{RobloxAPI.USERS_API}/v1/me/currency",
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("robux", 0)
                return None
            except Exception:
                return None

    @staticmethod
    async def get_account_age(cookie: str) -> Optional[int]:
        """Получить возраст аккаунта (сколько дней с момента создания)"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                headers = RobloxAPI._get_cookie_headers(cookie)
                resp = await client.get(
                    f"{RobloxAPI.USERS_API}/v1/me",
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    created_at = data.get("created")
                    if created_at:
                        from datetime import datetime
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        age = (datetime.utcnow().replace(tzinfo=created_date.tzinfo) - created_date).days
                        return age
                return None
            except Exception:
                return None

    @staticmethod
    async def get_thumbnail_url(user_id: str) -> str:
        """Получить URL аватара пользователя"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("data"):
                        return data["data"][0].get("imageUrl", "")
                return ""
            except Exception:
                return ""
