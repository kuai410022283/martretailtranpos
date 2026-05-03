from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel
import datetime

class SaleOrder(BaseModel):
    __tablename__ = 'sale_orders'
    
    order_no = Column(String(20), unique=True, nullable=False)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=True)
    total_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    actual_amount = Column(Float, default=0.0)
    payment_method = Column(String(20))
    status = Column(String(20), default='已完成')
    operator = Column(String(50))
    remark = Column(String(200))
    
    member = relationship("Member")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SaleOrder {self.order_no}>"

class SaleItem(BaseModel):
    __tablename__ = 'sale_items'
    
    sale_id = Column(Integer, ForeignKey('sale_orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Float)
    price = Column(Float)
    cost_price = Column(Float, default=0.0)
    amount = Column(Float)
    discount = Column(Float, default=0.0)
    
    sale = relationship("SaleOrder", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<SaleItem {self.product.name} x {self.quantity}>"
