from fastapi import FastAPI

from app.db.base import Base, engine #for creation of db tables
from app.routers.user_router import user_router
from app.routers.category_router import category_router
from app.routers.product_router import product_router
from app.routers.cart_router import cart_router
from app.routers.order_router import order_router

# import app.models.user
# import app.models.category
# import app.models.product
# import app.models.cart
# import app.models.order

app=FastAPI(title="Online Shopping API",
    description="Backend API for products, carts, and orders."
    )

@app.get('/')
def root():
    return {
        "message": "Online Shopping API is running",
    }
Base.metadata.create_all(engine)
app.include_router(user_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)