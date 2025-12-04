from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class CartItem(BaseModel):
    """Item individual do carrinho"""
    product_id: str = Field(..., description="ID do produto")
    quantity: int = Field(..., ge=1, description="Quantidade (mínimo 1)")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantidade deve ser no mínimo 1')
        return v

class CartItemResponse(BaseModel):
    """Resposta do item do carrinho com detalhes do produto"""
    product_id: str
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    quantity: int
    subtotal: float
    in_stock: bool
    available_stock: int

class AddToCartRequest(BaseModel):
    """Request para adicionar produto ao carrinho"""
    product_id: str
    quantity: int = Field(1, ge=1, description="Quantidade a adicionar")

class UpdateCartItemRequest(BaseModel):
    """Request para atualizar quantidade de um item"""
    quantity: int = Field(..., ge=0, description="Nova quantidade (0 para remover)")

class CartResponse(BaseModel):
    """Resposta completa do carrinho"""
    user_id: str
    items: List[CartItemResponse]
    total_items: int
    subtotal: float
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "674c1234...",
                "items": [
                    {
                        "product_id": "674d5678...",
                        "product_name": "iPhone 15 Pro",
                        "product_price": 7999.90,
                        "product_image": "/uploads/products/abc123.jpg",
                        "quantity": 2,
                        "subtotal": 15999.80,
                        "in_stock": True,
                        "available_stock": 25
                    }
                ],
                "total_items": 2,
                "subtotal": 15999.80,
                "updated_at": "2024-12-01T15:00:00"
            }
        }

class ClearCartResponse(BaseModel):
    """Resposta ao limpar carrinho"""
    message: str
    items_removed: int