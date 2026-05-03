from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
import datetime

class StockLog(BaseModel):
    __tablename__ = 'stock_logs'
    
    product_id = Column(Integer, ForeignKey('products.id'))
    type = Column(String(20))
    quantity = Column(Float)
    cost_price = Column(Float, nullable=True)  # 变动时的成本价
    related_order_no = Column(String(50), nullable=True)
    remark = Column(String(200))
    operator = Column(String(50))
    
    product = relationship("Product")
    
    def __repr__(self):
        return f"<StockLog {self.product.name} {self.type} {self.quantity}>"
