from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String(50), unique=True, index=True)
    discord_username = Column(String(100))
    access_key = Column(String(64), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    accounts = relationship("RobloxAccount", back_populates="user", cascade="all, delete-orphan")

class RobloxAccount(Base):
    __tablename__ = "roblox_accounts"
    __table_args__ = (UniqueConstraint("user_id", "username", name="_user_username_uc"),)
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(100), index=True)
    user_id_roblox = Column(String(50))  # Roblox user ID
    cookie = Column(Text, nullable=False)
    password = Column(Text, nullable=True)  # Зашифровано
    description = Column(Text, default="")
    is_valid = Column(Boolean, default=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="accounts")