from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "Pendente"
    CONFIRMED = "Confirmado"
    PROCESSING = "Em Processamento"
    SHIPPED = "Enviado"
    DELIVERED = "Entregue"
    CANCELLED = "Cancelado"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "Cartão de Crédito"
    DEBIT_CARD = "Cartão de Débito"
    PIX = "PIX"
    BOLETO = "Boleto Bancário"

class ShippingAddress(BaseModel):
    street: str = Field(..., min_length=3, max_length=200)
    number: str = Field(..., max_length=10)
    complement: Optional[str] = Field(None, max_length=100)
    neighborhood: str = Field(..., min_length=3, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=2, description="UF (ex: SP, RJ)")
    zip_code: str = Field(..., pattern=r'^\d{5}-?\d{3}$', description="CEP no formato 00000-000")
    
    @validator('state')
    def validate_state(cls, v):
        return v.upper()
    
    @validator('zip_code')
    def format_zip_code(cls, v):
        v = v.replace('-', '')
        return f"{v[:5]}-{v[5:]}"

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    product_price: float
    quantity: int
    subtotal: float

class CreateOrderRequest(BaseModel):
    payment_method: PaymentMethod
    shipping_address: ShippingAddress
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_method": "PIX",
                "shipping_address": {
                    "street": "Rua das Flores",
                    "number": "123",
                    "complement": "Apto 45",
                    "neighborhood": "Centro",
                    "city": "São Paulo",
                    "state": "SP",
                    "zip_code": "01234-567"
                }
            }
        }

class OrderResponse(BaseModel):
    id: str
    order_number: str
    user_id: str
    user_name: str
    user_email: str
    items: List[OrderItem]
    subtotal: float
    shipping_fee: float
    total: float
    payment_method: PaymentMethod
    shipping_address: ShippingAddress
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    estimated_delivery: Optional[datetime] = None
    tracking_code: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "674e1234...",
                "order_number": "PED-20241201-0001",
                "user_id": "674c1234...",
                "user_name": "Maria Silva",
                "user_email": "maria@example.com",
                "items": [
                    {
                        "product_id": "674d5678...",
                        "product_name": "iPhone 15 Pro",
                        "product_price": 7999.90,
                        "quantity": 1,
                        "subtotal": 7999.90
                    }
                ],
                "subtotal": 7999.90,
                "shipping_fee": 15.00,
                "total": 8014.90,
                "payment_method": "PIX",
                "shipping_address": {
                    "street": "Rua das Flores",
                    "number": "123",
                    "city": "São Paulo",
                    "state": "SP",
                    "zip_code": "01234-567"
                },
                "status": "Pendente",
                "created_at": "2024-12-01T15:00:00",
                "updated_at": "2024-12-01T15:00:00"
            }
        }

class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus
    tracking_code: Optional[str] = None

class OrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    orders: List[OrderResponse]

class OrderStatsResponse(BaseModel):
    total_orders: int
    total_spent: float
    pending_orders: int
    completed_orders: int
    cancelled_orders: int