# from datetime import datetime
from sqlalchemy import Column,Integer,String,ForeignKey,DateTime,Numeric
from app.db.base import Base
from sqlalchemy.orm import relationship

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    order_date = Column(
        DateTime,
        nullable=False
    )
    payment_method = Column(String,nullable=False)
    total_amount = Column(Numeric(10,2),nullable=False)

    user = relationship(
        "User",
        back_populates="orders"
    )
    details = relationship(
        "OrderDetail",
        back_populates="order"
    )


class OrderDetail(Base):
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10,2), nullable=False)

    order = relationship(
        "Order",
        back_populates="details"
    )

    product = relationship(
        "Product",
        back_populates="orders_details"
    )