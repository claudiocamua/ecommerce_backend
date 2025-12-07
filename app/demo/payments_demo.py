from uuid import uuid4

def simulate_card_payment(amount: float):
    return {
        "status": "success",
        "message": "Pagamento com cartão simulado (modo DEMO)",
        "transaction_id": f"demo-card-{uuid4()}"
    }

def simulate_pix_payment(amount: float):
    return {
        "status": "success",
        "message": "Pagamento PIX simulado (modo DEMO)",
        "transaction_id": f"demo-pix-{uuid4()}",
        "pix_code": "00020126360014BR.COM.PIX0114+5511999999995204000053039865406100.005802BR5913Loja Demo6009Sao Paulo62070503***6304ABCD"
    }
