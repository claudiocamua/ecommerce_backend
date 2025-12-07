from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class CartItem(BaseModel):
    product_id: str = Field(..., description="ID do produto")
    quantity: int = Field(..., ge=1, description="Quantidade mínima 1")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantidade deve ser no mínimo 1")
        return v

class CartItemResponse(BaseModel):
    product_id: str
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    quantity: int
    subtotal: float
    in_stock: bool
    available_stock: int

class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, description="Quantidade a adicionar")


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=0, description="Nova quantidade (0 para remover)")

class CartResponse(BaseModel):
    user_id: str
    items: List[CartItemResponse] = Field(default_factory=list)
    total_items: int
    subtotal: float
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "674c1234...",
                "items": [
                    {
                        "product_id": "674d5678...",
                        "product_name": "Vestido Floral",
                        "product_price": 199.90,
                        "product_image": "/uploads/products/abc123.jpg",
                        "quantity": 2,
                        "subtotal": 399.80,
                        "in_stock": True,
                        "available_stock": 15
                    }
                ],
                "total_items": 2,
                "subtotal": 399.80,
                "updated_at": "2024-12-01T15:00:00"
            }
        }

class ClearCartResponse(BaseModel):
    message: str
    items_removed: int
