from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User
from app.models.cart import CartItem
from app.models.product import Product
from app.models.order import Order, OrderDetail
from app.schemas.order_schema import (
    OrderCheckout,
    OrderHistoryResponse,
    OrderResponse
)

from app.routers.login_router import (
    get_current_user,
    require_roles
)

order_router = APIRouter()
@order_router.post("/checkout",response_model=OrderResponse,tags=["Orders"])
async def checkout_order(request: OrderCheckout,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can place orders only for yourself"
        )

    user = current_user
    user = (
        db.query(User)
        .filter(User.id == request.user_id)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == request.user_id)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    products = {}
    product_quantities = {}

    for cart_item in cart_items:
        if cart_item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Cart quantity must be greater than zero"
            )

        #validating product , product must be exist and active
        product = (
            db.query(Product)
            .filter(Product.id == cart_item.product_id,
                    Product.is_active.is_(True))
            .first()
        )

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product {cart_item.product_id} is unavailable and cannot be ordered"
            )

        products[product.id] = product
        product_quantities[product.id] = (
            product_quantities.get(product.id, 0)
            + cart_item.quantity
        )

    for product_id, quantity in product_quantities.items():
        product = products[product_id]
        if quantity > product.available_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock for product {product_id}. "
                    f"Available quantity: {product.available_quantity}"
                )
            )
    total_amount = 0
    for product_id, quantity in product_quantities.items():
        product = products[product_id]
        total_amount += product.price * quantity #calculatinng the total order
    new_order = Order(
        user_id=request.user_id,
        order_date=datetime.utcnow(),
        payment_method=request.payment_method.value,
        total_amount=total_amount
    )
    db.add(new_order)
    db.flush() #sends pending insert to db

    for product_id, quantity in product_quantities.items():
        product = products[product_id]
        product.available_quantity -= quantity #stock reducing
        new_order_detail = OrderDetail(
            order_id=new_order.id,
            product_id=product_id,
            quantity=quantity,
            price=product.price
        )
        db.add(new_order_detail)
    for cart_item in cart_items: #deleting cart item after successfull creation
        db.delete(cart_item)

    db.commit()
    db.refresh(new_order)
    return new_order


@order_router.get("/details/{order_id}",response_model=OrderResponse,tags=["Orders"])
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can view only your own order"
        )

    return order

@order_router.get(
    "/operations/all",
    response_model=list[OrderHistoryResponse],
    tags=["Orders"]
)
def get_all_orders(
    db: Session = Depends(get_db),
    operator_user: User = Depends(
        require_roles("admin", "support")
    )
):
    return (
        db.query(Order)
        .order_by(Order.order_date.desc())
        .all()
    )

@order_router.get(
    "/operations/{order_id}",
    response_model=OrderResponse,
    tags=["Orders"]
)
def get_operation_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    operator_user: User = Depends(
        require_roles("admin", "support")
    )
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order

@order_router.get("/{user_id}",response_model=list[OrderHistoryResponse],tags=["Orders"])
def get_order_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can view only your own order history"
        )

    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.order_date.desc())
        .all()
    )
