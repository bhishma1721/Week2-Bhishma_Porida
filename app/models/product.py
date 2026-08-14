from sqlalchemy import Column,Integer,String,ForeignKey,Boolean
from app.db.base import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, unique=True,nullable=False)
    description = Column(String,nullable=False)
    price = Column(Integer, nullable=False)
    available_quantity = Column(Integer,default=0,nullable=False)
    product_url = Column(String, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    category_id = Column(
            Integer,
            ForeignKey("categories.id"),
            nullable=False
        )
    category = relationship(
        "Category",
        back_populates="products"
    )
    cart_items = relationship(
        "CartItem",
        back_populates="product"
    )

    orders_details = relationship(
        "OrderDetail",
        back_populates="product"
    )