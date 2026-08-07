from fastapi import FastAPI,HTTPException,APIRouter
from app.schemas.category_schema import CategoryRegister, CategoryResponse

from app.db.base import get_db
from app.models.category import Category

from fastapi.params import Depends
from sqlalchemy.orm import Session

category_router=APIRouter()

@category_router.post('/category/create',response_model=CategoryResponse,tags=['Categories'])
def add(request:CategoryRegister,db:Session=Depends(get_db)):
    existing_category=(
        db.query(Category)
        .filter(Category.category_name==request.category_name)
        .first()
    )
    if existing_category is not None:
        raise HTTPException(status_code=404,detail="Category is already registered")

    new_category=Category(
        category_name=request.category_name
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category

@category_router.get('/category/list',response_model=list[CategoryResponse],tags=['Categories'])
def category_list(db:Session=Depends(get_db)):
    list=db.query(Category).all()
    return list