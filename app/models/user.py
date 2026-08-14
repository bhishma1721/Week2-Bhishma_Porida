from sqlalchemy import Column,Integer,String,ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,nullable=False)
    email=Column(String,unique=True,nullable=False)
    password=Column(String,nullable=False)
    mobile=Column(String,nullable=False)

    # Valid values: customer, admin, support
    role = Column(
        String(20),
        nullable=False,
        default="customer"
    )

    cart_items = relationship(
        "CartItem",
        back_populates="user"
    )

    orders = relationship(
        "Order",
        back_populates="user"
    )