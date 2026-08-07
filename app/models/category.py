from sqlalchemy import Column,Integer,String
from app.db.base import Base
from sqlalchemy.orm import relationship

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True,nullable=False)
    products = relationship(
        "Product",
        back_populates="category"
    )