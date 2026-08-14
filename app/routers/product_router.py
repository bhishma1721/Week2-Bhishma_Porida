from fastapi import FastAPI,HTTPException,APIRouter
from app.schemas.product_schema import (
    ProductRegister,
    ProductResponse,
    ProductUpdate,
)

from app.db.base import get_db
from app.models.product import Product
from app.models.category import Category

from app.models.user import User
from app.routers.login_router import require_roles



from fastapi.params import Depends
from sqlalchemy.orm import Session

product_router = APIRouter()


@product_router.post(
    "/products/create",
    response_model=ProductResponse,
    tags=["Products"]
)
def add_product(
    request: ProductRegister,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin")) #authorization dependency
):
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

    existing_product = (
        db.query(Product)
        .filter(Product.product_name == request.product_name)
        .first()
    )

    if existing_product is not None:
        raise HTTPException(
            status_code=409,
            detail="Product name is already registered"
        )

    new_product = Product(
        product_name=request.product_name,
        description=request.description,
        price=request.price,
        available_quantity=request.available_quantity,
        product_url=request.product_url,
        category_id=request.category_id,
        is_active=True
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@product_router.put(
    "/products/update/{product_id}",
    response_model=ProductResponse,
    tags=["Products"]
)
def update_product(
    product_id: int,
    request: ProductUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

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

    duplicate_product = (
        db.query(Product)
        .filter(
            Product.product_name == request.product_name,
            Product.id != product_id
        )
        .first()
    )

    if duplicate_product is not None:
        raise HTTPException(
            status_code=409,
            detail="Product name is already registered"
        )

    product.product_name = request.product_name
    product.description = request.description
    product.price = request.price
    product.available_quantity = request.available_quantity
    product.product_url = request.product_url
    product.category_id = request.category_id

    db.commit()
    db.refresh(product)

    return product


@product_router.delete(
    "/products/deactivate/{product_id}",
    tags=["Products"]
)
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if not product.is_active:
        raise HTTPException(
            status_code=409,
            detail="Product is already inactive"
        )

    product.is_active = False
    db.commit()

    return {
        "message": "Product deactivated successfully",
        "product_id": product_id
    }


@product_router.get(
    "/product",
    response_model=list[ProductResponse],
    tags=["Products"]
)
def get_products(db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .all()
    )


@product_router.get(
    "/product/search",
    response_model=list[ProductResponse],
    tags=["Products"]
)
def search_products(
    name: str | None = None,
    id: int | None = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
    )

    if name:
        query = query.filter(
            Product.product_name.ilike(f"%{name}%")
        )

    if id is not None:
        query = query.filter(
            Product.category_id == id
        )

    products = query.all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No products found"
        )

    return products


@product_router.get(
    "/product/{id}",
    response_model=ProductResponse,
    tags=["Products"]
)
def product_id(
    id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(
            Product.id == id,
            Product.is_active.is_(True)
        )
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product
