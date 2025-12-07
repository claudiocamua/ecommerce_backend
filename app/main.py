from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from app.database import test_connection, init_collections
from app.routes import auth, products, cart, orders
from app.config import settings
from app.routes import uploads
import os

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="E-commerce API",
    description="API completa para e-commerce com autenticação, produtos, carrinho e pedidos",
    version="4.0.0",
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

if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

@app.get("/health")
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

@app.get("/")
async def root():
    return {
        "message": "E-commerce API Completa",
        "version": "4.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "products": "/products",
            "cart": "/cart",
            "orders": "/orders"
        }
    }
from app.routes import payments
app.include_router(payments.router)

