from uuid import uuid4
from datetime import datetime

_fake_orders = []

def create_demo_order(user_id: str, items: list, total: float):
    order = {
        "id": str(uuid4()),
        "user_id": user_id,
        "items": items,
        "total": total,
        "status": "paid (demo)",
        "created_at": datetime.utcnow()
    }
    _fake_orders.append(order)
    return order

def list_demo_orders():
    return _fake_orders
