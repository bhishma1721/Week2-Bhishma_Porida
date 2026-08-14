from fastapi import FastAPI,HTTPException,APIRouter
from app.schemas.category_schema import CategoryRegister, CategoryResponse,CategoryUpdate

from app.db.base import get_db
from app.models.category import Category

from app.models.user import User
from app.routers.login_router import require_roles



from fastapi.params import Depends
from sqlalchemy.orm import Session

category_router=APIRouter()

@category_router.post("/category/create",response_model=CategoryResponse,tags=["Categories"])
def add(
    request: CategoryRegister,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    existing_category = (
        db.query(Category)
        .filter(
            Category.category_name == request.category_name
        )
        .first()
    )

    if existing_category is not None:
        raise HTTPException(
            status_code=404,
            detail="Category is already registered"
        )

    new_category = Category(
        category_name=request.category_name
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category

@category_router.put("/category/update/{category_id}",response_model=CategoryResponse,tags=["Categories"])
def update_category(
    category_id: int,
    request: CategoryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    duplicate_category = (
        db.query(Category)
        .filter(
            Category.category_name == request.category_name,
            Category.id != category_id
        )
        .first()
    )

    if duplicate_category is not None:
        raise HTTPException(
            status_code=409,
            detail="Category is already registered"
        )

    category.category_name = request.category_name

    db.commit()
    db.refresh(category)

    return category


@category_router.get('/category/list',response_model=list[CategoryResponse],tags=['Categories'])
def category_list(db:Session=Depends(get_db)):
    list=db.query(Category).all()
    return list