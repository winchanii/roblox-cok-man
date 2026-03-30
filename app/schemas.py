from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AccountCreate(BaseModel):
    cookie: str
    password: Optional[str] = None
    description: Optional[str] = ""

class AccountUpdate(BaseModel):
    description: Optional[str] = None
    password: Optional[str] = None

class AccountResponse(BaseModel):
    id: int
    username: str
    user_id_roblox: str
    description: str
    is_valid: bool
    last_checked: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
    valid_count: int
    invalid_count: int

class BulkUploadResponse(BaseModel):
    success: int
    failed: int
    errors: List[str]

class CookieResponse(BaseModel):
    account_id: int
    username: str
    cookie: str

class LoginKeyRequest(BaseModel):
    access_key: str