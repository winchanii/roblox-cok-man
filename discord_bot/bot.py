import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import sys

sys.path.append('..')

load_dotenv()

from app.models import User, Base
from app.auth import generate_access_key
from app.config import settings

# Настройки интентов
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Синхронный движок для Discord бота
DATABASE_URL_SYNC = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
engine = create_engine(DATABASE_URL_SYNC)

# URL сайта для входа
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")


def init_db():
    """Инициализировать таблицы БД если не существуют"""
    Base.metadata.create_all(engine)


@bot.event
async def on_ready():
    """Событие готовности бота"""
    init_db()
    print(f"✅ Bot logged in as {bot.user}")
    print(f"📊 Servers: {len(bot.guilds)}")
    print(f"🔗 Site URL: {SITE_URL}")


@bot.command(name="key")
@commands.cooldown(1, 60, commands.BucketType.user)  # 1 раз в 60 секунд
async def create_key(ctx):
    """
    Создать ключ доступа для сайта.
    Использование: !key
    """
    discord_id = str(ctx.author.id)

    with Session(engine) as session:
        # Проверить есть ли уже ключ
        result = session.execute(
            select(User).where(User.discord_id == discord_id)
        )
        user = result.scalar_one_or_none()

        if user and user.access_key:
            await ctx.send(
                f"🔑 **Ваш ключ уже существует:**\n"
                f"```\n{user.access_key}\n```\n"
                f"💡 Используйте команду `!renew` для обновления ключа.\n"
                f"🌐 Войти на сайт: {SITE_URL}/login",
                ephemeral=True
            )
            return

        # Создать нового пользователя или обновить существующего
        access_key = generate_access_key()
        
        if not user:
            new_user = User(
                discord_id=discord_id,
                discord_username=ctx.author.name,
                access_key=access_key,
                is_active=True
            )
            session.add(new_user)
        else:
            user.access_key = access_key
            user.discord_username = ctx.author.name
        
        session.commit()

        await ctx.send(
            f"🔑 **Ваш ключ доступа:**\n"
            f"```\n{access_key}\n```\n"
            f"⚠️ **Важно:**\n"
            f"• Сохраните ключ в надёжном месте\n"
            f"• Он показывается только один раз\n"
            f"• Используйте `!renew` для обновления\n\n"
            f"🌐 **Войти на сайт:** {SITE_URL}/login",
            ephemeral=True
        )


@bot.command(name="renew")
@commands.cooldown(1, 300, commands.BucketType.user)  # 1 раз в 5 минут
async def renew_key(ctx):
    """
    Обновить ключ доступа.
    Использование: !renew
    """
    discord_id = str(ctx.author.id)

    with Session(engine) as session:
        result = session.execute(
            select(User).where(User.discord_id == discord_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await ctx.send(
                "❌ Пользователь не найден.\n"
                f"Используйте `!key` для получения ключа.",
                ephemeral=True
            )
            return

        new_key = generate_access_key()
        user.access_key = new_key
        session.commit()

        await ctx.send(
            f"🔄 **Ключ обновлён:**\n"
            f"```\n{new_key}\n```\n"
            f"⚠️ Старый ключ больше не работает!",
            ephemeral=True
        )


@bot.command(name="me")
async def show_my_info(ctx):
    """
    Показать информацию о вашем аккаунте.
    Использование: !me
    """
    discord_id = str(ctx.author.id)

    with Session(engine) as session:
        result = session.execute(
            select(User).where(User.discord_id == discord_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await ctx.send(
                "❌ Вы ещё не зарегистрированы.\n"
                f"Используйте `!key` для получения ключа.",
                ephemeral=True
            )
            return

        # Посчитать аккаунты
        from app.models import RobloxAccount
        accounts_count = session.execute(
            select(RobloxAccount).where(RobloxAccount.user_id == user.id)
        ).scalars().all()
        
        valid_count = sum(1 for a in accounts_count if a.is_valid)

        embed = discord.Embed(
            title=f"👤 {user.discord_username}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🔑 Ключ", value=f"```\n{user.access_key[:20]}...\n```", inline=False)
        embed.add_field(name="📊 Аккаунтов", value=f"{len(accounts_count)}", inline=True)
        embed.add_field(name="✅ Валидные", value=f"{valid_count}", inline=True)
        embed.add_field(name="📅 Зарегистрирован", value=user.created_at.strftime("%d.%m.%Y"), inline=False)
        embed.set_footer(text=f"Discord ID: {user.discord_id}")

        await ctx.send(embed=embed, ephemeral=True)


@bot.command(name="stats")
@commands.is_owner()  # Только владелец бота
async def bot_stats(ctx):
    """
    Показать статистику бота (только для владельца).
    Использование: !stats
    """
    with Session(engine) as session:
        total_users = session.query(User).count()
        total_accounts = session.query(RobloxAccount).count()
        valid_accounts = session.query(RobloxAccount).filter(RobloxAccount.is_valid == True).count()

        embed = discord.Embed(title="📊 Статистика бота", color=discord.Color.green())
        embed.add_field(name="👥 Пользователей", value=str(total_users), inline=True)
        embed.add_field(name="🎮 Аккаунтов", value=str(total_accounts), inline=True)
        embed.add_field(name="✅ Валидные", value=str(valid_accounts), inline=True)
        embed.add_field(name="🖥️ Серверов", value=str(len(bot.guilds)), inline=True)
        embed.add_field(name="👤 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)

        await ctx.send(embed=embed)


@bot.command(name="help")
async def bot_help(ctx):
    """
    Показать справку по командам.
    Использование: !help
    """
    embed = discord.Embed(
        title="📚 Справка по командам",
        description="Roblox Account Manager - Discord Bot",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="`!key`",
        value="Получить ключ доступа для сайта",
        inline=False
    )
    embed.add_field(
        name="`!renew`",
        value="Обновить ключ доступа",
        inline=False
    )
    embed.add_field(
        name="`!me`",
        value="Показать информацию о вашем аккаунте",
        inline=False
    )
    embed.add_field(
        name="`!help`",
        value="Показать эту справку",
        inline=False
    )

    embed.set_footer(text=f"Сайт: {SITE_URL}")
    await ctx.send(embed=embed, ephemeral=True)


@bot.event
async def on_command_error(ctx, error):
    """Обработчик ошибок команд"""
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = int(error.retry_after)
        await ctx.send(
            f"⏳ Пожалуйста, подождите {retry_after} сек. перед использованием этой команды.",
            ephemeral=True
        )
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(
            f"❌ Команда не найдена. Используйте `!help` для списка команд.",
            ephemeral=True
        )
    else:
        print(f"Error: {error}")
        await ctx.send(
            f"❌ Произошла ошибка. Попробуйте позже.",
            ephemeral=True
        )


# Запуск бота
if __name__ == "__main__":
    if not settings.DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN не найден в .env файле!")
        sys.exit(1)
    
    bot.run(settings.DISCORD_BOT_TOKEN)
