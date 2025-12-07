from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    password_confirm: str

    @classmethod
    def validate_password(cls, v: str) -> str:
        """Regras fortes de senha"""
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Senha deve conter pelo menos 1 letra maiúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("Senha deve conter pelo menos 1 letra minúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Senha deve conter pelo menos 1 número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Senha deve conter pelo menos 1 caractere especial")
        return v

    @classmethod
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("As senhas não conferem")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "usuario@example.com",
                "full_name": "João Silva",
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-12-01T10:00:00"
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
