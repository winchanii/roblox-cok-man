from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
from typing import List, Optional, Tuple
from app.models import RobloxAccount, User
from app.services.roblox_api import RobloxAPI

class AccountManager:
    
    @staticmethod
    async def add_account(
        db: AsyncSession,
        user_id: int,
        cookie: str,
        password: Optional[str] = None,
        description: str = ""
    ) -> Tuple[bool, Optional[RobloxAccount], str]:
        """Добавить аккаунт"""
        try:
            # Получить инфо из Roblox
            user_info = await RobloxAPI.get_user_info(cookie)
            if not user_info:
                return False, None, "Invalid cookie or network error"
            
            # Проверка на дубликат
            result = await db.execute(
                select(RobloxAccount).where(
                    RobloxAccount.user_id == user_id,
                    RobloxAccount.username == user_info["username"]
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return False, None, f"Account {user_info['username']} already exists"
            
            # Создать аккаунт
            account = RobloxAccount(
                user_id=user_id,
                username=user_info["username"],
                user_id_roblox=user_info["user_id"],
                cookie=cookie,
                password=password,
                description=description,
                is_valid=True,
                last_checked=datetime.utcnow()
            )
            
            db.add(account)
            await db.commit()
            await db.refresh(account)
            
            return True, account, ""
        except Exception as e:
            return False, None, str(e)
    
    @staticmethod
    async def bulk_add_cookies(
        db: AsyncSession,
        user_id: int,
        cookies: List[str]
    ) -> Tuple[int, int, List[str]]:
        """Массовое добавление кук"""
        success, failed, errors = 0, 0, []
        
        for cookie in cookies:
            cookie = cookie.strip()
            if not cookie:
                continue
            
            ok, _, error = await AccountManager.add_account(db, user_id, cookie)
            if ok:
                success += 1
            else:
                failed += 1
                errors.append(f"Failed: {error[:50]}")
        
        return success, failed, errors
    
    @staticmethod
    async def link_passwords_from_file(
        db: AsyncSession,
        user_id: int,
        lines: List[str]
    ) -> Tuple[int, int, List[str]]:
        """Привязать логины:пароли к аккаунтам"""
        success, failed, errors = 0, 0, []
        
        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue
            
            parts = line.split(":", 1)
            if len(parts) != 2:
                failed += 1
                errors.append(f"Invalid format: {line[:30]}")
                continue
            
            username, password = parts[0].strip(), parts[1].strip()
            
            # Найти аккаунт по username
            result = await db.execute(
                select(RobloxAccount).where(
                    RobloxAccount.user_id == user_id,
                    RobloxAccount.username == username
                )
            )
            account = result.scalar_one_or_none()
            
            if account:
                account.password = password
                success += 1
            else:
                failed += 1
                errors.append(f"Account not found: {username}")
        
        await db.commit()
        return success, failed, errors
    
    @staticmethod
    async def get_all_accounts(db: AsyncSession, user_id: int) -> List[RobloxAccount]:
        """Получить все аккаунты пользователя"""
        result = await db.execute(
            select(RobloxAccount).where(RobloxAccount.user_id == user_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def delete_account(db: AsyncSession, user_id: int, account_id: int) -> bool:
        """Удалить аккаунт"""
        result = await db.execute(
            delete(RobloxAccount).where(
                RobloxAccount.id == account_id,
                RobloxAccount.user_id == user_id
            )
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def update_description(
        db: AsyncSession,
        user_id: int,
        account_id: int,
        description: str
    ) -> Tuple[bool, str]:
        """Обновить описание"""
        result = await db.execute(
            select(RobloxAccount).where(
                RobloxAccount.id == account_id,
                RobloxAccount.user_id == user_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            return False, "Account not found"
        
        account.description = description
        await db.commit()
        return True, ""
    
    @staticmethod
    async def check_all_cookies(db: AsyncSession, user_id: int) -> int:
        """Проверить все куки на валидность"""
        accounts = await AccountManager.get_all_accounts(db, user_id)
        updated = 0
        
        for account in accounts:
            is_valid = await RobloxAPI.check_cookie_valid(account.cookie)
            if account.is_valid != is_valid:
                account.is_valid = is_valid
                account.last_checked = datetime.utcnow()
                updated += 1
        
        await db.commit()
        return updated
    
    @staticmethod
    async def get_cookie(
        db: AsyncSession,
        user_id: int,
        account_id: int
    ) -> Optional[str]:
        """Получить куку аккаунта"""
        result = await db.execute(
            select(RobloxAccount).where(
                RobloxAccount.id == account_id,
                RobloxAccount.user_id == user_id
            )
        )
        account = result.scalar_one_or_none()
        return account.cookie if account else None