from pydantic import BaseModel, Field

class CategoryRegister(BaseModel):
    category_name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

class CategoryResponse(BaseModel):
    id: int
    category_name: str

    class Config:
        orm_mode = True