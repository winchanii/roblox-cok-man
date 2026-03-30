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

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

engine = create_engine(settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"))

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")

@bot.command(name="key")
async def create_key(ctx):
    """Создать ключ доступа"""
    discord_id = str(ctx.author.id)
    
    with Session(engine) as session:
        # Проверить есть ли уже ключ
        result = session.execute(
            select(User).where(User.discord_id == discord_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            if user.access_key:
                await ctx.send(
                    f"🔑 Ваш ключ уже существует:\n`{user.access_key}`\n\n"
                    f"Используйте его для входа на сайт.",
                    ephemeral=True
                )
                return
        
        # Создать нового пользователя
        access_key = generate_access_key()
        new_user = User(
            discord_id=discord_id,
            discord_username=ctx.author.name,
            access_key=access_key,
            is_active=True
        )
        session.add(new_user)
        session.commit()
        
        await ctx.send(
            f"🔑 Ваш ключ доступа:\n`{access_key}`\n\n"
            f"⚠️ **Сохраните его!** Он показывается только один раз.\n\n"
            f"Перейдите на сайт и введите этот ключ для входа.",
            ephemeral=True
        )

@bot.command(name="renew")
async def renew_key(ctx):
    """Обновить ключ доступа"""
    discord_id = str(ctx.author.id)
    
    with Session(engine) as session:
        result = session.execute(
            select(User).where(User.discord_id == discord_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await ctx.send("❌ Пользователь не найден. Используйте `!key` сначала.", ephemeral=True)
            return
        
        new_key = generate_access_key()
        user.access_key = new_key
        session.commit()
        
        await ctx.send(
            f"🔄 Ключ обновлён:\n`{new_key}`",
            ephemeral=True
        )

bot.run(settings.DISCORD_BOT_TOKEN)