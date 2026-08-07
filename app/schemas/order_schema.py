from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"


class OrderCheckout(BaseModel):
    user_id: int = Field(..., gt=0)
    payment_method: PaymentMethod


class OrderDetailResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int = Field(..., gt=0)
    price: int = Field(..., ge=0)
    class Config:
        orm_mode = True


class OrderHistoryResponse(BaseModel):
    id: int
    user_id: int
    order_date: datetime
    payment_method: PaymentMethod
    total_amount: int = Field(..., ge=0)
    class Config:
        orm_mode = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    order_date: datetime
    payment_method: PaymentMethod
    total_amount: int = Field(..., ge=0)
    details: list[OrderDetailResponse]
    class Config:
        orm_mode = True
