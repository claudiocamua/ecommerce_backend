from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from app.database import products_collection, carts_collection   # <-- já CORRIGIDO
from app.schemas.cart import (
    AddToCartRequest,
    UpdateCartItemRequest,
    CartResponse,
    CartItemResponse,
    ClearCartResponse
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/cart", tags=["Carrinho de Compras"])


def calculate_cart_total(items: List[dict]) -> tuple:
    """Calcula total de itens e subtotal (usando o preço atual do produto)"""
    total_items = sum(item["quantity"] for item in items)
    subtotal = sum(item["subtotal"] for item in items)
    return total_items, round(subtotal, 2)


def get_product_details(product_id: str) -> dict:
    """Busca detalhes do produto"""
    
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


def format_cart_items(cart_items: List[dict]) -> List[CartItemResponse]:
    """Formata itens do carrinho incluindo preço atualizado"""
    formatted_items = []
    
    for item in cart_items:
        product = get_product_details(item["product_id"])

        subtotal = round(item["quantity"] * product["price"], 2)
        
        formatted_items.append({
            "product_id": item["product_id"],
            "product_name": product["name"],
            "product_price": product["price"],
            "product_image": product.get("image_urls", [None])[0],
            "quantity": item["quantity"],
            "subtotal": subtotal,
            "in_stock": product["stock"] > 0,
            "available_stock": product["stock"]
        })
    
    return formatted_items


@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Adiciona produto ao carrinho"""
    
    user_id = str(current_user["_id"])
    product = get_product_details(request.product_id)

    # Estoque insuficiente
    if product["stock"] < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estoque insuficiente. Disponível: {product['stock']}"
        )

    cart = carts_collection.find_one({"user_id": user_id})

    # Criar carrinho se não existir
    if not cart:
        cart = {
            "user_id": user_id,
            "items": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        carts_collection.insert_one(cart)

    # Existe item?
    existing_item = next(
        (item for item in cart["items"] if item["product_id"] == request.product_id),
        None
    )

    if existing_item:
        new_quantity = existing_item["quantity"] + request.quantity

        if product["stock"] < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente. Disponível: {product['stock']}"
            )

        carts_collection.update_one(
            {"user_id": user_id, "items.product_id": request.product_id},
            {
                "$set": {
                    "items.$.quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        new_item = {
            "product_id": request.product_id,
            "quantity": request.quantity
        }

        carts_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {"items": new_item},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    return await get_cart(current_user)


@router.get("/", response_model=CartResponse)
async def get_cart(current_user: dict = Depends(get_current_active_user)):
    """Retorna o carrinho do usuário"""
    
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
    """Atualiza item do carrinho"""
    
    user_id = str(current_user["_id"])

    # Se for remover
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
    """Remove item do carrinho"""
    
    user_id = str(current_user["_id"])

    result = carts_collection.update_one(
        {"user_id": user_id},
        {
            "$pull": {"items": {"product_id": product_id}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    return await get_cart(current_user)


@router.delete("/clear", response_model=ClearCartResponse)
async def clear_cart(current_user: dict = Depends(get_current_active_user)):
    """Remove todos os itens do carrinho"""
    
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


@router.get("/validate", response_model=dict)
async def validate_cart(current_user: dict = Depends(get_current_active_user)):
    """Valida disponibilidade/estoque/preço dos itens"""
    
    user_id = str(current_user["_id"])
    cart = carts_collection.find_one({"user_id": user_id})

    if not cart or not cart.get("items"):
        return {"valid": True, "message": "Carrinho vazio", "issues": []}

    issues = []

    for item in cart["items"]:
        try:
            product = get_product_details(item["product_id"])

            if product["stock"] == 0:
                issues.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "issue": "Produto fora de estoque"
                })

            elif product["stock"] < item["quantity"]:
                issues.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "issue": f"Estoque insuficiente. Disponível: {product['stock']}"
                })

            # Preço mudou?
            if item.get("product_price") and item["product_price"] != product["price"]:
                issues.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "issue": f"Preço alterado"
                })

        except HTTPException:
            issues.append({
                "product_id": item["product_id"],
                "product_name": "Desconhecido",
                "issue": "Produto não encontrado"
            })

    return {
        "valid": len(issues) == 0,
        "message": "Carrinho válido" if len(issues) == 0 else "Há problemas",
        "issues": issues
    }
