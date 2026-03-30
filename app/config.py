import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/main.db")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-prod")
    ALGORITHM = "HS256"
    TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней
    
    # Discord OAuth2
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    
    # Roblox API
    ROBlox_CHECK_INTERVAL = int(os.getenv("COOKIE_CHECK_INTERVAL", "3600"))  # секунды

settings = Settings()