from pydantic import BaseModel,Field
from app.schemas.category_schema import CategoryResponse

class ProductRegister(BaseModel):
    product_name:str=Field(...,min_length=1,max_length=100)
    description:str=Field(min_length=1,max_length=1000)
    price:int=Field(...,gt=0)
    available_quantity:int=Field(ge=0)
    product_url:str |None=Field(default=None,max_length=200)
    category_id:int

class ProductResponse(BaseModel):
    id: int
    product_name: str
    description: str
    category_id: int
    price: int
    available_quantity: int
    product_url:str| None=None
    category: CategoryResponse| None=None

    class Config:
        orm_mode = True

