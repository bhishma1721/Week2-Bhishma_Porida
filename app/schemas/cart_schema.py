from pydantic import BaseModel,Field
from app.schemas.product_schema import ProductResponse
class CartAddRequest(BaseModel):
    user_id: int
    product_id: int
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    product: ProductResponse

    class Config:
        orm_mode = True

class CartUpdateRequest(BaseModel):
    quantity: int=Field(...,gt=0)#