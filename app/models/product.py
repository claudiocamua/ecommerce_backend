from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CategoryEnum(str, Enum):
    MODA = "Moda"
    MODA_INTIMA = "Moda Íntima"
    INFANTIL = "Infantil"
    VESTIDOS = "Vestidos"
    BLUSAS = "Blusas"
    CALCAS = "Calças"
    ACESSORIOS = "Acessórios"

class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200, description="Nome do produto")
    description: str = Field(..., min_length=10, max_length=2000, description="Descrição do produto")
    price: float = Field(..., gt=0, description="Preço do produto")
    stock: int = Field(..., ge=0, description="Quantidade em estoque")
    category: CategoryEnum = Field(..., description="Categoria do produto")
    brand: Optional[str] = Field(None, max_length=100, description="Marca")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        return round(v, 2)


class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[CategoryEnum] = None
    brand: Optional[str] = Field(None, max_length=100)

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float | None) -> float | None:
        if v is not None:
            return round(v, 2)
        return v

class ProductResponse(ProductBase):
    id: str
    image_urls: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "674c1234abcd5678efgh9012",
                "name": "Vestido Floral Longo",
                "description": "Vestido leve e confortável para o verão",
                "price": 199.90,
                "stock": 25,
                "category": "Vestidos",
                "brand": "FashionBrand",
                "image_urls": ["https://exemplo.com/vestido.jpg"],
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-01T10:00:00",
                "created_by": "admin123"
            }
        }

class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    products: List[ProductResponse]
