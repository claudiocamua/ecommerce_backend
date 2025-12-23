import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import test_connection, init_collections
from app.routes import auth, products, cart, orders, uploads, payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    """
    print(f"\n{'='*60}")
    print(f"Iniciando aplicação - Ambiente: {settings.ENVIRONMENT}")
    print(f"{'='*60}\n")
    
    test_connection()
    init_collections()
    
    print(f"\n{'='*60}")
    print("API inicializada com sucesso!")
    if settings.ENVIRONMENT == "development":
        print("Documentação: /docs")
    print(f"{'='*60}\n")
    
    yield
    
    # Shutdown
    print("\nEncerrando aplicação...")


# Criar diretório de uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="API completa para e-commerce com autenticação, produtos, carrinho e pedidos",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Middleware de sessão (necessário para OAuth)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (uploads)
app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    }


# Incluir routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(uploads.router)
app.include_router(payments.router)


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "E-commerce API Completa",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled",
            "auth": "/auth",
            "products": "/products",
            "cart": "/cart",
            "orders": "/orders",
            "uploads": f"/{settings.UPLOAD_DIR}",
            "payments": "/payments"
        }
    }
