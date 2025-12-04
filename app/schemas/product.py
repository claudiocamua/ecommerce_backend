from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CategoryEnum(str, Enum):
    """Categorias de produtos"""
    MODA = "Moda"
    MODA_INTIMA = "Moda Íntima"
    INFANTIL = "Infantil"

   

class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200, description="Nome do produto")
    description: str = Field(..., min_length=10, max_length=2000, description="Descrição do produto")
    price: float = Field(..., gt=0, description="Preço do produto (maior que 0)")
    stock: int = Field(..., ge=0, description="Quantidade em estoque")
    category: CategoryEnum = Field(..., description="Categoria do produto")
    brand: Optional[str] = Field(None, max_length=100, description="Marca do produto")
    
    @validator('price')
    def validate_price(cls, v):
        """Valida o preço com 2 casas decimais"""
        return round(v, 2)

class ProductCreate(ProductBase):
    """Schema para criar produto"""
    pass

class ProductUpdate(BaseModel):
    """Schema para atualizar produto (todos os campos opcionais)"""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[CategoryEnum] = None
    brand: Optional[str] = Field(None, max_length=100)
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None:
            return round(v, 2)
        return v

class ProductResponse(ProductBase):
    """Schema de resposta do produto"""
    id: str
    image_urls: List[str] = []
    created_at: datetime
    updated_at: datetime
    created_by: str  
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "674c1234abcd5678efgh9012",
                "name": "Smartphone XYZ",
                "description": "Smartphone de última geração com câmera de 108MP",
                "price": 2499.90,
                "stock": 50,
                "category": "Eletrônicos",
                "brand": "TechBrand",
                "image_urls": ["https://example.com/image1.jpg"],
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-01T10:00:00",
                "created_by": "user123"
            }
        }

class ProductListResponse(BaseModel):
    """Schema para lista de produtos com paginação"""
    total: int
    page: int
    page_size: int
    products: List[ProductResponse]