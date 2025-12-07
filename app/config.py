import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configurações gerais da aplicação"""

    APP_NAME = "E-commerce API"
    VERSION = "4.0.0"
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

    
    DEBUG = ENVIRONMENT != "production"

    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME", "ecommerce")

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 5242880))

    def get_allowed_origins(self):
        """Retorna lista dividida por vírgulas"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

settings = Settings()
