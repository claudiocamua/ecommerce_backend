from pydantic import BaseModel

class CardPayment(BaseModel):
    card_number: str
    card_holder: str
    expiry_date: str
    cvv: str
    amount: float

class PixPayment(BaseModel):
    amount: float
