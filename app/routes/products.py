from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.database import products_collection
from app.models.product import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse, 
    ProductListResponse,
    CategoryEnum
)
from app.utils.auth import get_current_active_user
from app.utils.upload import save_multiple_files, delete_file

router = APIRouter(prefix="/products", tags=["Produtos"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_active_user)
):

    print(f"  Criando produto:")
    print(f"   Nome: {product.name}")
    print(f"   Preço: {product.price}")
    print(f"   Estoque: {product.stock}")
    
    product_dict = {
        **product.dict(),
        "image_urls": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": str(current_user["_id"])
    }
    
    result = products_collection.insert_one(product_dict)
    created_product = products_collection.find_one({"_id": result.inserted_id})
    
    return {
        "id": str(created_product["_id"]),
        **{k: v for k, v in created_product.items() if k != "_id"}
    }

@router.post("/{product_id}/images", response_model=ProductResponse)
async def upload_product_images(
    product_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de produto inválido"
        )
    
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    image_urls = await save_multiple_files(files)
    
    current_images = product.get("image_urls", [])
    updated_images = current_images + image_urls
    
    products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "image_urls": updated_images,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    updated_product = products_collection.find_one({"_id": ObjectId(product_id)})
    
    return {
        "id": str(updated_product["_id"]),
        **{k: v for k, v in updated_product.items() if k != "_id"}
    }

@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Itens por página"),
    category: Optional[CategoryEnum] = Query(None, description="Filtrar por categoria"),
    search: Optional[str] = Query(None, description="Buscar por nome ou descrição"),
    min_price: Optional[float] = Query(None, ge=0, description="Preço mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Preço máximo"),
    in_stock: Optional[bool] = Query(None, description="Apenas produtos em estoque")
):
    
    filters = {}
    
    if category:
        filters["category"] = category.value
    
    if search:
        filters["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if min_price is not None or max_price is not None:
        filters["price"] = {}
        if min_price is not None:
            filters["price"]["$gte"] = min_price
        if max_price is not None:
            filters["price"]["$lte"] = max_price
    
    if in_stock:
        filters["stock"] = {"$gt": 0}
    
    total = products_collection.count_documents(filters)
    
    skip = (page - 1) * page_size
    
    products = list(
        products_collection
        .find(filters)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    
    products_response = [
        {
            "id": str(p["_id"]),
            **{k: v for k, v in p.items() if k != "_id"}
        }
        for p in products
    ]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "products": products_response
    }

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Retorna um produto específico"""
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de produto inválido"
        )
    
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    return {
        "id": str(product["_id"]),
        **{k: v for k, v in product.items() if k != "_id"}
    }

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de produto inválido"
        )
    
    existing_product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    update_data = {
        k: v for k, v in product_update.dict(exclude_unset=True).items()
        if v is not None
    }
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )
    
    updated_product = products_collection.find_one({"_id": ObjectId(product_id)})
    
    return {
        "id": str(updated_product["_id"]),
        **{k: v for k, v in updated_product.items() if k != "_id"}
    }

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de produto inválido"
        )
    
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    for image_url in product.get("image_urls", []):
        delete_file(image_url)
    
    products_collection.delete_one({"_id": ObjectId(product_id)})
    
    return None

@router.get("/categories/list")
async def list_categories():
    return {
        "categories": [
            {"value": cat.value, "label": cat.value}
            for cat in CategoryEnum
        ]
    }