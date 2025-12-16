from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from app.database import products_collection, carts_collection
from app.models.cart import (
    AddToCartRequest,
    UpdateCartItemRequest,
    CartResponse,
    CartItemResponse,
    ClearCartResponse
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/cart", tags=["Carrinho"])

def calculate_cart_total(items: List[dict]) -> tuple[int, float]:
    """Calcula total de itens e valor total do carrinho"""
    total_items = sum(item["quantity"] for item in items)
    subtotal = sum(item["total_price"] for item in items) 
    return total_items, round(subtotal, 2)

def get_product_details(product_id: str) -> dict:
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

    return product


def format_cart_items(items: List[dict]) -> List[dict]:
    """Formata os itens do carrinho com informações do produto"""
    formatted_items = []
    
    for item in items:
        product = products_collection.find_one({"_id": ObjectId(item["product_id"])})
        
        if not product:
            continue
        
        image_urls = product.get("image_urls", [])
        product_image = image_urls[0] if image_urls and len(image_urls) > 0 else None
        
        unit_price = product["price"]
        quantity = item["quantity"]
        subtotal = round(unit_price * quantity, 2)
        stock = product.get("stock", 0)
        
        formatted_items.append({
            "product_id": str(product["_id"]),
            "product_name": product["name"],
            "product_image": product_image,
            "product_price": unit_price, 
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal, 
            "total_price": subtotal,
            "in_stock": stock >= quantity, 
            "available_stock": stock  
        })
    
    return formatted_items

@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: dict = Depends(get_current_active_user)
):
    user_id = str(current_user["_id"])
    product = get_product_details(request.product_id)

    if product["stock"] < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estoque insuficiente. Disponível: {product['stock']}"
        )

    cart = carts_collection.find_one({"user_id": user_id})

    if not cart:
        carts_collection.insert_one({
            "user_id": user_id,
            "items": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

    existing_item = carts_collection.find_one({
        "user_id": user_id,
        "items.product_id": request.product_id
    })

    if existing_item:
        carts_collection.update_one(
            {"user_id": user_id, "items.product_id": request.product_id},
            {
                "$inc": {"items.$.quantity": request.quantity},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    else:
        carts_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "items": {
                        "product_id": request.product_id,
                        "quantity": request.quantity
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    return await get_cart(current_user)


@router.get("/", response_model=CartResponse)
async def get_cart(current_user: dict = Depends(get_current_active_user)):
    user_id = str(current_user["_id"])
    cart = carts_collection.find_one({"user_id": user_id})

    if not cart or not cart.get("items"):
        return {
            "user_id": user_id,
            "items": [],
            "total_items": 0,
            "subtotal": 0.0,
            "updated_at": datetime.utcnow()
        }

    formatted_items = format_cart_items(cart["items"])
    total_items, subtotal = calculate_cart_total(formatted_items)

    return {
        "user_id": user_id,
        "items": formatted_items,
        "total_items": total_items,
        "subtotal": subtotal,
        "updated_at": cart.get("updated_at", datetime.utcnow())
    }


@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    request: UpdateCartItemRequest,
    current_user: dict = Depends(get_current_active_user)
):
    user_id = str(current_user["_id"])

    if request.quantity == 0:
        carts_collection.update_one(
            {"user_id": user_id},
            {
                "$pull": {"items": {"product_id": product_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return await get_cart(current_user)

    product = get_product_details(product_id)

    if product["stock"] < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estoque insuficiente. Disponível: {product['stock']}"
        )

    result = carts_collection.update_one(
        {"user_id": user_id, "items.product_id": product_id},
        {
            "$set": {
                "items.$.quantity": request.quantity,
                "updated_at": datetime.utcnow()
            }
        }
    ) 

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado no carrinho"
        )

    return await get_cart(current_user)


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    product_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    user_id = str(current_user["_id"])

    carts_collection.update_one(
        {"user_id": user_id},
        {
            "$pull": {"items": {"product_id": product_id}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    return await get_cart(current_user)


@router.delete("/clear", response_model=ClearCartResponse)
async def clear_cart(current_user: dict = Depends(get_current_active_user)):
    user_id = str(current_user["_id"])
    cart = carts_collection.find_one({"user_id": user_id})

    if not cart:
        return {"message": "Carrinho já vazio", "items_removed": 0}

    items_count = len(cart.get("items", []))

    carts_collection.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )

    return {"message": "Carrinho esvaziado", "items_removed": items_count}
