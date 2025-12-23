from pydantic_settings import BaseSettings
from typing import List, ClassVar
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Configurações gerais da aplicação"""

    APP_NAME: ClassVar[str] = "E-commerce API"
    VERSION: ClassVar[str] = "1.0.0"
    
    MONGODB_URI: str
    DB_NAME: str = "ecommerce"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    ENVIRONMENT: str = "development"
    DEMO_MODE: bool = False
    
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5242880  
    
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    
    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    def get_google_redirect_uri(self) -> str:
        """
        Retorna a URI de redirect correta baseada no ambiente
        """
        if self.GOOGLE_REDIRECT_URI:
            return self.GOOGLE_REDIRECT_URI
        
        if self.ENVIRONMENT == "production":
            return "https://ecommerce-backend-qm1k.onrender.com/auth/google/callback"
        else:
            return "http://localhost:8000/auth/google/callback"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
