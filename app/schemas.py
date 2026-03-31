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

class AccountDetailResponse(BaseModel):
    id: int
    username: str
    user_id_roblox: str
    description: str
    password: Optional[str] = None
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

class BulkUploadWithPasswordsResponse(BaseModel):
    cookies_added: int
    cookies_failed: int
    passwords_linked: int
    passwords_not_linked: int
    errors: List[str]

class LinkPasswordResponse(BaseModel):
    success: int
    failed: int
    errors: List[str]

class CookieResponse(BaseModel):
    account_id: int
    cookie: str

class AccountExportResponse(BaseModel):
    username: str
    user_id_roblox: str
    cookie: str
    password: Optional[str] = None
    description: str
    is_valid: bool

class AccountsExportResponse(BaseModel):
    accounts: List[AccountExportResponse]
    total: int

class LoginKeyRequest(BaseModel):
    access_key: str

class RobloxUserInfo(BaseModel):
    username: str
    user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_email_verified: bool = False

class RobloxCheckResponse(BaseModel):
    is_valid: bool

class RobloxDescriptionResponse(BaseModel):
    message: str

class RobloxRobuxResponse(BaseModel):
    robux: int
