import httpx
from typing import Optional, Dict, Any

class RobloxAPI:
    BASE_URL = "https://www.roblox.com"
    API_URL = "https://api.roblox.com"
    
    @staticmethod
    async def get_user_info(cookie: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе по куке"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Получаем .ROBLOSECURITY валидацию и инфо
                headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
                
                # Endpoint для получения текущего пользователя
                resp = await client.get(
                    "https://users.roblox.com/v1/me",
                    headers=headers
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "username": data.get("name"),
                        "user_id": str(data.get("id")),
                        "display_name": data.get("displayName")
                    }
                return None
            except Exception as e:
                print(f"Error fetching user info: {e}")
                return None
    
    @staticmethod
    async def check_cookie_valid(cookie: str) -> bool:
        """Проверить валидность куки"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
                resp = await client.get(
                    "https://users.roblox.com/v1/me",
                    headers=headers
                )
                return resp.status_code == 200
            except Exception:
                return False
    
    @staticmethod
    async def set_description(cookie: str, description: str) -> bool:
        """Установить описание профиля"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = {
                    "Cookie": f".ROBLOSECURITY={cookie}",
                    "Content-Type": "application/json",
                    "X-CSRF-TOKEN": await RobloxAPI._get_csrf_token(cookie)
                }
                resp = await client.patch(
                    "https://accountsettings.roblox.com/v1/description",
                    json={"description": description[:250]},  # лимит Roblox
                    headers=headers
                )
                return resp.status_code == 200
            except Exception:
                return False
    
    @staticmethod
    async def _get_csrf_token(cookie: str) -> str:
        """Получить CSRF токен"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
                resp = await client.post(
                    "https://accountsettings.roblox.com/v1/description",
                    headers=headers
                )
                return resp.headers.get("X-CSRF-TOKEN", "")
            except Exception:
                return ""