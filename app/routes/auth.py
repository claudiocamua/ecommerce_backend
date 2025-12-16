import traceback
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from pydantic import BaseModel, Field
from bson import ObjectId

from app.database import users_collection
from app.models.user import UserCreate, UserResponse, Token
from app.utils.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_active_user
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])


class UpdateProfileRequest(BaseModel):
    full_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=72)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Registra um novo usuário"""
    
    try:
        # Verificar se email já existe
        if users_collection.find_one({"email": user.email.lower()}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este email já está cadastrado"
            )

        # Validar comprimento da senha em bytes (bcrypt tem limite de 72 bytes)
        if len(user.password.encode('utf-8')) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha não pode ter mais de 72 caracteres"
            )

        # Gerar hash da senha
        try:
            hashed_password = get_password_hash(user.password)
        except Exception as e:
            print(f"❌ Erro ao fazer hash da senha: {e}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao processar senha. Tente uma senha mais curta."
            )

        # Criar documento do usuário
        user_dict = {
            "email": user.email.lower(),
            "full_name": user.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Inserir no banco
        try:
            result = users_collection.insert_one(user_dict)
            created_user = users_collection.find_one({"_id": result.inserted_id})
            
            if not created_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao recuperar usuário criado"
                )
                
        except Exception as e:
            print(f"❌ Erro ao inserir no MongoDB: {e}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao salvar usuário no banco de dados"
            )

        # Retornar usuário criado
        return {
            "id": str(created_user["_id"]),
            "email": created_user["email"],
            "full_name": created_user["full_name"],
            "is_active": created_user["is_active"],
            "is_verified": created_user["is_verified"],
            "created_at": created_user["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro inesperado no registro: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no servidor"
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Faz login e retorna token JWT"""
    
    # DEBUG: Ver o que está chegando
    print(f"🔍 Tentativa de login:")
    print(f"   Username: {form_data.username}")
    print(f"   Password length: {len(form_data.password)}")

    user = users_collection.find_one({"email": form_data.username.lower()})
    
    # DEBUG: Verificar se usuário foi encontrado
    if not user:
        print(f"❌ Usuário não encontrado: {form_data.username.lower()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ Usuário encontrado: {user['email']}")
    print(f"   Hash armazenado: {user['hashed_password'][:20]}...")
    
    # Verificar senha
    password_valid = verify_password(form_data.password, user["hashed_password"])
    print(f"   Senha válida: {password_valid}")
    
    if not password_valid:
        print(f"❌ Senha incorreta para: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Entre em contato com o suporte."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    print(f"✅ Login bem-sucedido: {user['email']}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "is_verified": user.get("is_verified", False),
            "created_at": user["created_at"]
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Retorna dados do usuário logado"""

    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "is_active": current_user["is_active"],
        "is_verified": current_user.get("is_verified", False),
        "created_at": current_user["created_at"]
    }


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Atualiza os dados do usuário"""

    users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "full_name": data.full_name,
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated_user = users_collection.find_one({"_id": current_user["_id"]})

    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "full_name": updated_user["full_name"],
        "is_active": updated_user["is_active"],
        "is_verified": updated_user.get("is_verified", False),
        "created_at": updated_user["created_at"]
    }


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Altera a senha do usuário"""

    if not verify_password(data.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )

    # Validar comprimento da nova senha
    if len(data.new_password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha não pode ter mais de 72 caracteres"
        )

    users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "hashed_password": get_password_hash(data.new_password),
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Senha alterada com sucesso"}
