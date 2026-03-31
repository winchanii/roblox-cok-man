from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from app.models import RobloxAccount, User
from app.services.roblox_api import RobloxAPI


class AccountManager:
    """Менеджер для управления Roblox аккаунтами пользователей"""

    @staticmethod
    async def add_account(
        db: AsyncSession,
        user_id: int,
        cookie: str,
        password: Optional[str] = None,
        description: str = ""
    ) -> Tuple[bool, Optional[RobloxAccount], str]:
        """
        Добавить аккаунт по куке.
        Возвращает (успех, аккаунт, ошибка).
        """
        try:
            # Получить инфо из Roblox
            user_info = await RobloxAPI.get_user_info(cookie)
            if not user_info:
                return False, None, "Invalid cookie or network error"

            if not user_info.get("username") or not user_info.get("user_id"):
                return False, None, "Failed to parse user info"

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
        """
        Массовое добавление кук.
        Возвращает (успешно, неудачно, список ошибок).
        """
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
    async def bulk_add_cookies_with_passwords(
        db: AsyncSession,
        user_id: int,
        cookies: List[str],
        login_passwords: List[str]
    ) -> Tuple[int, int, List[str]]:
        """
        Массовое добавление кук с последующей привязкой логин:пароль.
        Возвращает (успешно, неудачно, список ошибок).
        """
        # Сначала добавляем все куки
        success, failed, errors = await AccountManager.bulk_add_cookies(db, user_id, cookies)
        
        if success == 0:
            return success, failed, errors
        
        # Затем привязываем пароли
        pwd_success, pwd_failed, pwd_errors = await AccountManager.link_passwords_from_file(
            db, user_id, login_passwords
        )
        
        # Объединяем ошибки
        errors.extend(pwd_errors)
        
        return success, failed + pwd_failed, errors

    @staticmethod
    async def link_passwords_from_file(
        db: AsyncSession,
        user_id: int,
        lines: List[str]
    ) -> Tuple[int, int, List[str]]:
        """
        Привязать логины:пароли к аккаунтам.
        Формат: username:password или email:password
        """
        success, failed, errors = 0, 0, []

        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            # Разделяем только по первому двоеточию (в пароле могут быть :)
            parts = line.split(":", 1)
            if len(parts) != 2:
                failed += 1
                errors.append(f"Invalid format: {line[:30]}")
                continue

            login, password = parts[0].strip(), parts[1].strip()

            # Ищем аккаунт по username (логин может быть username или email)
            result = await db.execute(
                select(RobloxAccount).where(
                    RobloxAccount.user_id == user_id,
                    RobloxAccount.username == login
                )
            )
            account = result.scalar_one_or_none()

            if account:
                account.password = password
                success += 1
            else:
                failed += 1
                errors.append(f"Account not found: {login}")

        await db.commit()
        return success, failed, errors

    @staticmethod
    async def get_all_accounts(db: AsyncSession, user_id: int) -> List[RobloxAccount]:
        """Получить все аккаунты пользователя"""
        result = await db.execute(
            select(RobloxAccount)
            .where(RobloxAccount.user_id == user_id)
            .order_by(RobloxAccount.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_account(
        db: AsyncSession,
        user_id: int,
        account_id: int
    ) -> Optional[RobloxAccount]:
        """Получить конкретный аккаунт"""
        result = await db.execute(
            select(RobloxAccount).where(
                RobloxAccount.id == account_id,
                RobloxAccount.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

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
    async def delete_all_accounts(db: AsyncSession, user_id: int) -> int:
        """Удалить все аккаунты пользователя"""
        result = await db.execute(
            delete(RobloxAccount).where(RobloxAccount.user_id == user_id)
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def update_description(
        db: AsyncSession,
        user_id: int,
        account_id: int,
        description: str
    ) -> Tuple[bool, str]:
        """Обновить описание в базе данных"""
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
    async def update_description_in_roblox(
        db: AsyncSession,
        user_id: int,
        account_id: int,
        description: str
    ) -> Tuple[bool, str]:
        """Обновить описание в базе данных и в Roblox"""
        # Обновляем в БД
        success, error = await AccountManager.update_description(
            db, user_id, account_id, description
        )
        if not success:
            return False, error
        
        # Получаем аккаунт для обновления в Roblox
        account = await AccountManager.get_account(db, user_id, account_id)
        if not account:
            return False, "Account not found after update"
        
        # Обновляем в Roblox
        roblox_success, roblox_error = await RobloxAPI.set_description(account.cookie, description)
        if not roblox_success:
            return False, f"DB updated but Roblox failed: {roblox_error}"
        
        return True, "Description updated in DB and Roblox"

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
    async def check_single_cookie(
        db: AsyncSession,
        user_id: int,
        account_id: int
    ) -> Tuple[bool, bool]:
        """
        Проверить куку конкретного аккаунта.
        Возвращает (найдено, валиден).
        """
        account = await AccountManager.get_account(db, user_id, account_id)
        if not account:
            return False, False
        
        is_valid = await RobloxAPI.check_cookie_valid(account.cookie)
        if account.is_valid != is_valid:
            account.is_valid = is_valid
            account.last_checked = datetime.utcnow()
            await db.commit()
        
        return True, is_valid

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

    @staticmethod
    async def get_account_with_password(
        db: AsyncSession,
        user_id: int,
        account_id: int
    ) -> Optional[Dict]:
        """Получить аккаунт с паролем (для экспорта)"""
        account = await AccountManager.get_account(db, user_id, account_id)
        if not account:
            return None
        
        return {
            "id": account.id,
            "username": account.username,
            "user_id_roblox": account.user_id_roblox,
            "cookie": account.cookie,
            "password": account.password,
            "description": account.description,
            "is_valid": account.is_valid
        }

    @staticmethod
    async def export_accounts_with_passwords(
        db: AsyncSession,
        user_id: int
    ) -> List[Dict]:
        """Экспортировать все аккаунты с паролями"""
        accounts = await AccountManager.get_all_accounts(db, user_id)
        result = []
        
        for account in accounts:
            result.append({
                "username": account.username,
                "user_id_roblox": account.user_id_roblox,
                "cookie": account.cookie,
                "password": account.password,
                "description": account.description,
                "is_valid": account.is_valid
            })
        
        return result
