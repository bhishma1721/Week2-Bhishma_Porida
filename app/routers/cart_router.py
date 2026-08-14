from fastapi import FastAPI,HTTPException,APIRouter
from app.schemas.cart_schema import CartAddRequest,CartItemResponse,CartUpdateRequest

from app.db.base import get_db
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.models.category import Category    #not used

from app.routers.login_router import get_current_user

from fastapi.params import Depends
from sqlalchemy.orm import Session,joinedload

cart_router=APIRouter()


#helper function
def get_cart_item(cart_item_id: int, db: Session):
    return (
        db.query(CartItem)
        .options(
            joinedload(CartItem.product)
            .joinedload(Product.category)
        )
        .filter(CartItem.id == cart_item_id)
        .first()
    )

@cart_router.post('/add',response_model=list[CartItemResponse],tags=["Carts"])
def add_to_cart(request: CartAddRequest,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can manage only your own cart"
        )

    user = current_user
    user = (
        db.query(User)
        .filter(User.id == request.user_id)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=404,detail="User not found")

    product = (
        db.query(Product)
        .filter(Product.id == request.product_id)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=404,detail="Product not found")

#checks if item is already in cart or not
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == request.user_id,
            CartItem.product_id == request.product_id
        )
        .first()
    )

    current_quantity = cart_item.quantity if cart_item else 0
    requested_quantity = current_quantity + request.quantity

    if requested_quantity > product.available_quantity:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    if cart_item:
        cart_item.quantity = requested_quantity
    else:
        cart_item = CartItem(
            user_id=request.user_id,
            product_id=request.product_id,
            quantity=request.quantity
        )
        db.add(cart_item)

    db.commit()

    return [get_cart_item(cart_item.id, db)]


@cart_router.get("/{user_id}",response_model=list[CartItemResponse],tags=["Carts"])
def view_cart(user_id: int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if user_id != current_user.id: # here it is checking the ownership
        raise HTTPException(
            status_code=403,
            detail="You can view only your own cart"
        )

    return (
        db.query(CartItem)
        .options(
            joinedload(CartItem.product)
            .joinedload(Product.category)
        )
        .filter(CartItem.user_id == current_user.id)
        .all()
    )

@cart_router.delete("/remove/{cart_item_id}",tags=["Carts"])
def remove_from_cart(cart_item_id: int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == cart_item_id)
        .first()
    )

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can remove only your own cart item"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Cart item removed successfully"
    }


@cart_router.put("/update/{cart_item_id}",response_model=CartItemResponse,tags=["Carts"])
def update_cart_quantity(
    cart_item_id: int,
    request: CartUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == cart_item_id)
        .first()
    )

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can update only your own cart item"
        )

    product = (
        db.query(Product)
        .filter(Product.id == cart_item.product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if request.quantity > product.available_quantity:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    cart_item.quantity = request.quantity
    db.commit()
    db.refresh(cart_item)

    return get_cart_item(cart_item.id, db)