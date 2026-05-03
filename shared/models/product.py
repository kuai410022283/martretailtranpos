from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Category(BaseModel):
    __tablename__ = 'categories'
    
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    description = Column(Text, nullable=True)
    
    parent = relationship("Category", remote_side='Category.id', back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"

class Product(BaseModel):
    __tablename__ = 'products'
    
    code = Column(String(50), unique=True, nullable=False)
    barcode = Column(String(50), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    brand = Column(String(100))
    specification = Column(String(100))
    price_cost = Column(Float, default=0.0)
    price_sale = Column(Float, default=0.0)
    price_member = Column(Float, default=0.0)
    stock_quantity = Column(Float, default=0.0)
    min_stock = Column(Float, default=0.0)
    max_stock = Column(Float, default=0.0)
    status = Column(String(20), default='正常')
    description = Column(Text)
    image_path = Column(String(500), nullable=True)
    
    category = relationship("Category", back_populates="products")
    
    def __repr__(self):
        return f"<Product {self.name}>"
