from sqlalchemy import Column,Integer,String,ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )
    quantity = Column(Integer, nullable=False)
    user = relationship(
        "User",
        back_populates="cart_items"
    )
    product = relationship(
        "Product",
        back_populates="cart_items"
    )