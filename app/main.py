from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from app.database import test_connection
from app.routes import auth, products, cart, orders
from app.config import settings
import os

app = FastAPI(
    title="E-commerce API",
    description="API completa para e-commerce com autenticação, produtos, carrinho e pedidos",
    version="4.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    print(f"Iniciando aplicação - Ambiente: {os.getenv('ENVIRONMENT', 'development')}")
    test_connection()

@app.on_event("shutdown")
async def shutdown_event():
    print("Encerrando aplicação...")

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

@app.get("/")
async def root():
    return {
        "message": "E-commerce API Completa",
        "version": "4.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/auth",
            "products": "/products",
            "cart": "/cart",
            "orders": "/orders"
        }
    }