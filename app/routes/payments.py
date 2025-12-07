from fastapi import APIRouter
from app.models.payment import CardPayment, PixPayment
from app.demo.payments_demo import simulate_card_payment, simulate_pix_payment
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/card")
def pay_with_card(data: CardPayment):
    if settings.DEMO_MODE:
        return simulate_card_payment(data.amount)
    return {"error": "Pagamento real não implementado"}

@router.post("/pix")
def pay_with_pix(data: PixPayment):
    if settings.DEMO_MODE:
        return simulate_pix_payment(data.amount)
    return {"error": "Pagamento real não implementado"}
