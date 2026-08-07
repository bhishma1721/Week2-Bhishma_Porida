from fastapi import FastAPI,HTTPException,APIRouter
from app.schemas.product_schema import ProductRegister

from app.db.base import get_db
from app.models.product import Product
from app.models.category import Category

from fastapi.params import Depends
from sqlalchemy.orm import Session

product_router=APIRouter()

@product_router.post('/products/create',tags=['Products'])
def add(request:ProductRegister,db:Session=Depends(get_db)):
    category = (
        db.query(Category)
        .filter(Category.id == request.category_id)
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    new_product = Product(
        product_name=request.product_name,
        description=request.description,
        price=request.price,
        available_quantity=request.available_quantity,
        product_url=request.product_url,
        category_id=request.category_id
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@product_router.get('/product',tags=["Products"])
def get_products(db:Session=Depends(get_db)):
    product=db.query(Product).all()
    return product

@product_router.get('/product/search',tags=["Products"])
def search_products(name:str=None,id:int=None,db:Session=Depends(get_db)):
    query = db.query(Product)
    if name:
        query = query.filter(
            Product.product_name.ilike(f"%{name}%") #ilike is case insensitive and % - wildcard it matches anything with the given word
        )

    if id:
        query=query.filter(
            Category.id==id
        )

    products=query.all()

    if not products:
        raise HTTPException(status_code=404,detail="No produts found")

    return products


@product_router.get("/product/{id}",tags=['Products'])
def product_id(id:int,db: Session=Depends(get_db)):
    product=db.query(Product).filter(Product.id==id).first()
    #we can also add exception like if product is None raise HttpException
    return product

