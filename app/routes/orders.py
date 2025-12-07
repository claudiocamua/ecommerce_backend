from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from pymongo import ReturnDocument
from datetime import datetime, timedelta
from bson import ObjectId
from app.database import products_collection, orders_collection, carts_collection, get_db
from app.models.order import (
    CreateOrderRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
    OrderListResponse,
    OrderStatsResponse,
    OrderStatus
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/orders", tags=["Pedidos"])

def get_counters_collection():
    """Retorna a collection de contadores"""
    return get_db()["counters"]

def generate_order_number() -> str:
    """Gera número único do pedido"""
    today = datetime.utcnow().strftime("%Y%m%d")
    
    counter = get_counters_collection().find_one_and_update(
    {"_id": f"order_{today}"},
    {"$inc": {"sequence": 1}},
    upsert=True,
    return_document=ReturnDocument.AFTER
)
    
    sequence = counter.get("sequence", 1)
    return f"PED-{today}-{sequence:04d}"

def calculate_shipping_fee(state: str) -> float:
    """Calcula taxa de frete baseado no estado"""
    shipping_table = {
        "SP": 15.00,
        "RJ": 20.00,
        "MG": 25.00,
        "ES": 30.00,
        "PR": 35.00,
        "SC": 35.00,
        "RS": 40.00,
    }
    return shipping_table.get(state, 50.00)  

def estimate_delivery_date(state: str) -> datetime:
    """Estima data de entrega baseado no estado"""
    delivery_days = {
        "SP": 3,
        "RJ": 5,
        "MG": 7,
        "ES": 7,
        "PR": 10,
        "SC": 10,
        "RS": 12,
    }
    days = delivery_days.get(state, 15)
    return datetime.utcnow() + timedelta(days=days)

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_request: CreateOrderRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Finaliza a compra criando um pedido a partir do carrinho"""
    
    user_id = str(current_user["_id"])
    
    cart = carts_collection.find_one({"user_id": user_id})
    
    if not cart or not cart.get("items"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carrinho vazio. Adicione produtos antes de finalizar a compra."
        )
    
    order_items = []
    subtotal = 0.0
    
    for cart_item in cart["items"]:
        product = products_collection.find_one({"_id": ObjectId(cart_item["product_id"])})
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Produto {cart_item['product_id']} não encontrado"
            )
        
        if product["stock"] < cart_item["quantity"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente para {product['name']}. Disponível: {product['stock']}"
            )
        
        item_subtotal = product["price"] * cart_item["quantity"]
        
        order_items.append({
            "product_id": cart_item["product_id"],
            "product_name": product["name"],
            "product_price": product["price"],
            "quantity": cart_item["quantity"],
            "subtotal": round(item_subtotal, 2)
        })
        
        subtotal += item_subtotal
    
    shipping_fee = calculate_shipping_fee(order_request.shipping_address.state)
    total = round(subtotal + shipping_fee, 2)
    
    order_number = generate_order_number()

    order_dict = {
        "order_number": order_number,
        "user_id": user_id,
        "user_name": current_user["full_name"],
        "user_email": current_user["email"],
        "items": order_items,
        "subtotal": round(subtotal, 2),
        "shipping_fee": shipping_fee,
        "total": total,
        "payment_method": order_request.payment_method.value,
        "shipping_address": order_request.shipping_address.dict(),
        "status": OrderStatus.PENDING.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "estimated_delivery": estimate_delivery_date(order_request.shipping_address.state),
        "tracking_code": None
    }
    
    result = orders_collection.insert_one(order_dict)
    
    for item in order_items:
        products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -item["quantity"]}}
        )
    
    carts_collection.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )
    
    created_order = orders_collection.find_one({"_id": result.inserted_id})
    
    return {
        "id": str(created_order["_id"]),
        **{k: v for k, v in created_order.items() if k != "_id"}
    }

@router.get("/my-orders", response_model=OrderListResponse)
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: Optional[OrderStatus] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Lista todos os pedidos do usuário logado"""
    
    user_id = str(current_user["_id"])
    
    filters = {"user_id": user_id}
    if status:
        filters["status"] = status.value
    
    total = orders_collection.count_documents(filters)
    
    skip = (page - 1) * page_size
    
    orders = list(
        orders_collection
        .find(filters)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    
    orders_response = [
        {
            "id": str(order["_id"]),
            **{k: v for k, v in order.items() if k != "_id"}
        }
        for order in orders
    ]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "orders": orders_response
    }

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Retorna detalhes de um pedido específico"""
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de pedido inválido"
        )
    
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    if order["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para ver este pedido"
        )
    
    return {
        "id": str(order["_id"]),
        **{k: v for k, v in order.items() if k != "_id"}
    }

@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Cancela um pedido (apenas se estiver pendente ou confirmado)"""
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de pedido inválido"
        )
    
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    if order["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para cancelar este pedido"
        )
    
    if order["status"] not in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível cancelar pedido com status '{order['status']}'"
        )
    
    orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "status": OrderStatus.CANCELLED.value,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    for item in order["items"]:
        products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": item["quantity"]}}
        )
    
    updated_order = orders_collection.find_one({"_id": ObjectId(order_id)})
    
    return {
        "id": str(updated_order["_id"]),
        **{k: v for k, v in updated_order.items() if k != "_id"}
    }

@router.get("/stats/summary", response_model=OrderStatsResponse)
async def get_order_stats(current_user: dict = Depends(get_current_active_user)):
    """Retorna estatísticas dos pedidos do usuário"""
    
    user_id = str(current_user["_id"])
    
    orders = list(orders_collection.find({"user_id": user_id}))
    
    total_orders = len(orders)
    total_spent = sum(order["total"] for order in orders)
    
    pending_orders = sum(1 for order in orders if order["status"] == OrderStatus.PENDING.value)
    completed_orders = sum(1 for order in orders if order["status"] == OrderStatus.DELIVERED.value)
    cancelled_orders = sum(1 for order in orders if order["status"] == OrderStatus.CANCELLED.value)
    
    return {
        "total_orders": total_orders,
        "total_spent": round(total_spent, 2),
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders
    }

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Atualiza o status do pedido (ADMIN)
    
    Para uso futuro com sistema de permissões de admin
    """
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de pedido inválido"
        )
    
    update_data = {
        "status": request.status.value,
        "updated_at": datetime.utcnow()
    }
    
    if request.tracking_code:
        update_data["tracking_code"] = request.tracking_code
    
    result = orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    updated_order = orders_collection.find_one({"_id": ObjectId(order_id)})
    
    return {
        "id": str(updated_order["_id"]),
        **{k: v for k, v in updated_order.items() if k != "_id"}
    }