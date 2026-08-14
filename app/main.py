import os
import time
from uuid import uuid4 #uuid creates a unique request identifier
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.util.logger import logger

from app.db.base import Base, engine #for creation of db tables
from app.routers.user_router import user_router
from app.routers.category_router import category_router
from app.routers.product_router import product_router
from app.routers.cart_router import cart_router
from app.routers.order_router import order_router

from app.routers.login_router import login_router

from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.cart import CartItem
from app.models.order import Order, OrderDetail

# import app.models.user
# import app.models.category
# import app.models.product
# import app.models.cart
# import app.models.order

app=FastAPI(title="Online Shopping API",
    description="Backend API for products, carts, and orders."
    )


#Request represents the incoming HTTP request.
@app.middleware("http") #runs the function for every http request
async def request_logging_middleware(request: Request, call_next):  #call_next passes the request to the next stage of the application
    request_id = str(uuid4())

    request.state.request_id = request_id #We save the request ID here

    start_time = time.perf_counter()

    try:
        response = await call_next(request) #Wait for the requested route to finish and return its response

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed "
            "request_id=%s method=%s path=%s "
            "status_code=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms
        )

        return response

    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            "request_failed "
            "request_id=%s method=%s path=%s "
            "duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            duration_ms
        )

        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exception: HTTPException
):
    request_id = getattr(
        request.state,
        "request_id",
        "not-available"
    )

    logger.warning(
        "http_error "
        "request_id=%s method=%s path=%s "
        "status_code=%s detail=%s",
        request_id,
        request.method,
        request.url.path,
        exception.status_code,
        exception.detail
    )

    return JSONResponse(
        status_code=exception.status_code,
        headers=exception.headers,
        content={
            "detail": exception.detail,
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exception: Exception
):
    request_id = getattr(
        request.state,
        "request_id",
        "not-available"
    )

    logger.exception(
        "unexpected_error "
        "request_id=%s method=%s path=%s error=%s",
        request_id,
        request.method,
        request.url.path,
        str(exception)
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id
        }
    )

@app.get('/')
def root():
    return {
        "message": "Online Shopping API is running",
    }

# Base.metadata.create_all(engine)

if os.getenv("TESTING") != "1":
    Base.metadata.create_all(engine)
# app.include_router(user_router)
# app.include_router(category_router)
# app.include_router(product_router)
# app.include_router(cart_router)
# app.include_router(order_router)
app.include_router(login_router,prefix="/auth")
app.include_router(user_router,     prefix="/users")
app.include_router(category_router, prefix="/categories")
app.include_router(product_router,  prefix="/products")
app.include_router(cart_router,     prefix="/cart")
app.include_router(order_router,    prefix="/orders")  