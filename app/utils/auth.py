from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.database import users_collection

# Configurar bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    """
    Gera hash da senha com tratamento para limite de 72 bytes do bcrypt.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash bcrypt da senha
        
    Raises:
        ValueError: Se houver erro ao gerar hash
    """
    try:
        # Converter para bytes e truncar se necessário (bcrypt tem limite de 72 bytes)
        password_bytes = password.encode('utf-8')
        
        if len(password_bytes) > 72:
            # Truncar em 72 bytes de forma segura
            password = password_bytes[:72].decode('utf-8', errors='ignore')
            print(f"⚠️ Senha truncada de {len(password_bytes)} para 72 bytes")
        
        return pwd_context.hash(password)
        
    except Exception as e:
        print(f"❌ Erro ao fazer hash da senha: {str(e)}")
        raise ValueError(f"Erro ao processar senha: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha corresponde ao hash.
    
    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash bcrypt armazenado
        
    Returns:
        True se a senha é válida, False caso contrário
    """
    try:
        # Aplicar o mesmo truncamento na verificação
        password_bytes = plain_password.encode('utf-8')
        
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
        
        return pwd_context.verify(plain_password, hashed_password)
        
    except Exception as e:
        print(f"❌ Erro ao verificar senha: {str(e)}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Cria um token JWT.
    
    Args:
        data: Dados para codificar no token
        expires_delta: Tempo de expiração (opcional)
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Obtém o usuário atual a partir do token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        Dados do usuário
        
    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"email": email})
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """
    Verifica se o usuário está ativo.
    
    Args:
        current_user: Dados do usuário atual
        
    Returns:
        Dados do usuário
        
    Raises:
        HTTPException: Se usuário inativo
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return current_user