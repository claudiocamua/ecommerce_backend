import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import test_connection, init_collections
from app.routes import auth, products, cart, orders, uploads, payments

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="API completa para e-commerce com autenticação, produtos, carrinho e pedidos",
    version=settings.VERSION,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup_event():
    print(f"\n{'='*60}")
    print(f"Iniciando aplicação - Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"{'='*60}\n")

    test_connection()
    init_collections()

    print(f"\n{'='*60}")
    print("API inicializada com sucesso!")
    print("Documentação: /docs (somente em desenvolvimento)")
    print(f"{'='*60}\n")


@app.on_event("shutdown")
async def shutdown_event():
    print("\nEncerrando aplicação...")


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }


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
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "products": "/products",
            "cart": "/cart",
            "orders": "/orders",
            "uploads": f"/{settings.UPLOAD_DIR}",
            "payments": "/payments"
        }
    }
