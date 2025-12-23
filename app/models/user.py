from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=30, description="Senha entre 8 e 30 caracteres")
    password_confirm: str = Field(..., min_length=8, max_length=30)
    full_name: str = Field(..., min_length=3, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('A senha deve ter no mínimo 8 caracteres')
        
        if len(v) > 30:
            raise ValueError('A senha deve ter no máximo 30 caracteres')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        
        if not re.search(r'\d', v):
            raise ValueError('A senha deve conter pelo menos um número')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        
        return v

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('As senhas não coincidem')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime

    oauth_provider: Optional[str] = None 
    oauth_id: Optional[str] = None  
    picture: Optional[str] = None 

    class Config:
        populate_by_name = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    email: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=30)
    new_password_confirm: str = Field(..., min_length=8, max_length=30)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('A senha deve ter no mínimo 8 caracteres')
        
        if len(v) > 30:
            raise ValueError('A senha deve ter no máximo 30 caracteres')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        
        if not re.search(r'\d', v):
            raise ValueError('A senha deve conter pelo menos um número')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        
        return v

    @field_validator('new_password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('As senhas não coincidem')
        return v


class ChangePasswordResponse(BaseModel):
    message: str


class GoogleCallbackResponse(BaseModel):
    token: Token
    is_new_user: bool = False
